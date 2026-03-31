# RTW Search Engine -- Codebase Knowledge Base

## Overview

The search engine finds valid round-the-world itinerary routes across oneworld carriers, scores them on multiple dimensions, checks flight availability, and feeds results into the downstream pipeline (validate, cost, verify). The code lives in two packages:

- `rtw/search/` -- Route generation, scoring, availability, export, fare comparison
- `rtw/nonstop/` -- SerpAPI-based nonstop service pre-verification

## Module Inventory

| File | Purpose |
|------|---------|
| `rtw/search/models.py` | Pydantic models: SearchQuery, RouteSegment, CandidateItinerary, ScoredCandidate, SearchResult |
| `rtw/search/query.py` | Input parsing and validation (IATA codes, continent coverage, date range) |
| `rtw/search/generator.py` | Combinatorial route generation with TC traversal and hub insertion |
| `rtw/search/scorer.py` | Three-axis scoring (availability, quality, cost) with configurable weight presets |
| `rtw/search/hubs.py` | Hub connection table loader -- reads `rtw/data/hubs.yaml` |
| `rtw/search/availability.py` | Flight availability checking via SerpAPI / fast-flights / Playwright cascade |
| `rtw/search/exporter.py` | Export scored candidate as loadable YAML itinerary |
| `rtw/search/fare_comparison.py` | RTW base fare vs sum of individual segment prices |
| `rtw/nonstop/models.py` | Pydantic models: NonstopResult, NonstopAlternative, NonstopBatchResult |
| `rtw/nonstop/checker.py` | SerpAPI-based nonstop verification with caching and oneworld alternative lookup |
| `rtw/output/search_formatter.py` | Rich + plain + JSON output formatting for search results |

---

## 1. Search Engine: How It Finds Valid RTW Routes

### Entry Point

The CLI `search` command (`rtw/cli.py`, line 1241) orchestrates a six-phase pipeline:

1. **Parse and validate** the query (cities, origin, dates, cabin, ticket type)
2. **Generate candidates** -- combinatorial route building with optional nonstop filter
3. **Score and rank** -- initial scoring before availability data
4. **Display skeletons** -- compact route overview (Phase 1 display)
5. **Check availability** -- SerpAPI/fast-flights/Playwright cascade for top 3
6. **Final output** -- re-score with availability data, compute fare comparison, display/export

### Route Generation Algorithm (`generator.py`)

The generator produces valid RTW itinerary skeletons through a structured combinatorial process:

**Step 1 -- Group cities by Tariff Conference (TC)**

Every airport maps to one of three IATA Tariff Conferences via the continent system:
- TC1: Americas (N_America, S_America)
- TC2: Europe, Middle East, Africa
- TC3: Asia, South West Pacific

`_group_cities_by_tc()` buckets the user's must-visit cities into TC1/TC2/TC3 groups.

**Step 2 -- Determine TC traversal order**

Two traversal orders are tried for every origin TC:

| Origin TC | Eastbound | Westbound |
|-----------|-----------|-----------|
| TC1 | TC1 -> TC2 -> TC3 -> TC1 | TC1 -> TC3 -> TC2 -> TC1 |
| TC2 | TC2 -> TC3 -> TC1 -> TC2 | TC2 -> TC1 -> TC3 -> TC2 |
| TC3 | TC3 -> TC1 -> TC2 -> TC3 | TC3 -> TC2 -> TC1 -> TC3 |

This encodes the IATA Rule 3015 directional constraint: the journey must proceed generally eastbound or westbound across all three tariff conferences, returning to the origin TC.

**Step 3 -- Permute cities within TC slots**

For each TC group, all permutations of the cities within that TC are generated. The algorithm iterates over the Cartesian product of TC1 permutations x TC2 permutations x TC3 permutations.

Cap: 1,000 candidates per direction (2,000 total) to prevent combinatorial explosion.

**Step 4 -- Insert hub connections**

`_build_route()` walks the TC traversal order and for each TC transition:
- If the user has cities in the destination TC, it routes through hub airports to reach them
- If no user cities exist in a TC, it picks the best-priority hub as a transit point
- Hub connections come from `HubTable` (loaded from `rtw/data/hubs.yaml`)
- Connections are sorted by priority (1 = best: lowest YQ, best availability, most direct)

If no hub connection exists for a required TC crossing, the candidate is discarded.

**Step 5 -- Convert to Itinerary and validate**

