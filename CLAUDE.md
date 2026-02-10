# RTW Optimizer

oneworld Explorer round-the-world ticket optimizer. Validates itineraries against IATA Rule 3015, estimates costs + surcharges, calculates BA NTP, analyzes segment value, generates phone booking scripts, searches for optimal routes, and verifies D-class availability via ExpertFlyer.

## Tech Stack

| Component | Version/Tool |
|-----------|-------------|
| Language | Python 3.11+ |
| CLI | Typer + Rich |
| Models | Pydantic v2 |
| Package mgr | uv (use `uv run`, `uv sync`) |
| Tests | pytest (980+ tests) |
| Lint | ruff |
| Scraping | Playwright + httpx |

## Quick Commands

```bash
uv run pytest                          # Run all tests
uv run pytest tests/test_cost.py -x    # Run one test file, stop on first failure
uv run pytest -m "not slow" -x         # Skip slow/integration tests
ruff check rtw/ tests/                 # Lint check
python3 -m rtw --help                  # Show all CLI commands
python3 -m rtw validate FILE.yaml      # Validate itinerary
python3 -m rtw search --cities LHR,NRT,JFK --origin SYD --type DONE4
python3 -m rtw verify                  # Verify D-class availability (needs ExpertFlyer)
```

## CLI Commands

| Command | Purpose |
|---------|---------|
| `validate` | Check itinerary against Rule 3015 constraints |
| `cost` | Estimate base fare + YQ surcharges per segment |
| `ntp` | Calculate BA New Tier Points earnings |
| `value` | Per-segment value analysis (cost vs distance) |
| `booking` | Generate phone booking script + GDS commands |
| `analyze` | Full pipeline: validate + cost + NTP + value |
| `search` | Find valid RTW route options across carriers |
| `verify` | D-class availability check via ExpertFlyer |
| `continent` | Airport → continent/tariff conference lookup |
| `show` | Pretty-print itinerary segments |
| `new` | Output blank YAML itinerary template |
| `scrape` | Scrape flight prices (Google Flights via SerpAPI) |
| `config` | Manage settings (API keys, defaults) |
| `cache` | Manage scrape result cache |
| `login` | Manage ExpertFlyer credentials (keyring) |
| `build` | Generate YAML itinerary from route string |
| `scan-dates` | Scan date range for D-class availability |
| `check-nonstop` | Verify nonstop service exists on a city-pair |

## Module Map

| Module | Path | Purpose |
|--------|------|---------|
| CLI | `rtw/cli.py` | All Typer commands and display logic |
| Models | `rtw/models.py` | Itinerary, Segment, Ticket, CabinClass, TicketType |
| Validator | `rtw/validator.py` | Rule 3015 orchestrator — builds ValidationContext, runs rules |
| Rules | `rtw/rules/` | Individual rule files (segments, carriers, direction, continents, etc.) |
| Airports | `rtw/airports.py` | Shared airportsdata loader (fail-fast, single import) |
| Cost | `rtw/cost.py` | Fare lookup + YQ surcharge calculation + FareLookupError |
| NTP | `rtw/ntp.py` | BA New Tier Points estimator |
| Value | `rtw/value.py` | Per-segment value rating (cost vs distance) |
| Booking | `rtw/booking.py` | Phone script + GDS command generator |
| Search | `rtw/search/` | Route search engine (models, scorer, display) |
| Nonstop | `rtw/nonstop/` | Nonstop route pre-verification via SerpAPI |
| Verify | `rtw/verify/` | D-class verification (models, state, orchestrator) |
| Scraper | `rtw/scraper/` | Google Flights (SerpAPI) + ExpertFlyer scrapers |
| Continents | `rtw/continents.py` | Airport → continent mapping with overrides |
| Distance | `rtw/distance.py` | Great-circle distance calculator |
| Data | `rtw/data/` | YAML reference: carriers, fares, continents, hubs |
| Output | `rtw/output/` | Rich + plain text formatters |

## Domain Vocabulary

| Term | Meaning |
|------|---------|
| RTW | Round-the-world ticket (oneworld Explorer) |
| Rule 3015 | IATA fare rule governing RTW ticket construction |
| AONE4 / AONE3 | First class, 4 or 3 continents |
| DONE4 / DONE3 | Business class, 4 or 3 continents |
| LONE4 / LONE3 | Economy class, 4 or 3 continents |
| NTP | New Tier Points — BA frequent flyer earning metric |
| YQ | Carrier-imposed fuel/insurance surcharge |
| D-class | Booking class for oneworld Explorer award-like fare |
| TC1 / TC2 / TC3 | IATA Tariff Conferences: Americas / Europe+Africa+Middle East / Asia+Pacific |
| SWP | South West Pacific sub-area within TC3 |
| Surface sector | Overland segment (not flown, counts toward routing but not fare) |
| Stopover | City where traveler stays >24 hours |
| Transfer | Connection in a city (<24 hours) |
| Backtrack | Returning to a previously visited tariff conference (restricted by Rule 3015) |
| ExpertFlyer | Third-party tool for checking airline seat availability |
| GDS | Global Distribution System (Amadeus/Sabre) used by booking agents |

