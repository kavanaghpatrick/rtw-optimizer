# Project Survey (AI-Enhanced)

## Summary

RTW is a Python CLI tool for optimizing oneworld Explorer round-the-world airline tickets. It validates itineraries against IATA Rule 3015, estimates costs (base fare + YQ surcharges), calculates BA New Tier Points, analyzes per-segment value, generates phone booking scripts and GDS commands, scrapes Google Flights for pricing and ExpertFlyer for availability, and includes an advanced search engine that generates, scores, and ranks candidate routes across up to 6 continents.

> Analyzed by: claude

## Tech Stack

| Aspect | Value |
|--------|-------|
| Language | Python 3.11+ |
| Framework | Typer (CLI) |
| Build Tool | hatchling |
| Test Framework | pytest |
| Package Manager | uv |

## Directory Structure

## Modules

### cli
- **Path**: `rtw/cli.py`
- **Status**: complete
- **Description**: Main CLI application with Typer — validate, cost, ntp, value, booking, analyze, search, scrape, config, cache commands

### models
- **Path**: `rtw/models.py`
- **Status**: complete
- **Description**: Pydantic domain models — Ticket, Segment, Itinerary, Airport, CarrierInfo, FareReference, ValidationReport, NTPEstimate, CostEstimate, SegmentValue

### validator
- **Path**: `rtw/validator.py`
- **Status**: complete
- **Description**: Rule 3015 validation engine — builds context from itinerary, runs all registered rules, produces ValidationReport

### rules
- **Path**: `rtw/rules/`
- **Status**: complete
- **Description**: 9-file rule engine implementing oneworld Explorer Rule 3015 — segments, carriers, validity, direction, stopovers, surface, geography, intercontinental, hemisphere

### cost
- **Path**: `rtw/cost.py`
- **Status**: complete
- **Description**: Cost estimation — base fare lookup by origin/ticket type, YQ surcharge calculation per carrier, origin comparison, plating carrier comparison

### ntp
- **Path**: `rtw/ntp.py`
- **Status**: complete
- **Description**: BA New Tier Points calculation — distance-based (most carriers) and revenue-based (BA/AA/IB) methods, BA Club World +400 bonus

### distance
- **Path**: `rtw/distance.py`
- **Status**: complete
- **Description**: Great-circle distance calculation between airports using haversine library

### value
- **Path**: `rtw/value.py`
- **Status**: complete
- **Description**: Per-segment value analysis — estimates one-way business class cost vs RTW ticket allocation, rates segments Excellent/Good/Moderate/Low

### continents
- **Path**: `rtw/continents.py`
- **Status**: complete
- **Description**: Airport-to-continent/TC resolution with overrides, same-city group lookups, segment limit tables

### booking
- **Path**: `rtw/booking.py`
- **Status**: complete
- **Description**: Booking assistant — phone script generation, GDS commands (FQD/SS/FXP/OSI), booking class logic, same-city and married-segment warnings

### output
- **Path**: `rtw/output/`
- **Status**: complete
- **Description**: Pluggable output formatting — Rich (colored tables), Plain (text), JSON, and Search formatters via protocol/factory pattern

### scraper
- **Path**: `rtw/scraper/`
- **Status**: complete
- **Description**: Web scraping subsystem — Google Flights price search, ExpertFlyer availability, batch async operations, TTL-based JSON cache

### search
- **Path**: `rtw/search/`
- **Status**: complete
- **Description**: Advanced itinerary discovery — query parsing, route generation via TC-ordered permutations with hub connections, availability checking, multi-metric scoring, YAML export

### data
- **Path**: `rtw/data/`
- **Status**: complete
- **Description**: YAML reference data — carriers, fares by origin, continent/country mappings, NTP rates, surcharges, same-city groups, hub connections

### docs
- **Path**: `*.md (root)`
- **Status**: complete
- **Description**: Reference documentation — fare rules (Rule 3015), optimization guides, BA NTP guide, comprehensive RTW strategy

## Discovered Features

