"""Tests for rtw.airports shared module."""

from rtw.airports import airports_db


class TestAirportsDB:
    def test_airports_db_is_populated(self):
        """Airport database should have 5000+ entries."""
        assert len(airports_db) > 5000

    def test_airports_db_contains_common_codes(self):
        """Database should contain major hub codes."""
        for code in ["JFK", "LHR", "NRT", "SYD", "CAI"]:
            assert code in airports_db, f"{code} missing from airports_db"
