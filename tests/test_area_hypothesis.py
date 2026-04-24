"""Property-based tests for AreaRepo segment ordering invariants.

These tests apply random sequences of mutations (append, insert, remove,
move) against an AreaRepo and assert, after *every* operation, that:

1. Positions are exactly ``[1, 2, ..., N]`` (contiguous, 1-based).
2. No duplicate positions exist in the DB (``UNIQUE(trip_id, position)``).
3. Segment count matches the expected count.
4. A parallel in-memory Python list stays in sync with
   ``repo.list_segments`` -- i.e. the DB faithfully represents an
   ordered list.

Run: ``uv run pytest tests/test_area_hypothesis.py -v``
"""

from __future__ import annotations

import itertools

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from rtw.area.db import open_area_db
from rtw.area.repo import AreaRepo
from rtw.models import (
    CabinClass,
    Segment,
    SegmentType,
    Ticket,
    TicketType,
)

# Unique slug/db counter so Hypothesis re-entries of the same ``tmp_path``
# don't collide on either the DB file or the ``trips.slug`` UNIQUE index.
_counter = itertools.count()


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


_UPPER = st.text(
    alphabet=st.characters(whitelist_categories=("Lu",)),
    min_size=3,
    max_size=3,
)


@st.composite
def segment_strategy(draw) -> Segment:
    """Generate a minimally-valid Segment with random 3-letter codes."""
    f = draw(_UPPER)
    t = draw(_UPPER)
    return Segment(
        **{"from": f, "to": t},
        carrier="BA",
        flight="100",
        type=SegmentType.STOPOVER,
    )


# Each op is a tuple: (op_name, *op-specific ints). We sample the op name
# here; the positions are resolved against the *current* list length at
# apply-time, by taking ``seed % len`` (or ``seed % (len+1)`` for insert).
op_strategy = st.tuples(
    st.sampled_from(["append", "insert", "remove", "move"]),
    st.integers(min_value=0, max_value=1000),  # position seed #1
    st.integers(min_value=0, max_value=1000),  # position seed #2
    segment_strategy(),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo(tmp_path) -> tuple[AreaRepo, int]:
    # One fresh DB file per invocation so Hypothesis iterations don't
    # share state across the same function-scoped ``tmp_path``.
    n = next(_counter)
    conn = open_area_db(tmp_path / f"area_{n}.db")
    repo = AreaRepo(conn)
    tid = repo.create_trip(
        f"fuzz_{n}",
        Ticket(
            type=TicketType.DONE3,
            cabin=CabinClass.BUSINESS,
            origin="OSL",
        ),
    )
    return repo, tid


def _db_positions(repo: AreaRepo, trip_id: int) -> list[int]:
    return [s["position"] for s in repo.list_segments(trip_id)]


def _db_routes(repo: AreaRepo, trip_id: int) -> list[tuple[str, str]]:
    return [(s["from_airport"], s["to_airport"]) for s in repo.list_segments(trip_id)]


def _assert_invariants(
    repo: AreaRepo,
    trip_id: int,
    expected: list[tuple[str, str]],
) -> None:
    """Check all four invariants after every op."""
    rows = repo.list_segments(trip_id)
    positions = [r["position"] for r in rows]
    routes = [(r["from_airport"], r["to_airport"]) for r in rows]

    # 1. Contiguous 1-based positions
    assert positions == list(range(1, len(rows) + 1)), (
        f"positions not contiguous: {positions}"
    )
    # 2. No duplicate positions (UNIQUE holds)
    assert len(positions) == len(set(positions)), (
        f"duplicate positions: {positions}"
    )
    # 3. Count matches
    assert len(rows) == len(expected), (
        f"count mismatch: db={len(rows)} expected={len(expected)}"
    )
    # 4. DB order matches the parallel list
    assert routes == expected, f"route mismatch: db={routes} expected={expected}"


def _apply_op(
    repo: AreaRepo,
    trip_id: int,
    expected: list[tuple[str, str]],
    op: tuple,
) -> None:
    """Mutate both the DB and the parallel ``expected`` list in lockstep."""
    name, seed1, seed2, seg = op
    route = (seg.from_airport, seg.to_airport)
    n = len(expected)

    if name == "append":
        repo.add_segment(trip_id, seg)
        expected.append(route)
        return

    if n == 0:
        # insert/remove/move need at least one element; treat as append.
        repo.add_segment(trip_id, seg)
        expected.append(route)
        return

    if name == "insert":
        pos = (seed1 % (n + 1)) + 1  # 1..n+1
        repo.add_segment(trip_id, seg, position=pos)
        expected.insert(pos - 1, route)
        return

    if name == "remove":
        pos = (seed1 % n) + 1  # 1..n
        repo.remove_segment(trip_id, pos)
        expected.pop(pos - 1)
        return

    if name == "move":
        frm = (seed1 % n) + 1
        to = (seed2 % n) + 1
        repo.move_segment(trip_id, frm, to)
        if frm != to:
            val = expected.pop(frm - 1)
            expected.insert(to - 1, val)
        return

    raise AssertionError(f"unknown op {name!r}")


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(ops=st.lists(op_strategy, min_size=0, max_size=30))
def test_random_ops_preserve_invariants(tmp_path, ops):
    """Any sequence of append/insert/remove/move keeps invariants intact."""
    repo, tid = _make_repo(tmp_path)
    expected: list[tuple[str, str]] = []
    try:
        for op in ops:
            _apply_op(repo, tid, expected, op)
            _assert_invariants(repo, tid, expected)
    finally:
        repo.conn.close()


@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    segs=st.lists(segment_strategy(), min_size=1, max_size=20),
)
def test_append_then_full_reversal_via_moves(tmp_path, segs):
    """Append N segments then reverse by repeatedly moving first -> last."""
    repo, tid = _make_repo(tmp_path)
    expected: list[tuple[str, str]] = []
    try:
        for s in segs:
            repo.add_segment(tid, s)
            expected.append((s.from_airport, s.to_airport))
            _assert_invariants(repo, tid, expected)

        n = len(expected)
        # Reverse in place by moving position 1 to position n, then 1->n-1, ...
        for k in range(n, 1, -1):
            repo.move_segment(tid, 1, k)
            val = expected.pop(0)
            expected.insert(k - 1, val)
            _assert_invariants(repo, tid, expected)

        assert expected == list(reversed([(s.from_airport, s.to_airport) for s in segs]))
    finally:
        repo.conn.close()


