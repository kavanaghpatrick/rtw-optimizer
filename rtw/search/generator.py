"""Route generation algorithm for RTW itinerary search.

Generates valid oneworld Explorer itinerary skeletons by:
1. Grouping must-visit cities by tariff conference
2. Determining TC traversal order (eastbound/westbound)
3. Permuting cities within TC slots
4. Inserting hub connections between TCs
5. Validating each candidate through the rule engine
"""

from __future__ import annotations

import itertools
import logging
from typing import Callable, Optional

from rtw.continents import get_continent
from rtw.models import (
    CONTINENT_TO_TC,
    CabinClass,
    Continent,
    Itinerary,
    Segment,
    SegmentType,
    TariffConference,
    Ticket,
)
from rtw.search.hubs import HubTable
from rtw.search.models import CandidateItinerary, Direction, RouteSegment, SearchQuery
from rtw.validator import Validator

logger = logging.getLogger(__name__)

_MAX_CANDIDATES_PER_DIRECTION = 1000

# TC traversal orders by origin TC
_EASTBOUND_ORDERS = {
    TariffConference.TC1: [TariffConference.TC1, TariffConference.TC2, TariffConference.TC3, TariffConference.TC1],
    TariffConference.TC2: [TariffConference.TC2, TariffConference.TC3, TariffConference.TC1, TariffConference.TC2],
    TariffConference.TC3: [TariffConference.TC3, TariffConference.TC1, TariffConference.TC2, TariffConference.TC3],
}

_WESTBOUND_ORDERS = {
    TariffConference.TC1: [TariffConference.TC1, TariffConference.TC3, TariffConference.TC2, TariffConference.TC1],
    TariffConference.TC2: [TariffConference.TC2, TariffConference.TC1, TariffConference.TC3, TariffConference.TC2],
    TariffConference.TC3: [TariffConference.TC3, TariffConference.TC2, TariffConference.TC1, TariffConference.TC3],
}


def _get_tc(airport: str) -> Optional[TariffConference]:
    """Get tariff conference for an airport."""
    cont = get_continent(airport)
    if cont:
        return CONTINENT_TO_TC[cont]
    return None


def _group_cities_by_tc(
    cities: list[str],
) -> dict[TariffConference, list[str]]:
    """Group cities by their tariff conference."""
    groups: dict[TariffConference, list[str]] = {
        TariffConference.TC1: [],
        TariffConference.TC2: [],
        TariffConference.TC3: [],
    }
    for city in cities:
        tc = _get_tc(city)
        if tc:
            groups[tc].append(city)
    return groups


# Where must-visit cities in the origin's tariff conference go: at the start
# of the journey (right after leaving origin) or at the end (just before
# returning). Index 0 = cities on the origin's own continent (e.g. MAD for
# LHR), index 1 = cities on the other continent in that conference (e.g. JNB
# for LHR, LIM for JFK).
_HEAD = "head"
_TAIL = "tail"
_ORIGIN_TC_LAYOUTS: list[tuple[str, str]] = [
    (own, other) for own in (_HEAD, _TAIL) for other in (_HEAD, _TAIL)
]


def _split_origin_tc_cities(
    origin: str,
    cities: tuple[str, ...],
    layout: tuple[str, str],
) -> tuple[list[str], list[str]]:
    """Split origin-TC must-visit cities into (head, tail) legs by continent.

    Cities on the origin's own continent and cities on the other continent of
    the same tariff conference form separate slots, each placed at the head or
    tail of the journey per ``layout``. When both share the head, the origin
    continent comes first; when both share the tail, it comes last, so the
    trip leaves and re-enters the origin continent only once.
    """
    origin_cont = get_continent(origin)
    own = [c for c in cities if get_continent(c) == origin_cont]
    other = [c for c in cities if get_continent(c) != origin_cont]
    own_pos, other_pos = layout
    head = (own if own_pos == _HEAD else []) + (other if other_pos == _HEAD else [])
    tail = (other if other_pos == _TAIL else []) + (own if own_pos == _TAIL else [])
    return head, tail


