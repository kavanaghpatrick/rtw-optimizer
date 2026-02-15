"""Ticket validity rules. Rule 3015 §12, §16."""

from rtw.rules.base import register_rule
from rtw.models import RuleResult, Severity
from rtw.continents import are_same_city, check_open_jaw_permitted


@register_rule
class ReturnToOriginRule:
    """Ticket must return to origin city (or same-city group)."""

    rule_id = "return_to_origin"
    rule_name = "Return to Origin"
    rule_reference = "Rule 3015 §18"

    def check(self, itinerary, context) -> list[RuleResult]:
        origin = itinerary.ticket.origin
        if not itinerary.segments:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message="No segments found.",
                )
            ]
        last_dest = itinerary.segments[-1].to_airport
        if are_same_city(origin, last_dest):
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message=f"Returns to origin: {last_dest} (same city as {origin}).",
                )
            ]
        # Check if this is a permitted open jaw
        result = check_open_jaw_permitted(origin, last_dest)
        if result.permitted:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message=f"Open jaw {origin}→{last_dest}: permitted ({result.reason}).",
                )
            ]
        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=False,
                severity=Severity.VIOLATION,
                message=f"Last destination {last_dest} does not match origin {origin}.",
                fix_suggestion=f"Add a final segment returning to {origin}. Permitted open-jaw pairs: same country, US↔CA, HK↔CN, MY↔SG, MV↔LK/IN, within Middle East, within Africa.",
            )
        ]


@register_rule
class OpenJawPairsRule:
    """Open-jaw pairs must be permitted per Rule 3015 §18."""

    rule_id = "open_jaw_pairs"
    rule_name = "Open-Jaw Permitted Pairs"
    rule_reference = "Rule 3015 SS18"

    def check(self, itinerary, context) -> list[RuleResult]:
        origin = itinerary.ticket.origin
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
        last_dest = itinerary.segments[-1].to_airport

        # If returns to origin (same city), not an open jaw
        if are_same_city(origin, last_dest):
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message="Returns to origin — not an open jaw.",
                )
            ]

        # Check if open jaw is permitted
        result = check_open_jaw_permitted(origin, last_dest)
        if result.permitted:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message=f"Open jaw {origin}→{last_dest}: permitted ({result.reason}).",
                )
            ]

        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=False,
                severity=Severity.VIOLATION,
                message=f"Open jaw {origin}→{last_dest}: not permitted. {result.reason}.",
                fix_suggestion="Permitted open-jaw pairs: same country, US↔CA, HK↔CN, MY↔SG, MV↔LK/IN, within Middle East, within Africa.",
            )
        ]


@register_rule
class ContinentCountRule:
    """Number of continents visited must match ticket type."""

    rule_id = "continent_count"
    rule_name = "Continent Count"
    rule_reference = "Rule 3015 §16"

    def check(self, itinerary, context) -> list[RuleResult]:
        expected = itinerary.ticket.num_continents
        actual = len(context.continents_visited)

        if actual != expected:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.WARNING,
                    message=f"Visiting {actual} continents but ticket is for {expected}. "
                    f"Continents: {', '.join(c.value for c in context.continents_visited)}.",
                    fix_suggestion=f"Adjust ticket type to {'DONE' if itinerary.ticket.fare_prefix == 'D' else 'LONE'}{actual} "
                    f"or modify routing to visit exactly {expected} continents.",
                )
            ]

        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=True,
                message=f"{actual} continents: {', '.join(c.value for c in context.continents_visited)}.",
            )
        ]


@register_rule
class TicketValidityRule:
    """Ticket valid for 10-365 days."""

    rule_id = "ticket_validity"
    rule_name = "Ticket Validity Period"
    rule_reference = "Rule 3015 §12"

    def check(self, itinerary, context) -> list[RuleResult]:
        # Get first and last dates
        dates = [s.date for s in itinerary.segments if s.date is not None]
        if len(dates) < 2:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    severity=Severity.INFO,
                    message="Insufficient dates to check validity period.",
                )
            ]

        first_date = min(dates)
        last_date = max(dates)
        days = (last_date - first_date).days

        results = []
        if days < 10:
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=f"Trip duration {days} days — minimum is 10 days.",
                    fix_suggestion="Extend itinerary to at least 10 days.",
                )
            )
        elif days > 365:
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=f"Trip duration {days} days — maximum is 365 days (1 year).",
                    fix_suggestion="Shorten itinerary to fit within 12 months.",
                )
            )
        else:
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message=f"Trip duration: {days} days (valid: 10-365).",
                )
            )

        return results


@register_rule
class OriginMatchesFirstSegmentRule:
    """Ticket origin must match first segment departure airport."""

    rule_id = "origin_matches_first_segment"
    rule_name = "Origin Matches First Segment"
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

        origin = itinerary.ticket.origin
        first_dep = itinerary.segments[0].from_airport
        if are_same_city(origin, first_dep):
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message=f"Origin {origin} matches first segment departure {first_dep}.",
                )
            ]

        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=False,
                severity=Severity.WARNING,
                message=(
                    f"Ticket origin {origin} does not match first segment departure "
                    f"{first_dep}. Origin-based rules may produce incorrect results."
                ),
                fix_suggestion=f"Change ticket origin to {first_dep} or update the first segment to depart from {origin}.",
                segments_involved=[0],
            )
        ]


@register_rule
class DateSequenceRule:
    """Segment dates must be in chronological order."""

    rule_id = "date_sequence"
    rule_name = "Date Sequence"
    rule_reference = "Rule 3015 §4"

    def check(self, itinerary, context) -> list[RuleResult]:
        dated_segments = [
            (i, s) for i, s in enumerate(itinerary.segments) if s.date is not None
        ]

        if len(dated_segments) < 2:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    severity=Severity.INFO,
                    message="Insufficient dates to check sequence.",
                )
            ]

        violations = []
        for j in range(len(dated_segments) - 1):
            idx_a, seg_a = dated_segments[j]
            idx_b, seg_b = dated_segments[j + 1]
            if seg_b.date < seg_a.date:
                violations.append(
                    (idx_a, idx_b, seg_a.date, seg_b.date)
                )

        if violations:
            results = []
            for idx_a, idx_b, date_a, date_b in violations:
                results.append(
                    RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        rule_reference=self.rule_reference,
                        passed=False,
                        severity=Severity.VIOLATION,
                        message=(
                            f"Segment {idx_b + 1} date {date_b} is before "
                            f"segment {idx_a + 1} date {date_a}."
                        ),
                        fix_suggestion="Correct the segment dates to be in chronological order.",
                        segments_involved=[idx_a, idx_b],
                    )
                )
            return results

        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=True,
                message="All segment dates in chronological order.",
            )
        ]
