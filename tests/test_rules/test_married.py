"""Tests for MarriedSegmentRule — CX hub-connection and through-flight split detection."""

from rtw.models import Itinerary, Ticket, Segment, Severity
from rtw.rules.married import MarriedSegmentRule


def _make_itinerary(segments_data, origin="LHR", ticket_type="DONE4"):
    ticket = Ticket(type=ticket_type, cabin="business", origin=origin)
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestCXHubConnection:
    def test_cx_not_through_hkg_warns(self):
        """CX NRT-SIN (neither is HKG) triggers married segment INFO."""
        segs = [
            {"from": "LHR", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "SIN", "carrier": "CX"},  # Neither is HKG
            {"from": "SIN", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        results = MarriedSegmentRule().check(itin, None)
        info = [r for r in results if not r.passed and r.severity == Severity.INFO]
        assert len(info) >= 1
        assert "CX" in info[0].message
        assert "HKG" in info[0].message

    def test_cx_through_hkg_no_warning(self):
        """CX HKG-SYD (one endpoint is HKG) does NOT trigger warning."""
        segs = [
            {"from": "LHR", "to": "HKG", "carrier": "CX"},
            {"from": "HKG", "to": "SYD", "carrier": "CX"},  # HKG is endpoint
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        results = MarriedSegmentRule().check(itin, None)
        cx_warnings = [r for r in results if not r.passed and "CX" in r.message]
        assert len(cx_warnings) == 0

    def test_multiple_cx_segments(self):
        """Multiple CX segments not through HKG produce multiple warnings."""
        segs = [
            {"from": "LHR", "to": "NRT", "carrier": "CX"},  # Neither is HKG
            {"from": "NRT", "to": "SIN", "carrier": "CX"},  # Neither is HKG
            {"from": "SIN", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        results = MarriedSegmentRule().check(itin, None)
        cx_warnings = [r for r in results if not r.passed and "CX" in r.message]
        assert len(cx_warnings) == 2


class TestThroughFlightSplit:
    def test_via_stop_city_as_stopover_warns(self):
        """Via SIN + SIN as stopover destination triggers split warning."""
        segs = [
            {"from": "LHR", "to": "SIN", "carrier": "BA"},  # Stopover in SIN
            {"from": "SIN", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "LAX", "carrier": "QF", "via": "SIN"},  # Via SIN!
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        results = MarriedSegmentRule().check(itin, None)
        split_warnings = [r for r in results if not r.passed and "through-flight" in r.message]
        assert len(split_warnings) == 1
        assert "SIN" in split_warnings[0].message

    def test_via_stop_no_matching_stopover_ok(self):
        """Via SIN but no SIN stopover elsewhere — no split warning."""
        segs = [
            {"from": "LHR", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "SYD", "carrier": "QF", "via": "SIN"},
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        results = MarriedSegmentRule().check(itin, None)
        split_warnings = [r for r in results if not r.passed and "through-flight" in r.message]
        assert len(split_warnings) == 0


class TestNoIssues:
    def test_no_cx_no_via_passes(self):
        """No CX and no via fields — clean pass."""
        segs = [
            {"from": "LHR", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        results = MarriedSegmentRule().check(itin, None)
        assert len(results) == 1
        assert results[0].passed is True
        assert "No married segment risks" in results[0].message