## CLI Usage Patterns

**Commands that take YAML files:**
```bash
python3 -m rtw validate itinerary.yaml        # Validate a YAML file
python3 -m rtw analyze itinerary.yaml          # Full pipeline on YAML file
python3 -m rtw cost itinerary.yaml             # Cost estimate on YAML file
python3 -m rtw ntp itinerary.yaml              # NTP calculation on YAML file
python3 -m rtw scrape availability FILE.yaml   # D-class check on YAML file (NOT `verify`)
python3 -m rtw booking itinerary.yaml          # Booking script from YAML file
```

**Commands that do NOT take YAML files:**
```bash
python3 -m rtw verify                          # Verifies LAST SEARCH results (option IDs)
python3 -m rtw verify --option 1               # Verify specific search option
python3 -m rtw check-nonstop --route "..."     # Nonstop check (route string, not YAML)
python3 -m rtw scan-dates DOH LAX QR --from .. # Date scan (positional args, not YAML)
python3 -m rtw build --route "..." --validate  # Build YAML from route string
```

**Common mistake**: `rtw verify FILE.yaml` does NOT work — use `rtw scrape availability FILE.yaml` for D-class checks on YAML files.

## Python API Quick Reference

**SerpAPI (nonstop/pricing):**
```python
from rtw.scraper.serpapi_flights import search_serpapi, search_serpapi_all
import datetime

date = datetime.date(2026, 4, 1)  # MUST be datetime.date, NOT string

# Single cheapest flight → FlightPrice | None
result = search_serpapi("LAX", "HND", date, max_stops=0)

# All flights → SerpAPIFlightsResponse | None
resp = search_serpapi_all("LAX", "HND", date, max_stops=0)
for f in resp.flights:  # SerpAPIFlight objects
    f.carrier          # "JL" (2-letter IATA)
    f.airline_name     # "JAL"
    f.flight_number    # "JL 15"
    f.stops            # 0
    f.duration_minutes # 705
    f.price_usd        # 3200.0
```

**ExpertFlyer (D-class availability):**
```python
from rtw.scraper.expertflyer import ExpertFlyerScraper
import datetime

scraper = ExpertFlyerScraper()
result = scraper.check_availability("DOH", "LAX", datetime.date(2026, 4, 1),
                                     carrier="QR", booking_class="D")
# result: DClassResult | None
result.seats           # 9 (max across all flights)
result.status          # DClassStatus.AVAILABLE
result.flights         # list[FlightAvailability]
result.nonstop_flights # list[FlightAvailability] (stops=0 only)
result.nonstop_seats   # 9 (max nonstop seats)
result.has_nonstop     # True
scraper.close()
```

**Nonstop checker (SerpAPI-based):**
```python
from rtw.nonstop.checker import NonstopChecker

checker = NonstopChecker()
result = checker.check("LAX", "HND", "JL")  # NonstopResult
result.has_nonstop     # True
result.nonstop_count   # 3
result.alternatives    # ["AA"] (other oneworld carriers with nonstop)
```

**NTP calculator:**
```python
from rtw.ntp import NTPCalculator
from rtw.models import Itinerary

calc = NTPCalculator()
itin = Itinerary(**yaml_data)
estimates = calc.calculate(itin)  # list[NTPEstimate], NOT object with .segments
for e in estimates:
    e.route            # "LAX-HND"
    e.carrier          # "JL"
    e.distance_miles   # 5476
    e.rate             # 0.5
    e.estimated_ntp    # 2738
total = sum(e.estimated_ntp for e in estimates)
```

**Validator:**
```python
from rtw.validator import Validator
from rtw.models import Itinerary

validator = Validator()
itin = Itinerary(**yaml_data)
report = validator.validate(itin)  # ValidationReport
report.passed          # True/False
report.results         # list[RuleResult] (all rules)
report.violations      # list[RuleResult] (failures only)
len(report.results)    # total rules checked
```

## Conventions

