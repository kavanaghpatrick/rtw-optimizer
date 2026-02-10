"""Tests for rtw scan-dates CLI command."""

import datetime
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rtw.cli import app


runner = CliRunner()


def _mock_dclass_result(seats=5, nonstop_seats=3, has_nonstop=True, flight_number="QR739"):
    """Build a mock DClassResult."""
    from rtw.verify.models import DClassResult, DClassStatus, FlightAvailability

    ns_flight = FlightAvailability(
        carrier="QR",
        flight_number=flight_number,
        seats=nonstop_seats,
        stops=0,
        booking_class="D",
    )
    conn_flight = FlightAvailability(
        carrier="QR",
        flight_number="QR740",
        seats=seats,
        stops=1,
        booking_class="D",
    )

    flights = []
    if has_nonstop and nonstop_seats > 0:
        flights.append(ns_flight)
    flights.append(conn_flight)

    return DClassResult(
        status=DClassStatus.AVAILABLE if seats > 0 else DClassStatus.NOT_AVAILABLE,
        seats=max(seats, nonstop_seats),
        carrier="QR",
        origin="DOH",
        destination="LAX",
        target_date=datetime.date(2026, 4, 15),
        booking_class="D",
        checked_at=datetime.datetime.now(),
        flights=flights,
    )


class TestScanDatesArgs:
    def test_help(self):
        result = runner.invoke(app, ["scan-dates", "--help"])
        assert result.exit_code == 0
        assert "Scan a date range" in result.output

    def test_invalid_from_date(self):
        result = runner.invoke(app, ["scan-dates", "DOH", "LAX", "QR", "--from", "bad-date"])
        assert result.exit_code == 2

    def test_invalid_to_date(self):
        result = runner.invoke(app, ["scan-dates", "DOH", "LAX", "QR", "--from", "2026-04-01", "--to", "bad"])
        assert result.exit_code == 2

    def test_to_before_from(self):
        result = runner.invoke(app, ["scan-dates", "DOH", "LAX", "QR", "--from", "2026-04-30", "--to", "2026-04-01"])
        assert result.exit_code == 2

    def test_invalid_dow(self):
        result = runner.invoke(app, ["scan-dates", "DOH", "LAX", "QR", "--from", "2026-04-01", "--to", "2026-04-10", "--dow", "xyz"])
        assert result.exit_code == 2


class TestScanDatesExecution:
    @patch("rtw.scraper.expertflyer.ExpertFlyerScraper")
    def test_basic_scan(self, mock_scraper_cls):
        mock_scraper = MagicMock()
        mock_scraper_cls.return_value = mock_scraper
        mock_scraper.check_availability.return_value = _mock_dclass_result()

        result = runner.invoke(app, [
            "scan-dates", "DOH", "LAX", "QR",
            "--from", "2026-04-15", "--to", "2026-04-17",
        ])
        assert result.exit_code == 0
        assert "DOH-LAX" in result.output
        assert mock_scraper.check_availability.call_count == 3  # 15, 16, 17

    @patch("rtw.scraper.expertflyer.ExpertFlyerScraper")
    def test_dow_filter_reduces_dates(self, mock_scraper_cls):
        mock_scraper = MagicMock()
        mock_scraper_cls.return_value = mock_scraper
        mock_scraper.check_availability.return_value = _mock_dclass_result()

        result = runner.invoke(app, [
            "scan-dates", "DOH", "LAX", "QR",
            "--from", "2026-04-13", "--to", "2026-04-19",  # Mon-Sun
            "--dow", "mon,wed",
        ])
        assert result.exit_code == 0
        # Only Mon (13) and Wed (15) should be checked
        assert mock_scraper.check_availability.call_count == 2

    @patch("rtw.scraper.expertflyer.ExpertFlyerScraper")
    def test_nonstop_only_filters(self, mock_scraper_cls):
        mock_scraper = MagicMock()
        mock_scraper_cls.return_value = mock_scraper
        # Return result with no nonstop
        mock_scraper.check_availability.return_value = _mock_dclass_result(
            seats=5, nonstop_seats=0, has_nonstop=False
        )

        result = runner.invoke(app, [
            "scan-dates", "DOH", "LAX", "QR",
            "--from", "2026-04-15", "--to", "2026-04-17",
            "--nonstop-only",
        ])
        assert result.exit_code == 0
        assert "0/3 dates have nonstop D-class" in result.output

    @patch("rtw.scraper.expertflyer.ExpertFlyerScraper")
    def test_summary_with_nonstop(self, mock_scraper_cls):
        mock_scraper = MagicMock()
        mock_scraper_cls.return_value = mock_scraper
        mock_scraper.check_availability.return_value = _mock_dclass_result(
            seats=9, nonstop_seats=9, has_nonstop=True
        )

        result = runner.invoke(app, [
            "scan-dates", "DOH", "LAX", "QR",
            "--from", "2026-04-15", "--to", "2026-04-16",
        ])
        assert result.exit_code == 0
        assert "have nonstop D-class" in result.output

    @patch("rtw.scraper.expertflyer.ExpertFlyerScraper")
    def test_login_failure(self, mock_scraper_cls):
        mock_scraper = MagicMock()
        mock_scraper_cls.return_value = mock_scraper
        mock_scraper.check_availability.return_value = None

        result = runner.invoke(app, [
            "scan-dates", "DOH", "LAX", "QR",
            "--from", "2026-04-15", "--to", "2026-04-16",
        ])
        assert result.exit_code == 2

    @patch("rtw.scraper.expertflyer.ExpertFlyerScraper")
    def test_uppercase_args(self, mock_scraper_cls):
        mock_scraper = MagicMock()
        mock_scraper_cls.return_value = mock_scraper
        mock_scraper.check_availability.return_value = _mock_dclass_result()

        result = runner.invoke(app, [
            "scan-dates", "doh", "lax", "qr",
            "--from", "2026-04-15", "--to", "2026-04-15",
        ])
        assert result.exit_code == 0
        call_args = mock_scraper.check_availability.call_args
        assert call_args[0][0] == "DOH"
        assert call_args[0][1] == "LAX"
