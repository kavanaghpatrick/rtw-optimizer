"""Tests for NonstopChecker service."""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from rtw.nonstop.checker import NonstopChecker, _carrier_name
from rtw.nonstop.models import NonstopAlternative, NonstopResult
from rtw.scraper.serpapi_flights import (
    SerpAPIAuthError,
    SerpAPIFlight,
    SerpAPIFlightsResponse,
    SerpAPIQuotaError,
)

TEST_DATE = datetime.date(2026, 3, 15)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(flights: list[SerpAPIFlight]) -> SerpAPIFlightsResponse:
    nonstop_count = sum(1 for f in flights if f.stops == 0)
    return SerpAPIFlightsResponse(
        flights=flights,
        total_count=len(flights),
        nonstop_count=nonstop_count,
    )


def _nonstop_flight(carrier="AY", name="Finnair", number="AY 1334", price=727.0):
    return SerpAPIFlight(
        carrier=carrier,
        airline_name=name,
        flight_number=number,
        price_usd=price,
        stops=0,
        duration_minutes=170,
    )


def _connecting_flight(carrier="AY", name="Finnair", number="AY 800", price=650.0):
    return SerpAPIFlight(
        carrier=carrier,
        airline_name=name,
        flight_number=number,
        price_usd=price,
        stops=1,
        duration_minutes=360,
    )


# ---------------------------------------------------------------------------
# TestCarrierName
# ---------------------------------------------------------------------------


class TestCarrierName:
    def test_known_carrier(self):
        assert _carrier_name("AY") == "Finnair"

    def test_unknown_carrier_fallback(self):
        assert _carrier_name("ZZ") == "ZZ"

    def test_case_insensitive(self):
        assert _carrier_name("ay") == "Finnair"


# ---------------------------------------------------------------------------
# TestCacheKey
# ---------------------------------------------------------------------------


class TestCacheKey:
    def test_format(self):
        key = NonstopChecker._cache_key("LHR", "HEL", "AY", TEST_DATE)
        assert key == "nonstop_LHR_HEL_AY_2026-03-15"

    def test_uppercases(self):
        key = NonstopChecker._cache_key("lhr", "hel", "ay", TEST_DATE)
        assert key == "nonstop_LHR_HEL_AY_2026-03-15"

    def test_oneworld_key(self):
        key = NonstopChecker._cache_key("LHR", "HEL", "ONEWORLD", TEST_DATE)
        assert key == "nonstop_LHR_HEL_ONEWORLD_2026-03-15"

    def test_different_dates_different_keys(self):
        k1 = NonstopChecker._cache_key("LHR", "HEL", "AY", datetime.date(2026, 3, 15))
        k2 = NonstopChecker._cache_key("LHR", "HEL", "AY", datetime.date(2026, 3, 16))
        assert k1 != k2


# ---------------------------------------------------------------------------
# TestCheck
# ---------------------------------------------------------------------------


class TestCheck:
    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_nonstop_found(self, mock_search):
        mock_search.return_value = _make_response([
            _nonstop_flight(),
            _nonstop_flight(number="AY 1336", price=749.0),
        ])
        checker = NonstopChecker()
        result = checker.check("LHR", "HEL", "AY", TEST_DATE)
        assert result.has_nonstop is True
        assert result.nonstop_flight_count == 2
        assert result.carrier == "AY"
        assert result.carrier_name == "Finnair"
        assert result.error is None
        assert result.price_range_usd == (727.0, 749.0)

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_no_nonstop(self, mock_search):
        mock_search.return_value = _make_response([])
        checker = NonstopChecker()
        result = checker.check("NRT", "JFK", "JL", TEST_DATE)
        assert result.has_nonstop is False
        assert result.nonstop_flight_count == 0

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_only_connecting_flights(self, mock_search):
        mock_search.return_value = _make_response([_connecting_flight()])
        checker = NonstopChecker()
        result = checker.check("NRT", "JFK", "AY", TEST_DATE)
        assert result.has_nonstop is False
        assert result.nonstop_flight_count == 0

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_retry_on_none(self, mock_search):
        """First call returns None, retry succeeds."""
        mock_search.side_effect = [
            None,
            _make_response([_nonstop_flight()]),
        ]
        checker = NonstopChecker()
        result = checker.check("LHR", "HEL", "AY", TEST_DATE)
        assert result.has_nonstop is True
        assert mock_search.call_count == 2

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_both_retries_fail(self, mock_search):
        mock_search.return_value = None
        checker = NonstopChecker()
        result = checker.check("LHR", "HEL", "AY", TEST_DATE)
        assert result.has_nonstop is False
        assert result.error is not None
        assert "retry" in result.error.lower()

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_auth_error(self, mock_search):
        mock_search.side_effect = SerpAPIAuthError("bad key")
        checker = NonstopChecker()
        result = checker.check("LHR", "HEL", "AY", TEST_DATE)
        assert result.has_nonstop is False
        assert "Auth error" in result.error

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_quota_error(self, mock_search):
        mock_search.side_effect = SerpAPIQuotaError("exceeded")
        checker = NonstopChecker()
        result = checker.check("LHR", "HEL", "AY", TEST_DATE)
        assert result.has_nonstop is False
        assert "Quota" in result.error

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_uppercases_codes(self, mock_search):
        mock_search.return_value = _make_response([_nonstop_flight()])
        checker = NonstopChecker()
        result = checker.check("lhr", "hel", "ay", TEST_DATE)
        assert result.origin == "LHR"
        assert result.destination == "HEL"
        assert result.carrier == "AY"

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_serpapi_called_with_correct_params(self, mock_search):
        mock_search.return_value = _make_response([])
        checker = NonstopChecker()
        checker.check("LHR", "HEL", "AY", TEST_DATE)
        mock_search.assert_called_with(
            origin="LHR",
            dest="HEL",
            date=TEST_DATE,
            cabin="business",
            max_stops=0,
            include_airlines="AY",
            deep_search=True,
        )


