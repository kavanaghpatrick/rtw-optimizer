"""Tests for rtw.codeshare (codeshare tier-point earning checker)."""

import pytest

from rtw.codeshare import (
    analyze_codeshares,
    build_options,
    earning_band,
)


class TestEarningBand:
    def test_distance_carriers(self):
        assert earning_band("QR").method == "distance"
        assert earning_band("QR").pct == 50
        assert earning_band("CX").pct == 25
        assert earning_band("WY").pct == 12.5

    def test_spend_carriers(self):
        for c in ("BA", "AA", "IB"):
            b = earning_band(c)
            assert b.method == "spend"
            assert b.pct is None

    def test_unknown_carrier(self):
        assert earning_band("ZZ").method == "unknown"

    def test_case_insensitive(self):
        assert earning_band("cx").pct == 25

    def test_finnair_codeshare_exception_is_spend(self):
        """AY codeshare numbers 2501-7000 earn spend, not distance."""
        b = earning_band("AY", "AY5449")
        assert b.method == "spend"
        assert "exception" in b.label
        # Evidence is a Finnair Plus change, not a BA Club rule.
        assert "unverified for BA Club" in b.caveat
        assert earning_band("QR").caveat == ""

    def test_finnair_own_flight_still_distance(self):
        """AY outside the codeshare range (or with no flight #) earns 50%."""
        assert earning_band("AY", "AY900").pct == 50
        assert earning_band("AY").pct == 50


def _rows():
    # A CX-operated HKG-LHR sold under CX (current, 25%) plus two 50%-band codes.
    return [
        {"marketing_carrier": "CX", "marketing_flight": "CX253", "d_seats": 9},
        {"marketing_carrier": "QR", "marketing_flight": "QR6969", "d_seats": 4},
        {"marketing_carrier": "JL", "marketing_flight": "JL7000", "d_seats": 0},
        {"marketing_carrier": "AA", "marketing_flight": "AA8001", "d_seats": 9},
    ]


class TestAnalyze:
    def test_ranks_50_above_25_above_spend(self):
        opts = build_options(_rows(), current_carrier="CX")
        a = analyze_codeshares(opts, distance_miles=5984, current_carrier="CX",
                               route="HKG-LHR")
        methods = [(o.marketing_carrier, o.earning.pct) for o in a.options]
        # QR/JL (50) come before CX (25); AA (spend) last
        assert methods[0][1] == 50
        assert a.options[-1].marketing_carrier == "AA"

    def test_best_bookable_skips_sold_out(self):
        """JL is 50% but D0 (sold out) -> best bookable is QR (50%, D4)."""
        opts = build_options(_rows(), current_carrier="CX")
        a = analyze_codeshares(opts, distance_miles=5984, current_carrier="CX")
        assert a.best_bookable is not None
        assert a.best_bookable.marketing_carrier == "QR"

    def test_tp_gain_is_50_minus_25(self):
        opts = build_options(_rows(), current_carrier="CX")
        a = analyze_codeshares(opts, distance_miles=5984, current_carrier="CX")
        # CX 25% = 1496; QR 50% = 2992; gain 1496
        assert a.current.estimated_tp == pytest.approx(1496, abs=1)
        assert a.best_bookable.estimated_tp == pytest.approx(2992, abs=1)
        assert a.tp_gain == pytest.approx(1496, abs=1)

    def test_current_is_marked(self):
        opts = build_options(_rows(), current_carrier="CX")
        a = analyze_codeshares(opts, distance_miles=5984, current_carrier="CX")
        assert a.current is not None
        assert a.current.marketing_carrier == "CX"

    def test_no_gain_when_already_top_band(self):
        """If the current leg is already 50%, there is no better distance swap."""
        rows = [
            {"marketing_carrier": "JL", "marketing_flight": "JL15", "d_seats": 9},
            {"marketing_carrier": "AA", "marketing_flight": "AA80", "d_seats": 9},
        ]
        opts = build_options(rows, current_carrier="JL")
        a = analyze_codeshares(opts, distance_miles=5149, current_carrier="JL")
        # best bookable is JL itself (50%); no positive gain over current
        assert a.best_bookable.marketing_carrier == "JL"
        assert a.tp_gain in (None, 0, 0.0)

    def test_finnair_codeshare_excluded_from_swap(self):
        """An AY codeshare in the spend range must not be offered as a 50% swap."""
        rows = [
            {"marketing_carrier": "BA", "marketing_flight": "BA49", "d_seats": 9},
            {"marketing_carrier": "AY", "marketing_flight": "AY5449", "d_seats": 9},
        ]
        opts = build_options(rows, current_carrier="BA")
        a = analyze_codeshares(opts, distance_miles=4786, current_carrier="BA")
        ay = next(o for o in a.options if o.marketing_carrier == "AY")
        assert ay.earning.method == "spend"
        # No distance option exists -> no bookable swap
        assert a.best_bookable is None

    def test_caveats_present(self):
        opts = build_options(_rows(), current_carrier="CX")
        a = analyze_codeshares(opts, distance_miles=5984, current_carrier="CX")
        joined = " ".join(a.caveats)
        assert "MARKETING carrier" in joined
        assert "Rule 3015" in joined


class TestSection4jEligibility:
    """Rule 3015 §4(j): options the fare does not permit are never a swap."""

    def test_qr_code_on_latam_flight_is_not_best_swap(self):
        rows = [
            {"marketing_carrier": "LA", "marketing_flight": "LA800", "operating_carrier": "LA", "d_seats": 9},
            {"marketing_carrier": "QR", "marketing_flight": "QR4567", "operating_carrier": "LA", "d_seats": 9},
        ]
        opts = build_options(rows, current_carrier="LA")
        a = analyze_codeshares(opts, distance_miles=7000, current_carrier="LA")
        assert a.best_bookable is None
        assert a.tp_gain is None
        for o in a.options:
            assert o.eligible is False
            assert o.estimated_tp is None
            assert "§4(j)" in o.note

    def test_ineligible_option_skipped_for_eligible_one(self):
        rows = [
            {"marketing_carrier": "CX", "marketing_flight": "CX253", "d_seats": 9},
            {"marketing_carrier": "QR", "marketing_flight": "QR6969", "operating_carrier": "EK", "d_seats": 9},
            {"marketing_carrier": "JL", "marketing_flight": "JL7000", "operating_carrier": "CX", "d_seats": 4},
        ]
        opts = build_options(rows, current_carrier="CX")
        a = analyze_codeshares(opts, distance_miles=5984, current_carrier="CX")
        assert a.best_bookable.marketing_carrier == "JL"
        qr = next(o for o in a.options if o.marketing_carrier == "QR")
        assert qr.eligible is False and qr.estimated_tp is None

    def test_manually_built_option_is_checked(self):
        from rtw.codeshare import CodeshareOption

        o = CodeshareOption(marketing_carrier="QR", operating_carrier="LA", earning=earning_band("QR"))
        a = analyze_codeshares([o], distance_miles=1000)
        assert o.eligible is False
        assert a.best_bookable is None
        assert o.note.count("§4(j)") == 1

    def test_qf_on_jetstar_is_eligible(self):
        opts = build_options([{"marketing_carrier": "QF", "operating_carrier": "JQ", "d_seats": 1}])
        assert opts[0].eligible is True
