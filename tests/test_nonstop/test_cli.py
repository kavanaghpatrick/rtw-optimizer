"""Tests for rtw check-nonstop CLI command."""

import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rtw.cli import app, _parse_route_string, _parse_pairs_file
from rtw.nonstop.models import NonstopAlternative, NonstopBatchResult, NonstopResult, NonstopSegmentResult


runner = CliRunner()
TEST_DATE = datetime.date(2026, 3, 15)


# ---------------------------------------------------------------------------
# Route string parsing
# ---------------------------------------------------------------------------


class TestParseRouteString:
    def test_single_segment(self):
        result = _parse_route_string("LHR-HEL:AY")
        assert result == [("LHR", "HEL", "AY")]

    def test_multiple_segments(self):
        result = _parse_route_string("LHR-HEL:AY,HEL-DOH:QR,DOH-MEL:QR")
        assert len(result) == 3
        assert result[0] == ("LHR", "HEL", "AY")
        assert result[2] == ("DOH", "MEL", "QR")

    def test_whitespace_tolerance(self):
        result = _parse_route_string("LHR-HEL:AY , HEL-DOH:QR")
        assert len(result) == 2

    def test_lowercase_uppercased(self):
        result = _parse_route_string("lhr-hel:ay")
        assert result == [("LHR", "HEL", "AY")]

    def test_invalid_format_raises(self):
        import typer
        with pytest.raises(typer.BadParameter, match="Invalid route segment"):
            _parse_route_string("INVALID")

    def test_empty_string_raises(self):
        import typer
        with pytest.raises(typer.BadParameter, match="Empty route"):
            _parse_route_string("")


# ---------------------------------------------------------------------------
# Pairs file parsing
# ---------------------------------------------------------------------------


class TestParsePairsFile:
    def test_basic_file(self, tmp_path):
        f = tmp_path / "pairs.txt"
        f.write_text("LHR HEL AY\nHEL DOH QR\n")
        result = _parse_pairs_file(f)
        assert len(result) == 2
        assert result[0] == ("LHR", "HEL", "AY")

    def test_comments_and_blanks_skipped(self, tmp_path):
        f = tmp_path / "pairs.txt"
        f.write_text("# This is a comment\n\nLHR HEL AY\n\n# Another comment\nHEL DOH QR\n")
        result = _parse_pairs_file(f)
        assert len(result) == 2

    def test_lowercase_uppercased(self, tmp_path):
        f = tmp_path / "pairs.txt"
        f.write_text("lhr hel ay\n")
        result = _parse_pairs_file(f)
        assert result == [("LHR", "HEL", "AY")]

    def test_file_not_found(self, tmp_path):
        import typer
        with pytest.raises(typer.BadParameter, match="File not found"):
            _parse_pairs_file(tmp_path / "missing.txt")

    def test_empty_file(self, tmp_path):
        import typer
        f = tmp_path / "pairs.txt"
        f.write_text("# only comments\n\n")
        with pytest.raises(typer.BadParameter, match="No segments found"):
            _parse_pairs_file(f)


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------


def _mock_result(has_nonstop=True, carrier="AY", origin="LHR", dest="HEL", error=None):
    return NonstopResult(
        origin=origin,
        destination=dest,
        carrier=carrier,
        carrier_name="Finnair" if carrier == "AY" else carrier,
        date_checked=TEST_DATE,
        has_nonstop=has_nonstop,
        nonstop_flight_count=4 if has_nonstop else 0,
        price_range_usd=(700.0, 800.0) if has_nonstop else None,
        alternatives=[
            NonstopAlternative(
                carrier="BA",
                carrier_name="British Airways",
                has_nonstop=True,
                nonstop_flight_count=2,
            ),
        ] if has_nonstop else [],
        error=error,
    )


def _mock_batch_result(segments_data):
    segments = []
    nonstop_count = 0
    error_count = 0
    for i, (o, d, c, has_ns) in enumerate(segments_data):
        r = _mock_result(has_nonstop=has_ns, carrier=c, origin=o, dest=d)
        segments.append(NonstopSegmentResult(index=i, origin=o, destination=d, carrier=c, result=r))
        if has_ns:
            nonstop_count += 1
    total = len(segments_data)
    return NonstopBatchResult(
        segments=segments,
        date_checked=TEST_DATE,
        total=total,
        nonstop_count=nonstop_count,
        no_nonstop_count=total - nonstop_count - error_count,
        error_count=error_count,
        api_calls_used=total * 2,
    )