def _build_route(
    origin: str,
    tc_order: list[TariffConference],
    city_groups: dict[TariffConference, list[str]],
    city_permutation: dict[TariffConference, tuple[str, ...]],
    hub_table: HubTable,
    origin_tc_layout: tuple[str, str] = (_HEAD, _HEAD),
) -> Optional[tuple[list[str], int]]:
    """Build a connected route from origin through TC order.

    Must-visit cities in the origin's own tariff conference are placed as a
    head leg (after leaving origin) and/or tail leg (before returning), split
    by continent according to ``origin_tc_layout``.

    Returns (airport_sequence, hub_count) or None if no valid connection exists.
    """
    route = [origin]
    hub_count = 0

    origin_tc = tc_order[0]
    head, tail = _split_origin_tc_cities(
        origin, tuple(city_permutation.get(origin_tc, ())), origin_tc_layout
    )

    # Travel order: head leg (origin TC), middle TCs, tail leg (origin TC).
    # tc_order is like [TC2, TC3, TC1, TC2] — the middle TCs skip first/last.
    legs: list[tuple[TariffConference, list[str]]] = [(origin_tc, head)]
    legs += [(tc, list(city_permutation.get(tc, ()))) for tc in tc_order[1:-1]]
    legs.append((origin_tc, tail))

    for leg_index, (tc, cities_in_tc) in enumerate(legs):
        is_origin_leg = leg_index in (0, len(legs) - 1)
        if not cities_in_tc and is_origin_leg:
            continue
        if not cities_in_tc:
            # No must-visit cities in this TC — pick a hub to transit through
            prev_airport = route[-1]
            prev_tc = _get_tc(prev_airport)
            if prev_tc and prev_tc != tc:
                conns = hub_table.get_connections(prev_tc, tc)
                if conns:
                    # Use the best hub as a transit city
                    cities_in_tc = [conns[0].to_hub]
                    hub_count += 1
                else:
                    return None  # No connection available

        for city in cities_in_tc:
            prev_airport = route[-1]
            prev_tc = _get_tc(prev_airport)
            city_tc = _get_tc(city)

            if prev_tc and city_tc and prev_tc != city_tc:
                # Need an intercontinental connection
                conns = hub_table.get_connections(prev_tc, city_tc)
                if not conns:
                    return None

                best = conns[0]
                # If prev_airport isn't the hub, route through the hub
                if prev_airport != best.from_hub:
                    route.append(best.from_hub)
                if city != best.to_hub:
                    route.append(best.to_hub)
                    hub_count += 1
                route.append(city)
            else:
                route.append(city)

    # Return to origin
    last_airport = route[-1]
    last_tc = _get_tc(last_airport)
    origin_tc = _get_tc(origin)
    if last_tc and origin_tc and last_tc != origin_tc:
        conns = hub_table.get_connections(last_tc, origin_tc)
        if not conns:
            return None
        best = conns[0]
        if last_airport != best.from_hub:
            route.append(best.from_hub)
        if origin != best.to_hub:
            route.append(best.to_hub)
    route.append(origin)

    return route, hub_count


def _route_to_itinerary(
    route: list[str],
    query: SearchQuery,
    hub_table: HubTable,
) -> Itinerary:
    """Convert an airport sequence to an Itinerary model."""
    segments = []
    for i in range(len(route) - 1):
        from_apt = route[i]
        to_apt = route[i + 1]
        from_cont = get_continent(from_apt)
        to_cont = get_continent(to_apt)

        # Pick carrier based on whether segment is intercontinental
        if from_cont and to_cont and from_cont != to_cont:
            from_tc = CONTINENT_TO_TC[from_cont]
            to_tc = CONTINENT_TO_TC[to_cont]
            conns = hub_table.get_connections(from_tc, to_tc)
            carrier = "AA"  # fallback
            for c in conns:
                if c.from_hub == from_apt or c.to_hub == to_apt:
                    carrier = c.carrier
                    break
        else:
            # Intra-continent — use primary carrier
            cont = to_cont or from_cont
            if cont:
                carrier = hub_table.get_intra_carrier(cont)
            else:
                carrier = "AA"

        # The last segment returns to origin: that arrival ends the journey and
        # is not a stopover, so it must not count toward the Rule 3015 §6
        # origin-continent stopover limit.
        is_last = i == len(route) - 2
        seg_type = SegmentType.FINAL if is_last else SegmentType.STOPOVER
        segments.append(
            Segment(
                **{
                    "from": from_apt,
                    "to": to_apt,
                    "carrier": carrier,
                    "type": seg_type,
                }
            )
        )

    ticket = Ticket(
        type=query.ticket_type,
        cabin=query.cabin,
        origin=query.origin,
        passengers=1,
    )

    return Itinerary(ticket=ticket, segments=segments)


def _route_key(route: list[str]) -> str:
    """Create a dedup key from airport sequence."""
    return "->".join(route)


