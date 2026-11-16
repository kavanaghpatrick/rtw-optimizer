"""Carrier eligibility rules. Rule 3015 §4(j), §19."""

from pathlib import Path
import yaml

from rtw.rules.base import register_rule
from rtw.carriers import codeshare_permitted
from rtw.continents import get_country
from rtw.models import RuleResult, Severity

_DATA_DIR = Path(__file__).parent.parent / "data"
with open(_DATA_DIR / "carriers.yaml") as f:
    _CARRIERS = yaml.safe_load(f)

_ELIGIBLE_CODES = {code for code, info in _CARRIERS.items() if info.get("eligible", False)}

_CODESHARE_PARENTS = {
    code: info["codeshare_parent"]
    for code, info in _CARRIERS.items()
    if info.get("codeshare_parent")
}


@register_rule
class QRNotFirstRule:
    """Qatar Airways cannot be the first carrier."""

    rule_id = "qr_not_first"
    rule_name = "QR Not First Carrier"
    rule_reference = "oneworld booking tool"

    def check(self, itinerary, context) -> list[RuleResult]:
        # Find first flown segment
        for seg in itinerary.segments:
            if seg.is_flown and seg.carrier:
                if seg.carrier == "QR":
                    return [
                        RuleResult(
                            rule_id=self.rule_id,
                            rule_name=self.rule_name,
                            rule_reference=self.rule_reference,
                            passed=False,
                            severity=Severity.WARNING,
                            message="Qatar Airways (QR) is the first carrier. "
                            "The online booking tool cannot issue tickets starting with QR; "
                            "book via AA RTW desk (+1 800 843 3000) or a travel agent.",
                            fix_suggestion="Start with a different carrier, or book by phone through the AA RTW desk.",
                        )
                    ]
                else:
                    return [
                        RuleResult(
                            rule_id=self.rule_id,
                            rule_name=self.rule_name,
                            rule_reference=self.rule_reference,
                            passed=True,
                            message=f"First carrier is {seg.carrier} (not QR).",
                        )
                    ]
        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=True,
                message="No flown segments found.",
            )
        ]


@register_rule
class EligibleCarrierRule:
    """Every flown segment must be marketed and operated per Rule 3015 §4(j)."""

    rule_id = "eligible_carriers"
    rule_name = "Eligible Carriers"
    rule_reference = "Rule 3015 §4(j)"

    def _result(self, passed, severity, message, fix="", idx=None):
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            rule_reference=self.rule_reference,
            passed=passed,
            severity=severity,
            message=message,
            fix_suggestion=fix,
            segments_involved=[idx] if idx is not None else [],
        )

    def check(self, itinerary, context) -> list[RuleResult]:
        results = []
        for i, seg in enumerate(itinerary.segments):
            if seg.is_surface or not seg.carrier:
                continue
            carrier = seg.carrier
            info = _CARRIERS.get(carrier, {}) or {}
            name = info.get("name", carrier)

            # A codeshare-only code (JQ): its own flight numbers are not allowed.
            parent = _CODESHARE_PARENTS.get(carrier)
            if parent:
                results.append(self._result(
                    False, Severity.VIOLATION,
                    f"Segment {i + 1}: {carrier} ({name}) flight numbers are not "
                    f"permitted. Rule 3015 §4(j) only allows {parent}-marketed "
                    f"flights operated by {carrier}.",
                    f"Book the {parent} flight number: carrier: {parent} with "
                    f"operating_carrier: {carrier}.",
                    i,
                ))
                continue

            if carrier not in _ELIGIBLE_CODES:
                note = info.get("notes", "")
                results.append(self._result(
                    False, Severity.VIOLATION,
                    f"Segment {i + 1}: {carrier} is not an eligible oneworld carrier. {note}".rstrip(),
                    f"Replace {carrier} with a oneworld member airline.",
                    i,
                ))
                continue

            successor = info.get("successor")
            if info.get("retired_code") and successor:
                results.append(self._result(
                    True, Severity.INFO,
                    f"Segment {i + 1}: the {carrier} ({name}) code is retired; "
                    f"these flights are now sold as {successor}.",
                    f"Use carrier: {successor}.",
                    i,
                ))

            operating = seg.operating_carrier
            if operating and operating != carrier:
                ok, reason = codeshare_permitted(carrier, operating)
                if not ok:
                    results.append(self._result(
                        False, Severity.VIOLATION,
                        f"Segment {i + 1}: {reason} (Rule 3015 §4(j)).",
                        f"Book a flight operated by a oneworld Explorer carrier "
                        f"instead of {operating}.",
                        i,
                    ))

        if not results:
            results.append(self._result(
                True, Severity.VIOLATION, "All carriers are eligible oneworld members."
            ))
        return results


