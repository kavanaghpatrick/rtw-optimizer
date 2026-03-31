# Test Suite Analysis

Last updated: 2026-03-30

## Summary

| Metric | Value |
|--------|-------|
| Total tests | 1,208 |
| Total test files | 67 |
| Total lines of test code | ~15,300 |
| Fixture YAML files | 40 |
| Test subdirectories | 5 (`test_rules/`, `test_scraper/`, `test_search/`, `test_verify/`, `test_nonstop/`) |
| Framework | pytest 8+ with Hypothesis (property-based), pytest-asyncio |
| Runner command | `uv run pytest` |

## File Organization

Tests mirror the source module structure. Top-level test files cover top-level `rtw/*.py` modules, while test subdirectories cover `rtw/` subpackages.

### Top-level tests (`tests/*.py`)

| Test File | Source Module | Tests | Purpose |
|-----------|--------------|------:|---------|
| `test_validator.py` | `rtw/validator.py` | 21 | Rule discovery, full validation pipeline |
| `test_models.py` | `rtw/models.py` | 32 | Pydantic model creation, validation, serialization |
| `test_cost.py` | `rtw/cost.py` | 43 | Base fare lookup, YQ surcharges, origin comparison |
| `test_ntp.py` | `rtw/ntp.py` | 17 | BA New Tier Points calculation |
| `test_value.py` | `rtw/value.py` | 7 | Per-segment value rating |
| `test_booking.py` | `rtw/booking.py` | 47 | Phone script + GDS command generation |
| `test_output.py` | `rtw/output/` | 64 | Rich, plain, and JSON formatters |
| `test_continents_country.py` | `rtw/continents.py` | 19 | Airport-to-continent mapping, country helpers |
| `test_distance.py` | `rtw/distance.py` | 9 | Great-circle distance |
| `test_airports.py` | `rtw/airports.py` | 2 | Airport data loader |
| `test_carriers.py` | `rtw/data/carriers.yaml` | 14 | Carrier data integrity |
| `test_verify_models.py` | `rtw/verify/models.py` | 20 | Verify module data models |

### CLI tests (`tests/*.py`)

| Test File | Tests | Purpose |
|-----------|------:|---------|
| `test_cli_e2e.py` | 31 | End-to-end CLI via `typer.testing.CliRunner` |
| `test_cli_build.py` | 19 | `rtw build` command |
| `test_cli_verify.py` | 17 | `rtw login`, `rtw verify`, `--verify-dclass` commands |
| `test_cli_scan_dates.py` | 11 | `rtw scan-dates` command |

### Rules tests (`tests/test_rules/`)

Each file tests one rule module in `rtw/rules/`. The 23 test files cover all 31 rules across 10 rule source files:

| Test File | Source Rule File | Tests | Rules Tested |
|-----------|-----------------|------:|--------------|
| `test_direction.py` | `rules/direction.py` | 12 | DirectionOfTravelRule, OceanCrossingRule |
| `test_direction_citypair.py` | `rules/direction.py` | 9 | City-pair direction constraints |
| `test_segments.py` | `rules/segments.py` | 13 | MaxSegmentRule, MinSegmentRule |
| `test_carriers.py` | `rules/carriers.py` | 12 | CarrierEligibilityRule |
| `test_codeshare.py` | `rules/carriers.py` | 11 | Codeshare rules (JQ, WY, S7) |
| `test_country.py` | `rules/country.py` | 16 | CountryLimitRule |
| `test_geography.py` | `rules/geography.py` | 9 | Geography rules |
| `test_geography_au.py` | `rules/geography.py` | 10 | Australia transcon rules |
| `test_hemisphere.py` | `rules/hemisphere.py` | 19 | Hemisphere crossing rules |
| `test_intercontinental.py` | `rules/intercontinental.py` | 31 | Intercontinental crossing limits |
| `test_stopovers.py` | `rules/stopovers.py` | 22 | Min stopovers, origin continent, same-city limits |
| `test_surface.py` | `rules/surface.py` | 1 | Surface sector rules |
| `test_surface_first_segment.py` | `rules/surface.py` | 5 | Surface as first segment |
| `test_surface_transoceanic.py` | `rules/surface.py` | 9 | Transoceanic surface restrictions |
| `test_validity.py` | `rules/validity.py` | 11 | Ticket validity period rules |
| `test_ticket_validity.py` | `rules/validity.py` | 9 | Ticket validity edge cases |
| `test_open_jaw.py` | `rules/geography.py` | 16 | Open-jaw validation |
| `test_implicit_asia.py` | `rules/geography.py` | 10 | Implicit Asia counting |
| `test_married.py` | `rules/married.py` | 6 | Married segment pattern detection |
| `test_via_counting.py` | `rules/segments.py` | 10 | Via/through-flight segment counting |
| `test_framework.py` | `rules/base.py` | 20 | Rule engine framework, continent classifier |
| `test_fixture_validation.py` | (cross-cutting) | 15 | Challenge fixtures through full validator |