`_route_to_itinerary()` converts the airport sequence into a full `Itinerary` model:
- Intercontinental segments get the carrier from the matching hub connection
- Intra-continent segments get the primary carrier for that continent (from `hubs.yaml` intra_continent section)
- Every candidate is passed through `Validator().validate()` -- only candidates with zero violations are kept

**Step 6 -- Optional nonstop filter**

When `--nonstop` is passed, the generator applies a callback filter to every flown segment. If any segment lacks nonstop service (per SerpAPI), the entire candidate is eliminated.

**Deduplication**: Routes are keyed by their full airport sequence (e.g., `LHR->DOH->NRT->LAX->LHR`). Duplicate sequences across different permutation paths are discarded.

---

## 2. Search Models (`models.py`)

### SearchQuery

The validated user request. Fields:
- `cities`: 3-8 IATA airport codes (must-visit list)
- `origin`: Home airport (start and end point)
- `date_from` / `date_to`: Travel window
- `cabin`: CabinClass enum (first, business, economy)
- `ticket_type`: TicketType enum (AONE4, DONE4, LONE4, etc.)
- `top_n`: Max results to return (default 10)
- `rank_by`: Weight preset ("availability", "cost", "quality")

Validators: uppercases all codes, enforces `date_from < date_to`.

### RouteSegment

A segment in a generated route: `from_airport`, `to_airport`, `carrier`, `segment_type`, and optional `SegmentAvailability`.

### CandidateItinerary

Wraps a full `Itinerary` model with metadata:
- `direction`: Eastbound or westbound
- `route_segments`: List of RouteSegment with availability tracking
- `hub_count`: Number of hub airports inserted (not user-requested cities)
- `must_visit_cities`: The user's original city list

### ScoredCandidate

A candidate with three sub-scores and a composite:
- `availability_score`: 0-100 based on confirmed seat availability
- `quality_score`: 0-100 based on route characteristics
- `cost_score`: 0-100 relative cost within the candidate set
- `composite_score`: Weighted sum using rank_by preset
- `fare_comparison`: Optional RTW-vs-individual fare analysis
- `estimated_cost_usd`, `availability_pct`: Summary metrics

### SearchResult

Top-level result container: `query`, `candidates_generated` count, `options` (list of ScoredCandidate), `base_fare_usd`.

### Supporting enums

- `Direction`: EASTBOUND / WESTBOUND
- `AvailabilityStatus`: AVAILABLE / LIKELY / UNKNOWN / NOT_AVAILABLE / NOT_CHECKED

---

## 3. The Scorer (`scorer.py`)

Routes are ranked by a weighted composite of three independent scores.

### Availability Score (0-100)

Measures the percentage of flown segments with confirmed availability:
- `AVAILABLE` = 1.0 weight
- `LIKELY` = 0.7 weight
- `NOT_CHECKED` = excluded from calculation (neutral)
- Everything else = 0.0

If no segments have been checked, returns 50.0 (neutral baseline).

Formula: `(sum of weighted confirmations / total flown segments) * 100`

### Route Quality Score (0-100)

Starts at 100. Deductions and bonuses:
- `-8 per hub connection` (penalizes auto-inserted transit cities)
- `-5 per segment beyond 12` (penalizes overly complex itineraries)
- `+3 per segment on a low-YQ carrier` (JL, AY, FJ, MH -- carriers with lower fuel surcharges)

Clamped to [0, 100].

### Cost Score (0-100)

Inversely proportional to cost relative to other candidates in the set:
- Cheapest candidate = 100
- Most expensive = 0
- Single candidate or equal costs = 50

Formula: `100 * (1 - (my_cost - min_cost) / (max_cost - min_cost))`

### Weight Presets

| Preset | Availability | Quality | Cost |
|--------|-------------|---------|------|
| `availability` (default) | 0.50 | 0.30 | 0.20 |
| `cost` | 0.20 | 0.20 | 0.60 |
| `quality` | 0.15 | 0.60 | 0.25 |

Selected via `--rank-by` CLI flag.

### Ranking

`rank_candidates()` stable-sorts by composite score descending, assigns rank numbers 1..N, and applies the `top_n` limit.

---

## 4. Hub Connection Table (`hubs.py`)

### Data Source: `rtw/data/hubs.yaml`

The YAML file defines:
- **Six TC crossing sections** (TC1_to_TC2, TC2_to_TC3, TC3_to_TC1, and reverses)
- **Intra-continent carriers and hubs** for six continent groups

Each crossing entry has: `from_hub`, `to_hub`, `carrier`, `priority` (1 = best).