# ---------------------------------------------------------------------------
# TestCheckCache
# ---------------------------------------------------------------------------


class TestCheckCache:
    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_cache_hit_skips_api(self, mock_search):
        cache = MagicMock()
        cache.get.return_value = {
            "origin": "LHR",
            "destination": "HEL",
            "carrier": "AY",
            "carrier_name": "Finnair",
            "date_checked": "2026-03-15",
            "has_nonstop": True,
            "nonstop_flight_count": 4,
            "from_cache": False,
            "source": "serpapi",
        }
        checker = NonstopChecker(cache=cache)
        result = checker.check("LHR", "HEL", "AY", TEST_DATE)
        assert result.has_nonstop is True
        assert result.from_cache is True
        assert result.source == "cache"
        mock_search.assert_not_called()

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_cache_miss_calls_api(self, mock_search):
        cache = MagicMock()
        cache.get.return_value = None
        mock_search.return_value = _make_response([_nonstop_flight()])
        checker = NonstopChecker(cache=cache)
        result = checker.check("LHR", "HEL", "AY", TEST_DATE)
        assert result.has_nonstop is True
        assert result.from_cache is False
        mock_search.assert_called_once()

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_positive_result_cached_with_positive_ttl(self, mock_search):
        cache = MagicMock()
        cache.get.return_value = None
        mock_search.return_value = _make_response([_nonstop_flight()])
        checker = NonstopChecker(cache=cache, positive_ttl_hours=6.0)
        checker.check("LHR", "HEL", "AY", TEST_DATE)
        cache.set.assert_called_once()
        _, kwargs = cache.set.call_args
        assert kwargs["ttl_hours"] == 6.0

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_negative_result_cached_with_negative_ttl(self, mock_search):
        cache = MagicMock()
        cache.get.return_value = None
        mock_search.return_value = _make_response([])
        checker = NonstopChecker(cache=cache, negative_ttl_hours=2.0)
        checker.check("NRT", "JFK", "JL", TEST_DATE)
        cache.set.assert_called_once()
        _, kwargs = cache.set.call_args
        assert kwargs["ttl_hours"] == 2.0

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_error_result_not_cached(self, mock_search):
        cache = MagicMock()
        cache.get.return_value = None
        mock_search.side_effect = SerpAPIAuthError("bad key")
        checker = NonstopChecker(cache=cache)
        checker.check("LHR", "HEL", "AY", TEST_DATE)
        cache.set.assert_not_called()


# ---------------------------------------------------------------------------
# TestCheckWithAlternatives
# ---------------------------------------------------------------------------


