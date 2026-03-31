# RTW Optimizer -- Codebase Architecture

## Overview

RTW Optimizer is a Python 3.11+ CLI tool for planning, validating, costing, and booking oneworld Explorer round-the-world airline tickets under IATA Rule 3015. It comprises ~14,000 lines of application code across 55 Python modules, with ~15,000 lines of tests (1,180+ test cases).

The system progresses through a pipeline: **parse YAML itinerary -> validate against fare rules -> estimate cost -> calculate loyalty points -> analyze value -> generate booking script -> verify seat availability**.

---

## System Architecture Diagram

```
                           +---------------------+
                           |    rtw/__main__.py   |
                           |   (entry point)      |
                           +----------+----------+
                                      |
                           +----------v----------+
                           |      rtw/cli.py      |
                           |  Typer app (2,900L)   |
                           |  15 commands + 4 sub  |
                           +----------+----------+
                                      |
          +---------------------------+---------------------------+
          |           |          |         |          |           |
  +-------v---+ +----v----+ +--v---+ +---v---+ +---v----+ +----v-----+
  | validator  | |  cost   | | ntp  | | value | | booking| |  search  |
  | (.py)      | | (.py)   | | (.py)| | (.py) | | (.py)  | | (pkg)    |
  +-----+-----+ +----+----+ +--+---+ +---+---+ +---+----+ +----+-----+
        |             |         |         |         |           |
  +-----v-----+      |    +----v----+    |         |     +-----v------+
  | rules/    |      |    | distance|    |         |     | generator  |
  | (11 files)|      |    | (.py)   |    |         |     | scorer     |
  | 34 rules  |      |    +---------+    |         |     | query      |
  +-----------+      |         |         |         |     | hubs       |
        |            |         |         |         |     | exporter   |
        +------+-----+---------+---------+---+-----+     | availability|
               |                             |           +-----+------+
        +------v------+              +-------v-------+         |
        |  continents  |              |   airports    |         |
        |  (.py)       |              |   (.py)       |   +-----v------+
        +--------------+              | (airportsdata)|   |  verify/   |
               |                      +---------------+   |  verifier  |
               |                                          |  session   |
        +------v------+                                   |  state     |
        |  data/      |                                   |  models    |
        | YAML + DB   |                                   +-----+------+
        +-------------+                                         |
                                                          +-----v------+
                                                          |  scraper/  |
                    +------------+                        | expertflyer|
                    |  output/   |                        | google_fl  |
                    | rich       |                        | serpapi    |
                    | plain      |                        | batch     |
                    | json       |                        | cache     |
                    | search     |                        +-----+------+
                    +------------+                              |
                                                          +-----v------+
                                                          | Playwright |
                                                          | (browser)  |
                                                          +------------+
```

---

## Data Flow Pipeline

The core pipeline processes a YAML itinerary through six stages. Each stage is independent and can be invoked individually or chained via `analyze`.

```
 itinerary.yaml
       |
       v
 +--[1. PARSE]--+    Pydantic: YAML -> Itinerary(Ticket + [Segment])
       |
       v
 +--[2. VALIDATE]--+  Validator builds ValidationContext, runs 34 registered
       |               rules across 11 modules. Returns ValidationReport
       |               with violations/warnings/info.
       v
 +--[3. COST]--+      CostEstimator: base fare (fares.yaml) + per-segment
       |               YQ surcharges (surcharges.yaml) + plating carrier
       |               comparison. Returns CostEstimate.
       v
 +--[4. NTP]--+       NTPCalculator: distance-based (haversine * rate) or
       |               revenue-based (GBP spend) per carrier. BA Club
       |               World +400 bonus. Returns [NTPEstimate].
       v
 +--[5. VALUE]--+     SegmentValueAnalyzer: estimated J-class one-way cost
       |               per segment vs RTW allocation. Rates each segment
       |               Excellent/Good/Moderate/Low. Returns [SegmentValue].
       v
 +--[6. BOOKING]--+   BookingGenerator: phone script (natural language) +
       |               GDS commands (FQD/SS/FXP/OSI). Per-carrier booking
       |               class (AA=H, others=D). Returns BookingScript.
       v
 +--[7. VERIFY]--+    DClassVerifier: ExpertFlyer browser automation via
                       Playwright. Checks booking class availability on
                       each flown segment. Caches results 24h.
```

