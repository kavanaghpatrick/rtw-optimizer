"""Tests for OriginCountryIntlLimitRule and OriginCountryReturnRule."""

from rtw.models import Itinerary, Ticket, Segment, Severity
from rtw.rules.country import OriginCountryIntlLimitRule, OriginCountryReturnRule
from rtw.validator import build_context


def _make_itinerary(segments_data, origin="SYD", ticket_type="DONE4"):
    ticket = Ticket(type=ticket_type, cabin="business", origin=origin)
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestOriginCountryIntlLimit:
    def test_au_one_dep_one_arr_passes(self):
        """AU origin: 1 intl departure + 1 intl arrival = PASS."""
        segs = [
            {"from": "SYD", "to": "NRT", "carrier": "QF"},  # intl departure from AU
            {"from": "NRT", "to": "LAX", "carrier": "JL"},
            {"from": "LAX", "to": "SYD", "carrier": "QF"},  # intl arrival into AU
        ]
        itin = _make_itinerary(segs, origin="SYD")
        ctx = build_context(itin)
        results = OriginCountryIntlLimitRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_au_two_intl_departures_violation(self):
        """AU origin: 2 intl departures = VIOLATION."""
        segs = [
            {"from": "SYD", "to": "NRT", "carrier": "QF"},  # 1st intl dep
            {"from": "NRT", "to": "SYD", "carrier": "QF"},  # intl arrival
            {"from": "SYD", "to": "LAX", "carrier": "QF"},  # 2nd intl dep
            {"from": "LAX", "to": "SYD", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs, origin="SYD")
        ctx = build_context(itin)
        results = OriginCountryIntlLimitRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1
        assert "departure" in violations[0].message.lower()

    def test_us_two_dep_one_transit_passes(self):
        """US origin: 2 intl departures but 1 is transit = PASS."""
        segs = [
            {"from": "JFK", "to": "LHR", "carrier": "BA", "type": "transit"},  # transit dep
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "NRT", "carrier": "JL"},  # 2nd intl dep
            {"from": "NRT", "to": "JFK", "carrier": "JL"},
        ]
        itin = _make_itinerary(segs, origin="JFK")
        ctx = build_context(itin)
        results = OriginCountryIntlLimitRule().check(itin, ctx)
        dep_violations = [r for r in results if r.severity == Severity.VIOLATION and "departure" in r.message.lower()]
        assert len(dep_violations) == 0

    def test_us_ca_not_international(self):
        """US<->CA movements are NOT international."""
        segs = [
            {"from": "JFK", "to": "YYZ", "carrier": "AA"},  # US->CA = exempt
            {"from": "YYZ", "to": "JFK", "carrier": "AA"},  # CA->US = exempt
            {"from": "JFK", "to": "LHR", "carrier": "BA"},  # 1 intl dep
            {"from": "LHR", "to": "JFK", "carrier": "BA"},  # 1 intl arrival
        ]
        itin = _make_itinerary(segs, origin="JFK")
        ctx = build_context(itin)
        results = OriginCountryIntlLimitRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_four_transfers_passes(self):
        """4 international transfers from one country = PASS (at limit)."""
        segs = [
            {"from": "LHR", "to": "CDG", "carrier": "BA"},
            {"from": "CDG", "to": "LHR", "carrier": "BA"},
            {"from": "LHR", "to": "FRA", "carrier": "BA"},
            {"from": "FRA", "to": "LHR", "carrier": "BA"},
            {"from": "LHR", "to": "MAD", "carrier": "BA"},
            {"from": "MAD", "to": "LHR", "carrier": "BA"},
            {"from": "LHR", "to": "FCO", "carrier": "BA"},
            {"from": "FCO", "to": "LHR", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs, origin="LHR")
        ctx = build_context(itin)
        results = OriginCountryIntlLimitRule().check(itin, ctx)
        transfer_violations = [r for r in results if r.severity == Severity.VIOLATION and "transfer" in r.message.lower()]
        assert len(transfer_violations) == 0

    def test_five_transfers_violation(self):
        """5 international transfers from one country = VIOLATION."""
        segs = [
            {"from": "LHR", "to": "CDG", "carrier": "BA"},
            {"from": "CDG", "to": "LHR", "carrier": "BA"},
            {"from": "LHR", "to": "FRA", "carrier": "BA"},
            {"from": "FRA", "to": "LHR", "carrier": "BA"},
            {"from": "LHR", "to": "MAD", "carrier": "BA"},
            {"from": "MAD", "to": "LHR", "carrier": "BA"},
            {"from": "LHR", "to": "FCO", "carrier": "BA"},
            {"from": "FCO", "to": "LHR", "carrier": "BA"},
            {"from": "LHR", "to": "AMS", "carrier": "BA"},
            {"from": "AMS", "to": "LHR", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs, origin="LHR")
        ctx = build_context(itin)
        results = OriginCountryIntlLimitRule().check(itin, ctx)
        transfer_violations = [r for r in results if r.severity == Severity.VIOLATION and "transfer" in r.message.lower()]
        assert len(transfer_violations) >= 1

    def test_segments_involved_populated(self):
        """segments_involved populated on violation."""
        segs = [
            {"from": "SYD", "to": "NRT", "carrier": "QF"},
            {"from": "NRT", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "SYD", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs, origin="SYD")
        ctx = build_context(itin)
        results = OriginCountryIntlLimitRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert any(r.segments_involved is not None and len(r.segments_involved) > 0 for r in violations)

    def test_surface_sectors_excluded(self):
        """Surface sectors not counted as international."""
        segs = [
            {"from": "SYD", "to": "NRT", "type": "surface"},  # surface, not counted
            {"from": "NRT", "to": "LAX", "carrier": "JL"},
            {"from": "LAX", "to": "SYD", "carrier": "QF"},  # only real intl dep from AU
        ]
        itin = _make_itinerary(segs, origin="SYD")
        ctx = build_context(itin)
        results = OriginCountryIntlLimitRule().check(itin, ctx)
        # Only 1 counted intl arrival (LAX->SYD), 0 counted departures
        dep_violations = [r for r in results if r.severity == Severity.VIOLATION and "departure" in r.message.lower()]
        assert len(dep_violations) == 0


class TestOriginCountryReturn:
    def test_uk_mid_journey_lhr_violation(self):
        """UK origin, mid-journey arrival at LHR = VIOLATION."""
        segs = [
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "LHR", "carrier": "BA", "type": "stopover"},  # mid-journey return!
            {"from": "LHR", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "LHR", "carrier": "QF"},  # final return (exempt)
        ]
        itin = _make_itinerary(segs, origin="LHR")
        ctx = build_context(itin)
        results = OriginCountryReturnRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1

    def test_uk_no_mid_journey_passes(self):
        """UK origin, no mid-journey return = PASS."""
        segs = [
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "LHR", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs, origin="LHR")
        ctx = build_context(itin)
        results = OriginCountryReturnRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_us_one_transit_passes(self):
        """US origin, 1 mid-journey transit = PASS (US exception)."""
        segs = [
            {"from": "JFK", "to": "LHR", "carrier": "BA"},
            {"from": "LHR", "to": "JFK", "carrier": "BA", "type": "transit"},  # transit, not stopover
            {"from": "JFK", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "JFK", "carrier": "JL"},  # final return
        ]
        itin = _make_itinerary(segs, origin="JFK")
        ctx = build_context(itin)
        results = OriginCountryReturnRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_us_stopover_violation(self):
        """US origin, 1 mid-journey stopover (not transit) = VIOLATION."""
        segs = [
            {"from": "JFK", "to": "LHR", "carrier": "BA"},
            {"from": "LHR", "to": "JFK", "carrier": "BA", "type": "stopover"},  # stopover!
            {"from": "JFK", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "JFK", "carrier": "JL"},
        ]
        itin = _make_itinerary(segs, origin="JFK")
        ctx = build_context(itin)
        results = OriginCountryReturnRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1

    def test_us_two_transits_violation(self):
        """US origin, 2 mid-journey transits = VIOLATION (only 1 allowed)."""
        segs = [
            {"from": "JFK", "to": "LHR", "carrier": "BA"},
            {"from": "LHR", "to": "JFK", "carrier": "BA", "type": "transit"},
            {"from": "JFK", "to": "NRT", "carrier": "JL"},
            {"from": "NRT", "to": "LAX", "carrier": "JL", "type": "transit"},  # LAX is also US
            {"from": "LAX", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "JFK", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs, origin="JFK")
        ctx = build_context(itin)
        results = OriginCountryReturnRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1

    def test_final_return_not_flagged(self):
        """Final return to origin country at end of journey is exempt."""
        segs = [
            {"from": "SYD", "to": "NRT", "carrier": "QF"},
            {"from": "NRT", "to": "LAX", "carrier": "JL"},
            {"from": "LAX", "to": "MEL", "carrier": "QF"},  # return to AU at end
            {"from": "MEL", "to": "SYD", "carrier": "QF"},  # still AU
        ]
        itin = _make_itinerary(segs, origin="SYD")
        ctx = build_context(itin)
        results = OriginCountryReturnRule().check(itin, ctx)
        assert all(r.passed for r in results)

    def test_country_not_city(self):
        """Country-level check: LHR->MAN mid-journey is still UK return."""
        segs = [
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "MAN", "carrier": "AA", "type": "stopover"},  # MAN is UK!
            {"from": "MAN", "to": "NRT", "carrier": "BA"},
            {"from": "NRT", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "LHR", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs, origin="LHR")
        ctx = build_context(itin)
        results = OriginCountryReturnRule().check(itin, ctx)
        violations = [r for r in results if r.severity == Severity.VIOLATION]
        assert len(violations) >= 1

    def test_no_origin_country_graceful(self):
        """Unknown origin airport doesn't crash."""
        segs = [
            {"from": "ZZZ", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "ZZZ", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs, origin="ZZZ")
        ctx = build_context(itin)
        results = OriginCountryReturnRule().check(itin, ctx)
        assert len(results) > 0
        assert all(r.passed for r in results)
