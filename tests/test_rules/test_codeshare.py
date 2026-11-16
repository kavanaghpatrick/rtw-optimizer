"""Tests for QFJQCodeshareRule, EligibleCarrierRule §4(j) handling and QFWithinUSARule."""

from rtw.models import Itinerary, Ticket, Segment, Severity
from rtw.rules.carriers import EligibleCarrierRule, QFJQCodeshareRule, QFWithinUSARule
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
        """JQ as carrier (a Jetstar flight number) = VIOLATION (Rule 3015 §4(j))."""
        segs = [
            {"from": "SYD", "to": "MEL", "carrier": "JQ"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = EligibleCarrierRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION and not r.passed]
        assert len(violations) == 1
        assert "operating_carrier: JQ" in violations[0].fix_suggestion
        assert "carrier: QF" in violations[0].fix_suggestion
        assert violations[0].rule_reference == "Rule 3015 §4(j)"

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

    def test_eligible_carrier_qf_operated_by_jq_passes(self):
        """QF-marketed, JQ-operated is the one non-member codeshare §4(j) allows."""
        segs = [
            {"from": "SYD", "to": "MEL", "carrier": "QF", "operating_carrier": "JQ"},
        ]
        itin = _make_itinerary(segs)
        results = EligibleCarrierRule().check(itin, build_context(itin))
        assert all(r.passed for r in results)

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


class TestCodeshareSection4j:
    """Rule 3015 §4(j): codeshares only when operated by an eligible carrier."""

    def _violations(self, segs, origin="LHR"):
        itin = _make_itinerary(segs, origin=origin)
        results = EligibleCarrierRule().check(itin, build_context(itin))
        return [r for r in results if not r.passed and r.severity == Severity.VIOLATION]

    def test_qf_operated_by_ek_violation(self):
        v = self._violations([{"from": "SYD", "to": "DXB", "carrier": "QF", "operating_carrier": "EK"}], "SYD")
        assert len(v) == 1
        assert "EK" in v[0].message and "§4(j)" in v[0].message

    def test_aa_operated_by_ei_violation(self):
        v = self._violations([{"from": "JFK", "to": "DUB", "carrier": "AA", "operating_carrier": "EI"}], "JFK")
        assert len(v) == 1

    def test_qr_operated_by_la_violation(self):
        v = self._violations([{"from": "GRU", "to": "SCL", "carrier": "QR", "operating_carrier": "LA"}], "GRU")
        assert len(v) == 1

    def test_operated_by_other_eligible_member_passes(self):
        assert not self._violations([{"from": "LHR", "to": "HEL", "carrier": "BA", "operating_carrier": "AY"}])

    def test_affiliate_operator_passes(self):
        segs = [
            {"from": "SEA", "to": "PDX", "carrier": "AS", "operating_carrier": "QX"},
            {"from": "PDX", "to": "DFW", "carrier": "AA", "operating_carrier": "MQ"},
            {"from": "DFW", "to": "LCY", "carrier": "BA", "operating_carrier": "CJ"},
            {"from": "LCY", "to": "MAD", "carrier": "IB", "operating_carrier": "I2"},
            {"from": "MAD", "to": "HEL", "carrier": "AY", "operating_carrier": "N7"},
            {"from": "HEL", "to": "ITM", "carrier": "JL", "operating_carrier": "XM"},
        ]
        assert not self._violations(segs, "SEA")

    def test_jq_operating_under_other_marketing_code_violation(self):
        """Only QF codeshares on Jetstar are excepted, not e.g. BA-marketed."""
        v = self._violations([{"from": "SYD", "to": "MEL", "carrier": "BA", "operating_carrier": "JQ"}], "SYD")
        assert len(v) == 1

    def test_nu_is_eligible(self):
        """Japan Transocean Air (NU) is an eligible carrier in Rule 3015."""
        segs = [
            {"from": "LHR", "to": "HND", "carrier": "JL"},
            {"from": "HND", "to": "OKA", "carrier": "NU"},
        ]
        assert not self._violations(segs)

    def test_ha_retired_code_routes_to_as(self):
        itin = _make_itinerary([{"from": "HNL", "to": "LAX", "carrier": "HA"}], origin="HNL")
        results = EligibleCarrierRule().check(itin, build_context(itin))
        assert all(r.passed for r in results)
        info = [r for r in results if r.severity == Severity.INFO]
        assert info and "carrier: AS" in info[0].fix_suggestion


class TestQFWithinUSA:
    def _results(self, segs, origin="SYD"):
        itin = _make_itinerary(segs, origin=origin)
        return QFWithinUSARule().check(itin, build_context(itin))

    def test_qf_us_domestic_connecting_at_lax_warns(self):
        r = self._results([
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "JFK", "carrier": "QF"},
        ])
        assert len(r) == 1
        assert r[0].severity == Severity.WARNING and not r[0].passed

    def test_qf_us_domestic_without_qf_at_lax_violation(self):
        r = self._results([
            {"from": "JFK", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "SYD", "carrier": "AA"},
        ], origin="JFK")
        assert len(r) == 1
        assert r[0].severity == Severity.VIOLATION and not r[0].passed

    def test_qf_marketed_aa_operated_not_flagged(self):
        r = self._results([
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "JFK", "carrier": "QF", "operating_carrier": "AA"},
        ])
        assert all(x.passed for x in r)

    def test_no_qf_in_usa_passes(self):
        r = self._results([{"from": "SYD", "to": "LAX", "carrier": "QF"}])
        assert all(x.passed for x in r)
