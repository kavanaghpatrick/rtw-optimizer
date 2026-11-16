"""Tests for availability verification orchestrator."""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from rtw.models import CabinClass
from rtw.scraper.expertflyer import SessionExpiredError
from rtw.verify.models import (
    DClassResult,
    DClassStatus,
    FlightAvailability,
    SegmentVerification,
    VerifyOption,
)
from rtw.verify.verifier import DClassVerifier


def _make_segment(origin, dest, carrier="CX", stype="FLOWN", date=None):
    return SegmentVerification(
        index=0,
        segment_type=stype,
        origin=origin,
        destination=dest,
        carrier=carrier,
        target_date=date or datetime.date(2026, 3, 10),
    )


def _make_dclass(status, seats, carrier="CX", origin="LHR", dest="HKG"):
    flights = []
    if status == DClassStatus.AVAILABLE and seats > 0:
        flights = [FlightAvailability(
            carrier=carrier, origin=origin, destination=dest,
            seats=seats, stops=0,
        )]
    return DClassResult(
        status=status,
        seats=seats,
        carrier=carrier,
        origin=origin,
        destination=dest,
        target_date=datetime.date(2026, 3, 10),
        flights=flights,
    )


class TestDClassVerifier:
    def _make_verifier(self, scraper_results=None, cache_results=None):
        """Create a verifier with mocked scraper and cache."""
        scraper = MagicMock()
        if scraper_results is not None:
            scraper.check_availability.side_effect = scraper_results
        cache = MagicMock()
        cache.get.return_value = cache_results
        return DClassVerifier(scraper=scraper, cache=cache), scraper, cache

    def test_all_available(self):
        results = [
            _make_dclass(DClassStatus.AVAILABLE, 9, origin="SYD", dest="HKG"),
            _make_dclass(DClassStatus.AVAILABLE, 5, origin="HKG", dest="LHR"),
        ]
        verifier, scraper, cache = self._make_verifier(scraper_results=results)

        option = VerifyOption(
            option_id=1,
            segments=[
                _make_segment("SYD", "HKG"),
                _make_segment("HKG", "LHR"),
            ],
        )
        result = verifier.verify_option(option)
        assert result.confirmed == 2
        assert result.total_flown == 2
        assert result.fully_bookable is True
        assert scraper.check_availability.call_count == 2

    def test_surface_skipped(self):
        results = [
            _make_dclass(DClassStatus.AVAILABLE, 9),
        ]
        verifier, scraper, cache = self._make_verifier(scraper_results=results)

        option = VerifyOption(
            option_id=1,
            segments=[
                _make_segment("SYD", "HKG"),
                _make_segment("HKG", "LHR", stype="SURFACE"),
            ],
        )
        result = verifier.verify_option(option)
        assert result.confirmed == 1
        assert result.total_flown == 1
        assert result.fully_bookable is True
        # Scraper only called once (surface skipped)
        assert scraper.check_availability.call_count == 1

    def test_partial_failure(self):
        results = [
            _make_dclass(DClassStatus.AVAILABLE, 9),
            _make_dclass(DClassStatus.NOT_AVAILABLE, 0),
        ]
        verifier, scraper, cache = self._make_verifier(scraper_results=results)

        option = VerifyOption(
            option_id=1,
            segments=[
                _make_segment("SYD", "HKG"),
                _make_segment("HKG", "LHR"),
            ],
        )
        result = verifier.verify_option(option)
        assert result.confirmed == 1
        assert result.total_flown == 2
        assert result.fully_bookable is False

    def test_session_expired_marks_remaining_unknown(self):
        verifier, scraper, cache = self._make_verifier()
        scraper.check_availability.side_effect = [
            _make_dclass(DClassStatus.AVAILABLE, 9),
            SessionExpiredError("expired"),
        ]

        option = VerifyOption(
            option_id=1,
            segments=[
                _make_segment("SYD", "HKG"),
                _make_segment("HKG", "LHR"),
                _make_segment("LHR", "JFK"),
            ],
        )
        result = verifier.verify_option(option)
        statuses = [s.dclass.status for s in result.segments if s.dclass]
        assert statuses[0] == DClassStatus.AVAILABLE
        assert statuses[1] == DClassStatus.UNKNOWN
        assert statuses[2] == DClassStatus.UNKNOWN

    def test_scrape_error_marks_error(self):
        verifier, scraper, cache = self._make_verifier()
        scraper.check_availability.side_effect = [
            _make_dclass(DClassStatus.AVAILABLE, 9),
            Exception("timeout"),
            _make_dclass(DClassStatus.AVAILABLE, 5),
        ]

        option = VerifyOption(
            option_id=1,
            segments=[
                _make_segment("SYD", "HKG"),
                _make_segment("HKG", "LHR"),
                _make_segment("LHR", "JFK"),
            ],
        )
        result = verifier.verify_option(option)
        statuses = [s.dclass.status for s in result.segments if s.dclass]
        assert statuses[0] == DClassStatus.AVAILABLE
        assert statuses[1] == DClassStatus.ERROR
        assert statuses[2] == DClassStatus.AVAILABLE

    def test_progress_callback(self):
        results = [
            _make_dclass(DClassStatus.AVAILABLE, 9),
            _make_dclass(DClassStatus.AVAILABLE, 5),
        ]
        verifier, scraper, cache = self._make_verifier(scraper_results=results)

        progress_calls = []

        def cb(current, total, seg):
            progress_calls.append((current, total))

        option = VerifyOption(
            option_id=1,
            segments=[
                _make_segment("SYD", "HKG"),
                _make_segment("HKG", "LHR"),
            ],
        )
        verifier.verify_option(option, progress_cb=cb)
        assert len(progress_calls) == 2
        assert progress_calls[0] == (1, 2)
        assert progress_calls[1] == (2, 2)

    def test_batch_verify(self):
        results = [
            _make_dclass(DClassStatus.AVAILABLE, 9),
            _make_dclass(DClassStatus.AVAILABLE, 5),
        ]
        verifier, scraper, cache = self._make_verifier(scraper_results=results)

        options = [
            VerifyOption(option_id=1, segments=[_make_segment("SYD", "HKG")]),
            VerifyOption(option_id=2, segments=[_make_segment("HKG", "LHR")]),
        ]
        results = verifier.verify_batch(options)
        assert len(results) == 2
        assert results[0].option_id == 1
        assert results[1].option_id == 2

    def test_empty_option(self):
        verifier, scraper, cache = self._make_verifier()
        option = VerifyOption(option_id=1, segments=[])
        result = verifier.verify_option(option)
        assert result.total_flown == 0
        assert result.fully_bookable is True
        assert scraper.check_availability.call_count == 0

    def test_aa_segment_uses_d_class(self):
        """AA segments are queried with primary booking_class='D' (H is fallback)."""
        results = [
            _make_dclass(DClassStatus.AVAILABLE, 9, carrier="AA", origin="JFK", dest="LAX"),
        ]
        verifier, scraper, cache = self._make_verifier(scraper_results=results)

        option = VerifyOption(
            option_id=1,
            segments=[_make_segment("JFK", "LAX", carrier="AA")],
        )
        verifier.verify_option(option)
        call_kwargs = scraper.check_availability.call_args[1]
        assert call_kwargs["booking_class"] == "D"

    def test_cx_segment_uses_d_class(self):
        """Non-AA carriers should use D class."""
        results = [
            _make_dclass(DClassStatus.AVAILABLE, 9),
        ]
        verifier, scraper, cache = self._make_verifier(scraper_results=results)

        option = VerifyOption(
            option_id=1,
            segments=[_make_segment("SYD", "HKG", carrier="CX")],
        )
        verifier.verify_option(option)
        call_kwargs = scraper.check_availability.call_args[1]
        assert call_kwargs["booking_class"] == "D"

    def test_mixed_carriers_use_correct_classes(self):
        """All carriers book D as primary (AA included) when available."""
        results = [
            _make_dclass(DClassStatus.AVAILABLE, 9, carrier="AA", origin="JFK", dest="LHR"),
            _make_dclass(DClassStatus.AVAILABLE, 5, carrier="CX", origin="LHR", dest="HKG"),
            _make_dclass(DClassStatus.AVAILABLE, 7, carrier="BA", origin="HKG", dest="SYD"),
        ]
        verifier, scraper, cache = self._make_verifier(scraper_results=results)

        option = VerifyOption(
            option_id=1,
            segments=[
                _make_segment("JFK", "LHR", carrier="AA"),
                _make_segment("LHR", "HKG", carrier="CX"),
                _make_segment("HKG", "SYD", carrier="BA"),
            ],
        )
        verifier.verify_option(option)
        calls = scraper.check_availability.call_args_list
        assert calls[0][1]["booking_class"] == "D"  # AA (primary D)
        assert calls[1][1]["booking_class"] == "D"  # CX
        assert calls[2][1]["booking_class"] == "D"  # BA

    def test_booking_class_override_forces_all(self):
        """Explicit booking_class override forces all segments to that class."""
        results = [
            _make_dclass(DClassStatus.AVAILABLE, 9, carrier="AA", origin="JFK", dest="LHR"),
            _make_dclass(DClassStatus.AVAILABLE, 5, carrier="CX", origin="LHR", dest="HKG"),
        ]
        scraper = MagicMock()
        scraper.check_availability.side_effect = results
        cache = MagicMock()
        cache.get.return_value = None
        verifier = DClassVerifier(scraper=scraper, cache=cache, booking_class="D")

        option = VerifyOption(
            option_id=1,
            segments=[
                _make_segment("JFK", "LHR", carrier="AA"),
                _make_segment("LHR", "HKG", carrier="CX"),
            ],
        )
        verifier.verify_option(option)
        calls = scraper.check_availability.call_args_list
        assert calls[0][1]["booking_class"] == "D"  # Override: AA forced to D
        assert calls[1][1]["booking_class"] == "D"  # CX stays D

    def test_cache_key_includes_correct_booking_class(self):
        """Primary cache key contains D; explicit fallback key contains H/B."""
        verifier, scraper, cache = self._make_verifier()

        aa_seg = _make_segment("JFK", "LHR", carrier="AA")
        cx_seg = _make_segment("LHR", "HKG", carrier="CX")

        # Primary keys both use D now
        assert verifier._cache_key(aa_seg).endswith("_D")
        assert verifier._cache_key(cx_seg).endswith("_D")

        # Fallback keys cache independently under their own class
        assert verifier._cache_key(aa_seg, "H").endswith("_H")
        assert verifier._cache_key(cx_seg, "B").endswith("_B")

    def test_dclass_result_has_booking_class_set(self):
        """DClassResult returned for AA should have primary booking_class='D'."""
        results = [
            _make_dclass(DClassStatus.AVAILABLE, 9, carrier="AA", origin="JFK", dest="LHR"),
        ]
        verifier, scraper, cache = self._make_verifier(scraper_results=results)

        option = VerifyOption(
            option_id=1,
            segments=[_make_segment("JFK", "LHR", carrier="AA")],
        )
        result = verifier.verify_option(option)
        assert result.segments[0].dclass.booking_class == "D"

    def test_dateless_segment_marked_unknown_not_crash(self):
        """A flown segment with no date is marked UNKNOWN, never crashes/scrapes."""
        scraper = MagicMock()  # must not be called
        cache = MagicMock()
        cache.get.return_value = None
        verifier = DClassVerifier(scraper=scraper, cache=cache)

        dateless = SegmentVerification(
            index=0, segment_type="FLOWN", origin="JFK",
            destination="LAX", carrier="AA", target_date=None,
        )
        option = VerifyOption(option_id=1, segments=[dateless])

        result = verifier.verify_option(option)  # must not raise
        assert scraper.check_availability.call_count == 0
        seg = result.segments[0]
        assert seg.dclass.status == DClassStatus.UNKNOWN
        assert "date" in (seg.dclass.error_message or "").lower()
        assert seg.fallback is None


