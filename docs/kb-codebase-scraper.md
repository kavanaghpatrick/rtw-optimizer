# ExpertFlyer Scraper, Verification System, and Caching Layer

Codebase reference for the RTW Optimizer's availability-checking subsystem. Covers the ExpertFlyer web scraper, the D-class verification orchestrator, the JSON file cache, and session/credential management.

---

## 1. ExpertFlyer Scraper (`rtw/scraper/expertflyer.py`)

### Overview

Playwright-based headless browser scraper that checks booking class availability on ExpertFlyer. Key design decision: constructs results URLs directly rather than filling the search form, which is faster and more reliable.

### URL Construction

`_build_results_url()` constructs a GET URL to the ExpertFlyer results endpoint:

```
https://www.expertflyer.com/air/availability/results?
  origin=LHR&
  destination=HKG&
  departureDateTime=2026-05-15T00:00&
  alliance=none&
  airLineCodes=CX&
  excludeCodeshares=false&
  classFilter=D&
  pcc=USA+(Default)&
  resultsDisplay=single
```

Parameters:
- `origin` / `destination`: 3-letter IATA codes, uppercased.
- `departureDateTime`: ISO format `YYYY-MM-DDT00:00` (time portion always midnight).
- `alliance`: Always `none` (searches by carrier code, not alliance-wide).
- `airLineCodes`: 2-letter carrier code, or empty string for all carriers.
- `excludeCodeshares`: Always `false`.
- `classFilter`: Booking class letter (default `D`; AA uses `H` for business).
- `pcc`: **Hardcoded to `USA (Default)`** -- see POS section below.
- `resultsDisplay`: Always `single`.

Values are URL-encoded via `urllib.parse.quote_plus`.

### POS Configuration (Point of Sale)

The `pcc` parameter is **hardcoded to `"USA (Default)"`** at line 295 of `expertflyer.py`. This means all availability queries are issued from a US point of sale. This matters because:

- Airlines file different availability buckets per POS. D-class inventory visible from a US POS may differ from what a UK, Norway, or Qatar POS would see.
- For RTW tickets originating from non-US cities (OSL, CAI, DOH), the actual GDS booking will use the agent's POS, which may not match the US default.
- ExpertFlyer supports multiple PCC/POS options in its dropdown; the current code does not parameterize this.

**Implication**: Availability results are indicative but may not match what a booking agent in a different country would see. This is a known limitation, not a bug.

### Auth0 Login Flow

The `_login()` method performs programmatic login via ExpertFlyer's Auth0 integration:

1. Navigate to `https://www.expertflyer.com/auth/login`.
2. Wait 3 seconds for Auth0 redirect.
3. If already on `www.expertflyer.com` (already logged in), return immediately.
4. If on `auth.expertflyer.com`:
   - Wait for email/username input field (tries `input[name="email"]`, `input[name="username"]`, `input[type="email"]` in order).
   - Fill email, click submit (Auth0 may split email/password into two screens).
   - Wait 2 seconds, then fill password field.
   - Click submit, wait 5 seconds for redirect.
   - Verify URL is back on `www.expertflyer.com`.
   - If not, wait 3 more seconds for delayed redirect.
5. Set `self._logged_in = True` on success.

The browser context persists across queries -- login happens once per scraper lifecycle.

### Rate Limiting

Two layers of rate control:

| Mechanism | Value | Purpose |
|-----------|-------|---------|
| `_MIN_QUERY_INTERVAL` | 5 seconds | Minimum gap between consecutive queries |
| `_DAILY_SOFT_LIMIT` | 50 queries | Warning threshold (logged, not enforced as hard limit) |

`_rate_limit_wait()` calculates elapsed time since last query and sleeps the difference plus a random 0.5-2.0 second jitter if under the minimum interval.

The soft limit triggers a `logger.warning` at exactly 50 queries but does **not** stop execution. This is intentional -- ExpertFlyer's actual limits are not publicly documented, and 50 is a conservative guideline.

