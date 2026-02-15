# RTW Optimizer

A command-line tool for optimizing [oneworld Explorer](https://www.oneworld.com/flights/round-the-world-fares) round-the-world tickets. Validates itineraries against IATA Rule 3015, estimates costs and carrier surcharges, calculates BA Avios/NTP earnings, rates per-segment value, searches for optimal routes with live pricing, verifies D-class seat availability, and generates phone booking scripts.

## Why This Exists

oneworld Explorer fares let you fly around the world on oneworld airlines (British Airways, Cathay Pacific, Qantas, JAL, American Airlines, Qatar, etc.) for a flat fare based on the number of continents visited. A business class ticket visiting 4 continents starts at ~$4,000 from Cairo or ~$10,500 from New York.

The catch: these tickets are governed by [IATA Rule 3015](docs/01-fare-rules.md), a complex set of constraints around direction of travel, continent crossings, backtracking, carrier requirements, and segment limits. Building a valid itinerary by hand means juggling 24 rules simultaneously while checking seat availability across a dozen airlines.

This tool automates all of that.

## What It Does

```
Plan your trip       Search routes       Check availability     Analyze costs       Book it
  /rtw-plan    -->    /rtw-search    -->    rtw verify     -->   /rtw-analyze   -->  /rtw-booking
```

| Feature | What It Does |
|---------|-------------|
| **Validate** | Check any itinerary against all Rule 3015 constraints with clear pass/fail per rule |
| **Cost** | Look up base fares by origin city + estimate YQ surcharges per carrier per segment |
| **NTP** | Calculate British Airways New Tier Points earnings for each segment |
| **Value** | Rate each segment's value (cost vs great-circle distance) as Excellent/Good/Low |
| **Search** | Generate valid RTW routes, score them, and optionally check live Google Flights pricing |
| **Verify** | Check D-class seat availability on ExpertFlyer — see exactly which flights have seats |
| **Booking** | Generate a phone script with GDS commands for calling the AA RTW desk |
| **Build** | Generate a YAML itinerary from a route string with validation and NTP |
| **Scan Dates** | Scan a date range for D-class availability on a specific route |
| **Check Nonstop** | Verify nonstop service exists on a city-pair before building routes |

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Install

```bash
git clone https://github.com/kavanaghpatrick/rtw-optimizer.git
cd rtw-optimizer
uv sync
```

### Verify It Works

```bash
python3 -m rtw --help          # Show all commands
uv run pytest -x -q            # Run test suite (1080+ tests)
```

### Optional: API Keys

Two optional services enable advanced features:

| Service | What For | How to Set Up |
|---------|----------|--------------|
| [SerpAPI](https://serpapi.com) | Live Google Flights pricing in search results | `export SERPAPI_API_KEY=your_key` in `~/.zshrc` |
| [ExpertFlyer](https://www.expertflyer.com) | D-class seat availability checking | `python3 -m rtw login expertflyer` (stores in system keyring) |

Without these, the core optimizer (validate, cost, NTP, value, booking) works fully. Search works but without live pricing. Verify requires ExpertFlyer.

If using ExpertFlyer, also install the browser automation driver:

```bash
uv run playwright install chromium
```

## Usage

### Search for Routes

Find the best RTW itineraries visiting specific cities:

```bash
# Quick search (no live pricing)
python3 -m rtw search --cities LHR,NRT,JFK --origin SYD --type DONE4 --skip-availability

# With live Google Flights pricing (needs SerpAPI key)
python3 -m rtw search --cities LHR,NRT,JFK --origin SYD --type DONE4

# Auto-verify D-class on top results (needs ExpertFlyer)
python3 -m rtw search --cities HKG,LHR,JFK --origin SYD --verify-dclass --top 3
```

### Validate an Itinerary

Check an itinerary YAML file against Rule 3015:

```bash
python3 -m rtw validate itinerary.yaml
```

The validator runs 24 rules covering direction of travel, ocean crossings, city-pair duplication, continent coverage, segment limits, carrier eligibility, codeshare validation, surface sector restrictions, transcontinental limits (AU/US), origin-country flight limits, open-jaw validation, and more.

### Full Analysis Pipeline

Run validate + cost + NTP + value in one command:

```bash
python3 -m rtw analyze itinerary.yaml
```

### Estimate Costs

```bash
python3 -m rtw cost itinerary.yaml
```

Shows base fare, per-segment YQ surcharges, and total cost. Highlights high-YQ carriers and suggests lower-surcharge alternatives.

### Compare Fares Across Origins

The same RTW ticket costs wildly different amounts depending on where you start:

```bash
python3 -c "
from rtw.cost import CostEstimator
from rtw.models import TicketType
e = CostEstimator()
for r in e.compare_origins(TicketType('DONE4'))[:5]:
    print(f\"{r['origin']:>5} ({r['name']:<20}) \${r['fare_usd']:>8,.0f}\")
"
```

```
  CAI (Cairo               )   $4,000
  JNB (Johannesburg        )   $5,000
  CMB (Colombo             )   $5,200
  OSL (Oslo                )   $5,400
  NRT (Tokyo Narita        )   $6,360
```

A DONE4 (business, 4 continents) ticket from Cairo costs $4,000 vs $10,500 from New York -- a positioning flight to Cairo can save $6,500.

### Build a Route

Generate a validated YAML itinerary from a route string:

```bash
# Print YAML + validation + NTP
python3 -m rtw build --route "LAX-HND:JL,HND-SYD:JL,SYD-DOH:QR,DOH-LAX:QR" \
  --origin LAX --type DONE4 --departure 2026-04-01 --validate --ntp

# Write to file
python3 -m rtw build --route "LAX-HND:JL,HND-SYD:JL,SYD-DOH:QR,DOH-LAX:QR" \
  --origin LAX --out itineraries/my-trip.yaml
```

### Check Nonstop Service

Verify a carrier actually flies nonstop between two cities before committing to a route:

```bash
# Single city-pair
python3 -m rtw check-nonstop LHR HEL AY

# Batch check entire route
python3 -m rtw check-nonstop --route "LAX-HND:JL,HND-SYD:JL,SYD-DOH:QR,DOH-LAX:QR"
```

### Scan Dates for D-Class

Find which dates have D-class availability on a specific route:

```bash
python3 -m rtw scan-dates DOH LAX QR --from 2026-04-01 --to 2026-04-30
python3 -m rtw scan-dates HEL LAX AY --from 2026-04-01 --to 2026-04-30 --nonstop-only --dow mon,wed,thu
```

### Verify D-Class Availability

After running a search, verify which flights actually have D-class seats:

```bash
python3 -m rtw verify              # Verify all options from last search
python3 -m rtw verify --option 1   # Verify specific option
python3 -m rtw verify --quiet      # Summary only, no per-flight detail
```

Output shows per-segment D-class status (D0-D9), per-flight availability with departure times and aircraft, and flags TIGHT segments (2 or fewer available flights).

### Look Up Airports

```bash
python3 -m rtw continent LHR NRT JFK SYD HKG DOH
```

```
  LHR: EU_ME (TC2)
  NRT: Asia (TC3)
  JFK: N_America (TC1)
  SYD: SWP (TC3)
  HKG: Asia (TC3)
  DOH: EU_ME (TC2)
```

### Generate Booking Script

```bash
python3 -m rtw booking itinerary.yaml
```

Generates a complete phone script for calling the AA RTW desk (1-800-433-7300), including what to say, each segment's details, and Amadeus GDS commands the agent can use directly.

## Itinerary Format

Itineraries are YAML files. Here's an example:

```yaml
ticket:
  type: DONE4
  cabin: business
  origin: SYD

segments:
  - from: SYD
    to: HKG
    carrier: CX
    type: stopover

  - from: HKG
    to: LHR
    carrier: CX
    type: stopover

  - from: LHR
    to: JFK
    carrier: BA
    type: stopover

  - from: JFK
    to: LAX
    carrier: AA
    type: transfer

  - from: LAX
    to: SYD
    carrier: QF
    type: stopover
```

Key fields:
- **type**: `stopover` (stay >24h) or `transfer` (<24h connection) or `surface` (overland, not flown)
- **carrier**: Two-letter IATA airline code (must be a oneworld member; omit for surface sectors)
- **operating_carrier**: Optional — actual operating carrier if different from marketing carrier (e.g., JQ operating a QF-marketed flight)
- **from/to**: IATA airport codes

## Ticket Types

| Type | Class | Continents | Example fare (Cairo) |
|------|-------|-----------|---------------------|
| AONE3 | First | 3 | $5,600 |
| AONE4 | First | 4 | $6,400 |
| AONE5 | First | 5 | $7,000 |
| AONE6 | First | 6 | $8,800 |
| DONE3 | Business | 3 | $3,500 |
| DONE4 | Business | 4 | $4,000 |
| DONE5 | Business | 5 | $4,400 |
| DONE6 | Business | 6 | $5,500 |
| LONE3 | Economy | 3 | $1,800 |
| LONE4 | Economy | 4 | $2,200 |
| LONE5 | Economy | 5 | $2,500 |
| LONE6 | Economy | 6 | $3,000 |

Fares vary significantly by origin city. Use the cost comparison feature to find the cheapest starting point.

## oneworld Carriers

| Airline | Code | Hub | YQ Level | Notes |
|---------|------|-----|----------|-------|
| British Airways | BA | LHR | Very High | |
| Cathay Pacific | CX | HKG | Medium | |
| Qantas | QF | SYD | Very High | |
| Japan Airlines | JL | NRT/HND | Very Low | |
| American Airlines | AA | DFW/JFK | Low | Uses H class (not D) |
| Qatar Airways | QR | DOH | Medium | Cannot be first carrier |
| Iberia | IB | MAD | High | |
| Finnair | AY | HEL | Very Low | |
| Malaysia Airlines | MH | KUL | Low | |
| Royal Jordanian | RJ | AMM | Medium | |
| SriLankan Airlines | UL | CMB | Low | |
| Fiji Airways | FJ | NAN | Very Low | Joined April 2025 |
| Alaska Airlines | AS | SEA | Low | |
| Royal Air Maroc | AT | CMN | Medium | |
| Oman Air | WY | MCT | Low | Joined June 2025 |
| S7 Airlines | S7 | OVB | — | Suspended (sanctions), ineligible |
| Jetstar Airways | JQ | MEL | — | Codeshare only (QF-marketed, JQ-operated) |

Low-YQ carriers (JL, AA, AY, IB) can save hundreds of dollars per segment compared to high-YQ carriers (BA, QF).

Jetstar (JQ) flights are permitted when marketed by Qantas (QF) as codeshares, but restricted on Alaska (AS) and Iberia (IB) ticket stock.

## Using with Claude Code

This project is a [Claude Code](https://claude.ai/claude-code) plugin. It gives Claude 12 slash commands for planning, searching, analyzing, and booking RTW tickets — plus domain knowledge about Rule 3015, D-class availability, NTP earning, and carrier surcharges.

### Install the Plugin

```bash
claude plugin add github:kavanaghpatrick/rtw-optimizer
```

That's it. The plugin works from any directory — you don't need to clone the repo or cd into anything. On your next Claude Code session, all `/rtw-*` commands will be available.

To verify it installed:

```
/rtw-help
```

### What You Get

**12 slash commands:**

| Command | What It Does |
|---------|-------------|
| `/rtw-plan` | Interactive trip planner — picks origin, cities, dates step by step |
| `/rtw-search` | Search for routes (accepts city codes or reads from saved plan) |
| `/rtw-build` | Full route-building workflow: nonstop check → build → verify → analyze |
| `/rtw-analyze` | Full pipeline on an itinerary: validate + cost + NTP + value |
| `/rtw-booking` | Generate phone booking script with GDS commands |
| `/rtw-compare` | Compare ticket prices across origin cities |
| `/rtw-lookup` | Quick airport-to-continent lookup |
| `/rtw-init` | First-time credential and environment setup |
| `/rtw-verify` | Run tests + lint check |
| `/rtw-status` | Project status dashboard (branch, tests, credentials, trip state) |
| `/rtw-setup` | Install dependencies and run smoke test |
| `/rtw-help` | Show all commands with descriptions and domain primer |

**Automatic environment checks:** A preflight hook runs on every session start to verify uv, Python venv, API keys, and ExpertFlyer credentials are set up. If something's missing, it tells you what to run.

**Domain knowledge skills:** Claude automatically gets context about route building patterns, D-class availability by carrier, NTP earning rates, and the Python API — so it can help you build and optimize itineraries without you having to explain the domain.

### First-Time Setup

After installing the plugin, run `/rtw-init` in Claude Code. It walks you through:

1. **SerpAPI key** — enables live Google Flights pricing in search results (`export SERPAPI_API_KEY=your_key` in `~/.zshrc`)
2. **ExpertFlyer credentials** — enables D-class seat availability checking (stored in macOS keyring)
3. **Playwright browser** — needed by the ExpertFlyer scraper (`uv run playwright install chromium`)

Without these, the core optimizer (validate, cost, NTP, value, booking) works fully. Search works but without live pricing. D-class verification requires ExpertFlyer.

### Plan a Trip (5-Minute Walkthrough)

```
/rtw-plan                    Step 1: Answer questions about where you want to go
/rtw-search                  Step 2: Claude finds and ranks valid routes
python3 -m rtw verify        Step 3: Check which flights have D-class seats
/rtw-analyze                 Step 4: See full cost breakdown + NTP earnings
/rtw-booking                 Step 5: Get a phone script to call AA and book it
```

Or build a specific route segment-by-segment:

```
/rtw-build                   Interactive: define segments → verify nonstop → check D-class → analyze
```

Claude understands the domain vocabulary (Rule 3015, NTP, YQ, D-class, tariff conferences) and can explain trade-offs, suggest alternatives, and help debug validation failures.

### For Developers (Cloned Repo)

If you've cloned the repo, the plugin also works as a project-level integration. Claude Code loads the project `CLAUDE.md` with module maps, conventions, and reference file pointers. The `.claude/settings.json` provides pre-approved bash permissions for common dev commands.

## Project Structure

```
rtw/
├── cli.py              # All Typer CLI commands
├── models.py           # Pydantic models (Itinerary, Segment, Ticket, etc.)
├── validator.py        # Rule 3015 validation orchestrator + context builder
├── rules/              # 24 individual rule implementations
│   ├── validity.py     # Return-to-origin, open-jaw pairs, continent count, ticket validity
│   ├── segments.py     # Segment count + per-continent limits
│   ├── carriers.py     # QR-first, eligible carriers, QF/JQ codeshare
│   ├── direction.py    # Direction of travel, ocean crossings, city-pair direction
│   ├── stopovers.py    # Minimum stopovers, origin-continent stopover limit
│   ├── hemisphere.py   # Hemisphere revisit (backtracking)
│   ├── intercontinental.py  # Intercontinental arrival/departure limits
│   ├── surface.py      # Same-city resolution, transoceanic surface ban
│   ├── geography.py    # Hawaii/Alaska, US/AU transcontinental, implicit Asia
│   └── country.py      # Origin-country intl flight limits, mid-journey return ban
├── airports.py         # Shared airportsdata loader (fail-fast)
├── cost.py             # Fare lookup + YQ calculation
├── ntp.py              # BA New Tier Points estimator
├── value.py            # Per-segment value analysis
├── booking.py          # Phone script + GDS command generator
├── search/             # Route search engine
│   ├── models.py       # Search-specific models
│   ├── generator.py    # Route generation
│   ├── scorer.py       # Route ranking
│   └── display.py      # Search result formatting
├── nonstop/            # Nonstop route pre-verification
│   ├── checker.py      # SerpAPI nonstop lookup + oneworld alternatives
│   └── models.py       # NonstopRoute, NonstopResult
├── verify/             # D-class availability verification
│   ├── models.py       # DClassResult, FlightAvailability, etc.
│   ├── verifier.py     # ExpertFlyer verification orchestrator
│   └── state.py        # Search state persistence
├── scraper/            # External data sources
│   ├── serpapi_flights.py  # Google Flights via SerpAPI
│   ├── expertflyer.py      # ExpertFlyer scraper (Playwright)
│   └── cache.py            # Response caching
├── continents.py       # Airport → continent mapping, country helpers, open-jaw validation
├── distance.py         # Great-circle distance calculator
├── data/               # Reference YAML files
│   ├── carriers.yaml   # oneworld carrier data (17 carriers incl. JQ codeshare)
│   ├── fares.yaml      # Base fare tables (AONE/DONE/LONE x 8 origins)
│   ├── ntp_rates.yaml  # BA NTP earning rates by carrier + booking class
│   ├── continents.yaml # Airport-continent mappings + country assignments
│   ├── same_cities.yaml # Same-city airport groups (NRT/HND, LHR/LGW, etc.)
│   ├── surcharges.yaml # YQ surcharge rates per carrier
│   └── hubs.yaml       # Carrier hub airports
└── output/             # Rich + plain text formatters
```

## Development

### Running Tests

```bash
uv run pytest                          # All tests (1080+)
uv run pytest tests/test_cost.py -x    # Single file, stop on failure
uv run pytest -m "not slow" -x         # Skip slow tests
uv run pytest -k "test_validate" -v    # Filter by name, verbose
```

### Linting

```bash
ruff check rtw/ tests/                 # Check for issues
ruff check --fix rtw/ tests/           # Auto-fix what's possible
```

### Adding a New Rule

1. Create a new file in `rtw/rules/` (e.g., `my_rule.py`)
2. Implement a function that takes a `ValidationContext` and returns `list[RuleResult]`
3. Register it in `rtw/validator.py`
4. Add tests in `tests/test_rules/`
5. Reference the authoritative source in `docs/01-fare-rules.md`

### Adding a New CLI Command

1. Add a function in `rtw/cli.py` decorated with `@app.command()`
2. Use Typer for argument parsing and Rich for output
3. Add `--json`, `--plain`, `--verbose`, `--quiet` flags for consistency
4. Add tests using `typer.testing.CliRunner`

## Key Concepts

### Rule 3015

The IATA fare rule that governs round-the-world ticket construction. The validator implements 24 rules across 10 modules:

| Rule | Section | What It Checks |
|------|---------|---------------|
| Return to Origin | General | Itinerary ends at origin (or permitted open-jaw) |
| Open-Jaw Pairs | §4(c) | Surface sector endpoints are in permitted bilateral pairs |
| Continent Count | General | Visited continents match ticket type (3/4/5/6) |
| Ticket Validity | §3 | Trip completes within 12-month validity period |
| Segment Count | §6 | Max 16 flown segments |
| Per-Continent Limit | §6 | Max segments per continent (default 4, some 5) |
| QR Not First | §4(j) | Qatar Airways cannot be the first carrier flown |
| Eligible Carriers | §4(j) | All carriers must be eligible oneworld members (codeshare recognition) |
| QF/JQ Codeshare | §4(j) | Jetstar codeshares restricted on AS/IB ticket stock |
| Direction of Travel | §7 | Consistent eastbound or westbound (no zigzagging) |
| Ocean Crossings | §7 | Both Atlantic and Pacific must be crossed by air |
| City-Pair Direction | §8 | Same city-pair cannot be flown twice in the same direction |
| Minimum Stopovers | General | At least 1 stopover required |
| Origin Stopover Limit | General | Max stopovers in origin continent |
| Hemisphere Revisit | §7 | No backtracking to a previously left tariff conference |
| Intercontinental Limits | General | Max intercontinental arrivals/departures per continent |
| Same-City Resolution | §4(d) | Resolves multi-airport cities (NRT/HND, LHR/LGW) |
| Transoceanic Surface | §4(i) | No surface sectors between TC1-TC2 or TC1-TC3 (SWP exemption) |
| Hawaii & Alaska | §4(k) | Special handling for US non-contiguous territories |
| US Transcontinental | §4(l) | Limits on US coast-to-coast nonstop flights |
| AU Transcontinental | §4(l) | Limits on Australia east coast-Perth/Darwin nonstops |
| Implicit Asia | Pricing | EU_ME-SWP direct flights count Asia as visited continent |
| Origin Country Intl | §4(f) | Max 1 international departure + 1 arrival from origin country |
| Origin Country Return | §4(f) | No mid-journey return to origin country (departure chain exemptions) |

See [docs/01-fare-rules.md](docs/01-fare-rules.md) for the complete rule reference.

### Tariff Conferences

The world is divided into three IATA Tariff Conferences:

| Conference | Regions |
|-----------|---------|
| **TC1** | North America, South America, Caribbean, Hawaii |
| **TC2** | Europe, Middle East, Africa |
| **TC3** | Asia, South West Pacific (Australia, NZ), Japan, Indian subcontinent |

Your ticket type (DONE**4**, LONE**3**, etc.) specifies how many of these conferences you must visit.

### D-Class Availability

oneworld Explorer tickets are booked in **D class** -- a special booking class that shows availability separately from regular economy/business. A flight might have plenty of business class seats for sale but zero D-class seats available.

The `verify` command checks ExpertFlyer to see the actual D-class inventory:
- **D9** = 9 seats available (wide open)
- **D5** = 5 seats
- **D0** = no seats (sold out in D class)

### YQ Surcharges

Airlines add fuel/insurance surcharges (YQ) on top of the base fare. These vary dramatically:
- **BA** London-New York: ~$500-800 per segment
- **JL** Tokyo-London: ~$50 per segment

Choosing low-YQ carriers (JAL, American, Finnair, Iberia) over high-YQ carriers (British Airways, Qantas) can save thousands on a multi-segment RTW ticket.

## License

MIT