class TestFallbackScan:
    """Fallback-class re-scan when the primary class (D) is sold out."""

    def _verifier(self, results, **kwargs):
        scraper = MagicMock()
        scraper.check_availability.side_effect = results
        cache = MagicMock()
        cache.get.return_value = None
        return DClassVerifier(scraper=scraper, cache=cache, **kwargs), scraper

    def test_fallback_scanned_when_primary_d0(self):
        """AA D0 triggers a second scan in the fallback class H."""
        results = [
            _make_dclass(DClassStatus.NOT_AVAILABLE, 0, carrier="AA", origin="JFK", dest="LAX"),
            _make_dclass(DClassStatus.AVAILABLE, 4, carrier="AA", origin="JFK", dest="LAX"),
        ]
        verifier, scraper = self._verifier(results)
        option = VerifyOption(
            option_id=1, segments=[_make_segment("JFK", "LAX", carrier="AA")]
        )
        result = verifier.verify_option(option)

        assert scraper.check_availability.call_count == 2
        calls = scraper.check_availability.call_args_list
        assert calls[0][1]["booking_class"] == "D"
        assert calls[1][1]["booking_class"] == "H"
        seg = result.segments[0]
        assert seg.dclass.status == DClassStatus.NOT_AVAILABLE
        assert seg.fallback is not None
        assert seg.fallback.status == DClassStatus.AVAILABLE
        assert seg.fallback.booking_class == "H"
        assert result.fallback_bookable == 1

    def test_non_aa_fallback_uses_b(self):
        """CX D0 triggers a fallback scan in B."""
        results = [
            _make_dclass(DClassStatus.NOT_AVAILABLE, 0, carrier="CX", origin="SYD", dest="HKG"),
            _make_dclass(DClassStatus.AVAILABLE, 2, carrier="CX", origin="SYD", dest="HKG"),
        ]
        verifier, scraper = self._verifier(results)
        option = VerifyOption(
            option_id=1, segments=[_make_segment("SYD", "HKG", carrier="CX")]
        )
        result = verifier.verify_option(option)
        assert scraper.check_availability.call_count == 2
        assert scraper.check_availability.call_args_list[1][1]["booking_class"] == "B"
        assert result.segments[0].fallback.booking_class == "B"

    def test_first_on_ib_scans_d_then_y(self):
        """AONE on IB books D (Rule 3015 §5(b)), and First falls back to Y."""
        results = [
            _make_dclass(DClassStatus.NOT_AVAILABLE, 0, carrier="IB", origin="MAD", dest="JFK"),
            _make_dclass(DClassStatus.AVAILABLE, 3, carrier="IB", origin="MAD", dest="JFK"),
        ]
        verifier, scraper = self._verifier(results, cabin=CabinClass.FIRST)
        option = VerifyOption(
            option_id=1, segments=[_make_segment("MAD", "JFK", carrier="IB")]
        )
        result = verifier.verify_option(option)
        calls = scraper.check_availability.call_args_list
        assert [c[1]["booking_class"] for c in calls] == ["D", "Y"]
        assert result.segments[0].fallback.booking_class == "Y"

    def test_first_on_ay_domestic_scans_y_without_fallback(self):
        """AY domestic First books Y, so a Y0 has no further fallback to scan."""
        results = [
            _make_dclass(DClassStatus.NOT_AVAILABLE, 0, carrier="AY", origin="HEL", dest="OUL"),
        ]
        verifier, scraper = self._verifier(results, cabin=CabinClass.FIRST)
        option = VerifyOption(
            option_id=1, segments=[_make_segment("HEL", "OUL", carrier="AY")]
        )
        result = verifier.verify_option(option)
        assert scraper.check_availability.call_count == 1
        assert scraper.check_availability.call_args_list[0][1]["booking_class"] == "Y"
        assert result.segments[0].fallback is None

    def test_no_fallback_when_primary_available(self):
        """No second scan when the primary class already has seats."""
        results = [
            _make_dclass(DClassStatus.AVAILABLE, 9, carrier="AA", origin="JFK", dest="LAX"),
        ]
        verifier, scraper = self._verifier(results)
        option = VerifyOption(
            option_id=1, segments=[_make_segment("JFK", "LAX", carrier="AA")]
        )
        result = verifier.verify_option(option)
        assert scraper.check_availability.call_count == 1
        assert result.segments[0].fallback is None

    def test_no_fallback_when_disabled(self):
        """enable_fallback=False suppresses the fallback scan on D0."""
        results = [
            _make_dclass(DClassStatus.NOT_AVAILABLE, 0, carrier="AA", origin="JFK", dest="LAX"),
        ]
        verifier, scraper = self._verifier(results, enable_fallback=False)
        option = VerifyOption(
            option_id=1, segments=[_make_segment("JFK", "LAX", carrier="AA")]
        )
        result = verifier.verify_option(option)
        assert scraper.check_availability.call_count == 1
        assert result.segments[0].fallback is None

    def test_no_fallback_with_explicit_override(self):
        """An explicit booking_class override disables fallback scanning."""
        results = [
            _make_dclass(DClassStatus.NOT_AVAILABLE, 0, carrier="AA", origin="JFK", dest="LAX"),
        ]
        verifier, scraper = self._verifier(results, booking_class="D")
        option = VerifyOption(
            option_id=1, segments=[_make_segment("JFK", "LAX", carrier="AA")]
        )
        result = verifier.verify_option(option)
        assert scraper.check_availability.call_count == 1
        assert result.segments[0].fallback is None


