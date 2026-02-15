"""Tests for HemisphereRevisitRule — continent revisit limits by hemisphere."""

from rtw.models import Itinerary, Ticket, Segment, Severity
from rtw.rules.hemisphere import HemisphereRevisitRule, EuMeAfricaZoneRule
from rtw.validator import build_context


def _make_itinerary(segments_data, origin="CAI"):
    ticket = Ticket(type="DONE4", cabin="business", origin=origin)
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestHemisphereRevisit:
    """HemisphereRevisitRule: northern max 2 visits, southern max 1,
    origin gets +1 bonus when it is the last transition."""

    def test_northern_visited_once_passes(self):
        """EU_ME origin, visit N_America once and return. No revisit issues."""
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "type": "stopover"},
            {"from": "AMM", "to": "JFK", "carrier": "QR", "type": "stopover"},
            {"from": "JFK", "to": "LHR", "carrier": "BA", "type": "stopover"},
            {"from": "LHR", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = HemisphereRevisitRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_northern_visited_twice_passes_with_info(self):
        """CAI origin, Asia visited twice (DOH->NRT, SYD->SIN). Should pass
        with INFO severity noting 2/2 visits."""
        segs = [
            {"from": "CAI", "to": "DOH", "carrier": "QR", "type": "stopover"},
            {"from": "DOH", "to": "NRT", "carrier": "QR", "type": "stopover"},
            {"from": "NRT", "to": "SYD", "carrier": "QF", "type": "stopover"},
            {"from": "SYD", "to": "SIN", "carrier": "QF", "type": "stopover"},
            {"from": "SIN", "to": "LAX", "carrier": "CX", "type": "stopover"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "stopover"},
            {"from": "LHR", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = HemisphereRevisitRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any(r.severity == Severity.INFO for r in results)
        assert any("Asia" in r.message and "2" in r.message for r in results)

    def test_northern_visited_three_times_fails(self):
        """Force 3 visits to Asia (EU->Asia->SWP->Asia->N_Am->Asia->EU).
        Northern max is 2, so the 3rd visit should fail."""
        segs = [
            {"from": "CAI", "to": "DOH", "carrier": "QR", "type": "stopover"},
            # Visit 1: Asia
            {"from": "DOH", "to": "NRT", "carrier": "QR", "type": "stopover"},
            # SWP
            {"from": "NRT", "to": "SYD", "carrier": "QF", "type": "stopover"},
            # Visit 2: Asia
            {"from": "SYD", "to": "SIN", "carrier": "QF", "type": "stopover"},
            # N_America
            {"from": "SIN", "to": "LAX", "carrier": "CX", "type": "stopover"},
            # Visit 3: Asia (back from N_America)
            {"from": "LAX", "to": "HKG", "carrier": "CX", "type": "stopover"},
            # Return to EU_ME
            {"from": "HKG", "to": "LHR", "carrier": "BA", "type": "stopover"},
            {"from": "LHR", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = HemisphereRevisitRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        assert any(r.severity == Severity.VIOLATION for r in results)

    def test_southern_visited_once_passes(self):
        """SYD origin, visit SWP once via stopover (NAN) then leave.
        Southern continents get max 1 visit."""
        segs = [
            {"from": "SYD", "to": "NAN", "carrier": "FJ", "type": "stopover"},
            {"from": "NAN", "to": "LAX", "carrier": "FJ", "type": "stopover"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "stopover"},
            {"from": "LHR", "to": "SYD", "carrier": "QF", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="SYD")
        ctx = build_context(itin)
        results = HemisphereRevisitRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_southern_visited_twice_non_origin_fails(self):
        """CAI origin, visit Africa twice (separate transitions).
        Africa is southern (max 1), not origin, so 2nd visit fails."""
        segs = [
            # Transition EU_ME -> Africa (visit 1)
            {"from": "CAI", "to": "NBO", "carrier": "QR", "type": "stopover"},
            # Africa -> EU_ME
            {"from": "NBO", "to": "DOH", "carrier": "QR", "type": "stopover"},
            # EU_ME -> Asia
            {"from": "DOH", "to": "NRT", "carrier": "QR", "type": "stopover"},
            # Asia -> Africa (visit 2)
            {"from": "NRT", "to": "JNB", "carrier": "QR", "type": "stopover"},
            # Africa -> EU_ME
            {"from": "JNB", "to": "LHR", "carrier": "BA", "type": "stopover"},
            {"from": "LHR", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = HemisphereRevisitRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        assert any(r.severity == Severity.VIOLATION for r in results)

    def test_southern_origin_return_passes(self):
        """SYD (SWP) origin. SWP visited twice in transitions: first via
        NAN (within SWP), then leave to N_America, then return to SYD.
        Origin bonus (+1) applies because SWP is the last transition,
        so 2 appearances (1 + 1 bonus) is allowed."""
        segs = [
            # SWP destination (NAN)
            {"from": "SYD", "to": "NAN", "carrier": "FJ", "type": "stopover"},
            # SWP -> N_America (leave SWP)
            {"from": "NAN", "to": "LAX", "carrier": "FJ", "type": "stopover"},
            # N_America -> EU_ME
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "stopover"},
            # EU_ME -> Asia
            {"from": "LHR", "to": "NRT", "carrier": "JL", "type": "stopover"},
            # Asia -> SWP (return to origin — 2nd SWP in transitions)
            {"from": "NRT", "to": "SYD", "carrier": "QF", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="SYD")
        ctx = build_context(itin)
        results = HemisphereRevisitRule().check(itin, ctx)
        assert all(r.passed for r in results)
        # Should have INFO about return to origin
        assert any(r.severity == Severity.INFO for r in results)
        assert any("return to origin" in r.message.lower() or "origin" in r.message.lower()
                    for r in results)

    def test_southern_origin_not_last_fails(self):
        """JNB (Africa) origin. Africa appears twice in transitions but
        the last transition is EU_ME, not Africa. Without the origin
        bonus, 2 visits to a southern continent exceeds the max-1 limit."""
        segs = [
            # Africa destination (NBO)
            {"from": "JNB", "to": "NBO", "carrier": "QR", "type": "stopover"},
            # Africa -> EU_ME
            {"from": "NBO", "to": "DOH", "carrier": "QR", "type": "stopover"},
            # EU_ME -> Asia
            {"from": "DOH", "to": "NRT", "carrier": "QR", "type": "stopover"},
            # Asia -> Africa (2nd Africa in transitions)
            {"from": "NRT", "to": "CPT", "carrier": "QR", "type": "stopover"},
            # Africa -> EU_ME (ends in EU_ME, NOT Africa => no origin bonus)
            {"from": "CPT", "to": "LHR", "carrier": "BA", "type": "stopover"},
            {"from": "LHR", "to": "CDG", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="JNB")
        ctx = build_context(itin)
        results = HemisphereRevisitRule().check(itin, ctx)
        assert any(not r.passed for r in results)

    def test_asia_twice_with_swp_europe_bridge_info(self):
        """Asia visited 2x, with SWP and EU_ME both present (SWP-Europe bridge).
        Should pass with INFO and message mentioning the bridge exception."""
        segs = [
            {"from": "CAI", "to": "DOH", "carrier": "QR", "type": "stopover"},
            # Visit 1: Asia
            {"from": "DOH", "to": "NRT", "carrier": "QR", "type": "stopover"},
            # SWP
            {"from": "NRT", "to": "SYD", "carrier": "QF", "type": "stopover"},
            # Visit 2: Asia (bridge back from SWP toward EU_ME)
            {"from": "SYD", "to": "SIN", "carrier": "QF", "type": "stopover"},
            # N_America
            {"from": "SIN", "to": "LAX", "carrier": "CX", "type": "stopover"},
            # EU_ME
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "stopover"},
            {"from": "LHR", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = HemisphereRevisitRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("SWP-Europe bridge" in r.message for r in results)

    def test_asia_twice_without_bridge(self):
        """Asia visited 2x, but no SWP or EU_ME in between. Still passes
        (northern allows 2), but message should NOT contain bridge."""
        segs = [
            # Start in N_America
            {"from": "JFK", "to": "NRT", "carrier": "JL", "type": "stopover"},
            # Asia -> S_America
            {"from": "NRT", "to": "GRU", "carrier": "JL", "type": "stopover"},
            # S_America -> Asia (visit 2)
            {"from": "GRU", "to": "HKG", "carrier": "CX", "type": "stopover"},
            # Asia -> N_America (return)
            {"from": "HKG", "to": "JFK", "carrier": "CX", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="JFK")
        ctx = build_context(itin)
        results = HemisphereRevisitRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert not any("bridge" in r.message.lower() for r in results)

    def test_too_few_segments_short_circuit(self):
        """A single segment produces <2 continent entries, triggering
        the short-circuit 'Too few segments' path."""
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "type": "stopover"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = HemisphereRevisitRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("Too few segments" in r.message for r in results)

    def test_v3_fixture_passes(self, v3_itinerary):
        """The V3 reference itinerary should pass hemisphere revisit."""
        itin = Itinerary(**v3_itinerary)
        ctx = build_context(itin)
        results = HemisphereRevisitRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_single_tc_zone_passes(self):
        """All segments within EU_ME. Only 1 continent, no revisit."""
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ", "type": "stopover"},
            {"from": "AMM", "to": "DOH", "carrier": "QR", "type": "stopover"},
            {"from": "DOH", "to": "LHR", "carrier": "QR", "type": "stopover"},
            {"from": "LHR", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = HemisphereRevisitRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_origin_bonus_applied_when_last(self):
        """LHR origin (EU_ME, northern). Transitions include EU_ME 3 times:
        start, mid, and end. Max is 2 for northern, +1 origin bonus when
        last transition = origin. So 3 is allowed."""
        segs = [
            # EU_ME -> Asia
            {"from": "LHR", "to": "NRT", "carrier": "JL", "type": "stopover"},
            # Asia -> EU_ME (visit 2)
            {"from": "NRT", "to": "IST", "carrier": "TK", "type": "stopover"},
            # EU_ME -> N_America
            {"from": "IST", "to": "JFK", "carrier": "TK", "type": "stopover"},
            # N_America -> EU_ME (visit 3, final = origin)
            {"from": "JFK", "to": "LHR", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="LHR")
        ctx = build_context(itin)
        results = HemisphereRevisitRule().check(itin, ctx)
        assert all(r.passed for r in results)


class TestEuMeAfricaZone:
    """EuMeAfricaZoneRule: when ALL intercontinental flights touching Africa
    go to/from EU_ME, South Africa (ZA) and Mauritius (MU) airports are excluded."""

    def test_no_africa_segments_passes(self):
        """No Africa segments at all. CAI is EU_ME (Egypt), so rule doesn't apply."""
        segs = [
            {"from": "CAI", "to": "NRT", "carrier": "QR", "type": "stopover"},
            {"from": "NRT", "to": "LAX", "carrier": "JL", "type": "stopover"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "stopover"},
            {"from": "LHR", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = EuMeAfricaZoneRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_africa_to_asia_ic_exempts(self):
        """Africa has IC flight to Asia (not just EU_ME). Rule doesn't apply."""
        segs = [
            {"from": "CAI", "to": "NBO", "carrier": "QR", "type": "stopover"},
            {"from": "NBO", "to": "NRT", "carrier": "QR", "type": "stopover"},
            {"from": "NRT", "to": "LAX", "carrier": "JL", "type": "stopover"},
            {"from": "LAX", "to": "LHR", "carrier": "BA", "type": "stopover"},
            {"from": "LHR", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = EuMeAfricaZoneRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("does not apply" in r.message for r in results)

    def test_africa_only_eu_me_no_za_passes(self):
        """All Africa IC flights go to/from EU_ME, but no ZA/MU airports. Pass."""
        segs = [
            {"from": "CAI", "to": "NBO", "carrier": "QR", "type": "stopover"},
            {"from": "NBO", "to": "LHR", "carrier": "BA", "type": "stopover"},
            {"from": "LHR", "to": "NRT", "carrier": "JL", "type": "stopover"},
            {"from": "NRT", "to": "LAX", "carrier": "JL", "type": "stopover"},
            {"from": "LAX", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = EuMeAfricaZoneRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("no excluded airports" in r.message for r in results)

    def test_africa_only_eu_me_with_jnb_fails(self):
        """All Africa IC flights to/from EU_ME and JNB (South Africa) present. VIOLATION."""
        segs = [
            {"from": "CAI", "to": "JNB", "carrier": "QR", "type": "stopover"},
            {"from": "JNB", "to": "LHR", "carrier": "BA", "type": "stopover"},
            {"from": "LHR", "to": "NRT", "carrier": "JL", "type": "stopover"},
            {"from": "NRT", "to": "LAX", "carrier": "JL", "type": "stopover"},
            {"from": "LAX", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = EuMeAfricaZoneRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        assert any(r.severity == Severity.VIOLATION for r in results)
        assert any("South Africa" in r.message for r in results)

    def test_africa_only_eu_me_with_mauritius_fails(self):
        """All Africa IC flights to/from EU_ME and MRU (Mauritius) present. VIOLATION."""
        segs = [
            {"from": "CAI", "to": "MRU", "carrier": "QR", "type": "stopover"},
            {"from": "MRU", "to": "LHR", "carrier": "BA", "type": "stopover"},
            {"from": "LHR", "to": "NRT", "carrier": "JL", "type": "stopover"},
            {"from": "NRT", "to": "LAX", "carrier": "JL", "type": "stopover"},
            {"from": "LAX", "to": "CAI", "carrier": "BA", "type": "final"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = EuMeAfricaZoneRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        assert any(r.severity == Severity.VIOLATION for r in results)
        assert any("Mauritius" in r.message for r in results)

    def test_jnb_fixture_not_affected(self):
        """The flyertalk_jnb_business fixture has IC flights from Africa to
        both EU_ME and Asia, so rule should NOT apply."""
        import yaml

        with open("tests/fixtures/flyertalk_jnb_business.yaml") as f:
            data = yaml.safe_load(f)
        itin = Itinerary(**data)
        ctx = build_context(itin)
        results = EuMeAfricaZoneRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("does not apply" in r.message for r in results)
