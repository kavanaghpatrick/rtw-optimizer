"""Tests for rtw.cost CostEstimator."""

import sqlite3
from pathlib import Path

import pytest

from rtw.models import CostEstimate, Itinerary, TicketType
from rtw.cost import CostEstimator, FareLookupError, FareSource

_FARES_DB = Path(__file__).parent.parent / "rtw" / "data" / "fares.db"


def _db_min(origins, fare_basis):
    """Cheapest filed fare for any of the given db origin codes, read straight from fares.db."""
    origins = [origins] if isinstance(origins, str) else list(origins)
    con = sqlite3.connect(_FARES_DB)
    try:
        row = con.execute(
            f"SELECT MIN(fare_usd) FROM fares WHERE fare_basis = ? "
            f"AND origin IN ({','.join('?' * len(origins))})",
            [fare_basis, *origins],
        ).fetchone()
    finally:
        con.close()
    return row[0]


def _db_carriers_at_min(origins, fare_basis):
    origins = [origins] if isinstance(origins, str) else list(origins)
    fare = _db_min(origins, fare_basis)
    con = sqlite3.connect(_FARES_DB)
    try:
        rows = con.execute(
            f"SELECT DISTINCT carrier FROM fares WHERE fare_basis = ? AND fare_usd = ? "
            f"AND origin IN ({','.join('?' * len(origins))})",
            [fare_basis, fare, *origins],
        ).fetchall()
    finally:
        con.close()
    return {r[0] for r in rows}


@pytest.fixture
def estimator():
    return CostEstimator()


def _make_itinerary(segments, origin="CAI", ticket_type="DONE4", passengers=1, cabin="business"):
    """Build a minimal Itinerary for testing."""
    return Itinerary.model_validate(
        {
            "ticket": {
                "type": ticket_type,
                "cabin": cabin,
                "origin": origin,
                "passengers": passengers,
            },
            "segments": segments,
        }
    )


# ------------------------------------------------------------------
# T026: Base fare lookup and origin comparison
# ------------------------------------------------------------------


class TestBaseFare:
    """Base fare lookup goes through FareSource (cheapest filed fare in fares.db)."""

    @pytest.mark.parametrize(
        "origin,db_codes,basis",
        [
            ("CAI", ["CAI"], "DONE4"),
            ("CAI", ["CAI"], "DONE3"),
            ("OSL", ["OSL"], "LONE4"),
            ("SYD", ["SYD"], "DONE4"),
            ("JFK", ["JFK"], "DONE4"),
            ("LAX", ["LAX"], "DONE4"),
            ("KHI", ["KHI"], "DONE3"),
            ("DEL", ["DEL"], "DONE3"),
            ("BOM", ["BOM"], "DONE3"),
        ],
    )
    def test_matches_fares_db_min(self, estimator, origin, db_codes, basis):
        fare = estimator.get_base_fare(origin, TicketType(basis))
        assert fare == pytest.approx(_db_min(db_codes, basis))

    def test_london_airports_use_city_code(self, estimator):
        """LHR/LGW/LCY resolve to the LON filings (cheapest across LON and LHR rows)."""
        expected = _db_min(["LON", "LHR"], "DONE4")
        for code in ("LHR", "LGW", "LCY", "LON"):
            assert estimator.get_base_fare(code, TicketType.DONE4) == pytest.approx(expected)
        assert estimator.fare_source.get("LHR", "DONE4").origin == "LON"

    def test_tokyo_airports_and_city_code(self, estimator):
        """fares.db has NRT and HND rows but no TYO row; all three resolve to Tokyo."""
        expected = _db_min(["NRT", "HND"], "DONE4")
        assert _db_min(["TYO"], "DONE4") is None
        for code in ("NRT", "HND", "TYO"):
            assert estimator.get_base_fare(code, TicketType.DONE4) == pytest.approx(expected)

    def test_unfiled_aone_returns_zero_not_estimate(self, estimator):
        """SYD and JNB file no AONE3; no 1.6x synthetic fare is returned."""
        for origin in ("SYD", "JNB"):
            assert _db_min([origin], "AONE3") is None
            assert estimator.get_base_fare(origin, TicketType.AONE3) == 0.0
            assert estimator.fare_source.get(origin, TicketType.AONE3) is None

    def test_unknown_origin_returns_zero(self, estimator):
        """Unknown origin should return 0."""
        fare = estimator.get_base_fare("ZZZ", TicketType.DONE4)
        assert fare == 0.0

    def test_case_insensitive(self, estimator):
        """Origin lookup should be case-insensitive."""
        assert estimator.get_base_fare("cai", TicketType.DONE4) == estimator.get_base_fare(
            "CAI", TicketType.DONE4
        )