# ---------------------------------------------------------------------------
# Cache must never turn a failed scrape into a sold-out D0
# ---------------------------------------------------------------------------


def _error_result(booking_class="D", carrier="CX", origin="LHR", dest="HKG"):
    return DClassResult(
        status=DClassStatus.ERROR,
        seats=0,
        carrier=carrier,
        origin=origin,
        destination=dest,
        target_date=datetime.date(2026, 3, 10),
        booking_class=booking_class,
        error_message="Results table not found for LHR→HKG",
    )


class TestCacheSafety:
    """Uses a real on-disk ScrapeCache; only the EF network call is stubbed."""

    def _verifier(self, tmp_path, results):
        from rtw.scraper.cache import ScrapeCache

        scraper = MagicMock()
        scraper.check_availability.side_effect = results
        cache = ScrapeCache(cache_dir=tmp_path)
        return DClassVerifier(scraper=scraper, cache=cache), scraper, cache

    def _option(self):
        return VerifyOption(option_id=1, segments=[_make_segment("LHR", "HKG")])

    def test_error_is_not_cached_and_not_replayed_as_d0(self, tmp_path):
        verifier, scraper, _ = self._verifier(
            tmp_path, [_error_result(), _error_result()]
        )
        first = verifier.verify_option(self._option())
        second = verifier.verify_option(self._option())

        assert list(tmp_path.iterdir()) == []  # nothing written
        assert scraper.check_availability.call_count == 2  # re-scraped
        for run in (first, second):
            seg = run.segments[0]
            assert seg.dclass.status == DClassStatus.ERROR
            assert seg.dclass.display_code == "D!"
            assert seg.dclass.from_cache is False
            assert seg.fallback is None  # no B scan off a failed D scrape

    def test_stale_cached_error_is_ignored(self, tmp_path):
        """An ERROR entry left by an older version triggers a fresh scrape."""
        fresh = _make_dclass(DClassStatus.AVAILABLE, 7)
        verifier, scraper, cache = self._verifier(tmp_path, [fresh])
        seg = _make_segment("LHR", "HKG")
        cache.set(verifier._cache_key(seg, "D"), _error_result().model_dump(mode="json"))

        result = verifier.verify_option(self._option())
        assert scraper.check_availability.call_count == 1
        assert result.segments[0].dclass.status == DClassStatus.AVAILABLE
        assert result.segments[0].dclass.from_cache is False

    def test_definitive_result_cached_with_status_kept(self, tmp_path):
        """A connection-only NOT_AVAILABLE with seats>0 stays NOT_AVAILABLE."""
        conn_only = DClassResult(
            status=DClassStatus.NOT_AVAILABLE,
            seats=9,
            carrier="CX",
            origin="LHR",
            destination="HKG",
            target_date=datetime.date(2026, 3, 10),
            flights=[
                FlightAvailability(origin="LHR", destination="HKG", seats=0),
                FlightAvailability(origin="LHR", destination="BRU", seats=9),
                FlightAvailability(origin="BRU", destination="HKG", seats=9),
            ],
        )
        fb = _make_dclass(DClassStatus.NOT_AVAILABLE, 0)
        verifier, scraper, _ = self._verifier(tmp_path, [conn_only, fb])
        verifier.verify_option(self._option())
        again = verifier.verify_option(self._option())

        assert scraper.check_availability.call_count == 2  # D + B, then cache
        seg = again.segments[0]
        assert seg.dclass.from_cache is True
        assert seg.dclass.status == DClassStatus.NOT_AVAILABLE
        assert seg.dclass.seats == 9

    def test_entry_without_status_derives_from_seats(self, tmp_path):
        verifier, scraper, cache = self._verifier(tmp_path, [])
        seg = _make_segment("LHR", "HKG")
        data = _make_dclass(DClassStatus.AVAILABLE, 4).model_dump(mode="json")
        del data["status"]
        cache.set(verifier._cache_key(seg, "D"), data)

        cached = verifier._check_cache(seg, "D")
        assert cached is not None
        assert cached.status == DClassStatus.AVAILABLE
        assert cached.from_cache is True

    def test_cache_ttl_is_short(self):
        from rtw.verify import verifier as verifier_mod

        assert verifier_mod._CACHE_TTL_HOURS <= 6