Example crossings (priority 1):
- TC1 -> TC2: JFK-LHR on AA
- TC2 -> TC3: DOH-HKG on QR, DOH-NRT on QR
- TC3 -> TC1: NRT-LAX on JL, NRT-SFO on JL

### HubTable class

- `get_connections(from_tc, to_tc)`: Returns hub connections sorted by priority. Empty list if same-TC.
- `get_intra_carrier(continent)`: Primary carrier for intra-continent flights (first in the YAML list).
- `get_hubs_for_continent(continent)`: Hub airports for a continent.

---

## 5. Availability Checking (`availability.py`)

### AvailabilityChecker

Checks flight availability for each segment of a scored candidate, updating it in-place.

**Date assignment**: Segments are assigned approximate dates within the travel window:
- Surface segments: no date
- Transit segments: same day as previous
- Stopover segments: advance by 3 days from previous

**Search cascade** (`_search_with_cascade`): Three backends in fallback order:
1. **SerpAPI** (`rtw/scraper/serpapi_flights.py`) -- preferred when `SERPAPI_API_KEY` is set
2. **fast-flights** (`rtw/scraper/google_flights.py`) -- Python library for Google Flights
3. **Playwright** (`rtw/scraper/google_flights.py`) -- headless browser scraping

Backend selection via `--backend` flag: `auto` (cascade), `serpapi`, `fast-flights`, `playwright`.

**Caching**: Results cached for 6 hours via `ScrapeCache` to avoid redundant API calls. Cache key format: `avail_{from}_{to}_{date}_{cabin}`.

**Progress callback**: The CLI hooks in a verbose progress reporter that prints segment-by-segment status to stderr.

### Fare Comparison (`fare_comparison.py`)

After availability checking, `compute_fare_comparison()` compares the RTW base fare against the sum of individual segment prices:

- Looks up the base fare via `CostEstimator().get_base_fare(origin, ticket_type)`
- Sums `price_usd` from all priced flown segments
- Computes savings (segment total minus base fare) and value multiplier
- Verdict scale: excellent (>=3x), great (>=2x), good (>=1.5x), fair (>=1x), poor (<1x)

---

## 6. Nonstop Verification (`rtw/nonstop/`)

### Purpose

Pre-verify whether specific carrier+city-pair combinations have nonstop service. Used both as a search pre-filter (`--nonstop`) and as a standalone CLI command (`rtw check-nonstop`).

### NonstopChecker (`checker.py`)

**Single check** (`check()`):
- Calls `search_serpapi_all()` with `max_stops=0` and `include_airlines=<carrier>`
- Filters response for flights with `stops == 0`
- Returns `NonstopResult` with flight count and price range
- Caches positive results for 6 hours, negative for 2 hours
- Single retry on failure (1-second delay)

**With alternatives** (`check_with_alternatives()`):
- Runs the single carrier check, then a second API call filtering by `include_airlines="ONEWORLD"`
- Returns all oneworld carriers with nonstop service on the route (excluding the queried carrier)
- Sorted: nonstop carriers first, then alphabetical

**Batch check** (`check_batch()`):
- Deduplicates identical (origin, dest, carrier) tuples
- Calls `check_with_alternatives()` per unique segment
- Returns `NonstopBatchResult` with aggregate counts: nonstop, no-nonstop, errors, API calls used
- `all_clear` property: true when every segment has nonstop service

**Hub pre-check** (`check_hub_connections()`):
- Lighter check (1 API call per segment, no alternatives)
- Returns dict keyed by (origin, dest, carrier) for O(1) lookup during generation

### Models (`nonstop/models.py`)

- `NonstopResult`: Full result for one check (has_nonstop, flight_count, price_range, alternatives, cache status, error)
- `NonstopAlternative`: A oneworld carrier with nonstop service (carrier, name, flight_count, price_range)
- `NonstopSegmentResult`: Wraps a NonstopResult with segment index for batch tracking
- `NonstopBatchResult`: Aggregated batch result with summary counts and `all_clear` property

### CLI Integration (`rtw check-nonstop`)

Three invocation modes:
- **Single**: `rtw check-nonstop LHR HEL AY`
- **Batch route string**: `rtw check-nonstop --route "LHR-HEL:AY,HEL-DOH:QR"`
- **Batch file**: `rtw check-nonstop --file pairs.txt` (one `ORIGIN DEST CARRIER` per line)

