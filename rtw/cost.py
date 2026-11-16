"""Cost estimator for RTW itineraries.

Estimates base fares, carrier-imposed surcharges (YQ), plating carrier
comparisons, and total trip cost.

Data loaded from:
- rtw/data/fares.db (filed-fare dump; the single source of base fares, read
  through FareSource)
- rtw/data/fares.yaml (explicit, source-annotated base-fare overrides only)
- rtw/data/surcharges.yaml (per-carrier YQ and plating comparison)
- rtw/data/carriers.yaml (carrier reference with yq_estimate_per_segment)
"""

import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Optional, Union

import yaml
from pydantic import BaseModel

from rtw.airports import airports_db
from rtw.models import CostEstimate, Itinerary, TicketType

_DATA_DIR = Path(__file__).parent / "data"
_FARES_DB = _DATA_DIR / "fares.db"
_FARE_OVERRIDES = _DATA_DIR / "fares.yaml"


class FareLookupError(Exception):
    """Raised when a fare lookup returns $0 (missing data)."""

    pass


# ------------------------------------------------------------------
# Fare source (fares.db + explicit overrides)
# ------------------------------------------------------------------

# Fares are filed per city. fares.db keys some cities by city code (LON, STO)
# and others by airport (NRT and HND both carry the Tokyo filings; there is no
# TYO row). Every airport in a group resolves to the group's city code, and the
# cheapest row across all member codes wins.
_METRO_GROUPS: dict[str, tuple[str, ...]] = {
    "LON": ("LON", "LHR", "LGW", "LCY", "STN", "LTN", "SEN"),
    "TYO": ("TYO", "NRT", "HND"),
    "STO": ("STO", "ARN"),
    "NYC": ("NYC", "JFK", "EWR", "LGA"),
    "WAS": ("WAS", "IAD", "DCA"),
}
_METRO_NAMES = {
    "LON": "London",
    "TYO": "Tokyo",
    "STO": "Stockholm",
    "NYC": "New York",
    "WAS": "Washington",
}
_CODE_TO_METRO = {code: metro for metro, codes in _METRO_GROUPS.items() for code in codes}

# Continent enum values (rtw.models.Continent) -> fares.db continent labels.
_CONTINENT_LABELS = {
    "EU_ME": "Europe/Middle East",
    "AFRICA": "Africa",
    "ASIA": "Asia",
    "SWP": "South West Pacific",
    "N_AMERICA": "North America",
    "S_AMERICA": "South America",
}


def fare_origin_key(origin: str) -> str:
    """Return the code fares are filed under for an airport or city code."""
    code = origin.upper()
    return _CODE_TO_METRO.get(code, code)


class FareQuote(BaseModel):
    """The base fare used for one origin and fare basis, with its provenance."""

    origin: str  # code the fare is filed under (city code for metro groups)
    fare_basis: str
    fare_usd: float
    carrier: str  # filing carrier(s) at this price, e.g. "QR" or "AA/AS/QR"
    country: str = ""
    continent: str = ""
    source: str  # "fares.db" or "fares.yaml override"
    note: str  # plain-language provenance shown to the user


@lru_cache(maxsize=4)
def _load_db(db_path: str) -> tuple[dict, dict]:
    """Load cheapest filed fare per (origin key, fare basis), plus metadata."""
    path = Path(db_path)
    if not path.exists():
        return {}, {}
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT origin, fare_basis, fare_usd, carrier, country, continent "
            "FROM fares WHERE fare_usd IS NOT NULL AND fare_usd > 0"
        ).fetchall()
        try:
            meta = dict(con.execute("SELECT key, value FROM metadata").fetchall())
        except sqlite3.OperationalError:
            meta = {}
    finally:
        con.close()

    best: dict[tuple[str, str], dict] = {}
    for origin, basis, fare, carrier, country, continent in rows:
        key = (fare_origin_key(origin), basis.upper())
        cur = best.get(key)
        if cur is None or fare < cur["fare_usd"]:
            best[key] = {
                "fare_usd": float(fare),
                "carriers": {carrier},
                "country": country or "",
                "continent": continent or "",
            }
        elif fare == cur["fare_usd"]:
            cur["carriers"].add(carrier)
    return best, meta


