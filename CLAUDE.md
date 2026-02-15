# RTW Optimizer

oneworld Explorer round-the-world ticket optimizer. Validates itineraries against IATA Rule 3015, estimates costs + surcharges, calculates BA NTP, analyzes segment value, generates phone booking scripts, searches for optimal routes, and verifies D-class availability via ExpertFlyer.

## Tech Stack

| Component | Version/Tool |
|-----------|-------------|
| Language | Python 3.11+ |
| CLI | Typer + Rich |
| Models | Pydantic v2 |
| Package mgr | uv (use `uv run`, `uv sync`) |
| Tests | pytest (1080+ tests) |
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
| Rules | `rtw/rules/` | 24 rules across 10 files (segments, carriers, direction, geography, country, surface, validity, etc.) |
| Airports | `rtw/airports.py` | Shared airportsdata loader (fail-fast, single import) |
| Cost | `rtw/cost.py` | Fare lookup + YQ surcharge calculation + FareLookupError |
| NTP | `rtw/ntp.py` | BA New Tier Points estimator |
| Value | `rtw/value.py` | Per-segment value rating (cost vs distance) |
| Booking | `rtw/booking.py` | Phone script + GDS command generator |
| Search | `rtw/search/` | Route search engine (models, scorer, display) |
| Nonstop | `rtw/nonstop/` | Nonstop route pre-verification via SerpAPI |
| Verify | `rtw/verify/` | D-class verification (models, state, orchestrator) |
| Scraper | `rtw/scraper/` | Google Flights (SerpAPI) + ExpertFlyer scrapers |
| Continents | `rtw/continents.py` | Airport → continent mapping, country helpers, open-jaw validation |
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
| `rtw/data/carriers.yaml` | oneworld carrier list (17 carriers incl. JQ codeshare, WY, S7 ineligible) |
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

**First time?** The `SessionStart` hook auto-checks your environment (uv, .venv, SERPAPI_API_KEY, ExpertFlyer keyring, Playwright). If anything is missing, run `/rtw-init` to set it up.

**Typical workflow**: `/rtw-plan` → `/rtw-search` → `/rtw-verify` (D-class) → `/rtw-analyze` → `/rtw-booking`

**Route building**: `/rtw-build` (interactive) or manually: `rtw check-nonstop` → `rtw build` → `rtw validate` → `rtw scan-dates` → `rtw analyze`
