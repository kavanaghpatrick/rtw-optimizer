"""Tests for country helpers and open-jaw validation."""

from rtw.continents import (
    get_country,
    get_country_name,
    MIDDLE_EAST_COUNTRIES,
    AFRICA_COUNTRIES,
    check_open_jaw_permitted,
)


class TestGetCountry:
    def test_known_airports(self):
        assert get_country("SYD") == "AU"
        assert get_country("LHR") == "GB"
        assert get_country("JFK") == "US"
        assert get_country("NRT") == "JP"
        assert get_country("DOH") == "QA"

    def test_unknown_airport(self):
        assert get_country("ZZZ") is None

    def test_case_insensitive(self):
        assert get_country("syd") == "AU"
        assert get_country("Lhr") == "GB"


class TestGetCountryName:
    def test_known_countries(self):
        assert get_country_name("GB") == "United Kingdom"
        assert get_country_name("AU") == "Australia"
        assert get_country_name("US") == "United States"

    def test_unknown_falls_back(self):
        assert get_country_name("XX") == "XX"

    def test_case_insensitive(self):
        assert get_country_name("gb") == "United Kingdom"


class TestMiddleEastCountries:
    def test_contains_all_14(self):
        assert len(MIDDLE_EAST_COUNTRIES) == 14
        for code in ["QA", "AE", "SA", "BH", "KW", "OM", "JO", "IL", "YE", "IQ", "LB", "SY", "PS", "EG"]:
            assert code in MIDDLE_EAST_COUNTRIES

    def test_does_not_contain_turkey(self):
        assert "TR" not in MIDDLE_EAST_COUNTRIES


class TestAfricaCountries:
    def test_non_empty(self):
        assert len(AFRICA_COUNTRIES) > 0

    def test_contains_key_countries(self):
        assert "ZA" in AFRICA_COUNTRIES
        assert "KE" in AFRICA_COUNTRIES
        assert "ET" in AFRICA_COUNTRIES


class TestCheckOpenJawPermitted:
    def test_same_country_uk(self):
        result = check_open_jaw_permitted("LHR", "MAN")
        assert result.permitted is True
        assert "United Kingdom" in result.reason

    def test_us_canada(self):
        result = check_open_jaw_permitted("JFK", "YYZ")
        assert result.permitted is True

    def test_not_permitted(self):
        result = check_open_jaw_permitted("LHR", "CDG")
        assert result.permitted is False

    def test_middle_east(self):
        result = check_open_jaw_permitted("DOH", "AMM")
        assert result.permitted is True
        assert "Middle East" in result.reason

    def test_africa(self):
        result = check_open_jaw_permitted("JNB", "NBO")
        assert result.permitted is True
        assert "Africa" in result.reason

    def test_hk_china(self):
        result = check_open_jaw_permitted("HKG", "PVG")
        assert result.permitted is True

    def test_my_sg(self):
        result = check_open_jaw_permitted("KUL", "SIN")
        assert result.permitted is True

    def test_maldives_sri_lanka(self):
        result = check_open_jaw_permitted("MLE", "CMB")
        assert result.permitted is True

    def test_unknown_airport(self):
        result = check_open_jaw_permitted("ZZZ", "LHR")
        assert result.permitted is False
