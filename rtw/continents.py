"""Airport-to-continent classification using IATA Tariff Conferences."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from rtw.airports import airports_db as _airports_db
from rtw.models import Continent, TariffConference, CONTINENT_TO_TC

_DATA_DIR = Path(__file__).parent / "data"

# Load continent data
with open(_DATA_DIR / "continents.yaml") as f:
    _CONTINENT_DATA = yaml.safe_load(f)

_OVERRIDES: dict[str, str] = _CONTINENT_DATA.get("overrides", {})
_COUNTRIES: dict[str, list[str]] = _CONTINENT_DATA.get("countries", {})
_SEGMENT_LIMITS: dict[str, int] = _CONTINENT_DATA.get("segment_limits", {})
# Russia is split at the Urals (01-fare-rules.md §3) and resolved by longitude.
_RUSSIA_URALS_LON: float = float(_CONTINENT_DATA["russia_urals_longitude"])

# Build reverse country lookup: country_code -> continent_name
_COUNTRY_TO_CONTINENT: dict[str, str] = {}
for continent_name, country_codes in _COUNTRIES.items():
    for cc in country_codes:
        # Catch YAML 1.1 surprises (bare NO -> False) and duplicate listings.
        if not (isinstance(cc, str) and len(cc) == 2):
            raise ValueError(f"continents.yaml: bad country code {cc!r} under {continent_name}")
        if cc in _COUNTRY_TO_CONTINENT:
            raise ValueError(
                f"continents.yaml: {cc} listed under both "
                f"{_COUNTRY_TO_CONTINENT[cc]} and {continent_name}"
            )
        _COUNTRY_TO_CONTINENT[cc] = continent_name
if "RU" in _COUNTRY_TO_CONTINENT:
    raise ValueError("continents.yaml: RU must not be in countries; it is split at the Urals")

# Load same-city groups
with open(_DATA_DIR / "same_cities.yaml") as f:
    _SAME_CITIES: dict[str, list[str]] = yaml.safe_load(f)

# Build reverse lookup: airport -> city group
_AIRPORT_TO_CITY_GROUP: dict[str, str] = {}
for group_name, airports in _SAME_CITIES.items():
    for apt in airports:
        _AIRPORT_TO_CITY_GROUP[apt] = group_name


def get_continent(airport_code: str) -> Optional[Continent]:
    """Get the continent for an airport code.

    Resolution order:
    1. Explicit overrides (CAI -> EU_ME, GUM -> Asia, etc.)
    2. Russia: Asia east of the Urals, Europe/Middle East west of them
       (01-fare-rules.md §3), decided by the airport's longitude
    3. Country lookup via airportsdata
    4. None if unknown
    """
    code = airport_code.upper()

    # Check overrides first
    if code in _OVERRIDES:
        return Continent(_OVERRIDES[code])

    # Try airportsdata country lookup
    if code in _airports_db:
        info = _airports_db[code]
        country = info.get("country", "")
        if country == "RU":
            if float(info["lon"]) > _RUSSIA_URALS_LON:
                return Continent.ASIA
            return Continent.EU_ME
        # airportsdata uses ISO 2-letter country codes
        if country in _COUNTRY_TO_CONTINENT:
            return Continent(_COUNTRY_TO_CONTINENT[country])

    return None


def get_tariff_conference(continent: Continent) -> TariffConference:
    """Get the Tariff Conference for a continent."""
    return CONTINENT_TO_TC[continent]


def get_segment_limit(continent: Continent) -> int:
    """Get the per-continent segment limit."""
    return _SEGMENT_LIMITS.get(continent.value, 4)


def get_same_city_group(airport_code: str) -> Optional[str]:
    """Get the same-city group for an airport, or None."""
    return _AIRPORT_TO_CITY_GROUP.get(airport_code.upper())


def are_same_city(airport1: str, airport2: str) -> bool:
    """Check if two airports are in the same city group."""
    g1 = get_same_city_group(airport1)
    g2 = get_same_city_group(airport2)
    if g1 is None or g2 is None:
        return airport1.upper() == airport2.upper()
    return g1 == g2


# ---------------------------------------------------------------------------
# Country helpers
# ---------------------------------------------------------------------------


def get_country(airport_code: str) -> Optional[str]:
    """Get ISO 2-letter country code for an airport."""
    code = airport_code.upper()
    info = _airports_db.get(code)
    return info["country"] if info else None


_COUNTRY_NAMES: dict[str, str] = {
    "AU": "Australia",
    "NZ": "New Zealand",
    "GB": "United Kingdom",
    "US": "United States",
    "CA": "Canada",
    "JP": "Japan",
    "HK": "Hong Kong",
    "CN": "China",
    "TW": "Taiwan",
    "SG": "Singapore",
    "MY": "Malaysia",
    "TH": "Thailand",
    "IN": "India",
    "LK": "Sri Lanka",
    "MV": "Maldives",
    "KR": "South Korea",
    "PH": "Philippines",
    "ID": "Indonesia",
    "VN": "Vietnam",
    "QA": "Qatar",
    "AE": "United Arab Emirates",
    "SA": "Saudi Arabia",
    "BH": "Bahrain",
    "KW": "Kuwait",
    "OM": "Oman",
    "JO": "Jordan",
    "IL": "Israel",
    "YE": "Yemen",
    "IQ": "Iraq",
    "LB": "Lebanon",
    "SY": "Syria",
    "PS": "Palestine",
    "EG": "Egypt",
    "ZA": "South Africa",
    "KE": "Kenya",
    "ET": "Ethiopia",
    "NG": "Nigeria",
    "MA": "Morocco",
    "TZ": "Tanzania",
    "DE": "Germany",
    "FR": "France",
    "ES": "Spain",
    "IT": "Italy",
    "PT": "Portugal",
    "NL": "Netherlands",
    "CH": "Switzerland",
    "AT": "Austria",
    "SE": "Sweden",
    "NO": "Norway",
    "DK": "Denmark",
    "FI": "Finland",
    "IE": "Ireland",
    "GR": "Greece",
    "TR": "Turkey",
    "RU": "Russia",
    "BR": "Brazil",
    "AR": "Argentina",
    "CL": "Chile",
    "PE": "Peru",
    "CO": "Colombia",
    "MX": "Mexico",
    "FJ": "Fiji",
}


def get_country_name(country_code: str) -> str:
    """Get full English country name. Falls back to uppercase code."""
    return _COUNTRY_NAMES.get(country_code.upper(), country_code.upper())


# ---------------------------------------------------------------------------
# Regional country sets
# ---------------------------------------------------------------------------

# Both sets come from continents.yaml so they cannot drift from get_continent().
MIDDLE_EAST_COUNTRIES: frozenset[str] = frozenset(_CONTINENT_DATA["middle_east"])

AFRICA_COUNTRIES: frozenset[str] = frozenset(_COUNTRIES["Africa"])

_ME_NOT_EU_ME = MIDDLE_EAST_COUNTRIES - set(_COUNTRIES["EU_ME"])
if _ME_NOT_EU_ME:
    raise ValueError(
        f"continents.yaml: middle_east codes not under EU_ME: {sorted(_ME_NOT_EU_ME)}"
    )


# ---------------------------------------------------------------------------
# Open-jaw permission check (Rule 3015 §18)
# ---------------------------------------------------------------------------


@dataclass
class OpenJawResult:
    permitted: bool
    reason: str


# Bilateral pairs for open-jaw
_OPEN_JAW_BILATERAL: list[tuple[frozenset[str], frozenset[str]]] = [
    (frozenset({"US"}), frozenset({"CA"})),          # USA <-> Canada
    (frozenset({"HK"}), frozenset({"CN"})),          # Hong Kong <-> China
    (frozenset({"MY"}), frozenset({"SG"})),          # Malaysia <-> Singapore
    (frozenset({"MV"}), frozenset({"LK", "IN"})),    # Maldives <-> Sri Lanka/India
]


def check_open_jaw_permitted(origin: str, dest: str) -> OpenJawResult:
    """Check if an open-jaw between two airports is permitted per Rule 3015 §18."""
    origin_country = get_country(origin)
    dest_country = get_country(dest)

    if not origin_country or not dest_country:
        return OpenJawResult(
            False, f"Unknown airport: {origin if not origin_country else dest}"
        )

    # 1. Same country
    if origin_country == dest_country:
        name = get_country_name(origin_country)
        return OpenJawResult(True, f"both in {name}")

    # 2. Bilateral pairs
    for set_a, set_b in _OPEN_JAW_BILATERAL:
        if (origin_country in set_a and dest_country in set_b) or \
           (origin_country in set_b and dest_country in set_a):
            name_a = get_country_name(origin_country)
            name_b = get_country_name(dest_country)
            return OpenJawResult(True, f"{name_a} \u2194 {name_b}")

    # 3. Both in Middle East
    if origin_country in MIDDLE_EAST_COUNTRIES and dest_country in MIDDLE_EAST_COUNTRIES:
        return OpenJawResult(True, "both in Middle East")

    # 4. Both in Africa
    if origin_country in AFRICA_COUNTRIES and dest_country in AFRICA_COUNTRIES:
        return OpenJawResult(True, "both in Africa")

    name_a = get_country_name(origin_country)
    name_b = get_country_name(dest_country)
    return OpenJawResult(
        False, f"{name_a} and {name_b} are not a permitted open-jaw pair"
    )
