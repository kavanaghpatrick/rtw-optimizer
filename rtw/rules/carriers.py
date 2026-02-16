"""Carrier eligibility rules. Rule 3015 §15, §19."""

from pathlib import Path
import yaml

from rtw.rules.base import register_rule
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
    """All carriers must be oneworld members."""

    rule_id = "eligible_carriers"
    rule_name = "Eligible Carriers"
    rule_reference = "Rule 3015 §15"

    def check(self, itinerary, context) -> list[RuleResult]:
        results = []
        invalid = []
        for i, seg in enumerate(itinerary.segments):
            if seg.is_surface or not seg.carrier:
                continue
            if seg.carrier not in _ELIGIBLE_CODES:
                # Check for codeshare parent
                parent = _CODESHARE_PARENTS.get(seg.carrier)
                if parent and parent in _ELIGIBLE_CODES:
                    carrier_info = _CARRIERS.get(seg.carrier, {})
                    carrier_name = carrier_info.get("name", seg.carrier)
                    parent_info = _CARRIERS.get(parent, {})
                    parent_name = parent_info.get("name", parent)
                    results.append(
                        RuleResult(
                            rule_id=self.rule_id,
                            rule_name=self.rule_name,
                            rule_reference=self.rule_reference,
                            passed=True,
                            severity=Severity.INFO,
                            message=f"Segment {i + 1}: {seg.carrier} ({carrier_name}) recognized as {parent} ({parent_name}) codeshare.",
                            fix_suggestion=f"For accuracy, use carrier: {parent} with operating_carrier: {seg.carrier}.",
                            segments_involved=[i],
                        )
                    )
                else:
                    invalid.append((i, seg.carrier))

        if invalid:
            for idx, carrier in invalid:
                carrier_info = _CARRIERS.get(carrier, {})
                note = carrier_info.get("notes", "")
                results.append(
                    RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        rule_reference=self.rule_reference,
                        passed=False,
                        severity=Severity.VIOLATION,
                        message=f"Segment {idx + 1}: {carrier} is not an eligible oneworld carrier. {note}",
                        fix_suggestion=f"Replace {carrier} with a oneworld member airline.",
                        segments_involved=[idx],
                    )
                )

        if not results:
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message="All carriers are eligible oneworld members.",
                )
            )
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
