"""Booking script generator for oneworld Explorer RTW tickets.

Generates phone scripts (natural-language instructions for calling the airline)
and Amadeus GDS commands for booking an RTW itinerary.

Data loaded from:
- rtw/data/carriers.yaml (booking classes per carrier)
- rtw/data/same_cities.yaml (same-city airport groups for warnings)
"""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

from rtw.models import CabinClass, Itinerary, SegmentType

_DATA_DIR = Path(__file__).parent / "data"

# Round-the-world global indicator and the mandatory ticket endorsement are
# first-party facts, quoted verbatim from carrier/alliance agent references
# (Qantas oneworld clue card; oneworld alliance Rule 3015 §18). See
# docs/kb-owe-rtw-gds-firstparty.md.
_RTW_GLOBAL_INDICATOR = "RW"
_RTW_ENDORSEMENT = "VALID ON ONEWORLD ONLY / NON REF"


# --- Data Models ---


class SegmentScript(BaseModel):
    """Phone script and GDS entry for a single segment."""

    segment_index: int
    route: str
    carrier: Optional[str] = None
    booking_class: Optional[str] = None
    fallback_class: Optional[str] = None
    phone_instruction: str
    gds_command: str = ""
    warnings: list[str] = Field(default_factory=list)


class BookingScript(BaseModel):
    """Complete booking script with phone instructions and GDS commands."""

    opening: str
    segments: list[SegmentScript]
    closing: str
    gds_commands: list[str]
    warnings: list[str] = Field(default_factory=list)


# --- Generator ---


