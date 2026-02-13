"""Tests for QFJQCodeshareRule and EligibleCarrierRule JQ handling."""

from rtw.models import Itinerary, Ticket, Segment, Severity
from rtw.rules.carriers import EligibleCarrierRule, QFJQCodeshareRule
from rtw.validator import build_context


def _make_itinerary(segments_data, origin="SYD", plating_carrier=None):
    ticket = Ticket(type="DONE4", cabin="business", origin=origin, plating_carrier=plating_carrier)
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestQFJQCodeshare:
    def test_qf_with_jq_operating_passes(self):
        """QF carrier with JQ operating = codeshare rule PASS."""
        segs = [
            {"from": "SYD", "to": "MEL", "carrier": "QF", "operating_carrier": "JQ"},
        ]
        itin = _make_itinerary(segs, plating_carrier="BA")
        ctx = build_context(itin)
        results = QFJQCodeshareRule().check(itin, ctx)
        # operating_carrier=JQ triggers JQ detection
        assert all(r.passed for r in results)

    def test_jq_carrier_alone_info(self):
        """JQ as carrier (not operating) = EligibleCarrierRule PASS with INFO."""
        segs = [
            {"from": "SYD", "to": "MEL", "carrier": "JQ"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = EligibleCarrierRule().check(itin, ctx)
        # JQ should be recognized as QF codeshare, not violation
        assert all(r.passed for r in results)
        info_results = [r for r in results if r.severity == Severity.INFO]
        assert len(info_results) >= 1
        assert "codeshare" in info_results[0].message.lower()

    def test_jq_plating_ib_warning(self):
        """JQ segments + IB plating = WARNING."""
        segs = [
            {"from": "SYD", "to": "MEL", "carrier": "JQ"},
        ]
        itin = _make_itinerary(segs, plating_carrier="IB")
        ctx = build_context(itin)
        results = QFJQCodeshareRule().check(itin, ctx)
        warnings = [r for r in results if r.severity == Severity.WARNING]
        assert len(warnings) >= 1
        assert "IB" in warnings[0].message

    def test_jq_plating_as_warning(self):
        """JQ segments + AS plating = WARNING."""
        segs = [
            {"from": "SYD", "to": "MEL", "carrier": "JQ"},
        ]
        itin = _make_itinerary(segs, plating_carrier="AS")
        ctx = build_context(itin)
        results = QFJQCodeshareRule().check(itin, ctx)
        warnings = [r for r in results if r.severity == Severity.WARNING]
        assert len(warnings) >= 1

    def test_jq_plating_ba_passes(self):
        """JQ segments + BA plating = PASS."""
        segs = [
            {"from": "SYD", "to": "MEL", "carrier": "JQ"},
        ]
        itin = _make_itinerary(segs, plating_carrier="BA")
        ctx = build_context(itin)
        results = QFJQCodeshareRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_operating_carrier_optional(self):
        """operating_carrier=None doesn't crash."""
        segs = [
            {"from": "SYD", "to": "MEL", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = QFJQCodeshareRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_eligible_carrier_jq_not_violation(self):
        """JQ should NOT trigger EligibleCarrierRule VIOLATION."""
        segs = [
            {"from": "SYD", "to": "MEL", "carrier": "JQ"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = EligibleCarrierRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) == 0

    def test_s7_still_ineligible(self):
        """S7 is still ineligible after codeshare changes."""
        segs = [
            {"from": "OVB", "to": "SVO", "carrier": "S7"},
        ]
        itin = _make_itinerary(segs, origin="OVB")
        ctx = build_context(itin)
        results = EligibleCarrierRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1

    def test_la_still_ineligible(self):
        """LA (LATAM) is still ineligible."""
        segs = [
            {"from": "SCL", "to": "GRU", "carrier": "LA"},
        ]
        itin = _make_itinerary(segs, origin="SCL")
        ctx = build_context(itin)
        results = EligibleCarrierRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1

    def test_no_jq_segments_passes(self):
        """No JQ segments = codeshare rule PASS."""
        segs = [
            {"from": "SYD", "to": "MEL", "carrier": "QF"},
            {"from": "MEL", "to": "LHR", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = QFJQCodeshareRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("No codeshare" in r.message for r in results)

    def test_plating_carrier_none_graceful(self):
        """JQ segments + no plating carrier = PASS."""
        segs = [
            {"from": "SYD", "to": "MEL", "carrier": "JQ"},
        ]
        itin = _make_itinerary(segs)  # no plating_carrier
        ctx = build_context(itin)
        results = QFJQCodeshareRule().check(itin, ctx)
        assert all(r.passed for r in results)
