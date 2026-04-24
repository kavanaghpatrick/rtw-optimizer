"""Field round-trip tests for the area DB repo.

Every Pydantic field on ``Ticket`` and ``Segment`` is exercised against
``AreaRepo.create_trip`` / ``add_segment`` / ``load_itinerary`` to confirm
values survive the SQLite persist + rebuild cycle unchanged.
"""

from datetime import date

import pytest

from rtw.area.db import open_area_db
from rtw.area.repo import AreaRepo
from rtw.models import (
    CabinClass,
    Segment,
    SegmentType,
    Ticket,
    TicketType,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers (mirrors tests/test_area.py style)
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
    f: str = "OSL",
    t: str = "LHR",
    **overrides,
) -> Segment:
    kwargs = {
        "carrier": "BA",
        "flight": "100",
        "type": SegmentType.STOPOVER,
    }
    kwargs.update(overrides)
    return Segment(**{"from": f, "to": t}, **kwargs)


def _roundtrip_first_segment(repo: AreaRepo, seg: Segment) -> Segment:
    tid = repo.create_trip("t", _ticket())
    repo.add_segment(tid, seg)
    return repo.load_itinerary(tid).segments[0]


def _roundtrip_ticket(repo: AreaRepo, ticket: Ticket, slug: str = "t") -> Ticket:
    tid = repo.create_trip(slug, ticket)
    # An Itinerary requires >=1 segment — add a throwaway so we can load.
    repo.add_segment(tid, _seg())
    return repo.load_itinerary(tid).ticket


# ---------------------------------------------------------------------------
# Segment.via round-trip (None / single string / list)
# ---------------------------------------------------------------------------


def test_segment_via_none_roundtrips(repo):
    seg = _seg(via=None)
    assert _roundtrip_first_segment(repo, seg).via is None


def test_segment_via_single_string_normalized_to_list_then_roundtrips(repo):
    # Pydantic normalizer turns "DOH" -> ["DOH"]; DB stores JSON list.
    seg = _seg(via="DOH")
    assert seg.via == ["DOH"]  # pre-persist invariant
    loaded = _roundtrip_first_segment(repo, seg)
    assert loaded.via == ["DOH"]
    assert isinstance(loaded.via, list)


def test_segment_via_list_roundtrips(repo):
    seg = _seg(via=["DOH", "BKK"])
    loaded = _roundtrip_first_segment(repo, seg)
    assert loaded.via == ["DOH", "BKK"]


def test_segment_via_list_stored_as_json_in_db(repo):
    """Defensive: confirm the raw column is JSON, not a Python repr."""
    tid = repo.create_trip("t", _ticket())
    repo.add_segment(tid, _seg(via=["DOH", "BKK"]))
    row = repo.conn.execute(
        "SELECT via_json FROM segments WHERE trip_id=?", (tid,)
    ).fetchone()
    assert row["via_json"] == '["DOH", "BKK"]'


# ---------------------------------------------------------------------------
# Segment.carrier vs operating_carrier (codeshare)
# ---------------------------------------------------------------------------


def test_segment_marketing_carrier_roundtrips(repo):
    seg = _seg(carrier="BA", operating_carrier="IB")
    assert _roundtrip_first_segment(repo, seg).carrier == "BA"


def test_segment_operating_carrier_roundtrips(repo):
    seg = _seg(carrier="BA", operating_carrier="IB")
    assert _roundtrip_first_segment(repo, seg).operating_carrier == "IB"


def test_segment_operating_carrier_none_roundtrips(repo):
    seg = _seg(carrier="BA", operating_carrier=None)
    assert _roundtrip_first_segment(repo, seg).operating_carrier is None


# ---------------------------------------------------------------------------
# Segment.notes — unicode, long strings, None
# ---------------------------------------------------------------------------


def test_segment_notes_none_roundtrips(repo):
    seg = _seg(notes=None)
    assert _roundtrip_first_segment(repo, seg).notes is None


def test_segment_notes_unicode_roundtrips(repo):
    note = "Café stop — layover in København; 日本語 test; emoji pass-through"
    seg = _seg(notes=note)
    assert _roundtrip_first_segment(repo, seg).notes == note