class TestCheckWithAlternatives:
    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_two_api_calls(self, mock_search):
        """Should call API twice: once for carrier, once for ONEWORLD."""
        mock_search.return_value = _make_response([_nonstop_flight()])
        checker = NonstopChecker()
        checker.check_with_alternatives("LHR", "HEL", "AY", TEST_DATE)
        assert mock_search.call_count == 2

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_excludes_queried_carrier(self, mock_search):
        """Alternatives should NOT include the queried carrier."""
        mock_search.side_effect = [
            # carrier check (AY)
            _make_response([_nonstop_flight()]),
            # oneworld check (returns AY + BA)
            _make_response([
                _nonstop_flight(carrier="AY", name="Finnair"),
                _nonstop_flight(carrier="BA", name="British Airways", number="BA 798", price=950.0),
            ]),
        ]
        checker = NonstopChecker()
        result = checker.check_with_alternatives("LHR", "HEL", "AY", TEST_DATE)
        carrier_codes = [a.carrier for a in result.alternatives]
        assert "AY" not in carrier_codes
        assert "BA" in carrier_codes

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_alternatives_sorted_nonstop_first(self, mock_search):
        mock_search.side_effect = [
            _make_response([_nonstop_flight()]),
            _make_response([
                _nonstop_flight(carrier="BA", name="British Airways"),
                _nonstop_flight(carrier="CX", name="Cathay Pacific"),
            ]),
        ]
        checker = NonstopChecker()
        result = checker.check_with_alternatives("LHR", "HEL", "AY", TEST_DATE)
        # All have nonstop, so alphabetical: BA, CX
        codes = [a.carrier for a in result.alternatives]
        assert codes == ["BA", "CX"]

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_carrier_ok_but_oneworld_fails(self, mock_search):
        """If carrier check works but oneworld scan fails, return empty alternatives."""
        mock_search.side_effect = [
            _make_response([_nonstop_flight()]),
            None,  # oneworld fails
        ]
        checker = NonstopChecker()
        result = checker.check_with_alternatives("LHR", "HEL", "AY", TEST_DATE)
        assert result.has_nonstop is True
        assert result.alternatives == []


# ---------------------------------------------------------------------------
# TestCheckBatch
# ---------------------------------------------------------------------------


class TestCheckBatch:
    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_batch_processes_all_segments(self, mock_search):
        mock_search.return_value = _make_response([_nonstop_flight()])
        checker = NonstopChecker()
        segments = [
            ("LHR", "HEL", "AY"),
            ("HEL", "DOH", "QR"),
        ]
        result = checker.check_batch(segments, TEST_DATE)
        assert result.total == 2
        assert len(result.segments) == 2

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_batch_deduplicates(self, mock_search):
        mock_search.return_value = _make_response([_nonstop_flight()])
        checker = NonstopChecker()
        segments = [
            ("LHR", "HEL", "AY"),
            ("LHR", "HEL", "AY"),  # duplicate
        ]
        result = checker.check_batch(segments, TEST_DATE)
        assert result.total == 2
        # Only 1 unique segment, so 2 API calls (carrier + oneworld), not 4
        assert result.api_calls_used == 2

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_batch_progress_callback(self, mock_search):
        mock_search.return_value = _make_response([_nonstop_flight()])
        checker = NonstopChecker()
        calls = []
        segments = [("LHR", "HEL", "AY"), ("HEL", "DOH", "QR")]
        checker.check_batch(segments, TEST_DATE, progress_cb=lambda c, t, l: calls.append((c, t, l)))
        assert len(calls) == 2
        assert calls[0] == (1, 2, "LHR-HEL AY")
        assert calls[1] == (2, 2, "HEL-DOH QR")

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_batch_counts(self, mock_search):
        # First segment: nonstop found (2 calls: carrier + oneworld)
        # Second segment: no nonstop (2 calls: carrier + oneworld)
        mock_search.side_effect = [
            _make_response([_nonstop_flight()]),      # AY carrier check
            _make_response([_nonstop_flight()]),      # AY oneworld check
            _make_response([]),                        # QR carrier check
            _make_response([]),                        # QR oneworld check (empty)
        ]
        checker = NonstopChecker()
        result = checker.check_batch(
            [("LHR", "HEL", "AY"), ("NRT", "JFK", "QR")],
            TEST_DATE,
        )
        assert result.nonstop_count == 1
        assert result.no_nonstop_count == 1
        assert result.error_count == 0
        assert result.all_clear is False

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_batch_all_clear(self, mock_search):
        mock_search.return_value = _make_response([_nonstop_flight()])
        checker = NonstopChecker()
        result = checker.check_batch([("LHR", "HEL", "AY")], TEST_DATE)
        assert result.all_clear is True

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_batch_empty_segments(self, mock_search):
        checker = NonstopChecker()
        result = checker.check_batch([], TEST_DATE)
        assert result.total == 0
        assert result.all_clear is True


# ---------------------------------------------------------------------------
# TestCheckHubConnections
# ---------------------------------------------------------------------------


