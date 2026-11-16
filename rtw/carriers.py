"""Shared carrier booking class resolution.

Resolves the correct booking class for a carrier/cabin combination using
the Rule 3015 §5(b) booking-code table in carriers.yaml (27 FEB 2026 filing).

- First (AONE*): A on AA/BA/CX/MH/QF/QR/JL/WY, D on AS/AT/FJ/IB/RJ/UL and
  AY international, Y on AY domestic, E on NU international.
- Business (DONE*): D everywhere except Y on AY domestic and E on NU
  international.
- Economy (LONE*): L everywhere.

Some carriers book differently on domestic flights (both airports in the
same country), so callers pass the segment's airports when they have them.

When the primary class is sold out, Rule 3015 permits a fallback class:
business may book B (H on AA); first may book Y.
"""

from pathlib import Path
from typing import Optional

import yaml

from rtw.models import CabinClass

_DATA_DIR = Path(__file__).parent / "data"
with open(_DATA_DIR / "carriers.yaml") as f:
    _CARRIERS: dict = yaml.safe_load(f)

# Used when a carrier has no §5(b) entry of its own (unknown/ineligible codes).
_DEFAULT_CLASSES = {
    CabinClass.FIRST: "A",
    CabinClass.BUSINESS: "D",
    CabinClass.ECONOMY: "L",
}

# "Where the applicable booking class for the lower class is not available,
# passengers travelling on First Class fares may book Y Class." (§5(b) NOTE)
_FIRST_FALLBACK_CLASS = "Y"


def is_domestic(from_airport: Optional[str], to_airport: Optional[str]) -> bool:
    """True when both airports are known and in the same country."""
    if not from_airport or not to_airport:
        return False

    from rtw.continents import get_country

    c1 = get_country(from_airport)
    c2 = get_country(to_airport)
    return c1 is not None and c1 == c2


def get_booking_class(
    carrier: Optional[str],
    cabin: CabinClass,
    from_airport: Optional[str] = None,
    to_airport: Optional[str] = None,
) -> str:
    """Return the primary booking class for a carrier/cabin combination.

    Pass the segment's airports so carriers with a separate domestic row
    (AY, NU) resolve correctly; without them the international row is used.
    Surface segments (carrier=None): returns D as safe default.

    Always returns a concrete single-letter string, never None.
    """
    if carrier is None:
        return "D"

    default = _DEFAULT_CLASSES.get(cabin, "D")
    carrier_data = _CARRIERS.get(carrier.upper()) or {}

    classes = carrier_data.get("rtw_booking_classes") or {}
    domestic = carrier_data.get("rtw_booking_classes_domestic")
    if domestic and is_domestic(from_airport, to_airport):
        classes = domestic

    return classes.get(cabin.value) or default


def get_fallback_class(
    carrier: Optional[str],
    cabin: CabinClass,
    from_airport: Optional[str] = None,
    to_airport: Optional[str] = None,
) -> Optional[str]:
    """Return the fallback booking class to try when the primary is sold out.

    Per Rule 3015 §5(b): DONE business passengers may book H on AA and B on
    every other eligible carrier (carriers.yaml rtw_fallback_class); First
    passengers may book Y on any carrier. Economy has no fallback.

    Returns None when no fallback applies (economy, surface segment, a
    carrier without a fallback defined, or a fallback identical to the
    primary class, e.g. First on AY domestic, which already books Y).
    """
    if carrier is None:
        return None

    if cabin == CabinClass.FIRST:
        fallback: Optional[str] = _FIRST_FALLBACK_CLASS
    elif cabin == CabinClass.BUSINESS:
        carrier_data = _CARRIERS.get(carrier.upper()) or {}
        fallback = carrier_data.get("rtw_fallback_class")
    else:
        return None

    if fallback is None:
        return None
    if fallback == get_booking_class(carrier, cabin, from_airport, to_airport):
        return None
    return fallback


# ---------------------------------------------------------------------------
# Rule 3015 §4(j) codeshare eligibility
# ---------------------------------------------------------------------------
#
# §(j): "Travel on any AA/AS/AT/AY/BA/CX/IB/JL/MH/NU/QF/QR/RJ/UL codeshare
# service operated by AA/AS/.../UL is permitted. Other codeshare services not
# permitted with the exception of QF Codeshare services operated by Jetstar
# (JQ)." The filing lists affiliates that operate on behalf of a member; a
# flight they operate counts as operated by that member.
#
# Operator code -> member(s) it flies for. Affiliates without their own IATA
# designator fly under the parent's code, so they need no entry here:
# BA Limited (BA), QantasLink operators and Jetconnect (QF), RAM Express (AT),
# HAC (ICAO NTH; flies JL numbers).
_CODESHARE_AFFILIATES: dict[str, frozenset[str]] = {
    "QX": frozenset({"AS"}),        # Horizon Air
    "OO": frozenset({"AS", "AA"}),  # SkyWest
    "MQ": frozenset({"AA"}),        # Envoy
    "YV": frozenset({"AA"}),        # Mesa
    "PT": frozenset({"AA"}),        # Piedmont
    "OH": frozenset({"AA"}),        # PSA
    "YX": frozenset({"AA"}),        # Republic
    "CJ": frozenset({"BA"}),        # BA CityFlyer
    "EZ": frozenset({"BA"}),        # SUN-AIR of Scandinavia
    "N7": frozenset({"AY"}),        # Nordic Regional Airlines
    "YW": frozenset({"IB"}),        # Air Nostrum (Iberia Regional)
    "I2": frozenset({"IB"}),        # Iberia Express
    "XM": frozenset({"JL"}),        # J-AIR
    "JC": frozenset({"JL"}),        # Japan Air Commuter
}

# The one non-member operator §(j) allows, and only under this marketing code.
_JETSTAR_EXCEPTION = ("QF", "JQ")


def eligible_codes() -> set[str]:
    """Carrier codes marked eligible for oneworld Explorer in carriers.yaml."""
    return {c for c, info in _CARRIERS.items() if (info or {}).get("eligible")}


def codeshare_permitted(
    marketing: Optional[str], operating: Optional[str] = None
) -> tuple[bool, str]:
    """Whether a marketing/operating pair is allowed under Rule 3015 §4(j).

    Returns ``(permitted, reason)``. ``reason`` explains a refusal, or names
    the exception or affiliate that made the pair pass ("" for a plain pass).
    A missing operating carrier means the marketing carrier operates it.
    """
    if not marketing:
        return True, ""
    m = marketing.upper()
    o = (operating or m).upper()
    eligible = eligible_codes()

    if m == "JQ":
        return False, (
            "JQ (Jetstar) flight numbers are not permitted; only QF-marketed "
            "flights operated by Jetstar are allowed"
        )
    if m not in eligible:
        return False, f"{m} is not an eligible oneworld Explorer carrier"
    if o == m or o in eligible:
        return True, ""
    if (m, o) == _JETSTAR_EXCEPTION:
        return True, "QF codeshare operated by Jetstar (JQ), the one non-member exception"
    parents = _CODESHARE_AFFILIATES.get(o, frozenset()) & eligible
    if parents:
        return True, f"{o} operates for {'/'.join(sorted(parents))}"
    return False, (
        f"{m}-marketed flight operated by {o}; codeshares are allowed only when "
        f"operated by an eligible oneworld carrier or its listed affiliate (or "
        f"QF-marketed Jetstar flights)"
    )