### Retry Logic

Configured via module-level constants:

| Constant | Value | Purpose |
|----------|-------|---------|
| `_MAX_RETRIES` | 3 | Maximum attempts per query |
| `_RETRY_BASE_DELAY` | 3 seconds | Base delay for exponential backoff |
| `_RETRY_JITTER` | 0.2 (20%) | Random jitter range on retry delay |

Retry behavior by error type:

| Error | Retry Strategy | Backoff |
|-------|---------------|---------|
| `SessionExpiredError` | Re-login attempt, then retry | No delay (immediate re-login) |
| `RateLimitError` | Long backoff: `60 * attempt` seconds | 60s, 120s, 180s |
| `ScrapeError` | Exponential: `3 * 2^(attempt-1)` with 20% jitter | ~3s, ~6s, ~12s |
| Generic `Exception` | Fixed delay | 3 seconds |

After all retries exhausted, returns a `DClassResult` with `status=ERROR` and the last error message (does not raise).

### Timeouts

| Constant | Value | Context |
|----------|-------|---------|
| `_PAGE_LOAD_TIMEOUT` | 30,000 ms | `page.goto()` navigation timeout |
| `_RESULTS_TIMEOUT` | 15,000 ms | Waiting for results table selector |

### Session Expiry Detection

`_check_session_expired()` inspects `page.url` -- if redirected to `auth.expertflyer.com` or any URL containing `/login`, raises `SessionExpiredError`.

`_check_rate_limited()` evaluates `document.body.innerText` in the browser and looks for the literal string `"Rate Limit Exceeded"`.

### HTML Parsing -- D-Class Results

The results page uses a `<table>` with CSS class `w-full bg-white shadow-md`. Each flight appears as a `<tr>` with class `hover:bg-sky-50`.

#### Per-Flight Extraction (`_parse_results_table`)

For each `tr.hover:bg-sky-50` row, extracts via `innerText` and regex:

| Field | Regex / Method | Example Match |
|-------|---------------|---------------|
| D-class seats | `\b{booking_class}(\d)\b` | `D9` -> 9 seats, `D0` -> 0 seats |
| Carrier + flight | `^\s*([A-Z\d]{2})\s*\n\s*(\d{1,4})\b` | `CX\n251` -> `CX251` |
| Stops | `\b(\d)\s*\n` | `0\n` -> nonstop |
| Departure/arrival | `\d{2}/\d{2}/\d{2}\s+\d{1,2}:\d{2}\s+[AP]M` | `05/15/26 2:30 PM` |
| Airports | `\b([A-Z]{3})\b` (filtered) | `LHR`, `HKG` (excludes day names) |
| Aircraft | `\b(3\d{2}\|7[2-8]\w\|A\d{2}\w?\|E\d{2})\b` | `77W`, `A350`, `E90` |

Deduplication: flights are deduplicated by `(flight_number, depart_time)` tuple.

Best flight selection: `max(flights, key=lambda f: (f.seats, -(len(f.depart_time or ""))))` -- highest seat count wins, ties broken by having a departure time.

#### Fallback: Body-Text Extraction

If per-row extraction yields zero flights, falls back to scanning `document.body.innerText` for all `D(\d)` matches. Takes the max seat count and attempts flight number extraction from the first result row.

#### Standalone HTML Parser (`parse_availability_html`)

A separate function for testing with HTML fixtures (not used at runtime by the scraper). Parses raw HTML using regex against `<tbody>` and `<tr>` tags directly, extracting airports from `cursor-pointer text-sky-600` styled links.

### Error Hierarchy

```
ScrapeError (base)
  |-- SessionExpiredError  (error_type="SESSION_EXPIRED")
  |-- RateLimitError       (error_type="RATE_LIMITED")
```

All have an `error_type` string attribute for programmatic handling.