# ---------------------------------------------------------------------------
# Connection-leg seats must not suppress the fallback scan
# ---------------------------------------------------------------------------


def _conn_result(status, nonstop_seats, legs, carrier="CX", origin="SIN", dest="HKG"):
    flights = [FlightAvailability(
        carrier=carrier, origin=origin, destination=dest, seats=nonstop_seats,
    )]
    flights += [
        FlightAvailability(carrier=carrier, origin=o, destination=d, seats=s)
        for o, d, s in legs
    ]
    return DClassResult(
        status=status,
        seats=max(f.seats for f in flights),
        carrier=carrier,
        origin=origin,
        destination=dest,
        target_date=datetime.date(2026, 3, 10),
        flights=flights,
    )


class TestConnectionLegsAndFallback:
    def _verifier(self, results):
        scraper = MagicMock()
        scraper.check_availability.side_effect = results
        cache = MagicMock()
        cache.get.return_value = None
        return DClassVerifier(scraper=scraper, cache=cache), scraper

    def test_nonstop_d0_with_connection_leg_seats_scans_fallback(self):
        """Even a result marked AVAILABLE off a leg (old parse) gets a B scan."""
        primary = _conn_result(
            DClassStatus.AVAILABLE, 0, [("SIN", "BKK", 9), ("BKK", "HKG", 0)]
        )
        fallback = _make_dclass(DClassStatus.AVAILABLE, 4, origin="SIN", dest="HKG")
        verifier, scraper = self._verifier([primary, fallback])
        option = VerifyOption(
            option_id=1, segments=[_make_segment("SIN", "HKG", carrier="CX")]
        )
        result = verifier.verify_option(option)

        classes = [c[1]["booking_class"] for c in scraper.check_availability.call_args_list]
        assert classes == ["D", "B"]
        assert result.confirmed == 0
        assert result.fallback_bookable == 1

    def test_error_primary_does_not_scan_fallback(self):
        verifier, scraper = self._verifier([_error_result(origin="SIN", dest="HKG")])
        option = VerifyOption(
            option_id=1, segments=[_make_segment("SIN", "HKG", carrier="CX")]
        )
        result = verifier.verify_option(option)
        assert scraper.check_availability.call_count == 1
        assert result.segments[0].fallback is None

    def test_fallback_with_only_connection_seats_is_not_a_rescue(self):
        primary = _make_dclass(DClassStatus.NOT_AVAILABLE, 0, origin="SIN", dest="HKG")
        fb = _conn_result(
            DClassStatus.NOT_AVAILABLE, 0, [("SIN", "BKK", 9), ("BKK", "HKG", 9)]
        )
        verifier, _ = self._verifier([primary, fb])
        option = VerifyOption(
            option_id=1, segments=[_make_segment("SIN", "HKG", carrier="CX")]
        )
        result = verifier.verify_option(option)
        assert result.segments[0].fallback is not None
        assert result.fallback_bookable == 0