### Scraper tests (`tests/test_scraper/`)

| Test File | Tests | Purpose |
|-----------|------:|---------|
| `test_serpapi_flights.py` | 67 | SerpAPI Google Flights integration |
| `test_google_flights.py` | 59 | fast-flights Google Flights scraper |
| `test_batch.py` | 8 | Async batch scraping |
| `test_cache.py` | 11 | Scrape result caching |
| `test_expertflyer.py` | 11 | ExpertFlyer session-based scraper |

### Search tests (`tests/test_search/`)

| Test File | Tests | Purpose |
|-----------|------:|---------|
| `test_scorer.py` | 20 | Route scoring algorithm |
| `test_generator.py` | 18 | Route candidate generation |
| `test_cli.py` | 17 | Search CLI commands |
| `test_availability.py` | 17 | Availability checking |
| `test_query.py` | 16 | Search query parsing |
| `test_display.py` | 16 | Search result display |
| `test_hubs.py` | 14 | Hub airport data |
| `test_integration.py` | 11 | Search pipeline integration |
| `test_exporter.py` | 9 | Result export |

### Verify tests (`tests/test_verify/`)

| Test File | Tests | Purpose |
|-----------|------:|---------|
| `test_models.py` | 34 | Verify data models |
| `test_verifier.py` | 14 | Verification orchestrator |
| `test_parser.py` | 14 | ExpertFlyer HTML parser |
| `test_state.py` | 8 | Verification state management |
| `test_session.py` | 6 | Session handling |
| `test_integration.py` | 5 | End-to-end verification |

### Nonstop tests (`tests/test_nonstop/`)

| Test File | Tests | Purpose |
|-----------|------:|---------|
| `test_checker.py` | 42 | Nonstop route verification |
| `test_cli.py` | 20 | Nonstop CLI commands |

### Special-purpose tests

| Test File | Tests | Purpose |
|-----------|------:|---------|
| `test_integration.py` | 51 | Full pipeline: validate + cost + NTP + value + booking against V3 fixture |
| `test_new_fixtures.py` | 26 | 5 real-world FlyerTalk/oneworld itineraries |
| `test_fuzz.py` | 9 | Hypothesis property-based fuzzing |
| `test_fare_comparison.py` | 34 | Cross-origin fare comparison |
| `test_smoke.py` | 3 | Basic project sanity checks |

## Fixture Patterns

### YAML fixtures (`tests/fixtures/`)

40 YAML files representing real and synthetic itineraries. They fall into categories:

**Valid itineraries (reference routings):**
- `valid_v3.yaml` -- Primary reference: CAI DONE4 eastbound, 16 segments
- `minimal_valid.yaml` -- Simplest valid: LHR DONE4 eastbound, 7 segments, 0 warnings
- `done3_cai_eastbound.yaml`, `lone3_osl_westbound.yaml` -- 3-continent variants

**Invalid itineraries (negative testing):**
- `invalid_qr_first.yaml` -- QR first class (not allowed)
- `invalid_hawaii_backtrack.yaml` -- Backtracking violation
- `invalid_too_many_segments.yaml` -- Exceeds 16-segment limit