Output: Rich table with status (NONSTOP / NO NONSTOP / ERROR), flight counts, and oneworld alternatives. JSON output via `--json`. Exit code: 0 if nonstop available, 1 if not.

---

## 7. Display Layer (`rtw/output/search_formatter.py`)

Two-phase display matches the two-phase pipeline:

### Phase 1: Skeleton Display (before availability check)

- Shows candidate count, route chains, direction, initial scores
- Rich: colored output with arrows (`LHR -> DOH -> NRT -> LAX -> LHR`)
- Plain: same structure without markup

### Phase 2: Full Results (after availability check)

- Rich table per option: segment-by-segment with carrier, flight number, date, stops, duration, availability status
- Color coding: green (AVAILABLE), yellow (LIKELY), dim (UNKNOWN/NOT_CHECKED), red (NOT AVAIL)
- Fare comparison line below each table: RTW fare vs segment total, savings amount, value multiplier with verdict

### JSON Output

Structured JSON with query echo, summary stats, and per-option segment arrays including availability, price, stops, flight number, duration, and fare comparison.

### YAML Export (`exporter.py`)

`export_itinerary()` converts a scored candidate into a YAML string that can be loaded back as an `Itinerary` model. Includes:
- Header comments with direction, score, rank, cities, date range, fare comparison
- Full segment list with dates, carriers, types, and availability notes

---

## 8. How Search Results Feed Into the Pipeline

The search engine is the discovery phase. Its outputs connect to every downstream module:

### State Persistence

After search completes, results are saved via `SearchState().save(result)` to `~/.rtw/last_search.json`. This state file is consumed by `rtw verify` to know which itinerary to verify D-class availability on.

### Validation (already embedded)

Every candidate passes through `Validator().validate()` during generation. Only zero-violation candidates survive. This means every search result is already Rule 3015 compliant.

### Cost Estimation

`CostEstimator().get_base_fare()` is called during search to:
1. Display the RTW base fare in skeleton output
2. Compute fare comparisons (RTW fare vs sum of individual segment prices)

### D-class Verification (optional)

When `--verify-dclass` is passed, the CLI:
1. Takes the top 3 ranked results
2. Converts each to a verify option via `_scored_to_verify_option()`
3. Passes to `DClassVerifier` backed by `ExpertFlyerScraper`
4. Displays verification results inline

### YAML Export -> Full Analysis

`--export N` exports option N as a YAML itinerary file. This file can then be fed into the full analysis pipeline:

```
rtw search --cities LHR,NRT,SYD --origin CAI --from 2025-09-01 --to 2025-11-15 --export 1 > trip.yaml
rtw validate trip.yaml
rtw cost trip.yaml
rtw ntp trip.yaml
rtw value trip.yaml
rtw booking trip.yaml
rtw verify trip.yaml
```

### Typical End-to-End Flow

```
Search (generate + score + availability)
  |
  +--> SearchState saved to ~/.rtw/last_search.json
  |
  +--> Optional: D-class verify via ExpertFlyer
  |
  +--> Export as YAML itinerary
         |
         +--> validate (Rule 3015 compliance -- already guaranteed)
         +--> cost (base fare + YQ surcharges per segment)
         +--> ntp (BA tier points calculation)
         +--> value (per-segment value analysis)
         +--> booking (phone script + GDS commands)
         +--> verify (D-class availability via ExpertFlyer)
```

---

## 9. Key Design Decisions

**Combinatorial with early pruning**: The generator produces all permutations of city orderings within each TC, but caps at 1,000 per direction and eliminates invalid candidates immediately via the validator. This keeps the search tractable for up to 8 cities while ensuring every result is Rule 3015 compliant.

**Hub-mediated connections**: Rather than trying to find arbitrary flights between any two airports, the generator routes through known hub airports where oneworld carriers have strong intercontinental service. This mirrors real-world booking patterns.

**Three-axis scoring with presets**: Separating availability, quality, and cost into independent scores allows users to prioritize what matters most. The preset system avoids exposing raw weight tuning.

**Cache-first availability**: The 6-hour TTL on availability cache prevents redundant API calls across repeated searches. Negative nonstop results use a shorter 2-hour TTL since schedules may update.

**Backend cascade**: The auto mode tries SerpAPI first (most reliable), falls back to fast-flights, then Playwright. This maximizes availability checking success while handling missing API keys gracefully.

**Fare comparison as value signal**: Comparing the RTW base fare against individual segment prices helps users understand whether the RTW ticket offers genuine savings. The multiplier and verdict system makes this instantly actionable.
