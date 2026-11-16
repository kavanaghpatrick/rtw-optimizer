"""Tests for segment and continent limit rules."""

from rtw.models import Continent, Itinerary, Ticket, Segment, Severity
from rtw.rules.segments import SegmentCountRule, PerContinentLimitRule, SegmentConnectivityRule
from rtw.validator import build_context


def _make_itinerary(segments_data: list[dict], ticket_type="DONE4") -> Itinerary:
    """Helper to build itinerary from segment dicts."""
    ticket = Ticket(type=ticket_type, cabin="business", origin="CAI")
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestSegmentCount:
    def test_valid_16_segments(self, v3_itinerary):
        itin = Itinerary(**v3_itinerary)
        ctx = build_context(itin)
        results = SegmentCountRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_too_many_segments(self):
        segs = [{"from": "CAI", "to": "AMM", "carrier": "RJ"}] * 17
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = SegmentCountRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        assert "17" in results[0].message

    def test_too_few_segments(self):
        segs = [{"from": "CAI", "to": "AMM", "carrier": "RJ"}] * 2
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = SegmentCountRule().check(itin, ctx)
        assert any(not r.passed for r in results)

    def test_minimum_3_passes(self):
        segs = [{"from": "CAI", "to": "AMM", "carrier": "RJ"}] * 3
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = SegmentCountRule().check(itin, ctx)
        assert all(r.passed for r in results)


