"""Tests for FirstSegmentNotSurfaceRule."""

from rtw.models import Itinerary, Ticket, Segment, Severity
from rtw.rules.surface import FirstSegmentNotSurfaceRule
from rtw.validator import build_context


def _make_itinerary(segments_data, origin="CAI"):
    ticket = Ticket(type="DONE4", cabin="business", origin=origin)
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestFirstSegmentNotSurface:
    def test_surface_first_segment_violation(self):
        """Surface as first segment = VIOLATION."""
        segs = [
            {"from": "CAI", "to": "DOH", "type": "surface"},
            {"from": "DOH", "to": "HEL", "carrier": "AY"},
            {"from": "HEL", "to": "CAI", "carrier": "AY"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = FirstSegmentNotSurfaceRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) == 1
        assert "surface sector" in violations[0].message.lower()
        assert violations[0].segments_involved == [0]

    def test_flown_first_segment_passes(self):
        """Flown first segment = PASS."""
        segs = [
            {"from": "CAI", "to": "DOH", "carrier": "RJ"},
            {"from": "DOH", "to": "HEL", "carrier": "AY"},
            {"from": "HEL", "to": "CAI", "carrier": "AY"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = FirstSegmentNotSurfaceRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_surface_middle_segment_passes(self):
        """Surface in the middle (not first) = PASS for this rule."""
        segs = [
            {"from": "CAI", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "LAX", "type": "surface"},
            {"from": "LAX", "to": "CAI", "carrier": "AA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = FirstSegmentNotSurfaceRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_fix_suggestion_present(self):
        """Violation includes fix suggestion."""
        segs = [
            {"from": "SYD", "to": "AKL", "type": "surface"},
            {"from": "AKL", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "SYD", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs, origin="SYD")
        ctx = build_context(itin)
        results = FirstSegmentNotSurfaceRule().check(itin, ctx)
        violations = [r for r in results if not r.passed]
        assert len(violations) == 1
        assert violations[0].fix_suggestion is not None
        assert "flown segment" in violations[0].fix_suggestion.lower()

    def test_integration_full_validator(self):
        """Rule is registered and runs through full validator."""
        from rtw.validator import Validator

        segs = [
            {"from": "CAI", "to": "DOH", "type": "surface"},
            {"from": "DOH", "to": "HEL", "carrier": "AY"},
            {"from": "HEL", "to": "JFK", "carrier": "AY"},
            {"from": "JFK", "to": "HND", "carrier": "JL"},
            {"from": "HND", "to": "SYD", "carrier": "JL"},
            {"from": "SYD", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "CAI", "carrier": "QR", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        report = Validator().validate(itin)
        surface_results = [
            r for r in report.results if r.rule_id == "first_segment_not_surface"
        ]
        assert len(surface_results) == 1
        assert not surface_results[0].passed
