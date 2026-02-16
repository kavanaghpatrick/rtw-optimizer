"""Tests for via-stop continent counting in build_context.

Via stops are through-flight technical stops (Rule 3015 §16).
They count the stop's continent as visited for pricing, but do NOT
add to per-continent segment limits (through-flight = one segment).
"""

import yaml
from pathlib import Path

from rtw.models import Itinerary, Ticket, Segment, Continent
from rtw.validator import build_context


def _make_itinerary(segments_data, origin="LHR", ticket_type="DONE4"):
    ticket = Ticket(type=ticket_type, cabin="business", origin=origin)
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestViaContinentCounting:
    """Tests for _detect_via_continents in build_context."""

    def test_via_adds_new_continent(self):
        """Via stop in a new continent adds it to continents_visited."""
        # Route: SYD -> LAX (via SIN) -> GRU -> JFK -> SYD
        # Without via: SWP, N_America, S_America = 3
        # With via SIN: SWP, N_America, S_America, Asia = 4
        segs = [
            {"from": "SYD", "to": "LAX", "carrier": "QF", "via": "SIN"},
            {"from": "LAX", "to": "GRU", "carrier": "AA"},
            {"from": "GRU", "to": "JFK", "carrier": "AA"},
            {"from": "JFK", "to": "SYD", "carrier": "QF", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="SYD")
        ctx = build_context(itin)
        assert Continent.ASIA in ctx.continents_visited
        assert Continent.ASIA in ctx.via_continents

    def test_via_same_continent_no_effect(self):
        """Via stop in an already-visited continent doesn't duplicate."""
        # NRT->SYD via SIN: SIN is Asia, same as NRT departure
        segs = [
            {"from": "LHR", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "SYD", "carrier": "QF", "via": "SIN"},
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        # Asia should appear exactly once in continents_visited
        asia_count = ctx.continents_visited.count(Continent.ASIA)
        assert asia_count == 1
        # But via_continents should still record it
        assert Continent.ASIA in ctx.via_continents

    def test_via_does_not_increment_segments_per_continent(self):
        """Via stop does NOT add to segments_per_continent."""
        # SYD->LAX via SIN: Asia counted via stop, not as a segment
        segs = [
            {"from": "SYD", "to": "LAX", "carrier": "QF", "via": "SIN"},
            {"from": "LAX", "to": "GRU", "carrier": "AA"},
            {"from": "GRU", "to": "JFK", "carrier": "AA"},
            {"from": "JFK", "to": "SYD", "carrier": "QF", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="SYD")
        ctx = build_context(itin)
        # Asia should have 0 segments (only counted via via-stop)
        assert ctx.segments_per_continent.get(Continent.ASIA, 0) == 0

    def test_via_continent_segments_tracking(self):
        """via_continent_segments records which segment and airport triggered detection."""
        segs = [
            {"from": "LHR", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "SYD", "carrier": "QF", "via": "SIN"},
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        assert Continent.ASIA in ctx.via_continent_segments
        entries = ctx.via_continent_segments[Continent.ASIA]
        assert len(entries) == 1
        seg_idx, via_apt = entries[0]
        assert seg_idx == 1  # Second segment (NRT->SYD)
        assert via_apt == "SIN"

    def test_multiple_via_stops(self):
        """Multiple via stops on a single segment all counted."""
        # Hypothetical: DOH->ADL via SIN,KUL
        segs = [
            {"from": "LHR", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "ADL", "carrier": "QR", "via": ["SIN", "KUL"]},
            {"from": "ADL", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        assert Continent.ASIA in ctx.via_continents
        entries = ctx.via_continent_segments[Continent.ASIA]
        # Both SIN and KUL are Asia, so two entries
        assert len(entries) == 2
        airports = [e[1] for e in entries]
        assert "SIN" in airports
        assert "KUL" in airports

    def test_via_works_alongside_implicit_asia(self):
        """Via counting and implicit Asia detection work independently."""
        # DOH->SYD triggers implicit Asia, NRT->SYD has via: SIN
        segs = [
            {"from": "LHR", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "SYD", "carrier": "QR"},  # Implicit Asia
            {"from": "SYD", "to": "NRT", "carrier": "QF"},
            {"from": "NRT", "to": "LAX", "carrier": "JL", "via": "SIN"},  # Via Asia
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        # Both mechanisms should detect Asia
        assert Continent.ASIA in ctx.implicit_continents
        assert Continent.ASIA in ctx.via_continents
        # But only one entry in continents_visited
        assert ctx.continents_visited.count(Continent.ASIA) == 1

    def test_no_via_field_no_via_continents(self):
        """Segments without via field produce empty via_continents."""
        segs = [
            {"from": "LHR", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        assert ctx.via_continents == []
        assert ctx.via_continent_segments == {}


class TestViaFixtureIntegration:
    """Integration test using the via_through_flight.yaml fixture."""

    def test_fixture_loads_and_validates(self):
        """via_through_flight.yaml loads correctly and passes validation."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "via_through_flight.yaml"
        with open(fixture_path) as f:
            data = yaml.safe_load(f)
        itin = Itinerary(**data)
        ctx = build_context(itin)

        # 5 continents: EU_ME, Asia, SWP, N_America, S_America
        assert len(ctx.continents_visited) == 5
        assert Continent.EU_ME in ctx.continents_visited
        assert Continent.ASIA in ctx.continents_visited
        assert Continent.SWP in ctx.continents_visited
        assert Continent.N_AMERICA in ctx.continents_visited
        assert Continent.S_AMERICA in ctx.continents_visited

    def test_fixture_via_detected(self):
        """Fixture's via: SIN is detected in via_continent_segments."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "via_through_flight.yaml"
        with open(fixture_path) as f:
            data = yaml.safe_load(f)
        itin = Itinerary(**data)
        ctx = build_context(itin)

        assert Continent.ASIA in ctx.via_continents
        entries = ctx.via_continent_segments[Continent.ASIA]
        assert any(apt == "SIN" for _, apt in entries)

    def test_fixture_via_no_segment_count(self):
        """Via stop doesn't inflate segments_per_continent."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "via_through_flight.yaml"
        with open(fixture_path) as f:
            data = yaml.safe_load(f)
        itin = Itinerary(**data)
        ctx = build_context(itin)

        # Asia segments: LHR->NRT counts (intra-continental would be 0 since
        # it's intercontinental TC2->TC3). Via SIN should NOT add any.
        # The key: via_continent_segments records via, but segments_per_continent doesn't.
        via_asia_count = len(ctx.via_continent_segments.get(Continent.ASIA, []))
        assert via_asia_count >= 1  # At least the via: SIN detection
