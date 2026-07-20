"""Tests for rtw.ntp NTP calculator."""

import pytest

from rtw.models import Itinerary, NTPMethod
from rtw.ntp import NTPCalculator


@pytest.fixture
def calc():
    return NTPCalculator()


def _make_itinerary(segments, origin="CAI", ticket_type="DONE4"):
    """Build a minimal Itinerary for testing."""
    return Itinerary.model_validate(
        {
            "ticket": {"type": ticket_type, "cabin": "business", "origin": origin},
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
        """BA segments should get Club World bonus (+400 NTP)."""
        itin = _make_itinerary(
            [
                {"from": "LHR", "to": "JFK", "carrier": "BA"},
            ],
            origin="LHR",
        )
        results = calc.calculate(itin, booking_class="D", total_fare_usd=5000)
        est = results[0]
        assert est.method == NTPMethod.REVENUE
        # Should include the 400 bonus on top of the fare-based NTP
        assert est.estimated_ntp >= 400
        assert "bonus" in est.notes.lower()

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
    """Fare lookup from fares.yaml."""

    def test_cai_done4_fare(self, calc):
        """CAI DONE4 fare should be 4000."""
        itin = _make_itinerary(
            [
                {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            ],
            origin="CAI",
            ticket_type="DONE4",
        )
        # Should use the default fare without error
        results = calc.calculate(itin, booking_class="D")
        assert len(results) == 1