| ID | Description | Module | Source | Confidence |
|----|-------------|--------|--------|------------|
| cli.validate | Validate an itinerary YAML file against all Rule 3015 rules, output pass/fail with violations and warnings | cli | inferred | 100% |
| cli.cost | Estimate total cost (base fare + YQ surcharges) for an itinerary with per-person and all-passengers breakdown | cli | inferred | 100% |
| cli.ntp | Calculate BA New Tier Points earnings per segment (distance or revenue method) with BA Club World bonus | cli | inferred | 100% |
| cli.value | Analyze per-segment value by comparing estimated J-class one-way cost against RTW ticket allocation | cli | inferred | 100% |
| cli.booking | Generate phone booking scripts and GDS commands (FQD/SS/FXP/OSI) for travel agent use | cli | inferred | 100% |
| cli.analyze | Run full pipeline (validate → cost → ntp → value) in a single command | cli | inferred | 100% |
| cli.continent | Look up continent and tariff conference for one or more airport IATA codes | cli | inferred | 100% |
| cli.show | Pretty-print itinerary segments in a formatted table | cli | inferred | 100% |
| cli.new | Output a YAML itinerary template to stdout for new trip creation | cli | inferred | 100% |
| cli.search | Advanced itinerary search — generate, score, rank, and optionally check availability for candidate routes | cli | inferred | 100% |
| cli.scrape.prices | Search Google Flights for real pricing on all segments in an itinerary | cli | inferred | 100% |
| cli.scrape.availability | Check ExpertFlyer award seat availability for all segments | cli | inferred | 100% |
| cli.config.set_expertflyer | Store ExpertFlyer credentials securely in system keyring | cli | inferred | 100% |
| cli.cache.clear | Clear the scrape cache (~/.rtw/cache/) | cli | inferred | 100% |
| rules.segment_count | Enforce 3-16 total segments (including surface) per Rule 3015 | rules | inferred | 100% |
| rules.per_continent_limit | Enforce max 4 intra-continental segments (6 for N_America) | rules | inferred | 100% |
| rules.qr_not_first | Enforce Qatar Airways cannot be the first carrier on the ticket | rules | inferred | 100% |
| rules.eligible_carrier | Validate all carriers are oneworld alliance members | rules | inferred | 100% |
| rules.return_to_origin | Validate itinerary returns to origin city (with same-city group support) | rules | inferred | 100% |
| rules.continent_count | Warn if continents visited doesn't match ticket type number | rules | inferred | 100% |
| rules.ticket_validity | Enforce trip duration 10-365 days | rules | inferred | 100% |
| rules.direction_of_travel | Enforce continuous forward direction (eastbound or westbound, no reversals) | rules | inferred | 100% |
| rules.ocean_crossing | Enforce Atlantic AND Pacific must be crossed once each, both flown (not surface) | rules | inferred | 100% |
| rules.minimum_stopover | Enforce minimum 2 stopovers required | rules | inferred | 100% |
| rules.origin_continent_stopover | Warn if more than 2 stopovers in origin continent | rules | inferred | 100% |
| rules.same_city_resolution | Identify same-city airport pairs (NRT/HND) and exclude from surface sector count | rules | inferred | 100% |
| rules.hawaii_alaska | Enforce Hawaii no-backtracking rule and Alaska 1-in/1-out limit | rules | inferred | 100% |
| rules.transcontinental_us | Enforce max 1 nonstop transcontinental flight within the US | rules | inferred | 100% |
| rules.intercontinental_limit | Enforce max 1 IC arrival + 1 IC departure per continent with exceptions | rules | inferred | 100% |
| rules.hemisphere_revisit | Enforce northern continents max 2 visits, southern max 1 (with origin bonus) | rules | inferred | 100% |
| validator.build_context | Pre-compute validation context (continent assignments, TC sequences, stopover counts, same-city pairs, IC flags) | validator | inferred | 100% |
| validator.validate | Run all registered rules against an itinerary and produce a ValidationReport | validator | inferred | 100% |
| cost.get_base_fare | Look up base fare by origin airport and ticket type from fares.yaml | cost | inferred | 100% |
| cost.estimate_surcharges | Calculate total YQ surcharges per segment using carrier YQ tiers | cost | inferred | 100% |
| cost.compare_origins | Compare all available origins sorted by total fare (cheapest first) | cost | inferred | 100% |
| cost.compare_plating | Compare plating carrier options and their impact on surcharges | cost | inferred | 100% |
| cost.estimate_total | Full cost breakdown: base fare + YQ per person × number of passengers | cost | inferred | 100% |
| ntp.calculate_distance_ntp | Calculate NTP using distance × rate percentage for non-revenue carriers | ntp | inferred | 100% |
| ntp.calculate_revenue_ntp | Calculate NTP using fare allocation (1 NTP per GBP 1) for BA/AA/IB with BA Club World +400 bonus | ntp | inferred | 100% |
| distance.miles | Calculate great-circle distance in miles between two airports using haversine | distance | inferred | 100% |
| value.analyze_segment | Estimate one-way J-class value per segment using distance heuristic with ultra-long/short-haul multipliers | value | inferred | 100% |
| continents.get_continent | Resolve airport IATA code to continent with explicit overrides and country fallback | continents | inferred | 100% |
| continents.get_tariff_conference | Map continent to IATA tariff conference (TC1/TC2/TC3) | continents | inferred | 100% |
| continents.get_same_city_group | Look up same-city airport group for an IATA code (NRT↔HND, TSA↔TPE, etc.) | continents | inferred | 100% |
| continents.are_same_city | Check if two airports belong to the same city group | continents | inferred | 100% |
| booking.generate_phone_script | Generate structured phone booking script with opening, per-segment instructions, and closing checklist | booking | inferred | 100% |
| booking.generate_gds_commands | Generate GDS commands (FQD fare display, SS sell, FXP price, OSI service info, plating override) | booking | inferred | 100% |
| booking.get_booking_class | Determine booking class by carrier and cabin (AA→H, most others→D for business) | booking | inferred | 100% |
| booking.warnings | Generate contextual warnings for same-city transitions, married segments, Iberia verification, FJ ATR-72 | booking | inferred | 100% |
| output.get_formatter | Factory function returning RichFormatter, PlainFormatter, or JsonFormatter based on user selection | output | inferred | 100% |
| output.rich.format_validation | Render validation results as colored Rich panels and tables with severity styling | output | inferred | 100% |
| output.rich.format_ntp | Render NTP estimates as Rich table with per-segment and total points | output | inferred | 100% |
| output.rich.format_cost | Render cost breakdown as Rich table with base fare, YQ, and totals | output | inferred | 100% |
| output.rich.format_value | Render segment value analysis as Rich table with verdicts | output | inferred | 100% |
| output.rich.format_booking | Render booking script and GDS commands as Rich panels | output | inferred | 100% |
| output.json.format_all | Render all outputs as valid JSON for piping to jq or other tools | output | inferred | 100% |
| output.search.format_skeleton | Render search candidate skeletons (compact summary for scanning) | output | inferred | 100% |
| output.search.format_full | Render full search results with scores, availability, and route details | output | inferred | 100% |
| scraper.google_flights.search | Search Google Flights via fast-flights library with rate limiting and oneworld carrier filtering | scraper | inferred | 100% |
| scraper.expertflyer.check_availability | Check ExpertFlyer award seat availability via async browser automation with keyring credentials | scraper | inferred | 100% |
| scraper.batch.search_prices | Async batch price search for all segments with graceful failure handling | scraper | inferred | 100% |
| scraper.batch.check_availability | Async batch availability check for all segments with booking class parameter | scraper | inferred | 100% |
| scraper.cache.set | Store scrape result in JSON file cache with TTL metadata | scraper | inferred | 100% |
| scraper.cache.get | Retrieve cached scrape result if within TTL window | scraper | inferred | 100% |
| scraper.cache.clear | Clear all cached scrape results from disk | scraper | inferred | 100% |
| search.parse_query | Parse and validate search query — cities (3-8), origin, date range, cabin, ticket type with fuzzy airport suggestions | search | inferred | 100% |
| search.generate_routes | Generate candidate itineraries by TC-ordered city permutations with hub connections (eastbound + westbound) | search | inferred | 100% |
| search.score_candidates | Score candidates on availability (0-100), quality (0-100), and cost (0-100) with configurable weight presets | search | inferred | 100% |
| search.check_availability | Check top-N candidates for award seat availability via ExpertFlyer with async progress callback | search | inferred | 100% |
| search.export_yaml | Export scored candidate to YAML itinerary format for use with other CLI commands | search | inferred | 100% |
| search.hub_lookup | Pre-computed hub connection table between tariff conferences for route generation fallback | search | inferred | 100% |
| models.ticket | Pydantic model for ticket — type (DONE/LONE/AONE 3-6), cabin, origin, passengers, departure, plating carrier | models | inferred | 100% |
| models.segment | Pydantic model for flight segment — airports, carrier, flight number, date, type (stopover/transit/surface/final) | models | inferred | 100% |
| models.itinerary | Pydantic model for full itinerary — ticket + segments list with min_length=1 validation | models | inferred | 100% |
| models.enums | Domain enums — TicketType (18 variants), CabinClass, SegmentType, Continent (6), TariffConference (3), NTPMethod, Severity | models | inferred | 100% |

