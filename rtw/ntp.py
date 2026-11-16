"""NTP (New Tier Points) calculator for RTW itineraries.

Supports two earning methods:
- Distance-based: NTP = distance_miles * (rate_percentage / 100)
- Revenue-based: NTP = estimated GBP spend (1 NTP per GBP 1)

Rate data loaded from rtw/data/ntp_rates.yaml.
"""

import re
from pathlib import Path
from typing import Optional

import yaml

from rtw.carriers import get_booking_class
from rtw.codeshare import earning_band
from rtw.cost import CostEstimator, FareSource
from rtw.distance import DistanceCalculator
from rtw.models import (
    Itinerary,
    NTPEstimate,
    NTPMethod,
    Segment,
)

_DATA_DIR = Path(__file__).parent / "data"

# First-cabin RBDs. AONE on AS AT FJ IB RJ UL / AY intl already resolves to D
# (rtw.carriers, Rule 3015 §5(b)); an A booking with no verified first rate
# falls back to the D rate.
_FIRST_CLASSES = {"A", "F"}

# Airline designator at the start of a flight number: two characters, at least
# one a letter ("BA7001", "U2 123"), followed by the numeric part.
_FLIGHT_PREFIX_RE = re.compile(r"^\s*([A-Z]{2}|[A-Z]\d|\d[A-Z])\s*\d")


def _flight_prefix(flight: Optional[str]) -> Optional[str]:
    """Marketing carrier code from a flight number ('BA7001' -> 'BA')."""
    if not flight:
        return None
    m = _FLIGHT_PREFIX_RE.match(flight.upper())
    return m.group(1) if m else None

# Rough USD-to-GBP conversion rate
_USD_TO_GBP = 0.79

# Top business earning band (QR/JL/AY flexible D/C/J earn 50% of miles), used as
# the reference point when explaining why a segment earns "half". See
# docs/kb-... / rtw/data/ntp_rates.yaml.
_TOP_BUSINESS_RATE = 50.0


def _pct(x: float) -> str:
    """Format an earning percentage without spurious trailing zeros: 25 -> '25%',
    12.5 -> '12.5%'."""
    return f"{x:g}%"