- **Invocation**: Always use `python3 -m rtw`, never `rtw` directly
- **Testing**: NEVER use mocks for API responses — tests use real data from `tests/fixtures/`. Mocks only for credentials and external service calls.
- **Test structure**: Test files mirror source: `rtw/cost.py` → `tests/test_cost.py`
- **Models**: All data models are Pydantic v2 BaseModel. Use `model_dump(mode="json")` for serialization.
- **YAML**: Itinerary files use YAML format. See `python3 -m rtw new` for template.
- **Credentials**: ExpertFlyer in system keyring (`python3 -m rtw login expertflyer`), SerpAPI via env var (`export SERPAPI_API_KEY=...`). Run `/rtw-init` to set up both.
- **State files**: Search results saved to `~/.rtw/last_search.json`. Trip planning state in `.claude/rtw-state.local.md`.
- **Rules engine**: Each rule is a separate file in `rtw/rules/`. Rules return `RuleResult` with severity. Never invent fare rules — read `01-fare-rules.md` (project root) for authoritative source.
- **Continent overrides**: Some airports have non-obvious continent assignments (e.g., Egypt = EU_ME, Guam = Asia). See `rtw/continents.py`.

## Reference Files

| File | Content |
|------|---------|
| `docs/ARCHITECTURE.md` | Full architecture documentation (15KB) |
| `01-fare-rules.md` | Authoritative IATA Rule 3015 fare rules (project root) |
| `12-rtw-optimization-guide.md` | RTW trip optimization strategies (project root) |
| `rtw/data/carriers.yaml` | oneworld carrier list (16 carriers incl. WY, S7 ineligible) |
| `rtw/data/fares.yaml` | Base fare table: AONE/DONE/LONE x 8 origins |
| `rtw/data/continents.yaml` | Airport → continent/TC mappings |

## Slash Commands

**Domain workflow** (interactive, multi-step):

| Command | Description | Model |
|---------|-------------|-------|
| `/rtw-plan` | Plan an RTW trip interactively | opus |
| `/rtw-search` | Search for itinerary options | sonnet |
| `/rtw-analyze` | Run full analysis pipeline | sonnet |
| `/rtw-booking` | Generate phone booking script | sonnet |
| `/rtw-compare` | Compare fares across origin cities | sonnet |
| `/rtw-lookup` | Airport continent/TC lookup | haiku |

**Developer tools** (fast, non-interactive):

| Command | Description | Model |
|---------|-------------|-------|
| `/rtw-init` | First-time credential & environment setup | sonnet |
| `/rtw-verify` | Run tests + lint check | haiku |
| `/rtw-status` | Project status dashboard | haiku |
| `/rtw-setup` | Install dependencies & run smoke test | sonnet |
| `/rtw-help` | Command inventory + domain primer | haiku |
| `/rtw-build` | Full route-building workflow (search → build → verify) | opus |

**First time?** Run `/rtw-init` to configure SerpAPI + ExpertFlyer credentials and verify the environment.

**Typical workflow**: `/rtw-plan` → `/rtw-search` → `/rtw-verify` (D-class) → `/rtw-analyze` → `/rtw-booking`

**Route building**: `/rtw-build` (interactive) or manually: `rtw check-nonstop` → `rtw build` → `rtw validate` → `rtw scan-dates` → `rtw analyze`

## Route Building Knowledge

### Airport Preferences
- **HND > NRT** for Tokyo: AY flies HND-HEL nonstop, JL flies HND-SYD nonstop; neither from NRT
- Always verify nonstop service with `rtw check-nonstop` before building — many plausible pairs have no nonstop

### Nonstop Gotchas (NO nonstop despite seeming plausible)
- NRT-SYD (JL) — JL nonstops are from HND
- NRT-HEL (AY) — AY nonstops are from HND
- SYD-LHR (QF) — no nonstop, goes via SIN or PER

### D-class Patterns
- **QR**: Generous — D9 common on DOH routes (DOH-LAX, DOH-LHR, etc.)
- **JL**: Good availability, especially HND-SYD
- **AY**: Tight on long-haul nonstops — HEL-LAX AY1 showed 0/12 dates nonstop D-class
- **BA**: D9 common on LHR-LAX (5+ daily flights)

### NTP Earning Rates (for route optimization)
- **Tier 1 (50% distance)**: JL, QR, AY, FJ, RJ, S7, WY
- **Tier 2 (25% distance)**: CX, QF, MH, SL
- **Revenue-based (~0 on D-class)**: BA, AA, IB, AS

### Proven LAX Westbound Routes
- **V1 Direct** (4 seg): LAX→HND:JL → SYD:JL → DOH:QR → LAX:QR — 13,158 NTP, all D-class confirmed
- **V2 London** (5 seg): LAX→HND:JL → SYD:JL → DOH:QR → LHR:QR → LAX:BA — 11,684 NTP, all D-class confirmed

### AY1 HEL-LAX Schedule
- Operates Mon/Wed/Thu ONLY
- D-class extremely scarce on nonstop (0 across all dates checked Apr 2026)

## Notes

If `.claude/rules/` contains `ralph-dev-*` files, ignore them — they are from an unrelated project and not part of this codebase.
