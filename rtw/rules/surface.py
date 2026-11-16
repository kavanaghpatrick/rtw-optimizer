"""Surface sector rules. Rule 3015 §7."""

from rtw.rules.base import register_rule
from rtw.models import RuleResult, Severity, Continent, TariffConference, CONTINENT_TO_TC
from rtw.continents import get_continent


@register_rule
class FirstSegmentNotSurfaceRule:
    """First segment of the itinerary must be a flown segment, not surface."""

    rule_id = "first_segment_not_surface"
    rule_name = "First Segment Not Surface"
    rule_reference = "Rule 3015 §7"

    def check(self, itinerary, context) -> list[RuleResult]:
        if not itinerary.segments:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message="No segments to check.",
                )
            ]

        first = itinerary.segments[0]
        if first.is_surface:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=(
                        f"First segment {first.from_airport}->{first.to_airport} "
                        f"is a surface sector. The first segment must be a flown segment."
                    ),
                    fix_suggestion=(
                        "Replace the opening surface sector with a flown segment "
                        "on a oneworld carrier. The ticket origin is defined by "
                        "the departure point of the first flight."
                    ),
                    segments_involved=[0],
                )
            ]

        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=True,
                message="First segment is a flown segment.",
            )
        ]


@register_rule
class SameCityResolutionRule:
    """Same-city airport changes (NRT->HND, TSA->TPE) are implicit surface sectors.

    Rule 3015 §4: landing at one airport and departing from a different airport
    by ground transport is a surface segment, and surface segments count toward
    the 16-segment limit and per-continent limits. §7 "Avoiding Wasted
    Segments": such surface segments waste a segment.
    """

    rule_id = "same_city_resolution"
    rule_name = "Same-City Resolution"
    rule_reference = "Rule 3015 §4/§7"

    def check(self, itinerary, context) -> list[RuleResult]:
        results = []
        for seg_idx, next_idx in context.same_city_pairs:
            arr = itinerary.segments[seg_idx].to_airport
            dep = itinerary.segments[next_idx].from_airport
            cont = get_continent(arr)
            cont_name = cont.value if cont else "that continent"
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.WARNING,
                    message=(
                        f"Same-city airport change {arr}->{dep} is a surface sector: "
                        f"it uses one of the 16 segments and counts toward the "
                        f"{cont_name} segment limit."
                    ),
                    fix_suggestion=(
                        f"Fly into and out of the same airport ({arr} or {dep}) "
                        f"to save a segment."
                    ),
                    segments_involved=[seg_idx, next_idx],
                )
            )
        if not results:
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message="No same-city airport changes detected.",
                )
            )
        return results


@register_rule
class TransoceanicSurfaceRule:
    """Transoceanic surface sectors are not permitted (with SWP exception)."""

    rule_id = "transoceanic_surface"
    rule_name = "Transoceanic Surface Sectors"
    rule_reference = "Rule 3015 SS7"

    def check(self, itinerary, context) -> list[RuleResult]:
        transoceanic_indices: list[int] = []
        last_from = ""
        last_to = ""

        for i, seg in enumerate(itinerary.segments):
            if not seg.is_surface:
                continue

            from_continent = get_continent(seg.from_airport)
            to_continent = get_continent(seg.to_airport)

            if from_continent is None or to_continent is None:
                continue

            from_tc = CONTINENT_TO_TC[from_continent]
            to_tc = CONTINENT_TO_TC[to_continent]

            if from_tc == to_tc:
                continue

            # TC2<->TC3 is NOT restricted
            if {from_tc, to_tc} == {TariffConference.TC2, TariffConference.TC3}:
                continue

            # TC1<->TC2 or TC1<->TC3 = transoceanic
            transoceanic_indices.append(i)
            last_from = seg.from_airport
            last_to = seg.to_airport

        count = len(transoceanic_indices)

        if count == 0:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message="No transoceanic surface sectors.",
                )
            ]

        if context.origin_continent == Continent.SWP:
            if count == 1:
                return [
                    RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        rule_reference=self.rule_reference,
                        passed=True,
                        severity=Severity.WARNING,
                        message=(
                            f"1 transoceanic surface sector "
                            f"({last_from}->{last_to}) — SWP-origin allowance."
                        ),
                        fix_suggestion="SWP-origin permits 1 transoceanic surface sector.",
                        segments_involved=transoceanic_indices,
                    )
                ]
            else:
                return [
                    RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        rule_reference=self.rule_reference,
                        passed=False,
                        severity=Severity.VIOLATION,
                        message=(
                            f"{count} transoceanic surface sectors "
                            f"— SWP-origin allows at most 1."
                        ),
                        segments_involved=transoceanic_indices,
                    )
                ]

        # Non-SWP origin
        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=False,
                severity=Severity.VIOLATION,
                message=(
                    f"{count} transoceanic surface sector(s) "
                    f"({last_from}->{last_to}) — not permitted."
                ),
                fix_suggestion="Replace transoceanic surface sectors with flown segments.",
                segments_involved=transoceanic_indices,
            )
        ]