class FareSource:
    """Single source of base fares: MIN(fare_usd) from fares.db per origin.

    fares.yaml holds only explicit overrides, each of which must name its
    source. Nothing is estimated: an origin or fare basis with no filed row
    returns None.
    """

    def __init__(
        self,
        db_path: Path = _FARES_DB,
        overrides_path: Optional[Path] = _FARE_OVERRIDES,
    ) -> None:
        self._db_path = Path(db_path)
        self._best, self._meta = _load_db(str(self._db_path))
        self._overrides: dict[tuple[str, str], dict] = {}
        if overrides_path is not None and Path(overrides_path).exists():
            with open(overrides_path) as f:
                data = yaml.safe_load(f) or {}
            for origin, fares in (data.get("overrides") or {}).items():
                for basis, entry in (fares or {}).items():
                    if not isinstance(entry, dict) or "fare_usd" not in entry:
                        raise ValueError(
                            f"fares.yaml override {origin}/{basis} needs a fare_usd value"
                        )
                    if not entry.get("source"):
                        raise ValueError(
                            f"fares.yaml override {origin}/{basis} must name its source"
                        )
                    self._overrides[(fare_origin_key(origin), str(basis).upper())] = entry

    @property
    def data_date(self) -> Optional[str]:
        """Build date of the spreadsheet fares.db was made from (YYYY-MM-DD)."""
        value = self._meta.get("source_built")
        return value[:10] if value else None

    def _db_note(self, carrier: str) -> str:
        date = self.data_date or "unknown date"
        return f"Cheapest filed fare ({carrier}) from fares.db, data built {date}"

    def get(self, origin: str, fare_basis: Union[str, TicketType]) -> Optional[FareQuote]:
        """Return the cheapest fare for an origin and fare basis, or None."""
        basis = fare_basis.value if isinstance(fare_basis, TicketType) else str(fare_basis)
        key = (fare_origin_key(origin), basis.upper())
        db = self._best.get(key)
        override = self._overrides.get(key)
        if override is not None:
            carrier = str(override.get("carrier", ""))
            return FareQuote(
                origin=key[0],
                fare_basis=key[1],
                fare_usd=float(override["fare_usd"]),
                carrier=carrier,
                country=db["country"] if db else "",
                continent=db["continent"] if db else "",
                source="fares.yaml override",
                note=f"Override from fares.yaml: {override['source']}",
            )
        if db is None:
            return None
        carrier = "/".join(sorted(db["carriers"]))
        return FareQuote(
            origin=key[0],
            fare_basis=key[1],
            fare_usd=db["fare_usd"],
            carrier=carrier,
            country=db["country"],
            continent=db["continent"],
            source="fares.db",
            note=self._db_note(carrier),
        )

    def all_quotes(
        self, fare_basis: Union[str, TicketType], continent: Optional[str] = None
    ) -> list[FareQuote]:
        """Cheapest fare for every origin that files this fare basis, cheapest first.

        ``continent`` accepts a Continent enum value (e.g. "EU_ME", "Asia") or a
        fares.db label (e.g. "Europe/Middle East").
        """
        basis = fare_basis.value if isinstance(fare_basis, TicketType) else str(fare_basis)
        basis = basis.upper()
        wanted = None
        if continent:
            wanted = _CONTINENT_LABELS.get(continent.upper(), continent).lower()
        origins = {o for (o, b) in self._best if b == basis}
        origins |= {o for (o, b) in self._overrides if b == basis}
        quotes = []
        for origin in origins:
            quote = self.get(origin, basis)
            if quote is None:
                continue
            if wanted is not None and quote.continent.lower() != wanted:
                continue
            quotes.append(quote)
        quotes.sort(key=lambda q: (q.fare_usd, q.origin))
        return quotes


def _origin_name(code: str) -> str:
    if code in _METRO_NAMES:
        return _METRO_NAMES[code]
    info = airports_db.get(code)
    return info.get("city") or info.get("name") or code if info else code

# US airport codes for AA domestic zero-YQ rule (dynamic from airportsdata)
_US_AIRPORTS = {
    code for code, info in airports_db.items() if info.get("country") == "US"
}