class TestMarriedPattern:
    def _verifier(self):
        return DClassVerifier(scraper=MagicMock(), cache=MagicMock())

    def test_pattern1_fires_on_stops0_connection_legs(self):
        """Legs parse as stops=0 rows; a complete chain still counts."""
        seg = _make_segment("SIN", "BKK", carrier="CX")
        result = _conn_result(
            DClassStatus.NOT_AVAILABLE, 0,
            [("SIN", "HKG", 5), ("HKG", "BKK", 7)],
            origin="SIN", dest="BKK",
        )
        note = self._verifier()._check_married_pattern(seg, result)
        assert note is not None
        assert "only via connection" in note

    def test_pattern1_ignores_broken_chain(self):
        """A seat on one leg only (other leg D0) is not a connection option."""
        seg = _make_segment("SIN", "BKK", carrier="CX")
        result = _conn_result(
            DClassStatus.NOT_AVAILABLE, 0,
            [("SIN", "HKG", 9), ("HKG", "BKK", 0)],
            origin="SIN", dest="BKK",
        )
        assert self._verifier()._check_married_pattern(seg, result) is None

    def test_pattern2_quotes_nonstop_seats(self):
        seg = _make_segment("LHR", "HKG", carrier="CX")
        result = _conn_result(
            DClassStatus.AVAILABLE, 2,
            [("LHR", "BRU", 9), ("BRU", "HKG", 9)],
            origin="LHR", dest="HKG",
        )
        note = self._verifier()._check_married_pattern(seg, result)
        assert "EF shows D2 " in note

    def test_pattern2_silent_when_nonstop_sold_out(self):
        seg = _make_segment("LHR", "HKG", carrier="CX")
        result = _conn_result(
            DClassStatus.NOT_AVAILABLE, 0,
            [("LHR", "BRU", 9), ("BRU", "HKG", 9)],
            origin="LHR", dest="HKG",
        )
        assert self._verifier()._check_married_pattern(seg, result) is None