class TestFareSource:
    """Provenance, metadata and overrides of the single fare source."""

    def test_quote_names_filing_carrier(self):
        quote = FareSource().get("CAI", TicketType.DONE4)
        assert set(quote.carrier.split("/")) == _db_carriers_at_min("CAI", "DONE4")
        assert quote.source == "fares.db"
        assert quote.carrier in quote.note

    def test_data_date_from_metadata_table(self):
        con = sqlite3.connect(_FARES_DB)
        try:
            built = dict(con.execute("SELECT key, value FROM metadata").fetchall())[
                "source_built"
            ]
        finally:
            con.close()
        fs = FareSource()
        assert fs.data_date == built[:10]
        assert built[:10] in fs.get("OSL", "DONE3").note

    def test_override_wins_and_is_labelled(self, tmp_path):
        overrides = tmp_path / "fares.yaml"
        overrides.write_text(
            "overrides:\n  LHR:\n    DONE3: {fare_usd: 7000, carrier: BA, "
            "source: 'test quote'}\n"
        )
        fs = FareSource(overrides_path=overrides)
        quote = fs.get("LGW", "DONE3")
        assert quote.fare_usd == 7000
        assert quote.source == "fares.yaml override"
        assert "test quote" in quote.note
        # Other fare bases still come from fares.db
        assert fs.get("LHR", "DONE4").fare_usd == pytest.approx(
            _db_min(["LON", "LHR"], "DONE4")
        )

    def test_override_without_source_rejected(self, tmp_path):
        overrides = tmp_path / "fares.yaml"
        overrides.write_text("overrides:\n  OSL:\n    DONE3: {fare_usd: 1}\n")
        with pytest.raises(ValueError, match="source"):
            FareSource(overrides_path=overrides)

    def test_shipped_overrides_all_name_a_source(self):
        """Loading the shipped fares.yaml must succeed (every override has a source)."""
        FareSource()


class TestCompareOrigins:
    """Origin comparison ranks every origin in fares.db."""

    def test_sorted_cheapest_first(self, estimator):
        """Results should be sorted cheapest first."""
        results = estimator.compare_origins(TicketType.DONE4)
        fares = [r["fare_usd"] for r in results]
        assert fares == sorted(fares)

    def test_cheapest_matches_db_global_min(self, estimator):
        """The top-ranked fare is the lowest filed DONE3 fare anywhere in fares.db."""
        results = estimator.compare_origins(TicketType.DONE3)
        con = sqlite3.connect(_FARES_DB)
        try:
            db_origin, db_fare = con.execute(
                "SELECT origin, MIN(fare_usd) FROM fares WHERE fare_basis = 'DONE3'"
            ).fetchone()
        finally:
            con.close()
        assert results[0]["fare_usd"] == pytest.approx(db_fare)
        assert results[0]["origin"] == db_origin

    def test_ranks_all_db_origins(self, estimator):
        """Every origin filing DONE4 appears (metro airports collapsed to one city)."""
        con = sqlite3.connect(_FARES_DB)
        try:
            db_origins = {
                r[0]
                for r in con.execute(
                    "SELECT DISTINCT origin FROM fares WHERE fare_basis = 'DONE4'"
                )
            }
        finally:
            con.close()
        results = estimator.compare_origins(TicketType.DONE4)
        origins = {r["origin"] for r in results}
        assert len(results) == len(origins)  # one row per origin
        assert len(origins) > 100
        assert {"KHI", "DEL", "BOM", "CAI", "OSL", "LON", "TYO", "LAX"}.issubset(origins)
        assert "LHR" not in origins and "NRT" not in origins  # collapsed into LON/TYO
        assert len(origins) >= len(db_origins) - 10

    def test_khi_cheaper_than_cai_for_done3(self, estimator):
        """Cairo is not the cheapest: Karachi files DONE3 below Cairo."""
        results = estimator.compare_origins(TicketType.DONE3)
        origins = [r["origin"] for r in results]
        assert _db_min("KHI", "DONE3") < _db_min("CAI", "DONE3")
        assert origins.index("KHI") < origins.index("CAI")

    def test_continent_filter(self, estimator):
        results = estimator.compare_origins(TicketType.DONE4, continent="EU_ME")
        assert results
        assert all(r["continent"] == "Europe/Middle East" for r in results)
        assert {"CAI", "OSL", "LON"}.issubset({r["origin"] for r in results})
        label = estimator.compare_origins(TicketType.DONE4, continent="Europe/Middle East")
        assert [r["origin"] for r in label] == [r["origin"] for r in results]

    def test_unfiled_aone3_origins_absent(self, estimator):
        origins = {r["origin"] for r in estimator.compare_origins(TicketType.AONE3)}
        assert "SYD" not in origins and "JNB" not in origins

    def test_result_has_expected_keys(self, estimator):
        """Each result should have origin, name, fare_usd, currency, notes, carrier."""
        results = estimator.compare_origins(TicketType.DONE4)
        for r in results:
            for key in ("origin", "name", "fare_usd", "currency", "notes", "carrier"):
                assert key in r


