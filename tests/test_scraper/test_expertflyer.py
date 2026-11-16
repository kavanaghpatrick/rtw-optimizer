"""Tests for ExpertFlyer scraper module."""

import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from rtw.scraper.expertflyer import (
    ExpertFlyerScraper,
    ScrapeError,
    SessionExpiredError,
    parse_availability_html,
)


class TestExpertFlyerScraper:
    """Test ExpertFlyerScraper session-based approach."""

    def test_scraper_init_no_session(self):
        scraper = ExpertFlyerScraper()
        assert scraper._session_path is None
        assert scraper._query_count == 0

    def test_scraper_init_with_session(self, tmp_path):
        path = str(tmp_path / "session.json")
        scraper = ExpertFlyerScraper(session_path=path)
        assert scraper._session_path == path

    @patch("rtw.scraper.expertflyer._get_credentials", return_value=None)
    def test_check_availability_no_credentials(self, mock_creds):
        """Returns None when no credentials configured."""
        scraper = ExpertFlyerScraper()
        result = scraper.check_availability(
            origin="LHR",
            dest="HKG",
            date=datetime.date(2026, 3, 10),
            carrier="CX",
        )
        assert result is None

    def test_build_results_url(self):
        scraper = ExpertFlyerScraper()
        url = scraper._build_results_url(
            origin="LHR",
            dest="HKG",
            date=datetime.date(2026, 3, 10),
            booking_class="D",
            carrier="CX",
        )
        assert "origin=LHR" in url
        assert "destination=HKG" in url
        assert "classFilter=D" in url
        assert "airLineCodes=CX" in url
        assert "resultsDisplay=single" in url
        assert "/air/availability/results" in url

    def test_build_results_url_no_carrier(self):
        scraper = ExpertFlyerScraper()
        url = scraper._build_results_url(
            origin="SYD",
            dest="LAX",
            date=datetime.date(2026, 5, 1),
        )
        assert "airLineCodes=" in url
        assert "origin=SYD" in url

    def test_session_expired_error(self):
        err = SessionExpiredError()
        assert err.error_type == "SESSION_EXPIRED"
        assert isinstance(err, ScrapeError)

    def test_scrape_error(self):
        err = ScrapeError("timeout", error_type="TIMEOUT")
        assert err.error_type == "TIMEOUT"
        assert "timeout" in str(err)


class TestParseAvailabilityHtml:
    """Test the standalone HTML parser."""

    @pytest.fixture
    def fixture_html(self):
        path = Path(__file__).parent.parent / "fixtures" / "ef_results_lhr_hkg_d.html"
        if not path.exists():
            pytest.skip("ExpertFlyer fixture not found")
        return path.read_text(encoding="utf-8")

    def test_parse_real_fixture(self, fixture_html):
        results = parse_availability_html(fixture_html, "D")
        assert len(results) >= 7
        # All results should have carrier
        carriers = [r["carrier"] for r in results if r["carrier"]]
        assert "CX" in carriers

    def test_d_class_seats(self, fixture_html):
        results = parse_availability_html(fixture_html, "D")
        seats = [r["seats"] for r in results if r["seats"] is not None]
        assert 9 in seats  # CX flights had D9
        assert 5 in seats  # BA 31 had D5

    def test_empty_html(self):
        results = parse_availability_html("<html></html>", "D")
        assert results == []

    @pytest.mark.integration
    def test_real_availability_check(self):
        """Integration test: requires valid ExpertFlyer session."""
        session_path = Path.home() / ".rtw" / "expertflyer_session.json"
        if not session_path.exists():
            pytest.skip("ExpertFlyer session not configured")

        scraper = ExpertFlyerScraper(session_path=str(session_path))
        result = scraper.check_availability(
            origin="LHR",
            dest="HKG",
            date=datetime.date(2026, 3, 15),
            carrier="CX",
        )
        assert result is not None
        assert result.origin == "LHR"
        assert result.destination == "HKG"


# ---------------------------------------------------------------------------
# Live-parser O&D matching (real fixture rendered in headless Chromium)
# ---------------------------------------------------------------------------

_FIXTURE = Path(__file__).parent.parent / "fixtures" / "ef_results_lhr_hkg_d.html"
_FIXTURE_DATE = datetime.date(2026, 2, 19)


def _nonstops_sold_out(html: str) -> str:
    """Edit the fixture so every LHR-HKG nonstop shows D0.

    Rows before the first '1 Connection' header are the nonstops; the
    BRU/MUC connection legs after it keep their D9.
    """
    import re

    cut = html.index("1 Connection")
    return re.sub(r"\bD[1-9]\b", "D0", html[:cut]) + html[cut:]


