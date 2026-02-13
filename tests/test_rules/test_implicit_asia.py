"""Tests for ImplicitAsiaRule and implicit Asia detection in build_context."""

from rtw.models import Itinerary, Ticket, Segment, Severity, Continent
from rtw.rules.geography import ImplicitAsiaRule
from rtw.rules.validity import ContinentCountRule
from rtw.validator import build_context


def _make_itinerary(segments_data, origin="LHR", ticket_type="DONE4"):
    ticket = Ticket(type=ticket_type, cabin="business", origin=origin)
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)


class TestImplicitAsia:
    def test_doh_syd_triggers_implicit_asia(self):
        """DOH-SYD = EU_ME->SWP, triggers implicit Asia."""
        segs = [
            {"from": "LHR", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "SYD", "carrier": "QR"},  # EU_ME -> SWP
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "LHR", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = ImplicitAsiaRule().check(itin, ctx)
        info_results = [r for r in results if r.severity == Severity.INFO]
        assert len(info_results) >= 1
        assert "DOH-SYD" in info_results[0].message
        assert "Asia" in info_results[0].message

    def test_lhr_per_triggers_implicit_asia(self):
        """LHR-PER = EU_ME->SWP, triggers implicit Asia."""
        segs = [
            {"from": "LHR", "to": "PER", "carrier": "QF"},  # EU_ME -> SWP
            {"from": "PER", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "LHR", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = ImplicitAsiaRule().check(itin, ctx)
        info_results = [r for r in results if r.severity == Severity.INFO]
        assert len(info_results) >= 1
        assert "LHR-PER" in info_results[0].message

    def test_doh_nrt_no_trigger(self):
        """DOH-NRT = EU_ME->Asia, NOT EU_ME->SWP. No implicit Asia."""
        segs = [
            {"from": "LHR", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "NRT", "carrier": "QR"},  # EU_ME -> Asia (not SWP!)
            {"from": "NRT", "to": "LAX", "carrier": "JL"},
            {"from": "LAX", "to": "LHR", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = ImplicitAsiaRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("No implicit" in r.message for r in results)

    def test_jnb_syd_no_trigger(self):
        """JNB-SYD = Africa->SWP, NOT EU_ME->SWP. No implicit Asia."""
        segs = [
            {"from": "LHR", "to": "JNB", "carrier": "BA"},
            {"from": "JNB", "to": "SYD", "carrier": "QF"},  # Africa -> SWP (not EU_ME!)
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "LHR", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = ImplicitAsiaRule().check(itin, ctx)
        assert all(r.passed for r in results)
        assert any("No implicit" in r.message for r in results)

    def test_continent_count_includes_implicit(self):
        """build_context adds Asia to continents_visited for DOH-SYD."""
        segs = [
            {"from": "LHR", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "SYD", "carrier": "QR"},  # triggers implicit Asia
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "LHR", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        assert Continent.ASIA in ctx.continents_visited
        assert Continent.ASIA in ctx.implicit_continents

    def test_info_message_explains_asia(self):
        """INFO message explains the Asia counting."""
        segs = [
            {"from": "LHR", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "SYD", "carrier": "QR"},
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "LHR", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = ImplicitAsiaRule().check(itin, ctx)
        info = [r for r in results if r.severity == Severity.INFO]
        assert len(info) == 1
        assert "pricing" in info[0].message.lower()

    def test_done3_with_doh_syd_warns(self):
        """DONE3 + DOH-SYD = ContinentCountRule WARNING (4 continents on DONE3)."""
        segs = [
            {"from": "LHR", "to": "DOH", "carrier": "QR"},
            {"from": "DOH", "to": "SYD", "carrier": "QR"},  # implicit Asia -> 4 continents
            {"from": "SYD", "to": "LAX", "carrier": "QF"},
            {"from": "LAX", "to": "LHR", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs, ticket_type="DONE3")
        ctx = build_context(itin)
        # Should have 4 continents: EU_ME, SWP, N_America, Asia (implicit)
        assert len(ctx.continents_visited) >= 4
        # ContinentCountRule should warn about mismatch
        results = ContinentCountRule().check(itin, ctx)
        # DONE3 expects 3 but has 4 = WARNING
        warnings = [r for r in results if not r.passed]
        assert len(warnings) >= 1

    def test_reverse_direction_syd_doh(self):
        """SYD-DOH = SWP->EU_ME (reverse direction), still triggers implicit Asia."""
        segs = [
            {"from": "SYD", "to": "DOH", "carrier": "QR"},  # SWP -> EU_ME
            {"from": "DOH", "to": "LHR", "carrier": "BA"},
            {"from": "LHR", "to": "JFK", "carrier": "BA"},
            {"from": "JFK", "to": "SYD", "carrier": "QF"},
        ]
        itin = _make_itinerary(segs, origin="SYD")
        ctx = build_context(itin)
        results = ImplicitAsiaRule().check(itin, ctx)
        info_results = [r for r in results if r.severity == Severity.INFO]
        assert len(info_results) >= 1

    def test_multiple_eu_me_swp_segments(self):
        """Multiple EU_ME<->SWP segments all listed in message."""
        segs = [
            {"from": "LHR", "to": "SYD", "carrier": "QF"},  # EU_ME -> SWP
            {"from": "SYD", "to": "DOH", "carrier": "QR"},  # SWP -> EU_ME
            {"from": "DOH", "to": "JFK", "carrier": "QR"},
            {"from": "JFK", "to": "LHR", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        results = ImplicitAsiaRule().check(itin, ctx)
        info = [r for r in results if r.severity == Severity.INFO]
        assert len(info) >= 1
        # Should mention both flights
        assert "2" in info[0].message

    def test_already_visiting_asia_no_double_count(self):
        """Already visiting Asia via NRT -- implicit Asia doesn't double count."""
        segs = [
            {"from": "LHR", "to": "NRT", "carrier": "JL"},  # Already in Asia!
            {"from": "NRT", "to": "SYD", "carrier": "QF"},
            {"from": "SYD", "to": "DOH", "carrier": "QR"},  # SWP -> EU_ME (triggers implicit)
            {"from": "DOH", "to": "JFK", "carrier": "QR"},
            {"from": "JFK", "to": "LHR", "carrier": "BA"},
        ]
        itin = _make_itinerary(segs)
        ctx = build_context(itin)
        # Asia should appear only once in continents_visited
        asia_count = ctx.continents_visited.count(Continent.ASIA)
        assert asia_count == 1