class CostEstimator:
    """Estimate costs for oneworld Explorer RTW tickets."""

    def __init__(self, fare_source: Optional[FareSource] = None) -> None:
        self.fare_source = fare_source or FareSource()

        with open(_DATA_DIR / "surcharges.yaml") as f:
            self._surcharges = yaml.safe_load(f)

        with open(_DATA_DIR / "carriers.yaml") as f:
            self._carriers = yaml.safe_load(f)

    def get_base_fare(self, origin: str, ticket_type: TicketType) -> float:
        """Look up base fare for an origin and ticket type.

        Returns 0.0 if no fare is filed for that origin and ticket type.
        """
        quote = self.fare_source.get(origin, ticket_type)
        return quote.fare_usd if quote else 0.0

    def compare_origins(
        self, ticket_type: TicketType, continent: Optional[str] = None
    ) -> list[dict]:
        """Compare every origin that files this ticket type, cheapest first.

        ``continent`` optionally limits results to one continent (Continent enum
        value such as "EU_ME" or a fares.db label such as "Europe/Middle East").

        Returns list of dicts with keys: origin, name, fare_usd, currency, notes,
        carrier, country, continent, source.
        """
        return [
            {
                "origin": q.origin,
                "name": _origin_name(q.origin),
                "fare_usd": q.fare_usd,
                "currency": "USD",
                "notes": q.note,
                "carrier": q.carrier,
                "country": q.country,
                "continent": q.continent,
                "source": q.source,
            }
            for q in self.fare_source.all_quotes(ticket_type, continent)
        ]

    def estimate_surcharges(self, itinerary: Itinerary, plating_carrier: str = "AA") -> float:
        """Estimate total YQ surcharges for an itinerary.

        Rules:
        - Surface segments: $0 YQ
        - AA domestic (US-US): $0 YQ
        - Other segments: use carrier's yq_estimate_per_segment from
          carriers.yaml, falling back to surcharges.yaml carrier_yq
        """
        carrier_yq = self._surcharges.get("carrier_yq", {})
        total = 0.0

        for seg in itinerary.segments:
            # Surface segments: zero YQ
            if seg.is_surface:
                continue

            carrier = seg.carrier or ""

            # AA domestic (both airports in US): zero YQ
            if carrier == "AA" and self._is_us_domestic(seg.from_airport, seg.to_airport):
                continue

            # Look up per-segment YQ: carriers.yaml first, then surcharges.yaml
            carrier_data = self._carriers.get(carrier, {})
            yq = carrier_data.get("yq_estimate_per_segment")
            if yq is None:
                yq = carrier_yq.get(carrier, 0)

            total += float(yq)

        return total

    def compare_plating(self, itinerary: Itinerary) -> list[dict]:
        """Compare plating carrier options for an itinerary.

        Returns list sorted by total estimated cost (base + YQ), cheapest first.
        Each dict: plating_carrier, name, total_yq_usd, flexibility, notes.
        """
        plating = self._surcharges.get("plating_comparison", {})
        results = []

        for code, data in plating.items():
            carrier_data = self._carriers.get(code, {})
            results.append(
                {
                    "plating_carrier": code,
                    "name": carrier_data.get("name", code),
                    "total_yq_usd": float(data.get("typical_total_yq_usd", 0)),
                    "flexibility": data.get("flexibility", "unknown"),
                    "notes": data.get("notes", ""),
                }
            )

        results.sort(key=lambda x: x["total_yq_usd"])
        return results

    def estimate_total(self, itinerary: Itinerary, plating_carrier: str = "AA") -> CostEstimate:
        """Estimate total cost for an itinerary.

        Sums base_fare + total_yq per person, then multiplies by passengers.
        """
        origin = itinerary.ticket.origin
        ticket_type = itinerary.ticket.type
        passengers = itinerary.ticket.passengers

        quote = self.fare_source.get(origin, ticket_type)
        if quote is None:
            raise FareLookupError(
                f"No filed fare for origin={origin} ticket_type={ticket_type.value} "
                f"in rtw/data/fares.db (and no override in rtw/data/fares.yaml)."
            )
        base_fare = quote.fare_usd
        total_yq = self.estimate_surcharges(itinerary, plating_carrier)
        per_person = base_fare + total_yq
        total_all = per_person * passengers

        # Build notes
        notes_parts = []
        plating_data = self._surcharges.get("plating_comparison", {}).get(plating_carrier, {})
        if plating_data:
            notes_parts.append(plating_data.get("notes", ""))
        if plating_carrier == "AA":
            notes_parts.append("AA RTW desk offers best flexibility for mid-trip changes.")

        return CostEstimate(
            origin=origin,
            ticket_type=ticket_type,
            base_fare_usd=base_fare,
            total_yq_usd=total_yq,
            total_per_person_usd=per_person,
            total_all_pax_usd=total_all,
            passengers=passengers,
            plating_carrier=plating_carrier,
            fare_carrier=quote.carrier,
            fare_source=quote.note,
            notes=" ".join(notes_parts),
        )

    @staticmethod
    def _is_us_domestic(from_airport: str, to_airport: str) -> bool:
        """Check if both airports are in the US."""
        return from_airport in _US_AIRPORTS and to_airport in _US_AIRPORTS