def test_segment_notes_long_string_roundtrips(repo):
    note = "x" * 10_000
    seg = _seg(notes=note)
    assert _roundtrip_first_segment(repo, seg).notes == note


# ---------------------------------------------------------------------------
# Segment.date — None and a real date
# ---------------------------------------------------------------------------


def test_segment_date_none_roundtrips(repo):
    seg = _seg(date=None)
    assert _roundtrip_first_segment(repo, seg).date is None


def test_segment_date_real_date_roundtrips(repo):
    seg = _seg(date=date(2026, 4, 27))
    assert _roundtrip_first_segment(repo, seg).date == date(2026, 4, 27)


# ---------------------------------------------------------------------------
# Segment.flight — None, normal, leading-zero preservation
# ---------------------------------------------------------------------------


def test_segment_flight_none_roundtrips(repo):
    seg = _seg(flight=None)
    assert _roundtrip_first_segment(repo, seg).flight is None


def test_segment_flight_normal_string_roundtrips(repo):
    seg = _seg(flight="785")
    assert _roundtrip_first_segment(repo, seg).flight == "785"


def test_segment_flight_preserves_leading_zero(repo):
    seg = _seg(flight="049")
    assert _roundtrip_first_segment(repo, seg).flight == "049"


# ---------------------------------------------------------------------------
# Segment.type — all 4 enum values round-trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "seg_type",
    [
        SegmentType.STOPOVER,
        SegmentType.TRANSIT,
        SegmentType.SURFACE,
        SegmentType.FINAL,
    ],
)
def test_segment_type_enum_roundtrips(repo, seg_type):
    # SURFACE commonly has no carrier/flight/date — build that way so this
    # parametrization is realistic across all four.
    if seg_type == SegmentType.SURFACE:
        seg = _seg(carrier=None, flight=None, date=None, type=seg_type)
    else:
        seg = _seg(type=seg_type)
    assert _roundtrip_first_segment(repo, seg).type == seg_type


def test_surface_segment_preserves_none_carrier(repo):
    seg = _seg(
        "LHR", "CDG",
        carrier=None, flight=None, date=None, type=SegmentType.SURFACE,
    )
    loaded = _roundtrip_first_segment(repo, seg)
    assert loaded.carrier is None


def test_surface_segment_preserves_none_flight(repo):
    seg = _seg(
        "LHR", "CDG",
        carrier=None, flight=None, date=None, type=SegmentType.SURFACE,
    )
    assert _roundtrip_first_segment(repo, seg).flight is None


def test_surface_segment_preserves_none_date(repo):
    seg = _seg(
        "LHR", "CDG",
        carrier=None, flight=None, date=None, type=SegmentType.SURFACE,
    )
    assert _roundtrip_first_segment(repo, seg).date is None


def test_surface_segment_preserves_airports(repo):
    seg = _seg(
        "LHR", "CDG",
        carrier=None, flight=None, date=None, type=SegmentType.SURFACE,
    )
    loaded = _roundtrip_first_segment(repo, seg)
    assert (loaded.from_airport, loaded.to_airport) == ("LHR", "CDG")


# ---------------------------------------------------------------------------
# Ticket.type — all 12 TicketType variants round-trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticket_type", list(TicketType))
def test_ticket_type_enum_roundtrips(repo, ticket_type):
    ticket = _ticket(type=ticket_type)
    loaded = _roundtrip_ticket(repo, ticket, slug=f"t-{ticket_type.value}")
    assert loaded.type == ticket_type


# ---------------------------------------------------------------------------
# Ticket.cabin — all 3 CabinClass values
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cabin", list(CabinClass))
def test_ticket_cabin_enum_roundtrips(repo, cabin):
    ticket = _ticket(cabin=cabin)
    loaded = _roundtrip_ticket(repo, ticket, slug=f"t-{cabin.value}")
    assert loaded.cabin == cabin


# ---------------------------------------------------------------------------
# Ticket.passengers — range boundaries
# ---------------------------------------------------------------------------


def test_ticket_passengers_one_roundtrips(repo):
    ticket = _ticket(passengers=1)
    assert _roundtrip_ticket(repo, ticket).passengers == 1


