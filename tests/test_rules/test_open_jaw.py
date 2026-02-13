"""Tests for OpenJawPairsRule and ReturnToOriginRule open-jaw handling."""

from rtw.models import Itinerary, Ticket, Segment, Severity
from rtw.rules.validity import OpenJawPairsRule, ReturnToOriginRule
from rtw.validator import build_context


def _make_itinerary(segments_data, origin="LHR"):
    ticket = Ticket(type="DONE4", cabin="business", origin=origin)
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestOpenJawPairsRule:
    def test_same_country_uk(self):
        """LHR->MAN: both UK = permitted."""
        segs = [
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "MAN", "carrier": "AA"},
        ]
        itin = _make_itinerary(segs, origin="LHR")
        ctx = build_context(itin)
        results = OpenJawPairsRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("United Kingdom" in r.message or "permitted" in r.message for r in results)

    def test_us_ca(self):
        """JFK->YYZ: US<->Canada bilateral = permitted."""
        segs = [
            {"from": "JFK", "to": "LHR", "carrier": "BA"},
            {"from": "LHR", "to": "YYZ", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs, origin="JFK")
        ctx = build_context(itin)
        results = OpenJawPairsRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_different_country_violation(self):
        """LHR->CDG: UK/France = NOT permitted."""
        segs = [
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "CDG", "carrier": "AA"},
        ]
        itin = _make_itinerary(segs, origin="LHR")
        ctx = build_context(itin)
        results = OpenJawPairsRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) == 1
        assert violations[0].fix_suggestion is not None

    def test_middle_east(self):
        """CAI->DOH: both Middle East = permitted."""
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            {"from": "AMM", "to": "DOH", "carrier": "QR"},
        ]
        itin = _make_itinerary(segs, origin="CAI")
        ctx = build_context(itin)
        results = OpenJawPairsRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("Middle East" in r.message for r in results)

    def test_hk_china(self):
        """HKG->PVG: HK<->China bilateral = permitted."""
        segs = [
            {"from": "HKG", "to": "NRT", "carrier": "CX"},
            {"from": "NRT", "to": "PVG", "carrier": "JL"},
        ]
        itin = _make_itinerary(segs, origin="HKG")
        ctx = build_context(itin)
        results = OpenJawPairsRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_my_sg(self):
        """KUL->SIN: Malaysia<->Singapore bilateral = permitted."""
        segs = [
            {"from": "KUL", "to": "NRT", "carrier": "MH"},
            {"from": "NRT", "to": "SIN", "carrier": "JL"},
        ]
        itin = _make_itinerary(segs, origin="KUL")
        ctx = build_context(itin)
        results = OpenJawPairsRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_mv_lk(self):
        """MLE->CMB: Maldives<->Sri Lanka bilateral = permitted."""
        segs = [
            {"from": "MLE", "to": "NRT", "carrier": "UL"},
            {"from": "NRT", "to": "CMB", "carrier": "UL"},
        ]
        itin = _make_itinerary(segs, origin="MLE")
        ctx = build_context(itin)
        results = OpenJawPairsRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_mv_in(self):
        """MLE->DEL: Maldives<->India bilateral = permitted."""
        segs = [
            {"from": "MLE", "to": "NRT", "carrier": "UL"},
            {"from": "NRT", "to": "DEL", "carrier": "JL"},
        ]
        itin = _make_itinerary(segs, origin="MLE")
        ctx = build_context(itin)
        results = OpenJawPairsRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_africa(self):
        """JNB->NBO: both Africa = permitted."""
        segs = [
            {"from": "JNB", "to": "LHR", "carrier": "BA"},
            {"from": "LHR", "to": "NBO", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs, origin="JNB")
        ctx = build_context(itin)
        results = OpenJawPairsRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_return_to_origin_defers(self):
        """ReturnToOriginRule also passes for permitted open jaw."""
        segs = [
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "MAN", "carrier": "AA"},
        ]
        itin = _make_itinerary(segs, origin="LHR")
        ctx = build_context(itin)
        results = ReturnToOriginRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_return_to_origin_still_passes_exact(self):
        """ReturnToOriginRule still passes for exact origin match."""
        segs = [
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "LHR", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs, origin="LHR")
        ctx = build_context(itin)
        results = ReturnToOriginRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_return_to_origin_same_city(self):
        """ReturnToOriginRule passes for same-city (LHR/LGW)."""
        segs = [
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "LGW", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs, origin="LHR")
        ctx = build_context(itin)
        results = ReturnToOriginRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_violation_fix_suggestion(self):
        """Violation includes permitted pairs in fix_suggestion."""
        segs = [
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "CDG", "carrier": "AA"},
        ]
        itin = _make_itinerary(segs, origin="LHR")
        ctx = build_context(itin)
        results = OpenJawPairsRule().check(itin, ctx)
        violations = [r for r in results if not r.passed]
        assert len(violations) == 1
        assert "US" in violations[0].fix_suggestion or "Middle East" in violations[0].fix_suggestion

    def test_origin_equals_dest_not_open_jaw(self):
        """Origin == destination: 'returns to origin', not open jaw."""
        segs = [
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "LHR", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs, origin="LHR")
        ctx = build_context(itin)
        results = OpenJawPairsRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("origin" in r.message.lower() for r in results)

    def test_unknown_airport_graceful(self):
        """Unknown airport in open jaw doesn't crash."""
        segs = [
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "ZZZ", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs, origin="LHR")
        ctx = build_context(itin)
        results = OpenJawPairsRule().check(itin, ctx)
        # Should not crash, should return a result
        assert len(results) > 0

    def test_v3_fixture_still_passes_return(self, v3_itinerary):
        """V3 fixture still passes ReturnToOriginRule."""
        itin = Itinerary(**v3_itinerary)
        ctx = build_context(itin)
        results = ReturnToOriginRule().check(itin, ctx)
        assert all(r.passed for r in results)