### Browser Lifecycle

The `ExpertFlyerScraper` manages its own Playwright instance:

- `_ensure_browser()`: Lazily launches Chromium (headless), creates a context with a Chrome 120 user agent and 1400x900 viewport.
- Context manager (`with scraper:`) calls `_ensure_browser()` on enter, `close()` on exit.
- `close()`: Closes browser then stops Playwright. Sets all references to `None`.
- The page is reused across queries (no new tab per query).

---

## 2. Verification Orchestrator (`rtw/verify/verifier.py`)

### Overview

`DClassVerifier` coordinates the scraper, cache, and progress reporting. It verifies booking class availability for every flown segment of an itinerary option, resolving the correct booking class per carrier.

### Booking Class Resolution

Per-carrier resolution via `rtw/carriers.py::get_booking_class()`:

| Cabin | Default Class | Exceptions |
|-------|--------------|------------|
| Business | D | AA -> H |
| Economy | L | (none) |
| First | A | (none) |
| Surface (no carrier) | D | (safe default) |

An explicit override (`booking_class` constructor param) bypasses per-carrier resolution entirely.

### Segment-by-Segment Flow (`verify_option`)

For each segment in a `VerifyOption`:

1. **Surface segments**: Skipped entirely (appended to results with no D-class check).
2. **Session expired flag**: If a previous segment caused `SessionExpiredError`, all remaining segments are marked `UNKNOWN` with message `"Session expired during batch"`. No further scraper calls are made.
3. **Cache lookup**: Unless `no_cache=True`, checks the cache. Cache hits are returned with `from_cache=True`.
4. **Scraper call**: Calls `ExpertFlyerScraper.check_availability()` with the resolved booking class. Times the call for debug logging.
5. **Married segment check**: On successful scrape, runs `_check_married_pattern()` (see below).
6. **Error handling**:
   - `SessionExpiredError`: Sets the `_session_expired` flag, marks segment as `UNKNOWN`.
   - Any other exception: Marks segment as `ERROR`, continues to next segment.

Progress callback `progress_cb(completed, total, segment)` is invoked after each segment regardless of outcome.

### Married Segment Detection (`_check_married_pattern`)

Applies only to carriers in `_MARRIED_CHECK_HUBS`:
- **CX** (Cathay Pacific) at **HKG**
- **QR** (Qatar Airways) at **DOH**

Two detection patterns:

**Pattern 1 -- Classic Married Segment** (neither endpoint is the hub):
If nonstop flights show 0 seats but connecting flights (stops > 0) show availability, flags as `"D-class only via connection (likely married through {hub})"`.

**Pattern 2 -- O&D Control Warning** (segment touches the hub):
If the segment originates or terminates at the carrier's hub and seats > 0, warns that ExpertFlyer shows leg-level (AVS) availability but the airline's origin-destination revenue management may block standalone D-class on RTW fares. Recommends presenting to the agent as a connected routing.

### Batch Verification (`verify_batch`)

Simple sequential loop over multiple `VerifyOption` objects. No parallelism. Each option is verified independently.

---

## 3. Data Models (`rtw/verify/models.py`)

### `DClassStatus` (Enum)

| Value | Meaning |
|-------|---------|
| `AVAILABLE` | D-class seats found (seats > 0) |
| `NOT_AVAILABLE` | Query succeeded, zero seats |
| `UNKNOWN` | Could not determine (session expired, scraper returned None) |
| `ERROR` | Scraper failed after retries |
| `CACHED` | (Defined but not actively used -- cache hits are set to AVAILABLE or NOT_AVAILABLE) |

### `FlightAvailability`

Per-flight granularity within a single D-class result:

