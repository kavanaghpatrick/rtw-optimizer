"""Tests for data-integrity validation rules (origin match, date sequence)."""

from rtw.models import Itinerary, Ticket, Segment, Severity
from rtw.rules.validity import OriginMatchesFirstSegmentRule, DateSequenceRule
from rtw.validator import build_context


def _make_itinerary(segments_data, origin="CAI"):
    ticket = Ticket(type="DONE4", cabin="business", origin=origin)
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestOriginMatchesFirstSegment:
    def test_origin_matches_passes(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            {"from": "AMM", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "CAI", "carrier": "QR"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = OriginMatchesFirstSegmentRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_same_city_group_passes(self):
        # NRT and HND are both in the TYO same-city group
        segs = [
            {"from": "HND", "to": "SIN", "carrier": "JL"},
            {"from": "SIN", "to": "NRT", "carrier": "JL"},
        ]
        itin = _make_itinerary(segs, origin="NRT")
        ctx = build_context(itin)
        results = OriginMatchesFirstSegmentRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_mismatch_warns(self):
        segs = [
            {"from": "JFK", "to": "LAX", "carrier": "AA"},
            {"from": "LAX", "to": "JFK", "carrier": "AA"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = OriginMatchesFirstSegmentRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        assert any(r.severity == Severity.WARNING for r in results)

    def test_no_segments_passes(self):
        # Bypass Pydantic min_length=1 validation using model_construct
        ticket = Ticket(type="DONE4", cabin="business", origin="CAI")
        itin = Itinerary.model_construct(ticket=ticket, segments=[])
        ctx = build_context(itin)
        results = OriginMatchesFirstSegmentRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert "No segments" in results[0].message

    def test_v3_passes(self, v3_itinerary):
        itin = Itinerary(**v3_itinerary)
        ctx = build_context(itin)
        results = OriginMatchesFirstSegmentRule().check(itin, ctx)
        assert all(r.passed for r in results)


class TestDateSequence:
    def test_chronological_passes(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "date": "2026-03-01"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "date": "2026-03-15"},
            {"from": "DOH", "to": "CAI", "carrier": "QR", "date": "2026-04-01"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = DateSequenceRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_out_of_order_fails(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "date": "2026-03-15"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "date": "2026-03-01"},
            {"from": "DOH", "to": "CAI", "carrier": "QR", "date": "2026-04-01"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = DateSequenceRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        assert any(r.severity == Severity.VIOLATION for r in results)

    def test_same_date_passes(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "date": "2026-03-15"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "date": "2026-03-15"},
            {"from": "DOH", "to": "CAI", "carrier": "QR", "date": "2026-04-01"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = DateSequenceRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_single_date_insufficient(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "date": "2026-03-01"},
            {"from": "AMM", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "CAI", "carrier": "QR"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = DateSequenceRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any(r.severity == Severity.INFO for r in results)
        assert "Insufficient dates" in results[0].message

    def test_no_dates_insufficient(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            {"from": "AMM", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "CAI", "carrier": "QR"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = DateSequenceRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any(r.severity == Severity.INFO for r in results)
        assert "Insufficient dates" in results[0].message

    def test_multiple_violations(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "date": "2026-04-01"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "date": "2026-03-01"},
            {"from": "DOH", "to": "CAI", "carrier": "QR", "date": "2026-02-01"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = DateSequenceRule().check(itin, ctx)
        failed = [r for r in results if not r.passed]
        assert len(failed) == 2
        assert all(r.severity == Severity.VIOLATION for r in failed)