# ------------------------------------------------------------------
# T027: Surcharge estimation
# ------------------------------------------------------------------


class TestSurcharges:
    """Surcharge (YQ) estimation."""

    def test_surface_segment_zero_yq(self, estimator):
        """Surface segments should have zero YQ."""
        itin = _make_itinerary(
            [
                {"from": "JFK", "to": "MCO", "carrier": None, "type": "surface"},
            ]
        )
        yq = estimator.estimate_surcharges(itin)
        assert yq == 0.0

    def test_aa_domestic_zero_yq(self, estimator):
        """AA domestic US-US should have zero YQ."""
        itin = _make_itinerary(
            [
                {"from": "SFO", "to": "JFK", "carrier": "AA"},
            ]
        )
        yq = estimator.estimate_surcharges(itin)
        assert yq == 0.0

    def test_aa_international_has_yq(self, estimator):
        """AA international (e.g. MIA-MEX) should charge YQ."""
        itin = _make_itinerary(
            [
                {"from": "MIA", "to": "MEX", "carrier": "AA"},
            ]
        )
        yq = estimator.estimate_surcharges(itin)
        assert yq > 0

    def test_surcharge_ranking(self, estimator):
        """Per-segment YQ ranking: JL < AA < CX < IB < BA."""
        carriers = ["JL", "AA", "CX", "IB", "BA"]
        yq_values = []
        for carrier in carriers:
            itin = _make_itinerary(
                [
                    {"from": "NRT", "to": "LHR", "carrier": carrier},
                ]
            )
            yq_values.append(estimator.estimate_surcharges(itin))

        for i in range(len(yq_values) - 1):
            assert yq_values[i] < yq_values[i + 1], (
                f"{carriers[i]} (${yq_values[i]}) should be less than "
                f"{carriers[i + 1]} (${yq_values[i + 1]})"
            )

    def test_multi_segment_sum(self, estimator):
        """Surcharges should sum across segments."""
        itin = _make_itinerary(
            [
                {"from": "DOH", "to": "NRT", "carrier": "QR"},
                {"from": "NRT", "to": "HKG", "carrier": "CX"},
            ]
        )
        yq = estimator.estimate_surcharges(itin)
        # QR(150) + CX(200) = 350
        assert yq == pytest.approx(350, abs=5)

    def test_mixed_surface_and_flown(self, estimator):
        """Surface segments contribute zero; flown segments contribute YQ."""
        itin = _make_itinerary(
            [
                {"from": "DOH", "to": "NRT", "carrier": "QR"},
                {"from": "NRT", "to": "LAX", "carrier": None, "type": "surface"},
                {"from": "LAX", "to": "LHR", "carrier": "BA"},
            ]
        )
        yq = estimator.estimate_surcharges(itin)
        # QR(150) + surface(0) + BA(321) = 471
        assert yq == pytest.approx(471, abs=5)


