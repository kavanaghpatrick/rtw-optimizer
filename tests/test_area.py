"""Area repo + CLI tests: trip CRUD, segment positions, validator integration."""

from datetime import date

import pytest

from rtw.area.db import open_area_db
from rtw.area.repo import AreaRepo, NoActiveTripError, TripNotFoundError
from rtw.models import (
    CabinClass,
    Itinerary,
    Segment,
    SegmentType,
    Ticket,
    TicketType,
    ValidationReport,
)


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


def _positions(repo: AreaRepo, trip_id: int) -> list[int]:
    return [s["position"] for s in repo.list_segments(trip_id)]


def _route(repo: AreaRepo, trip_id: int) -> list[tuple[str, str]]:
    return [(s["from_airport"], s["to_airport"]) for s in repo.list_segments(trip_id)]


# ---------------------------------------------------------------------------
# Trip lifecycle
# ---------------------------------------------------------------------------


def test_create_trip_sets_active(repo):
    tid = repo.create_trip("t1", _ticket())
    assert repo.get_active_trip_id() == tid


def test_only_one_active_trip(repo):
    repo.create_trip("t1", _ticket())
    t2 = repo.create_trip("t2", _ticket())
    assert repo.get_active_trip_id() == t2
    by_slug = {t["slug"]: t for t in repo.list_trips()}
    assert by_slug["t1"]["is_active"] == 0
    assert by_slug["t2"]["is_active"] == 1


def test_switch_active(repo):
    t1 = repo.create_trip("t1", _ticket())
    repo.create_trip("t2", _ticket())  # now active
    repo.set_active(t1)
    assert repo.get_active_trip_id() == t1


def test_set_active_unknown_raises(repo):
    with pytest.raises(TripNotFoundError):
        repo.set_active(999)


def test_get_active_or_raise_empty(repo):
    with pytest.raises(NoActiveTripError):
        repo.get_active_or_raise()


def test_delete_trip_cascades_segments(repo):
    tid = repo.create_trip("t", _ticket())
    repo.add_segment(tid, _seg("OSL", "LHR"))
    repo.add_segment(tid, _seg("LHR", "OSL"))
    repo.delete_trip(tid)
    assert repo.get_trip_by_slug("t") is None
    # Segments must be gone (FK ON DELETE CASCADE)
    row = repo.conn.execute(
        "SELECT COUNT(*) AS n FROM segments WHERE trip_id=?", (tid,)
    ).fetchone()
    assert row["n"] == 0


def test_slug_is_unique(repo):
    repo.create_trip("dup", _ticket())
    with pytest.raises(Exception):  # sqlite3.IntegrityError
        repo.create_trip("dup", _ticket())


# ---------------------------------------------------------------------------
# Segment CRUD + position invariants
# ---------------------------------------------------------------------------


def test_append_is_contiguous(repo):
    tid = repo.create_trip("t", _ticket())
    for f, t in [("OSL", "LHR"), ("LHR", "SEA"), ("SEA", "OSL")]:
        repo.add_segment(tid, _seg(f, t))
    assert _positions(repo, tid) == [1, 2, 3]
    assert _route(repo, tid) == [("OSL", "LHR"), ("LHR", "SEA"), ("SEA", "OSL")]


def test_insert_shifts_later_segments(repo):
    tid = repo.create_trip("t", _ticket())
    repo.add_segment(tid, _seg("OSL", "LHR"))
    repo.add_segment(tid, _seg("LHR", "OSL"))
    repo.add_segment(tid, _seg("LHR", "SEA"), position=2)
    assert _positions(repo, tid) == [1, 2, 3]
    assert _route(repo, tid) == [
        ("OSL", "LHR"),
        ("LHR", "SEA"),
        ("LHR", "OSL"),
    ]


def test_insert_at_head(repo):
    tid = repo.create_trip("t", _ticket())
    repo.add_segment(tid, _seg("LHR", "OSL"))
    repo.add_segment(tid, _seg("OSL", "LHR"), position=1)
    assert _route(repo, tid) == [("OSL", "LHR"), ("LHR", "OSL")]
    assert _positions(repo, tid) == [1, 2]


def test_insert_at_tail_position_equals_append(repo):
    tid = repo.create_trip("t", _ticket())
    repo.add_segment(tid, _seg("OSL", "LHR"))
    repo.add_segment(tid, _seg("LHR", "SEA"), position=2)
    assert _route(repo, tid) == [("OSL", "LHR"), ("LHR", "SEA")]


def test_insert_out_of_range_raises(repo):
    tid = repo.create_trip("t", _ticket())
    repo.add_segment(tid, _seg("OSL", "LHR"))
    with pytest.raises(ValueError):
        repo.add_segment(tid, _seg("LHR", "SEA"), position=5)
    with pytest.raises(ValueError):
        repo.add_segment(tid, _seg("LHR", "SEA"), position=0)


def test_remove_compacts(repo):
    tid = repo.create_trip("t", _ticket())
    for f, t in [("OSL", "LHR"), ("LHR", "SEA"), ("SEA", "OSL")]:
        repo.add_segment(tid, _seg(f, t))
    repo.remove_segment(tid, 2)
    assert _positions(repo, tid) == [1, 2]
    assert _route(repo, tid) == [("OSL", "LHR"), ("SEA", "OSL")]


