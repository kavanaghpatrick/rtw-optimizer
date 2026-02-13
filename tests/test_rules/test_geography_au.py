"""Tests for TranscontinentalAURule."""

from rtw.models import Itinerary, Ticket, Segment, Severity
from rtw.rules.geography import TranscontinentalAURule
from rtw.validator import build_context


def _make_itinerary(segments_data, origin="SYD", ticket_type="DONE4"):
    ticket = Ticket(type=ticket_type, cabin="business", origin=origin)
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestTranscontinentalAU:
    def test_single_syd_per_passes(self):
        """Single SYD-PER = PASS with INFO severity."""
        segs = [
            {"from": "SYD", "to": "PER", "carrier": "QF"},
            {"from": "PER", "to": "SIN", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TranscontinentalAURule().check(itin, ctx)
        assert all(r.passed for r in results)
        info_results = [r for r in results if r.severity == Severity.INFO]
        assert len(info_results) == 1
        assert "Perth" in info_results[0].message or "east coast" in info_results[0].message

    def test_syd_per_mel_per_violation(self):
        """SYD-PER + MEL-PER = VIOLATION (PER-MEL also counts as reverse)."""
        segs = [
            {"from": "SYD", "to": "PER", "carrier": "QF"},
            {"from": "PER", "to": "MEL", "carrier": "QF"},
            {"from": "MEL", "to": "PER", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TranscontinentalAURule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1
        assert violations[0].segments_involved is not None
        assert len(violations[0].segments_involved) == 3

    def test_cbr_drw_syd_drw_violation(self):
        """CBR-DRW + SYD-DRW = VIOLATION (Darwin group)."""
        segs = [
            {"from": "CBR", "to": "DRW", "carrier": "QF"},
            {"from": "DRW", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "DRW", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs, origin="CBR")
        ctx = build_context(itin)
        results = TranscontinentalAURule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1
        assert "Darwin" in violations[0].message

    def test_different_pairs_both_pass(self):
        """SYD-PER (group 1) + MEL-DRW (group 2) = both pass (1 each)."""
        segs = [
            {"from": "SYD", "to": "PER", "carrier": "QF"},
            {"from": "PER", "to": "SIN", "carrier": "QF"},
            {"from": "SIN", "to": "MEL", "carrier": "QF"},
            {"from": "MEL", "to": "DRW", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TranscontinentalAURule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_reverse_direction_counted(self):
        """PER-SYD counts as transcontinental (bidirectional)."""
        segs = [
            {"from": "PER", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "PER", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs, origin="PER")
        # PER origin without JNB = NOT exempt
        ctx = build_context(itin)
        results = TranscontinentalAURule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1

    def test_per_origin_exempt(self):
        """PER origin with JNB connection = exempt."""
        segs = [
            {"from": "PER", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "PER", "carrier": "QF"},
            {"from": "PER", "to": "JNB", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs, origin="PER")
        ctx = build_context(itin)
        results = TranscontinentalAURule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_nz_origin_exempt(self):
        """NZ origin (AKL) with JNB connection = exempt."""
        segs = [
            {"from": "AKL", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "PER", "carrier": "QF"},
            {"from": "PER", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "JNB", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs, origin="AKL")
        ctx = build_context(itin)
        results = TranscontinentalAURule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_surface_sector_excluded(self):
        """Surface SYD-PER not counted; only flown MEL-PER = 1 counted (PASS)."""
        segs = [
            {"from": "SYD", "to": "PER", "type": "surface"},
            {"from": "PER", "to": "SIN", "carrier": "QF"},
            {"from": "SIN", "to": "MEL", "carrier": "QF"},
            {"from": "MEL", "to": "PER", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = TranscontinentalAURule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_bme_kta_group(self):
        """BNE-BME + MEL-KTA = VIOLATION (Broome/Karratha group)."""
        segs = [
            {"from": "BNE", "to": "BME", "carrier": "QF"},
            {"from": "BME", "to": "MEL", "carrier": "QF"},
            {"from": "MEL", "to": "KTA", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs, origin="BNE")
        ctx = build_context(itin)
        results = TranscontinentalAURule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1
        assert "Broome" in violations[0].message or "Karratha" in violations[0].message

    def test_no_au_segments_passes(self):
        """Itinerary with no AU segments = PASS."""
        segs = [
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "NRT", "carrier": "JL"},
        ]
        itin = _make_itinerary(segs, origin="LHR")
        ctx = build_context(itin)
        results = TranscontinentalAURule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("No AU transcontinental" in r.message for r in results)
