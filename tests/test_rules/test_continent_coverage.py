"""Tests for UnknownContinentRule and unknown-continent tracking in build_context."""

from rtw.models import Continent, Itinerary, Segment, Severity, Ticket
from rtw.rules.continent_coverage import UnknownContinentRule
from rtw.validator import Validator, build_context


def _itin(segs, origin="LHR", ticket_type="DONE3"):
    ticket = Ticket(type=ticket_type, cabin="business", origin=origin)
    return Itinerary(ticket=ticket, segments=[Segment(**s) for s in segs])


# GOH (Nuuk, Greenland) is a real airport whose country is deliberately
# unmapped: the rule text does not say which continent Greenland belongs to.
_GREENLAND_TRIP = [
    {"from": "LHR", "to": "GOH", "carrier": "BA"},
    {"from": "GOH", "to": "JFK", "carrier": "AA"},
    {"from": "JFK", "to": "HKG", "carrier": "CX"},
    {"from": "HKG", "to": "LHR", "carrier": "CX"},
]


class TestUnknownContinentContext:
    def test_known_itinerary_has_no_unknowns(self):
        itin = _itin([
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "HKG", "carrier": "CX"},
            {"from": "HKG", "to": "LHR", "carrier": "CX"},
        ])
        assert build_context(itin).unknown_continent_airports == {}

    def test_unknown_airport_recorded_with_segments(self):
        ctx = build_context(_itin(_GREENLAND_TRIP))
        assert ctx.unknown_continent_airports == {"GOH": [0, 1]}

    def test_unknown_destination_not_borrowed_from_origin(self):
        """LHR-GOH must not be counted as an intra-Europe segment."""
        ctx = build_context(_itin(_GREENLAND_TRIP))
        assert ctx.segment_continents[0] is None
        assert ctx.segments_per_continent.get(Continent.EU_ME, 0) == 0

    def test_unknown_origin_recorded(self):
        itin = _itin(
            [
                {"from": "GOH", "to": "JFK", "carrier": "AA"},
                {"from": "JFK", "to": "LHR", "carrier": "BA"},
                {"from": "LHR", "to": "GOH", "carrier": "BA"},
            ],
            origin="GOH",
        )
        ctx = build_context(itin)
        assert ctx.origin_continent is None
        assert ctx.unknown_continent_airports["GOH"] == [-1, 0, 2]


class TestUnknownContinentRule:
    def test_passes_when_all_known(self):
        itin = _itin([
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "HKG", "carrier": "CX"},
            {"from": "HKG", "to": "LHR", "carrier": "CX"},
        ])
        results = UnknownContinentRule().check(itin, build_context(itin))
        assert len(results) == 1 and results[0].passed

    def test_violation_for_unknown_airport(self):
        itin = _itin(_GREENLAND_TRIP)
        results = UnknownContinentRule().check(itin, build_context(itin))
        assert len(results) == 1
        r = results[0]
        assert not r.passed
        assert r.severity == Severity.VIOLATION
        assert "Unknown continent for GOH" in r.message
        assert "segment 1" in r.message and "segment 2" in r.message
        assert r.segments_involved == [0, 1]

    def test_full_validator_fails_itinerary_with_unknown_airport(self):
        report = Validator().validate(_itin(_GREENLAND_TRIP))
        assert not report.passed
        assert any(v.rule_id == "unknown_continent" for v in report.violations)
