"""Tests for stopover and surface rules."""

from rtw.models import Itinerary, Ticket, Segment, Severity
from rtw.rules.stopovers import (
    MinimumStopoverRule,
    OriginContinentStopoverRule,
    OriginCountryStopoverPerDirectionRule,
    SameCityVisitLimitRule,
)
from rtw.rules.surface import SameCityResolutionRule
from rtw.validator import build_context


def _make_itinerary(segments_data, origin="CAI"):
    ticket = Ticket(type="DONE4", cabin="business", origin=origin)
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestMinimumStopovers:
    def test_v3_passes(self, v3_itinerary):
        itin = Itinerary(**v3_itinerary)
        ctx = build_context(itin)
        results = MinimumStopoverRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_zero_stopovers_fails(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "type": "transit"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "type": "transit"},
            {"from": "DOH", "to": "CAI", "carrier": "QR", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = MinimumStopoverRule().check(itin, ctx)
        assert any(not r.passed for r in results)


class TestOriginContinentStopovers:
    def test_v3_warns_about_mad(self, v3_itinerary):
        """V3 has AMM, DOH, MAD as EU/ME stopovers — should warn."""
        itin = Itinerary(**v3_itinerary)
        ctx = build_context(itin)
        results = OriginContinentStopoverRule().check(itin, ctx)
        # Should produce a warning (3 stopovers in EU/ME)
        warnings = [r for r in results if r.severity == Severity.WARNING]
        assert len(warnings) >= 1  # 3 stopovers in EU/ME should produce a warning


class TestSameCityResolution:
    def test_v3_detects_same_city_pairs(self, v3_itinerary):
        itin = Itinerary(**v3_itinerary)
        ctx = build_context(itin)
        results = SameCityResolutionRule().check(itin, ctx)
        info_results = [r for r in results if "Same-city pair" in r.message]
        assert len(info_results) >= 2  # NRT/HND and TSA/TPE


class TestMinimumStopoverBoundary:
    def test_exactly_one_stopover_fails(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "type": "stopover"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "type": "transit"},
            {"from": "DOH", "to": "CAI", "carrier": "QR", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = MinimumStopoverRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        assert any("Only 1" in r.message for r in results)

    def test_exactly_two_stopovers_passes(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "type": "stopover"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "type": "stopover"},
            {"from": "DOH", "to": "CAI", "carrier": "QR", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = MinimumStopoverRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("2 stopovers" in r.message for r in results)

    def test_many_stopovers_passes(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "type": "stopover"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "type": "stopover"},
            {"from": "DOH", "to": "NRT", "carrier": "QR", "type": "stopover"},
            {"from": "NRT", "to": "SYD", "carrier": "QF", "type": "stopover"},
            {"from": "SYD", "to": "LAX", "carrier": "QF", "type": "stopover"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "stopover"},
            {"from": "LHR", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = MinimumStopoverRule().check(itin, ctx)
        assert all(r.passed for r in results)


class TestOriginContinentStopoverExpanded:
    def test_zero_stopovers_in_origin_continent(self):
        # No stopovers in EU_ME (CAI origin) — LHR is transit, not stopover
        segs = [
            {"from": "CAI", "to": "NRT", "carrier": "QR", "type": "transit"},
            {"from": "NRT", "to": "LAX", "carrier": "JL", "type": "stopover"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "transit"},
            {"from": "LHR", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = OriginContinentStopoverRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("0/2" in r.message for r in results)

    def test_one_stopover_in_origin_continent(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "type": "stopover"},
            {"from": "AMM", "to": "NRT", "carrier": "QR", "type": "stopover"},
            {"from": "NRT", "to": "LAX", "carrier": "JL", "type": "stopover"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "transit"},
            {"from": "LHR", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = OriginContinentStopoverRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("1/2" in r.message for r in results)

    def test_two_stopovers_in_origin_continent(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "type": "stopover"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "type": "stopover"},
            {"from": "DOH", "to": "NRT", "carrier": "QR", "type": "stopover"},
            {"from": "NRT", "to": "LAX", "carrier": "JL", "type": "stopover"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "transit"},
            {"from": "LHR", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = OriginContinentStopoverRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("2/2" in r.message for r in results)

    def test_three_stopovers_in_origin_warns(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "type": "stopover"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "type": "stopover"},
            {"from": "DOH", "to": "IST", "carrier": "QR", "type": "stopover"},
            {"from": "IST", "to": "NRT", "carrier": "BA", "type": "stopover"},
            {"from": "NRT", "to": "LAX", "carrier": "JL", "type": "stopover"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "transit"},
            {"from": "LHR", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = OriginContinentStopoverRule().check(itin, ctx)
        warnings = [r for r in results if r.severity == Severity.WARNING]
        assert len(warnings) >= 1
        assert any("3 stopovers" in r.message for r in results)

    def test_unknown_origin_passes_with_info(self):
        segs = [
            {"from": "ZZZ", "to": "JFK", "carrier": "AA", "type": "stopover"},
            {"from": "JFK", "to": "ZZZ", "carrier": "AA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="ZZZ")
        ctx = build_context(itin)
        results = OriginContinentStopoverRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("Cannot determine" in r.message for r in results)


class TestOriginCountryStopoverPerDirection:
    def test_one_outbound_one_return_passes(self):
        """One stopover leaving Egypt, one returning -- within 1/direction limit."""
        segs = [
            {"from": "CAI", "to": "LXR", "carrier": "MS", "type": "stopover"},  # outbound EG stopover
            {"from": "LXR", "to": "DOH", "carrier": "QR", "type": "stopover"},  # leaves Egypt
            {"from": "DOH", "to": "NRT", "carrier": "QR", "type": "stopover"},
            {"from": "NRT", "to": "LAX", "carrier": "JL", "type": "stopover"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "transit"},
            {"from": "LHR", "to": "SSH", "carrier": "BA", "type": "stopover"},  # return EG stopover
            {"from": "SSH", "to": "CAI", "carrier": "MS", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = OriginCountryStopoverPerDirectionRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("1 outbound, 1 return" in r.message for r in results)

    def test_two_outbound_stopovers_fails(self):
        """Two stopovers in Egypt on outbound exceeds the 1/direction limit."""
        segs = [
            {"from": "CAI", "to": "LXR", "carrier": "MS", "type": "stopover"},  # EG stopover 1
            {"from": "LXR", "to": "HRG", "carrier": "MS", "type": "stopover"},  # EG stopover 2
            {"from": "HRG", "to": "DOH", "carrier": "QR", "type": "stopover"},  # leaves Egypt
            {"from": "DOH", "to": "NRT", "carrier": "QR", "type": "stopover"},
            {"from": "NRT", "to": "LAX", "carrier": "JL", "type": "stopover"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "transit"},
            {"from": "LHR", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = OriginCountryStopoverPerDirectionRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        violations = [r for r in results if not r.passed]
        assert any("2 stopovers" in r.message for r in violations)
        assert any("outbound" in r.message for r in violations)

    def test_two_return_stopovers_fails(self):
        """Two stopovers in Egypt on return exceeds the 1/direction limit."""
        segs = [
            {"from": "CAI", "to": "DOH", "carrier": "QR", "type": "transit"},   # leaves Egypt immediately
            {"from": "DOH", "to": "NRT", "carrier": "QR", "type": "stopover"},
            {"from": "NRT", "to": "LAX", "carrier": "JL", "type": "stopover"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "transit"},
            {"from": "LHR", "to": "SSH", "carrier": "BA", "type": "stopover"},  # EG return stopover 1
            {"from": "SSH", "to": "LXR", "carrier": "MS", "type": "stopover"},  # EG return stopover 2
            {"from": "LXR", "to": "CAI", "carrier": "MS", "type": "final"},     # final (EG)
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = OriginCountryStopoverPerDirectionRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        violations = [r for r in results if not r.passed]
        assert any("return" in r.message for r in violations)

    def test_no_origin_country_stopovers_passes(self):
        """No stopovers at all in Egypt -- only transits in EG, stopovers abroad."""
        segs = [
            {"from": "CAI", "to": "DOH", "carrier": "QR", "type": "transit"},   # transit, not stopover
            {"from": "DOH", "to": "NRT", "carrier": "QR", "type": "stopover"},
            {"from": "NRT", "to": "LAX", "carrier": "JL", "type": "stopover"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "stopover"},
            {"from": "LHR", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = OriginCountryStopoverPerDirectionRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("0 outbound, 0 return" in r.message for r in results)

    def test_unknown_origin_country_passes(self):
        """Unknown origin airport -- cannot determine country, passes with INFO."""
        segs = [
            {"from": "ZZZ", "to": "JFK", "carrier": "AA", "type": "stopover"},
            {"from": "JFK", "to": "ZZZ", "carrier": "AA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="ZZZ")
        ctx = build_context(itin)
        results = OriginCountryStopoverPerDirectionRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any(r.severity == Severity.INFO for r in results)
        assert any("Cannot determine" in r.message for r in results)


class TestSameCityVisitLimit:
    def test_normal_visits_pass(self):
        """Each city visited once or twice -- well under any limit."""
        segs = [
            {"from": "CAI", "to": "DOH", "carrier": "QR", "type": "stopover"},
            {"from": "DOH", "to": "NRT", "carrier": "QR", "type": "stopover"},
            {"from": "NRT", "to": "LAX", "carrier": "JL", "type": "stopover"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "stopover"},
            {"from": "LHR", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = SameCityVisitLimitRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_five_visits_same_city_fails(self):
        """DOH visited 5 times as destination -- exceeds the 4-visit non-NA limit."""
        segs = [
            {"from": "CAI", "to": "DOH", "carrier": "QR", "type": "stopover"},  # DOH visit 1
            {"from": "DOH", "to": "AMM", "carrier": "RJ", "type": "stopover"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "type": "stopover"},  # DOH visit 2
            {"from": "DOH", "to": "IST", "carrier": "QR", "type": "stopover"},
            {"from": "IST", "to": "DOH", "carrier": "QR", "type": "stopover"},  # DOH visit 3
            {"from": "DOH", "to": "NRT", "carrier": "QR", "type": "stopover"},
            {"from": "NRT", "to": "DOH", "carrier": "QR", "type": "stopover"},  # DOH visit 4
            {"from": "DOH", "to": "LHR", "carrier": "QR", "type": "stopover"},
            {"from": "LHR", "to": "DOH", "carrier": "QR", "type": "stopover"},  # DOH visit 5
            {"from": "DOH", "to": "CAI", "carrier": "QR", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = SameCityVisitLimitRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        violations = [r for r in results if not r.passed]
        assert any("5 visits" in r.message and "DOH" in r.message for r in violations)

    def test_na_allows_five_visits(self):
        """JFK (North America) visited 5 times -- within the 5-visit NA limit."""
        segs = [
            {"from": "JFK", "to": "LAX", "carrier": "AA", "type": "stopover"},
            {"from": "LAX", "to": "JFK", "carrier": "AA", "type": "stopover"},  # JFK visit 1
            {"from": "JFK", "to": "DFW", "carrier": "AA", "type": "stopover"},
            {"from": "DFW", "to": "JFK", "carrier": "AA", "type": "stopover"},  # JFK visit 2
            {"from": "JFK", "to": "MIA", "carrier": "AA", "type": "stopover"},
            {"from": "MIA", "to": "JFK", "carrier": "AA", "type": "stopover"},  # JFK visit 3
            {"from": "JFK", "to": "ORD", "carrier": "AA", "type": "stopover"},
            {"from": "ORD", "to": "JFK", "carrier": "AA", "type": "stopover"},  # JFK visit 4
            {"from": "JFK", "to": "SFO", "carrier": "AA", "type": "stopover"},
            {"from": "SFO", "to": "JFK", "carrier": "AA", "type": "final"},     # JFK visit 5
        ]
        itin = _make_itinerary(segs, origin="JFK")
        ctx = build_context(itin)
        results = SameCityVisitLimitRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_same_city_group_counted_together(self):
        """NRT and HND (both Tokyo) counted as same city -- 4 visits at limit, passes."""
        segs = [
            {"from": "CAI", "to": "NRT", "carrier": "QR", "type": "stopover"},  # TYO visit 1
            {"from": "NRT", "to": "SYD", "carrier": "JL", "type": "stopover"},
            {"from": "SYD", "to": "HND", "carrier": "QF", "type": "stopover"},  # TYO visit 2
            {"from": "HND", "to": "LAX", "carrier": "JL", "type": "stopover"},
            {"from": "LAX", "to": "NRT", "carrier": "AA", "type": "stopover"},  # TYO visit 3
            {"from": "NRT", "to": "DOH", "carrier": "QR", "type": "stopover"},
            {"from": "DOH", "to": "HND", "carrier": "QR", "type": "stopover"},  # TYO visit 4
            {"from": "HND", "to": "CAI", "carrier": "QR", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = SameCityVisitLimitRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_no_violations_pass_message(self):
        """Simple route with no visit limit issues -- pass message contains OK."""
        segs = [
            {"from": "CAI", "to": "DOH", "carrier": "QR", "type": "stopover"},
            {"from": "DOH", "to": "NRT", "carrier": "QR", "type": "stopover"},
            {"from": "NRT", "to": "CAI", "carrier": "QR", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = SameCityVisitLimitRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("OK" in r.message for r in results)
