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

    def test_hawaii_reentry_fixture_still_fails(self, hawaii_backtrack_itinerary):
        itin = Itinerary(**hawaii_backtrack_itinerary)
        ctx = build_context(itin)
        results = HawaiiAlaskaRule().check(itin, ctx)
        assert any(
            not r.passed and "after leaving" in r.message for r in results
        )


def _hawaii_results(route, origin="LHR"):
    """Run HawaiiAlaskaRule on a dash-separated airport route."""
    codes = route.split("-")
    segs = [
        Segment(**{"from": a, "to": b, "carrier": "AA"})
        for a, b in zip(codes, codes[1:])
    ]
    itin = Itinerary(
        ticket=Ticket(type="DONE4", cabin="business", origin=origin), segments=segs
    )
    return HawaiiAlaskaRule().check(itin, build_context(itin))


class TestHawaiiSideTrip:
    """Rule 3015 §5: no backtracking between Hawaii and other North America points."""

    def test_mainland_hawaii_mainland_fails(self):
        results = _hawaii_results("LAX-HNL-SFO", origin="LAX")
        assert any(not r.passed and "side trip" in r.message for r in results)

    def test_side_trip_with_interisland_hop_fails(self):
        results = _hawaii_results("LAX-HNL-OGG-SFO", origin="LAX")
        failures = [r for r in results if not r.passed]
        assert len(failures) == 1
        assert "side trip" in failures[0].message
        assert failures[0].segments_involved == [0, 1, 2]

    def test_full_rtw_with_hawaii_side_trip_fails(self):
        results = _hawaii_results("LHR-JFK-LAX-HNL-SFO-NRT-HKG-LHR")
        assert any(not r.passed and "side trip" in r.message for r in results)

    def test_canada_or_alaska_side_trip_fails(self):
        assert any(not r.passed for r in _hawaii_results("YVR-HNL-ANC", origin="YVR"))

    def test_asia_to_hawaii_to_mainland_passes(self):
        results = _hawaii_results("NRT-HNL-LAX", origin="NRT")
        assert all(r.passed for r in results)

    def test_mainland_to_hawaii_to_asia_passes(self):
        results = _hawaii_results("LAX-HNL-NRT", origin="LAX")
        assert all(r.passed for r in results)

    def test_na_origin_home_via_hawaii_passes(self):
        # Starts in North America, returns home via Hawaii: the first and last
        # mainland stops are separated by other continents, not a side trip.
        results = _hawaii_results("LAX-LHR-DOH-HKG-NRT-HNL-LAX", origin="LAX")
        assert all(r.passed for r in results)

    def test_interisland_within_transpacific_passes(self):
        results = _hawaii_results("NRT-HNL-OGG-LAX", origin="NRT")
        assert all(r.passed for r in results)


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
