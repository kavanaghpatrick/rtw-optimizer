"""Nonstop route checker service.

Wraps SerpAPI to verify whether a carrier flies nonstop on a city-pair,
with caching, oneworld alternative lookups, and batch processing.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import date as Date
from pathlib import Path
from typing import Callable, Optional

import yaml

from rtw.nonstop.models import (
    NonstopAlternative,
    NonstopBatchResult,
    NonstopResult,
    NonstopSegmentResult,
)
from rtw.scraper.cache import ScrapeCache
from rtw.scraper.serpapi_flights import (
    SerpAPIAuthError,
    SerpAPIFlightsResponse,
    SerpAPIQuotaError,
    search_serpapi_all,
)

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data"
with open(_DATA_DIR / "carriers.yaml") as _f:
    _CARRIERS: dict = yaml.safe_load(_f)


def _carrier_name(code: str) -> str:
    """Resolve IATA code to carrier name via carriers.yaml."""
    data = _CARRIERS.get(code.upper(), {})
    return data.get("name", code.upper())


# ---------------------------------------------------------------------------
# NonstopChecker
# ---------------------------------------------------------------------------


class NonstopChecker:
    """Check nonstop service for city-pairs via SerpAPI."""

    def __init__(
        self,
        cache: Optional[ScrapeCache] = None,
        positive_ttl_hours: float = 6.0,
        negative_ttl_hours: float = 2.0,
    ) -> None:
        self._cache = cache
        self._positive_ttl = positive_ttl_hours
        self._negative_ttl = negative_ttl_hours

    # -- cache helpers -------------------------------------------------------

    @staticmethod
    def _cache_key(origin: str, dest: str, carrier: str, check_date: Date) -> str:
        return f"nonstop_{origin.upper()}_{dest.upper()}_{carrier.upper()}_{check_date.isoformat()}"

    def _cache_get(self, key: str) -> Optional[dict]:
        if self._cache is None:
            return None
        return self._cache.get(key)

    def _cache_set(self, key: str, data: dict, positive: bool) -> None:
        if self._cache is None:
            return
        ttl = self._positive_ttl if positive else self._negative_ttl
        self._cache.set(key, data, ttl_hours=ttl)

    # -- public API ----------------------------------------------------------

    def check(
        self,
        origin: str,
        dest: str,
        carrier: str,
        check_date: Date,
    ) -> NonstopResult:
        """Check if *carrier* flies nonstop origin→dest on *check_date*.

        Returns NonstopResult with has_nonstop, flight count, and pricing.
        Caches positive results for 6 h, negative for 2 h, errors not cached.
        """
        origin, dest, carrier = origin.upper(), dest.upper(), carrier.upper()
        key = self._cache_key(origin, dest, carrier, check_date)

        # Cache hit
        cached = self._cache_get(key)
        if cached is not None:
            result = NonstopResult.model_validate(cached)
            result.from_cache = True
            result.source = "cache"
            return result

        # API call with single retry
        result = self._call_serpapi(origin, dest, carrier, check_date)
        if result is None:
            time.sleep(1)
            result = self._call_serpapi(origin, dest, carrier, check_date)

        if result is None:
            return NonstopResult(
                origin=origin,
                destination=dest,
                carrier=carrier,
                carrier_name=_carrier_name(carrier),
                date_checked=check_date,
                has_nonstop=False,
                error="SerpAPI returned no data after retry",
            )

        # Cache (skip errors)
        if result.error is None:
            self._cache_set(key, result.model_dump(mode="json"), positive=result.has_nonstop)

        return result

    def check_with_alternatives(
        self,
        origin: str,
        dest: str,
        carrier: str,
        check_date: Date,
    ) -> NonstopResult:
        """Check carrier nonstop + find oneworld alternatives (2 API calls)."""
        result = self.check(origin, dest, carrier, check_date)

        alternatives = self._check_oneworld(origin, dest, check_date)
        # Exclude the queried carrier from alternatives
        filtered = [a for a in alternatives if a.carrier.upper() != carrier.upper()]
        # Sort: nonstop first, then alphabetical
        filtered.sort(key=lambda a: (not a.has_nonstop, a.carrier))
        result.alternatives = filtered
        return result

    def check_batch(
        self,
        segments: list[tuple[str, str, str]],
        check_date: Date,
        progress_cb: Optional[Callable[[int, int, str], None]] = None,
    ) -> NonstopBatchResult:
        """Batch-check multiple segments, deduplicating API calls.

        Args:
            segments: List of (origin, dest, carrier) tuples.
            check_date: Date to check.
            progress_cb: Called with (current, total, label) per segment.
        """
        # Deduplicate
        seen: dict[tuple[str, str, str], NonstopResult] = {}
        results: list[NonstopSegmentResult] = []
        api_calls = 0
        total = len(segments)

        for idx, (origin, dest, carrier) in enumerate(segments):
            origin, dest, carrier = origin.upper(), dest.upper(), carrier.upper()
            dedup_key = (origin, dest, carrier)

            if dedup_key in seen:
                nr = seen[dedup_key]
            else:
                nr = self.check_with_alternatives(origin, dest, carrier, check_date)
                if not nr.from_cache:
                    api_calls += 2  # carrier + oneworld
                seen[dedup_key] = nr

            results.append(NonstopSegmentResult(
                index=idx,
                origin=origin,
                destination=dest,
                carrier=carrier,
                result=nr,
            ))

            if progress_cb:
                progress_cb(idx + 1, total, f"{origin}-{dest} {carrier}")

        nonstop_count = sum(1 for r in results if r.result and r.result.has_nonstop)
        error_count = sum(1 for r in results if r.result and r.result.error)
        no_nonstop_count = total - nonstop_count - error_count

        return NonstopBatchResult(
            segments=results,
            date_checked=check_date,
            total=total,
            nonstop_count=nonstop_count,
            no_nonstop_count=no_nonstop_count,
            error_count=error_count,
            api_calls_used=api_calls,
        )

    def check_hub_connections(
        self,
        segments: list[tuple[str, str, str]],
        check_date: Date,
    ) -> dict[tuple[str, str, str], NonstopResult]:
        """Pre-check segments for generator integration (1 API call each).

        Returns dict keyed by (origin, dest, carrier) for O(1) lookup.
        """
        results: dict[tuple[str, str, str], NonstopResult] = {}
        for origin, dest, carrier in segments:
            origin, dest, carrier = origin.upper(), dest.upper(), carrier.upper()
            key = (origin, dest, carrier)
            if key not in results:
                results[key] = self.check(origin, dest, carrier, check_date)
        return results

    # -- private helpers -----------------------------------------------------

    def _call_serpapi(
        self,
        origin: str,
        dest: str,
        carrier: str,
        check_date: Date,
    ) -> Optional[NonstopResult]:
        """Single SerpAPI call for a carrier on a route. Returns None on failure."""
        try:
            resp = search_serpapi_all(
                origin=origin,
                dest=dest,
                date=check_date,
                cabin="business",
                max_stops=0,
                include_airlines=carrier,
                deep_search=True,
            )
        except SerpAPIAuthError as exc:
            return NonstopResult(
                origin=origin,
                destination=dest,
                carrier=carrier,
                carrier_name=_carrier_name(carrier),
                date_checked=check_date,
                has_nonstop=False,
                error=f"Auth error: {exc}",
            )
        except SerpAPIQuotaError as exc:
            return NonstopResult(
                origin=origin,
                destination=dest,
                carrier=carrier,
                carrier_name=_carrier_name(carrier),
                date_checked=check_date,
                has_nonstop=False,
                error=f"Quota exceeded: {exc}",
            )

        if resp is None:
            return None

        nonstops = [f for f in resp.flights if f.stops == 0]
        prices = [f.price_usd for f in nonstops if f.price_usd is not None]
        price_range = (min(prices), max(prices)) if prices else None

        return NonstopResult(
            origin=origin,
            destination=dest,
            carrier=carrier,
            carrier_name=_carrier_name(carrier),
            date_checked=check_date,
            has_nonstop=len(nonstops) > 0,
            nonstop_flight_count=len(nonstops),
            source="serpapi",
            price_range_usd=price_range,
        )

    def _check_oneworld(
        self,
        origin: str,
        dest: str,
        check_date: Date,
    ) -> list[NonstopAlternative]:
        """Scan all oneworld carriers for nonstop service on a route."""
        origin, dest = origin.upper(), dest.upper()
        key = self._cache_key(origin, dest, "ONEWORLD", check_date)

        cached = self._cache_get(key)
        if cached is not None:
            return [NonstopAlternative.model_validate(a) for a in cached]

        try:
            resp = search_serpapi_all(
                origin=origin,
                dest=dest,
                date=check_date,
                cabin="business",
                max_stops=0,
                include_airlines="ONEWORLD",
                deep_search=True,
            )
        except (SerpAPIAuthError, SerpAPIQuotaError) as exc:
            logger.warning("Oneworld scan failed %s-%s: %s", origin, dest, exc)
            return []

        if resp is None:
            return []

        # Group by carrier
        by_carrier: dict[str, list] = defaultdict(list)
        for flight in resp.flights:
            if flight.stops == 0:
                by_carrier[flight.carrier].append(flight)

        alternatives: list[NonstopAlternative] = []
        for code, flights in sorted(by_carrier.items()):
            prices = [f.price_usd for f in flights if f.price_usd is not None]
            alternatives.append(NonstopAlternative(
                carrier=code,
                carrier_name=_carrier_name(code),
                has_nonstop=True,
                nonstop_flight_count=len(flights),
                price_range_usd=(min(prices), max(prices)) if prices else None,
            ))

        # Cache the alternatives list
        data = [a.model_dump(mode="json") for a in alternatives]
        has_any = len(alternatives) > 0
        self._cache_set(key, data, positive=has_any)

        return alternatives
