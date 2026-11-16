"""Unknown-continent guard. Rule 3015 §3 (continent definitions).

Every other rule depends on each airport resolving to one of the six oneworld
continents. If an airport cannot be placed, continent counts, intercontinental
limits and ocean-crossing checks are computed on partial data, so the result
must not be reported as a clean pass.
"""

from rtw.rules.base import register_rule
from rtw.models import RuleResult, Severity


@register_rule
class UnknownContinentRule:
    """Every ticketed point must resolve to a oneworld continent."""

    rule_id = "unknown_continent"
    rule_name = "Continent Coverage"
    rule_reference = "Rule 3015 §3"

    def check(self, itinerary, context) -> list[RuleResult]:
        unknown: dict[str, list[int]] = getattr(context, "unknown_continent_airports", {}) or {}
        if not unknown:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message="Every airport resolves to a oneworld continent.",
                )
            ]

        results = []
        for airport, seg_indices in unknown.items():
            where = ", ".join(
                "ticket origin" if i < 0 else f"segment {i + 1}" for i in seg_indices
            )
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=(
                        f"Unknown continent for {airport} ({where}); continent "
                        "counts and direction checks for this itinerary are unreliable."
                    ),
                    fix_suggestion=(
                        "Check the airport code. If it is correct, add its country "
                        "(or an airport override) to rtw/data/continents.yaml using "
                        "01-fare-rules.md §3."
                    ),
                    segments_involved=[i for i in seg_indices if i >= 0],
                )
            )
        return results