def test_remove_first(repo):
    tid = repo.create_trip("t", _ticket())
    for f, t in [("OSL", "LHR"), ("LHR", "OSL")]:
        repo.add_segment(tid, _seg(f, t))
    repo.remove_segment(tid, 1)
    assert _positions(repo, tid) == [1]
    assert _route(repo, tid) == [("LHR", "OSL")]


def test_remove_out_of_range_raises(repo):
    tid = repo.create_trip("t", _ticket())
    repo.add_segment(tid, _seg("OSL", "LHR"))
    with pytest.raises(ValueError):
        repo.remove_segment(tid, 5)


def test_move_forward(repo):
    tid = repo.create_trip("t", _ticket())
    for f, t in [("OSL", "LHR"), ("LHR", "SEA"), ("SEA", "OSL")]:
        repo.add_segment(tid, _seg(f, t))
    repo.move_segment(tid, 1, 3)  # move first to last
    assert _positions(repo, tid) == [1, 2, 3]
    assert _route(repo, tid) == [
        ("LHR", "SEA"),
        ("SEA", "OSL"),
        ("OSL", "LHR"),
    ]


def test_move_backward(repo):
    tid = repo.create_trip("t", _ticket())
    for f, t in [("OSL", "LHR"), ("LHR", "SEA"), ("SEA", "OSL")]:
        repo.add_segment(tid, _seg(f, t))
    repo.move_segment(tid, 3, 1)
    assert _route(repo, tid) == [
        ("SEA", "OSL"),
        ("OSL", "LHR"),
        ("LHR", "SEA"),
    ]


def test_move_same_position_noop(repo):
    tid = repo.create_trip("t", _ticket())
    for f, t in [("OSL", "LHR"), ("LHR", "OSL")]:
        repo.add_segment(tid, _seg(f, t))
    before = _route(repo, tid)
    repo.move_segment(tid, 1, 1)
    assert _route(repo, tid) == before


def test_move_out_of_range_raises(repo):
    tid = repo.create_trip("t", _ticket())
    repo.add_segment(tid, _seg("OSL", "LHR"))
    with pytest.raises(ValueError):
        repo.move_segment(tid, 1, 5)


# ---------------------------------------------------------------------------
# Load Itinerary + run Validator end-to-end
# ---------------------------------------------------------------------------


def _build_jzxswh(repo: AreaRepo) -> int:
    """Populate the real JZXSWH booking as stored on the sample PDF."""
    tid = repo.create_trip(
        "jzxswh",
        _ticket(
            type=TicketType.DONE3,
            plating_carrier="CX",
            departure=date(2026, 4, 27),
        ),
        pnr="JZXSWH",
    )
    jzx = [
        ("OSL", "LHR", "BA", "785", "transit", date(2026, 4, 27)),
        ("LHR", "SEA", "BA", "49", "stopover", date(2026, 4, 27)),
        ("SEA", "LAX", "AS", "1480", "stopover", date(2026, 5, 2)),
        ("LAX", "HKG", "CX", "881", "stopover", date(2026, 5, 6)),
        ("HKG", "LHR", "CX", "253", "stopover", date(2026, 5, 8)),
        ("LHR", "OSL", "BA", "780", "final", date(2026, 10, 15)),
    ]
    for f, t, c, fl, ty, d in jzx:
        repo.add_segment(
            tid, _seg(f, t, carrier=c, flight=fl, seg_type=ty, d=d)
        )
    return tid


def test_load_itinerary_roundtrip_jzxswh(repo):
    tid = _build_jzxswh(repo)
    itin = repo.load_itinerary(tid)
    assert isinstance(itin, Itinerary)
    assert itin.ticket.origin == "OSL"
    assert itin.ticket.type == TicketType.DONE3
    assert itin.ticket.plating_carrier == "CX"
    assert len(itin.segments) == 6
    assert [(s.from_airport, s.to_airport) for s in itin.segments] == [
        ("OSL", "LHR"),
        ("LHR", "SEA"),
        ("SEA", "LAX"),
        ("LAX", "HKG"),
        ("HKG", "LHR"),
        ("LHR", "OSL"),
    ]
    assert itin.segments[0].flight == "785"
    assert itin.segments[-1].type == SegmentType.FINAL


def test_validator_runs_on_loaded_trip(repo):
    """The end-to-end ask: DB -> Itinerary -> Validator -> ValidationReport."""
    from rtw.validator import Validator

    tid = _build_jzxswh(repo)
    itin = repo.load_itinerary(tid)
    report = Validator().validate(itin)
    assert isinstance(report, ValidationReport)
    assert report.itinerary == itin
    # Validator must have run *some* rules; pass/fail depends on fixtures.
    assert len(report.results) > 0


def test_mutation_then_validate(repo):
    """Mutate the trip then re-run validator — the new itinerary gets used."""
    from rtw.validator import Validator

    tid = _build_jzxswh(repo)
    repo.remove_segment(tid, 6)  # drop LHR-OSL final
    itin = repo.load_itinerary(tid)
    assert len(itin.segments) == 5
    report = Validator().validate(itin)
    assert report.itinerary == itin
    assert len(report.results) > 0


def test_load_empty_trip_raises(repo):
    tid = repo.create_trip("empty", _ticket())
    with pytest.raises(Exception):
        repo.load_itinerary(tid)
