"""Tests for rtw.verify.models nonstop filtering."""

import datetime

import pytest

from rtw.verify.models import (
    DClassResult,
    DClassStatus,
    FlightAvailability,
    SegmentVerification,
    VerifyResult,
)

_DATE = datetime.date(2026, 9, 15)


def _flight(origin, dest, seats, stops=0, carrier=None, flight_number=None):
    """Build a FlightAvailability for testing."""
    return FlightAvailability(
        carrier=carrier,
        flight_number=flight_number,
        origin=origin,
        destination=dest,
        seats=seats,
        stops=stops,
    )


def _dclass(origin, dest, flights, carrier="QR", status=DClassStatus.AVAILABLE):
    """Build a DClassResult with given flights."""
    best = max((f.seats for f in flights), default=0)
    return DClassResult(
        status=status,
        seats=best,
        carrier=carrier,
        origin=origin,
        destination=dest,
        target_date=_DATE,
        flights=flights,
    )


# ------------------------------------------------------------------
# DClassResult.nonstop_flights
# ------------------------------------------------------------------


class TestNonstopFlights:
    """DClassResult.nonstop_flights property."""

    def test_filters_to_nonstop_only(self):
        dc = _dclass("LAX", "HEL", [
            _flight("LAX", "HEL", 9, stops=2),  # multi-stop
            _flight("LAX", "JFK", 7, stops=0),   # wrong destination
            _flight("LAX", "HEL", 5, stops=0),   # nonstop — keep
        ])
        ns = dc.nonstop_flights
        assert len(ns) == 1
        assert ns[0].seats == 5
        assert ns[0].stops == 0

    def test_empty_when_no_nonstops(self):
        dc = _dclass("LAX", "HEL", [
            _flight("LAX", "HEL", 9, stops=2),
            _flight("LAX", "DFW", 7, stops=0),
            _flight("DFW", "HEL", 9, stops=0),
        ])
        assert dc.nonstop_flights == []

    def test_excludes_zero_seat_nonstops(self):
        dc = _dclass("DOH", "SYD", [
            _flight("DOH", "SYD", 0, stops=0),  # nonstop but sold out
            _flight("DOH", "SYD", 7, stops=1),  # 1-stop with seats
        ])
        assert dc.nonstop_flights == []

    def test_all_nonstops_returned(self):
        dc = _dclass("HND", "LAX", [
            _flight("HND", "LAX", 7, stops=0),
            _flight("HND", "LAX", 9, stops=0, flight_number="JL16"),
            _flight("HND", "LAX", 3, stops=0),
        ])
        assert len(dc.nonstop_flights) == 3

    def test_empty_flights_list(self):
        dc = _dclass("LHR", "HEL", [])
        assert dc.nonstop_flights == []


# ------------------------------------------------------------------
# DClassResult.has_nonstop / nonstop_seats
# ------------------------------------------------------------------


class TestHasNonstop:
    def test_true_when_nonstop_exists(self):
        dc = _dclass("DOH", "SYD", [
            _flight("DOH", "SYD", 9, stops=0),
        ])
        assert dc.has_nonstop is True

    def test_false_when_connections_only(self):
        dc = _dclass("LAX", "HEL", [
            _flight("LAX", "HEL", 9, stops=2),
        ])
        assert dc.has_nonstop is False

    def test_false_when_no_flights(self):
        dc = _dclass("LHR", "JFK", [])
        assert dc.has_nonstop is False


class TestNonstopSeats:
    def test_returns_best_nonstop(self):
        dc = _dclass("HND", "LAX", [
            _flight("HND", "LAX", 7, stops=0),
            _flight("HND", "LAX", 9, stops=0),
            _flight("HND", "LAX", 3, stops=0),
        ])
        assert dc.nonstop_seats == 9

    def test_zero_when_no_nonstops(self):
        dc = _dclass("LAX", "HEL", [
            _flight("LAX", "HEL", 9, stops=2),
        ])
        assert dc.nonstop_seats == 0

    def test_ignores_connection_seats(self):
        dc = _dclass("LAX", "HEL", [
            _flight("LAX", "HEL", 9, stops=2),  # connection D9
            _flight("LAX", "HEL", 3, stops=0),  # nonstop D3
        ])
        assert dc.nonstop_seats == 3