## Completion Assessment

**Overall: 88%**

**Notes:**
- All core modules (validation, cost, NTP, value, booking, output) are fully implemented with comprehensive rule coverage
- Search module is complete but untracked in git (new feature in progress)
- 13+ YAML test fixtures covering valid and invalid itineraries plus real-world FlyerTalk examples
- Comprehensive test suite with unit, integration, e2e, fuzz, and smoke tests
- Scraper module has real external dependencies (Google Flights, ExpertFlyer) — tests use mocking
- Some files have uncommitted modifications (cli.py, google_flights.py) and untracked files (search/, hubs.yaml, search_formatter.py)
- Documentation is thorough with 4 markdown guides covering fare rules, optimization, and NTP strategy
- Missing: no CI/CD pipeline, no Docker/containerization, no published package

## Recommendations

- Commit the untracked search module and related files to git
- Add CI/CD pipeline (GitHub Actions) for automated testing on push
- Add a README.md with installation instructions, usage examples, and architecture overview
- Consider publishing to PyPI for easier installation
- Add --dry-run mode for scrape commands to preview what would be searched
- Consider adding a web UI (Streamlit/Gradio) for visual itinerary building
- Add rate limit configuration for scrapers (currently hardcoded 2s delay)
- Consider adding multi-currency display support beyond USD

## Commands

```bash
# Install dependencies
uv sync

# Start development server
uv run rtw --help

# Build for production
uv build

# Run tests
uv run pytest
```

---

*Generated by agent-foreman with AI analysis*