class TestCheckNonstopCLI:
    """CLI tests mock at the serpapi_flights module level since cli.py uses lazy imports."""

    @patch("rtw.nonstop.checker.search_serpapi_all")
    @patch("rtw.scraper.serpapi_flights.serpapi_available", return_value=True)
    def test_single_nonstop_exit_0(self, mock_avail, mock_search):
        from rtw.scraper.serpapi_flights import SerpAPIFlight, SerpAPIFlightsResponse
        mock_search.return_value = SerpAPIFlightsResponse(
            flights=[SerpAPIFlight(carrier="AY", airline_name="Finnair", stops=0, price_usd=700.0)],
            total_count=1, nonstop_count=1,
        )
        result = runner.invoke(app, ["check-nonstop", "LHR", "HEL", "AY", "--plain"])
        assert result.exit_code == 0

    @patch("rtw.nonstop.checker.search_serpapi_all")
    @patch("rtw.scraper.serpapi_flights.serpapi_available", return_value=True)
    def test_no_nonstop_exit_1(self, mock_avail, mock_search):
        from rtw.scraper.serpapi_flights import SerpAPIFlightsResponse
        mock_search.return_value = SerpAPIFlightsResponse(flights=[], total_count=0, nonstop_count=0)
        result = runner.invoke(app, ["check-nonstop", "NRT", "JFK", "JL", "--plain"])
        assert result.exit_code == 1

    @patch("rtw.scraper.serpapi_flights.serpapi_available", return_value=False)
    def test_missing_api_key_exit_2(self, mock_avail):
        result = runner.invoke(app, ["check-nonstop", "LHR", "HEL", "AY"])
        assert result.exit_code == 2

    def test_no_args_exit_2(self):
        result = runner.invoke(app, ["check-nonstop"])
        assert result.exit_code == 2

    @patch("rtw.nonstop.checker.search_serpapi_all")
    @patch("rtw.scraper.serpapi_flights.serpapi_available", return_value=True)
    def test_json_output(self, mock_avail, mock_search):
        import json
        from rtw.scraper.serpapi_flights import SerpAPIFlight, SerpAPIFlightsResponse
        mock_search.return_value = SerpAPIFlightsResponse(
            flights=[SerpAPIFlight(carrier="AY", airline_name="Finnair", stops=0, price_usd=700.0)],
            total_count=1, nonstop_count=1,
        )
        result = runner.invoke(app, ["check-nonstop", "LHR", "HEL", "AY", "--json"])
        data = json.loads(result.output)
        assert data["has_nonstop"] is True
        assert data["origin"] == "LHR"

    @patch("rtw.nonstop.checker.search_serpapi_all")
    @patch("rtw.scraper.serpapi_flights.serpapi_available", return_value=True)
    def test_route_option_batch(self, mock_avail, mock_search):
        from rtw.scraper.serpapi_flights import SerpAPIFlight, SerpAPIFlightsResponse
        mock_search.return_value = SerpAPIFlightsResponse(
            flights=[SerpAPIFlight(carrier="AY", airline_name="Finnair", stops=0, price_usd=700.0)],
            total_count=1, nonstop_count=1,
        )
        result = runner.invoke(app, ["check-nonstop", "--route", "LHR-HEL:AY,HEL-DOH:QR", "--plain"])
        assert result.exit_code == 0

    @patch("rtw.nonstop.checker.search_serpapi_all")
    @patch("rtw.scraper.serpapi_flights.serpapi_available", return_value=True)
    def test_batch_failure_exit_1(self, mock_avail, mock_search):
        from rtw.scraper.serpapi_flights import SerpAPIFlight, SerpAPIFlightsResponse
        # First segment nonstop, second none
        mock_search.side_effect = [
            SerpAPIFlightsResponse(
                flights=[SerpAPIFlight(carrier="AY", airline_name="Finnair", stops=0, price_usd=700.0)],
                total_count=1, nonstop_count=1,
            ),
            SerpAPIFlightsResponse(flights=[], total_count=0, nonstop_count=0),  # AY oneworld
            SerpAPIFlightsResponse(flights=[], total_count=0, nonstop_count=0),  # JL carrier
            None,  # retry
            SerpAPIFlightsResponse(flights=[], total_count=0, nonstop_count=0),  # JL oneworld
        ]
        result = runner.invoke(app, ["check-nonstop", "--route", "LHR-HEL:AY,NRT-JFK:JL", "--plain"])
        assert result.exit_code == 1

    @patch("rtw.scraper.serpapi_flights.serpapi_available", return_value=True)
    def test_invalid_date_exit_2(self, mock_avail):
        result = runner.invoke(app, ["check-nonstop", "LHR", "HEL", "AY", "--date", "not-a-date"])
        assert result.exit_code == 2

    @patch("rtw.nonstop.checker.search_serpapi_all")
    @patch("rtw.scraper.serpapi_flights.serpapi_available", return_value=True)
    @patch("rtw.scraper.cache.ScrapeCache.get", return_value=None)
    def test_error_result_exit_2(self, mock_cache_get, mock_avail, mock_search):
        # check_with_alternatives calls check() + _check_oneworld()
        # check() tries twice (initial + retry), both None => error result
        mock_search.return_value = None
        result = runner.invoke(app, ["check-nonstop", "LHR", "HEL", "AY", "--plain"])
        assert result.exit_code == 2
