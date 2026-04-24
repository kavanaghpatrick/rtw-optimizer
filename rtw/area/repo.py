"""Area repo: trip + ordered-segment CRUD backed by SQLite.

Positions are 1-based and always contiguous — every mutation rebuilds
position numbers so ``SELECT ... ORDER BY position`` reflects the live
itinerary. Uses a negative-offset trick to avoid violating the
``UNIQUE (trip_id, position)`` constraint mid-statement.
"""

import json
import sqlite3
from datetime import date as Date
from typing import Any, Optional

from rtw.models import (
    CabinClass,
    Itinerary,
    Segment,
    SegmentType,
    Ticket,
    TicketType,
)


class TripNotFoundError(Exception):
    """Raised when a trip id or slug cannot be resolved."""


class NoActiveTripError(Exception):
    """Raised when an operation requires an active trip and none is set."""


class AreaRepo:
    """Thin repository over the area SQLite DB."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    # ---- trips ------------------------------------------------------------

    def create_trip(
        self,
        slug: str,
        ticket: Ticket,
        *,
        pnr: Optional[str] = None,
        set_active: bool = True,
    ) -> int:
        """Insert a new trip. If ``set_active`` is True, clear any existing
        active flag first (the partial unique index allows at most one)."""
        with self.conn:
            if set_active:
                self.conn.execute("UPDATE trips SET is_active = 0")
            cur = self.conn.execute(
                """INSERT INTO trips(slug, pnr, ticket_type, cabin, origin,
                                     passengers, departure, plating_carrier,
                                     is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    slug,
                    pnr,
                    ticket.type.value,
                    ticket.cabin.value,
                    ticket.origin,
                    ticket.passengers,
                    ticket.departure.isoformat() if ticket.departure else None,
                    ticket.plating_carrier,
                    1 if set_active else 0,
                ),
            )
            return int(cur.lastrowid)

    def list_trips(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """SELECT t.id, t.slug, t.pnr, t.ticket_type, t.cabin, t.origin,
                      t.passengers, t.departure, t.plating_carrier,
                      t.is_active, t.created_at, t.updated_at,
                      (SELECT COUNT(*) FROM segments s WHERE s.trip_id = t.id)
                          AS segment_count
               FROM trips t
               ORDER BY t.created_at DESC"""
        ).fetchall()
        return [dict(r) for r in rows]

    def get_trip_by_slug(self, slug: str) -> Optional[int]:
        row = self.conn.execute(
            "SELECT id FROM trips WHERE slug = ?", (slug,)
        ).fetchone()
        return int(row["id"]) if row else None

    def get_active_trip_id(self) -> Optional[int]:
        row = self.conn.execute(
            "SELECT id FROM trips WHERE is_active = 1"
        ).fetchone()
        return int(row["id"]) if row else None

    def get_active_or_raise(self) -> int:
        tid = self.get_active_trip_id()
        if tid is None:
            raise NoActiveTripError(
                "No active trip. Use `rtw area new` or `rtw area switch <slug>`."
            )
        return tid

    def set_active(self, trip_id: int) -> None:
        with self.conn:
            self._assert_trip_exists(trip_id)
            self.conn.execute("UPDATE trips SET is_active = 0")
            self.conn.execute(
                "UPDATE trips SET is_active = 1 WHERE id = ?", (trip_id,)
            )

    def delete_trip(self, trip_id: int) -> None:
        with self.conn:
            self._assert_trip_exists(trip_id)
            self.conn.execute("DELETE FROM trips WHERE id = ?", (trip_id,))

    # ---- segments ---------------------------------------------------------

    def add_segment(
        self,
        trip_id: int,
        seg: Segment,
        *,
        position: Optional[int] = None,
    ) -> None:
        """Insert a segment at ``position`` (1-based), or append if None.
        Shifts later segments up by 1 to keep positions contiguous."""
        with self.conn:
            self._assert_trip_exists(trip_id)
            n = self._seg_count(trip_id)
            if position is None:
                target = n + 1
            else:
                if position < 1 or position > n + 1:
                    raise ValueError(
                        f"position must be between 1 and {n + 1}, got {position}"
                    )
                target = position
            if target <= n:
                # Lift positions >= target to negatives, then shift up by 1.
                self.conn.execute(
                    """UPDATE segments SET position = -position
                       WHERE trip_id = ? AND position >= ?""",
                    (trip_id, target),
                )
                self.conn.execute(
                    """UPDATE segments SET position = -position + 1
                       WHERE trip_id = ? AND position < 0""",
                    (trip_id,),
                )
            self._insert_raw(trip_id, target, seg)
            self._touch_trip(trip_id)

    def remove_segment(self, trip_id: int, position: int) -> None:
        """Delete the segment at ``position`` and compact down."""
        with self.conn:
            self._assert_trip_exists(trip_id)
            n = self._seg_count(trip_id)
            if position < 1 or position > n:
                raise ValueError(
                    f"position must be between 1 and {n}, got {position}"
                )
            self.conn.execute(
                "DELETE FROM segments WHERE trip_id = ? AND position = ?",
                (trip_id, position),
            )
            self.conn.execute(
                """UPDATE segments SET position = -position
                   WHERE trip_id = ? AND position > ?""",
                (trip_id, position),
            )
            self.conn.execute(
                """UPDATE segments SET position = -position - 1
                   WHERE trip_id = ? AND position < 0""",
                (trip_id,),
            )
            self._touch_trip(trip_id)

    def move_segment(self, trip_id: int, from_pos: int, to_pos: int) -> None:
        """Reorder: remove from ``from_pos``, insert at ``to_pos``."""
        with self.conn:
            self._assert_trip_exists(trip_id)
            n = self._seg_count(trip_id)
            if not (1 <= from_pos <= n) or not (1 <= to_pos <= n):
                raise ValueError(
                    f"positions must be between 1 and {n}, got {from_pos} and {to_pos}"
                )
            if from_pos == to_pos:
                return
            rows = self.conn.execute(
                "SELECT id FROM segments WHERE trip_id = ? ORDER BY position",
                (trip_id,),
            ).fetchall()
            ids = [int(r["id"]) for r in rows]
            moved = ids.pop(from_pos - 1)
            ids.insert(to_pos - 1, moved)
            # Lift every row to a negative position, then re-seat by id.
            self.conn.execute(
                "UPDATE segments SET position = -position WHERE trip_id = ?",
                (trip_id,),
            )
            for new_pos, sid in enumerate(ids, start=1):
                self.conn.execute(
                    "UPDATE segments SET position = ? WHERE id = ?",
                    (new_pos, sid),
                )
            self._touch_trip(trip_id)

    # ---- load -------------------------------------------------------------

    def load_itinerary(self, trip_id: int) -> Itinerary:
        """Rebuild a Pydantic Itinerary. Raises if the trip has 0 segments
        (Itinerary requires min_length=1)."""
        self._assert_trip_exists(trip_id)
        trip = self.conn.execute(
            "SELECT * FROM trips WHERE id = ?", (trip_id,)
        ).fetchone()
        ticket = Ticket(
            type=TicketType(trip["ticket_type"]),
            cabin=CabinClass(trip["cabin"]),
            origin=trip["origin"],
            passengers=trip["passengers"],
            departure=(
                Date.fromisoformat(trip["departure"]) if trip["departure"] else None
            ),
            plating_carrier=trip["plating_carrier"],
        )
        seg_rows = self.conn.execute(
            "SELECT * FROM segments WHERE trip_id = ? ORDER BY position",
            (trip_id,),
        ).fetchall()
        segments = [self._row_to_segment(r) for r in seg_rows]
        return Itinerary(ticket=ticket, segments=segments)

    def list_segments(self, trip_id: int) -> list[dict[str, Any]]:
        """Return raw segment rows (handy for `show` when segments < 1)."""
        self._assert_trip_exists(trip_id)
        rows = self.conn.execute(
            "SELECT * FROM segments WHERE trip_id = ? ORDER BY position",
            (trip_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ---- internals --------------------------------------------------------

    def _seg_count(self, trip_id: int) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM segments WHERE trip_id = ?", (trip_id,)
        ).fetchone()
        return int(row["n"])

    def _assert_trip_exists(self, trip_id: int) -> None:
        row = self.conn.execute(
            "SELECT 1 FROM trips WHERE id = ?", (trip_id,)
        ).fetchone()
        if row is None:
            raise TripNotFoundError(f"Trip id {trip_id} not found")

    def _touch_trip(self, trip_id: int) -> None:
        self.conn.execute(
            "UPDATE trips SET updated_at = datetime('now') WHERE id = ?",
            (trip_id,),
        )

    def _insert_raw(self, trip_id: int, position: int, seg: Segment) -> None:
        self.conn.execute(
            """INSERT INTO segments(trip_id, position, from_airport, to_airport,
                                    carrier, operating_carrier, flight, date,
                                    segment_type, via_json, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                trip_id,
                position,
                seg.from_airport,
                seg.to_airport,
                seg.carrier,
                seg.operating_carrier,
                seg.flight,
                seg.date.isoformat() if seg.date else None,
                seg.type.value,
                json.dumps(seg.via) if seg.via else None,
                seg.notes,
            ),
        )

    @staticmethod
    def _row_to_segment(r: sqlite3.Row) -> Segment:
        return Segment(
            **{"from": r["from_airport"], "to": r["to_airport"]},
            carrier=r["carrier"],
            operating_carrier=r["operating_carrier"],
            flight=r["flight"],
            date=Date.fromisoformat(r["date"]) if r["date"] else None,
            type=SegmentType(r["segment_type"]),
            via=json.loads(r["via_json"]) if r["via_json"] else None,
            notes=r["notes"],
        )
