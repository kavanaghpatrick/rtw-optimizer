"""Stopover rules. Rule 3015 §6."""

from rtw.rules.base import register_rule
from rtw.models import RuleResult, Severity, Continent
from rtw.continents import get_country, get_country_name, get_continent, get_same_city_group


@register_rule
class MinimumStopoverRule:
    """Minimum 2 stopovers required."""

    rule_id = "minimum_stopovers"
    rule_name = "Minimum Stopovers"
    rule_reference = "Rule 3015 §6"

    def check(self, itinerary, context) -> list[RuleResult]:
        stopovers = [s for s in itinerary.segments if s.is_stopover]
        count = len(stopovers)
        if count < 2:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=f"Only {count} stopovers — minimum is 2.",
                    fix_suggestion="Change at least 2 transit connections to stopovers (>24h).",
                )
            ]
        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=True,
                message=f"{count} stopovers (minimum: 2).",
            )
        ]


@register_rule
class OriginContinentStopoverRule:
    """Maximum 2 stopovers in continent of origin."""

    rule_id = "origin_continent_stopovers"
    rule_name = "Origin Continent Stopover Limit"
    rule_reference = "Rule 3015 §6"

    def check(self, itinerary, context) -> list[RuleResult]:
        origin_cont = context.origin_continent
        if not origin_cont:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    severity=Severity.INFO,
                    message="Cannot determine origin continent.",
                )
            ]

        count = context.stopovers_per_continent.get(origin_cont, 0)

        if count > 2:
            # Check if this is the MAD-type ambiguity (return leg stopovers)
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.WARNING,
                    message=f"{count} stopovers in origin continent {origin_cont.value} (limit: 2). "
                    f"Verify with AA RTW desk whether return-leg stopovers count.",
                    fix_suggestion="Make intermediate return stops into transits (<24h) or confirm exemption with booking desk.",
                )
            ]

        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=True,
                message=f"{count}/2 stopovers in origin continent {origin_cont.value}.",
            )
        ]


@register_rule
class OriginCountryStopoverPerDirectionRule:
    """Maximum 1 stopover per direction in the country of origin."""

    rule_id = "origin_country_stopover_direction"
    rule_name = "Origin Country Stopover Per Direction"
    rule_reference = "Rule 3015 §6"

    def check(self, itinerary, context) -> list[RuleResult]:
        origin = itinerary.ticket.origin
        origin_country = get_country(origin)
        if not origin_country:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    severity=Severity.INFO,
                    message="Cannot determine origin country.",
                )
            ]

        # Split itinerary into outbound and return legs.
        # Outbound = initial chain of segments while still in or departing origin country.
        # Return = final chain of segments arriving back in origin country.
        # Everything in between is mid-journey (covered by origin_country_return rule).
        segs = itinerary.segments

        # Find outbound stopovers: segments at start that are in origin country
        outbound_stopovers = []
        for i, seg in enumerate(segs):
            seg_country = get_country(seg.to_airport)
            if seg.is_stopover and seg_country == origin_country:
                outbound_stopovers.append(i)
            elif seg_country != origin_country:
                break  # Left origin country

        # Find return stopovers: walk backwards from end
        return_stopovers = []
        for i in range(len(segs) - 1, -1, -1):
            seg = segs[i]
            seg_country = get_country(seg.to_airport)
            if seg_country == origin_country:
                if seg.is_stopover:
                    return_stopovers.append(i)
            else:
                break  # Haven't arrived back yet

        results = []
        country_name = get_country_name(origin_country)

        if len(outbound_stopovers) > 1:
            seg_nums = ", ".join(str(idx + 1) for idx in outbound_stopovers)
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=(
                        f"{len(outbound_stopovers)} stopovers in {country_name} on outbound "
                        f"(segments {seg_nums}) — limit is 1 per direction."
                    ),
                    fix_suggestion=f"Convert excess outbound stopovers in {country_name} to transits (<24h).",
                    segments_involved=outbound_stopovers,
                )
            )

        if len(return_stopovers) > 1:
            seg_nums = ", ".join(str(idx + 1) for idx in return_stopovers)
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=(
                        f"{len(return_stopovers)} stopovers in {country_name} on return "
                        f"(segments {seg_nums}) — limit is 1 per direction."
                    ),
                    fix_suggestion=f"Convert excess return stopovers in {country_name} to transits (<24h).",
                    segments_involved=return_stopovers,
                )
            )

        if not results:
            out_count = len(outbound_stopovers)
            ret_count = len(return_stopovers)
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message=f"Origin country stopovers: {out_count} outbound, {ret_count} return (limit: 1/direction).",
                )
            )

        return results


@register_rule
class SameCityVisitLimitRule:
    """Same city can be visited at most 4 times (5 in North America)."""

    rule_id = "same_city_visit_limit"
    rule_name = "Same-City Visit Limit"
    rule_reference = "Rule 3015 §6"

    def check(self, itinerary, context) -> list[RuleResult]:
        # Count arrivals per city group
        city_visits: dict[str, list[int]] = {}
        for i, seg in enumerate(itinerary.segments):
            city = get_same_city_group(seg.to_airport) or seg.to_airport
            if city not in city_visits:
                city_visits[city] = []
            city_visits[city].append(i)

        results = []
        for city, indices in city_visits.items():
            count = len(indices)
            # Determine limit based on continent
            sample_airport = itinerary.segments[indices[0]].to_airport
            continent = get_continent(sample_airport)
            limit = 5 if continent == Continent.N_AMERICA else 4

            if count > limit:
                seg_nums = ", ".join(str(idx + 1) for idx in indices)
                results.append(
                    RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        rule_reference=self.rule_reference,
                        passed=False,
                        severity=Severity.VIOLATION,
                        message=(
                            f"{count} visits to {city} (segments {seg_nums}) — "
                            f"limit is {limit} per city."
                        ),
                        fix_suggestion=f"Reduce visits to {city} to {limit} or fewer.",
                        segments_involved=indices,
                    )
                )

        if not results:
            if city_visits:
                max_city = max(city_visits, key=lambda c: len(city_visits[c]))
                max_count = len(city_visits[max_city])
                results.append(
                    RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        rule_reference=self.rule_reference,
                        passed=True,
                        message=f"Same-city visits: OK (max {max_count} at {max_city}).",
                    )
                )
            else:
                results.append(
                    RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        rule_reference=self.rule_reference,
                        passed=True,
                        message="No segments to check.",
                    )
                )

        return results
