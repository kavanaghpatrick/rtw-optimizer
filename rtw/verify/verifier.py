"""Availability verification orchestrator.

Coordinates the scraper, cache, and progress reporting to verify
award class availability across all flown segments of an itinerary option.
Uses per-carrier booking class resolution (D for business on all carriers).
When the primary class is sold out, re-scans the rule-mandated fallback
class (H on AA, B otherwise) so genuinely bookable segments are not
reported as unavailable.
"""

import logging
import time
from typing import Optional

from rtw.carriers import get_booking_class, get_fallback_class
from rtw.models import CabinClass
from rtw.scraper.cache import ScrapeCache
from rtw.scraper.expertflyer import ExpertFlyerScraper, SessionExpiredError
from rtw.verify.models import (
    DClassResult,
    DClassStatus,
    ProgressCallback,
    SegmentVerification,
    VerifyOption,
    VerifyResult,
)

logger = logging.getLogger(__name__)

_CACHE_TTL_HOURS = 24
_CACHE_KEY_PREFIX = "dclass"

# Carriers with known married segment patterns (hub-connection)
_MARRIED_CHECK_HUBS = {
    "CX": "HKG",
    "QR": "DOH",
}


class DClassVerifier:
    """Verify award class availability for itinerary segments.

    Checks each flown segment against ExpertFlyer, using the cache
    to avoid redundant queries. Surface segments are skipped.

    Resolves booking class per carrier (D for business on all carriers)
    unless an explicit override is provided. When the primary class is
    sold out, re-scans the carrier's fallback class (H on AA, B otherwise)
    unless fallback scanning is disabled or an override is set.
    """

    def __init__(
        self,
        scraper: ExpertFlyerScraper,
        cache: Optional[ScrapeCache] = None,
        booking_class: Optional[str] = None,
        cabin: CabinClass = CabinClass.BUSINESS,
        enable_fallback: bool = True,
    ) -> None:
        self.scraper = scraper
        self.cache = cache or ScrapeCache()
        self._booking_class_override = booking_class
        self.cabin = cabin
        self._enable_fallback = enable_fallback
        self._session_expired = False

    def _get_segment_booking_class(self, seg: SegmentVerification) -> str:
        """Resolve the booking class for a segment.

        If an override was set, use it for all segments.
        Otherwise, look up per carrier from carriers.yaml.
        """
        if self._booking_class_override is not None:
            return self._booking_class_override
        return get_booking_class(seg.carrier, self.cabin)

    def _cache_key(
        self, seg: SegmentVerification, booking_class: Optional[str] = None
    ) -> str:
        """Build cache key for a segment + booking class.

        Defaults to the segment's resolved primary class; pass an explicit
        class to cache fallback scans independently.
        """
        bc = booking_class or self._get_segment_booking_class(seg)
        return (
            f"{_CACHE_KEY_PREFIX}_{seg.carrier}_{seg.origin}_"
            f"{seg.destination}_{seg.target_date}_{bc}"
        )

    def _check_cache(
        self, seg: SegmentVerification, booking_class: Optional[str] = None
    ) -> Optional[DClassResult]:
        """Look up cached result for a segment + booking class."""
        if self.cache is None:
            return None
        key = self._cache_key(seg, booking_class)
        cached = self.cache.get(key)
        if cached is None:
            return None
        try:
            result = DClassResult.model_validate(cached)
            result.from_cache = True
            result.status = (
                DClassStatus.AVAILABLE
                if result.seats > 0
                else DClassStatus.NOT_AVAILABLE
            )
            return result
        except Exception:
            return None

    def _store_cache(
        self,
        seg: SegmentVerification,
        result: DClassResult,
        booking_class: Optional[str] = None,
    ) -> None:
        """Cache a result under its booking-class-specific key."""
        if self.cache is None:
            return
        key = self._cache_key(seg, booking_class)
        self.cache.set(key, result.model_dump(mode="json"), ttl_hours=_CACHE_TTL_HOURS)

    def _scan_class(
        self,
        seg: SegmentVerification,
        booking_class: str,
        no_cache: bool = False,
    ) -> DClassResult:
        """Scan a single booking class for a segment: cache -> scrape -> store.

        Returns a populated DClassResult. Lets SessionExpiredError and other
        scraper exceptions propagate to the caller for status handling.
        """
        if not no_cache:
            cached = self._check_cache(seg, booking_class)
            if cached is not None:
                return cached

        start = time.time()
        dclass = self.scraper.check_availability(
            origin=seg.origin,
            dest=seg.destination,
            date=seg.target_date,
            carrier=seg.carrier or "",
            booking_class=booking_class,
        )
        elapsed = time.time() - start
        logger.debug(
            "ExpertFlyer check %s→%s %s: %s (%.1fs)",
            seg.origin,
            seg.destination,
            booking_class,
            dclass.display_code if dclass else "None",
            elapsed,
        )

        if dclass:
            dclass.booking_class = booking_class
            self._store_cache(seg, dclass, booking_class)
            return dclass

        return DClassResult(
            status=DClassStatus.UNKNOWN,
            seats=0,
            carrier=seg.carrier or "??",
            origin=seg.origin,
            destination=seg.destination,
            target_date=seg.target_date,
            booking_class=booking_class,
            error_message="Scraper returned None (no session?)",
        )

    def _should_scan_fallback(
        self, seg: SegmentVerification, primary: DClassResult
    ) -> bool:
        """Whether to scan the fallback class after the primary result.

        Only when fallback is enabled, no explicit override is in force, the
        primary is definitively unavailable (D0, not ERROR/UNKNOWN), and the
        carrier has a fallback class defined.
        """
        if not self._enable_fallback:
            return False
        if self._booking_class_override is not None:
            return False
        if primary.status != DClassStatus.NOT_AVAILABLE:
            return False
        return get_fallback_class(seg.carrier, self.cabin) is not None

    def _check_married_pattern(
        self, seg: SegmentVerification, result: DClassResult
    ) -> Optional[str]:
        """Detect married segment patterns and hub O&D control risks.

        Checks two patterns:
        1. If nonstop has 0 seats but connections have seats (classic MSC)
        2. If segment terminates at or transits through a carrier's hub
           where O&D control may make EF results misleading

        ExpertFlyer queries leg-level (AVS) availability which cannot
        reflect O&D-based inventory restrictions applied at sell time.
        D-class showing on EF does NOT guarantee bookability on RTW fares.
        """
        carrier = seg.carrier
        if not carrier or carrier not in _MARRIED_CHECK_HUBS:
            return None
        hub = _MARRIED_CHECK_HUBS[carrier]

        # Pattern 1: Neither endpoint is the hub — check nonstop vs connection
        if seg.origin != hub and seg.destination != hub:
            nonstop_seats = result.nonstop_seats
            connecting_with_seats = [
                f for f in result.flights if f.stops > 0 and f.seats > 0
            ]
            if nonstop_seats == 0 and connecting_with_seats:
                return (
                    f"{result.booking_class}-class only via connection "
                    f"(likely married through {hub})"
                )
            return None

        # Pattern 2: Segment touches the hub — O&D control warning
        # EF shows leg-level availability but the airline may block
        # standalone D-class at the hub for RTW fares
        if result.seats > 0:
            carrier_name = "Cathay Pacific" if carrier == "CX" else "Qatar Airways"
            return (
                f"O&D control: {carrier_name} uses origin-destination revenue "
                f"management at {hub}. EF shows {result.booking_class}"
                f"{result.seats} but D-class may be unbookable standalone "
                f"on RTW fares. Present to agent as connected routing "
                f"(e.g., {seg.origin}-[next city] via {hub}) rather than "
                f"standalone {seg.origin}-{seg.destination}."
            )
        return None

    def verify_option(
        self,
        option: VerifyOption,
        progress_cb: Optional[ProgressCallback] = None,
        no_cache: bool = False,
    ) -> VerifyResult:
        """Verify D-class for all flown segments in one option.

        Surface segments are skipped (not sent to scraper).
        On SessionExpiredError, remaining segments are marked UNKNOWN.
        On individual segment errors, that segment is marked ERROR
        and verification continues.
        """
        result = VerifyResult(option_id=option.option_id, segments=[])

        for seg in option.segments:
            # Copy segment for result
            verified = seg.model_copy()

            if seg.segment_type == "SURFACE":
                result.segments.append(verified)
                if progress_cb:
                    progress_cb(len(result.segments), len(option.segments), verified)
                continue

            if seg.target_date is None:
                # No date to query — can't verify. Mark UNKNOWN rather than
                # calling the scraper with a None date (which would crash).
                verified.dclass = DClassResult(
                    status=DClassStatus.UNKNOWN,
                    seats=0,
                    carrier=seg.carrier or "??",
                    origin=seg.origin,
                    destination=seg.destination,
                    target_date=None,
                    booking_class=self._get_segment_booking_class(seg),
                    error_message="No date assigned to segment — cannot verify",
                )
                result.segments.append(verified)
                if progress_cb:
                    progress_cb(len(result.segments), len(option.segments), verified)
                continue

            if self._session_expired:
                # Session died mid-batch — mark remaining as unknown
                verified.dclass = DClassResult(
                    status=DClassStatus.UNKNOWN,
                    seats=0,
                    carrier=seg.carrier or "??",
                    origin=seg.origin,
                    destination=seg.destination,
                    target_date=seg.target_date,
                    booking_class=self._get_segment_booking_class(seg),
                    error_message="Session expired during batch",
                )
                result.segments.append(verified)
                if progress_cb:
                    progress_cb(len(result.segments), len(option.segments), verified)
                continue

            # Scrape primary class (cache handled inside _scan_class)
            seg_bc = self._get_segment_booking_class(seg)
            try:
                dclass = self._scan_class(seg, seg_bc, no_cache)
                verified.dclass = dclass
                # Check for married segment pattern on the primary result
                verified.married_segment_note = self._check_married_pattern(
                    seg, dclass
                )

                # Primary sold out → try the rule-mandated fallback class
                # (H on AA, B otherwise). Best-effort: failures leave fallback
                # unset rather than failing the whole segment.
                if self._should_scan_fallback(seg, dclass):
                    fb_class = get_fallback_class(seg.carrier, self.cabin)
                    try:
                        verified.fallback = self._scan_class(seg, fb_class, no_cache)
                    except SessionExpiredError:
                        self._session_expired = True
                    except Exception:
                        pass

            except SessionExpiredError as exc:
                self._session_expired = True
                verified.dclass = DClassResult(
                    status=DClassStatus.UNKNOWN,
                    seats=0,
                    carrier=seg.carrier or "??",
                    origin=seg.origin,
                    destination=seg.destination,
                    target_date=seg.target_date,
                    booking_class=seg_bc,
                    error_message=str(exc),
                )
            except Exception as exc:
                verified.dclass = DClassResult(
                    status=DClassStatus.ERROR,
                    seats=0,
                    carrier=seg.carrier or "??",
                    origin=seg.origin,
                    destination=seg.destination,
                    target_date=seg.target_date,
                    booking_class=seg_bc,
                    error_message=str(exc),
                )

            result.segments.append(verified)
            if progress_cb:
                progress_cb(len(result.segments), len(option.segments), verified)

        return result

    def verify_batch(
        self,
        options: list[VerifyOption],
        progress_cb: Optional[ProgressCallback] = None,
        no_cache: bool = False,
    ) -> list[VerifyResult]:
        """Verify D-class for multiple itinerary options sequentially."""
        results = []
        for option in options:
            result = self.verify_option(option, progress_cb, no_cache)
            results.append(result)
        return results