class TestCheckHubConnections:
    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_returns_dict(self, mock_search):
        mock_search.return_value = _make_response([_nonstop_flight()])
        checker = NonstopChecker()
        result = checker.check_hub_connections(
            [("LHR", "HEL", "AY")],
            TEST_DATE,
        )
        assert isinstance(result, dict)
        assert ("LHR", "HEL", "AY") in result

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_uses_check_not_alternatives(self, mock_search):
        """Hub connections use check() (1 API call) not check_with_alternatives() (2)."""
        mock_search.return_value = _make_response([_nonstop_flight()])
        checker = NonstopChecker()
        checker.check_hub_connections(
            [("LHR", "HEL", "AY")],
            TEST_DATE,
        )
        # check() calls search_serpapi_all once per segment (not twice)
        assert mock_search.call_count == 1

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_deduplicates(self, mock_search):
        mock_search.return_value = _make_response([_nonstop_flight()])
        checker = NonstopChecker()
        result = checker.check_hub_connections(
            [("LHR", "HEL", "AY"), ("LHR", "HEL", "AY")],
            TEST_DATE,
        )
        assert mock_search.call_count == 1
        assert len(result) == 1

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_empty_segments(self, mock_search):
        checker = NonstopChecker()
        result = checker.check_hub_connections([], TEST_DATE)
        assert result == {}
        mock_search.assert_not_called()

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_result_keyed_by_tuple(self, mock_search):
        mock_search.return_value = _make_response([_nonstop_flight()])
        checker = NonstopChecker()
        result = checker.check_hub_connections(
            [("LHR", "HEL", "AY"), ("HEL", "DOH", "QR")],
            TEST_DATE,
        )
        assert ("LHR", "HEL", "AY") in result
        assert ("HEL", "DOH", "QR") in result


# ---------------------------------------------------------------------------
# TestOneWorldAlternatives
# ---------------------------------------------------------------------------


class TestOneWorldAlternatives:
    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_groups_by_carrier(self, mock_search):
        mock_search.return_value = _make_response([
            _nonstop_flight(carrier="AY", name="Finnair", number="AY 1334"),
            _nonstop_flight(carrier="AY", name="Finnair", number="AY 1336"),
            _nonstop_flight(carrier="BA", name="British Airways", number="BA 798"),
        ])
        checker = NonstopChecker()
        alts = checker._check_oneworld("LHR", "HEL", TEST_DATE)
        carriers = {a.carrier for a in alts}
        assert "AY" in carriers
        assert "BA" in carriers
        ay_alt = next(a for a in alts if a.carrier == "AY")
        assert ay_alt.nonstop_flight_count == 2

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_price_range(self, mock_search):
        mock_search.return_value = _make_response([
            _nonstop_flight(carrier="AY", price=700.0),
            _nonstop_flight(carrier="AY", price=800.0),
        ])
        checker = NonstopChecker()
        alts = checker._check_oneworld("LHR", "HEL", TEST_DATE)
        ay = alts[0]
        assert ay.price_range_usd == (700.0, 800.0)

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_auth_error_returns_empty(self, mock_search):
        mock_search.side_effect = SerpAPIAuthError("bad key")
        checker = NonstopChecker()
        alts = checker._check_oneworld("LHR", "HEL", TEST_DATE)
        assert alts == []

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_none_response_returns_empty(self, mock_search):
        mock_search.return_value = None
        checker = NonstopChecker()
        alts = checker._check_oneworld("LHR", "HEL", TEST_DATE)
        assert alts == []

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_oneworld_cache_key(self, mock_search):
        """Oneworld scan uses ONEWORLD in cache key."""
        cache = MagicMock()
        cache.get.return_value = None
        mock_search.return_value = _make_response([])
        checker = NonstopChecker(cache=cache)
        checker._check_oneworld("LHR", "HEL", TEST_DATE)
        cache_key = cache.get.call_args[0][0]
        assert "ONEWORLD" in cache_key

    @patch("rtw.nonstop.checker.search_serpapi_all")
    def test_oneworld_cached(self, mock_search):
        cache = MagicMock()
        cache.get.return_value = [
            {"carrier": "BA", "carrier_name": "British Airways", "has_nonstop": True, "nonstop_flight_count": 1},
        ]
        checker = NonstopChecker(cache=cache)
        alts = checker._check_oneworld("LHR", "HEL", TEST_DATE)
        assert len(alts) == 1
        assert alts[0].carrier == "BA"
        mock_search.assert_not_called()
