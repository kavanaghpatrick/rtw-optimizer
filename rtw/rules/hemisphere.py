"""Hemisphere / continent revisit rules. Rule 3015 SS11."""

from rtw.rules.base import register_rule
from rtw.models import RuleResult, Severity, Continent
from rtw.continents import get_continent, get_country

# Hemisphere classification per Rule 3015 Section 11 / Section 3.
# Each Tariff Conference has one northern and one southern continent:
#   TC1: N_America (north) / S_America (south)
#   TC2: EU_ME (north) / Africa (south)
#   TC3: Asia (north) / SWP (south)

NORTHERN_HEMISPHERE: set[Continent] = {
    Continent.ASIA,
    Continent.EU_ME,
    Continent.N_AMERICA,
}

SOUTHERN_HEMISPHERE: set[Continent] = {
    Continent.AFRICA,
    Continent.SWP,
    Continent.S_AMERICA,
}

# Maximum visits by hemisphere
MAX_VISITS_NORTHERN = 2  # Can visit twice
MAX_VISITS_SOUTHERN = 1  # Can visit once only


@register_rule
class HemisphereRevisitRule:
    """Hemisphere-aware continent revisit rule (Rule 3015 Section 11).

    Northern hemisphere continents (Asia, EU/ME, N_America) may be visited
    up to twice.  Southern hemisphere continents (Africa, SWP, S_America)
    may be visited only once.

    The origin continent receives +1 allowance for the mandatory return leg,
    provided it appears as the final entry in the transition sequence.

    An informational note is emitted when Asia is visited twice and the
    itinerary also includes both SWP and EU_ME (the SWP-Europe bridge
    exception of Section 4).
    """

    rule_id = "hemisphere_revisit"
    rule_name = "Hemisphere Revisit"
    rule_reference = "Rule 3015 SS11"

    def check(self, itinerary, context) -> list[RuleResult]:
        # Build continent sequence from segment destinations, skipping None
        continent_seq: list[Continent] = [
            c for c in context.segment_continents if c is not None
        ]

        if len(continent_seq) < 2:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message="Too few segments to check continent revisit.",
                )
            ]

        # Build transition sequence (remove consecutive duplicates)
        transitions: list[Continent] = [continent_seq[0]]
        for c in continent_seq[1:]:
            if c != transitions[-1]:
                transitions.append(c)

        # Count visits per continent.
        # Each appearance in the deduplicated transition list is a separate visit.
        visit_count: dict[Continent, int] = {}
        for cont in transitions:
            visit_count[cont] = visit_count.get(cont, 0) + 1

        origin = context.origin_continent
        violations: list[str] = []
        infos: list[str] = []

        for continent, count in visit_count.items():
            is_northern = continent in NORTHERN_HEMISPHERE
            max_allowed = MAX_VISITS_NORTHERN if is_northern else MAX_VISITS_SOUTHERN

            # The origin continent gets +1 allowance for the return leg,
            # but only if it actually appears at the end of the transition sequence.
            origin_bonus = 0
            if continent == origin and transitions[-1] == continent:
                origin_bonus = 1

            effective_max = max_allowed + origin_bonus

            if count > effective_max:
                hemisphere = "northern" if is_northern else "southern"
                bonus_note = " + 1 for return to origin" if origin_bonus else ""
                violations.append(
                    f"Continent {continent.value} visited {count} times "
                    f"(max {max_allowed} for {hemisphere} hemisphere{bonus_note})."
                )
            elif count > 1 and is_northern:
                msg = (
                    f"{continent.value} visited {count}/{max_allowed} times "
                    f"(northern hemisphere allows {max_allowed})"
                )
                if (
                    continent == Continent.ASIA
                    and self._asia_swp_europe_exception_applies(transitions)
                ):
                    msg += "; SWP-Europe bridge exception also applies"
                infos.append(msg)
            elif count > 1 and not is_northern and continent == origin:
                infos.append(
                    f"{continent.value} visited {count} times "
                    f"(return to origin permitted)"
                )

        if violations:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=" | ".join(violations),
                    fix_suggestion=(
                        "Reduce revisits to stay within hemisphere limits: "
                        "northern continents (Asia, EU/ME, N.America) max 2 visits, "
                        "southern continents (Africa, SWP, S.America) max 1 visit."
                    ),
                )
            ]

        # Build pass message
        pass_msg = (
            f"Hemisphere revisit check passed. "
            f"Sequence: {' -> '.join(c.value for c in transitions)}."
        )
        if infos:
            pass_msg += " " + " | ".join(infos)

        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=True,
                severity=Severity.INFO if infos else Severity.VIOLATION,
                message=pass_msg,
            )
        ]

    @staticmethod
    def _asia_swp_europe_exception_applies(transitions: list[Continent]) -> bool:
        """Check if the Asia SWP-Europe bridge exception applies.

        Two visits to Asia are permitted when the itinerary connects
        SWP and Europe/Middle East (meaning Asia serves as a bridge).
        """
        has_swp = Continent.SWP in transitions
        has_eu_me = Continent.EU_ME in transitions
        return has_swp and has_eu_me