| Field | Type | Notes |
|-------|------|-------|
| `carrier` | `Optional[str]` | 2-letter code |
| `flight_number` | `Optional[str]` | e.g., `CX251` |
| `origin` / `destination` | `Optional[str]` | 3-letter IATA |
| `depart_time` / `arrive_time` | `Optional[str]` | String format from EF: `MM/DD/YY H:MM AM/PM` |
| `aircraft` | `Optional[str]` | e.g., `77W`, `A350` |
| `seats` | `int` | 0-9 (constrained) |
| `booking_class` | `str` | Default `D` |
| `stops` | `int` | 0 = nonstop |

### `DClassResult`

Aggregate result for a route/date query:

| Field | Type | Notes |
|-------|------|-------|
| `status` | `DClassStatus` | Overall status |
| `seats` | `int` | Best seat count across all flights (0-9) |
| `flight_number` | `Optional[str]` | Flight number of the best result |
| `carrier` | `str` | Queried carrier |
| `origin` / `destination` | `str` | 3-letter IATA (validated min/max length 3) |
| `target_date` | `date` | Queried date |
| `booking_class` | `str` | Default `D` |
| `checked_at` | `datetime` | UTC timestamp, auto-set |
| `from_cache` | `bool` | Whether result came from cache |
| `error_message` | `Optional[str]` | Error detail on failure |
| `alternate_dates` | `list[AlternateDateResult]` | Availability on nearby dates |
| `flights` | `list[FlightAvailability]` | Per-flight breakdown |

Key computed properties:

| Property | Returns | Logic |
|----------|---------|-------|
| `available` | `bool` | Status is AVAILABLE and seats > 0 |
| `available_flights` | `list` | Flights with seats > 0, sorted by seats desc |
| `nonstop_flights` | `list` | stops==0, seats > 0, matching O&D |
| `has_nonstop` | `bool` | Any nonstop flight with seats |
| `nonstop_seats` | `int` | Max seats among nonstops (0 if none) |
| `display_code` | `str` | Short display: `D9 (3 ns)`, `D9* (2 conn)`, `D0`, `D?`, `D!` |
| `best_alternate` | `Optional` | Best alternate date by seats, then proximity |

`display_code` format:
- `D9 (3 ns)` -- 9 seats, 3 nonstop flights with availability
- `D9* (2 conn)` -- 9 seats but only via connections (asterisk flag)
- `D0` -- zero seats
- `D?` -- unknown (session issue)
- `D!` -- error (scrape failure)

### `SegmentVerification`

Wrapper for a single segment's verification state:

| Field | Type | Notes |
|-------|------|-------|
| `index` | `int` | Segment position in itinerary |
| `segment_type` | `str` | `FLOWN`, `SURFACE`, or `TRANSIT` |
| `origin` / `destination` | `str` | IATA codes |
| `carrier` | `Optional[str]` | Airline code |
| `flight_number` | `Optional[str]` | |
| `target_date` | `Optional[date]` | |
| `dclass` | `Optional[DClassResult]` | Populated after verification |
| `married_segment_note` | `Optional[str]` | Warning from married segment check |

### `VerifyOption` / `VerifyResult`

`VerifyOption` is the input (list of `SegmentVerification` to check). `VerifyResult` is the output (same segments with `dclass` populated).

`VerifyResult` properties:

| Property | Logic |
|----------|-------|
| `confirmed` | Count of flown segments with **nonstop** D-class available |
| `confirmed_any` | Count with any D-class (including connections) |
| `total_flown` | Count of FLOWN segments |
| `percentage` | `confirmed / total_flown * 100` |
| `fully_bookable` | All flown segments have nonstop D-class |
| `connection_only_segments` | Segments with D-class only via connections |

---

## 4. Cache Layer (`rtw/scraper/cache.py`)

### Storage Format

JSON files stored at `~/.rtw/cache/`. Each file contains:

```json
{
  "key": "dclass_CX_LHR_HKG_2026-05-15_D",
  "data": { ... DClassResult as JSON ... },
  "timestamp": 1711756800.0,
  "ttl_seconds": 86400
}
```

### Key Structure

