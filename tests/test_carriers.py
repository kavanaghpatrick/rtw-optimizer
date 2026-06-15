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

    def test_first_has_no_fallback(self):
        assert get_fallback_class("BA", CabinClass.FIRST) is None

    def test_surface_has_no_fallback(self):
        assert get_fallback_class(None, CabinClass.BUSINESS) is None

    def test_unknown_carrier_has_no_fallback(self):
        assert get_fallback_class("ZZ", CabinClass.BUSINESS) is None
