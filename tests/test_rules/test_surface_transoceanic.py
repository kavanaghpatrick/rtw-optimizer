"""Tests for TransoceanicSurfaceRule."""

from rtw.models import Itinerary, Ticket, Segment, Severity
from rtw.rules.surface import TransoceanicSurfaceRule
from rtw.validator import build_context


def _make_itinerary(segments_data, origin="CAI"):
    ticket = Ticket(type="DONE4", cabin="business", origin=origin)
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestTransoceanicSurface:
    def test_jfk_surface_lhr_violation(self):
        """JFK-surface-LHR = TC1->TC2 surface = VIOLATION."""
        segs = [
            {"from": "CAI", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "LHR", "type": "surface"},  # Transoceanic!
            {"from": "LHR", "to": "CAI", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TransoceanicSurfaceRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1
        assert violations[0].segments_involved is not None

    def test_ist_surface_bkk_passes(self):
        """IST-surface-BKK = TC2->TC3 surface = NOT restricted, PASS."""
        segs = [
            {"from": "CAI", "to": "IST", "carrier": "TK"},
            {"from": "IST", "to": "BKK", "type": "surface"},  # TC2->TC3, allowed
            {"from": "BKK", "to": "NRT", "carrier": "JL"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TransoceanicSurfaceRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_swp_origin_one_exempt(self):
        """SWP origin + 1 transoceanic surface = WARNING (not violation)."""
        segs = [
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "JFK", "type": "surface"},  # TC1 internal, not transoceanic
            {"from": "JFK", "to": "LHR", "type": "surface"},  # TC1->TC2, transoceanic!
            {"from": "LHR", "to": "SYD", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs, origin="SYD")
        ctx = build_context(itin)
        results = TransoceanicSurfaceRule().check(itin, ctx)
        # Should be WARNING, not VIOLATION
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        warnings = [r for r in results if r.severity == Severity.WARNING]
        assert len(violations) == 0
        assert len(warnings) >= 1

    def test_swp_origin_two_violation(self):
        """SWP origin + 2 transoceanic surfaces = VIOLATION."""
        segs = [
            {"from": "SYD", "to": "LAX", "type": "surface"},  # TC3->TC1, transoceanic
            {"from": "LAX", "to": "LHR", "type": "surface"},  # TC1->TC2, transoceanic
            {"from": "LHR", "to": "SYD", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs, origin="SYD")
        ctx = build_context(itin)
        results = TransoceanicSurfaceRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1

    def test_flown_tc1_tc2_not_affected(self):
        """Flown JFK->LHR = not a surface sector, not affected."""
        segs = [
            {"from": "CAI", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "LHR", "carrier": "BA"},  # Flown, not surface
            {"from": "LHR", "to": "CAI", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TransoceanicSurfaceRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_tc2_tc3_surface_passes(self):
        """TC2<->TC3 surface = NOT restricted."""
        segs = [
            {"from": "CAI", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "NRT", "type": "surface"},  # TC2->TC3, allowed
            {"from": "NRT", "to": "SYD", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TransoceanicSurfaceRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_tc1_tc3_surface_violation(self):
        """LAX-surface-NRT = TC1->TC3 (Pacific) = VIOLATION."""
        segs = [
            {"from": "CAI", "to": "LAX", "carrier": "BA"},
            {"from": "LAX", "to": "NRT", "type": "surface"},  # TC1->TC3, transoceanic!
            {"from": "NRT", "to": "LHR", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TransoceanicSurfaceRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1

    def test_no_surface_sectors_passes(self):
        """No surface sectors at all = PASS."""
        segs = [
            {"from": "CAI", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "LHR", "carrier": "BA"},
            {"from": "LHR", "to": "CAI", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TransoceanicSurfaceRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("No transoceanic" in r.message for r in results)

    def test_segments_involved_populated(self):
        """segments_involved has correct indices for transoceanic surface."""
        segs = [
            {"from": "CAI", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "LHR", "type": "surface"},  # index 1, transoceanic
            {"from": "LHR", "to": "CAI", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TransoceanicSurfaceRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert violations[0].segments_involved == [1]