@register_rule
class QFJQCodeshareRule:
    """QF/Jetstar codeshare plating carrier restrictions."""

    rule_id = "qf_jq_codeshare"
    rule_name = "QF/Jetstar Codeshare"
    rule_reference = "Rule 3015 SS15"

    def check(self, itinerary, context) -> list[RuleResult]:
        # Find all JQ segments (operating_carrier or carrier)
        jq_segments = []
        for i, seg in enumerate(itinerary.segments):
            if seg.is_surface:
                continue
            if seg.carrier == "JQ" or (hasattr(seg, 'operating_carrier') and seg.operating_carrier == "JQ"):
                jq_segments.append(i)

        if not jq_segments:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message="No codeshare restrictions applicable.",
                )
            ]

        # Check plating carrier
        plating = itinerary.ticket.plating_carrier
        restricted_plating = {"AS", "IB"}
        if plating and plating in restricted_plating:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.WARNING,
                    message=f"JQ (Jetstar) segments present but plating carrier is {plating}. "
                    f"{plating} stock does not permit JQ-operated flights.",
                    fix_suggestion="Use QF, BA, or another plating carrier for itineraries with Jetstar flights.",
                    segments_involved=jq_segments,
                )
            ]

        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=True,
                message=f"JQ segments found ({len(jq_segments)}). Plating carrier {'is ' + plating if plating else 'not specified'} — OK.",
            )
        ]


def _is_qf_operated(seg) -> bool:
    return (seg.operating_carrier or seg.carrier) == "QF"


def _is_qf_own_flight(seg) -> bool:
    """QF-marketed and QF-operated."""
    return seg.carrier == "QF" and _is_qf_operated(seg)


@register_rule
class QFWithinUSARule:
    """QF-operated flights within the USA only as part of a QF journey via LAX."""

    rule_id = "qf_within_usa"
    rule_name = "QF Within USA"
    rule_reference = "Rule 3015 carrier restrictions (QF within USA)"

    def check(self, itinerary, context) -> list[RuleResult]:
        segs = itinerary.segments
        results = []
        for i, seg in enumerate(segs):
            if seg.is_surface or not seg.carrier or not _is_qf_operated(seg):
                continue
            if get_country(seg.from_airport) != "US" or get_country(seg.to_airport) != "US":
                continue

            prev_seg = segs[i - 1] if i > 0 else None
            next_seg = segs[i + 1] if i + 1 < len(segs) else None
            via_lax = (
                seg.to_airport == "LAX"
                and next_seg is not None
                and not next_seg.is_surface
                and next_seg.from_airport == "LAX"
                and _is_qf_own_flight(next_seg)
            ) or (
                seg.from_airport == "LAX"
                and prev_seg is not None
                and not prev_seg.is_surface
                and prev_seg.to_airport == "LAX"
                and _is_qf_own_flight(prev_seg)
            )
            route = f"{seg.from_airport}-{seg.to_airport}"
            if via_lax:
                results.append(RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.WARNING,
                    message=f"Segment {i + 1}: QF-operated {route} is within the USA. "
                    "Qantas flights within the USA are restricted on oneworld Explorer; "
                    "this one connects with a Qantas flight at LAX, which is the "
                    "permitted pattern, but confirm with the ticketing agent.",
                    fix_suggestion="Confirm the QF domestic US sector prices on the RTW fare.",
                    segments_involved=[i],
                ))
            else:
                results.append(RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=f"Segment {i + 1}: QF-operated {route} is within the USA "
                    "with no connecting or stopover Qantas (QF-marketed, QF-operated) "
                    "flight at LAX. Qantas flights within the USA are not permitted "
                    "on their own.",
                    fix_suggestion="Fly this US sector on AA or AS, or connect it to a "
                    "Qantas flight at LAX.",
                    segments_involved=[i],
                ))

        if not results:
            results.append(RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=True,
                message="No Qantas-operated flights within the USA.",
            ))
        return results