def generate_candidates(
    query: SearchQuery,
    hub_table: Optional[HubTable] = None,
    nonstop_filter: Optional[Callable[[str, str, str], bool]] = None,
) -> list[CandidateItinerary]:
    """Generate valid RTW itinerary candidates.

    Produces candidates in both eastbound and westbound directions.
    Every returned candidate passes Validator().validate() with 0 violations.

    Args:
        query: Validated search query.
        hub_table: Hub connection table (loads default if None).
        nonstop_filter: Optional callback ``(origin, dest, carrier) -> bool``.
            When provided, each flown segment is tested. If any segment
            returns False the candidate is eliminated. Exceptions are
            treated as "unknown" (segment retained).

    Returns:
        List of valid CandidateItinerary objects, capped at 2000 total.
    """
    if hub_table is None:
        hub_table = HubTable()

    validator = Validator()
    origin_tc = _get_tc(query.origin)
    if origin_tc is None:
        logger.warning("Unknown origin airport TC: %s", query.origin)
        return []

    # Group must-visit cities by TC
    city_groups = _group_cities_by_tc(query.cities)

    # Remove origin from cities if present (it's always start/end)
    for tc_key in city_groups:
        city_groups[tc_key] = [c for c in city_groups[tc_key] if c != query.origin]

    must_visit = set(query.cities) - {query.origin}
    candidates: list[CandidateItinerary] = []
    seen_routes: set[str] = set()

    for direction, tc_orders in [
        (Direction.EASTBOUND, _EASTBOUND_ORDERS),
        (Direction.WESTBOUND, _WESTBOUND_ORDERS),
    ]:
        tc_order = tc_orders[origin_tc]
        direction_count = 0

        # Generate permutations for each TC group
        tc_perms: dict[TariffConference, list[tuple[str, ...]]] = {}
        for tc, cities in city_groups.items():
            if cities:
                tc_perms[tc] = list(itertools.permutations(cities))
            else:
                tc_perms[tc] = [()]

        # Iterate over all combinations of permutations across TCs
        for perm_combo in itertools.product(
            tc_perms[TariffConference.TC1],
            tc_perms[TariffConference.TC2],
            tc_perms[TariffConference.TC3],
        ):
            if direction_count >= _MAX_CANDIDATES_PER_DIRECTION:
                break

            perm_map = {
                TariffConference.TC1: perm_combo[0],
                TariffConference.TC2: perm_combo[1],
                TariffConference.TC3: perm_combo[2],
            }

            for layout in _ORIGIN_TC_LAYOUTS:
                if direction_count >= _MAX_CANDIDATES_PER_DIRECTION:
                    break
                result = _build_route(
                    query.origin, tc_order, city_groups, perm_map, hub_table, layout
                )
                if result is None:
                    continue

                route, hub_count = result

                # Every must-visit city must actually be on the route.
                if not must_visit <= set(route):
                    continue

                # Dedup
                key = _route_key(route)
                if key in seen_routes:
                    continue
                seen_routes.add(key)

                # Build itinerary and validate
                try:
                    itinerary = _route_to_itinerary(route, query, hub_table)
                except Exception:
                    logger.debug("Failed to build itinerary for route %s", route)
                    continue

                report = validator.validate(itinerary)
                if not report.passed:
                    continue

                # Ticket type must match continents actually visited (priced per
                # continent, Rule 3015 §16). Fewer continents = mislabelled/overpaid.
                # Under-visiting is only a WARNING, so check the rule explicitly:
                # every candidate is promised to be issuable as labelled.
                if not all(
                    r.passed for r in report.results if r.rule_id == "continent_count"
                ):
                    continue

                # Nonstop filter: eliminate candidates with non-nonstop segments
                if nonstop_filter is not None:
                    filtered_out = False
                    for seg in itinerary.segments:
                        if seg.type == SegmentType.SURFACE:
                            continue
                        try:
                            if not nonstop_filter(
                                seg.from_airport, seg.to_airport, seg.carrier or ""
                            ):
                                filtered_out = True
                                break
                        except Exception:
                            pass  # Treat errors as "unknown" — keep segment
                    if filtered_out:
                        continue

                # Build route segments for display
                route_segments = [
                    RouteSegment(
                        from_airport=seg.from_airport,
                        to_airport=seg.to_airport,
                        carrier=seg.carrier or "AA",
                        segment_type=seg.type,
                    )
                    for seg in itinerary.segments
                ]

                candidates.append(
                    CandidateItinerary(
                        itinerary=itinerary,
                        direction=direction,
                        route_segments=route_segments,
                        hub_count=hub_count,
                        must_visit_cities=list(query.cities),
                    )
                )
                direction_count += 1

    return candidates