class NTPCalculator:
    """Calculate NTP earnings for RTW itinerary segments."""

    def __init__(self) -> None:
        with open(_DATA_DIR / "ntp_rates.yaml") as f:
            self._rates = yaml.safe_load(f)

        self._fare_source = FareSource()
        self._cost = CostEstimator(fare_source=self._fare_source)

        self._distance_calc = DistanceCalculator()

        # Build sets for quick lookup
        self._revenue_carriers = set(self._rates["revenue_based"]["carriers"])
        self._distance_carriers = set(self._rates["distance_based"].keys())
        self._ba_bonus = self._rates.get("ba_bonus", {})
        self._ba_haul = self._rates.get("ba_bonus_haul", {})
        city_airports = self._ba_haul.get("city_airports", {})
        self._airport_city = {
            apt: city for city, apts in city_airports.items() for apt in apts
        }
        self._short_haul_routes = {
            frozenset(r.split("-")) for r in self._ba_haul.get("short_haul_routes", [])
        }

    # ------------------------------------------------------------------
    # Distance-based NTP
    # ------------------------------------------------------------------

    def _distance_based(
        self,
        segment_index: int,
        segment: Segment,
        distance_miles: float,
        booking_class: str,
        carrier: Optional[str] = None,
    ) -> NTPEstimate:
        """Calculate NTP for a distance-based carrier.

        ``carrier`` is the marketing carrier that earning keys on (defaults to
        ``segment.carrier``).
        """
        carrier = carrier or segment.carrier or ""
        carrier_rates = self._rates["distance_based"].get(carrier, {})
        d_rate = carrier_rates.get("D", 0)  # business-primary (flexible D) rate
        confidence = "calculated"
        note_parts: list[str] = []

        if (
            booking_class in _FIRST_CLASSES
            and booking_class not in carrier_rates
            and d_rate
        ):
            # First ticket on a carrier with no first cabin (Rule 3015 books
            # business D there) or no verified first rate in BA's table:
            # earn at D rather than silently returning 0%.
            rate = d_rate
            confidence = "estimated"
            note_parts.append(
                f"{carrier} has no first cabin or no verified first-class rate; "
                f"estimated at the business D rate ({_pct(d_rate)})"
            )
            booking_class = "D"
        else:
            rate = carrier_rates.get(booking_class, 0)

        ntp = distance_miles * (rate / 100)

        route = f"{segment.from_airport}-{segment.to_airport}"

        # FJ ATR-72 segments: D maps to Y cabin but still earns at D-class rate
        if carrier == "FJ" and distance_miles < 700 and booking_class == "D":
            note_parts.append("ATR-72 segment: D maps to Y cabin, earns at D-class rate")

        # Plain-language earning explanation (band vs 50% partners, or fallback drop)
        explanation = self._earning_note(carrier, booking_class, rate, d_rate)
        if explanation:
            note_parts.append(explanation)

        return NTPEstimate(
            segment_index=segment_index,
            route=route,
            carrier=carrier,
            distance_miles=distance_miles,
            method=NTPMethod.DISTANCE,
            rate=rate,
            estimated_ntp=round(ntp, 1),
            confidence=confidence,
            notes="; ".join(note_parts),
        )

    def _earning_note(
        self, carrier: str, booking_class: str, rate: float, d_rate: float
    ) -> str:
        """Explain a distance-carrier's earning rate in plain language.

        Two cases the user cares about:
        - The business-primary (D) bucket on a sub-50% carrier — e.g. CX/QF/MH
          earn 25% (half) and WY earns 12.5% (a quarter) of a 50%-band partner
          (QR/JL/AY).
        - A non-D bucket (e.g. a Rule 3015 B/H business fallback) that earns far
          less than D on the same carrier.
        """
        if booking_class == "D":
            if d_rate and d_rate < _TOP_BUSINESS_RATE:
                if d_rate == _TOP_BUSINESS_RATE / 2:
                    frac = "half"
                elif d_rate == _TOP_BUSINESS_RATE / 4:
                    frac = "a quarter"
                else:
                    frac = f"{d_rate / _TOP_BUSINESS_RATE:.0%}"
                return (
                    f"{carrier} business (D) earns {_pct(d_rate)} of miles — "
                    f"{frac} of a 50%-band partner (QR/JL/AY)"
                )
            return ""
        # Non-D bucket: flag the earning drop vs D on the same carrier.
        if d_rate and rate < d_rate:
            return (
                f"booked {booking_class}: earns {_pct(rate)} of miles "
                f"(D on {carrier} earns {_pct(d_rate)})"
            )
        return ""

    # ------------------------------------------------------------------
    # Revenue-based NTP
    # ------------------------------------------------------------------

    def _revenue_based(
        self,
        segment_index: int,
        segment: Segment,
        distance_miles: float,
        total_spend_usd: float,
        total_distance: float,
        cabin_prefix: str = "D",
        carrier: Optional[str] = None,
    ) -> NTPEstimate:
        """Calculate NTP for a revenue-based carrier.

        Uses distance-weighted allocation: each segment's share of the
        eligible spend (fare + YQ) is proportional to its share of total
        flown distance. ``cabin_prefix`` is the ticket's fare prefix (A/D/L)
        and, with the haul, picks the BA bonus. ``carrier`` is the marketing
        carrier (defaults to ``segment.carrier``).
        """
        carrier = carrier or segment.carrier or ""
        route = f"{segment.from_airport}-{segment.to_airport}"

        # Allocate eligible spend (fare + YQ) proportionally by distance
        if total_distance > 0:
            segment_share_usd = (distance_miles / total_distance) * total_spend_usd
        else:
            segment_share_usd = 0.0

        segment_share_gbp = segment_share_usd * _USD_TO_GBP
        ntp = segment_share_gbp  # 1 NTP per GBP 1

        notes_parts = [
            f"${segment_share_usd:.0f} of fare + YQ allocated ({distance_miles:.0f}/"
            f"{total_distance:.0f} mi), ~{chr(163)}{segment_share_gbp:.0f}"
        ]

        # BA bonus NTP: BA-marketed flights only, keyed on cabin and haul.
        # No AA/IB bonus is modelled (no first-party evidence held).
        if carrier == "BA":
            key, label = self._ba_bonus_key(segment, distance_miles, cabin_prefix)
            bonus = float(self._ba_bonus.get(key, 0))
            if bonus:
                ntp += bonus
                notes_parts.append(f"+{bonus:.0f} BA {label} bonus")

        return NTPEstimate(
            segment_index=segment_index,
            route=route,
            carrier=carrier,
            distance_miles=distance_miles,
            method=NTPMethod.REVENUE,
            rate=None,
            estimated_ntp=round(ntp, 1),
            confidence="estimated",
            notes="; ".join(notes_parts),
        )

    def _is_ba_short_haul(self, segment: Segment, distance_miles: float) -> bool:
        """BA bonus haul per BA's offer terms: short-haul is up to 2,000 miles
        on BA-operated flights, up to 3,000 miles otherwise, or a listed route."""
        a = self._airport_city.get(segment.from_airport, segment.from_airport)
        b = self._airport_city.get(segment.to_airport, segment.to_airport)
        if frozenset((a, b)) in self._short_haul_routes:
            return True
        operator = segment.operating_carrier or segment.carrier
        if operator == "BA":
            limit = self._ba_haul.get("short_haul_max_miles_ba_operated", 2000)
        else:
            limit = self._ba_haul.get("short_haul_max_miles_other", 3000)
        return distance_miles <= limit

    def _ba_bonus_key(
        self, segment: Segment, distance_miles: float, cabin_prefix: str
    ) -> tuple[str, str]:
        """Pick the ba_bonus key and its display label from cabin and haul.

        BA's terms treat First on a short-haul flight as Club Europe.
        """
        short = self._is_ba_short_haul(segment, distance_miles)
        if cabin_prefix == "L":
            return ("euro_traveller", "Euro Traveller") if short else (
                "world_traveller", "World Traveller")
        if cabin_prefix == "A":
            return ("club_europe", "Club Europe") if short else ("first", "First")
        return ("club_europe", "Club Europe") if short else ("club_world", "Club World")

    # ------------------------------------------------------------------
    # Full itinerary calculation
    # ------------------------------------------------------------------

    def calculate(
        self,
        itinerary: Itinerary,
        booking_class: Optional[str] = None,
        total_fare_usd: Optional[float] = None,
    ) -> list[NTPEstimate]:
        """Calculate NTP for every segment in the itinerary.

        Args:
            itinerary: The parsed itinerary.
            booking_class: Optional itinerary-wide RBD override for
                distance-based earning. Each segment resolves its class as
                ``Segment.booking_class``, then this override, then the
                ticket cabin's primary class for that carrier (D business,
                L economy, A first).
            total_fare_usd: Base fare in USD. If None, looked up through
                FareSource (fares.db). If no fare is filed for the origin,
                spend-based segments are labelled "fare unknown" with 0 NTP
                rather than estimated from a substitute fare. The
                itinerary's estimated YQ is added on top to form the
                eligible-spend pool (fare + YQ).

        Returns:
            List of NTPEstimate, one per segment (including 0-NTP surface sectors).
        """
        # Resolve total fare
        if total_fare_usd is None:
            total_fare_usd = self._default_fare(itinerary)

        # Eligible spend for BA/AA/IB-marketed segments is fare + YQ/YR.
        total_spend_usd: Optional[float] = None
        if total_fare_usd is not None:
            total_spend_usd = total_fare_usd + self._cost.estimate_surcharges(itinerary)

        cabin = itinerary.ticket.cabin
        cabin_prefix = itinerary.ticket.fare_prefix

        # Pre-compute all distances
        distances: list[float] = []
        for seg in itinerary.segments:
            if seg.is_surface:
                distances.append(0.0)
            else:
                distances.append(self._distance_calc.miles(seg.from_airport, seg.to_airport))

        total_distance = sum(distances)

        # Calculate NTP per segment
        results: list[NTPEstimate] = []
        for i, seg in enumerate(itinerary.segments):
            dist = distances[i]

            # Surface segments earn zero NTP
            if seg.is_surface:
                results.append(
                    NTPEstimate(
                        segment_index=i,
                        route=f"{seg.from_airport}-{seg.to_airport}",
                        carrier=seg.carrier or "SURFACE",
                        distance_miles=0.0,
                        method=NTPMethod.DISTANCE,
                        rate=0,
                        estimated_ntp=0.0,
                        confidence="calculated",
                        notes="Surface sector — no NTP earned",
                    )
                )
                continue

            # Earning follows the MARKETING carrier, i.e. the flight-number
            # prefix on the coupon. When it disagrees with seg.carrier, trust
            # the flight number and say so.
            prefix = _flight_prefix(seg.flight)
            carrier = prefix or seg.carrier or ""
            mismatch_note = ""
            if prefix and seg.carrier and prefix != seg.carrier:
                mismatch_note = (
                    f"flight {seg.flight} is {prefix}-marketed but carrier is "
                    f"{seg.carrier}; earning follows the flight number ({prefix})"
                )

            # Per-segment RBD wins, then the explicit override, then the ticket
            # cabin's primary class (D/L/A). A segment booked in a Rule 3015
            # fallback (e.g. B) earns at that class's rate, not D's.
            seg_class = (
                seg.booking_class
                or booking_class
                or get_booking_class(carrier, cabin, seg.from_airport, seg.to_airport)
            )

            # One source of truth for the earning method (shared with
            # codeshare.py), including codeshare spend-range exceptions.
            band = earning_band(carrier, seg.flight)

            if band.method == "spend" and total_spend_usd is None:
                est = self._fare_unknown(i, seg, dist, itinerary)
            elif band.method == "spend":
                est = self._revenue_based(
                    i, seg, dist, total_spend_usd, total_distance,
                    cabin_prefix=cabin_prefix, carrier=carrier,
                )
            elif band.method == "distance":
                est = self._distance_based(i, seg, dist, seg_class, carrier=carrier)
            else:
                # Unknown carrier — attempt distance-based with 0 rate
                est = self._distance_based(i, seg, dist, seg_class, carrier=carrier)
                est.notes = f"Unknown carrier {carrier}; no NTP rate found"

            # Jetstar-operated QF codeshares: BA Club earning on JQ-operated
            # flights is not confirmed from a first-party source, so keep the
            # QF estimate but say so rather than guess 0.
            jq_note = ""
            if seg.operating_carrier == "JQ":
                jq_note = (
                    "operated by Jetstar (JQ): tier-point earning on Jetstar-operated "
                    "flights is not confirmed, so this estimate may be too high"
                )

            extra = [n for n in (band.caveat, mismatch_note, jq_note) if n]
            if extra:
                est.notes = "; ".join([p for p in (est.notes, *extra) if p])

            results.append(est)

        return results

    def _default_fare(self, itinerary: Itinerary) -> Optional[float]:
        """Look up the itinerary's base fare through FareSource, or None if not filed."""
        quote = self._fare_source.get(itinerary.ticket.origin, itinerary.ticket.type)
        return quote.fare_usd if quote else None

    @staticmethod
    def _fare_unknown(
        segment_index: int, segment: Segment, distance_miles: float, itinerary: Itinerary
    ) -> NTPEstimate:
        """Spend-based segment when no fare is filed for the origin: no estimate."""
        return NTPEstimate(
            segment_index=segment_index,
            route=f"{segment.from_airport}-{segment.to_airport}",
            carrier=segment.carrier or "",
            distance_miles=distance_miles,
            method=NTPMethod.REVENUE,
            rate=None,
            estimated_ntp=0.0,
            confidence="fare unknown",
            notes=(
                f"Fare unknown: no filed {itinerary.ticket.type.value} fare for "
                f"origin {itinerary.ticket.origin}, so spend-based tier points "
                f"are not estimated"
            ),
        )
