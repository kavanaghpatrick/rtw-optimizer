"""Segment count, per-continent limit, and connectivity rules. Rule 3015 §4."""

from rtw.rules.base import register_rule
from rtw.models import RuleResult, Severity
from rtw.continents import get_segment_limit, are_same_city


@register_rule
class SegmentCountRule:
    """Total segments must be 3-16 (including surface sectors)."""

    rule_id = "segment_count"
    rule_name = "Segment Count"
    rule_reference = "Rule 3015 §4"

    def check(self, itinerary, context) -> list[RuleResult]:
        total = len(itinerary.segments)
        if total < 3:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=f"Only {total} segments — minimum is 3.",
                    fix_suggestion="Add more segments to reach at least 3.",
                )
            ]
        if total > 16:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=f"{total} segments exceeds maximum of 16 (including surface sectors).",
                    fix_suggestion="Remove segments or convert some to side trips.",
                )
            ]
        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=True,
                message=f"{total} segments (limit: 16).",
            )
        ]


@register_rule
class PerContinentLimitRule:
    """Per-continent intra-continental segment limits: 4 for most, 6 for North America.

    Only intra-continental segments (from_continent == to_continent) count.
    Intercontinental segments are validated by IntercontinentalLimitRule.
    """

    rule_id = "per_continent_limit"
    rule_name = "Per-Continent Segment Limit"
    rule_reference = "Rule 3015 §4"

    def check(self, itinerary, context) -> list[RuleResult]:
        results = []
        for continent, count in context.segments_per_continent.items():
            limit = get_segment_limit(continent)
            if count > limit:
                results.append(
                    RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        rule_reference=self.rule_reference,
                        passed=False,
                        severity=Severity.VIOLATION,
                        message=f"{continent.value}: {count} segments exceeds limit of {limit}.",
                        fix_suggestion=f"Reduce segments in {continent.value} to {limit} or fewer.",
                    )
                )
            else:
                results.append(
                    RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        rule_reference=self.rule_reference,
                        passed=True,
                        message=f"{continent.value}: {count}/{limit} segments.",
                    )
                )
        return results


@register_rule
class SegmentConnectivityRule:
    """Check that consecutive segments form a connected chain."""

    rule_id = "segment_connectivity"
    rule_name = "Segment Connectivity"
    rule_reference = "Rule 3015 §4"

    def check(self, itinerary, context) -> list[RuleResult]:
        if len(itinerary.segments) < 2:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message="Too few segments to check connectivity.",
                )
            ]

        gaps = []
        for i in range(len(itinerary.segments) - 1):
            arr = itinerary.segments[i].to_airport
            dep = itinerary.segments[i + 1].from_airport
            if arr != dep and not are_same_city(arr, dep):
                # Gap between segments — only flag if next segment is not a surface sector
                if not itinerary.segments[i + 1].is_surface:
                    gaps.append((i, i + 1, arr, dep))

        if gaps:
            results = []
            for seg_a, seg_b, arr, dep in gaps:
                results.append(
                    RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        rule_reference=self.rule_reference,
                        passed=False,
                        severity=Severity.WARNING,
                        message=(
                            f"Segment {seg_b + 1} departs {dep} but segment {seg_a + 1} "
                            f"arrives {arr} — no connecting surface sector."
                        ),
                        fix_suggestion=f"Add a surface sector between {arr} and {dep}, or correct the airport code.",
                        segments_involved=[seg_a, seg_b],
                    )
                )
            return results

        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=True,
                message="All segments connected.",
            )
        ]