def _parse_in_browser(htmls: dict) -> dict:
    """Load each HTML into real Chromium and run the live row parser on it.

    Runs in a worker thread because Playwright's sync API refuses to start
    on a thread that already has an asyncio loop (pytest may install one).
    Returns {key: DClassResult}; keys are (name, booking_class) tuples.
    """
    from concurrent.futures import ThreadPoolExecutor

    sync_api = pytest.importorskip("playwright.sync_api")

    def _run():
        with sync_api.sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                out = {}
                for (name, bc), html in htmls.items():
                    page.set_content(html)
                    out[(name, bc)] = ExpertFlyerScraper()._parse_results_table(
                        page, "LHR", "HKG", _FIXTURE_DATE, "CX", bc
                    )
                return out
            finally:
                browser.close()

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(_run).result()
    except Exception as exc:  # browser binaries not installed
        if "Executable doesn't exist" in str(exc):
            pytest.skip(f"Chromium not available: {exc}")
        raise


@pytest.fixture(scope="module")
def parsed():
    if not _FIXTURE.exists():
        pytest.skip("ExpertFlyer fixture not found")
    html = _FIXTURE.read_text(encoding="utf-8")
    return _parse_in_browser({
        ("original", "D"): html,
        ("nonstops_d0", "D"): _nonstops_sold_out(html),
    })


class TestParseResultsTableODMatching:
    def test_unedited_fixture_available_on_nonstops(self, parsed):
        from rtw.verify.models import DClassStatus

        result = parsed[("original", "D")]
        assert result.status == DClassStatus.AVAILABLE
        assert result.has_nonstop
        assert result.seats == 9
        assert len(result.nonstop_flights) == 7
        assert result.booking_class == "D"

    def test_connection_legs_do_not_make_segment_available(self, parsed):
        """Nonstops D0, only LHR-BRU-HKG / LHR-MUC-HKG legs at D9."""
        from rtw.verify.models import DClassStatus

        result = parsed[("nonstops_d0", "D")]

        # All 11 rows still kept for display
        assert len(result.flights) == 11
        # Verdict comes from LHR-HKG rows only
        assert result.status == DClassStatus.NOT_AVAILABLE
        assert not result.has_nonstop
        assert result.nonstop_seats == 0
        # Both connections are complete LHR->HKG chains with D9 on each leg
        routes = [
            [(f.origin, f.destination) for f in legs]
            for legs in result.available_connections
        ]
        assert routes == [
            [("LHR", "BRU"), ("BRU", "HKG")],
            [("LHR", "MUC"), ("MUC", "HKG")],
        ]
        assert result.seats == 9  # connection signal, not a nonstop
        assert result.display_code == "D9* (2 conn)"

    def test_fixture_d0_nonstops_trigger_fallback_scan(self, parsed):
        """End to end: parsed D0-nonstop result makes the verifier scan B."""
        from rtw.scraper.cache import ScrapeCache
        from rtw.verify.models import SegmentVerification, VerifyOption
        from rtw.verify.verifier import DClassVerifier

        primary = parsed[("nonstops_d0", "D")]
        # B-class page: reuse the unedited fixture (nonstops with seats)
        fallback = parsed[("original", "D")].model_copy(update={"booking_class": "B"})

        class _StubScraper:
            """Stands in for the network call; returns parsed fixture data."""

            def __init__(self):
                self.classes = []

            def check_availability(self, origin, dest, date, carrier, booking_class):
                self.classes.append(booking_class)
                return (primary if booking_class == "D" else fallback).model_copy()

        import tempfile

        scraper = _StubScraper()
        with tempfile.TemporaryDirectory() as tmp:
            verifier = DClassVerifier(
                scraper=scraper, cache=ScrapeCache(cache_dir=Path(tmp))
            )
            option = VerifyOption(option_id=1, segments=[SegmentVerification(
                index=0, segment_type="FLOWN", origin="LHR", destination="HKG",
                carrier="CX", target_date=_FIXTURE_DATE,
            )])
            result = verifier.verify_option(option, no_cache=True)

        assert scraper.classes == ["D", "B"]
        seg = result.segments[0]
        assert not seg.dclass.has_nonstop
        assert seg.fallback is not None and seg.fallback.has_nonstop
        assert result.confirmed == 0
        assert result.fallback_bookable == 1


class TestRetriesExhaustedResult:
    def test_error_result_carries_booking_class(self, monkeypatch):
        """After retries run out the ERROR result names the class scanned."""
        import rtw.scraper.expertflyer as ef
        from rtw.verify.models import DClassStatus

        monkeypatch.setattr(ef, "_get_credentials", lambda: ("user", "pw"))
        monkeypatch.setattr(ef.time, "sleep", lambda s: None)
        scraper = ExpertFlyerScraper()
        monkeypatch.setattr(scraper, "_ensure_logged_in", lambda: None)

        def _fail(*args, **kwargs):
            raise ScrapeError("Results table not found", error_type="PARSE_ERROR")

        monkeypatch.setattr(scraper, "_fetch_and_parse", _fail)
        result = scraper.check_availability(
            "JFK", "LAX", datetime.date(2026, 3, 10), carrier="AA", booking_class="H"
        )
        assert result.status == DClassStatus.ERROR
        assert result.booking_class == "H"
        assert result.display_code == "H!"
