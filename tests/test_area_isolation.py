"""Multi-trip isolation tests for the area DB.

Complements ``tests/test_area.py`` (which covers single-trip cases) by
exercising concurrent trips, the partial unique active index, segment
isolation across ``trip_id``, and ``ON DELETE CASCADE`` behavior.
"""

import sqlite3
from datetime import date

import pytest

from rtw.area.db import open_area_db
from rtw.area.repo import AreaRepo
from rtw.models import CabinClass, Segment, SegmentType, Ticket, TicketType


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def repo(tmp_path):
    conn = open_area_db(tmp_path / "area.db")
    try:
        yield AreaRepo(conn)
    finally:
        conn.close()


def _ticket(**overrides) -> Ticket:
    base = {
        "type": TicketType.DONE3,
        "cabin": CabinClass.BUSINESS,
        "origin": "OSL",
    }
    base.update(overrides)
    return Ticket(**base)


def _seg(
    f: str,
    t: str,
    *,
    carrier: str = "BA",
    flight: str = "100",
    seg_type: str = "stopover",
    d: date | None = None,
) -> Segment:
    return Segment(
        **{"from": f, "to": t},
        carrier=carrier,
        flight=flight,
        type=SegmentType(seg_type),
        date=d,
    )


def _positions(repo: AreaRepo, trip_id: int) -> list[int]:
    return [s["position"] for s in repo.list_segments(trip_id)]


def _route(repo: AreaRepo, trip_id: int) -> list[tuple[str, str]]:
    return [(s["from_airport"], s["to_airport"]) for s in repo.list_segments(trip_id)]


def _active_map(repo: AreaRepo) -> dict[int, int]:
    """Map trip_id -> is_active for every trip (raw, order-independent)."""
    rows = repo.conn.execute("SELECT id, is_active FROM trips").fetchall()
    return {int(r["id"]): int(r["is_active"]) for r in rows}


# ---------------------------------------------------------------------------
# Active-trip invariant
# ---------------------------------------------------------------------------


def test_creating_three_trips_leaves_only_last_active(repo):
    a = repo.create_trip("a", _ticket(), set_active=True)
    b = repo.create_trip("b", _ticket(), set_active=True)
    c = repo.create_trip("c", _ticket(), set_active=True)

    flags = _active_map(repo)
    assert flags[a] == 0
    assert flags[b] == 0
    assert flags[c] == 1
    assert repo.get_active_trip_id() == c
    # Exactly one row has is_active=1.
    assert sum(flags.values()) == 1


def test_set_active_flips_exactly_one_row(repo):
    a = repo.create_trip("a", _ticket(), set_active=True)
    b = repo.create_trip("b", _ticket(), set_active=True)
    c = repo.create_trip("c", _ticket(), set_active=True)

    repo.set_active(b)

    flags = _active_map(repo)
    assert flags[a] == 0
    assert flags[b] == 1
    assert flags[c] == 0
    assert repo.get_active_trip_id() == b
    assert sum(flags.values()) == 1


def test_create_with_set_active_false_preserves_current(repo):
    a = repo.create_trip("a", _ticket(), set_active=True)
    assert repo.get_active_trip_id() == a

    b = repo.create_trip("b", _ticket(), set_active=False)

    flags = _active_map(repo)
    assert flags[a] == 1
    assert flags[b] == 0
    assert repo.get_active_trip_id() == a


def test_deleting_active_trip_clears_active(repo):
    a = repo.create_trip("a", _ticket(), set_active=True)
    repo.create_trip("b", _ticket(), set_active=False)
    repo.delete_trip(a)
    # No orphan active — get_active_trip_id returns None (not b).
    assert repo.get_active_trip_id() is None


def test_raw_sql_cannot_force_two_active_trips(repo):
    """Partial unique index ``ux_trips_active`` must prevent two is_active=1."""
    a = repo.create_trip("a", _ticket(), set_active=True)
    b = repo.create_trip("b", _ticket(), set_active=False)
    # a is currently active (=1); forcing b to 1 as well must violate the
    # partial unique index WHERE is_active = 1.
    with pytest.raises(sqlite3.IntegrityError):
        with repo.conn:
            repo.conn.execute(
                "UPDATE trips SET is_active = 1 WHERE id IN (?, ?)", (a, b)
            )


# ---------------------------------------------------------------------------
# Segment isolation across trips
# ---------------------------------------------------------------------------