# ------------------------------------------------------------------
# T028: Plating carrier comparison
# ------------------------------------------------------------------


class TestPlatingComparison:
    """Plating carrier comparison."""

    def test_qr_cheapest_plating(self, estimator):
        """QR should be the cheapest plating option."""
        itin = _make_itinerary(
            [
                {"from": "DOH", "to": "NRT", "carrier": "QR"},
            ]
        )
        results = estimator.compare_plating(itin)
        assert results[0]["plating_carrier"] == "QR"

    def test_ba_most_expensive_plating(self, estimator):
        """BA should be the most expensive plating option."""
        itin = _make_itinerary(
            [
                {"from": "DOH", "to": "NRT", "carrier": "QR"},
            ]
        )
        results = estimator.compare_plating(itin)
        assert results[-1]["plating_carrier"] == "BA"

    def test_plating_order(self, estimator):
        """Plating order: QR < MH < CX < AA < BA."""
        itin = _make_itinerary(
            [
                {"from": "DOH", "to": "NRT", "carrier": "QR"},
            ]
        )
        results = estimator.compare_plating(itin)
        carriers = [r["plating_carrier"] for r in results]
        expected = ["QR", "MH", "CX", "AA", "BA"]
        assert carriers == expected

    def test_aa_plating_has_flexibility_note(self, estimator):
        """AA plating should mention flexibility."""
        itin = _make_itinerary(
            [
                {"from": "DOH", "to": "NRT", "carrier": "QR"},
            ]
        )
        results = estimator.compare_plating(itin)
        aa = [r for r in results if r["plating_carrier"] == "AA"][0]
        assert aa["flexibility"] == "high"
        assert "flexibility" in aa["notes"].lower() or "change" in aa["notes"].lower()

    def test_result_has_expected_keys(self, estimator):
        """Each result should have plating_carrier, name, total_yq_usd, flexibility, notes."""
        itin = _make_itinerary(
            [
                {"from": "DOH", "to": "NRT", "carrier": "QR"},
            ]
        )
        results = estimator.compare_plating(itin)
        for r in results:
            assert "plating_carrier" in r
            assert "name" in r
            assert "total_yq_usd" in r
            assert "flexibility" in r
            assert "notes" in r


# ------------------------------------------------------------------
# T030: Total cost estimation
# ------------------------------------------------------------------


