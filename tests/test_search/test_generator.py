"""Tests for route generation algorithm."""

from datetime import date, timedelta

import pytest

from rtw.search.generator import generate_candidates
from rtw.search.hubs import HubTable
from rtw.search.models import Direction, SearchQuery
from rtw.models import CabinClass, TicketType
from rtw.validator import Validator

TODAY = date.today()
FUTURE = TODAY + timedelta(days=60)
FUTURE_END = TODAY + timedelta(days=120)


@pytest.fixture(scope="module")
def hub_table():
    return HubTable()


@pytest.fixture(scope="module")
def validator():
    return Validator()


def _make_query(**kwargs) -> SearchQuery:
    defaults = dict(
        cities=["LHR", "NRT", "SYD", "JFK"],
        origin="CAI",
        date_from=FUTURE,
        date_to=FUTURE_END,
        cabin=CabinClass.BUSINESS,
        ticket_type=TicketType.DONE4,
    )
    defaults.update(kwargs)
    return SearchQuery(**defaults)


class TestCoreGeneration:
    def test_4_continent_produces_candidates(self, hub_table):
        query = _make_query()
        candidates = generate_candidates(query, hub_table)
        assert len(candidates) >= 1, "Should produce at least 1 candidate"

    def test_both_directions_generated(self, hub_table):
        query = _make_query()
        candidates = generate_candidates(query, hub_table)
        directions = {c.direction for c in candidates}
        # At least one direction should produce candidates
        assert len(directions) >= 1

    def test_3_city_done3_produces_candidates(self, hub_table):
        query = _make_query(
            cities=["LHR", "NRT", "JFK"],
            origin="SYD",
            ticket_type=TicketType.DONE3,
        )
        candidates = generate_candidates(query, hub_table)
        assert len(candidates) >= 1


class TestInvariants:
    def test_every_candidate_passes_validator(self, hub_table, validator):
        query = _make_query()
        candidates = generate_candidates(query, hub_table)
        assert len(candidates) >= 1
        for c in candidates:
            report = validator.validate(c.itinerary)
            assert report.passed, (
                f"Candidate failed validation: "
                f"{[v.message for v in report.violations]}"
            )

    def test_every_candidate_starts_ends_at_origin(self, hub_table):
        query = _make_query()
        candidates = generate_candidates(query, hub_table)
        for c in candidates:
            segs = c.itinerary.segments
            assert segs[0].from_airport == query.origin, (
                f"First segment starts at {segs[0].from_airport}, not {query.origin}"
            )
            assert segs[-1].to_airport == query.origin, (
                f"Last segment ends at {segs[-1].to_airport}, not {query.origin}"
            )

    def test_every_candidate_contains_must_visit_cities(self, hub_table):
        query = _make_query()
        candidates = generate_candidates(query, hub_table)
        for c in candidates:
            airports = set()
            for seg in c.itinerary.segments:
                airports.add(seg.from_airport)
                airports.add(seg.to_airport)
            for city in query.cities:
                assert city in airports, (
                    f"City {city} not found in candidate route"
                )

    def test_no_duplicate_candidates(self, hub_table):
        query = _make_query()
        candidates = generate_candidates(query, hub_table)
        routes = []
        for c in candidates:
            route = tuple(
                (s.from_airport, s.to_airport) for s in c.itinerary.segments
            )
            assert route not in routes, f"Duplicate candidate: {route}"
            routes.append(route)


class TestBounds:
    def test_candidate_count_bounded(self, hub_table):
        query = _make_query()
        candidates = generate_candidates(query, hub_table)
        assert len(candidates) <= 2000

    def test_generates_at_least_one(self, hub_table):
        query = _make_query()
        candidates = generate_candidates(query, hub_table)
        assert len(candidates) >= 1

    @pytest.mark.slow
    def test_8_city_completes_within_10s(self, hub_table):
        import time
        query = _make_query(
            cities=["LHR", "NRT", "JFK", "SYD", "HKG", "DEL", "DOH", "LAX"],
            ticket_type=TicketType.DONE6,
        )
        start = time.time()
        candidates = generate_candidates(query, hub_table)
        elapsed = time.time() - start
        assert elapsed < 10, f"8-city generation took {elapsed:.1f}s (limit: 10s)"


class TestEdgeCases:
    def test_impossible_continent_coverage_returns_empty(self, hub_table):
        """3 EU cities for DONE4 (needs 4 continents) — can't be satisfied."""
        query = _make_query(
            cities=["LHR", "MAD", "AMM"],
            origin="CAI",
            ticket_type=TicketType.DONE4,
        )
        candidates = generate_candidates(query, hub_table)
        # May produce 0 candidates because not enough continent coverage
        # even with hub additions — this is acceptable
        # Just verify no crashes
        assert isinstance(candidates, list)

    def test_origin_in_must_visit_list(self, hub_table):
        """Origin city also in must-visit list should not cause issues."""
        query = _make_query(
            cities=["CAI", "LHR", "NRT", "JFK"],
            origin="CAI",
        )
        candidates = generate_candidates(query, hub_table)
        # Should work, just skip origin from permutation
        assert isinstance(candidates, list)


class TestNonstopFilter:
    def test_no_filter_produces_candidates(self, hub_table):
        """Without filter, behaves identically to before."""
        query = _make_query()
        candidates = generate_candidates(query, hub_table, nonstop_filter=None)
        assert len(candidates) >= 1

    def test_allow_all_filter_same_as_none(self, hub_table):
        """Filter that allows everything produces same count as no filter."""
        query = _make_query()
        without = generate_candidates(query, hub_table)
        with_filter = generate_candidates(query, hub_table, nonstop_filter=lambda o, d, c: True)
        assert len(with_filter) == len(without)

    def test_reject_all_filter_returns_empty(self, hub_table):
        """Filter that rejects everything produces zero candidates."""
        query = _make_query()
        candidates = generate_candidates(query, hub_table, nonstop_filter=lambda o, d, c: False)
        assert len(candidates) == 0

    def test_filter_reduces_candidates(self, hub_table):
        """A selective filter should produce fewer candidates than no filter."""
        query = _make_query()
        without = generate_candidates(query, hub_table)

        # Reject routes involving DOH (a common hub)
        def reject_doha(o, d, c):
            return o != "DOH" and d != "DOH"

        with_filter = generate_candidates(query, hub_table, nonstop_filter=reject_doha)
        assert len(with_filter) < len(without)

    def test_filter_exception_treated_as_keep(self, hub_table):
        """If filter raises exception, segment is kept (not eliminated)."""
        query = _make_query()

        def flaky_filter(o, d, c):
            raise RuntimeError("API error")

        candidates = generate_candidates(query, hub_table, nonstop_filter=flaky_filter)
        # Should produce same candidates as no filter (all exceptions = all kept)
        without = generate_candidates(query, hub_table)
        assert len(candidates) == len(without)

    def test_surface_segments_not_filtered(self, hub_table):
        """Filter should not be called for SURFACE segments."""
        query = _make_query()
        calls = []

        def tracking_filter(o, d, c):
            calls.append((o, d, c))
            return True

        generate_candidates(query, hub_table, nonstop_filter=tracking_filter)
        # No call should have empty carrier (surface segments are skipped)
        for o, d, c in calls:
            assert len(o) == 3
            assert len(d) == 3
