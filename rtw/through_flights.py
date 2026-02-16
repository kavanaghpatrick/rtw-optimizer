"""Through-flight reference data loader.

Known oneworld through-flights where intermediate stops add
cross-continent impact for pricing (Rule 3015 §16).
"""

from pathlib import Path
from typing import Optional

import yaml

_DATA_PATH = Path(__file__).parent / "data" / "through_flights.yaml"
_CACHE: Optional[dict] = None


def load_through_flights() -> dict:
    """Load through-flight reference data."""
    global _CACHE
    if _CACHE is None:
        with open(_DATA_PATH) as f:
            _CACHE = yaml.safe_load(f)
    return _CACHE


def get_cross_continent_flights() -> list[dict]:
    """Return only through-flights with cross-continent impact."""
    data = load_through_flights()
    return data.get("cross_continent", [])


def lookup_via_airports(carrier: str, from_apt: str, to_apt: str) -> list[str]:
    """Look up known via airports for a carrier/route pair.

    Returns list of via airport codes, or empty list if not a known through-flight.
    This is reference-only — users must still add `via:` explicitly to their segments.
    """
    for entry in get_cross_continent_flights():
        if (entry["carrier"] == carrier
                and entry["from"] == from_apt
                and entry["to"] == to_apt):
            return entry.get("via", [])
        # Check reverse direction too
        if (entry["carrier"] == carrier
                and entry["from"] == to_apt
                and entry["to"] == from_apt):
            return entry.get("via", [])
    return []
