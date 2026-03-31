# Cost, NTP, Value, and Booking Modules

Technical documentation for the four financial analysis modules in the RTW Optimizer: cost estimation, NTP calculation, segment value analysis, and booking script generation.

## Module Overview

| Module | File | Primary Class | Output Model |
|--------|------|---------------|--------------|
| Cost | `rtw/cost.py` | `CostEstimator` | `CostEstimate` |
| NTP | `rtw/ntp.py` | `NTPCalculator` | `NTPEstimate` (list) |
| Value | `rtw/value.py` | `SegmentValueAnalyzer` | `SegmentValue` (list) |
| Booking | `rtw/booking.py` | `BookingGenerator` | `BookingScript` |

All four modules accept a parsed `Itinerary` (Pydantic v2 model) and produce structured output models that are passed to formatters in `rtw/output/` for display.

---

## 1. Cost Estimation (`rtw/cost.py`)

### Architecture

`CostEstimator` loads three YAML data files at initialization:

- **`fares.yaml`** -- Base fares by origin city and ticket type (8 origins x 12 ticket types = 96 fares)
- **`surcharges.yaml`** -- Per-carrier YQ estimates and plating carrier comparison data
- **`carriers.yaml`** -- Carrier reference with `yq_estimate_per_segment` field

### Base Fare Lookup

`get_base_fare(origin, ticket_type)` performs a simple dictionary lookup:

```
fares.yaml -> origins -> {IATA code} -> fares -> {ticket_type}
```

Returns `0.0` if the origin or ticket type is missing. The eight supported origin cities are:

| Origin | Currency | DONE4 Fare | Notes |
|--------|----------|-----------|-------|
| CAI | EGP | $4,000 | Cheapest; EGP devaluation advantage |
| OSL | NOK | $5,400 | NOK weakness; easy London positioning |
| JNB | ZAR | $5,000 | ZAR weakness; good if Africa on route |
| CMB | LKR | $5,200 | SriLankan is oneworld |
| NRT | JPY | $6,360 | Higher taxes/YQ |
| LHR | GBP | $8,000 | High UK departure taxes |
| SYD | AUD | $8,800 | Ex-Japan is roughly half price |
| JFK | USD | $10,500 | Most expensive; consider positioning |

All fares are stored as approximate USD equivalents.

### FareLookupError

When `estimate_total()` is called and `get_base_fare()` returns `$0.0` (missing data), the method raises `FareLookupError` with a message pointing to `fares.yaml`. The CLI catches this exception and displays it in an error panel with exit code 2.

### YQ Surcharge Calculation

`estimate_surcharges(itinerary, plating_carrier)` iterates over every segment and applies these rules:

1. **Surface segments**: $0 YQ (skipped entirely)
2. **AA domestic (US-to-US)**: $0 YQ. US airports are determined dynamically from `airportsdata` at module load via `_US_AIRPORTS = {code for code, info in airports_db.items() if info.get("country") == "US"}`
3. **All other segments**: Look up the carrier's per-segment YQ estimate from `carriers.yaml` first (`yq_estimate_per_segment`), falling back to `surcharges.yaml` (`carrier_yq`). This dual-source approach allows carrier-level overrides.

Per-carrier YQ estimates (approximate USD per segment):

| Carrier | YQ/Segment | Tier |
|---------|-----------|------|
| AY | $10 | Very low |
| JL | $12 | Very low |
| FJ | $20 | Very low |
| AS | $40 | Low |
| AA | $50 | Low |
| UL | $50 | Low |
| MH | $60 | Low |
| WY | $90 | Low |
| AT | $100 | Medium |
| QR | $150 | Medium (non-linear) |
| RJ | $170 | Medium |
| CX | $200 | Medium |
| IB | $220 | High |
| BA | $321 | Very high |
| QF | $334 | Very high |

### Total Cost Estimation

`estimate_total(itinerary, plating_carrier)` computes:

```
per_person = base_fare + total_yq
total = per_person * passengers
```

Returns a `CostEstimate` model with all components broken out. The `plating_carrier` parameter defaults to `"AA"` and affects the notes field (AA RTW desk recommended for flexibility).

### Origin and Plating Comparison

Two comparison methods support fare shopping:

