"""Codeshare tier-point earning checker.

A single physical flight is often sold under several oneworld codeshare flight
numbers. BA-Club tier points are credited on the **marketing** carrier (the
flight number on the coupon), read against that carrier's booking-class table
-- confirmed by BA's own T&Cs. So ticketing a leg under a higher-earning
codeshare (e.g. a 50%-band QR/JL number instead of a 25% CX number) can raise
Tier Points on the *same seat*.

This module maps a marketing carrier to its earning band and ranks codeshare
options for a leg. What it deliberately does NOT do:

- It applies the Rule 3015 §4(j) codeshare test (eligible marketing carrier on
  a flight operated by an eligible carrier or listed affiliate, or QF on
  Jetstar) and drops options that fail it, but it cannot confirm the fare
  permits re-marketing a particular coupon -- that stays a question for the
  ticketing agent.
- Codeshare booking-class inventory is a separate, often thinner bucket, so D
  availability must be checked per marketing code (ExpertFlyer, codeshares
  shown) and finally confirmed in the GDS.

Earning bands come from rtw/data/ntp_rates.yaml (the same source the NTP
calculator uses). See docs / memory rtw_ba_earning_rules_and_gap.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

from rtw.carriers import codeshare_permitted

_DATA_DIR = Path(__file__).parent / "data"

# Reference: the top oneworld business band (QR/JL/AY flexible D/C/J = 50%).
_TOP_BUSINESS_RATE = 50.0

# Codeshare-specific earning exceptions: some carriers pay SPEND-based tier
# points (not their normal distance band) when the leg is flown under a
# CODESHARE flight number in a given numeric range. Finnair moved codeshares
# AY2501-AY7000 to spend-based on 2025-06-03. Extend as new exceptions are
# verified (e.g. from the codeshare-arbitrage research).
#
# Each range is (lo, hi, verified_for_ba_club). The AY range is NOT verified
# for BA Club crediting: the evidence is a Finnair Plus programme change, not a
# BA Club rule, so results that rely on it carry a caveat.
_CODESHARE_SPEND_RANGES: dict[str, list[tuple[int, int, bool]]] = {
    "AY": [(2501, 7000, False)],
}

_UNVERIFIED_RANGE_CAVEAT = (
    "codeshare spend-based range is from a Finnair Plus change and is "
    "unverified for BA Club crediting"
)


class EarningBand(BaseModel):
    """How a marketing carrier credits BA-Club tier points for a business fare."""

    carrier: str
    method: str  # "spend" | "distance" | "unknown"
    pct: Optional[float] = None  # distance %-of-miles for business D (if distance)
    label: str
    caveat: str = ""  # set when the band rests on evidence unverified for BA Club


class CodeshareOption(BaseModel):
    """One marketing flight number that sells a given physical flight."""

    marketing_carrier: str
    marketing_flight: Optional[str] = None
    operating_carrier: Optional[str] = None
    depart_time: Optional[str] = None
    d_seats: Optional[int] = None  # D-class seats under THIS marketing code (None = unknown)
    earning: EarningBand
    estimated_tp: Optional[float] = None  # distance method + known distance only
    is_current: bool = False
    eligible: bool = True  # False when Rule 3015 §4(j) forbids this marketing/operating pair
    note: str = ""


class CodeshareAnalysis(BaseModel):
    """Ranked codeshare options for a leg, best-earning first."""

    route: str
    distance_miles: Optional[float] = None
    booking_class: str = "D"
    options: list[CodeshareOption] = Field(default_factory=list)
    current: Optional[CodeshareOption] = None
    best_bookable: Optional[CodeshareOption] = None
    tp_gain: Optional[float] = None  # best_bookable vs current (distance methods)
    caveats: list[str] = Field(default_factory=list)


# --- rate data ---------------------------------------------------------------

_rates = yaml.safe_load(open(_DATA_DIR / "ntp_rates.yaml"))
_SPEND_CARRIERS = set(_rates["revenue_based"]["carriers"])
_DISTANCE_RATES: dict = _rates["distance_based"]


def _flight_int(flight_number: Optional[str]) -> Optional[int]:
    """Extract the numeric part of a flight number ('QR6969' -> 6969)."""
    if not flight_number:
        return None
    m = re.search(r"(\d{1,4})", flight_number)
    return int(m.group(1)) if m else None


def _codeshare_spend_range(
    carrier: str, flight_number: Optional[str]
) -> Optional[tuple[int, int, bool]]:
    """The spend-based codeshare range this flight number falls in, if any."""
    ranges = _CODESHARE_SPEND_RANGES.get(carrier.upper(), [])
    n = _flight_int(flight_number)
    if not ranges or n is None:
        return None
    return next((r for r in ranges if r[0] <= n <= r[1]), None)


def _codeshare_earns_spend(carrier: str, flight_number: Optional[str]) -> bool:
    """Whether this codeshare number falls in a known spend-based range."""
    return _codeshare_spend_range(carrier, flight_number) is not None


def earning_band(carrier: str, flight_number: Optional[str] = None) -> EarningBand:
    """Resolve a marketing carrier's business-D tier-point earning band.

    ``flight_number`` lets codeshare-specific spend exceptions apply (e.g.
    Finnair AY2501-AY7000).
    """
    c = (carrier or "").upper()

    spend_range = _codeshare_spend_range(c, flight_number) if flight_number else None
    if spend_range is not None:
        lo, hi, verified = spend_range
        return EarningBand(
            carrier=c, method="spend", pct=None,
            label="spend-based (codeshare exception)",
            caveat="" if verified else f"{c}{lo}-{c}{hi} {_UNVERIFIED_RANGE_CAVEAT}",
        )
    if c in _SPEND_CARRIERS:
        return EarningBand(carrier=c, method="spend", pct=None, label="spend-based")
    rates = _DISTANCE_RATES.get(c)
    if rates is None:
        return EarningBand(carrier=c, method="unknown", pct=None, label="unknown carrier")
    pct = float(rates.get("D", 0))
    return EarningBand(carrier=c, method="distance", pct=pct, label=f"{pct:g}% of miles")


def _band_descriptor(pct: float) -> str:
    """'half' / 'a quarter' relative to a 50%-band partner."""
    if pct == _TOP_BUSINESS_RATE:
        return "top 50% band"
    if pct == _TOP_BUSINESS_RATE / 2:
        return "half of a 50%-band partner"
    if pct == _TOP_BUSINESS_RATE / 4:
        return "a quarter of a 50%-band partner"
    return f"{pct / _TOP_BUSINESS_RATE:.0%} of a 50%-band partner"


_STANDARD_CAVEATS = [
    "Earning follows the MARKETING carrier (ticketed flight number), read "
    "against that carrier's booking-class table (BA T&Cs).",
    "CONFIRM WITH AGENT: an oneworld Explorer (Rule 3015) fare may not permit "
    "re-marketing a coupon under a chosen partner code -- verify before booking.",
    "Codeshare D inventory is a separate, thinner bucket; ExpertFlyer is "
    "point-of-sale-based (POS != POC), so confirm the partner code books in D "
    "on the actual RTW fare in the GDS.",
]


def _ineligible_note(reason: str) -> str:
    return f"not permitted on oneworld Explorer (Rule 3015 §4(j)): {reason}"


def analyze_codeshares(
    options: list[CodeshareOption],
    *,
    distance_miles: Optional[float] = None,
    current_carrier: Optional[str] = None,
    route: str = "",
    booking_class: str = "D",
) -> CodeshareAnalysis:
    """Rank codeshare options by tier-point earning and find the best swap.

    ``options`` should already carry an ``earning`` band (use
    :func:`build_options`). Distance-method options are ranked by percentage
    then by D availability; spend/unknown options rank below any distance
    option (on a cheap RTW through-fare, spend-based earns little).
    """
    current = next((o for o in options if o.is_current), None)
    if current is None and current_carrier:
        current = next(
            (o for o in options if o.marketing_carrier.upper() == current_carrier.upper()),
            None,
        )

    # Rule 3015 §4(j): an option the fare does not permit cannot be a swap.
    for o in options:
        ok, reason = codeshare_permitted(o.marketing_carrier, o.operating_carrier)
        if not ok and o.eligible:
            o.eligible = False
            o.note = (o.note + "; " if o.note else "") + _ineligible_note(reason)

    # Compute estimated TP for distance options when distance is known.
    for o in options:
        if not o.eligible:
            o.estimated_tp = None
            continue
        if o.earning.method == "distance" and o.earning.pct and distance_miles:
            o.estimated_tp = round(distance_miles * o.earning.pct / 100, 1)
        if o.earning.method == "distance" and o.earning.pct and o.earning.pct < _TOP_BUSINESS_RATE:
            desc = _band_descriptor(o.earning.pct)
            if desc and "top" not in desc:
                o.note = (o.note + "; " if o.note else "") + desc

    def rank_key(o: CodeshareOption):
        is_dist = o.earning.method == "distance"
        pct = o.earning.pct if (is_dist and o.earning.pct) else -1.0
        seats = o.d_seats if o.d_seats is not None else -1
        return (pct, seats)

    ranked = sorted(options, key=rank_key, reverse=True)

    # Best bookable = highest-pct distance option with D seats confirmed open
    # (or unknown seats, flagged). Prefer strictly better than current.
    def is_distance(o: CodeshareOption) -> bool:
        return o.eligible and o.earning.method == "distance" and bool(o.earning.pct)

    bookable = [o for o in ranked if is_distance(o) and (o.d_seats is None or o.d_seats > 0)]
    best_bookable = bookable[0] if bookable else None

    tp_gain = None
    if (
        best_bookable is not None
        and current is not None
        and best_bookable.estimated_tp is not None
        and current.estimated_tp is not None
        and best_bookable is not current
    ):
        tp_gain = round(best_bookable.estimated_tp - current.estimated_tp, 1)

    caveats = list(_STANDARD_CAVEATS)
    if any(o.earning.label.endswith("(codeshare exception)") for o in options):
        caveats.append(
            "Some codeshares earn spend-based despite a distance-band carrier "
            "(e.g. Finnair AY2501-AY7000 since 2025-06-03, a Finnair Plus change "
            "unverified for BA Club) -- excluded from the swap."
        )
    if best_bookable is not None and best_bookable.d_seats is None:
        caveats.append(
            "Best option's D availability is UNKNOWN from this data -- verify "
            "the partner code has D seats before assuming the swap is bookable."
        )

    return CodeshareAnalysis(
        route=route,
        distance_miles=distance_miles,
        booking_class=booking_class,
        options=ranked,
        current=current,
        best_bookable=best_bookable,
        tp_gain=tp_gain,
        caveats=caveats,
    )


def build_options(
    rows: list[dict],
    *,
    current_carrier: Optional[str] = None,
) -> list[CodeshareOption]:
    """Build CodeshareOption objects (with earning bands) from raw rows.

    Each row: {marketing_carrier, marketing_flight?, operating_carrier?,
    depart_time?, d_seats?}. ``current_carrier`` marks the currently-ticketed
    marketing carrier.
    """
    out: list[CodeshareOption] = []
    for r in rows:
        mc = str(r["marketing_carrier"]).upper()
        mf = r.get("marketing_flight")
        oc = (r.get("operating_carrier") or None)
        oc = oc.upper() if oc else None
        ok, reason = codeshare_permitted(mc, oc)
        out.append(
            CodeshareOption(
                marketing_carrier=mc,
                marketing_flight=mf,
                operating_carrier=oc,
                depart_time=r.get("depart_time"),
                d_seats=r.get("d_seats"),
                earning=earning_band(mc, mf),
                is_current=bool(current_carrier and mc == current_carrier.upper()),
                eligible=ok,
                note="" if ok else _ineligible_note(reason),
            )
        )
    return out