def _seed_two_trips(repo: AreaRepo) -> tuple[int, int]:
    """Trip A: 3 segments (OSL->LHR, LHR->SEA, SEA->OSL).
    Trip B: 2 segments (OSL->HKG, HKG->OSL)."""
    a = repo.create_trip("a", _ticket(), set_active=True)
    for f, t in [("OSL", "LHR"), ("LHR", "SEA"), ("SEA", "OSL")]:
        repo.add_segment(a, _seg(f, t))
    b = repo.create_trip("b", _ticket(), set_active=True)
    for f, t in [("OSL", "HKG"), ("HKG", "OSL")]:
        repo.add_segment(b, _seg(f, t))
    return a, b


def test_segments_are_isolated_by_trip(repo):
    a, b = _seed_two_trips(repo)

    assert len(repo.list_segments(a)) == 3
    assert len(repo.list_segments(b)) == 2
    # Positions restart at 1 for every trip.
    assert _positions(repo, a) == [1, 2, 3]
    assert _positions(repo, b) == [1, 2]


def test_remove_on_a_does_not_touch_b(repo):
    a, b = _seed_two_trips(repo)
    b_route_before = _route(repo, b)
    b_pos_before = _positions(repo, b)

    repo.remove_segment(a, 2)  # drop LHR->SEA

    # A compacts to 2 segments.
    assert _positions(repo, a) == [1, 2]
    assert _route(repo, a) == [("OSL", "LHR"), ("SEA", "OSL")]
    # B is unchanged.
    assert _positions(repo, b) == b_pos_before
    assert _route(repo, b) == b_route_before


def test_move_on_a_does_not_reorder_b(repo):
    a, b = _seed_two_trips(repo)
    b_route_before = _route(repo, b)

    repo.move_segment(a, 1, 3)  # rotate A's first to last

    assert _route(repo, a) == [
        ("LHR", "SEA"),
        ("SEA", "OSL"),
        ("OSL", "LHR"),
    ]
    # B untouched.
    assert _route(repo, b) == b_route_before
    assert _positions(repo, b) == [1, 2]


def test_load_itinerary_returns_only_trip_segments(repo):
    a, b = _seed_two_trips(repo)

    itin_a = repo.load_itinerary(a)
    itin_b = repo.load_itinerary(b)

    assert [(s.from_airport, s.to_airport) for s in itin_a.segments] == [
        ("OSL", "LHR"),
        ("LHR", "SEA"),
        ("SEA", "OSL"),
    ]
    assert [(s.from_airport, s.to_airport) for s in itin_b.segments] == [
        ("OSL", "HKG"),
        ("HKG", "OSL"),
    ]


# ---------------------------------------------------------------------------
# Cascade delete
# ---------------------------------------------------------------------------


def test_delete_trip_cascades_only_its_segments(repo):
    a, b = _seed_two_trips(repo)
    b_route_before = _route(repo, b)
    b_pos_before = _positions(repo, b)

    repo.delete_trip(a)

    # A's segments are gone.
    row = repo.conn.execute(
        "SELECT COUNT(*) AS n FROM segments WHERE trip_id=?", (a,)
    ).fetchone()
    assert row["n"] == 0
    # B's segments remain, unchanged in position and route.
    assert _positions(repo, b) == b_pos_before
    assert _route(repo, b) == b_route_before


def test_slug_can_be_reused_after_delete(repo):
    a = repo.create_trip("a", _ticket(), set_active=True)
    repo.add_segment(a, _seg("OSL", "LHR"))
    repo.delete_trip(a)

    # Slug "a" should now be available again.
    a2 = repo.create_trip("a", _ticket(), set_active=True)
    assert a2 != a
    assert repo.get_trip_by_slug("a") == a2


# ---------------------------------------------------------------------------
# Slug behavior
# ---------------------------------------------------------------------------


def test_duplicate_slug_raises_integrity_error(repo):
    repo.create_trip("dup", _ticket(), set_active=True)
    with pytest.raises(sqlite3.IntegrityError):
        repo.create_trip("dup", _ticket(), set_active=False)


def test_slug_is_case_sensitive(repo):
    """SQLite TEXT UNIQUE uses BINARY collation by default, so "A" != "a".
    Documenting actual behavior — callers that want case-insensitive slugs
    must normalize before insert."""
    lower = repo.create_trip("a", _ticket(), set_active=True)
    upper = repo.create_trip("A", _ticket(), set_active=False)

    assert lower != upper
    assert repo.get_trip_by_slug("a") == lower
    assert repo.get_trip_by_slug("A") == upper
