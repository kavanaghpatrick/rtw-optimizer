# RTW Optimizer

A CLI tool for optimizing [oneworld Explorer](https://www.oneworld.com/flights/round-the-world-fares) round-the-world tickets. Validates itineraries against IATA Rule 3015, estimates costs + surcharges, calculates BA NTP earnings, searches for optimal routes with live pricing, verifies D-class seat availability, and generates phone booking scripts.

## Why This Exists

oneworld Explorer fares let you fly around the world on oneworld airlines for a flat fare based on continents visited. A business class ticket visiting 4 continents starts at ~$4,000 from Cairo or ~$10,500 from New York.

The catch: these tickets are governed by [IATA Rule 3015](01-fare-rules.md) -- 24 rules around direction of travel, continent crossings, backtracking, carrier requirements, segment limits, and more. Building a valid itinerary by hand means juggling all of these while checking seat availability across a dozen airlines. This tool automates all of that.

## Quick Start

```bash
git clone https://github.com/kavanaghpatrick/rtw-optimizer.git
cd rtw-optimizer
uv sync                        # Requires Python 3.11+ and uv
python3 -m rtw --help          # Show all commands
uv run pytest -x -q            # Run test suite (1080+ tests)
```

**Optional API keys** for advanced features:

| Service | What For | Setup |
|---------|----------|-------|
| [SerpAPI](https://serpapi.com) | Live Google Flights pricing | `export SERPAPI_API_KEY=your_key` |
| [ExpertFlyer](https://www.expertflyer.com) | D-class seat availability | `python3 -m rtw login expertflyer` + `uv run playwright install chromium` |

Without these, validate/cost/NTP/value/booking work fully. Search works without live pricing. Verify requires ExpertFlyer.

## Usage

The typical workflow: **search** for routes, **verify** D-class availability, **analyze** costs, then **book**.

```bash
# Search for routes visiting specific cities
python3 -m rtw search --cities LHR,NRT,JFK --origin SYD --type DONE4

# Validate an itinerary against all 24 Rule 3015 constraints
python3 -m rtw validate itinerary.yaml

# Full analysis: validate + cost + NTP + value
python3 -m rtw analyze itinerary.yaml

# Build a YAML itinerary from a route string
python3 -m rtw build --route "LAX-HND:JL,HND-SYD:JL,SYD-DOH:QR,DOH-LAX:QR" \
  --origin LAX --type DONE4 --departure 2026-04-01 --validate --ntp

# Verify D-class seat availability (needs ExpertFlyer)
python3 -m rtw verify

# Generate phone booking script with GDS commands
python3 -m rtw booking itinerary.yaml
```

### All Commands

| Command | Purpose |
|---------|---------|
| `search` | Find valid RTW routes, score and rank them, optionally with live pricing |
| `validate` | Check itinerary against Rule 3015 (24 rules across direction, segments, carriers, geography, etc.) |
| `analyze` | Full pipeline: validate + cost + NTP + value |
| `cost` | Estimate base fare + YQ surcharges per segment |
| `ntp` | Calculate BA New Tier Points earnings |
| `value` | Per-segment value rating (cost vs distance) |
| `booking` | Generate phone script + GDS commands for the AA RTW desk |
| `build` | Generate YAML itinerary from a route string |
| `verify` | D-class availability check via ExpertFlyer |
| `scan-dates` | Scan date range for D-class availability |
| `check-nonstop` | Verify nonstop service exists on a city-pair |
| `continent` | Airport to continent/tariff conference lookup |
| `show` | Pretty-print itinerary segments |
| `new` | Output blank YAML itinerary template |

Run `python3 -m rtw <command> --help` for full options on any command.

## Itinerary Format

Itineraries are YAML files:

```yaml
ticket:
  type: DONE4          # Class + continents (AONE/DONE/LONE + 3-6)
  cabin: business
  origin: SYD

segments:
  - from: SYD
    to: HKG
    carrier: CX        # IATA airline code (oneworld member)
    type: stopover      # stopover (>24h), transfer (<24h), or surface (overland)

  - from: HKG
    to: LHR
    carrier: CX
    type: stopover

  - from: LHR
    to: JFK
    carrier: BA
    type: stopover

  - from: JFK
    to: SYD
    carrier: QF
    type: stopover
```

Segments also support `operating_carrier` for codeshares (e.g., QF-marketed, JQ-operated) and `date` for ticket validity checks.

## Fares and Carriers

Ticket types follow the pattern `{class}{continents}`: **AONE** (First), **DONE** (Business), **LONE** (Economy), each with 3-6 continents. Fares vary dramatically by origin -- a DONE4 from Cairo is $4,000 vs $10,500 from New York. Run `python3 -m rtw cost --compare DONE4` to see all origins ranked by price.

**oneworld carriers**: BA, CX, QF, JL, AA, QR, IB, AY, MH, RJ, UL, FJ, AS, AT, WY. S7 is suspended (sanctions). Jetstar (JQ) is permitted as QF codeshare only.

**YQ surcharges** vary dramatically by carrier -- BA/QF charge $500-800/segment while JL/AY charge ~$50. Choosing low-YQ carriers can save thousands on a multi-segment ticket.

## Using with Claude Code

This project is a [Claude Code](https://claude.ai/claude-code) plugin with 12 slash commands:

```bash
claude plugin add github:kavanaghpatrick/rtw-optimizer
```

Key commands: `/rtw-plan` (interactive trip planner), `/rtw-search` (find routes), `/rtw-build` (build + verify + analyze), `/rtw-analyze` (full pipeline), `/rtw-booking` (phone script). Run `/rtw-help` for the full list.

A `SessionStart` hook auto-checks your environment on each session. Run `/rtw-init` for first-time credential setup.

## Development

```bash
uv run pytest                          # All tests (1080+)
uv run pytest tests/test_cost.py -x    # Single file, stop on failure
ruff check rtw/ tests/                 # Lint
```

The validator runs 24 rules across 10 modules in `rtw/rules/`. Each rule returns `RuleResult` with severity (PASS/WARNING/VIOLATION/INFO). See [01-fare-rules.md](01-fare-rules.md) for the authoritative rule reference and `CLAUDE.md` for the full module map and project conventions.

## License

MIT