@register_rule
class EuMeAfricaZoneRule:
    """EU/ME-Africa zone restriction: SA and Mauritius excluded when both IC flights are Africa↔EU/ME.

    Rule 3015 SS11: If both intercontinental flights are between Africa and the
    Europe Zone, then South Africa and Mauritius cannot be included.
    """

    rule_id = "eu_me_africa_zone"
    rule_name = "EU/ME-Africa Zone Restriction"
    rule_reference = "Rule 3015 SS11"

    # Countries excluded when restriction applies
    _EXCLUDED_COUNTRIES = frozenset({"ZA", "MU"})

    def check(self, itinerary, context) -> list[RuleResult]:
        # Find all intercontinental segments touching Africa or EU_ME
        africa_ic_segments = []
        non_africa_eu_me_ic = False

        for i, seg in enumerate(itinerary.segments):
            from_cont = get_continent(seg.from_airport)
            to_cont = get_continent(seg.to_airport)
            if not from_cont or not to_cont or from_cont == to_cont:
                continue

            # This is an intercontinental segment
            # Check if it involves Africa
            if Continent.AFRICA in (from_cont, to_cont):
                other = to_cont if from_cont == Continent.AFRICA else from_cont
                if other == Continent.EU_ME:
                    africa_ic_segments.append(i)
                else:
                    # Africa connects to something other than EU/ME
                    non_africa_eu_me_ic = True

        # Rule only applies if ALL intercontinental flights touching Africa go to/from EU_ME
        if not africa_ic_segments or non_africa_eu_me_ic:
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    message="EU/ME-Africa zone restriction does not apply.",
                )
            ]

        # Check for excluded countries (ZA, MU) in any segment
        excluded_segments = []
        for i, seg in enumerate(itinerary.segments):
            for airport in (seg.from_airport, seg.to_airport):
                country = get_country(airport)
                if country in self._EXCLUDED_COUNTRIES:
                    excluded_segments.append((i, airport, country))

        if excluded_segments:
            airports = ", ".join(
                f"{apt} ({'South Africa' if cc == 'ZA' else 'Mauritius'})"
                for _, apt, cc in excluded_segments
            )
            seg_nums = ", ".join(str(idx + 1) for idx, _, _ in excluded_segments)
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=False,
                    severity=Severity.VIOLATION,
                    message=(
                        f"Both intercontinental flights to/from Africa are via EU/ME zone. "
                        f"South Africa and Mauritius cannot be included. "
                        f"Affected airports: {airports} (segments {seg_nums})."
                    ),
                    fix_suggestion="Route Africa via a non-EU/ME continent or remove South Africa/Mauritius stops.",
                    segments_involved=[idx for idx, _, _ in excluded_segments],
                )
            ]

        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                rule_reference=self.rule_reference,
                passed=True,
                message="EU/ME-Africa zone: no excluded airports found.",
            )
        ]
