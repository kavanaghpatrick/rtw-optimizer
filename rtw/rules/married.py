"""Married segment pattern detection. Based on community-reported patterns."""

from rtw.rules.base import register_rule
from rtw.models import RuleResult, Severity


@register_rule
class MarriedSegmentRule:
    """Detect married segment risks from known airline patterns."""

    rule_id = "married_segment"
    rule_name = "Married Segment Detection"
    rule_reference = "Community knowledge (FlyerTalk)"

    # Carriers with known hub O&D control patterns.
    # These carriers use Origin-Destination revenue management to block D-class
    # for standalone segments to/from their hub, while releasing it for
    # connecting itineraries through the hub.
    _HUB_CARRIERS = {
        "CX": ("HKG", "Cathay Pacific uses O&D control at HKG — D-class may only be available for connecting itineraries through HKG, not standalone segments to/from HKG"),
        "QR": ("DOH", "Qatar Airways uses aggressive O&D control at DOH — D-class may only be available for connecting itineraries through DOH"),
    }

    def check(self, itinerary, context) -> list[RuleResult]:
        results = []

        # Check 1: CX hub-connection patterns
        for i, seg in enumerate(itinerary.segments):
            if not seg.is_flown or not seg.carrier:
                continue
            if seg.carrier in self._HUB_CARRIERS:
                hub, reason = self._HUB_CARRIERS[seg.carrier]
                from_apt = seg.from_airport
                to_apt = seg.to_airport
                # If neither endpoint is the hub, D-class may be married through hub
                if from_apt != hub and to_apt != hub:
                    results.append(
                        RuleResult(
                            rule_id=self.rule_id,
                            rule_name=self.rule_name,
                            rule_reference=self.rule_reference,
                            passed=False,
                            severity=Severity.INFO,
                            message=(
                                f"Seg {i+1} {from_apt}-{to_apt} on {seg.carrier}: "
                                f"{reason}. D-class may only be available "
                                f"on connecting itineraries through {hub}."
                            ),
                            fix_suggestion=(
                                f"Check if adding a {hub} stopover improves D-class availability, "
                                f"or verify standalone availability via ExpertFlyer."
                            ),
                            segments_involved=[i],
                        )
                    )

        # Check 2: Through-flight split risk
        # If a segment has a via stop, and that via city appears as a
        # stopover destination elsewhere, splitting could trigger reissue fees.
        via_cities = {}  # via_airport -> segment_index
        stopover_cities = set()

        for i, seg in enumerate(itinerary.segments):
            if seg.has_via:
                for via_apt in seg.via_airports:
                    via_cities[via_apt] = i
            if seg.is_stopover:
                stopover_cities.add(seg.to_airport)

        for via_apt, seg_idx in via_cities.items():
            if via_apt in stopover_cities:
                seg = itinerary.segments[seg_idx]
                results.append(
                    RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        rule_reference="Qantas AgencyConnect",
                        passed=False,
                        severity=Severity.INFO,
                        message=(
                            f"Seg {seg_idx+1} {seg.from_airport}-{seg.to_airport} "
                            f"is a through-flight via {via_apt}, but {via_apt} also "
                            f"appears as a stopover. Splitting the through-flight "
                            f"into separate segments may require reissue + fee."
                        ),
                        fix_suggestion=(
                            f"Keep {seg.from_airport}-{seg.to_airport} as a single "
                            f"through-flight segment. If you need a stopover in "
                            f"{via_apt}, book separate segments instead."
                        ),
                        segments_involved=[seg_idx],
                    )
                )

        if not results:
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    rule_reference=self.rule_reference,
                    passed=True,
                    severity=Severity.INFO,
                    message="No married segment risks detected.",
                )
            )

        return results
