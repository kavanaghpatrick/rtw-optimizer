"""Tests for direction and ocean crossing rules."""

from rtw.models import Itinerary, Ticket, Segment
from rtw.rules.direction import DirectionOfTravelRule, OceanCrossingRule
from rtw.validator import build_context


def _make_itinerary(segments_data):
    ticket = Ticket(type="DONE4", cabin="business", origin="CAI")
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestDirectionOfTravel:
    def test_v3_eastbound_passes(self, v3_itinerary):
        itin = Itinerary(**v3_itinerary)
        ctx = build_context(itin)
        results = DirectionOfTravelRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("eastbound" in r.message for r in results)


class TestOceanCrossings:
    def test_v3_both_crossings(self, v3_itinerary):
        itin = Itinerary(**v3_itinerary)
        ctx = build_context(itin)
        results = OceanCrossingRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_missing_pacific(self):
        # Only Atlantic crossing, no Pacific
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            {"from": "AMM", "to": "JFK", "carrier": "QR"},  # TC2->TC1 Atlantic
            {"from": "JFK", "to": "LHR", "carrier": "BA"},  # TC1->TC2 Atlantic (2nd!)
            {"from": "LHR", "to": "CAI", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = OceanCrossingRule().check(itin, ctx)
        pacific_results = [r for r in results if "Pacific" in r.message]
        assert any(not r.passed for r in pacific_results)

    def test_surface_crossing_not_counted(self):
        # Surface sector across ocean should not count
        segs = [
            {"from": "CAI", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "NRT", "carrier": "QR"},  # TC2->TC3
            {"from": "NRT", "to": "LAX", "type": "surface"},  # Pacific but surface!
            {"from": "LAX", "to": "LHR", "carrier": "BA"},  # TC1->TC2 Atlantic
            {"from": "LHR", "to": "CAI", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = OceanCrossingRule().check(itin, ctx)
        pacific_results = [r for r in results if "Pacific" in r.message]
        assert any(not r.passed for r in pacific_results)


class TestDirectionOfTravelExpanded:
    def test_westbound_passes(self):
        # TC2->TC1->TC3->TC2 = westbound
        segs = [
            {"from": "CAI", "to": "LHR", "carrier": "BA"},         # TC2 intra
            {"from": "LHR", "to": "JFK", "carrier": "BA"},         # TC2->TC1
            {"from": "JFK", "to": "LAX", "carrier": "AA"},         # TC1 intra
            {"from": "LAX", "to": "NRT", "carrier": "JL"},         # TC1->TC3
            {"from": "NRT", "to": "SIN", "carrier": "JL"},         # TC3 intra
            {"from": "SIN", "to": "DOH", "carrier": "QR"},         # TC3->TC2
            {"from": "DOH", "to": "CAI", "carrier": "QR"},         # TC2 intra
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = DirectionOfTravelRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("westbound" in r.message for r in results)

    def test_eastbound_reversal_fails(self):
        # Start eastbound (TC2->TC3), then reverse (TC3->TC2)
        segs = [
            {"from": "CAI", "to": "DOH", "carrier": "QR"},        # TC2 intra
            {"from": "DOH", "to": "NRT", "carrier": "QR"},        # TC2->TC3 (eastbound)
            {"from": "NRT", "to": "SIN", "carrier": "JL"},        # TC3 intra
            {"from": "SIN", "to": "LHR", "carrier": "BA"},        # TC3->TC2 (REVERSAL for eastbound!)
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = DirectionOfTravelRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        assert any("reversal" in r.message.lower() for r in results)

    def test_single_tc_zone_passes(self):
        # All within TC2
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            {"from": "AMM", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "LHR", "carrier": "QR"},
            {"from": "LHR", "to": "CAI", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = DirectionOfTravelRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_insufficient_tc_transitions(self):
        # Only 1 segment, no TC transitions possible
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = DirectionOfTravelRule().check(itin, ctx)
        assert all(r.passed for r in results)


class TestOceanCrossingsExpanded:
    def test_two_pacific_crossings_fails(self):
        segs = [
            {"from": "LHR", "to": "JFK", "carrier": "BA"},        # TC2->TC1 Atlantic
            {"from": "JFK", "to": "NRT", "carrier": "JL"},        # TC1->TC3 Pacific #1
            {"from": "NRT", "to": "SYD", "carrier": "QF"},        # TC3 intra
            {"from": "SYD", "to": "LAX", "carrier": "QF"},        # TC3->TC1 Pacific #2!
            {"from": "LAX", "to": "LHR", "carrier": "BA"},        # TC1->TC2 Atlantic #2
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = OceanCrossingRule().check(itin, ctx)
        pacific_fails = [r for r in results if not r.passed and "Pacific" in r.message]
        assert len(pacific_fails) >= 1

    def test_two_atlantic_crossings_fails(self):
        segs = [
            {"from": "LHR", "to": "JFK", "carrier": "BA"},        # TC2->TC1 Atlantic #1
            {"from": "JFK", "to": "LHR", "carrier": "BA"},        # TC1->TC2 Atlantic #2
            {"from": "LHR", "to": "NRT", "carrier": "BA"},        # TC2->TC3
            {"from": "NRT", "to": "LAX", "carrier": "JL"},        # TC3->TC1 Pacific
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = OceanCrossingRule().check(itin, ctx)
        atlantic_fails = [r for r in results if not r.passed and "Atlantic" in r.message]
        assert len(atlantic_fails) >= 1

    def test_no_crossings_at_all_fails(self):
        # All within TC2
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            {"from": "AMM", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "LHR", "carrier": "QR"},
            {"from": "LHR", "to": "CAI", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = OceanCrossingRule().check(itin, ctx)
        fails = [r for r in results if not r.passed]
        assert len(fails) >= 2  # Both Pacific and Atlantic missing

    def test_missing_atlantic_only(self):
        # Only Pacific, no Atlantic
        segs = [
            {"from": "NRT", "to": "SIN", "carrier": "JL"},        # TC3 intra
            {"from": "SIN", "to": "SYD", "carrier": "QF"},        # TC3 intra
            {"from": "SYD", "to": "LAX", "carrier": "QF"},        # TC3->TC1 Pacific
            {"from": "LAX", "to": "NRT", "carrier": "JL"},        # TC1->TC3 Pacific #2
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = OceanCrossingRule().check(itin, ctx)
        atlantic_fails = [r for r in results if not r.passed and "Atlantic" in r.message]
        assert len(atlantic_fails) >= 1
