"""Shared carrier booking class resolution.

Resolves the correct booking class for a carrier/cabin combination
using data from carriers.yaml. Business books D on every eligible
carrier (including AA). When D is sold out, Rule 3015 permits a
fallback class: B on all carriers except AA, which falls back to H.
"""

from pathlib import Path
from typing import Optional

import yaml

from rtw.models import CabinClass

_DATA_DIR = Path(__file__).parent / "data"
with open(_DATA_DIR / "carriers.yaml") as f:
    _CARRIERS: dict = yaml.safe_load(f)


def get_booking_class(carrier: Optional[str], cabin: CabinClass) -> str:
    """Return the primary booking class for a carrier/cabin combination.

    Business: D for all carriers (from carriers.yaml rtw_booking_class).
    Economy: L for all carriers.
    First: A for all carriers.
    Surface segments (carrier=None): returns D as safe default.

    Always returns a concrete single-letter string, never None.
    """
    if carrier is None:
        return "D"

    carrier = carrier.upper()

    if cabin == CabinClass.BUSINESS:
        carrier_data = _CARRIERS.get(carrier, {})
        return carrier_data.get("rtw_booking_class", "D")

    if cabin == CabinClass.ECONOMY:
        return "L"

    if cabin == CabinClass.FIRST:
        return "A"

    return "D"


def get_fallback_class(carrier: Optional[str], cabin: CabinClass) -> Optional[str]:
    """Return the fallback booking class to try when the primary is sold out.

    Per Rule 3015, DONE business passengers may book the fallback class when
    D is unavailable: H on AA, B on every other eligible carrier (from
    carriers.yaml rtw_fallback_class). Only defined for business; economy and
    first have no modelled fallback.

    Returns None when no fallback applies (non-business cabin, surface
    segment, or a carrier without a fallback class defined).
    """
    if carrier is None:
        return None

    if cabin != CabinClass.BUSINESS:
        return None

    carrier_data = _CARRIERS.get(carrier.upper(), {})
    return carrier_data.get("rtw_fallback_class")