class BookingGenerator:
    """Generate phone scripts and GDS commands for RTW bookings."""

    def __init__(self) -> None:
        with open(_DATA_DIR / "carriers.yaml") as f:
            self._carriers: dict = yaml.safe_load(f)

        with open(_DATA_DIR / "same_cities.yaml") as f:
            self._same_cities: dict[str, list[str]] = yaml.safe_load(f)

        # Build reverse lookup: airport -> city group name
        self._airport_to_city: dict[str, str] = {}
        for group, airports in self._same_cities.items():
            for apt in airports:
                self._airport_to_city[apt] = group

    # --- Booking class logic (T031) ---

    def _get_booking_class(
        self,
        carrier: Optional[str],
        cabin: CabinClass,
        from_airport: Optional[str] = None,
        to_airport: Optional[str] = None,
    ) -> Optional[str]:
        """Determine the booking class for a carrier/cabin combination.

        Delegates to shared utility in rtw.carriers. The airports let
        carriers with a domestic row (AY, NU) resolve correctly. Returns
        None for surface segments (carrier=None).
        """
        if carrier is None:
            return None

        from rtw.carriers import get_booking_class

        return get_booking_class(carrier, cabin, from_airport, to_airport)

    def _get_fallback_class(
        self,
        carrier: Optional[str],
        cabin: CabinClass,
        from_airport: Optional[str] = None,
        to_airport: Optional[str] = None,
    ) -> Optional[str]:
        """Determine the fallback booking class (business: H on AA, B
        otherwise; first: Y).

        Delegates to shared utility in rtw.carriers. Returns None when no
        fallback applies (surface segment or economy cabin).
        """
        if carrier is None:
            return None

        from rtw.carriers import get_fallback_class

        return get_fallback_class(carrier, cabin, from_airport, to_airport)

    def _is_same_city(self, airport1: str, airport2: str) -> bool:
        """Check if two airports are in the same city group."""
        g1 = self._airport_to_city.get(airport1.upper())
        g2 = self._airport_to_city.get(airport2.upper())
        if g1 is None or g2 is None:
            return airport1.upper() == airport2.upper()
        return g1 == g2

    def _get_city_group_name(self, airport: str) -> Optional[str]:
        """Get the city group name for an airport, or None."""
        return self._airport_to_city.get(airport.upper())

    # --- Phone script (T032) ---

    def _opening_script(self, itinerary: Itinerary) -> str:
        """Generate the opening phone script."""
        t = itinerary.ticket
        cabin = t.cabin.value.title()
        pax = t.passengers
        origin = t.origin
        plating = t.plating_carrier or "AA"
        num_continents = t.num_continents
        departure = t.departure.strftime("%d %B %Y") if t.departure else "TBD"
        num_segments = len(itinerary.flown_segments)
        num_surface = len(itinerary.surface_segments)
        # Same-city airport changes (NRT -> HND) are unlisted surface sectors
        # that still use a segment (Rule 3015 §4).
        num_airport_changes = sum(
            1
            for prev, nxt in zip(itinerary.segments, itinerary.segments[1:])
            if prev.to_airport != nxt.from_airport
            and self._is_same_city(prev.to_airport, nxt.from_airport)
        )
        surface_line = f"{num_segments} flown + {num_surface} surface"
        if num_airport_changes:
            surface_line += (
                f" + {num_airport_changes} airport-change surface"
                f" = {num_segments + num_surface + num_airport_changes} total"
            )

        lines = [
            "Hello, I'd like to book a oneworld Explorer Round-the-World ticket.",
            "",
            f"  Ticket type:  {t.type.value} ({num_continents} continents, {cabin})",
            f"  Passengers:   {pax}",
            f"  Origin:       {origin}",
            f"  Departure:    {departure}",
            f"  Plating:      {plating}",
            f"  Segments:     {surface_line}",
            "",
            "I'll give you the segments one at a time. Please book each segment",
            "before we move to the next one.",
        ]
        return "\n".join(lines)

    def _segment_scripts(self, itinerary: Itinerary) -> list[SegmentScript]:
        """Generate per-segment phone instructions and warnings."""
        cabin = itinerary.ticket.cabin
        segments = itinerary.segments
        scripts: list[SegmentScript] = []

        for i, seg in enumerate(segments):
            warnings: list[str] = []
            booking_class = self._get_booking_class(
                seg.carrier, cabin, seg.from_airport, seg.to_airport
            )
            fallback_class = self._get_fallback_class(
                seg.carrier, cabin, seg.from_airport, seg.to_airport
            )
            route = f"{seg.from_airport}-{seg.to_airport}"

            # --- Same-city transition warning ---
            # Check if this segment departs from a different airport in the
            # same city where the previous segment arrived
            if i > 0:
                prev = segments[i - 1]
                if prev.to_airport != seg.from_airport and self._is_same_city(
                    prev.to_airport, seg.from_airport
                ):
                    city = self._get_city_group_name(seg.from_airport)
                    warnings.append(
                        f"Same-city transition: {prev.to_airport} -> {seg.from_airport} "
                        f"({city}). Passenger must transfer between airports. "
                        f"This airport change is a surface sector and uses one of "
                        f"the 16 segments (Rule 3015 §4)."
                    )

            # --- Surface segment ---
            if seg.is_surface:
                instruction = (
                    f"Segment {i + 1}: SURFACE — {route}\n"
                    f"  This is ground transport, not a booked flight.\n"
                    f"  No booking needed for this segment."
                )
                if seg.notes:
                    instruction += f"\n  Note: {seg.notes}"

                scripts.append(
                    SegmentScript(
                        segment_index=i,
                        route=route,
                        carrier=None,
                        booking_class=None,
                        phone_instruction=instruction,
                        gds_command="",
                        warnings=warnings,
                    )
                )
                continue

            # --- FJ ATR-72 note ---
            fj_atr_note = ""
            if seg.carrier == "FJ" and booking_class == "D":
                # Check notes for ATR-72 indicator
                # Rule 3015 §5(b): no business cabin -> book the lower
                # (economy) cabin's code L, then B; never Y.
                if seg.notes and "ATR" in seg.notes.upper():
                    fj_atr_note = (
                        " (Note: ATR-72 is a single-class aircraft: book L; "
                        "if L is unavailable, book B; no refund for the "
                        "downgrade.)"
                    )

            # --- Married segment warning (short connection) ---
            # If this segment is a transit and connects to the next segment
            # on the same day, warn about married segment risk (airline may
            # link both flights so changing one cancels the other)
            if seg.type == SegmentType.TRANSIT and i + 1 < len(segments):
                nxt = segments[i + 1]
                if (
                    not nxt.is_surface
                    and seg.date is not None
                    and nxt.date is not None
                    and seg.date == nxt.date
                ):
                    warnings.append(
                        f"Married segment risk: {seg.from_airport}-{seg.to_airport} "
                        f"connects to {nxt.from_airport}-{nxt.to_airport} same day. "
                        f"If booked as married segment, changes to one flight may "
                        f"cancel both. Request separate PNRs if possible."
                    )

            # --- Mainline IB verification ---
            if seg.carrier == "IB":
                flight_num = seg.flight or ""
                # Iberia Express is I2, but flights may show as IB operationally
                # Flag MAD-CAI or any IB segment for verification
                if "MAD" in (seg.from_airport, seg.to_airport):
                    warnings.append(
                        f"Verify this is mainline Iberia (IB), not Iberia Express (I2). "
                        f"Flight {flight_num}: check operating carrier is IB."
                    )

            # --- Through-flight via-stop annotation ---
            via_info = ""
            if seg.has_via:
                via_str = ", ".join(seg.via_airports)
                via_info = f"\n  Through-flight via: {via_str} (book as single segment)"
                warnings.append(
                    f"Through-flight {route} via {via_str}: must be booked as a "
                    f"single segment. Splitting into separate segments requires "
                    f"reissue and may incur fees."
                )

            # --- Hub O&D control warnings ---
            # Carriers using O&D revenue management at their hub may block
            # standalone D-class on RTW fares. Present to agent as connected
            # routing through the hub rather than standalone segments.
            _OD_HUB_CARRIERS = {
                "CX": "HKG",
                "QR": "DOH",
            }
            if seg.carrier in _OD_HUB_CARRIERS:
                hub = _OD_HUB_CARRIERS[seg.carrier]
                from_apt = seg.from_airport
                to_apt = seg.to_airport
                if from_apt != hub and to_apt != hub:
                    # Segment doesn't touch hub — married through hub
                    warnings.append(
                        f"{seg.carrier} {from_apt}-{to_apt}: D-class may be married "
                        f"through {hub}. Check standalone availability via ExpertFlyer."
                    )
                elif to_apt == hub:
                    # Segment terminates at hub — O&D control risk
                    # Find the next flown segment to suggest connected routing
                    next_city = None
                    for j in range(i + 1, len(segments)):
                        if not segments[j].is_surface:
                            next_city = segments[j].to_airport
                            break
                    if next_city:
                        warnings.append(
                            f"O&D CONTROL: {seg.carrier} uses origin-destination revenue "
                            f"management at {hub}. D-class on {from_apt}-{hub} may be "
                            f"unbookable standalone on RTW fares. Present to agent as "
                            f"connected routing: \"{from_apt} to {next_city} via {hub}\" "
                            f"rather than standalone {from_apt}-{hub}."
                        )
                    else:
                        warnings.append(
                            f"O&D CONTROL: {seg.carrier} uses origin-destination revenue "
                            f"management at {hub}. D-class on {from_apt}-{hub} may be "
                            f"unbookable standalone on RTW fares. If possible, book with "
                            f"an onward connection from {hub}."
                        )

            # --- Build phone instruction ---
            date_str = seg.date.strftime("%d %b %Y") if seg.date else "date TBD"
            flight_info = f" flight {seg.flight}" if seg.flight else ""

            # Rule 3015 §5(b) NOTE: when the cabin's code is unavailable, book
            # the lower cabin's own code first, and only then the last-resort
            # class (B, or H on AA, for DONE*; Y for First). Display text only:
            # fallback_class stays the last-resort class the verify scanner uses.
            class_line = f"  Booking class: {booking_class}"
            if fallback_class:
                if cabin == CabinClass.FIRST:
                    class_line += (
                        f" (if {booking_class} unavailable: the lower-cabin code"
                        f" (D or I), then {fallback_class}; no refund for the"
                        f" downgrade; Rule 3015 §5(b))"
                    )
                else:
                    class_line += (
                        f" (if {booking_class} unavailable: L, economy cabin;"
                        f" then {fallback_class}; no refund for the downgrade; Rule 3015 §5(b))"
                    )

            instruction = (
                f"Segment {i + 1}: {seg.carrier}{flight_info} — {route} — {date_str}\n"
                f"{class_line}"
            )
            if via_info:
                instruction += via_info
            if fj_atr_note:
                instruction += fj_atr_note
            if seg.notes:
                instruction += f"\n  Note: {seg.notes}"

            scripts.append(
                SegmentScript(
                    segment_index=i,
                    route=route,
                    carrier=seg.carrier,
                    booking_class=booking_class,
                    fallback_class=fallback_class,
                    phone_instruction=instruction,
                    warnings=warnings,
                )
            )

        return scripts

    def _closing_checklist(self, itinerary: Itinerary) -> str:
        """Generate the closing checklist after all segments are booked."""
        t = itinerary.ticket
        plating = t.plating_carrier or "AA"
        pax = t.passengers

        lines = [
            "CLOSING CHECKLIST:",
            "",
            f"  1. Confirm all {len(itinerary.flown_segments)} flown segments are ticketed",
            f"  2. Verify plating carrier is {plating}",
            f"  3. Confirm {pax} passenger(s) on all segments",
            f"  4. Request fare quote — ticket type {t.type.value}",
            "  5. Verify total matches expected fare + YQ surcharges",
            "  6. Ask about change/cancellation flexibility",
            "  7. Ask the agent to insert OSI YY OW RTW in the PNR (Rule 3015 §5(a));"
            " without it the reservation may be auto-cancelled.",
        ]

        if t.departure:
            lines.append(
                f"  8. Confirm first segment date lock: {t.departure.strftime('%d %b %Y')}"
            )
            lines.append("     (First segment date is fixed; other dates can change)")

        lines.extend(
            [
                "",
                "  IMPORTANT: Get the PNR/booking reference and save it.",
                "  Ask the agent to email the full itinerary confirmation.",
            ]
        )

        return "\n".join(lines)

    # --- GDS commands (T033) ---

    def _format_gds_date(self, d) -> str:
        """Format a date as GDS date string: 15MAR."""
        if d is None:
            return "01JAN"
        return d.strftime("%d%b").upper()

    def _first_flown_line(self, itinerary: Itinerary) -> int:
        """1-based PNR line number of the first flown (non-surface) segment.

        The RTW global indicator attaches to the first flight sector
        (``/S{N}RW``); the Qantas oneworld clue card shows ``FXP/S2RW`` and
        notes verbatim that "'2' refers to the 1st flight sector in the
        itinerary". Amadeus numbers passenger-name elements before the
        itinerary, so one passenger puts the first segment on line 2 and two
        passengers on line 3. Surface sectors occupy a PNR line (ARNK) and
        also count. Infants without a seat travel on an adult's name line and
        do not get their own; ``ticket.passengers`` counts seated travellers.
        """
        pax = itinerary.ticket.passengers
        for i, seg in enumerate(itinerary.segments):
            if not seg.is_surface:
                return pax + i + 1
        return pax + 1

    def _gds_commands(self, itinerary: Itinerary) -> list[str]:
        """Amadeus cryptic entries that identify and price the itinerary as a
        oneworld Explorer round-the-world fare.

        Only the two first-party-verified RTW entries are emitted:

        - ``FQD{O}{O}/VRW/{date}`` — display the published RTW fare (origin
          back to origin; ``/VRW`` is the round-the-world global indicator).
        - ``FXP/S{N}RW/A-{fare_basis}`` — price the PNR as a round-the-world
          *specified* fare, attaching the RW global indicator to the first
          flown segment and forcing the OWE fare basis (DONE4, AONE3, ...).

        Both are quoted from carrier/alliance agent references
        (docs/kb-owe-rtw-gds-firstparty.md). Bare ``FXP`` is deliberately not
        used: the fare owner publishes "auto-pricing available: No", so
        auto-pricing never builds the RTW fare — the ``/S{N}RW`` +
        ``/A-{fare_basis}`` qualifiers are what make it an RTW ticket.

        Per-segment sells (SS), surface sectors (ARNK), the OSI advisory, and
        the validating-carrier element (FV / ``/R,VC-``) are intentionally
        omitted: they are standard Amadeus plumbing not covered by any
        first-party source and must be confirmed on a live Amadeus terminal
        before being emitted. The per-segment booking instructions are already
        provided in the phone script.
        """
        t = itinerary.ticket
        origin = t.origin
        departure_date = self._format_gds_date(t.departure)
        first_flown = self._first_flown_line(itinerary)

        return [
            f"FQD{origin}{origin}/V{_RTW_GLOBAL_INDICATOR}/{departure_date}",
            f"FXP/S{first_flown}{_RTW_GLOBAL_INDICATOR}/A-{t.fare_basis}",
        ]

    # --- Full generation (T034) ---

    def generate(self, itinerary: Itinerary) -> BookingScript:
        """Generate the complete booking script.

        Combines phone script (opening, per-segment instructions, closing)
        with Amadeus GDS commands and aggregated warnings.
        """
        opening = self._opening_script(itinerary)
        segment_scripts = self._segment_scripts(itinerary)
        closing = self._closing_checklist(itinerary)
        gds = self._gds_commands(itinerary)

        # Collect all warnings from segments plus global warnings
        all_warnings: list[str] = []
        for ss in segment_scripts:
            all_warnings.extend(ss.warnings)

        # Global warning: first segment date lock
        if itinerary.ticket.departure:
            all_warnings.append(
                f"First segment date ({itinerary.ticket.departure.strftime('%d %b %Y')}) "
                f"is locked after ticketing. Other dates remain flexible."
            )

        # RTW ticketing notes (first-party: docs/kb-owe-rtw-gds-firstparty.md)
        all_warnings.append(
            f"Endorsement required (Rule 3015 §18): {_RTW_ENDORSEMENT}."
        )
        first_flown = self._first_flown_line(itinerary)
        all_warnings.append(
            f"FXP/S{first_flown}RW: 'S{first_flown}' targets the first flown "
            f"segment's line in the built PNR (passenger-name lines and "
            f"surface/ARNK lines count). Verify against the live PNR before "
            f"pricing."
        )
        all_warnings.append(
            "GDS list shows only the first-party-verified RTW entries (FQD fare "
            "display + FXP RTW pricing). Segment sells (SS/ARNK) are given "
            "per-segment in the phone script above; the OSI YY OW RTW element "
            "(Rule 3015 §5(a)) is a closing-checklist item for the agent to "
            "insert. The validating-carrier element (FV) is omitted pending "
            "live-terminal confirmation (docs/kb-owe-rtw-gds-firstparty.md)."
        )

        return BookingScript(
            opening=opening,
            segments=segment_scripts,
            closing=closing,
            gds_commands=gds,
            warnings=all_warnings,
        )
