"""Continent coverage: every airport must land in the right oneworld continent.

Sources: 01-fare-rules.md §3 (continent definitions), §19 (Guam = TC3 South
East Asia), and the IATA First Schedule sub-area lists cited in
rtw/data/continents.yaml.
"""

from pathlib import Path

import pytest
import yaml

from rtw.airports import airports_db
from rtw.continents import (
    AFRICA_COUNTRIES,
    MIDDLE_EAST_COUNTRIES,
    _COUNTRIES,
    _COUNTRY_TO_CONTINENT,
    get_continent,
)
from rtw.models import Continent, Itinerary
from rtw.validator import Validator, build_context

FIXTURES = Path(__file__).parent / "fixtures"

with open(FIXTURES / "oneworld_stations.yaml") as _f:
    _STATIONS: dict[str, list[str]] = yaml.safe_load(_f)

_STATION_CASES = [(apt, cont) for cont, apts in _STATIONS.items() for apt in apts]

# Countries the rule text does not place, left unmapped on purpose so the
# validator reports them instead of guessing. Keep in sync with the comment at
# the top of the countries block in rtw/data/continents.yaml.
_DELIBERATELY_UNMAPPED = {"AQ", "EH", "FK", "GL", "SH", "SS", "TL", "UM"}


class TestOneworldStationCoverage:
    @pytest.mark.parametrize("airport,expected", _STATION_CASES)
    def test_station_resolves_to_expected_continent(self, airport, expected):
        assert airport in airports_db, f"{airport} missing from airportsdata"
        assert get_continent(airport) == Continent(expected)


class TestCountryCoverage:
    def test_every_airportsdata_country_is_mapped_or_documented(self):
        """Every country with an IATA airport resolves, apart from the
        documented rule-silent list. A new country in airportsdata fails here
        until someone decides where it belongs."""
        countries = {info["country"] for info in airports_db.values()}
        handled = set(_COUNTRY_TO_CONTINENT) | {"RU"} | _DELIBERATELY_UNMAPPED
        assert sorted(countries - handled) == []

    def test_unmapped_list_is_really_unmapped(self):
        assert not (_DELIBERATELY_UNMAPPED & set(_COUNTRY_TO_CONTINENT))

    def test_every_airport_in_mapped_country_resolves(self):
        missing = [
            code
            for code, info in airports_db.items()
            if info["country"] not in _DELIBERATELY_UNMAPPED and get_continent(code) is None
        ]
        assert missing == []

    def test_deliberately_unmapped_airport_returns_none(self):
        # Nuuk, Greenland: IATA Area 1 but the rule text names no continent.
        assert get_continent("GOH") is None


class TestRegressionPoints:
    @pytest.mark.parametrize("airport", ["ANU", "GCM", "AUA", "BGI", "SXM", "CUR"])
    def test_caribbean_is_north_america(self, airport):
        assert get_continent(airport) == Continent.N_AMERICA

    @pytest.mark.parametrize("airport", ["LCA", "MLA", "KEF", "RIX", "TLL", "VNO", "BEY"])
    def test_europe_middle_east(self, airport):
        assert get_continent(airport) == Continent.EU_ME

    @pytest.mark.parametrize("airport", ["MFM", "GUM", "SPN", "ROR", "MAJ", "PNI"])
    def test_tc3_south_east_asia(self, airport):
        assert get_continent(airport) == Continent.ASIA

    @pytest.mark.parametrize("airport", ["RAR", "PPG", "INU"])
    def test_south_west_pacific(self, airport):
        assert get_continent(airport) == Continent.SWP


class TestRussiaUrals:
    @pytest.mark.parametrize("airport", ["VVO", "OVB", "KHV", "TJM"])
    def test_east_of_urals_is_asia(self, airport):
        assert get_continent(airport) == Continent.ASIA

    @pytest.mark.parametrize("airport", ["LED", "SVO", "DME", "KGD", "UFA"])
    def test_west_of_urals_is_europe(self, airport):
        assert get_continent(airport) == Continent.EU_ME

    @pytest.mark.parametrize("airport", ["SVX", "CEK", "VKT"])
    def test_boundary_overrides_stay_europe(self, airport):
        assert get_continent(airport) == Continent.EU_ME


class TestRegionalSetsFromYaml:
    def test_africa_set_matches_yaml(self):
        assert AFRICA_COUNTRIES == frozenset(_COUNTRIES["Africa"])

    def test_africa_set_matches_get_continent(self):
        # Johannesburg and Luanda (formerly only in the hardcoded set) agree.
        assert "AO" in AFRICA_COUNTRIES
        assert get_continent("LAD") == Continent.AFRICA
        assert get_continent("JNB") == Continent.AFRICA

    def test_north_africa_not_in_africa_set(self):
        for cc in ("EG", "LY", "MA", "TN", "DZ", "SD"):
            assert cc not in AFRICA_COUNTRIES

    def test_middle_east_all_resolve_to_eu_me(self):
        for cc in MIDDLE_EAST_COUNTRIES:
            assert _COUNTRY_TO_CONTINENT[cc] == "EU_ME"


class TestCaribbeanItinerary:
    """LHR-ANU-MIA-LAX-HKG-LHR used to fail with 'No Atlantic ocean crossing'
    and count Antigua as a Europe stopover."""

    @pytest.fixture
    def itinerary(self, load_yaml):
        return Itinerary(**load_yaml("caribbean_anu_done3.yaml"))

    def test_lhr_anu_is_intercontinental(self, itinerary):
        ctx = build_context(itinerary)
        assert ctx.is_intercontinental[0] is True
        assert ctx.segment_continents[0] == Continent.N_AMERICA
        assert Continent.EU_ME not in ctx.stopovers_per_continent
        assert ctx.unknown_continent_airports == {}

    def test_validates_clean(self, itinerary):
        report = Validator().validate(itinerary)
        assert report.violations == []
