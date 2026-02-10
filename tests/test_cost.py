"""Tests for rtw.cost CostEstimator."""

import pytest

from rtw.models import CostEstimate, Itinerary, TicketType
from rtw.cost import CostEstimator, FareLookupError


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
    """Base fare lookup from fares.yaml."""

    def test_cai_done4_in_range(self, estimator):
        """CAI DONE4 should be $3500-$5000."""
        fare = estimator.get_base_fare("CAI", TicketType.DONE4)
        assert 3500 <= fare <= 5000, f"CAI DONE4 = ${fare}, expected $3500-$5000"

    def test_cai_done4_exact(self, estimator):
        """CAI DONE4 should be $4000 per fares.yaml."""
        fare = estimator.get_base_fare("CAI", TicketType.DONE4)
        assert fare == 4000

    def test_jfk_most_expensive(self, estimator):
        """JFK should be the most expensive origin for DONE4."""
        fare = estimator.get_base_fare("JFK", TicketType.DONE4)
        assert fare == 10500

    def test_unknown_origin_returns_zero(self, estimator):
        """Unknown origin should return 0."""
        fare = estimator.get_base_fare("ZZZ", TicketType.DONE4)
        assert fare == 0.0

    def test_case_insensitive(self, estimator):
        """Origin lookup should be case-insensitive."""
        fare = estimator.get_base_fare("cai", TicketType.DONE4)
        assert fare == 4000


class TestCompareOrigins:
    """Origin comparison sorted by fare."""

    def test_sorted_cheapest_first(self, estimator):
        """Results should be sorted cheapest first."""
        results = estimator.compare_origins(TicketType.DONE4)
        fares = [r["fare_usd"] for r in results]
        assert fares == sorted(fares)

    def test_cai_cheapest_for_done4(self, estimator):
        """CAI should be the cheapest origin for DONE4."""
        results = estimator.compare_origins(TicketType.DONE4)
        assert results[0]["origin"] == "CAI"

    def test_jfk_most_expensive_for_done4(self, estimator):
        """JFK should be the most expensive origin for DONE4."""
        results = estimator.compare_origins(TicketType.DONE4)
        assert results[-1]["origin"] == "JFK"

    def test_origin_ordering_done4(self, estimator):
        """Check relative ordering: CAI < JNB < OSL < NRT < LHR < JFK."""
        results = estimator.compare_origins(TicketType.DONE4)
        origins = [r["origin"] for r in results]
        # Verify these origins appear in correct relative order
        for earlier, later in [
            ("CAI", "JNB"),
            ("JNB", "OSL"),
            ("OSL", "NRT"),
            ("NRT", "LHR"),
            ("LHR", "JFK"),
        ]:
            assert origins.index(earlier) < origins.index(later), (
                f"{earlier} should be cheaper than {later}"
            )

    def test_all_origins_present(self, estimator):
        """All origins from fares.yaml should appear."""
        results = estimator.compare_origins(TicketType.DONE4)
        origins = {r["origin"] for r in results}
        assert {"CAI", "OSL", "JNB", "NRT", "LHR", "JFK", "SYD", "CMB"}.issubset(origins)

    def test_result_has_expected_keys(self, estimator):
        """Each result should have origin, name, fare_usd, currency, notes."""
        results = estimator.compare_origins(TicketType.DONE4)
        for r in results:
            assert "origin" in r
            assert "name" in r
            assert "fare_usd" in r
            assert "currency" in r
            assert "notes" in r


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

    def test_v3_per_person_in_range(self, estimator, v3_itinerary):
        """V3 per-person cost should be $4,000-$8,000."""
        itin = Itinerary.model_validate(v3_itinerary)
        result = estimator.estimate_total(itin)
        assert 4_000 <= result.total_per_person_usd <= 8_000, (
            f"V3 per-person ${result.total_per_person_usd:.0f} outside $4,000-$8,000"
        )

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
    """AONE first class fares from fares.yaml."""

    _ORIGINS = ["CAI", "OSL", "JNB", "NRT", "CMB", "LHR", "JFK", "SYD"]
    _AONE_TYPES = [TicketType.AONE3, TicketType.AONE4, TicketType.AONE5, TicketType.AONE6]

    def test_aone_fares_nonzero(self, estimator):
        """AONE4 fare should be > 0 for all 8 origins."""
        for origin in self._ORIGINS:
            fare = estimator.get_base_fare(origin, TicketType.AONE4)
            assert fare > 0, f"AONE4 fare for {origin} is $0"

    def test_aone_fares_all_origins_all_types(self, estimator):
        """All 32 AONE entries should be > 0."""
        for origin in self._ORIGINS:
            for tt in self._AONE_TYPES:
                fare = estimator.get_base_fare(origin, tt)
                assert fare > 0, f"{tt.value} fare for {origin} is $0"

    def test_aone_more_than_done(self, estimator):
        """AONE should be more expensive than DONE for same origin+continent count."""
        done_types = [TicketType.DONE3, TicketType.DONE4, TicketType.DONE5, TicketType.DONE6]
        for origin in self._ORIGINS:
            for aone, done in zip(self._AONE_TYPES, done_types):
                aone_fare = estimator.get_base_fare(origin, aone)
                done_fare = estimator.get_base_fare(origin, done)
                assert aone_fare > done_fare, (
                    f"{origin}: {aone.value}=${aone_fare} should be > {done.value}=${done_fare}"
                )

    def test_aone_done_ratio_in_range(self, estimator):
        """AONE/DONE ratio should be in 1.4-1.8x range."""
        done_types = [TicketType.DONE3, TicketType.DONE4, TicketType.DONE5, TicketType.DONE6]
        for origin in self._ORIGINS:
            for aone, done in zip(self._AONE_TYPES, done_types):
                aone_fare = estimator.get_base_fare(origin, aone)
                done_fare = estimator.get_base_fare(origin, done)
                ratio = aone_fare / done_fare
                assert 1.4 <= ratio <= 1.8, (
                    f"{origin}: {aone.value}/{done.value} ratio = {ratio:.2f}, expected 1.4-1.8"
                )


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

    def test_done3_per_person_in_range(self, estimator, done3_itinerary):
        """DONE3 per-person cost should be reasonable ($3,000-$6,000)."""
        itin = Itinerary.model_validate(done3_itinerary)
        result = estimator.estimate_total(itin)
        assert 3_000 <= result.total_per_person_usd <= 6_000

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