# ------------------------------------------------------------------
# DClassResult.display_code
# ------------------------------------------------------------------


class TestDisplayCode:
    def test_nonstop_shows_ns(self):
        dc = _dclass("DOH", "SYD", [
            _flight("DOH", "SYD", 9, stops=0),
            _flight("DOH", "SYD", 7, stops=0),
        ])
        assert dc.display_code == "D9 (2 ns)"

    def test_connection_only_shows_star(self):
        dc = _dclass("LAX", "HEL", [
            _flight("LAX", "HEL", 9, stops=2),
            _flight("LAX", "DFW", 5, stops=0),
            _flight("DFW", "HEL", 9, stops=0),
        ])
        assert "*" in dc.display_code
        assert "conn" in dc.display_code

    def test_error_shows_bang(self):
        dc = DClassResult(
            status=DClassStatus.ERROR, carrier="QR",
            origin="DOH", destination="SYD", target_date=_DATE,
        )
        assert dc.display_code == "D!"

    def test_unknown_shows_question(self):
        dc = DClassResult(
            status=DClassStatus.UNKNOWN, carrier="QR",
            origin="DOH", destination="SYD", target_date=_DATE,
        )
        assert dc.display_code == "D?"

    def test_no_flights_shows_bare_seats(self):
        dc = DClassResult(
            status=DClassStatus.AVAILABLE, seats=5, carrier="QR",
            origin="DOH", destination="SYD", target_date=_DATE,
        )
        assert dc.display_code == "D5"


# ------------------------------------------------------------------
# VerifyResult.confirmed (nonstop-only)
# ------------------------------------------------------------------


def _seg(origin, dest, carrier, dclass_result):
    """Build a SegmentVerification for testing."""
    seg = SegmentVerification(
        index=0, segment_type="FLOWN",
        origin=origin, destination=dest, carrier=carrier,
    )
    seg.dclass = dclass_result
    return seg


class TestVerifyResultConfirmed:
    def test_counts_nonstop_only(self):
        result = VerifyResult(option_id=1, segments=[
            _seg("DOH", "SYD", "QR", _dclass("DOH", "SYD", [
                _flight("DOH", "SYD", 9, stops=0),  # nonstop
            ])),
            _seg("LAX", "HEL", "AY", _dclass("LAX", "HEL", [
                _flight("LAX", "HEL", 9, stops=2),  # connection only
            ])),
        ])
        assert result.confirmed == 1
        assert result.confirmed_any == 2
        assert result.fully_bookable is False

    def test_all_nonstop(self):
        result = VerifyResult(option_id=1, segments=[
            _seg("LHR", "HEL", "AY", _dclass("LHR", "HEL", [
                _flight("LHR", "HEL", 9, stops=0),
            ])),
            _seg("HEL", "DOH", "QR", _dclass("HEL", "DOH", [
                _flight("HEL", "DOH", 9, stops=0),
            ])),
        ])
        assert result.confirmed == 2
        assert result.fully_bookable is True

    def test_connection_only_segments(self):
        conn_dc = _dclass("LAX", "HEL", [
            _flight("LAX", "HEL", 9, stops=2),
        ])
        result = VerifyResult(option_id=1, segments=[
            _seg("DOH", "SYD", "QR", _dclass("DOH", "SYD", [
                _flight("DOH", "SYD", 9, stops=0),
            ])),
            _seg("LAX", "HEL", "AY", conn_dc),
        ])
        conn_segs = result.connection_only_segments
        assert len(conn_segs) == 1
        assert conn_segs[0].origin == "LAX"
        assert conn_segs[0].destination == "HEL"

    def test_surface_segments_ignored(self):
        surface_seg = SegmentVerification(
            index=0, segment_type="SURFACE",
            origin="NRT", destination="HND",
        )
        result = VerifyResult(option_id=1, segments=[
            surface_seg,
            _seg("HND", "LAX", "JL", _dclass("HND", "LAX", [
                _flight("HND", "LAX", 9, stops=0),
            ])),
        ])
        assert result.total_flown == 1
        assert result.confirmed == 1
