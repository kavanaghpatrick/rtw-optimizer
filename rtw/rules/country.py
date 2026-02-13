"""Country-of-origin rules. Rule 3015 §4(f), §6."""

from rtw.models import RuleResult, SegmentType, Severity
from rtw.rules.base import register_rule
from rtw.continents import get_country, get_country_name


def _is_international(from_country: str, to_country: str) -> bool:
    """Check if a movement is international (excluding US<->CA exemption)."""
    if from_country == to_country:
        return False
    # US<->CA exemption: movements between US and CA are NOT international
    if {from_country, to_country} == {"US", "CA"}:
        return False
    return True


@register_rule
class OriginCountryIntlLimitRule:
    """Origin country international departure/arrival limit. Rule 3015 §4(f)."""

    rule_id = "origin_country_intl_limit"
    rule_name = "Origin Country Intl Flights"
    rule_reference = "Rule 3015 SS4(f)"

    def check(self, itinerary, context) -> list[RuleResult]:
        origin_country = get_country(itinerary.ticket.origin)
        if not origin_country:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    severity=Severity.INFO,
                    message="Origin airport country unknown — skipping intl limit check.",
                )
            ]

        results = []
        origin_name = get_country_name(origin_country)

        # Count international departures and arrivals from origin country
        intl_departures = 0
        intl_arrivals = 0
        intl_dep_segments = []
        intl_arr_segments = []
        transit_departures = 0  # US exception: transit departures

        # Count international transfers from any single country
        country_transfers: dict[str, int] = {}

        for i, seg in enumerate(itinerary.segments):
            if seg.is_surface:
                continue

            from_country = get_country(seg.from_airport)
            to_country = get_country(seg.to_airport)

            if not from_country or not to_country:
                continue

            # Count intl departures from origin country
            if from_country == origin_country and _is_international(from_country, to_country):
                intl_departures += 1
                intl_dep_segments.append(i)
                if seg.type == SegmentType.TRANSIT:
                    transit_departures += 1

            # Count intl arrivals into origin country
            if to_country == origin_country and _is_international(from_country, to_country):
                intl_arrivals += 1
                intl_arr_segments.append(i)

            # Count transfers per country (for 4-transfer sub-rule)
            if _is_international(from_country, to_country):
                country_transfers[from_country] = country_transfers.get(from_country, 0) + 1

        # Departure limit check
        dep_limit = 1
        if origin_country == "US" and transit_departures >= 1:
            dep_limit = 2  # US exception: 2 departures if one is transit

        if intl_departures > dep_limit:
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=f"{intl_departures} international departures from {origin_name} — limit is {dep_limit}.",
                    fix_suggestion=f"Reduce international departures from {origin_name}. US-origin allows 2 if one is a transit.",
                    segments_involved=intl_dep_segments,
                )
            )

        # Arrival limit check (always 1)
        if intl_arrivals > 1:
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=f"{intl_arrivals} international arrivals into {origin_name} — limit is 1.",
                    fix_suggestion=f"Reduce international arrivals into {origin_name} to 1.",
                    segments_involved=intl_arr_segments,
                )
            )

        # 4-transfer sub-rule: max 4 intl transfers from any single country
        for country, count in country_transfers.items():
            if count > 4:
                c_name = get_country_name(country)
                results.append(
                    RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        rule_reference=self.rule_reference,
                        passed=False,
                        severity=Severity.VIOLATION,
                        message=f"{count} international transfers from {c_name} — limit is 4.",
                        fix_suggestion=f"Reduce international departures from {c_name}.",
                    )
                )

        if not results:
            dep_msg = f"{intl_departures}/{dep_limit} departures"
            arr_msg = f"{intl_arrivals}/1 arrivals"
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    severity=Severity.INFO,
                    message=f"{origin_name} international flights: {dep_msg}, {arr_msg}.",
                )
            )

        return results


@register_rule
class OriginCountryReturnRule:
    """No mid-journey return to origin country. Rule 3015 §6."""

    rule_id = "origin_country_return"
    rule_name = "Origin Country Return Ban"
    rule_reference = "Rule 3015 SS6"

    def check(self, itinerary, context) -> list[RuleResult]:
        origin_country = get_country(itinerary.ticket.origin)
        if not origin_country:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    severity=Severity.INFO,
                    message="Origin airport country unknown — skipping return ban check.",
                )
            ]

        origin_name = get_country_name(origin_country)
        segments = itinerary.segments

        if not segments:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message="No segments to check.",
                )
            ]

        # Identify "start of journey": walk forward from first segment
        # while segments stay within origin country (initial departure chain, exempt)
        initial_departure_end = 0
        for j in range(len(segments)):
            seg = segments[j]
            from_country = get_country(seg.from_airport)
            to_country = get_country(seg.to_airport)
            if from_country == origin_country and to_country == origin_country:
                initial_departure_end = j + 1
            else:
                break

        # Identify "end of journey": walk backwards from last segment
        # while segments touch origin country, mark as final return (exempt)
        final_return_start = len(segments)
        for j in range(len(segments) - 1, -1, -1):
            seg = segments[j]
            to_country = get_country(seg.to_airport)
            from_country = get_country(seg.from_airport)
            if to_country == origin_country or from_country == origin_country:
                final_return_start = j
            else:
                break

        # Check mid-journey segments for returns to origin country
        # (skip initial departure chain and final return)
        mid_journey_returns = []
        transit_returns = 0  # US exception: transit through origin country
        for i in range(initial_departure_end, final_return_start):
            seg = segments[i]
            if seg.is_surface:
                continue
            to_country = get_country(seg.to_airport)
            if to_country == origin_country:
                mid_journey_returns.append(i)
                if seg.type == SegmentType.TRANSIT:
                    transit_returns += 1

        if not mid_journey_returns:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message=f"No mid-journey return to {origin_name}.",
                )
            ]

        # US exception: 1 transit (not stopover) permitted
        if origin_country == "US" and len(mid_journey_returns) == 1 and transit_returns == 1:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    severity=Severity.INFO,
                    message=f"1 mid-journey transit through {origin_name} — US exception permits this.",
                )
            ]

        # For non-US, or US with multiple returns, or US with stopover
        if origin_country == "US" and transit_returns < len(mid_journey_returns):
            # Some are stopovers, not just transits
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=f"{len(mid_journey_returns)} mid-journey return(s) to {origin_name}. "
                    f"US allows 1 transit only (not stopovers).",
                    fix_suggestion=f"Remove mid-journey stopovers in {origin_name}. Only 1 transit permitted for US origin.",
                    segments_involved=mid_journey_returns,
                )
            ]

        if origin_country == "US" and len(mid_journey_returns) > 1:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=f"{len(mid_journey_returns)} mid-journey returns to {origin_name} — US allows at most 1 transit.",
                    fix_suggestion=f"Reduce mid-journey returns to {origin_name} to at most 1 transit.",
                    segments_involved=mid_journey_returns,
                )
            ]

        # Non-US: any mid-journey return is violation
        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=False,
                severity=Severity.VIOLATION,
                message=f"Mid-journey return to {origin_name} not permitted.",
                fix_suggestion=f"Remove segments returning to {origin_name} mid-journey. "
                f"Final return at end of journey is exempt.",
                segments_involved=mid_journey_returns,
            )
        ]
