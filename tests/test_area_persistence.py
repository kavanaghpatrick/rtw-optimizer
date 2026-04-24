"""Persistence, bootstrap idempotence, and env-var resolution tests for area DB.

These tests complement ``tests/test_area.py`` by explicitly exercising
close/reopen cycles, repeated schema bootstrap, and ``RTW_AREA_DB`` env-var
resolution in :mod:`rtw.area.db`.
"""

from datetime import date
from pathlib import Path

import pytest

from rtw.area.db import _DEFAULT_PATH, default_db_path, open_area_db
from rtw.area.repo import AreaRepo
from rtw.models import CabinClass, Segment, SegmentType, Ticket, TicketType


# ---------------------------------------------------------------------------
# Helpers (duplicated from test_area.py so this file stands alone)
# ---------------------------------------------------------------------------


def _ticket(**overrides):
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


def _route(repo: AreaRepo, trip_id: int) -> list[tuple[str, str]]:
    return [(s["from_airport"], s["to_airport"]) for s in repo.list_segments(trip_id)]


def _positions(repo: AreaRepo, trip_id: int) -> list[int]:
    return [s["position"] for s in repo.list_segments(trip_id)]


# ---------------------------------------------------------------------------
# Persistence across connections
# ---------------------------------------------------------------------------


def test_trip_and_segments_persist_across_close_reopen(tmp_path):
    """The big one: SQLite must actually commit. Write via conn1, read via conn2."""
    db_path = tmp_path / "area.db"

    conn1 = open_area_db(db_path)
    try:
        repo1 = AreaRepo(conn1)
        tid = repo1.create_trip("persist", _ticket(plating_carrier="CX"))
        for f, t in [("OSL", "LHR"), ("LHR", "SEA"), ("SEA", "OSL")]:
            repo1.add_segment(tid, _seg(f, t))
    finally:
        conn1.close()

    # Reopen a completely new connection on the same path.
    conn2 = open_area_db(db_path)
    try:
        repo2 = AreaRepo(conn2)
        trips = {t["slug"]: t for t in repo2.list_trips()}
        assert "persist" in trips
        trip_row = trips["persist"]
        assert trip_row["plating_carrier"] == "CX"
        assert trip_row["origin"] == "OSL"
        assert trip_row["is_active"] == 1

        # load_itinerary validates via Pydantic + contiguous positions
        itin = repo2.load_itinerary(trip_row["id"])
        assert len(itin.segments) == 3
        assert [(s.from_airport, s.to_airport) for s in itin.segments] == [
            ("OSL", "LHR"),
            ("LHR", "SEA"),
            ("SEA", "OSL"),
        ]
        # Position order must be preserved by persisted rows too.
        assert _positions(repo2, trip_row["id"]) == [1, 2, 3]
    finally:
        conn2.close()


def test_add_segment_visible_to_fresh_connection(tmp_path):
    db_path = tmp_path / "area.db"

    conn1 = open_area_db(db_path)
    try:
        repo1 = AreaRepo(conn1)
        tid = repo1.create_trip("addseg", _ticket())
        repo1.add_segment(tid, _seg("OSL", "LHR", carrier="BA", flight="785"))
    finally:
        conn1.close()

    conn2 = open_area_db(db_path)
    try:
        repo2 = AreaRepo(conn2)
        trip = next(t for t in repo2.list_trips() if t["slug"] == "addseg")
        segs = repo2.list_segments(trip["id"])
        assert len(segs) == 1
        assert segs[0]["from_airport"] == "OSL"
        assert segs[0]["to_airport"] == "LHR"
        assert segs[0]["carrier"] == "BA"
        assert segs[0]["flight"] == "785"
    finally:
        conn2.close()


