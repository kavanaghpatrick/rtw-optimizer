#!/usr/bin/env python3
"""Build SQLite database from RTW fares Excel file."""

import sqlite3
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path

EXCEL_PATH = Path(__file__).parent.parent / "rtw" / "data" / "rtw_fares_all.xlsx"
DB_PATH = Path(__file__).parent.parent / "rtw" / "data" / "fares.db"


def xlsx_build_date(path: Path = EXCEL_PATH) -> str | None:
    """Return the spreadsheet's own build timestamp (docProps/core.xml modified)."""
    with zipfile.ZipFile(path) as zf:
        try:
            core = ET.fromstring(zf.read("docProps/core.xml"))
        except KeyError:
            return None
    ns = {"dcterms": "http://purl.org/dc/terms/"}
    for tag in ("dcterms:modified", "dcterms:created"):
        el = core.find(tag, ns)
        if el is not None and el.text:
            return el.text.strip()
    return None


def write_metadata(db: sqlite3.Connection, rebuilt: bool = True) -> None:
    """(Re)write the metadata table recording where and when the data came from."""
    db.execute("DROP TABLE IF EXISTS metadata")
    db.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)")
    rows = [
        ("source_file", EXCEL_PATH.name),
        ("source_built", xlsx_build_date() or ""),
        ("db_built" if rebuilt else "metadata_written", datetime.now(timezone.utc).isoformat(timespec="seconds")),
    ]
    db.executemany("INSERT INTO metadata VALUES (?, ?)", rows)
    print(f"  metadata: {dict(rows)}")


def build_db():
    import openpyxl

    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True)
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")

    # --- All Fares (main table) ---
    db.execute("DROP TABLE IF EXISTS fares")
    db.execute("""
        CREATE TABLE fares (
            origin TEXT NOT NULL,
            country TEXT,
            continent TEXT,
            carrier TEXT NOT NULL,
            fare_basis TEXT NOT NULL,
            booking_class TEXT,
            cabin TEXT,
            trip_type TEXT,
            fare_usd REAL,
            min_stay TEXT,
            max_stay TEXT,
            advance_purchase TEXT,
            effective TEXT,
            expiration TEXT
        )
    """)

    ws = wb["All Fares"]
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    db.executemany(
        "INSERT INTO fares VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    print(f"  fares: {len(rows)} rows")

    # --- Cheapest by Fare Type ---
    db.execute("DROP TABLE IF EXISTS cheapest")
    ws2 = wb["Cheapest by Fare Type"]
    header = [cell for cell in next(ws2.iter_rows(min_row=1, max_row=1, values_only=True))]
    cols_def = ", ".join(
        f'"{h}" TEXT' if i < 3 else f'"{h}" TEXT'
        for i, h in enumerate(header)
    )
    db.execute('DROP TABLE IF EXISTS cheapest')
    db.execute(f'CREATE TABLE cheapest ({cols_def})')

    rows2 = list(ws2.iter_rows(min_row=2, values_only=True))
    placeholders = ",".join(["?"] * len(header))
    db.executemany(f"INSERT INTO cheapest VALUES ({placeholders})", rows2)
    print(f"  cheapest: {len(rows2)} rows")

    # --- Summary ---
    db.execute("DROP TABLE IF EXISTS summary")
    ws3 = wb["Summary"]
    header3 = [cell for cell in next(ws3.iter_rows(min_row=1, max_row=1, values_only=True))]
    cols3 = []
    for h in header3:
        clean = h.replace(" ", "_").replace("(", "").replace(")", "")
        if "USD" in str(h):
            cols3.append(f'"{clean}" REAL')
        elif h == "Total Fares":
            cols3.append(f'"{clean}" INTEGER')
        else:
            cols3.append(f'"{clean}" TEXT')
    db.execute(f'CREATE TABLE summary ({", ".join(cols3)})')

    rows3 = list(ws3.iter_rows(min_row=2, values_only=True))
    placeholders3 = ",".join(["?"] * len(header3))
    db.executemany(f"INSERT INTO summary VALUES ({placeholders3})", rows3)
    print(f"  summary: {len(rows3)} rows")

    # --- Metadata (fares table has no effective/expiration dates) ---
    write_metadata(db)

    # --- Indexes ---
    db.execute("CREATE INDEX idx_fares_origin ON fares(origin)")
    db.execute("CREATE INDEX idx_fares_fare_basis ON fares(fare_basis)")
    db.execute("CREATE INDEX idx_fares_carrier ON fares(carrier)")
    db.execute("CREATE INDEX idx_fares_cabin ON fares(cabin)")
    db.execute("CREATE INDEX idx_fares_origin_basis ON fares(origin, fare_basis)")

    db.commit()
    db.close()
    print(f"\nDatabase: {DB_PATH} ({DB_PATH.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    if "--metadata-only" in sys.argv:
        # Add/refresh the metadata table on an existing fares.db without rebuilding.
        con = sqlite3.connect(DB_PATH)
        write_metadata(con, rebuilt=False)
        con.commit()
        con.close()
    else:
        build_db()
