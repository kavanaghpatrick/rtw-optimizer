# Codebase: CLI Commands and Entry Points

Reference for every CLI command in the RTW Optimizer, covering arguments, backend modules, output formats, and notable CLI-layer logic.

## Entry Point

**File**: `rtw/__main__.py`

```python
from rtw.cli import app
app()
```

Invoked via `python3 -m rtw`. The single `app()` call starts the Typer application defined in `rtw/cli.py`.

## App Structure

The CLI is built with [Typer](https://typer.tiangolo.com/) and organized as one root app with five sub-apps (command groups):

| App | Mount Name | Purpose |
|-----|-----------|---------|
| `app` | (root) | Core analysis + utility commands |
| `scrape_app` | `scrape` | Flight price/availability scraping |
| `config_app` | `config` | Configuration management |
| `cache_app` | `cache` | Scrape cache management |
| `login_app` | `login` | Service credential management |
| `kb_app` | `kb` | Knowledge base queries |

All sub-apps are registered via `app.add_typer(...)`.

## Global Options and Output Format

Four reusable option types are defined as `Annotated` aliases:

| Flag | Short | Type | Purpose |
|------|-------|------|---------|
| `--json` | | `bool` | Output as JSON |
| `--plain` | | `bool` | Output as plain text (no ANSI) |
| `--verbose` / `-v` | `-v` | `bool` | Verbose/debug output |
| `--quiet` / `-q` | `-q` | `bool` | Suppress non-essential output |

### Format Auto-Detection (`_get_format`)

The helper `_get_format(json_flag, plain_flag)` resolves the output format with this priority:

1. `--json` flag -> `"json"`
2. `--plain` flag -> `"plain"`
3. stdout is a TTY -> `"rich"` (colored tables/panels)
4. stdout is piped -> `"plain"` (no ANSI)

This means piping to a file or another command automatically disables Rich formatting.

### Formatter System

Most core commands use the `rtw.output` formatter protocol. The `get_formatter(name)` factory in `rtw/output/__init__.py` returns one of:

- **`RichFormatter`** (`rtw/output/rich_formatter.py`) -- Rich tables, panels, color
- **`PlainFormatter`** (`rtw/output/plain_formatter.py`) -- plain text, no ANSI
- **`JsonFormatter`** (`rtw/output/json_formatter.py`) -- structured JSON

The `Formatter` protocol defines five methods: `format_validation`, `format_ntp`, `format_cost`, `format_value`, `format_booking`.

The `search` command uses a separate set of formatters in `rtw/output/search_formatter.py` with standalone functions (`format_search_results_rich`, `format_search_results_plain`, `format_search_json`, etc.).

The `verify`, `scan-dates`, `check-nonstop`, and `kb` commands handle their own display logic inline in `cli.py`, with Rich/plain fallback patterns.

## Shared CLI Helpers

### `_load_itinerary(file: str) -> Itinerary`

Central YAML loader used by `validate`, `cost`, `ntp`, `value`, `booking`, `analyze`, `show`, `scrape prices`, and `scrape availability`. Provides:

- File-not-found errors with working directory hint
- YAML parse errors with line/column
- Pydantic validation errors with field paths
- Fuzzy airport code suggestions via `difflib.get_close_matches` against `airportsdata`

### `_error_panel(message: str)`

Displays errors in a Rich `Panel` (red border, "Error" title) if Rich is available, falls back to `typer.echo` on stderr.

### `_setup_logging(verbose, quiet)`

Sets Python `logging` level: `ERROR` if quiet, `DEBUG` if verbose, `WARNING` otherwise.

### `_fuzzy_airport_suggestion(code: str) -> str`

Returns a "Did you mean: XXX?" string using `difflib.get_close_matches` against all known airport codes from `airportsdata`.

## Exit Codes

All commands follow a consistent exit code scheme:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Domain failure (validation failed, no results, missing prerequisites) |
| 2 | Infrastructure/input error (bad parameter, API failure, missing credentials) |

---

## Core Commands (Root App)

### `validate`

**Purpose**: Validate an itinerary against oneworld Rule 3015.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | Argument | Yes | Path to itinerary YAML file |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |
| `--verbose` / `-v` | Flag | No | Verbose output |
| `--quiet` / `-q` | Flag | No | Suppress non-essential output |

**Backend**: `rtw.validator.Validator` -- `validator.validate(itinerary)` returns a `ValidationReport`.

**Output**: Formatted via `Formatter.format_validation(report)`. Exits with code 1 if validation fails.

---

### `cost`

**Purpose**: Estimate costs (base fare + YQ surcharges) for an RTW itinerary.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | Argument | Yes | Path to itinerary YAML file |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |
| `--verbose` / `-v` | Flag | No | Show origin comparison + plating comparison |
| `--quiet` / `-q` | Flag | No | Suppress non-essential output |

**Backend**: `rtw.cost.CostEstimator` -- `estimator.estimate_total(itinerary)` returns a `CostEstimate`.

**Output**: Formatted via `Formatter.format_cost(estimate)`.

**Notable CLI logic**: When `--verbose` is set (and not quiet), the CLI also calls:
- `estimator.compare_origins(ticket_type)` -- shows cheapest fare origins
- `estimator.compare_plating(itinerary)` -- shows cheapest plating carriers by YQ

These verbose extras are rendered inline (not through the formatter).

**Error handling**: Catches `FareLookupError` specifically (from `rtw.cost`).

---

### `ntp`

**Purpose**: Estimate BA New Tier Points (NTP) earnings for an itinerary.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | Argument | Yes | Path to itinerary YAML file |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |
| `--verbose` / `-v` | Flag | No | Verbose output |
| `--quiet` / `-q` | Flag | No | Suppress non-essential output |

**Backend**: `rtw.ntp.NTPCalculator` -- `calc.calculate(itinerary)` returns `list[NTPEstimate]`.

**Output**: Formatted via `Formatter.format_ntp(estimates)`.

---

### `value`

**Purpose**: Analyze per-segment value of an itinerary (cost vs distance).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | Argument | Yes | Path to itinerary YAML file |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |
| `--verbose` / `-v` | Flag | No | Verbose output |
| `--quiet` / `-q` | Flag | No | Suppress non-essential output |

**Backend**: `rtw.value.SegmentValueAnalyzer` -- `analyzer.analyze(itinerary)` returns `list[SegmentValue]`.

**Output**: Formatted via `Formatter.format_value(values)`.

---

### `booking`

**Purpose**: Generate a phone booking script and GDS commands for an itinerary.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | Argument | Yes | Path to itinerary YAML file |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |
| `--verbose` / `-v` | Flag | No | Verbose output |
| `--quiet` / `-q` | Flag | No | Suppress non-essential output |

**Backend**: `rtw.booking.BookingGenerator` -- `generator.generate(itinerary)` returns a `BookingScript`.

**Output**: Formatted via `Formatter.format_booking(script)`.

---

### `analyze`

**Purpose**: Run the full analysis pipeline in one command.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | Argument | Yes | Path to itinerary YAML file |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |
| `--verbose` / `-v` | Flag | No | Verbose output |
| `--quiet` / `-q` | Flag | No | Suppress non-essential output |

**Backend**: Calls four modules sequentially:
1. `rtw.validator.Validator` -> `ValidationReport`
2. `rtw.cost.CostEstimator` -> `CostEstimate`
3. `rtw.ntp.NTPCalculator` -> `list[NTPEstimate]`
4. `rtw.value.SegmentValueAnalyzer` -> `list[SegmentValue]`

**Output**: Each step's output is formatted through the `Formatter` and printed with section headers (`--- Validation ---`, `--- Cost Estimate ---`, etc.) unless `--quiet`. Exits with code 1 if validation fails.

---

### `continent`

**Purpose**: Look up continent and IATA tariff conference for airport codes.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `codes` | Argument (list) | Yes | Airport IATA codes to look up (space-separated) |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |

**Backend**: `rtw.continents.get_continent(code)` and `rtw.continents.get_tariff_conference(continent)`.

**Output**: Does NOT use the Formatter protocol. Handles JSON via `json.dumps` directly. Plain output prints one line per code: `  LHR: EU_ME (TC2)`. Unknown codes include fuzzy suggestions.

**Notable**: Accepts multiple codes as positional arguments (e.g., `rtw continent LHR NRT SYD`).

---

### `show`

**Purpose**: Pretty-print an itinerary's segments.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | Argument | Yes | Path to itinerary YAML file |
| `--json` | Flag | No | JSON output (full Pydantic model dump) |
| `--plain` | Flag | No | Plain text output |

**Backend**: `_load_itinerary` only (no analysis module).

**Output**: Does NOT use the Formatter protocol. With `--json`, dumps the full Itinerary model via `model_dump(mode="json")`. Otherwise prints ticket metadata and a numbered segment list with route, carrier, flight number, date, segment type, and notes.

---

### `new`

**Purpose**: Output a blank YAML itinerary template.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--template` / `-t` | Option | Yes (required) | Template name (e.g., `done4-eastbound`) |

**Backend**: Reads template files from `rtw/data/templates/`. Tries exact filename, then `.yaml`, then `.yml` extension.

**Output**: Raw YAML text to stdout. Lists available templates on error.

**Notable**: No `--json`/`--plain` flags. Pure file-read command.

---

### `search`

**Purpose**: Search for valid RTW itinerary options across carriers and routes.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--cities` / `-c` | Option | Yes | Comma-separated IATA codes to visit |
| `--from` / `-f` | Option | Yes | Start date (YYYY-MM-DD) |
| `--to` / `-t` | Option | Yes | End date (YYYY-MM-DD) |
| `--origin` / `-o` | Option | Yes | Origin airport IATA code |
| `--cabin` | Option | No | Cabin class (default: `business`) |
| `--type` | Option | No | Ticket type (default: `DONE4`) |
| `--top` / `-n` | Option | No | Max results (default: 10) |
| `--rank-by` | Option | No | Ranking strategy (default: `availability`) |
| `--skip-availability` | Flag | No | Skip availability check phase |
| `--nonstop` | Flag | No | Show only nonstop flights |
| `--backend` / `-b` | Option | No | Search backend: `auto`, `serpapi`, `fast-flights`, `playwright` |
| `--verify-dclass` | Flag | No | Auto-verify D-class on top results via ExpertFlyer |
| `--export` / `-e` | Option | No | Export option N as YAML (1-based) |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |
| `--verbose` / `-v` | Flag | No | Verbose output |
| `--quiet` / `-q` | Flag | No | Suppress non-essential output |

**Backend**: Multi-phase pipeline:
1. **Parse**: `rtw.search.query.parse_search_query(...)` -> `SearchQuery`
2. **Generate**: `rtw.search.generator.generate_candidates(query, nonstop_filter)` -> candidates
3. **Score**: `rtw.search.scorer.score_candidates(scored, rank_by)` + `rank_candidates(scored, top_n)`
4. **Display skeletons**: Shows initial results before availability check
5. **Availability**: `rtw.search.availability.AvailabilityChecker` checks top 3 options, then re-scores
6. **Fare comparison**: `rtw.search.fare_comparison.compute_fare_comparison(opt, query)` for each result
7. **D-class verification** (optional): `rtw.verify.verifier.DClassVerifier` with `rtw.scraper.expertflyer.ExpertFlyerScraper`
8. **Export** (optional): `rtw.search.exporter.export_itinerary(...)` -> YAML string

**Output**: Uses `rtw.output.search_formatter` functions directly (not the Formatter protocol):
- `format_search_skeletons_rich` / `format_search_skeletons_plain` (phase 4)
- `format_search_results_rich` / `format_search_results_plain` (final)
- `format_search_json` (JSON mode)

**State**: Saves results to `~/.rtw/last_search.json` via `rtw.verify.state.SearchState` for use by `rtw verify`.

**Notable CLI logic**:
- Nonstop pre-filter (`--nonstop`): Uses `rtw.nonstop.checker.NonstopChecker` with a local cache dict to filter candidates before scoring. Falls back gracefully if SERPAPI_API_KEY is not set.
- Backend validation: Checks `SearchBackend` enum and SERPAPI availability before proceeding.
- The skeleton display (phase 4) shows preliminary results while availability is being checked.
- Base fare lookup via `rtw.cost.CostEstimator.get_base_fare(origin, ticket_type)` is used for display.
- This is the most complex command in the CLI (~250 lines).

---

### `verify`

**Purpose**: Verify D-class booking availability for saved search results via ExpertFlyer.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `option_ids` | Argument (list, optional) | No | Option IDs to verify (1-based). Omit for top 3. |
| `--class` / `-c` | Option | No | Override booking class (default: auto per carrier -- AA=H, others=D) |
| `--no-cache` | Flag | No | Skip cache |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |
| `--verbose` / `-v` | Flag | No | Verbose output |
| `--quiet` / `-q` | Flag | No | Suppress non-essential output |

**Backend**:
- `rtw.verify.state.SearchState` -- loads saved search results from `~/.rtw/last_search.json`
- `rtw.scraper.expertflyer.ExpertFlyerScraper` -- browser-based D-class checking (context-managed)
- `rtw.verify.verifier.DClassVerifier` -- orchestrates verification per option

**Output**: Custom Rich table display via `_display_verify_result()` and `_display_verify_summary()` (both defined in cli.py). Features:
- Color-coded D-class status (green=available, red=unavailable, yellow=error)
- Per-flight sub-rows showing individual available flights with departure times, aircraft, stops
- "TIGHT" badge when 2 or fewer flights have D availability
- Alternate date hints for unavailable segments
- Connection-only callouts suggesting `rtw check-nonstop`
- Summary panel for batch verify showing bookability percentage

**Notable CLI logic**:
- Warns if search results are >60 minutes old
- Defaults to verifying top 3 options if no IDs specified
- Uses Rich `Status` spinner for progress display
- Progress callback updates with segment-by-segment status
- `_scored_to_verify_option()` converts `ScoredCandidate` -> `VerifyOption`

---

### `check-nonstop`

**Purpose**: Verify nonstop flight service exists on a city-pair for a specific carrier.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `origin` | Argument | Conditional | Origin airport (3-letter IATA) |
| `dest` | Argument | Conditional | Destination airport (3-letter IATA) |
| `carrier` | Argument | Conditional | Carrier (2-letter IATA) |
| `--route` / `-r` | Option | Conditional | Batch route: `LHR-HEL:AY,HEL-DOH:QR` |
| `--file` / `-f` | Option | Conditional | File with `ORIGIN DEST CARRIER` per line |
| `--date` / `-d` | Option | No | Check date (default: 30 days from now) |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |
| `--verbose` / `-v` | Flag | No | Verbose output |
| `--quiet` / `-q` | Flag | No | Suppress non-essential output |

**Three input modes** (mutually exclusive):
1. **Single**: `rtw check-nonstop LHR HEL AY` -- positional arguments
2. **Batch route**: `--route "LHR-HEL:AY,HEL-DOH:QR"` -- comma-separated route string
3. **File**: `--file pairs.txt` -- one `ORIGIN DEST CARRIER` per line (comments with `#`)

**Backend**: `rtw.nonstop.checker.NonstopChecker` (uses `rtw.scraper.cache.ScrapeCache`). Requires `SERPAPI_API_KEY`.
- Single mode: `checker.check_with_alternatives(origin, dest, carrier, date)`
- Batch mode: `checker.check_batch(segments, date, progress_cb)`

**Output**: Custom Rich table/text display (not the Formatter protocol).
- Single: Shows NONSTOP AVAILABLE / NO NONSTOP SERVICE with flight count and price range. Shows oneworld nonstop alternatives table.
- Batch: Rich table with route, carrier, status, flight count, alternatives. Summary line with all-clear/incomplete status.

**Exit codes**: 0 if nonstop available (or all clear in batch), 1 if not.

**Notable**: Route string parser `_parse_route_string()` and file parser `_parse_pairs_file()` are shared with the `build` command.

---

### `build`

**Purpose**: Generate a YAML itinerary from a compact route string.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--route` / `-r` | Option | Yes | Route string: `LAX-HND:JL,HND-SYD:JL,SYD-DOH:QR,DOH-LAX:QR` |
| `--origin` / `-o` | Option | No | Origin airport (inferred from first segment if omitted) |
| `--type` / `-t` | Option | No | Ticket type (default: `DONE4`) |
| `--cabin` / `-c` | Option | No | Cabin class (default: `business`) |
| `--departure` / `-d` | Option | No | Departure date (default: 60 days from now) |
| `--gap` / `-g` | Option | No | Days between stopovers (default: 4) |
| `--out` | Option | No | Write YAML to file instead of stdout |
| `--validate` | Flag | No | Run validation after building |
| `--ntp` | Flag | No | Calculate NTP after building |
| `--plain` | Flag | No | Plain text output |

**Backend**: Uses `rtw.models` directly (`Itinerary`, `Segment`, `Ticket`, `TicketType`, `CabinClass`, `SegmentType`). Optionally chains:
- `rtw.validator.Validator` (when `--validate`)
- `rtw.ntp.NTPCalculator` (when `--ntp`)

**Output**: YAML text via `yaml.dump()`. Optionally followed by validation result and/or NTP summary.

**Notable CLI logic**:
- Reuses `_parse_route_string()` for parsing the route
- Auto-assigns dates based on departure + gap interval
- Last segment gets `SegmentType.FINAL`, others get `SegmentType.STOPOVER`
- Hardcodes `plating_carrier: AA` and `passengers: 1`
- NTP display includes per-segment breakdown with rate and mileage

---

### `scan-dates`

**Purpose**: Scan a date range for D-class availability on one route via ExpertFlyer.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `origin` | Argument | Yes | Origin airport (3-letter IATA) |
| `dest` | Argument | Yes | Destination airport (3-letter IATA) |
| `carrier` | Argument | Yes | Carrier (2-letter IATA) |
| `--from` | Option | No | Start date (default: 30 days from now) |
| `--to` | Option | No | End date (default: 30 days after start) |
| `--class` / `-c` | Option | No | Booking class (default: `D`) |
| `--nonstop-only` | Flag | No | Only show dates with nonstop D-class |
| `--dow` | Option | No | Days of week filter: `mon,wed,thu` |
| `--plain` | Flag | No | Plain text output |
| `--verbose` / `-v` | Flag | No | Verbose output |
| `--quiet` / `-q` | Flag | No | Suppress non-essential output |

**Backend**: `rtw.scraper.expertflyer.ExpertFlyerScraper` -- calls `scraper.check_availability(origin, dest, date, carrier, booking_class)` for each date in the range.

**Output**: Custom Rich table with columns: Date, Day, D Total, Nonstop, Conn (connections), Best Flight. Nonstop availability highlighted in green. Summary line with best date and seat count.

**Notable CLI logic**:
- Day-of-week filter uses a map: `{"mon": 0, "tue": 1, ..., "sun": 6}`
- Tracks best nonstop date/seats across all checked dates
- Handles ExpertFlyer session errors specifically (login/session failures)
- Scraper is opened without context manager but closed explicitly at the end
- No `--json` flag (unlike most other commands)

---

## Scrape Subcommands (`scrape`)

### `scrape prices`

**Purpose**: Search Google Flights prices for all segments in an itinerary.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | Argument | Yes | Path to itinerary YAML file |
| `--backend` / `-b` | Option | No | Backend: `auto`, `serpapi`, `fast-flights`, `playwright` |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |
| `--verbose` / `-v` | Flag | No | Verbose output |
| `--quiet` / `-q` | Flag | No | Suppress non-essential output |

**Backend**:
- `rtw.scraper.google_flights.SearchBackend` -- enum for backend selection
- `rtw.scraper.batch.search_with_fallback(itinerary, cache, backend)` -- orchestrates search
- `rtw.scraper.cache.ScrapeCache` -- result caching
- `rtw.scraper.serpapi_flights` -- SerpAPI availability check

**Output**: Custom display (not Formatter protocol). JSON mode outputs per-segment price objects. Plain mode lists prices per segment. Surface segments marked as `SURFACE (no flight)`.

**Error handling**: Catches `SerpAPIAuthError` and `SerpAPIQuotaError` with specific guidance messages.

---

### `scrape availability`

**Purpose**: Check ExpertFlyer availability for all segments in an itinerary.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | Argument | Yes | Path to itinerary YAML file |
| `--class` / `-c` | Option | No | Override booking class (default: auto per carrier -- AA=H, others=D) |
| `--verbose` / `-v` | Flag | No | Verbose output |
| `--quiet` / `-q` | Flag | No | Suppress non-essential output |

**Backend**: `rtw.scraper.batch.check_itinerary_availability(itinerary, booking_class)`.

**Output**: Custom plain text display. Shows AVAILABLE/NOT AVAILABLE with seat count and flight count per segment. Handles both object-style and dict-style results.

**Notable**: No `--json`/`--plain` flags.

---

## Config Subcommands (`config`)

### `config set-expertflyer`

**Purpose**: Store ExpertFlyer credentials in the system keyring.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--username` | Option (prompted) | Yes | ExpertFlyer username |
| `--password` | Option (prompted, hidden) | Yes | ExpertFlyer password |

**Backend**: `keyring` library -- stores under service `"expertflyer.com"`, keys `"username"` and `"password"`.

**Output**: Confirmation message.

**Notable**: This is a legacy command. The preferred credential management is via `login expertflyer`.

---

## Cache Subcommands (`cache`)

### `cache clear`

**Purpose**: Clear the scrape result cache.

No arguments.

**Backend**: `rtw.scraper.cache.ScrapeCache` -- `cache.clear()`.

**Output**: Confirmation message.

---

## Login Subcommands (`login`)

### `login expertflyer`

**Purpose**: Store ExpertFlyer credentials and test the login.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--verbose` / `-v` | Flag | No | Verbose output |
| `--quiet` / `-q` | Flag | No | Suppress non-essential output |

**Backend**:
- `keyring` -- credential storage
- `rtw.scraper.expertflyer.ExpertFlyerScraper` -- login test via `scraper._ensure_logged_in()`

**Flow**:
1. Check for existing credentials; prompt to replace if found
2. Prompt for email and password (password hidden)
3. Save to system keyring
4. Test login by connecting to ExpertFlyer (non-blocking on failure -- credentials saved regardless)

---

### `login status`

**Purpose**: Check ExpertFlyer credential status.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--json` | Flag | No | JSON output |

**Backend**: `keyring` -- checks for stored `"username"` and `"password"`.

**Output**: JSON with `has_credentials` and `username`, or plain text status message.

---

### `login clear`

**Purpose**: Clear saved ExpertFlyer credentials from the keyring.

No arguments.

**Backend**: `keyring.delete_password(...)`.

---

## Knowledge Base Subcommands (`kb`)

All KB commands use `rtw.kb.KnowledgeBase` as the backend, opened via the helper `_open_kb(db_path)`. The KB is a SQLite-backed knowledge store.

### `kb search`

**Purpose**: Natural language search across the knowledge base.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | Argument | Yes | Natural language search query |
| `--carrier` / `-c` | Option | No | Filter by carrier code |
| `--topic` / `-t` | Option | No | Filter by topic |
| `--limit` / `-n` | Option | No | Max results (default: 10) |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |
| `--verbose` / `-v` | Flag | No | Show full body previews |

**Backend**: `kb.search(query, carrier, topic, limit)`.

**Output**: Via `_display_kb_results()` -- Rich table with score, source, heading; plain text with score bar.

---

### `kb carrier`

**Purpose**: Show all knowledge about a specific carrier.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | Argument | Yes | 2-letter IATA carrier code |
| `--context` | Option | No | Filter: `yq`, `msc`, `availability`, `booking` |
| `--limit` / `-n` | Option | No | Max results (default: 20) |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |
| `--verbose` / `-v` | Flag | No | Show full body previews |

**Backend**: `kb.carrier_lookup(code, context, limit)`.

---

### `kb lookup`

**Purpose**: Look up structured facts in the KB.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `subject` | Argument | Yes | Subject (carrier, route, rule) |
| `predicate` | Argument | No | Predicate to narrow (e.g., `yq`, `rate`) |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |

**Backend**: `kb.fact_lookup(subject, predicate)`.

**Output**: Via `_display_facts()` -- Rich table with subject, predicate, value, confidence, article; includes source quotes.

---

### `kb ask`

**Purpose**: Answer a question using the knowledge base.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `question` | Argument | Yes | Natural language question |
| `--limit` / `-n` | Option | No | Max results (default: 5) |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |
| `--verbose` / `-v` | Flag | No | Show full body previews |

**Backend**: `kb.answer(question, limit)`.

---

### `kb related`

**Purpose**: Find content related to a specific KB chunk.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chunk_id` | Argument | Yes | Chunk ID to find related content for |
| `--limit` / `-n` | Option | No | Max results (default: 10) |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |

**Backend**: `kb.related(chunk_id, limit)`.

**Output**: Via `_display_related()` -- Rich table with strength percentage, relation type, heading.

---

### `kb stale`

**Purpose**: Find knowledge articles older than a threshold.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--days` / `-d` | Option | No | Max age in days (default: 90) |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |

**Backend**: `kb.stale_articles(max_age_days)`.

**Output**: Via `_display_stale()` -- Rich table with article, title, source date, age.

---

### `kb stats`

**Purpose**: Show knowledge base statistics.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |

**Backend**: `kb.stats()`.

**Output**: Via `_display_stats()` -- Rich table of metrics (articles, chunks, facts, sources, carriers tracked, topics, freshness).

---

### `kb brief`

**Purpose**: Contextual briefing for a specific booking scenario.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--origin` / `-o` | Option | No | Origin airport code |
| `--ticket` / `-t` | Option | No | Ticket type (DONE3, DONE4, etc.) |
| `--carrier` / `-c` | Option (list) | No | Carrier codes (can repeat) |
| `--city` | Option (list) | No | Cities on route (can repeat) |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |

**Backend**: `kb.context_brief(origin, ticket_type, carriers, cities)`.

**Output**: Via `_display_kb_results()` with `verbose=True` (always shows full previews).

---

### `kb topic`

**Purpose**: Show everything on a specific topic.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | Argument | Yes | Topic name or partial match |
| `--limit` / `-n` | Option | No | Max results (default: 15) |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |
| `--verbose` / `-v` | Flag | No | Show full body previews |

**Backend**: `kb.topic_search(name, limit)`.

---

### `kb list`

**Purpose**: List all articles in the knowledge base.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |

**Backend**: `kb.list_articles()`.

**Output**: Rich table with slug, title, category, word count, section count, finding count.

---

### `kb carriers`

**Purpose**: List all carriers with mention counts.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |

**Backend**: `kb.list_carriers()`.

**Output**: Rich table with carrier code, total/YQ/MSC/availability/warning mention counts.

---

### `kb topics`

**Purpose**: List all topics in the knowledge base.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |

**Backend**: `kb.list_topics()`.

**Output**: Rich table with topic name, display name, chunk count, description.

---

### `kb sources`

**Purpose**: List knowledge base sources.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--type` | Option | No | Filter: `flyertalk_thread`, `document`, `web` |
| `--article` | Option | No | Filter by article slug |
| `--json` | Flag | No | JSON output |
| `--plain` | Flag | No | Plain text output |

**Backend**: `kb.get_sources(source_type, article_slug)`.

**Output**: Rich table with type, reference, title, date.

---

## Command-to-Module Dependency Map

| Command | Primary Module(s) | External Service |
|---------|-------------------|------------------|
| `validate` | `rtw.validator` | None |
| `cost` | `rtw.cost` | None |
| `ntp` | `rtw.ntp` | None |
| `value` | `rtw.value` | None |
| `booking` | `rtw.booking` | None |
| `analyze` | `rtw.validator`, `rtw.cost`, `rtw.ntp`, `rtw.value` | None |
| `continent` | `rtw.continents` | None |
| `show` | `rtw.models` (load only) | None |
| `new` | File read from `rtw/data/templates/` | None |
| `search` | `rtw.search.*`, `rtw.cost`, `rtw.nonstop`, `rtw.verify`, `rtw.scraper` | SerpAPI, ExpertFlyer (optional) |
| `verify` | `rtw.verify.*`, `rtw.scraper.expertflyer` | ExpertFlyer |
| `check-nonstop` | `rtw.nonstop.checker`, `rtw.scraper.cache` | SerpAPI |
| `build` | `rtw.models`, optionally `rtw.validator`, `rtw.ntp` | None |
| `scan-dates` | `rtw.scraper.expertflyer` | ExpertFlyer |
| `scrape prices` | `rtw.scraper.batch`, `rtw.scraper.cache` | SerpAPI / Google Flights |
| `scrape availability` | `rtw.scraper.batch` | ExpertFlyer |
| `config set-expertflyer` | `keyring` | None |
| `cache clear` | `rtw.scraper.cache` | None |
| `login expertflyer` | `keyring`, `rtw.scraper.expertflyer` | ExpertFlyer (test) |
| `login status` | `keyring` | None |
| `login clear` | `keyring` | None |
| `kb *` | `rtw.kb.KnowledgeBase` | None (SQLite) |

## Output Format Support Matrix

| Command | Rich | Plain | JSON | Formatter Protocol |
|---------|------|-------|------|--------------------|
| `validate` | Yes | Yes | Yes | Yes |
| `cost` | Yes | Yes | Yes | Yes |
| `ntp` | Yes | Yes | Yes | Yes |
| `value` | Yes | Yes | Yes | Yes |
| `booking` | Yes | Yes | Yes | Yes |
| `analyze` | Yes | Yes | Yes | Yes |
| `continent` | No | Yes | Yes | No (inline) |
| `show` | No | Yes | Yes | No (inline) |
| `new` | - | YAML only | - | No |
| `search` | Yes | Yes | Yes | No (search_formatter) |
| `verify` | Yes | Yes | Yes | No (inline) |
| `check-nonstop` | Yes | Yes | Yes | No (inline) |
| `build` | - | YAML + text | - | No |
| `scan-dates` | Yes | Yes | No | No (inline) |
| `scrape prices` | No | Yes | Yes | No (inline) |
| `scrape availability` | No | Yes | No | No (inline) |
| `cache clear` | - | Text | - | No |
| `login *` | No | Yes | Partial | No (inline) |
| `kb *` | Yes | Yes | Yes | No (KB display helpers) |

## Design Patterns

### Lazy Imports
All heavy modules (`rtw.validator`, `rtw.cost`, `rtw.ntp`, `rtw.scraper.*`, etc.) are imported inside command functions, not at module level. This keeps `python3 -m rtw --help` fast by avoiding loading the full dependency tree.

### Error Boundary
Every command wraps its body in `try/except` with three catch layers:
1. `typer.Exit` -- re-raised (intentional exits)
2. `typer.BadParameter` -- re-raised (input validation errors)
3. `Exception` -- caught, displayed via `_error_panel()`, exits with code 2

### Rich Fallback
Commands that render Rich output (verify, check-nonstop, scan-dates, KB) wrap their Rich display code in `try/except ImportError` and fall back to plain text. This allows the CLI to work in environments without Rich installed.

### Progress Display
The `verify` and `search` commands use Rich `Status` spinners with progress callbacks that update segment-by-segment. The callbacks are defined inline as closures capturing the current option ID and status object.