def test_ticket_passengers_nine_roundtrips(repo):
    ticket = _ticket(passengers=9)
    assert _roundtrip_ticket(repo, ticket).passengers == 9


# ---------------------------------------------------------------------------
# Ticket.departure — None and real date
# ---------------------------------------------------------------------------


def test_ticket_departure_none_roundtrips(repo):
    ticket = _ticket(departure=None)
    assert _roundtrip_ticket(repo, ticket).departure is None


def test_ticket_departure_real_date_roundtrips(repo):
    ticket = _ticket(departure=date(2026, 4, 27))
    assert _roundtrip_ticket(repo, ticket).departure == date(2026, 4, 27)


# ---------------------------------------------------------------------------
# Ticket.plating_carrier — None + uppercase normalizer
# ---------------------------------------------------------------------------


def test_ticket_plating_carrier_none_roundtrips(repo):
    ticket = _ticket(plating_carrier=None)
    assert _roundtrip_ticket(repo, ticket).plating_carrier is None


def test_ticket_plating_carrier_two_letter_roundtrips(repo):
    ticket = _ticket(plating_carrier="CX")
    assert _roundtrip_ticket(repo, ticket).plating_carrier == "CX"


def test_ticket_plating_carrier_lowercase_stored_uppercase(repo):
    # Pydantic normalizer uppercases input; DB must preserve that.
    ticket = _ticket(plating_carrier="ba")
    assert ticket.plating_carrier == "BA"  # pre-persist invariant
    assert _roundtrip_ticket(repo, ticket).plating_carrier == "BA"


# ---------------------------------------------------------------------------
# Ticket.origin — uppercase normalizer round-trip
# ---------------------------------------------------------------------------


def test_ticket_origin_lowercase_stored_uppercase(repo):
    ticket = _ticket(origin="osl")
    assert ticket.origin == "OSL"  # pre-persist invariant
    assert _roundtrip_ticket(repo, ticket).origin == "OSL"


# ---------------------------------------------------------------------------
# Full Itinerary structural equality (JZXSWH + via + surface sector)
# ---------------------------------------------------------------------------


def test_jzxswh_with_via_and_surface_roundtrips_structural_equality(repo):
    """Full Itinerary.model_dump() must match byte-for-byte after a DB cycle."""
    from rtw.models import Itinerary

    ticket = _ticket(
        type=TicketType.DONE3,
        cabin=CabinClass.BUSINESS,
        origin="OSL",
        plating_carrier="CX",
        departure=date(2026, 4, 27),
        passengers=2,
    )
    segments = [
        Segment(
            **{"from": "OSL", "to": "LHR"},
            carrier="BA", flight="785", type=SegmentType.TRANSIT,
            date=date(2026, 4, 27),
        ),
        Segment(
            **{"from": "LHR", "to": "SIN"},
            carrier="QR", operating_carrier="QR", flight="1",
            type=SegmentType.STOPOVER, date=date(2026, 4, 28),
            via=["DOH"], notes="via DOH — fifth-freedom segment",
        ),
        Segment(
            **{"from": "SIN", "to": "KUL"},
            carrier=None, flight=None, date=None,
            type=SegmentType.SURFACE, notes="train/bus",
        ),
        Segment(
            **{"from": "KUL", "to": "HKG"},
            carrier="CX", flight="712", type=SegmentType.STOPOVER,
            date=date(2026, 5, 1),
        ),
        Segment(
            **{"from": "HKG", "to": "LHR"},
            carrier="CX", flight="253", type=SegmentType.STOPOVER,
            date=date(2026, 5, 8),
        ),
        Segment(
            **{"from": "LHR", "to": "OSL"},
            carrier="BA", flight="780", type=SegmentType.FINAL,
            date=date(2026, 10, 15),
        ),
    ]
    original = Itinerary(ticket=ticket, segments=segments)

    tid = repo.create_trip("jzxswh", ticket, pnr="JZXSWH")
    for s in segments:
        repo.add_segment(tid, s)
    loaded = repo.load_itinerary(tid)

    assert loaded.model_dump() == original.model_dump()