class TestTotalEstimate:
    """Total cost estimation."""

    def test_returns_cost_estimate(self, estimator):
        """Should return a CostEstimate model."""
        itin = _make_itinerary(
            [
                {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            ]
        )
        result = estimator.estimate_total(itin)
        assert isinstance(result, CostEstimate)

    def test_total_equals_base_plus_yq(self, estimator):
        """Per-person total should equal base_fare + total_yq."""
        itin = _make_itinerary(
            [
                {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            ]
        )
        result = estimator.estimate_total(itin)
        assert result.total_per_person_usd == pytest.approx(
            result.base_fare_usd + result.total_yq_usd
        )

    def test_all_pax_equals_per_person_times_passengers(self, estimator):
        """All-pax total should equal per-person * passengers."""
        itin = _make_itinerary(
            [
                {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            ],
            passengers=2,
        )
        result = estimator.estimate_total(itin)
        assert result.total_all_pax_usd == pytest.approx(result.total_per_person_usd * 2)

    def test_v3_per_person_uses_filed_fare(self, estimator, v3_itinerary):
        """V3 (ex-CAI DONE4) per-person cost = filed CAI DONE4 fare + YQ."""
        itin = Itinerary.model_validate(v3_itinerary)
        result = estimator.estimate_total(itin)
        assert result.base_fare_usd == pytest.approx(_db_min("CAI", "DONE4"))
        assert result.total_per_person_usd == pytest.approx(
            _db_min("CAI", "DONE4") + result.total_yq_usd
        )

    def test_estimate_shows_fare_source_and_date(self, estimator, v3_itinerary):
        itin = Itinerary.model_validate(v3_itinerary)
        result = estimator.estimate_total(itin)
        assert "fares.db" in result.fare_source
        assert estimator.fare_source.data_date in result.fare_source
        assert set(result.fare_carrier.split("/")) == _db_carriers_at_min("CAI", "DONE4")

    def test_lax_origin_now_costed(self, estimator):
        """LAX was missing from the old fare table; it files DONE4 in fares.db."""
        itin = _make_itinerary(
            [{"from": "LAX", "to": "LHR", "carrier": "BA"}], origin="LAX"
        )
        result = estimator.estimate_total(itin)
        assert result.base_fare_usd == pytest.approx(_db_min("LAX", "DONE4"))

    def test_v3_origin_and_ticket_type(self, estimator, v3_itinerary):
        """V3 estimate should reflect CAI origin and DONE4 ticket type."""
        itin = Itinerary.model_validate(v3_itinerary)
        result = estimator.estimate_total(itin)
        assert result.origin == "CAI"
        assert result.ticket_type == TicketType.DONE4

    def test_v3_passengers(self, estimator, v3_itinerary):
        """V3 has 2 passengers."""
        itin = Itinerary.model_validate(v3_itinerary)
        result = estimator.estimate_total(itin)
        assert result.passengers == 2

    def test_v3_plating_carrier(self, estimator, v3_itinerary):
        """Default plating should be AA."""
        itin = Itinerary.model_validate(v3_itinerary)
        result = estimator.estimate_total(itin)
        assert result.plating_carrier == "AA"

    def test_v3_base_fare_matches_lookup(self, estimator, v3_itinerary):
        """V3 base fare should match direct lookup."""
        itin = Itinerary.model_validate(v3_itinerary)
        result = estimator.estimate_total(itin)
        expected = estimator.get_base_fare("CAI", TicketType.DONE4)
        assert result.base_fare_usd == expected

    def test_v3_yq_positive(self, estimator, v3_itinerary):
        """V3 should have positive YQ (it has international segments)."""
        itin = Itinerary.model_validate(v3_itinerary)
        result = estimator.estimate_total(itin)
        assert result.total_yq_usd > 0

    def test_plating_affects_notes(self, estimator, v3_itinerary):
        """AA plating should include flexibility note."""
        itin = Itinerary.model_validate(v3_itinerary)
        result = estimator.estimate_total(itin, plating_carrier="AA")
        assert "flexibility" in result.notes.lower() or "change" in result.notes.lower()


# ------------------------------------------------------------------
# AONE (first class) fare tests
# ------------------------------------------------------------------


class TestAONEFares:
    """AONE first class fares come only from filed rows in fares.db."""

    _ORIGINS = ["CAI", "OSL", "JNB", "NRT", "CMB", "LHR", "JFK", "SYD"]
    _DB_CODES = {"NRT": ["NRT", "HND"], "LHR": ["LON", "LHR"]}
    _AONE_TYPES = [TicketType.AONE3, TicketType.AONE4, TicketType.AONE5, TicketType.AONE6]
    _DONE_TYPES = [TicketType.DONE3, TicketType.DONE4, TicketType.DONE5, TicketType.DONE6]

    def _codes(self, origin):
        return self._DB_CODES.get(origin, [origin])

    def test_aone_matches_db_or_absent(self, estimator):
        """Every AONE fare equals the filed min; unfiled combinations return 0."""
        for origin in self._ORIGINS:
            for tt in self._AONE_TYPES:
                expected = _db_min(self._codes(origin), tt.value)
                fare = estimator.get_base_fare(origin, tt)
                if expected is None:
                    assert fare == 0.0, f"{origin}/{tt.value} has no filed row"
                else:
                    assert fare == pytest.approx(expected), f"{origin}/{tt.value}"

    def test_aone_more_than_done(self, estimator):
        """Where both are filed, AONE is more expensive than DONE for the same origin."""
        for origin in self._ORIGINS:
            for aone, done in zip(self._AONE_TYPES, self._DONE_TYPES):
                aone_fare = estimator.get_base_fare(origin, aone)
                done_fare = estimator.get_base_fare(origin, done)
                if aone_fare == 0.0:
                    continue
                assert aone_fare > done_fare, (
                    f"{origin}: {aone.value}=${aone_fare} should be > {done.value}=${done_fare}"
                )

    def test_aone_done_ratio_matches_db(self, estimator):
        """AONE/DONE ratio equals the ratio of the filed fares (no fixed 1.6x multiplier)."""
        for origin in self._ORIGINS:
            for aone, done in zip(self._AONE_TYPES, self._DONE_TYPES):
                db_aone = _db_min(self._codes(origin), aone.value)
                db_done = _db_min(self._codes(origin), done.value)
                if db_aone is None or db_done is None:
                    continue
                ratio = estimator.get_base_fare(origin, aone) / estimator.get_base_fare(
                    origin, done
                )
                assert ratio == pytest.approx(db_aone / db_done)


# ------------------------------------------------------------------
# Zero-fare guard tests
# ------------------------------------------------------------------


class TestZeroFareGuard:
    """FareLookupError when fare data is missing."""

    def test_zero_fare_raises_fare_lookup_error(self, estimator):
        """estimate_total() should raise FareLookupError when base_fare == $0."""
        itin = _make_itinerary(
            [{"from": "ZZZ", "to": "YYY", "carrier": "QR"}],
            origin="ZZZ",
        )
        with pytest.raises(FareLookupError):
            estimator.estimate_total(itin)

    def test_fare_lookup_error_message_contains_origin(self, estimator):
        """FareLookupError message should contain the origin code and ticket type."""
        itin = _make_itinerary(
            [{"from": "ZZZ", "to": "YYY", "carrier": "QR"}],
            origin="ZZZ",
        )
        with pytest.raises(FareLookupError, match="ZZZ"):
            estimator.estimate_total(itin)


# ------------------------------------------------------------------
# Fixture-based tests (DONE3, LONE3)
# ------------------------------------------------------------------


class TestDONE3Fixture:
    """DONE3 fixture: 3-continent business routing."""

    def test_done3_base_fare_nonzero(self, estimator, done3_itinerary):
        """DONE3 fixture should have nonzero base fare."""
        itin = Itinerary.model_validate(done3_itinerary)
        result = estimator.estimate_total(itin)
        assert result.base_fare_usd > 0

    def test_done3_base_fare_matches_db(self, estimator, done3_itinerary):
        """DONE3 fixture (ex-CAI) base fare is the filed CAI DONE3 fare."""
        itin = Itinerary.model_validate(done3_itinerary)
        result = estimator.estimate_total(itin)
        assert result.base_fare_usd == pytest.approx(_db_min("CAI", "DONE3"))

    def test_done3_cheaper_than_done4(self, estimator, done3_itinerary, v3_itinerary):
        """DONE3 base fare should be less than DONE4."""
        done3 = Itinerary.model_validate(done3_itinerary)
        done4 = Itinerary.model_validate(v3_itinerary)
        # Both are ex-CAI, so compare base fares
        fare3 = estimator.get_base_fare(done3.ticket.origin, done3.ticket.type)
        fare4 = estimator.get_base_fare(done4.ticket.origin, done4.ticket.type)
        assert fare3 < fare4


class TestLONE3Fixture:
    """LONE3 fixture: 3-continent economy routing."""

    def test_lone3_base_fare_nonzero(self, estimator, lone3_itinerary):
        """LONE3 fixture should have nonzero base fare."""
        itin = Itinerary.model_validate(lone3_itinerary)
        result = estimator.estimate_total(itin)
        assert result.base_fare_usd > 0

    def test_lone3_cheaper_than_done3(self, estimator, lone3_itinerary):
        """LONE3 should be cheaper than DONE3 for same continent count."""
        itin = Itinerary.model_validate(lone3_itinerary)
        lone3_fare = estimator.get_base_fare(itin.ticket.origin, TicketType.LONE3)
        done3_fare = estimator.get_base_fare(itin.ticket.origin, TicketType.DONE3)
        assert lone3_fare < done3_fare