**Real-world itineraries (sourced from FlyerTalk, oneworld.com, Karryon):**
- `flyertalk_bud_westbound.yaml` -- BUD DONE5 westbound from FlyerTalk
- `flyertalk_hnd_first.yaml` -- HND first class from FlyerTalk guide
- `flyertalk_jfk_eastbound.yaml` -- JFK eastbound from FlyerTalk
- `oneworld_lhr_eastbound.yaml` -- Official oneworld sample
- `karryon_syd_6cont.yaml` -- SYD 6-continent from Karryon

**Challenge fixtures (edge cases for specific rules):**
- `challenge_au_transcon_gauntlet.yaml` -- Australia transcon edge cases
- `challenge_doh_double_count.yaml` -- DOH double-counting trap
- `challenge_transoceanic_surface.yaml` -- Transoceanic surface ban
- `challenge_uk_country_trap.yaml` -- UK country-limit trap
- `challenge_us_exception_stress.yaml` -- US exception stress test

**Rule-specific fixtures:**
- `rule_4c_open_jaw.yaml`, `rule_4f_country_limit.yaml`, `rule_4i_surface_ban.yaml`, etc.
- Named after specific Rule 3015 sub-clauses

**HTML fixtures:**
- `ef_results_lhr_hkg_d.html` -- Real ExpertFlyer results page for HTML parser testing

### conftest.py helpers

The top-level `tests/conftest.py` provides:

```python
# Fixture loader factory
@pytest.fixture
def load_yaml():
    def _load(name: str) -> dict:
        path = FIXTURES_DIR / name
        with open(path) as f:
            return yaml.safe_load(f)
    return _load

# Pre-loaded fixtures as raw dicts
@pytest.fixture
def v3_itinerary(load_yaml):        # Primary reference routing
def qr_first_itinerary(load_yaml):  # Invalid QR first
def hawaii_backtrack_itinerary(load_yaml):  # Invalid backtrack
def too_many_segments_itinerary(load_yaml): # Invalid 17 segments
def minimal_valid_itinerary(load_yaml):     # Minimal valid
def done3_itinerary(load_yaml):     # DONE3 3-continent
def lone3_itinerary(load_yaml):     # LONE3 3-continent
```

Scraper tests have their own `tests/test_scraper/conftest.py` that auto-disables rate limiting:

```python
@pytest.fixture(autouse=True)
def _no_rate_limit(monkeypatch):
    monkeypatch.setattr("rtw.scraper.serpapi_flights._rate_limit", lambda: None)
```

## Itinerary Construction Patterns

Tests construct itineraries in three ways, from most common to least:

### 1. Load from YAML fixture (integration/fixture tests)

Used for realistic, multi-segment itineraries. The YAML is loaded as a raw dict, then parsed into a Pydantic model:

```python
def _load(name: str) -> Itinerary:
    with open(FIXTURES_DIR / name) as f:
        return Itinerary(**yaml.safe_load(f))
```

### 2. Inline programmatic construction (unit tests)

Most rule tests build minimal itineraries in-line with a helper function. This is the dominant pattern in `test_rules/`:

```python
def _make_itinerary(segments_data, origin="CAI"):
    ticket = Ticket(type="DONE4", cabin="business", origin=origin)
    segments = [Segment(**s) for s in segments_data]
    return Itinerary(ticket=ticket, segments=segments)

# Usage:
segs = [
    {"from": "CAI", "to": "NRT", "carrier": "QR"},
    {"from": "NRT", "to": "LAX", "carrier": "JL"},
    {"from": "LAX", "to": "CAI", "carrier": "BA"},
]
itin = _make_itinerary(segs)
```

Each test file defines its own `_make_itinerary()` helper (not shared via conftest) because different modules need different default ticket parameters.

### 3. Full model construction (model/integration tests)

Used in `test_integration.py` for constructing itineraries with all fields specified:

```python
Itinerary(
    ticket=Ticket(type="DONE4", cabin="business", origin="LHR"),
    segments=[
        Segment(**{"from": "LHR", "to": "NRT", "carrier": "BA",
                   "date": "2026-04-01", "type": "stopover"}),
        ...
    ],
)
```

## Testing Philosophy

### The "no mocks" policy

From CLAUDE.md: *"NEVER use mocks for API responses -- tests use real data from tests/fixtures/. Mocks only for credentials and external service calls."*