Cache keys for D-class results follow the pattern:

```
dclass_{carrier}_{origin}_{destination}_{date}_{booking_class}
```

Example: `dclass_CX_LHR_HKG_2026-05-15_D`

### Filename Sanitization

`_sanitize_key()` converts the key to a filesystem-safe filename:
1. Replace non-alphanumeric characters (except `_` and `-`) with underscores.
2. Truncate to 80 characters.
3. Append a 12-character SHA-256 hash of the original key for collision avoidance.
4. Add `.json` extension.

Result: `dclass_CX_LHR_HKG_2026_05_15_D_a1b2c3d4e5f6.json`

### TTL and Expiry

| Setting | Value | Notes |
|---------|-------|-------|
| Default TTL | 24 hours | Set at both cache level and verifier level |
| D-class TTL | 24 hours | `_CACHE_TTL_HOURS` in `verifier.py` |
| Nonstop positive | 6 hours | Different subsystem (`nonstop/checker.py`) |
| Nonstop negative | 2 hours | Different subsystem |

On `get()`, if the entry's age exceeds its `ttl_seconds`, the file is deleted and `None` is returned.

### Cache Operations

| Method | Behavior |
|--------|----------|
| `set(key, data, ttl_hours)` | Write JSON file with timestamp and TTL |
| `get(key)` | Read file, check TTL, return data or None. Deletes expired files. |
| `clear()` | Remove all `*.json` files in cache directory |

The cache directory is created on `__init__` with `mkdir(parents=True, exist_ok=True)`.

### Cache Integration in Verifier

The verifier checks cache before every scraper call (unless `no_cache=True`). On cache hit:
- Deserializes via `DClassResult.model_validate(cached)`
- Sets `from_cache = True`
- Recalculates status from seat count (AVAILABLE if seats > 0, else NOT_AVAILABLE)

On successful scrape, stores the result via `DClassResult.model_dump(mode="json")`.

---

## 5. Session Management (`rtw/verify/session.py`)

### Overview

`SessionManager` handles browser session persistence via Playwright's `storage_state` mechanism. This is a **legacy/alternative** approach to the programmatic Auth0 login -- the main scraper now uses keyring credentials directly.

### Session File

- Path: `~/.rtw/expertflyer_session.json`
- Max age: 24 hours
- Permissions: `0o600` (owner read/write only)
- Contains Playwright storage state (cookies + localStorage)

### Interactive Login

`login_interactive()` launches a **headed** (visible) Chromium browser:
1. Navigates to `https://www.expertflyer.com`.
2. Polls every 2 seconds for up to 120 seconds (configurable).
3. Detects login success when URL is on `www.expertflyer.com` (not `auth.`) and authenticated cookies are present (looks for `__txn_*` or `auth0` cookies on `expertflyer.com` domain).
4. Saves `context.storage_state()` to the session file.

This is the manual login fallback -- the user sees the browser and logs in themselves.

---

## 6. Credential Management

### Keyring Storage

Credentials are stored in the macOS Keychain via the `keyring` Python library:

| Keyring Service | Key | Value |
|-----------------|-----|-------|
| `expertflyer.com` | `username` | Email address |
| `expertflyer.com` | `password` | Account password |

Set via CLI: `python3 -m rtw login expertflyer`

### Credential Retrieval

`_get_credentials()` (module-level function) calls `keyring.get_password()` for both username and password. Returns `(username, password)` tuple or `None` if either is missing or keyring raises an exception.

The scraper checks credentials at multiple points:
1. `credentials_available()` -- boolean check (no login attempt).
2. `check_availability()` -- early return `None` if no credentials and no legacy session path.
3. `_ensure_logged_in()` -- calls `_login()` which calls `_get_credentials()`.

---

## 7. Search State (`rtw/verify/state.py`)

### Purpose

Bridges the `rtw search` and `rtw verify` commands. After a search, results are saved so `rtw verify` can check availability without re-searching.

