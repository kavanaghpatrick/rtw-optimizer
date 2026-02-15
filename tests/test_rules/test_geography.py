"""Tests for geography rules."""

from rtw.models import Itinerary, Ticket, Segment
from rtw.rules.geography import HawaiiAlaskaRule, TranscontinentalUSRule
from rtw.validator import build_context


def _make_itinerary(segments_data):
    ticket = Ticket(type="DONE4", cabin="business", origin="CAI")
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestHawaiiAlaska:
    def test_v3_passes(self, v3_itinerary):
        itin = Itinerary(**v3_itinerary)
        ctx = build_context(itin)
        results = HawaiiAlaskaRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_hawaii_backtrack_fails(self):
        segs = [
            {"from": "LAX", "to": "HNL", "carrier": "AA"},
            {"from": "HNL", "to": "LAX", "carrier": "AA"},
            {"from": "LAX", "to": "HNL", "carrier": "AA"},  # Backtrack!
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = HawaiiAlaskaRule().check(itin, ctx)
        assert any(not r.passed for r in results)


class TestTranscontinentalUS:
    def test_v3_passes(self, v3_itinerary):
        itin = Itinerary(**v3_itinerary)
        ctx = build_context(itin)
        results = TranscontinentalUSRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_two_transcon_fails(self):
        segs = [
            {"from": "JFK", "to": "LAX", "carrier": "AA"},
            {"from": "LAX", "to": "JFK", "carrier": "AA"},  # 2nd transcon
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TranscontinentalUSRule().check(itin, ctx)
        assert any(not r.passed for r in results)


class TestAlaskaFlightLimits:
    def test_one_to_one_from_alaska_passes(self):
        segs = [
            {"from": "SEA", "to": "ANC", "carrier": "AA"},  # 1 to Alaska
            {"from": "ANC", "to": "SEA", "carrier": "AA"},  # 1 from Alaska
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = HawaiiAlaskaRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_two_flights_to_alaska_fails(self):
        segs = [
            {"from": "SEA", "to": "ANC", "carrier": "AA"},
            {"from": "ANC", "to": "SEA", "carrier": "AA"},
            {"from": "SEA", "to": "FAI", "carrier": "AA"},  # 2nd to Alaska!
            {"from": "FAI", "to": "SEA", "carrier": "AA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = HawaiiAlaskaRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        assert any("TO Alaska" in r.message for r in results)

    def test_two_flights_from_alaska_fails(self):
        segs = [
            {"from": "SEA", "to": "ANC", "carrier": "AA"},
            {"from": "ANC", "to": "SEA", "carrier": "AA"},
            {"from": "LAX", "to": "ANC", "carrier": "AA"},
            {"from": "ANC", "to": "LAX", "carrier": "AA"},  # 2nd from Alaska
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = HawaiiAlaskaRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        assert any("FROM Alaska" in r.message for r in results)

    def test_no_alaska_segments_passes(self):
        segs = [
            {"from": "JFK", "to": "LAX", "carrier": "AA"},
            {"from": "LAX", "to": "JFK", "carrier": "AA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = HawaiiAlaskaRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_surface_to_alaska_not_counted(self):
        segs = [
            {"from": "SEA", "to": "ANC", "type": "surface"},  # Surface — not counted as flown
            {"from": "ANC", "to": "SEA", "carrier": "AA"},    # 1 from Alaska (flown)
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = HawaiiAlaskaRule().check(itin, ctx)
        # Surface to ANC not counted as flown, so to_alaska=0, from_alaska=1
        assert all(r.passed for r in results)