def test_move_segment_persists_across_reopen(tmp_path):
    db_path = tmp_path / "area.db"

    conn1 = open_area_db(db_path)
    try:
        repo1 = AreaRepo(conn1)
        tid = repo1.create_trip("mv", _ticket())
        for f, t in [("OSL", "LHR"), ("LHR", "SEA"), ("SEA", "OSL")]:
            repo1.add_segment(tid, _seg(f, t))
        repo1.move_segment(tid, 1, 3)  # OSL-LHR moves to the end
    finally:
        conn1.close()

    conn2 = open_area_db(db_path)
    try:
        repo2 = AreaRepo(conn2)
        trip = next(t for t in repo2.list_trips() if t["slug"] == "mv")
        assert _route(repo2, trip["id"]) == [
            ("LHR", "SEA"),
            ("SEA", "OSL"),
            ("OSL", "LHR"),
        ]
        assert _positions(repo2, trip["id"]) == [1, 2, 3]
    finally:
        conn2.close()


# ---------------------------------------------------------------------------
# Idempotent bootstrap
# ---------------------------------------------------------------------------


def test_open_area_db_is_idempotent_schema_survives(tmp_path):
    db_path = tmp_path / "area.db"

    # First bootstrap — table list recorded.
    conn1 = open_area_db(db_path)
    try:
        first_tables = sorted(
            r["name"]
            for r in conn1.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        )
        first_indexes = sorted(
            r["name"]
            for r in conn1.execute(
                "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
            )
        )
        assert "trips" in first_tables
        assert "segments" in first_tables
    finally:
        conn1.close()

    # Second bootstrap on the same path — must not error, must not duplicate.
    conn2 = open_area_db(db_path)
    try:
        second_tables = sorted(
            r["name"]
            for r in conn2.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        )
        second_indexes = sorted(
            r["name"]
            for r in conn2.execute(
                "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
            )
        )
        assert second_tables == first_tables
        assert second_indexes == first_indexes
    finally:
        conn2.close()


def test_data_survives_second_bootstrap(tmp_path):
    """Opening a path that already holds data must not wipe it."""
    db_path = tmp_path / "area.db"

    conn1 = open_area_db(db_path)
    try:
        repo1 = AreaRepo(conn1)
        tid = repo1.create_trip("keepme", _ticket())
        repo1.add_segment(tid, _seg("OSL", "LHR"))
        repo1.add_segment(tid, _seg("LHR", "OSL"))
    finally:
        conn1.close()

    # Bootstrap again — CREATE IF NOT EXISTS must be a no-op on data.
    conn2 = open_area_db(db_path)
    try:
        repo2 = AreaRepo(conn2)
        trips = [t for t in repo2.list_trips() if t["slug"] == "keepme"]
        assert len(trips) == 1, "trip was lost by second bootstrap"
        segs = repo2.list_segments(trips[0]["id"])
        assert len(segs) == 2, "segments were lost by second bootstrap"
        assert [(s["from_airport"], s["to_airport"]) for s in segs] == [
            ("OSL", "LHR"),
            ("LHR", "OSL"),
        ]
    finally:
        conn2.close()


def test_second_bootstrap_does_not_duplicate_tables(tmp_path):
    db_path = tmp_path / "area.db"

    conn1 = open_area_db(db_path)
    conn1.close()
    conn2 = open_area_db(db_path)
    try:
        # Exactly one trips table and one segments table must exist.
        trip_count = conn2.execute(
            "SELECT COUNT(*) AS n FROM sqlite_master "
            "WHERE type='table' AND name='trips'"
        ).fetchone()["n"]
        seg_count = conn2.execute(
            "SELECT COUNT(*) AS n FROM sqlite_master "
            "WHERE type='table' AND name='segments'"
        ).fetchone()["n"]
        assert trip_count == 1
        assert seg_count == 1
    finally:
        conn2.close()


# ---------------------------------------------------------------------------
# Env var + default path
# ---------------------------------------------------------------------------


def test_default_db_path_unset_returns_home_default(monkeypatch):
    monkeypatch.delenv("RTW_AREA_DB", raising=False)
    assert default_db_path() == _DEFAULT_PATH
    assert default_db_path() == Path.home() / ".rtw" / "area.db"


def test_default_db_path_honors_env_var(monkeypatch, tmp_path):
    custom = tmp_path / "custom" / "path.db"
    monkeypatch.setenv("RTW_AREA_DB", str(custom))
    assert default_db_path() == Path(str(custom))