### Storage

- File: `~/.rtw/last_search.json`
- Format: Pydantic `SearchResult` serialized via `model_dump(mode="json")` plus a `_saved_at` timestamp.
- No TTL enforcement (age is queryable via `state_age_minutes()` but not auto-expired).

### Operations

| Method | Behavior |
|--------|----------|
| `save(result)` | Serialize and write to file |
| `load()` | Deserialize, strip `_saved_at`, return `SearchResult` or `None` |
| `get_option(id)` | Load and return 1-based option by index |
| `state_age_minutes()` | File mtime-based age |
| `option_count` | Count of options in saved state |

---

## 8. Batch Scraper (`rtw/scraper/batch.py`)

### Price Searching

`search_itinerary_prices()` (async) and `search_with_fallback()` (sync wrapper) search flight prices for all segments using a cascade:

1. SerpAPI (if `SERPAPI_API_KEY` is set)
2. fast-flights library

Playwright is excluded from the batch cascade (too slow for multi-segment pricing).

### Availability Checking

`check_itinerary_availability()` is a simpler batch function that creates an `ExpertFlyerScraper` and checks each flown segment sequentially. Unlike the verifier, this function:
- Does not use the cache
- Does not detect married segments
- Returns raw dicts, not `DClassResult` objects
- Never raises (catches all exceptions)

This is a lower-level utility; the `DClassVerifier` is the preferred entry point for availability checking.

---

## 9. Architecture Diagram

```
CLI (rtw verify)
    |
    v
DClassVerifier (verifier.py)
    |-- Resolves booking class per carrier (carriers.py)
    |-- Checks ScrapeCache (cache.py)
    |-- Calls ExpertFlyerScraper (expertflyer.py)
    |     |-- _get_credentials() from keyring
    |     |-- _login() via Auth0
    |     |-- _build_results_url() with hardcoded USA POS
    |     |-- _fetch_and_parse() with Playwright
    |     |-- _parse_results_table() regex extraction
    |     |-- Rate limiting + retry with backoff
    |-- Runs _check_married_pattern() for CX/QR
    |-- Stores result in ScrapeCache
    |-- Reports progress via callback
    v
VerifyResult (models.py)
    |-- Per-segment DClassResult
    |-- Aggregate: confirmed / total_flown / percentage
    |-- Flags: connection_only_segments, fully_bookable
```

---

## 10. Known Limitations

1. **POS is hardcoded to USA**: The `pcc` parameter is always `"USA (Default)"`. Availability may differ for non-US points of sale. To fix, `_build_results_url()` would need a `pcc` parameter threaded from the CLI or itinerary origin.

2. **No parallel verification**: Segments are checked sequentially with rate limiting. A 16-segment itinerary takes ~80+ seconds minimum (5s per query).

3. **ExpertFlyer shows leg-level availability**: EF queries AVS (availability status) which is leg-level inventory. Airlines using O&D revenue management (CX, QR) may show D-class available on EF but block it at booking time for certain origin-destination pairs.

4. **Seat count ceiling of 9**: ExpertFlyer displays availability as a single digit (0-9). Values above 9 are shown as 9. The `FlightAvailability.seats` field is constrained to `ge=0, le=9`.

5. **Auth0 form selectors may break**: The login flow uses CSS selectors for Auth0's login form (`input[name="email"]`, `button[type="submit"]`). If ExpertFlyer or Auth0 changes their UI, login will fail.

6. **No headless detection evasion**: The scraper sets a standard Chrome user agent but does not employ advanced anti-detection measures (e.g., stealth plugin, WebGL spoofing). ExpertFlyer does not currently block headless browsers.

7. **Cache does not invalidate on date changes**: If you check availability for a date, then the airline opens/closes inventory, the cache will serve stale data for up to 24 hours. Use `no_cache=True` or `rtw cache clear` for fresh results.
