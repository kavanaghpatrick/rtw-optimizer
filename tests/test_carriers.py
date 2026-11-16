"""Tests for shared carrier booking class resolution."""

import pytest

from rtw.carriers import get_booking_class, get_fallback_class
from rtw.models import CabinClass


class TestGetBookingClass:
    """Test get_booking_class() for all carrier/cabin combinations."""

    def test_aa_business_returns_d(self):
        # AA's primary business RBD is D like every carrier; H is only fallback.
        assert get_booking_class("AA", CabinClass.BUSINESS) == "D"

    def test_aa_lowercase_returns_d(self):
        assert get_booking_class("aa", CabinClass.BUSINESS) == "D"

    def test_ba_business_returns_d(self):
        assert get_booking_class("BA", CabinClass.BUSINESS) == "D"

    def test_cx_business_returns_d(self):
        assert get_booking_class("CX", CabinClass.BUSINESS) == "D"

    def test_qr_business_returns_d(self):
        assert get_booking_class("QR", CabinClass.BUSINESS) == "D"

    def test_jl_business_returns_d(self):
        assert get_booking_class("JL", CabinClass.BUSINESS) == "D"

    def test_qf_business_returns_d(self):
        assert get_booking_class("QF", CabinClass.BUSINESS) == "D"

    def test_unknown_carrier_business_returns_d(self):
        assert get_booking_class("ZZ", CabinClass.BUSINESS) == "D"

    def test_economy_returns_l(self):
        assert get_booking_class("AA", CabinClass.ECONOMY) == "L"

    def test_economy_any_carrier_returns_l(self):
        assert get_booking_class("BA", CabinClass.ECONOMY) == "L"

    def test_first_returns_a(self):
        assert get_booking_class("AA", CabinClass.FIRST) == "A"

    def test_first_any_carrier_returns_a(self):
        assert get_booking_class("QF", CabinClass.FIRST) == "A"

    def test_none_carrier_returns_d(self):
        """Surface segments (carrier=None) return safe default."""
        assert get_booking_class(None, CabinClass.BUSINESS) == "D"

    def test_never_returns_none(self):
        """Function always returns a string, never None."""
        for carrier in [None, "AA", "BA", "ZZ"]:
            for cabin in CabinClass:
                result = get_booking_class(carrier, cabin)
                assert isinstance(result, str)
                assert len(result) == 1


class TestGetFallbackClass:
    """Test get_fallback_class() — the class to try when D is sold out."""

    def test_aa_fallback_is_h(self):
        assert get_fallback_class("AA", CabinClass.BUSINESS) == "H"

    def test_aa_lowercase_fallback_is_h(self):
        assert get_fallback_class("aa", CabinClass.BUSINESS) == "H"

    def test_non_aa_fallback_is_b(self):
        for carrier in ("BA", "CX", "QF", "QR", "JL", "AY", "MH"):
            assert get_fallback_class(carrier, CabinClass.BUSINESS) == "B"

    def test_economy_has_no_fallback(self):
        assert get_fallback_class("AA", CabinClass.ECONOMY) is None

    def test_first_falls_back_to_y(self):
        """§5(b) NOTE: First Class fares may book Y when the class is unavailable."""
        for carrier in ("BA", "QR", "IB", "AS", "AY"):
            assert get_fallback_class(carrier, CabinClass.FIRST) == "Y"

    def test_first_no_fallback_when_primary_already_y(self):
        """AY domestic First already books Y, so there is nothing to fall back to."""
        assert get_fallback_class("AY", CabinClass.FIRST, "HEL", "OUL") is None

    def test_ay_domestic_business_still_falls_back_to_b(self):
        assert get_fallback_class("AY", CabinClass.BUSINESS, "HEL", "OUL") == "B"

    def test_surface_has_no_fallback(self):
        assert get_fallback_class(None, CabinClass.BUSINESS) is None

    def test_unknown_carrier_has_no_fallback(self):
        assert get_fallback_class("ZZ", CabinClass.BUSINESS) is None


class TestRule3015BookingCodeTable:
    """Rule 3015 §5(b) booking codes, 27 FEB 2026 filing."""

    @pytest.mark.parametrize("carrier", ["AA", "BA", "CX", "MH", "QF", "QR", "JL", "WY"])
    def test_first_a_carriers(self, carrier):
        assert get_booking_class(carrier, CabinClass.FIRST, "LHR", "JFK") == "A"

    @pytest.mark.parametrize("carrier", ["AS", "AT", "FJ", "IB", "RJ", "UL"])
    def test_first_d_carriers(self, carrier):
        assert get_booking_class(carrier, CabinClass.FIRST) == "D"

    def test_ib_first_is_d(self):
        assert get_booking_class("IB", CabinClass.FIRST, "MAD", "JFK") == "D"

    def test_as_first_is_d(self):
        assert get_booking_class("AS", CabinClass.FIRST, "JFK", "SEA") == "D"

    def test_ba_first_is_a(self):
        assert get_booking_class("BA", CabinClass.FIRST, "LHR", "JFK") == "A"

    def test_ay_domestic_first_and_business_are_y(self):
        assert get_booking_class("AY", CabinClass.FIRST, "HEL", "OUL") == "Y"
        assert get_booking_class("AY", CabinClass.BUSINESS, "HEL", "OUL") == "Y"
        assert get_booking_class("AY", CabinClass.ECONOMY, "HEL", "OUL") == "L"

    def test_ay_international_first_and_business_are_d(self):
        assert get_booking_class("AY", CabinClass.FIRST, "HEL", "JFK") == "D"
        assert get_booking_class("AY", CabinClass.BUSINESS, "HEL", "JFK") == "D"

    def test_ay_without_airports_uses_international_row(self):
        assert get_booking_class("AY", CabinClass.BUSINESS) == "D"

    def test_nu_international_is_e(self):
        assert get_booking_class("NU", CabinClass.FIRST, "OKA", "TPE") == "E"
        assert get_booking_class("NU", CabinClass.BUSINESS, "OKA", "TPE") == "E"
        assert get_booking_class("NU", CabinClass.ECONOMY, "OKA", "TPE") == "L"

    def test_nu_domestic_books_like_jl(self):
        assert get_booking_class("NU", CabinClass.FIRST, "OKA", "HND") == "A"
        assert get_booking_class("NU", CabinClass.BUSINESS, "OKA", "HND") == "D"

    def test_issue_itinerary_first_classes(self):
        """AONE3 HEL-OUL(AY)-MAD(IB)-JFK(IB)-SEA(AS)-NRT(JL)-HEL(AY)."""
        legs = [
            ("AY", "HEL", "OUL"),
            ("IB", "OUL", "MAD"),
            ("IB", "MAD", "JFK"),
            ("AS", "JFK", "SEA"),
            ("JL", "SEA", "NRT"),
            ("AY", "NRT", "HEL"),
        ]
        got = [get_booking_class(c, CabinClass.FIRST, a, b) for c, a, b in legs]
        assert got == ["Y", "D", "D", "D", "A", "D"]
