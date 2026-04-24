"""Area DB: SQLite connection and schema bootstrap.

Default location: ``~/.rtw/area.db``. Override via the ``RTW_AREA_DB`` env var
or by passing an explicit path to :func:`open_area_db`.
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

_DEFAULT_PATH = Path.home() / ".rtw" / "area.db"

_SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS trips (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  slug             TEXT    NOT NULL UNIQUE,
  pnr              TEXT,
  ticket_type      TEXT    NOT NULL,
  cabin            TEXT    NOT NULL,
  origin           TEXT    NOT NULL,
  passengers       INTEGER NOT NULL DEFAULT 1,
  departure        TEXT,
  plating_carrier  TEXT,
  is_active        INTEGER NOT NULL DEFAULT 0,
  created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
  updated_at       TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_trips_active
  ON trips(is_active) WHERE is_active = 1;

CREATE TABLE IF NOT EXISTS segments (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  trip_id            INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  position           INTEGER NOT NULL,
  from_airport       TEXT    NOT NULL,
  to_airport         TEXT    NOT NULL,
  carrier            TEXT,
  operating_carrier  TEXT,
  flight             TEXT,
  date               TEXT,
  segment_type       TEXT    NOT NULL DEFAULT 'stopover',
  via_json           TEXT,
  notes              TEXT,
  UNIQUE (trip_id, position)
);
CREATE INDEX IF NOT EXISTS ix_segments_trip ON segments(trip_id, position);
"""


def default_db_path() -> Path:
    """Return the default area DB path, honoring ``RTW_AREA_DB`` env var."""
    env = os.environ.get("RTW_AREA_DB")
    return Path(env) if env else _DEFAULT_PATH


def open_area_db(path: Optional[Path] = None) -> sqlite3.Connection:
    """Open (creating if needed) the area SQLite DB and bootstrap schema."""
    p = path or default_db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    return conn