### Parallel / Independent Flows

```
 search --cities LHR,NRT,JFK     check-nonstop SYD-LAX QF
       |                                 |
       v                                 v
  SearchQuery -> generator          SerpAPI lookup
  -> scorer -> availability         -> NonstopResult
  -> ScoredCandidate[]              (confirms direct service)
       |
       v
  Export to YAML -> feed into main pipeline
```

---

## Module Dependency Map

### Core Domain Modules

| Module | Depends On | Depended On By |
|--------|-----------|----------------|
| `models.py` (338L) | pydantic | Everything |
| `airports.py` (39L) | airportsdata | continents, distance, cost |
| `continents.py` (100L+) | airports, models, data/continents.yaml, data/same_cities.yaml | validator, rules, search, booking |
| `distance.py` (32L) | airports, haversine | ntp, value |
| `carriers.py` (46L) | models, data/carriers.yaml | verify, booking |
| `through_flights.py` (47L) | data/through_flights.yaml | validator |

### Analysis Modules

| Module | Depends On | Depended On By |
|--------|-----------|----------------|
| `validator.py` (257L) | models, continents, rules/* | cli, search |
| `cost.py` (200L+) | models, airports, data/{fares,surcharges,carriers}.yaml | cli |
| `ntp.py` (150L+) | models, distance, data/{ntp_rates,fares}.yaml | cli |
| `value.py` (87L) | models, distance | cli |
| `booking.py` (300L+) | models, data/{carriers,same_cities}.yaml | cli |
| `kb.py` (500L+) | data/knowledge.db (SQLite + FTS5) | cli |

### Rules Engine (11 files, 34 registered rules)

| File | Rules | Implements |
|------|-------|-----------|
| `rules/segments.py` | SegmentCountRule, PerContinentLimitRule, SegmentConnectivityRule | 3-16 segments, per-continent caps, chain continuity |
| `rules/direction.py` | DirectionOfTravelRule, OceanCrossingRule, CityPairDirectionRule | Forward travel, both oceans, no duplicate city-pairs |
| `rules/stopovers.py` | MinimumStopoverRule, OriginContinentStopoverRule, OriginCountryStopoverPerDirectionRule, SameCityVisitLimitRule | Min 2 stopovers, origin continent max 2, per-direction country limit, city visit caps |
| `rules/surface.py` | FirstSegmentNotSurfaceRule, SameCityResolutionRule, TransoceanicSurfaceRule | No surface first, same-city exemption, no transoceanic surface |
| `rules/geography.py` | HawaiiAlaskaRule, TranscontinentalUSRule, TranscontinentalAURule, ImplicitAsiaRule | Hawaii/Alaska limits, US/AU transcon caps, implicit Asia via EU_ME-SWP |
| `rules/carriers.py` | QRNotFirstRule, EligibleCarrierRule, QFJQCodeshareRule | QR not first, oneworld only, QF/JQ codeshare plating |
| `rules/validity.py` | ReturnToOriginRule, OpenJawPairsRule, ContinentCountRule, TicketValidityRule, OriginMatchesFirstSegmentRule, DateSequenceRule | Return to origin, open-jaw pairs, continent count, 10-365 days, origin match, chronological dates |
| `rules/hemisphere.py` | HemisphereRevisitRule, EuMeAfricaZoneRule | Northern max 2 visits, southern max 1, EU/ME-Africa zone |
| `rules/intercontinental.py` | IntercontinentalLimitRule | Max 1 IC arrival + 1 IC departure per continent |
| `rules/country.py` | OriginCountryIntlLimitRule, OriginCountryReturnRule | Origin country int'l limits, no mid-journey return |
| `rules/married.py` | MarriedSegmentRule | Married segment risk detection |

### Search Pipeline (`rtw/search/`, 7 files)

| File | Purpose |
|------|---------|
| `models.py` (133L) | SearchQuery, CandidateItinerary, ScoredCandidate, SearchResult |
| `query.py` (129L) | Parse/validate search query (cities, origin, dates, cabin, type) |
| `generator.py` (336L) | TC-ordered permutation with hub connections, both directions |
| `scorer.py` (131L) | Multi-metric scoring: availability (0-100), quality (0-100), cost (0-100) |
| `hubs.py` (109L) | Pre-computed hub connection table between tariff conferences |
| `availability.py` (209L) | Async ExpertFlyer availability check for top-N candidates |
| `exporter.py` (106L) | Export ScoredCandidate to YAML itinerary format |
| `fare_comparison.py` (83L) | Compare fares across origin cities |

### Verification Pipeline (`rtw/verify/`, 4 files)

| File | Purpose |
|------|---------|
| `models.py` (204L) | DClassResult, DClassStatus, SegmentVerification, VerifyResult, VerifyOption |
| `verifier.py` (287L) | Orchestrator: coordinates scraper, cache, progress, married segment detection |
| `session.py` (149L) | Playwright storage_state session persistence (~/.rtw/expertflyer_session.json) |
| `state.py` (78L) | Persistent verification state for incremental re-checks |

### Scraper Subsystem (`rtw/scraper/`, 5 files)

| File | Purpose |
|------|---------|
| `__init__.py` (83L) | BrowserManager: async Playwright lifecycle (Chromium launch/teardown) |
| `expertflyer.py` (675L) | ExpertFlyer scraper: Auth0 login via keyring, direct URL construction, HTML table parsing, retry/rate-limiting |
| `google_flights.py` (529L) | Google Flights scraper via fast-flights library |
| `serpapi_flights.py` (372L) | SerpAPI integration for nonstop route verification |
| `batch.py` (219L) | Async batch operations with graceful failure handling |
| `cache.py` (97L) | JSON file cache at ~/.rtw/cache/ with TTL expiry |

### Nonstop Checker (`rtw/nonstop/`, 2 files)

| File | Purpose |
|------|---------|
| `models.py` | NonstopResult, NonstopAlternative, NonstopBatchResult |
| `checker.py` | SerpAPI-backed nonstop route verification with oneworld alternatives |

### Output Formatters (`rtw/output/`, 5 files)

| File | Purpose |
|------|---------|
| `__init__.py` (68L) | Formatter protocol + get_formatter() factory |
| `rich_formatter.py` | Colored Rich tables/panels for terminal display |
| `plain_formatter.py` | Plain text (no ANSI) for piping/CI |
| `json_formatter.py` | JSON output for machine consumption (jq-friendly) |
| `search_formatter.py` | Specialized search result display (skeleton + full modes) |

---

## External Dependencies

### Runtime

| Library | Purpose | Used By |
|---------|---------|---------|
| `typer[all]` (>=0.12) | CLI framework with Rich integration | cli.py |
| `rich` (>=13.0) | Terminal tables, panels, progress bars, colors | output/, cli.py, airports.py |
| `pydantic` (>=2.0) | Data models with validation | models.py, booking.py, verify/models.py |
| `pyyaml` (>=6.0) | YAML itinerary + reference data parsing | Every data-loading module |
| `haversine` (>=2.8) | Great-circle distance calculation | distance.py |
| `airportsdata` (>=20240101) | IATA airport database (lat/lon, country, city) | airports.py (shared singleton) |
| `playwright` (>=1.40) | Browser automation for ExpertFlyer | scraper/expertflyer.py, scraper/__init__.py, verify/session.py |
| `keyring` (>=25.0) | OS keychain credential storage | scraper/expertflyer.py (ExpertFlyer login) |
| `requests` (>=2.28) | HTTP client | scraper/serpapi_flights.py |
| `fast-flights` (>=2.2) | Google Flights price scraping | scraper/google_flights.py |
| `sqlite3` (stdlib) | Knowledge base FTS5 queries | kb.py |

### Development

| Library | Purpose |
|---------|---------|
| `pytest` (>=8.0) | Test runner |
| `pytest-asyncio` (>=0.23) | Async test support for scraper tests |
| `hypothesis` (>=6.100) | Property-based / fuzz testing |
| `pytest-recording` (>=0.13) | VCR-style HTTP recording |
| `ruff` (>=0.5) | Linting and formatting |

### Build

| Tool | Purpose |
|------|---------|
| `hatchling` | PEP 517 build backend |
| `uv` | Package manager (replaces pip/venv) |

---

## Configuration and State Management

### Credentials

| Service | Storage | Access Pattern |
|---------|---------|---------------|
| ExpertFlyer | macOS Keychain via `keyring` | `python3 -m rtw login expertflyer` stores username/password. Scraper reads at runtime. |
| SerpAPI | Environment variable `SERPAPI_API_KEY` | Read by `scraper/serpapi_flights.py` for nonstop checks |

### State Files (all under `~/.rtw/`)

| Path | Purpose | TTL |
|------|---------|-----|
| `~/.rtw/cache/*.json` | Scrape result cache (prices, availability) | 24 hours |
| `~/.rtw/expertflyer_session.json` | Playwright storage_state (cookies/localStorage) | 24 hours |
| `~/.rtw/last_search.json` | Most recent search results for quick recall | Until overwritten |

### Reference Data (`rtw/data/`)

All YAML files are loaded at module import time and cached in module-level globals.

| File | Content | Consumers |
|------|---------|-----------|
| `carriers.yaml` | 17 oneworld carriers: codes, names, YQ tiers, booking classes, NTP methods | cost, ntp, booking, carriers, nonstop, rules/carriers |
| `fares.yaml` | Base fares by origin city (8 origins) x ticket type (12 types) | cost, ntp |
| `continents.yaml` | Airport overrides, country-to-continent mappings, segment limits | continents |
| `same_cities.yaml` | Same-city airport groups (NRT/HND, TSA/TPE, etc.) | continents, booking |
| `surcharges.yaml` | Per-carrier YQ surcharge rates and plating comparison data | cost |
| `ntp_rates.yaml` | NTP earning rates: distance % per carrier, revenue carrier list, BA bonus | ntp |
| `hubs.yaml` | Inter-TC hub connection table for route generation | search/hubs |
| `through_flights.yaml` | Known through-flights with cross-continent impact | through_flights, validator |
| `knowledge.db` | SQLite FTS5 database: articles, findings, questions from FlyerTalk research | kb |
| `fares.db` | SQLite fare database (supplementary) | scripts/build_fares_db.py |
| `templates/` | YAML itinerary templates (done4-eastbound, done5-eastbound) | cli (new command) |

---

## CLI Command Structure

The CLI (`rtw/cli.py`, 2,909 lines) is organized as a main Typer app with four sub-apps:

```
rtw (main app)
  |-- validate       Validate itinerary against Rule 3015
  |-- cost           Estimate base fare + YQ surcharges
  |-- ntp            Calculate BA New Tier Points
  |-- value          Per-segment value analysis
  |-- booking        Generate phone script + GDS commands
  |-- analyze        Full pipeline (validate + cost + NTP + value)
  |-- show           Pretty-print itinerary segments
  |-- new            Output blank YAML template
  |-- continent      Airport -> continent/TC lookup
  |-- search         Route discovery engine
  |-- verify         D-class availability check
  |-- build          Generate YAML from route string
  |-- check-nonstop  Verify nonstop service on city-pair
  |-- scan-dates     Scan date range for D-class availability
  |
  |-- scrape (sub-app)
  |     |-- prices        Google Flights price search
  |     +-- availability  ExpertFlyer award seat check
  |
  |-- config (sub-app)
  |     +-- set_expertflyer  Store ExpertFlyer credentials
  |
  |-- cache (sub-app)
  |     +-- clear  Clear scrape cache
  |
  |-- login (sub-app)
  |     +-- expertflyer  Manage ExpertFlyer keyring credentials
  |
  +-- kb (sub-app)
        |-- search   Full-text search knowledge base
        |-- lookup   Look up a specific fact/carrier/route
        |-- carrier  Carrier-specific intelligence
        |-- ask      Question answering
        +-- stats    Database statistics
```

### Global Flags

All main commands accept: `--json`, `--plain`, `--verbose` / `-v`, `--quiet` / `-q`.

Output format auto-detection: JSON if `--json`, plain if `--plain` or stdout is not a TTY, Rich otherwise.

---

## Slash Commands / Skills Ecosystem

The project integrates with Claude Code through custom slash commands defined in `CLAUDE.md`. These are AI-assisted workflows that orchestrate multiple CLI commands.

### Domain Workflows (interactive, multi-step)

| Command | Purpose | Model |
|---------|---------|-------|
| `/rtw-plan` | Interactive RTW trip planning conversation | opus |
| `/rtw-search` | Search for itinerary options | sonnet |
| `/rtw-analyze` | Run full analysis pipeline | sonnet |
| `/rtw-booking` | Generate phone booking script | sonnet |
| `/rtw-compare` | Compare fares across origin cities | sonnet |
| `/rtw-lookup` | Airport continent/TC lookup | haiku |

### Developer Tools (fast, non-interactive)

| Command | Purpose | Model |
|---------|---------|-------|
| `/rtw-init` | First-time credential and environment setup | sonnet |
| `/rtw-verify` | Run tests + lint check | haiku |
| `/rtw-status` | Project status dashboard | haiku |
| `/rtw-setup` | Install dependencies and run smoke test | sonnet |
| `/rtw-help` | Command inventory + domain primer | haiku |
| `/rtw-build` | Full route-building workflow (search -> build -> verify) | opus |

### Typical Workflow

```
/rtw-plan -> /rtw-search -> /rtw-verify (D-class) -> /rtw-analyze -> /rtw-booking
```

### Route Building Workflow

```
/rtw-build (interactive)
   or manually:
rtw check-nonstop -> rtw build -> rtw validate -> rtw scan-dates -> rtw analyze
```

---

## Test Structure

Tests are organized to mirror source modules, with specialized directories for package-level subsystems.

```
tests/
  conftest.py                  # Shared fixtures (itineraries, mocked services)
  fixtures/                    # 40 YAML itineraries + HTML fixtures
    minimal_valid.yaml
    flyertalk_*.yaml           # Real-world FlyerTalk examples
    challenge_*.yaml           # Edge-case stress tests
    rule_*.yaml                # Per-rule regression tests
    ef_results_*.html          # ExpertFlyer HTML for parser tests
  test_models.py               # Pydantic model tests
  test_validator.py            # Validator + context builder
  test_rules/                  # Per-rule test files
  test_cost.py                 # Cost estimator
  test_ntp.py                  # NTP calculator
  test_value.py                # Segment value analyzer
  test_booking.py              # Booking generator
  test_output.py               # Formatter tests
  test_distance.py             # Distance calculator
  test_airports.py             # Airport DB tests
  test_carriers.py             # Carrier resolution
  test_continents_country.py   # Continent + country mapping
  test_cli_e2e.py              # CLI end-to-end (Typer CliRunner)
  test_cli_build.py            # Build command tests
  test_cli_verify.py           # Verify command tests
  test_cli_scan_dates.py       # Scan-dates command tests
  test_integration.py          # Cross-module integration
  test_smoke.py                # Quick sanity checks
  test_fuzz.py                 # Hypothesis property-based tests
  test_fare_comparison.py      # Fare comparison tests
  test_verify_models.py        # Verify model tests
  test_search/                 # Search pipeline tests
  test_scraper/                # Scraper tests
  test_nonstop/                # Nonstop checker tests
  test_verify/                 # Verify pipeline tests
  test_new_fixtures.py         # New fixture validation
```

### Test Markers

- `@pytest.mark.slow` -- tests requiring external services or long-running operations
- `@pytest.mark.integration` -- tests requiring external service connectivity

### Test Philosophy

- Real data from `tests/fixtures/` -- never mock API responses
- Mocks only for credentials and external service call points
- Property-based fuzzing via Hypothesis for model validation

---

## Design Patterns

### Rule Engine (Registry Pattern)

Rules are self-registering via the `@register_rule` decorator. Each rule class implements the `Rule` protocol (`check(itinerary, context) -> [RuleResult]`). The `Validator` discovers rules by importing all rule modules, which triggers registration. New rules are added by creating a class in any `rules/*.py` file and decorating it.

### Formatter Protocol (Strategy Pattern)

The `Formatter` protocol defines `format_validation`, `format_ntp`, `format_cost`, `format_value`, `format_booking`. The `get_formatter("rich"|"plain"|"json")` factory returns the appropriate implementation. Output format is auto-detected from TTY status.

### Shared Airport Database (Singleton)

`airports.py` loads the airportsdata IATA database exactly once at import time. All modules import from `rtw.airports` rather than loading airportsdata directly. If the library is missing, the process exits immediately (fail-fast) since every downstream calculation depends on it.

### Data Loading (Module-Level Caching)

YAML reference data is loaded at module import time into module-level globals. This means:
- First import pays the I/O cost
- Subsequent accesses are dict lookups
- No reload mechanism (restart for data changes)

### Browser Automation (Async Context Manager)

`BrowserManager` wraps Playwright's async lifecycle. The `ExpertFlyerScraper` builds results URLs directly (no form filling), parses HTML tables, handles Auth0 login, and implements rate limiting (5s between queries, 50/day soft limit) with retry logic (3 attempts, exponential backoff + jitter).

### Search Pipeline (Generate-Score-Filter)

The search engine generates candidates by TC-ordered city permutations, scores them on multiple metrics (availability, quality, cost), and filters to top-N. Availability checking is async and optional. Results can be exported to YAML for the main pipeline.

---

## Scripts (`scripts/`)

Utility and debugging scripts, not part of the main package:

| Script | Purpose |
|--------|---------|
| `build_fares_db.py` | Build SQLite fare database from Excel source |
| `ingest_kb.py` | Ingest research articles into knowledge.db |
| `ft_scrape.py` | FlyerTalk thread scraper |
| `ef_debug_page.py` | Debug ExpertFlyer page rendering |
| `ef_test_search.py` | Test ExpertFlyer search functionality |
| `explore_ef_pages.py` | Explore ExpertFlyer page structure |
| `explore_expertflyer.py` | ExpertFlyer discovery/research |
| `scrape_worldvia_reddit.py` | Scrape WorldVia Reddit content |
| `validate_harness.py` | Validation test harness |

---

## Key Architectural Decisions

1. **Pydantic v2 for all models**: Type safety, validation, and serialization throughout. All YAML is parsed into typed models before processing.

2. **Rule engine with auto-discovery**: Adding a new Rule 3015 constraint requires only adding a decorated class -- no registration boilerplate. Rules are isolated and independently testable.

3. **Fail-fast on missing airportsdata**: Since distances, continents, and costs all depend on airport coordinates, a missing database would produce silently wrong results. The system exits immediately instead.

4. **Direct URL construction for ExpertFlyer**: Instead of filling web forms, the scraper constructs results URLs directly, making it faster and more reliable than Selenium-style form automation.

5. **Per-carrier booking class resolution**: AA uses H-class for oneworld Explorer business; all others use D. This is centralized in `carriers.py` to avoid scattered special-casing.

6. **Separation of validation context and rules**: The validator pre-computes a `ValidationContext` (continent assignments, TC sequences, IC flags, same-city pairs) once, then passes it to all rules. Rules never recompute shared state.

7. **Cache-first verification**: ExpertFlyer results are cached for 24 hours. Re-running `verify` skips already-checked segments, enabling incremental verification as dates change.

8. **Knowledge base with FTS5**: Travel intelligence (FlyerTalk research, strategy guides) is indexed in SQLite with full-text search, queryable from both CLI and AI agents.