- **`compare_origins(ticket_type)`**: Returns all origins sorted cheapest-first for a given ticket type. Used in verbose CLI output.
- **`compare_plating(itinerary)`**: Returns plating carrier options sorted by typical total YQ. The five plating options with typical DONE4 YQ totals: QR ($800), MH ($900), CX ($1,500), AA ($1,800), BA ($2,500).

---

## 2. NTP Calculation (`rtw/ntp.py`)

### Architecture

`NTPCalculator` loads two data files:

- **`ntp_rates.yaml`** -- Earning rates by carrier and booking class
- **`fares.yaml`** -- For default fare lookup when `total_fare_usd` is not provided

It also instantiates a `DistanceCalculator` (haversine great-circle distance via `airportsdata`).

### Two Earning Methods

BA New Tier Points use two distinct earning models depending on the marketing carrier:

#### Revenue-Based (BA, AA, IB)

Formula: **1 NTP per GBP 1 of eligible spend**

The fare is allocated proportionally across segments by distance:

```
segment_share_usd = (segment_distance / total_itinerary_distance) * total_fare_usd
segment_share_gbp = segment_share_usd * 0.79  (hardcoded USD-to-GBP rate)
ntp = segment_share_gbp
```

BA segments receive an additional flat bonus per segment. For Club World (long-haul business), this is **+400 NTP** per segment. Other BA cabin bonuses are defined in `ntp_rates.yaml` (`ba_bonus` section) but currently only `club_world` is applied in code.

The confidence level for revenue-based estimates is `"estimated"` because the fare allocation is an approximation.

#### Distance-Based (All Other Carriers)

Formula: **NTP = distance_miles * (rate_percentage / 100)**

Rates vary by carrier and booking class. For D-class (typical RTW business booking):

| Carrier | D-Class Rate | NTP Tier |
|---------|-------------|----------|
| QR | 50% | Tier 1 (most generous) |
| JL | 50% | Tier 1 |
| AY | 50% | Tier 1 |
| CX | 25% | Tier 2 |
| FJ | 25% | Tier 2 |
| RJ | 25% | Tier 2 |
| QF | 25% | Tier 2 |
| MH | 25% | Tier 2 |
| AS | 25% | Tier 2 |
| AT | 25% | Tier 2 |
| UL | 25% | Tier 2 |
| WY | 12.5% | Tier 3 (lowest for business) |

The confidence level for distance-based estimates is `"calculated"` (deterministic).

### Full Itinerary Calculation Flow

`calculate(itinerary, booking_class, total_fare_usd)`:

1. **Resolve total fare**: If `total_fare_usd` is not provided, look it up from `fares.yaml` using the itinerary's origin and ticket type. Falls back to CAI fares (cheapest origin) if the origin is missing, with a hardcoded $4,000 as last resort.
2. **Pre-compute distances**: Calculate haversine great-circle miles for every segment (0 for surface sectors).
3. **Per-segment calculation**: For each segment:
   - Surface segments: 0 NTP, `"Surface sector -- no NTP earned"`
   - Revenue-based carriers (BA, AA, IB): Distance-weighted fare allocation
   - Distance-based carriers: Percentage of miles
   - Unknown carriers: Distance-based with 0 rate (effectively 0 NTP)

### Special Cases

- **FJ ATR-72 segments**: When carrier is FJ, distance < 700 miles, and booking class is D, adds a note that D maps to Y cabin on ATR-72 aircraft but still earns at D-class rate.
- **Unknown carriers**: Treated as distance-based with 0% rate, with an explanatory note.

---

## 3. Value Analysis (`rtw/value.py`)

### Architecture

`SegmentValueAnalyzer` uses only `DistanceCalculator`. It has no data file dependencies -- all thresholds and rates are hardcoded constants.

### Cost Estimation Heuristic

The module estimates what a one-way business class ticket would cost on the open market for each segment, using great-circle distance as a proxy:

```
base_cost = distance_miles * $0.30/mile
```

Distance multipliers adjust for route economics:

| Distance | Multiplier | Rationale |
|----------|-----------|-----------|
| > 5,000 miles | 1.2x | Ultra-long-haul premium |
| < 500 miles | 0.8x | Short-haul discount |
| 500-5,000 miles | 1.0x | Standard rate |

