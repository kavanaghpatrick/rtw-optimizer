"""Tests for CityPairDirectionRule."""

from rtw.models import Itinerary, Ticket, Segment, Severity
from rtw.rules.direction import CityPairDirectionRule
from rtw.validator import build_context


def _make_itinerary(segments_data, origin="CAI"):
    ticket = Ticket(type="DONE4", cabin="business", origin=origin)
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestCityPairDirection:
    def test_nrt_tpe_twice_violation(self):
        """NRT->TPE twice = VIOLATION."""
        segs = [
            {"from": "NRT", "to": "TPE", "carrier": "JL"},
            {"from": "TPE", "to": "HKG", "carrier": "CX"},
            {"from": "HKG", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "TPE", "carrier": "JL"},  # duplicate
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = CityPairDirectionRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1
        assert "NRT" in violations[0].message or "TPE" in violations[0].message

    def test_nrt_tpe_reverse_passes(self):
        """NRT->TPE + TPE->NRT = different directions, PASS."""
        segs = [
            {"from": "NRT", "to": "TPE", "carrier": "JL"},
            {"from": "TPE", "to": "NRT", "carrier": "JL"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = CityPairDirectionRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_same_city_group_detected(self):
        """HND->TSA + NRT->TPE = same city pair (Tokyo->Taipei), VIOLATION."""
        segs = [
            {"from": "HND", "to": "TSA", "carrier": "JL"},
            {"from": "TSA", "to": "HKG", "carrier": "CX"},
            {"from": "HKG", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "TPE", "carrier": "JL"},  # same city pair!
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = CityPairDirectionRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1

    def test_surface_sector_excluded(self):
        """Surface NRT->TPE + flown NRT->TPE = only 1 counted, PASS."""
        segs = [
            {"from": "NRT", "to": "TPE", "type": "surface"},
            {"from": "TPE", "to": "HKG", "carrier": "CX"},
            {"from": "HKG", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "TPE", "carrier": "JL"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = CityPairDirectionRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_segments_involved_populated(self):
        """segments_involved contains the correct indices."""
        segs = [
            {"from": "NRT", "to": "TPE", "carrier": "JL"},
            {"from": "TPE", "to": "HKG", "carrier": "CX"},
            {"from": "HKG", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "TPE", "carrier": "JL"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = CityPairDirectionRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert violations[0].segments_involved == [0, 3]

    def test_no_duplicates_passes(self):
        """All unique pairs = PASS."""
        segs = [
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "SYD", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs, origin="LHR")
        ctx = build_context(itin)
        results = CityPairDirectionRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_three_duplicates(self):
        """NRT->TPE flown 3 times = VIOLATION."""
        segs = [
            {"from": "NRT", "to": "TPE", "carrier": "JL"},
            {"from": "TPE", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "TPE", "carrier": "JL"},
            {"from": "TPE", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "TPE", "carrier": "JL"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = CityPairDirectionRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1

    def test_different_carriers_still_fails(self):
        """Same city pair, different carriers = still VIOLATION."""
        segs = [
            {"from": "NRT", "to": "TPE", "carrier": "JL"},
            {"from": "TPE", "to": "HKG", "carrier": "CX"},
            {"from": "HKG", "to": "NRT", "carrier": "CX"},
            {"from": "NRT", "to": "TPE", "carrier": "CX"},  # different carrier, same pair
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = CityPairDirectionRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1

    def test_v3_fixture_passes(self, v3_itinerary):
        """V3 reference fixture has no duplicate city pairs."""
        itin = Itinerary(**v3_itinerary)
        ctx = build_context(itin)
        results = CityPairDirectionRule().check(itin, ctx)
        assert all(r.passed for r in results)