This is enforced in practice:

**What gets mocked (only these categories):**
- **Credentials**: `keyring.get_password`, `_get_credentials` -- prevents tests from touching the system keyring
- **External API calls**: `search_fast_flights`, `search_serpapi`, HTTP requests -- prevents tests from calling Google, SerpAPI, or ExpertFlyer
- **Environment variables**: `monkeypatch.setenv("SERPAPI_API_KEY", ...)` -- tests API key detection without real keys
- **Rate limiters**: `_rate_limit` disabled via autouse fixture in scraper tests

**What is NEVER mocked:**
- Validation logic (all 31 rules run against real data)
- Cost estimation (uses real fares.yaml data)
- NTP calculation (uses real distance + carrier data)
- Model construction and serialization
- Continent/geography classification
- HTML parsing (uses real captured HTML fixtures)

The HTML fixture `ef_results_lhr_hkg_d.html` is a real captured ExpertFlyer results page, so the parser tests verify against actual production HTML structure.

**Where mock usage is concentrated:**
- 14 out of 67 test files use mocks (21%)
- 181 total mock/monkeypatch occurrences
- Heaviest mock usage: `test_scraper/test_serpapi_flights.py` (50 occurrences), `test_nonstop/test_checker.py` (36), `test_search/test_availability.py` (25), `test_search/test_cli.py` (20)

### Property-based testing (Hypothesis)

`test_fuzz.py` uses Hypothesis to generate random itineraries and verify invariants:
- Custom strategies for airport codes (50/50 real IATA vs random 3-letter)
- Custom strategies for carrier codes, segment types, ticket types
- Tests that the validator never crashes on any input
- Tests that results are always well-formed `ValidationReport` objects
- 3 tests marked `@pytest.mark.slow` for deeper exploration

### Test marks

```ini
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests requiring external services",
]
```

- `@pytest.mark.slow` -- 5 uses (3 in fuzz tests, 2 in scraper integration)
- `@pytest.mark.integration` -- 3 uses (ExpertFlyer, SerpAPI live tests)
- `@pytest.mark.live` -- 1 use (Google Flights live test)
- `@pytest.mark.asyncio` -- 4 uses (batch scraping tests)
- `@pytest.mark.parametrize` -- 3 uses (output formatter tests)

Skip slow tests: `uv run pytest -m "not slow" -x`

## Integration vs Unit Tests

### Unit tests (majority)

Most tests are true unit tests that exercise a single module in isolation:
- Rule tests call `RuleClass().check(itin, ctx)` directly
- Cost tests call `CostEstimator().get_base_fare()` directly
- Model tests verify Pydantic validation directly
- No external dependencies, no file I/O beyond fixture loading

### Integration tests

| File | Scope |
|------|-------|
| `test_integration.py` (51 tests) | Full pipeline: validate + cost + NTP + value + booking against V3 fixture |
| `test_cli_e2e.py` (31 tests) | End-to-end CLI via `typer.testing.CliRunner` against real fixtures |
| `test_new_fixtures.py` (26 tests) | 5 real-world itineraries through full validation |
| `test_rules/test_fixture_validation.py` (15 tests) | Challenge fixtures through full validator |
| `test_search/test_integration.py` (11 tests) | Search pipeline end-to-end |
| `test_verify/test_integration.py` (5 tests) | Verify pipeline end-to-end |

### Pipeline test pattern

`test_integration.py` follows the full analysis pipeline sequence, testing each stage feeds the next correctly:

1. Load V3 fixture YAML
2. Validate with all 31 rules -- assert pass/fail and check specific rule results
3. Estimate cost -- verify base fare, YQ surcharges, segment costs
4. Calculate NTP -- verify tier point earnings per segment
5. Analyze value -- verify per-segment value ratings
6. Generate booking script -- verify GDS commands and phone script text

A separate "clean itinerary" variant is constructed programmatically to verify a routing with 0 violations and 0 warnings (the V3 fixture has known warnings).

## Test Execution Stats

Running `uv run pytest` collects 1,208 tests in ~0.6 seconds. The full suite completes in under 10 seconds (excluding slow/integration-marked tests).