### Value Classification

The estimated business class cost determines the value verdict:

| Estimated Cost | Verdict | Suggestion |
|---------------|---------|-----------|
| >= $1,500 | Excellent | "Great value segment" |
| >= $500 | Good | "Solid value segment" |
| >= $250 | Moderate | "Acceptable value" |
| < $250 | Low | "Consider side trip to maximize value" |

### Surface Sector Handling

Surface segments receive: `$0.00` cost, `"N/A"` verdict, `"Surface sector"` suggestion.

### Interpretation

Higher estimated cost = more value extracted from the RTW ticket, because that segment would be expensive to purchase separately. The core principle: **use RTW ticket segments for long-haul business class flights that are expensive to buy individually, and use low-cost carriers or surface sectors for short hops.**

---

## 4. Booking Script Generation (`rtw/booking.py`)

### Architecture

`BookingGenerator` loads two data files:

- **`carriers.yaml`** -- For booking class resolution (delegates to `rtw/carriers.py`)
- **`same_cities.yaml`** -- Airport groups for same-city transition warnings (15 city groups, e.g., LON = LHR/LGW/STN/LCY/LTN)

### Output Structure

`BookingScript` (Pydantic model) contains four sections:

| Field | Type | Content |
|-------|------|---------|
| `opening` | `str` | Phone greeting with ticket summary |
| `segments` | `list[SegmentScript]` | Per-segment phone instructions + warnings |
| `closing` | `str` | Post-booking checklist (7 items) |
| `gds_commands` | `list[str]` | Amadeus GDS command sequence |
| `warnings` | `list[str]` | Aggregated warnings from all segments + global warnings |

### Phone Script Generation

#### Opening Script

Summarizes the booking request: ticket type, passenger count, origin, departure date, plating carrier, and segment counts (flown + surface).

#### Per-Segment Instructions

For each segment, generates:
- Segment number, carrier, flight number, route, date, booking class
- Through-flight via annotations (if `segment.via` is set)
- FJ ATR-72 notes (if applicable)
- Segment-level notes from the YAML file

#### Closing Checklist

Seven verification items:
1. Confirm all flown segments ticketed
2. Verify plating carrier
3. Confirm passenger count on all segments
4. Request fare quote for ticket type
5. Verify total matches expected fare + YQ
6. Ask about change/cancellation flexibility
7. Confirm first segment date lock (if departure date is set)

### Booking Class Resolution

Delegated to `rtw/carriers.py:get_booking_class()`:

| Cabin | Class | Exception |
|-------|-------|-----------|
| Business | D | AA uses H class |
| Economy | L | All carriers |
| First | A | All carriers |

### Warning System

The booking generator produces six categories of warnings:

#### 1. Same-City Transition Warnings
Triggered when consecutive segments involve different airports in the same city group (e.g., arriving LHR, departing LGW). The passenger must physically transfer between airports.

#### 2. Married Segment Warnings
Triggered when a transit segment connects to the next segment on the same date. Warns that changing one flight may cancel both if booked as married segments. Suggests requesting separate PNRs.

#### 3. Iberia Mainline Verification
Triggered for any IB segment touching MAD. Warns to verify the operating carrier is mainline Iberia (IB), not Iberia Express (I2), which may not be eligible.

#### 4. Through-Flight Via-Stop Warnings
Triggered when a segment has `via` airports set. Warns that the through-flight must be booked as a single segment and cannot be split without reissue and potential fees.

#### 5. Hub O&D Control Warnings
Triggered for CX (hub: HKG) and QR (hub: DOH) segments. Two sub-cases:
- **Segment doesn't touch hub**: Warns D-class may be married through the hub.
- **Segment terminates at hub**: Warns about origin-destination revenue management. Suggests presenting the routing to the agent as connected (e.g., "SYD to NRT via HKG") rather than standalone (e.g., "SYD to HKG").

#### 6. Global Warnings
- **First segment date lock**: After ticketing, the first segment date is fixed while other dates remain flexible. Added whenever a departure date is present.

### GDS Command Generation

Generates an Amadeus GDS command sequence:

1. **`FQD`** -- Fare display (round-trip same city with RTW designator): `FQD{origin}{origin}/VRW/D{date}`
2. **`SS`** -- Sell segment entries for each flown segment: `SS {class}1 {flight} {date} {city_pair}`
3. **`ARNK`** -- "Arrival Not Known" for surface sectors
4. **`FXP`** -- Price the itinerary
5. **`OSI YY OW RTW`** -- Other service information (oneworld RTW flag)
6. **`/R,VC-{plating}`** -- Plating carrier override

Date format is GDS-standard: `15MAR` (no year). Flight numbers default to `{carrier}0000` when not specified in the itinerary.

---

## 5. Module Interactions

### Data Flow

```
YAML itinerary file
       |
       v
   _load_itinerary()  [cli.py - parses YAML into Itinerary model]
       |
       +---> CostEstimator.estimate_total()      --> CostEstimate
       |         reads: fares.yaml, surcharges.yaml, carriers.yaml
       |         uses: airports_db (for US domestic check)
       |
       +---> NTPCalculator.calculate()            --> list[NTPEstimate]
       |         reads: ntp_rates.yaml, fares.yaml
       |         uses: DistanceCalculator (haversine)
       |
       +---> SegmentValueAnalyzer.analyze()       --> list[SegmentValue]
       |         uses: DistanceCalculator (haversine)
       |
       +---> BookingGenerator.generate()          --> BookingScript
       |         reads: carriers.yaml, same_cities.yaml
       |         uses: rtw.carriers.get_booking_class()
       |
       v
   get_formatter(format)  -->  format_cost() / format_ntp() / format_value() / format_booking()
       |
       v
   typer.echo() to stdout
```

### Shared Dependencies

| Dependency | Used By | Purpose |
|-----------|---------|---------|
| `fares.yaml` | Cost, NTP | Base fare lookup |
| `carriers.yaml` | Cost, Booking | YQ estimates, booking classes |
| `surcharges.yaml` | Cost | Per-carrier YQ, plating comparison |
| `ntp_rates.yaml` | NTP | Earning rates by carrier/class |
| `same_cities.yaml` | Booking | Same-city airport groups |
| `DistanceCalculator` | NTP, Value | Great-circle distance |
| `airports_db` | Cost, Distance | Airport coordinates and country data |
| `rtw.carriers` | Booking | Booking class resolution |

### The `analyze` Pipeline

The `analyze` CLI command runs all four modules sequentially on the same itinerary:

1. **Validate** (Rule 3015 checks) -- exits with code 1 if violations found
2. **Cost** -- base fare + YQ surcharges
3. **NTP** -- per-segment NTP earnings
4. **Value** -- per-segment value classification

Each step's output is independently formatted and printed. The modules do not depend on each other's output -- they all operate directly on the `Itinerary` model.

### Output Formatting

All output models are passed through `rtw/output/get_formatter()` which returns either a Rich formatter (default, with tables and colors) or a plain text formatter. The formatter has dedicated methods: `format_cost()`, `format_ntp()`, `format_value()`, `format_booking()`. JSON output serializes the Pydantic models directly via `model_dump(mode="json")`.

---

## Key Design Decisions

1. **No cross-module dependencies**: Cost, NTP, Value, and Booking all operate independently on the Itinerary model. This keeps each module testable in isolation.

2. **Data-driven configuration**: All rates, fares, and surcharges live in YAML files rather than hardcoded values (except Value module thresholds). This allows updates without code changes.

3. **Dual-source YQ lookup**: Surcharges check `carriers.yaml` first, then fall back to `surcharges.yaml`. This allows per-carrier overrides while maintaining a separate surcharge reference.

4. **Conservative NTP estimation**: Revenue-based NTP uses distance-weighted fare allocation (an approximation), marked with `confidence: "estimated"`. Distance-based NTP is deterministic, marked `confidence: "calculated"`.

5. **Defensive booking warnings**: The booking generator is deliberately cautious, flagging potential issues (married segments, O&D control, same-city transfers, Iberia Express) even when they may not apply. Better to over-warn than miss a booking risk.

6. **AA H-class exception**: American Airlines uses H class instead of D for oneworld Explorer business. This is handled in the shared `rtw/carriers.py` module, which both Booking and Verify modules use.
