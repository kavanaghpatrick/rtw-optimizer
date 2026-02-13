"""Surface sector rules. Rule 3015 §7."""

from rtw.rules.base import register_rule
from rtw.models import RuleResult, Severity, Continent, TariffConference, CONTINENT_TO_TC
from rtw.continents import get_continent


@register_rule
class SameCityResolutionRule:
    """Same-city airport pairs (NRT/HND, TSA/TPE) are NOT surface sectors."""

    rule_id = "same_city_resolution"
    rule_name = "Same-City Resolution"
    rule_reference = "Rule 3015 §7"

    def check(self, itinerary, context) -> list[RuleResult]:
        results = []
        for i, (seg_idx, next_idx) in enumerate(context.same_city_pairs):
            arr = itinerary.segments[seg_idx].to_airport
            dep = itinerary.segments[next_idx].from_airport
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    severity=Severity.INFO,
                    message=f"Same-city pair: {arr}/{dep} (not a surface sector).",
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
                    message="No same-city pairs detected.",
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