class TestImplicitSurfaceSectors:
    """Same-city airport changes are surface sectors (Rule 3015 §4)."""

    @staticmethod
    def _fifteen_with_two_gaps() -> Itinerary:
        # 15 listed segments; NRT->HND (Tokyo) and JFK->LGA (New York) gaps
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            {"from": "AMM", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "NRT", "carrier": "QR"},
            {"from": "HND", "to": "TPE", "carrier": "JL"},
            {"from": "TPE", "to": "HKG", "carrier": "CX"},
            {"from": "HKG", "to": "SIN", "carrier": "CX"},
            {"from": "SIN", "to": "NAN", "carrier": "FJ"},
            {"from": "NAN", "to": "SFO", "carrier": "FJ"},
            {"from": "SFO", "to": "JFK", "carrier": "AA"},
            {"from": "LGA", "to": "ORD", "carrier": "AA"},
            {"from": "ORD", "to": "DFW", "carrier": "AA"},
            {"from": "DFW", "to": "MIA", "carrier": "AA"},
            {"from": "MIA", "to": "MEX", "carrier": "AA"},
            {"from": "MEX", "to": "MAD", "carrier": "IB"},
            {"from": "MAD", "to": "CAI", "carrier": "IB"},
        ]
        return _make_itinerary(segs)

    def test_15_listed_plus_2_gaps_fails_with_17(self):
        itin = self._fifteen_with_two_gaps()
        assert len(itin.segments) == 15
        ctx = build_context(itin)
        assert ctx.implicit_surface_count == 2
        results = SegmentCountRule().check(itin, ctx)
        assert len(results) == 1
        assert not results[0].passed
        assert results[0].severity == Severity.VIOLATION
        assert "15 listed + 2 implicit airport-change surface sectors = 17" in results[0].message
        assert "same airport" in results[0].fix_suggestion

    def test_gaps_count_toward_their_continent(self):
        ctx = build_context(self._fifteen_with_two_gaps())
        # Asia: HND-TPE, TPE-HKG, HKG-SIN + NRT/HND gap = 4
        assert ctx.segments_per_continent[Continent.ASIA] == 4
        # N_America: SFO-JFK, LGA-ORD, ORD-DFW, DFW-MIA, MIA-MEX + JFK/LGA gap = 6
        assert ctx.segments_per_continent[Continent.N_AMERICA] == 6

    def test_asia_limit_exceeded_by_implicit_gaps(self):
        # 3 listed Asia segments + 2 airport changes = 5 > 4
        segs = [
            {"from": "CAI", "to": "NRT", "carrier": "QR"},
            {"from": "HND", "to": "TSA", "carrier": "JL"},
            {"from": "TPE", "to": "HKG", "carrier": "CX"},
            {"from": "HKG", "to": "SIN", "carrier": "CX"},
            {"from": "SIN", "to": "CAI", "carrier": "QR"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        assert ctx.segments_per_continent[Continent.ASIA] == 5
        results = PerContinentLimitRule().check(itin, ctx)
        asia = [r for r in results if r.message.startswith("Asia")]
        assert len(asia) == 1
        assert not asia[0].passed
        assert "Asia: 5 segments (incl. 2 implicit airport-change surface sectors)" in asia[0].message

        # The same routing flown NRT in/out and TPE in/out stays within the limit
        fixed = _make_itinerary([
            {"from": "CAI", "to": "NRT", "carrier": "QR"},
            {"from": "NRT", "to": "TPE", "carrier": "JL"},
            {"from": "TPE", "to": "HKG", "carrier": "CX"},
            {"from": "HKG", "to": "SIN", "carrier": "CX"},
            {"from": "SIN", "to": "CAI", "carrier": "QR"},
        ])
        fctx = build_context(fixed)
        assert fctx.segments_per_continent[Continent.ASIA] == 3
        assert all(r.passed for r in PerContinentLimitRule().check(fixed, fctx))

    def test_explicit_surface_counts_toward_continent(self):
        segs = [
            {"from": "CAI", "to": "NRT", "carrier": "QR"},
            {"from": "NRT", "to": "KIX", "type": "surface"},
            {"from": "KIX", "to": "HKG", "carrier": "CX"},
            {"from": "HKG", "to": "SIN", "carrier": "CX"},
            {"from": "SIN", "to": "BKK", "carrier": "QR"},
            {"from": "BKK", "to": "KUL", "carrier": "MH"},
            {"from": "KUL", "to": "CAI", "carrier": "QR"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        # NRT-KIX surface + KIX-HKG + HKG-SIN + SIN-BKK + BKK-KUL = 5 > 4
        assert ctx.segments_per_continent[Continent.ASIA] == 5
        results = PerContinentLimitRule().check(itin, ctx)
        asia = [r for r in results if r.message.startswith("Asia")]
        assert not asia[0].passed
        assert "implicit" not in asia[0].message

    def test_explicit_nrt_hnd_surface_not_double_counted(self):
        segs = [
            {"from": "CAI", "to": "NRT", "carrier": "QR"},
            {"from": "NRT", "to": "HND", "type": "surface"},
            {"from": "HND", "to": "SIN", "carrier": "JL"},
            {"from": "SIN", "to": "CAI", "carrier": "QR"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        assert ctx.same_city_pairs == []
        assert ctx.implicit_surface_count == 0
        # NRT-HND surface + HND-SIN = 2, not 3
        assert ctx.segments_per_continent[Continent.ASIA] == 2
        results = SegmentCountRule().check(itin, ctx)
        assert results[0].passed
        assert results[0].message == "4 segments (limit: 16)."

    def test_gap_counts_toward_minimum_3(self):
        # 2 listed + 1 airport change = 3 segments
        segs = [
            {"from": "CAI", "to": "NRT", "carrier": "QR"},
            {"from": "HND", "to": "CAI", "carrier": "JL"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = SegmentCountRule().check(itin, ctx)
        assert results[0].passed
        assert "2 listed + 1 implicit airport-change surface sector = 3" in results[0].message

    def test_origin_open_jaw_not_counted(self):
        # Out of LHR, back into LGW: origin/destination open jaw (§7/§18),
        # not a consecutive-segment gap.
        ticket = Ticket(type="DONE4", cabin="business", origin="LHR")
        segs = [
            Segment(**{"from": "LHR", "to": "JFK", "carrier": "BA"}),
            Segment(**{"from": "JFK", "to": "LAX", "carrier": "AA"}),
            Segment(**{"from": "LAX", "to": "LGW", "carrier": "BA"}),
        ]
        itin = Itinerary(ticket=ticket, segments=segs)
        ctx = build_context(itin)
        assert ctx.implicit_surface_count == 0
        results = SegmentCountRule().check(itin, ctx)
        assert results[0].message == "3 segments (limit: 16)."


class TestPerContinentLimit:
    def test_v3_passes(self, v3_itinerary):
        itin = Itinerary(**v3_itinerary)
        ctx = build_context(itin)
        results = PerContinentLimitRule().check(itin, ctx)
        violations = [r for r in results if not r.passed and r.severity == Severity.VIOLATION]
        assert len(violations) == 0

    def test_5_eu_me_segments_fails(self):
        # 5 segments all in EU/ME should fail (limit is 4)
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            {"from": "AMM", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "IST", "carrier": "QR"},
            {"from": "IST", "to": "MAD", "carrier": "IB"},
            {"from": "MAD", "to": "CAI", "carrier": "IB"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = PerContinentLimitRule().check(itin, ctx)
        eu_me_results = [r for r in results if "EU_ME" in r.message]
        assert any(not r.passed for r in eu_me_results)

    def test_na_allows_6(self):
        # 6 segments in NA should be fine (limit is 6)
        segs = [
            {"from": "JFK", "to": "LAX", "carrier": "AA"},
            {"from": "LAX", "to": "SFO", "carrier": "AA"},
            {"from": "SFO", "to": "DFW", "carrier": "AA"},
            {"from": "DFW", "to": "MIA", "carrier": "AA"},
            {"from": "MIA", "to": "MCO", "carrier": "AA"},
            {"from": "MCO", "to": "JFK", "carrier": "AA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = PerContinentLimitRule().check(itin, ctx)
        na_results = [r for r in results if "N_America" in r.message]
        assert all(r.passed for r in na_results)


class TestSegmentConnectivity:
    def test_connected_chain_passes(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            {"from": "AMM", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "CAI", "carrier": "QR"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = SegmentConnectivityRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert "All segments connected" in results[0].message

    def test_gap_detected(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            {"from": "DOH", "to": "CAI", "carrier": "QR"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = SegmentConnectivityRule().check(itin, ctx)
        assert any(not r.passed for r in results)
        assert any(r.severity == Severity.WARNING for r in results)

    def test_same_city_group_ok(self):
        # NRT and HND are both in the TYO same-city group
        segs = [
            {"from": "CAI", "to": "NRT", "carrier": "QR"},
            {"from": "HND", "to": "SIN", "carrier": "JL"},
            {"from": "SIN", "to": "CAI", "carrier": "QR"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = SegmentConnectivityRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert "All segments connected" in results[0].message

    def test_surface_sector_exempts_gap(self):
        # Gap before a surface sector should not be flagged
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ"},
            {"from": "DOH", "to": "NRT", "carrier": "QR", "type": "surface"},
            {"from": "NRT", "to": "CAI", "carrier": "JL"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = SegmentConnectivityRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_single_segment_passes(self):
        segs = [
            {"from": "CAI", "to": "AMM", "carrier": "RJ"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = SegmentConnectivityRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert "Too few segments" in results[0].message

    def test_v3_passes(self, v3_itinerary):
        itin = Itinerary(**v3_itinerary)
        ctx = build_context(itin)
        results = SegmentConnectivityRule().check(itin, ctx)
        assert all(r.passed for r in results)
