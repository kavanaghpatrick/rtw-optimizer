"""Geography-specific rules: Hawaii, Alaska, Australia, Transcontinental. Rule 3015 §9-10."""

from rtw.continents import get_country
from rtw.rules.base import register_rule
from rtw.models import RuleResult, Severity

# Hawaii airports
_HAWAII_AIRPORTS = {"HNL", "OGG", "KOA", "LIH", "ITO"}
# Alaska airports
_ALASKA_AIRPORTS = {"ANC", "FAI", "JNU", "SIT", "KTN"}
# US mainland (approximate — for transcontinental check)
_US_EAST = {
    "JFK",
    "LGA",
    "EWR",
    "BOS",
    "PHL",
    "DCA",
    "IAD",
    "BWI",
    "ATL",
    "MIA",
    "MCO",
    "FLL",
    "TPA",
    "CLT",
    "RDU",
    "PIT",
    "DTW",
    "CLE",
    "CVG",
    "IND",
    "MSP",
    "STL",
    "MCI",
    "MSY",
    "BNA",
    "MEM",
    "ORD",
    "MDW",
}
_US_WEST = {
    "LAX",
    "SFO",
    "SEA",
    "PDX",
    "SAN",
    "SJC",
    "OAK",
    "SMF",
    "LAS",
    "PHX",
    "DEN",
    "SLC",
    "DFW",
    "IAH",
    "AUS",
    "SAT",
}


@register_rule
class HawaiiAlaskaRule:
    """Hawaii backtracking banned. Alaska: only 1 flight to, 1 from."""

    rule_id = "hawaii_alaska"
    rule_name = "Hawaii & Alaska Restrictions"
    rule_reference = "Rule 3015 §5, §10"

    def check(self, itinerary, context) -> list[RuleResult]:
        results = []

        # Hawaii backtracking check
        visited_hawaii = False
        left_hawaii = False
        for seg in itinerary.segments:
            if seg.is_surface:
                continue
            if seg.to_airport in _HAWAII_AIRPORTS:
                if left_hawaii:
                    results.append(
                        RuleResult(
                            rule_id=self.rule_id,
                            rule_name=self.rule_name,
                            rule_reference=self.rule_reference,
                            passed=False,
                            severity=Severity.VIOLATION,
                            message="Backtracking to Hawaii after leaving is not permitted.",
                            fix_suggestion="Remove the return flight to Hawaii or restructure routing.",
                        )
                    )
                visited_hawaii = True
            elif visited_hawaii and seg.from_airport in _HAWAII_AIRPORTS:
                left_hawaii = True

        # Alaska flight count
        to_alaska = sum(
            1 for s in itinerary.segments if s.is_flown and s.to_airport in _ALASKA_AIRPORTS
        )
        from_alaska = sum(
            1 for s in itinerary.segments if s.is_flown and s.from_airport in _ALASKA_AIRPORTS
        )

        if to_alaska > 1:
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=f"{to_alaska} flights TO Alaska — only 1 permitted.",
                    fix_suggestion="Remove extra flights to Alaska.",
                )
            )
        if from_alaska > 1:
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=f"{from_alaska} flights FROM Alaska — only 1 permitted.",
                    fix_suggestion="Remove extra flights from Alaska.",
                )
            )

        if not results:
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message="Hawaii/Alaska restrictions: OK.",
                )
            )

        return results


@register_rule
class TranscontinentalUSRule:
    """Only one nonstop transcontinental flight within USA/Canada."""

    rule_id = "transcontinental_us"
    rule_name = "US Transcontinental Limit"
    rule_reference = "Rule 3015 §10"

    def check(self, itinerary, context) -> list[RuleResult]:
        transcon_count = 0
        for seg in itinerary.segments:
            if seg.is_surface:
                continue
            from_east = seg.from_airport in _US_EAST
            from_west = seg.from_airport in _US_WEST
            to_east = seg.to_airport in _US_EAST
            to_west = seg.to_airport in _US_WEST

            if (from_east and to_west) or (from_west and to_east):
                transcon_count += 1

        if transcon_count > 1:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=f"{transcon_count} transcontinental US flights — only 1 permitted.",
                    fix_suggestion="Route through an intermediate hub to avoid nonstop transcontinental.",
                )
            ]

        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=True,
                message=f"US transcontinental flights: {transcon_count}/1.",
            )
        ]


# AU transcontinental airport groups
_AU_EAST_PER = frozenset({"BNE", "CBR", "CNS", "SYD", "MEL"})
_AU_PER = frozenset({"PER"})
_AU_EAST_DRW = frozenset({"CBR", "MEL", "SYD"})
_AU_DRW = frozenset({"DRW"})
_AU_EAST_BME = frozenset({"BNE", "MEL", "SYD"})
_AU_BME_KTA = frozenset({"BME", "KTA"})

_AU_TRANSCON_GROUPS = [
    (_AU_EAST_PER, _AU_PER, "east coast and Perth"),
    (_AU_EAST_DRW, _AU_DRW, "east coast and Darwin"),
    (_AU_EAST_BME, _AU_BME_KTA, "east coast and Broome/Karratha"),
]


@register_rule
class TranscontinentalAURule:
    """Only one transcontinental flight within Australia per pair group."""

    rule_id = "transcontinental_au"
    rule_name = "AU Transcontinental Limit"
    rule_reference = "Rule 3015 SS9"

    def check(self, itinerary, context) -> list[RuleResult]:
        # PER-origin exemption: PER origin with JNB connection
        if itinerary.ticket.origin == "PER":
            if any(
                s.from_airport == "JNB" or s.to_airport == "JNB"
                for s in itinerary.segments
            ):
                return [
                    RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        rule_reference=self.rule_reference,
                        passed=True,
                        severity=Severity.INFO,
                        message="Perth origin with JNB connection — AU transcontinental limit exempt.",
                    )
                ]

        # NZ-origin exemption: NZ origin with JNB connection
        origin_country = get_country(itinerary.ticket.origin)
        if origin_country == "NZ":
            if any(
                s.from_airport == "JNB" or s.to_airport == "JNB"
                for s in itinerary.segments
            ):
                return [
                    RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        rule_reference=self.rule_reference,
                        passed=True,
                        severity=Severity.INFO,
                        message="NZ origin with JNB connection — AU transcontinental limit exempt.",
                    )
                ]

        results: list[RuleResult] = []

        for set_a, set_b, label in _AU_TRANSCON_GROUPS:
            matching_indices: list[int] = []
            for i, seg in enumerate(itinerary.segments):
                if seg.is_surface:
                    continue
                if (seg.from_airport in set_a and seg.to_airport in set_b) or (
                    seg.from_airport in set_b and seg.to_airport in set_a
                ):
                    matching_indices.append(i)

            count = len(matching_indices)

            if count >= 2:
                results.append(
                    RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        rule_reference=self.rule_reference,
                        passed=False,
                        severity=Severity.VIOLATION,
                        message=f"{count} AU transcontinental flights between {label} — only 1 permitted.",
                        fix_suggestion=f"Remove extra {label} segments or route via an intermediate city.",
                        segments_involved=matching_indices,
                    )
                )
            elif count == 1:
                results.append(
                    RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        rule_reference=self.rule_reference,
                        passed=True,
                        severity=Severity.INFO,
                        message=f"1 AU transcontinental flight between {label} (within limit).",
                    )
                )
            # count == 0: skip

        if not results:
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message="No AU transcontinental flights detected.",
                )
            )

        return results