def test_default_db_path_empty_env_var_falls_back_to_default(monkeypatch):
    """An empty string for RTW_AREA_DB is falsy -> default path used."""
    monkeypatch.setenv("RTW_AREA_DB", "")
    assert default_db_path() == _DEFAULT_PATH


def test_open_area_db_no_arg_uses_env_var(monkeypatch, tmp_path):
    """Calling ``open_area_db()`` with no arg must open at the env-var path."""
    target = tmp_path / "env_area.db"
    assert not target.exists()
    monkeypatch.setenv("RTW_AREA_DB", str(target))

    conn = open_area_db()
    try:
        # The DB file must now exist at the env-var path.
        assert target.exists(), (
            f"expected DB file at env-var path {target}, not created"
        )
        # And the schema must be bootstrapped.
        tables = {
            r["name"]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert "trips" in tables
        assert "segments" in tables
    finally:
        conn.close()


def test_open_area_db_creates_missing_parent_directories(tmp_path):
    """Parent dir auto-creation for deeply nested paths."""
    nested = tmp_path / "nested" / "deep" / "down" / "area.db"
    assert not nested.parent.exists()

    conn = open_area_db(nested)
    try:
        assert nested.parent.is_dir(), "parent directory was not created"
        assert nested.exists(), "DB file was not created at nested path"
    finally:
        conn.close()


def test_open_area_db_env_var_creates_missing_parents(monkeypatch, tmp_path):
    """Parent-creation must work when path comes from env var too."""
    target = tmp_path / "env" / "nested" / "area.db"
    monkeypatch.setenv("RTW_AREA_DB", str(target))
    assert not target.parent.exists()

    conn = open_area_db()
    try:
        assert target.parent.is_dir()
        assert target.exists()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Foreign keys pragma
# ---------------------------------------------------------------------------


def test_foreign_keys_pragma_is_on(tmp_path):
    """Cascade-delete from trips -> segments depends on FK enforcement."""
    conn = open_area_db(tmp_path / "area.db")
    try:
        row = conn.execute("PRAGMA foreign_keys").fetchone()
        # PRAGMA foreign_keys returns a single column, "foreign_keys".
        # Using numeric index works regardless of row_factory.
        assert row[0] == 1, f"expected foreign_keys=1, got {row[0]!r}"
    finally:
        conn.close()


def test_foreign_keys_pragma_on_for_env_var_open(monkeypatch, tmp_path):
    monkeypatch.setenv("RTW_AREA_DB", str(tmp_path / "fk_env.db"))
    conn = open_area_db()
    try:
        row = conn.execute("PRAGMA foreign_keys").fetchone()
        assert row[0] == 1
    finally:
        conn.close()


def test_foreign_keys_cascade_actually_works(tmp_path):
    """Sanity: pragma=1 alone is worthless if cascade doesn't fire."""
    conn = open_area_db(tmp_path / "area.db")
    try:
        repo = AreaRepo(conn)
        tid = repo.create_trip("cascade", _ticket())
        repo.add_segment(tid, _seg("OSL", "LHR"))
        repo.add_segment(tid, _seg("LHR", "OSL"))
        # Delete trip directly via SQL to exercise ON DELETE CASCADE.
        conn.execute("DELETE FROM trips WHERE id = ?", (tid,))
        conn.commit()
        orphan = conn.execute(
            "SELECT COUNT(*) AS n FROM segments WHERE trip_id = ?", (tid,)
        ).fetchone()
        assert orphan["n"] == 0, (
            "cascade delete failed — foreign_keys pragma likely off"
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Safety: do not touch the real ~/.rtw/area.db
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _guard_real_db(monkeypatch, tmp_path):
    """Auto-applied safety net: redirect default path away from ~/.rtw.

    Tests that explicitly set or unset RTW_AREA_DB will override this via their
    own ``monkeypatch`` calls (monkeypatch is LIFO-undone per test).
    """
    monkeypatch.setenv("RTW_AREA_DB", str(tmp_path / "_guard.db"))
    yield
