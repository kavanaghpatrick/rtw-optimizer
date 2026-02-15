"""Tests for TicketValidityRule — 10-365 day validity window."""

from rtw.models import Itinerary, Ticket, Segment, Severity
from rtw.rules.validity import TicketValidityRule
from rtw.validator import build_context


def _make_itinerary(segments_data, origin="CAI"):
    ticket = Ticket(type="DONE4", cabin="business", origin=origin)
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestTicketValidity:
    """TicketValidityRule: trip must be between 10 and 365 days inclusive."""

    def test_exactly_10_days_passes(self):
        """First date 2025-06-01, last date 2025-06-11: gap = 10 days.
        Boundary: exactly at the minimum."""
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "date": "2025-06-01", "type": "stopover"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "date": "2025-06-05", "type": "stopover"},
            {"from": "DOH", "to": "CAI", "carrier": "QR", "date": "2025-06-11", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TicketValidityRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_9_days_too_short(self):
        """First date 2025-06-01, last date 2025-06-10: gap = 9 days.
        Below the 10-day minimum."""
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "date": "2025-06-01", "type": "stopover"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "date": "2025-06-05", "type": "stopover"},
            {"from": "DOH", "to": "CAI", "carrier": "QR", "date": "2025-06-10", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TicketValidityRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        assert any(r.severity == Severity.VIOLATION for r in results)
        assert any("minimum is 10" in r.message for r in results)

    def test_exactly_365_days_passes(self):
        """First date 2025-01-01, last date 2025-12-31: gap = 364 days.
        Within the 365-day maximum (non-leap year)."""
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "date": "2025-01-01", "type": "stopover"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "date": "2025-06-15", "type": "stopover"},
            {"from": "DOH", "to": "CAI", "carrier": "QR", "date": "2025-12-31", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TicketValidityRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_366_days_too_long(self):
        """First date 2025-01-01, last date 2026-01-02: gap = 366 days.
        Exceeds the 365-day maximum."""
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "date": "2025-01-01", "type": "stopover"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "date": "2025-06-15", "type": "stopover"},
            {"from": "DOH", "to": "CAI", "carrier": "QR", "date": "2026-01-02", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TicketValidityRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        assert any(r.severity == Severity.VIOLATION for r in results)
        assert any("maximum is 365" in r.message for r in results)

    def test_180_days_happy_path(self):
        """Mid-range trip of ~180 days. Should pass easily."""
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "date": "2025-03-01", "type": "stopover"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "date": "2025-06-01", "type": "stopover"},
            {"from": "DOH", "to": "CAI", "carrier": "QR", "date": "2025-08-28", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TicketValidityRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_only_one_date_insufficient(self):
        """Only 1 segment has a date. Rule cannot compute duration,
        returns passed=True with INFO severity."""
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "date": "2025-06-01", "type": "stopover"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "type": "stopover"},
            {"from": "DOH", "to": "CAI", "carrier": "QR", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TicketValidityRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any(r.severity == Severity.INFO for r in results)
        assert any("Insufficient dates" in r.message for r in results)

    def test_no_dates_insufficient(self):
        """No dates on any segment. Same insufficient-dates path."""
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "type": "stopover"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "type": "stopover"},
            {"from": "DOH", "to": "CAI", "carrier": "QR", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TicketValidityRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any(r.severity == Severity.INFO for r in results)
        assert any("Insufficient dates" in r.message for r in results)

    def test_zero_days_same_date(self):
        """Both segments on the same date. Gap = 0 days, which is < 10."""
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "date": "2025-06-01", "type": "stopover"},
            {"from": "AMM", "to": "CAI", "carrier": "RJ", "date": "2025-06-01", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TicketValidityRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        assert any(r.severity == Severity.VIOLATION for r in results)

    def test_v3_fixture_passes(self, v3_itinerary):
        """The V3 reference itinerary should pass the validity check."""
        itin = Itinerary(**v3_itinerary)
        ctx = build_context(itin)
        results = TicketValidityRule().check(itin, ctx)
        assert all(r.passed for r in results)
