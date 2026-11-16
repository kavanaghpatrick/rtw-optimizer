"""Tests for rtw.ntp NTP calculator."""

import pytest

from rtw.models import Itinerary, NTPMethod
from rtw.ntp import NTPCalculator


@pytest.fixture
def calc():
    return NTPCalculator()


def _make_itinerary(segments, origin="CAI", ticket_type="DONE4", cabin="business"):
    """Build a minimal Itinerary for testing."""
    return Itinerary.model_validate(
        {
            "ticket": {"type": ticket_type, "cabin": cabin, "origin": origin},
            "segments": segments,
        }
    )


# ------------------------------------------------------------------
# Distance-based NTP tests
# ------------------------------------------------------------------


class TestDistanceBased:
    """Distance-based NTP earning: NTP = distance * (rate / 100)."""

    def test_qr_doh_nrt_d_class(self, calc):
        """QR DOH-NRT in D class: 50% of ~5156 miles = ~2578 NTP."""
        itin = _make_itinerary(
            [
                {"from": "DOH", "to": "NRT", "carrier": "QR"},
            ]
        )
        results = calc.calculate(itin, booking_class="D")
        assert len(results) == 1
        est = results[0]
        assert est.method == NTPMethod.DISTANCE
        assert est.rate == 50
        assert est.confidence == "calculated"
        assert est.estimated_ntp == pytest.approx(2578, abs=25)

    def test_cx_tpe_hkg_d_class(self, calc):
        """CX TPE-HKG in D class: 25% of ~501 miles = ~125 NTP."""
        itin = _make_itinerary(
            [
                {"from": "TPE", "to": "HKG", "carrier": "CX"},
            ]
        )
        results = calc.calculate(itin, booking_class="D")
        est = results[0]
        assert est.method == NTPMethod.DISTANCE
        assert est.rate == 25
        assert est.estimated_ntp == pytest.approx(125, abs=25)

    def test_fj_nan_sfo_d_class(self, calc):
        """FJ NAN-SFO in D class: 25% of ~5466 miles = ~1366 NTP."""
        itin = _make_itinerary(
            [
                {"from": "NAN", "to": "SFO", "carrier": "FJ"},
            ]
        )
        results = calc.calculate(itin, booking_class="D")
        est = results[0]
        assert est.method == NTPMethod.DISTANCE
        assert est.rate == 25
        assert est.estimated_ntp == pytest.approx(1366, abs=25)

    def test_rj_cai_amm_d_class(self, calc):
        """RJ CAI-AMM in D class: 25% of ~294 miles = ~73 NTP."""
        itin = _make_itinerary(
            [
                {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            ]
        )
        results = calc.calculate(itin, booking_class="D")
        est = results[0]
        assert est.method == NTPMethod.DISTANCE
        assert est.rate == 25
        assert est.estimated_ntp == pytest.approx(73, abs=25)

    def test_fj_atr72_earns_at_d_rate(self, calc):
        """FJ ATR-72 segment (NAN-FUN, short-haul): D maps to Y but earns at D rate."""
        itin = _make_itinerary(
            [
                {"from": "NAN", "to": "FUN", "carrier": "FJ"},
            ]
        )
        results = calc.calculate(itin, booking_class="D")
        est = results[0]
        assert est.rate == 25  # D-class rate, not Y-class
        assert est.estimated_ntp == pytest.approx(162, abs=25)
        assert "ATR-72" in est.notes

    def test_wy_ntp_positive_for_business(self, calc):
        """WY MCT-LHR in D class should earn positive NTP (12.5% of ~3260 miles)."""
        itin = _make_itinerary(
            [
                {"from": "MCT", "to": "LHR", "carrier": "WY"},
            ]
        )
        results = calc.calculate(itin, booking_class="D")
        assert len(results) == 1
        est = results[0]
        assert est.method == NTPMethod.DISTANCE
        assert est.rate == 12.5
        assert est.estimated_ntp > 0


class TestPerSegmentBookingClass:
    """Per-segment RBD overrides the itinerary-wide default (fixes B-class over-count)."""

    def test_default_class_earns_d_rate(self, calc):
        """No booking_class on the segment -> uses the default D (JL D = 50%)."""
        itin = _make_itinerary([{"from": "HND", "to": "SIN", "carrier": "JL"}])
        est = calc.calculate(itin)[0]
        assert est.rate == 50

    def test_segment_booking_class_overrides_default(self, calc):
        """A JL segment booked in B earns the B rate (15%), not D's 50%."""
        itin = _make_itinerary(
            [{"from": "HND", "to": "SIN", "carrier": "JL", "booking_class": "B"}]
        )
        est = calc.calculate(itin)[0]
        assert est.rate == 15
        # and it is genuinely lower than the D-rate result
        d_est = calc.calculate(
            _make_itinerary([{"from": "HND", "to": "SIN", "carrier": "JL"}])
        )[0]
        assert est.estimated_ntp < d_est.estimated_ntp

    def test_mixed_classes_per_segment(self, calc):
        """Different RBDs on different segments are honoured independently."""
        itin = _make_itinerary(
            [
                {"from": "SFO", "to": "HND", "carrier": "JL"},  # default D -> 50
                {"from": "HND", "to": "SIN", "carrier": "JL", "booking_class": "B"},  # 15
            ]
        )
        results = calc.calculate(itin)
        assert results[0].rate == 50
        assert results[1].rate == 15


class TestTicketCabinClass:
    """With no class given (as every CLI caller does), earning follows the
    ticket cabin: LONE books L, AONE books A, DONE books D."""

    def test_lone_qr_earns_economy_rate(self, calc):
        """Regression: LONE4 QR LHR-DOH earned 50% (1,629 NTP); L is 7% (~228)."""
        itin = _make_itinerary(
            [{"from": "LHR", "to": "DOH", "carrier": "QR"}],
            origin="LHR", ticket_type="LONE4", cabin="economy",
        )
        est = calc.calculate(itin)[0]
        assert est.rate == 7
        assert est.estimated_ntp == pytest.approx(228, abs=5)

    def test_aone_qr_earns_first_rate(self, calc):
        """AONE4 QR earns at A (40%), not D (50%)."""
        itin = _make_itinerary(
            [{"from": "LHR", "to": "DOH", "carrier": "QR"}],
            origin="LHR", ticket_type="AONE4", cabin="first",
        )
        est = calc.calculate(itin)[0]
        assert est.rate == 40
        assert est.confidence == "calculated"

    def test_done_qr_still_earns_d_rate(self, calc):
        itin = _make_itinerary([{"from": "LHR", "to": "DOH", "carrier": "QR"}], origin="LHR")
        assert calc.calculate(itin)[0].rate == 50

    def test_aone_on_fj_books_d_and_earns_d_rate(self, calc):
        """Rule 3015 §5(b): AONE on FJ books D, so it earns the D rate (25%)
        exactly, rather than an estimate from a non-existent A booking."""
        itin = _make_itinerary(
            [{"from": "NAN", "to": "SFO", "carrier": "FJ"}],
            origin="LHR", ticket_type="AONE4", cabin="first",
        )
        est = calc.calculate(itin)[0]
        assert est.rate == 25
        assert est.estimated_ntp > 0
        assert est.confidence == "calculated"

    def test_aone_wy_first_rate(self, calc):
        """WY First (A) earns 25%, double its flat 12.5% business rate."""
        itin = _make_itinerary(
            [{"from": "MCT", "to": "LHR", "carrier": "WY"}],
            origin="LHR", ticket_type="AONE4", cabin="first",
        )
        assert calc.calculate(itin)[0].rate == 25

    def test_segment_class_beats_ticket_cabin(self, calc):
        itin = _make_itinerary(
            [{"from": "LHR", "to": "DOH", "carrier": "QR", "booking_class": "B"}],
            origin="LHR", ticket_type="LONE4", cabin="economy",
        )
        assert calc.calculate(itin)[0].rate == 15


class TestSpendBased:
    """BA/AA/IB spend pool includes YQ; BA bonus keyed on cabin and haul."""

    def _ba(self, calc, to, ticket_type="DONE4", cabin="business", **seg):
        itin = _make_itinerary(
            [{"from": "LHR", "to": to, "carrier": "BA", **seg}],
            origin="LHR", ticket_type=ticket_type, cabin=cabin,
        )
        return calc.calculate(itin, total_fare_usd=5000)[0]

    def test_spend_pool_includes_yq(self, calc):
        """BA YQ (~$321/segment in carriers.yaml) is added to the fare before proration."""
        est = self._ba(calc, "JFK")
        assert "$5321 of fare + YQ allocated" in est.notes

    def test_short_haul_business_gets_club_europe(self, calc):
        """Regression: LHR-MAD BA DONE4 got '+400 Club World'; it is Club Europe 175."""
        est = self._ba(calc, "MAD")
        assert "+175 BA Club Europe bonus" in est.notes
        assert "Club World" not in est.notes

    def test_long_haul_business_gets_club_world(self, calc):
        assert "+500 BA Club World bonus" in self._ba(calc, "JFK").notes

    def test_economy_bonuses(self, calc):
        short = self._ba(calc, "MAD", ticket_type="LONE4", cabin="economy")
        long_ = self._ba(calc, "JFK", ticket_type="LONE4", cabin="economy")
        assert "+75 BA Euro Traveller bonus" in short.notes
        assert "+150 BA World Traveller bonus" in long_.notes

    def test_first_bonuses(self, calc):
        """Long-haul First earns the First bonus; BA terms treat short-haul First
        as Club Europe."""
        assert "+650 BA First bonus" in self._ba(
            calc, "JFK", ticket_type="AONE4", cabin="first").notes
        assert "+175 BA Club Europe bonus" in self._ba(
            calc, "MAD", ticket_type="AONE4", cabin="first").notes

    def test_lon_amm_listed_short_haul(self, calc):
        """LON-AMM is on BA's short-haul route list despite >2,000 miles."""
        assert "Club Europe" in self._ba(calc, "AMM").notes

    def test_ba_operated_2000_mile_cutoff(self, calc):
        """LHR-TLV (~2,220 mi) is long-haul when BA-operated, short-haul when
        BA-marketed on another operator (3,000-mile limit)."""
        assert "Club World" in self._ba(calc, "TLV").notes
        assert "Club Europe" in self._ba(calc, "TLV", operating_carrier="IB").notes

    def test_no_bonus_on_aa_or_ib(self, calc):
        itin = _make_itinerary(
            [{"from": "MAD", "to": "LHR", "carrier": "IB"},
             {"from": "LHR", "to": "JFK", "carrier": "AA"}],
            origin="MAD",
        )
        for est in calc.calculate(itin, total_fare_usd=5000):
            assert "bonus" not in est.notes

    def test_flight_prefix_decides_marketing_carrier(self, calc):
        """Regression: carrier CX with flight BA7001 earned CX 25% distance; the
        coupon is BA-marketed, so it earns spend-based, with a warning."""
        itin = _make_itinerary(
            [{"from": "HKG", "to": "LHR", "carrier": "CX", "flight": "BA7001"}],
            origin="LHR",
        )
        est = calc.calculate(itin, total_fare_usd=5000)[0]
        assert est.method == NTPMethod.REVENUE
        assert "earning follows the flight number (BA)" in est.notes

    def test_ay_codeshare_range_matches_codeshare_module(self, calc):
        """Regression: NTP gave AY5449 50% distance while codeshare.py said spend.
        Both now agree, and the unverified-for-BA-Club caveat is shown."""
        from rtw.codeshare import earning_band

        itin = _make_itinerary(
            [{"from": "SIN", "to": "HKG", "carrier": "AY", "flight": "AY5449"}],
            origin="LHR",
        )
        est = calc.calculate(itin, total_fare_usd=5000)[0]
        assert earning_band("AY", "AY5449").method == "spend"
        assert est.method == NTPMethod.REVENUE
        assert "unverified for BA Club" in est.notes
        assert "bonus" not in est.notes

    def test_ay_own_flight_still_distance(self, calc):
        itin = _make_itinerary(
            [{"from": "HEL", "to": "LHR", "carrier": "AY", "flight": "AY1331"}],
            origin="LHR",
        )
        est = calc.calculate(itin)[0]
        assert est.method == NTPMethod.DISTANCE
        assert est.rate == 50


class TestEarningNotes:
    """Plain-language earning explanations on distance segments."""

    def test_half_band_carrier_flagged(self, calc):
        """A 25%-band carrier (CX) in D is flagged as half of a 50%-band partner."""
        itin = _make_itinerary([{"from": "SIN", "to": "HKG", "carrier": "CX"}])
        est = calc.calculate(itin)[0]
        assert "half of a 50%-band partner" in est.notes
        assert "25%" in est.notes

    def test_quarter_band_carrier_flagged(self, calc):
        """WY (12.5%) in D is flagged as a quarter of a 50%-band partner."""
        itin = _make_itinerary([{"from": "MCT", "to": "LHR", "carrier": "WY"}])
        est = calc.calculate(itin)[0]
        assert "a quarter of a 50%-band partner" in est.notes

    def test_top_band_carrier_no_half_note(self, calc):
        """A 50%-band carrier (JL) in D is NOT flagged as reduced."""
        itin = _make_itinerary([{"from": "SFO", "to": "HND", "carrier": "JL"}])
        est = calc.calculate(itin)[0]
        assert "half of a 50%-band partner" not in est.notes

    def test_fallback_class_note(self, calc):
        """A non-D fallback bucket explains the earning drop vs D."""
        itin = _make_itinerary(
            [{"from": "HND", "to": "SIN", "carrier": "JL", "booking_class": "B"}]
        )
        est = calc.calculate(itin)[0]
        assert "booked B" in est.notes
        assert "15%" in est.notes
        assert "D on JL earns 50%" in est.notes


class TestRateDisplay:
    """The rate column renders whole-number percents, not fractions * 100."""

    def test_plain_formatter_rate_not_multiplied(self):
        """Regression: rate 25 must render '25%', never '2500%' (was f'{rate:.0%}')."""
        from rtw.models import NTPEstimate
        from rtw.output import get_formatter

        est = NTPEstimate(
            segment_index=0, route="HKG-LHR", carrier="CX", distance_miles=5984,
            method=NTPMethod.DISTANCE, rate=25, estimated_ntp=1496,
            confidence="calculated", notes="",
        )
        out = get_formatter("plain").format_ntp([est])
        assert "25%" in out
        assert "2500%" not in out

    def test_plain_formatter_fractional_rate(self):
        """A 12.5% rate renders cleanly, not '1250%' or '12%'."""
        from rtw.models import NTPEstimate
        from rtw.output import get_formatter

        est = NTPEstimate(
            segment_index=0, route="MCT-LHR", carrier="WY", distance_miles=3260,
            method=NTPMethod.DISTANCE, rate=12.5, estimated_ntp=408,
            confidence="calculated", notes="",
        )
        out = get_formatter("plain").format_ntp([est])
        assert "12.5%" in out


# ------------------------------------------------------------------
# Revenue-based NTP tests
# ------------------------------------------------------------------


class TestRevenueBased:
    """Revenue-based NTP earning: 1 NTP per GBP 1 of eligible spend."""

    def test_aa_segment_is_revenue_based(self, calc):
        """AA segments should use revenue method with estimated confidence."""
        itin = _make_itinerary(
            [
                {"from": "SFO", "to": "JFK", "carrier": "AA"},
            ]
        )
        results = calc.calculate(itin, booking_class="D", total_fare_usd=4000)
        est = results[0]
        assert est.method == NTPMethod.REVENUE
        assert est.confidence == "estimated"
        assert est.estimated_ntp > 0

    def test_ba_segment_gets_bonus(self, calc):
        """BA long-haul business gets the Club World bonus (+500 NTP from Apr 2026)."""
        itin = _make_itinerary(
            [
                {"from": "LHR", "to": "JFK", "carrier": "BA"},
            ],
            origin="LHR",
        )
        results = calc.calculate(itin, booking_class="D", total_fare_usd=5000)
        est = results[0]
        assert est.method == NTPMethod.REVENUE
        assert est.estimated_ntp >= 500
        assert "+500 BA Club World bonus" in est.notes

    def test_ib_segment_is_revenue_based(self, calc):
        """IB segments should use revenue method."""
        itin = _make_itinerary(
            [
                {"from": "MEX", "to": "MAD", "carrier": "IB"},
            ]
        )
        results = calc.calculate(itin, booking_class="D", total_fare_usd=4000)
        est = results[0]
        assert est.method == NTPMethod.REVENUE
        assert est.confidence == "estimated"


# ------------------------------------------------------------------
# Surface and special segments
# ------------------------------------------------------------------


class TestSurfaceSegments:
    """Surface sectors earn zero NTP."""

    def test_surface_segment_zero_ntp(self, calc):
        """Surface segment should earn 0 NTP."""
        itin = _make_itinerary(
            [
                {"from": "JFK", "to": "MCO", "carrier": None, "type": "surface"},
            ]
        )
        results = calc.calculate(itin, booking_class="D")
        assert len(results) == 1
        est = results[0]
        assert est.estimated_ntp == 0.0
        assert est.distance_miles == 0.0
        assert "surface" in est.notes.lower()

    def test_surface_in_mixed_itinerary(self, calc):
        """Surface segment among flown segments still earns 0."""
        itin = _make_itinerary(
            [
                {"from": "DOH", "to": "NRT", "carrier": "QR"},
                {"from": "NRT", "to": "LAX", "carrier": None, "type": "surface"},
                {"from": "LAX", "to": "SFO", "carrier": "AA"},
            ]
        )
        results = calc.calculate(itin, booking_class="D", total_fare_usd=4000)
        assert len(results) == 3
        assert results[1].estimated_ntp == 0.0
        # Flown segments should have positive NTP
        assert results[0].estimated_ntp > 0
        assert results[2].estimated_ntp > 0


# ------------------------------------------------------------------
# Full V3 itinerary integration test
# ------------------------------------------------------------------


class TestV3Itinerary:
    """Integration test with the full V3 reference routing."""

    def test_v3_total_ntp_in_range(self, calc, v3_itinerary):
        """V3 total NTP should be in 6,000-12,000 range."""
        itin = Itinerary.model_validate(v3_itinerary)
        results = calc.calculate(itin, booking_class="D")

        total = sum(r.estimated_ntp for r in results)
        assert 6_000 <= total <= 12_000, f"Total NTP {total:.0f} outside 6,000-12,000"

    def test_v3_segment_count(self, calc, v3_itinerary):
        """Should produce one NTPEstimate per segment."""
        itin = Itinerary.model_validate(v3_itinerary)
        results = calc.calculate(itin, booking_class="D")
        assert len(results) == len(itin.segments)

    def test_v3_surface_segment_is_zero(self, calc, v3_itinerary):
        """JFK-MCO surface segment (index 11) should be 0 NTP."""
        itin = Itinerary.model_validate(v3_itinerary)
        results = calc.calculate(itin, booking_class="D")
        # Find the surface segment
        surface = [r for r in results if "surface" in r.notes.lower()]
        assert len(surface) == 1
        assert surface[0].estimated_ntp == 0.0

    def test_v3_distance_based_total(self, calc, v3_itinerary):
        """Distance-based segments should sum to ~7,300 NTP."""
        itin = Itinerary.model_validate(v3_itinerary)
        results = calc.calculate(itin, booking_class="D")

        distance_ntp = sum(r.estimated_ntp for r in results if r.method == NTPMethod.DISTANCE)
        # Expected ~7,331 from RJ + QR + JL + CX + FJ segments
        assert distance_ntp == pytest.approx(7_331, abs=200)

    def test_v3_has_both_methods(self, calc, v3_itinerary):
        """V3 should include both distance-based and revenue-based segments."""
        itin = Itinerary.model_validate(v3_itinerary)
        results = calc.calculate(itin, booking_class="D")

        methods = {r.method for r in results if r.estimated_ntp > 0}
        assert NTPMethod.DISTANCE in methods
        assert NTPMethod.REVENUE in methods


# ------------------------------------------------------------------
# Default fare lookup
# ------------------------------------------------------------------


class TestDefaultFare:
    """Default fare comes from FareSource (cheapest filed fare in fares.db)."""

    @staticmethod
    def _db_min(origin, fare_basis):
        import sqlite3
        from pathlib import Path

        db = Path(__file__).parent.parent / "rtw" / "data" / "fares.db"
        con = sqlite3.connect(db)
        try:
            return con.execute(
                "SELECT MIN(fare_usd) FROM fares WHERE origin = ? AND fare_basis = ?",
                [origin, fare_basis],
            ).fetchone()[0]
        finally:
            con.close()

    def test_cai_done4_fare(self, calc):
        """CAI DONE4 default fare is the filed CAI DONE4 fare."""
        itin = _make_itinerary(
            [
                {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            ],
            origin="CAI",
            ticket_type="DONE4",
        )
        assert calc._default_fare(itin) == pytest.approx(self._db_min("CAI", "DONE4"))
        results = calc.calculate(itin, booking_class="D")
        assert len(results) == 1

    def test_lax_uses_lax_fare_not_cai(self, calc):
        """Spend-based NTP ex-LAX allocates the filed LAX fare, not a Cairo substitute."""
        itin = _make_itinerary(
            [{"from": "LAX", "to": "JFK", "carrier": "AA"}],
            origin="LAX",
            ticket_type="DONE4",
        )
        lax_fare = self._db_min("LAX", "DONE4")
        default = calc.calculate(itin, booking_class="D")
        explicit = calc.calculate(itin, booking_class="D", total_fare_usd=lax_fare)
        assert default[0].method == NTPMethod.REVENUE
        assert default[0].estimated_ntp == pytest.approx(explicit[0].estimated_ntp)
        # AA US-domestic carries no YQ, so the spend pool is just the LAX fare.
        assert f"${lax_fare:.0f} of fare + YQ allocated" in default[0].notes

    def test_unfiled_origin_labelled_fare_unknown(self, calc):
        """No filed fare: spend-based segments say 'fare unknown' instead of guessing."""
        itin = _make_itinerary(
            [
                {"from": "GLA", "to": "LHR", "carrier": "BA"},
                {"from": "LHR", "to": "DOH", "carrier": "QR"},
            ],
            origin="GLA",
            ticket_type="DONE4",
        )
        assert self._db_min("GLA", "DONE4") is None
        assert calc._default_fare(itin) is None
        results = calc.calculate(itin, booking_class="D")
        assert results[0].confidence == "fare unknown"
        assert results[0].estimated_ntp == 0.0
        assert "Fare unknown" in results[0].notes
        # Distance-based segments do not need the fare and are still calculated
        assert results[1].method == NTPMethod.DISTANCE
        assert results[1].estimated_ntp > 0



class TestJetstarOperated:
    """QF codeshares operated by Jetstar: earning unconfirmed, so flagged."""

    def test_qf_operated_by_jq_flagged(self, calc):
        itin = _make_itinerary(
            [{"from": "SYD", "to": "MEL", "carrier": "QF", "operating_carrier": "JQ"}],
            origin="SYD",
        )
        est = calc.calculate(itin)[0]
        assert "Jetstar" in est.notes
        assert "not confirmed" in est.notes

    def test_qf_own_flight_not_flagged(self, calc):
        itin = _make_itinerary([{"from": "SYD", "to": "MEL", "carrier": "QF"}], origin="SYD")
        est = calc.calculate(itin)[0]
        assert "Jetstar" not in (est.notes or "")