@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    segs=st.lists(segment_strategy(), min_size=1, max_size=15),
)
def test_insert_at_head_repeatedly(tmp_path, segs):
    """Inserting every new segment at position 1 keeps positions contiguous."""
    repo, tid = _make_repo(tmp_path)
    expected: list[tuple[str, str]] = []
    try:
        for s in segs:
            repo.add_segment(tid, s, position=1)
            expected.insert(0, (s.from_airport, s.to_airport))
            _assert_invariants(repo, tid, expected)
    finally:
        repo.conn.close()


# ---------------------------------------------------------------------------
# Targeted regression tests (non-Hypothesis)
# ---------------------------------------------------------------------------


def _seg(f: str, t: str) -> Segment:
    return Segment(
        **{"from": f, "to": t},
        carrier="BA",
        flight="100",
        type=SegmentType.STOPOVER,
    )


def test_regression_insert_head_then_remove_middle(tmp_path):
    """Mini-sequence: append x3, insert at head, remove middle, move.

    Exercises the negative-offset shift used by add_segment when
    ``target <= n`` and by remove_segment's compaction.
    """
    repo, tid = _make_repo(tmp_path)
    try:
        for f, t in [("AAA", "BBB"), ("BBB", "CCC"), ("CCC", "DDD")]:
            repo.add_segment(tid, _seg(f, t))
        repo.add_segment(tid, _seg("ZZZ", "AAA"), position=1)
        assert _db_positions(repo, tid) == [1, 2, 3, 4]
        assert _db_routes(repo, tid) == [
            ("ZZZ", "AAA"),
            ("AAA", "BBB"),
            ("BBB", "CCC"),
            ("CCC", "DDD"),
        ]
        repo.remove_segment(tid, 3)
        assert _db_positions(repo, tid) == [1, 2, 3]
        assert _db_routes(repo, tid) == [
            ("ZZZ", "AAA"),
            ("AAA", "BBB"),
            ("CCC", "DDD"),
        ]
        repo.move_segment(tid, 1, 3)
        assert _db_positions(repo, tid) == [1, 2, 3]
        assert _db_routes(repo, tid) == [
            ("AAA", "BBB"),
            ("CCC", "DDD"),
            ("ZZZ", "AAA"),
        ]
    finally:
        repo.conn.close()


def test_regression_churn_keeps_positions_contiguous(tmp_path):
    """Alternating insert/remove/move should never violate UNIQUE."""
    repo, tid = _make_repo(tmp_path)
    try:
        repo.add_segment(tid, _seg("AAA", "BBB"))
        repo.add_segment(tid, _seg("BBB", "CCC"))
        repo.add_segment(tid, _seg("CCC", "DDD"), position=1)
        repo.remove_segment(tid, 2)
        repo.add_segment(tid, _seg("DDD", "EEE"), position=1)
        repo.move_segment(tid, 1, 3)
        repo.remove_segment(tid, 1)
        repo.move_segment(tid, 1, 2)

        rows = repo.list_segments(tid)
        positions = [r["position"] for r in rows]
        assert positions == list(range(1, len(rows) + 1))
        assert len(positions) == len(set(positions))
    finally:
        repo.conn.close()
