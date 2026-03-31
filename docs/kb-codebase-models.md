# RTW Optimizer -- Data Model Layer Reference

Complete reference for every Pydantic model, enum, YAML data file, and their interconnections in the RTW Optimizer codebase.

---

## 1. Enums

All enums are defined in `rtw/models.py` unless otherwise noted. Every enum inherits from `str, Enum` so it serialises as its string value.

### TicketType

oneworld Explorer ticket types. Naming convention: `{Cabin}{Continents}`.

| Value | Cabin | Continents |
|-------|-------|------------|
| `AONE3` - `AONE6` | First (A) | 3-6 |
| `DONE3` - `DONE6` | Business (D) | 3-6 |
| `LONE3` - `LONE6` | Economy (L) | 3-6 |

The prefix letter matches the GDS booking class used on most carriers (D = business, L = economy, A = first). The trailing digit is the continent count. `Ticket.num_continents` extracts it via `int(self.type.value[-1])`.

### CabinClass

```
ECONOMY = "economy"
BUSINESS = "business"
FIRST = "first"
```

### SegmentType

```
STOPOVER = "stopover"    # >24h stay
TRANSIT  = "transit"     # <=24h connection
SURFACE  = "surface"     # Ground transport (not flown)
FINAL    = "final"       # Last segment returning to origin
```

### Continent

oneworld Explorer's six continent divisions (NOT the standard seven continents):

| Value | Name | Tariff Conference |
|-------|------|-------------------|
| `EU_ME` | Europe / Middle East | TC2 |
| `Africa` | Sub-Saharan Africa | TC2 |
| `Asia` | Asia | TC3 |
| `SWP` | South West Pacific | TC3 |
| `N_America` | North America | TC1 |
| `S_America` | South America | TC1 |

### TariffConference

```
TC1 = "TC1"   # Americas (N_America, S_America)
TC2 = "TC2"   # Europe, Middle East, Africa (EU_ME, Africa)
TC3 = "TC3"   # Asia, South West Pacific (Asia, SWP)
```

Mapping is defined in `CONTINENT_TO_TC` dict in `models.py`.

### NTPMethod

How BA New Tier Points are earned on a carrier:

```
REVENUE  = "revenue"    # BA, AA, IB: 1 NTP per GBP 1 of eligible spend
DISTANCE = "distance"   # All others: percentage of great-circle miles
```

### Severity

Validation result severity levels:

```
VIOLATION = "violation"   # Rule broken, ticket invalid
WARNING   = "warning"     # Ambiguous or risky
INFO      = "info"        # Informational
```

### Direction (rtw/search/models.py)

```
EASTBOUND = "eastbound"
WESTBOUND = "westbound"
```

### AvailabilityStatus (rtw/search/models.py)

```
AVAILABLE     = "available"
LIKELY        = "likely"
UNKNOWN       = "unknown"
NOT_AVAILABLE = "not_available"
NOT_CHECKED   = "not_checked"
```

### DClassStatus (rtw/verify/models.py)

```
AVAILABLE     = "available"
NOT_AVAILABLE = "not_available"
UNKNOWN       = "unknown"
ERROR         = "error"
CACHED        = "cached"
```

---

## 2. Core Itinerary Models (rtw/models.py)

### Ticket

RTW ticket metadata. Top-level configuration for an itinerary.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `type` | `TicketType` | required | e.g. DONE4 |
| `cabin` | `CabinClass` | required | economy / business / first |
| `origin` | `str` | 3 chars, uppercase validator | IATA origin airport |
| `passengers` | `int` | 1-9, default 1 | Passenger count |
| `departure` | `Optional[date]` | | Trip start date |
| `plating_carrier` | `Optional[str]` | 2 chars, uppercase validator | Carrier issuing the ticket |

Computed properties:
- `num_continents` -- extracts the trailing digit from `type.value` (e.g. DONE4 -> 4)
- `fare_prefix` -- extracts the first character (D, L, or A)

### Segment

A single flight or surface segment within an itinerary.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `from_airport` | `str` | 3 chars, alias `"from"`, uppercase validator | Departure airport |
| `to_airport` | `str` | 3 chars, alias `"to"`, uppercase validator | Arrival airport |
| `carrier` | `Optional[str]` | 2 chars, uppercase validator | Marketing carrier |
| `operating_carrier` | `Optional[str]` | 2 chars, uppercase validator | Operating carrier (if different) |
| `flight` | `Optional[str]` | | Flight number |
| `date` | `Optional[date]` | | Departure date |
| `type` | `SegmentType` | default STOPOVER | Segment classification |
| `via` | `Optional[str \| list[str]]` | normalized to list[str] uppercase | Intermediate stop airports (through-flights) |
| `notes` | `Optional[str]` | | Freeform notes |

Config: `populate_by_name = True` (allows both `from` and `from_airport` in input).

The `via` field validator normalises a single string to a one-element list and uppercases all values. This supports through-flights where a single flight number stops at intermediate airports.

Computed properties:
- `has_via` -- True if via list is non-empty
- `via_airports` -- returns `self.via` or empty list
- `is_surface` -- True if type is SURFACE
- `is_stopover` -- True if type is STOPOVER
- `is_flown` -- True if type is NOT SURFACE

### Itinerary

Complete RTW itinerary, composed of a Ticket and a list of Segments.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `ticket` | `Ticket` | required | Ticket metadata |
| `segments` | `list[Segment]` | min_length=1 | Ordered list of segments |

Computed properties:
- `flown_segments` -- excludes surface sectors
- `surface_segments` -- surface sectors only
- `stopovers` -- stopover segments only

---

## 3. Reference Data Models (rtw/models.py)

### Airport

Airport reference data model (not used for bulk storage; the primary airport database is `airportsdata` loaded via `rtw/airports.py`).

| Field | Type | Description |
|-------|------|-------------|
| `iata` | `str` (3 chars) | IATA code |
| `name` | `str` | Airport name |
| `city` | `str` | City name |
| `country` | `str` | ISO country code |
| `continent` | `Optional[Continent]` | oneworld continent |
| `tariff_conference` | `Optional[TariffConference]` | TC zone |
| `latitude` / `longitude` | `Optional[float]` | Coordinates |
| `same_city_group` | `Optional[str]` | City group key (e.g. "TYO" for NRT/HND) |

### CarrierInfo

Carrier reference data, matching the structure in `carriers.yaml`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `code` | `str` (2 chars) | required | IATA carrier code |
| `name` | `str` | required | Carrier name |
| `alliance` | `str` | "oneworld" | Alliance membership |
| `eligible` | `bool` | True | Eligible for oneworld Explorer |
| `ntp_method` | `Optional[NTPMethod]` | | Revenue or distance |
| `ntp_rates` | `Optional[dict[str, float]]` | | NTP percentage by booking class |
| `yq_tier` | `Optional[str]` | | Surcharge tier (very_low to very_high) |
| `yq_estimate_per_segment` | `Optional[float]` | | Approximate USD YQ per segment |
| `rtw_booking_class` | `Optional[str]` | | Booking class for OWE (D for most, H for AA) |
| `notes` | `str` | "" | Freeform notes |

### FareReference

Fare reference for a specific origin (not currently instantiated as Pydantic objects at runtime; fares are loaded as raw dicts from `fares.yaml`).

| Field | Type | Description |
|-------|------|-------------|
| `origin` | `str` (3 chars) | Origin airport |
| `ticket_type` | `TicketType` | Fare type |
| `base_fare_usd` | `float` | Base fare in USD |
| `currency` | `str` | Original filing currency |
| `last_updated` | `Optional[date]` | Data freshness |

---

## 4. Result Models (rtw/models.py)

### RuleResult

Output from a single rule check in the validator.

| Field | Type | Description |
|-------|------|-------------|
| `rule_id` | `str` | Unique rule identifier |
| `rule_name` | `str` | Human-readable rule name |
| `rule_reference` | `str` | e.g. "Rule 3015 S4" |
| `passed` | `bool` | Whether the rule passed |
| `severity` | `Severity` | VIOLATION, WARNING, or INFO |
| `message` | `str` | Explanation text |
| `fix_suggestion` | `str` | How to fix violations |
| `segments_involved` | `list[int]` | Segment indices that triggered the rule |

### ValidationReport

Complete validation report aggregating all rule results.

| Field | Type | Description |
|-------|------|-------------|
| `itinerary` | `Itinerary` | The validated itinerary |
| `results` | `list[RuleResult]` | All rule check results |

Computed properties:
- `passed` -- True if no violations (warnings are OK)
- `violations` / `warnings` -- filtered sublists
- `violation_count` / `warning_count` -- counts

### NTPEstimate

BA New Tier Points estimate for a single segment.

| Field | Type | Description |
|-------|------|-------------|
| `segment_index` | `int` | Segment position in itinerary |
| `route` | `str` | e.g. "DOH-NRT" |
| `carrier` | `str` | Marketing carrier |
| `distance_miles` | `float` | Great-circle distance |
| `method` | `NTPMethod` | Revenue or distance |
| `rate` | `Optional[float]` | Percentage for distance-based |
| `estimated_ntp` | `float` | Calculated NTP |
| `confidence` | `str` | "calculated" or "estimated" |
| `notes` | `str` | Additional info |

### CostEstimate

Cost estimate for an entire itinerary.

| Field | Type | Description |
|-------|------|-------------|
| `origin` | `str` | Origin airport |
| `ticket_type` | `TicketType` | Fare type |
| `base_fare_usd` | `float` | Base fare |
| `total_yq_usd` | `float` | Total surcharges |
| `total_per_person_usd` | `float` | Per-person total |
| `total_all_pax_usd` | `float` | Total for all passengers |
| `passengers` | `int` | Passenger count |
| `plating_carrier` | `str` | Issuing carrier |
| `notes` | `str` | Additional info |

### SegmentValue

Per-segment value analysis comparing RTW allocation vs market price.

| Field | Type | Description |
|-------|------|-------------|
| `segment_index` | `int` | Segment position |
| `route` | `str` | e.g. "DOH-NRT" |
| `carrier` | `str` | Marketing carrier |
| `estimated_j_cost_usd` | `float` | Market price for business class |
| `verdict` | `str` | "Excellent", "Good", "Moderate", "Low" |
| `suggestion` | `str` | Optimisation advice |
| `source` | `str` | "reference" or "scraped" |

---

## 5. Search Models (rtw/search/models.py)

### SearchQuery

User's search request for finding RTW route options.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `cities` | `list[str]` | 3-8 items, uppercase validator | Must-visit cities |
| `origin` | `str` | 3 chars, uppercase validator | Trip origin |
| `date_from` / `date_to` | `date` | date_from < date_to | Travel window |
| `cabin` | `CabinClass` | | Target cabin |
| `ticket_type` | `TicketType` | | Fare type |
| `top_n` | `int` | >= 1, default 10 | Max results |
| `rank_by` | `str` | default "availability" | Ranking strategy |

### SegmentAvailability

Availability result for a single segment from search.

| Field | Type | Description |
|-------|------|-------------|
| `status` | `AvailabilityStatus` | Availability status |
| `price_usd` | `Optional[float]` | Market price |
| `carrier` | `Optional[str]` | Carrier |
| `date` | `Optional[date]` | Date checked |
| `stops` | `Optional[int]` | Stop count |
| `error_reason` | `Optional[str]` | Error details |
| `source` | `Optional[str]` | Data source |
| `flight_number` | `Optional[str]` | Flight number |
| `duration_minutes` | `Optional[int]` | Flight duration |

### RouteSegment

A segment in a generated route candidate.

| Field | Type | Description |
|-------|------|-------------|
| `from_airport` | `str` (3 chars) | Departure airport |
| `to_airport` | `str` (3 chars) | Arrival airport |
| `carrier` | `str` (2 chars) | Carrier |
| `segment_type` | `SegmentType` | Segment classification |
| `availability` | `Optional[SegmentAvailability]` | Availability data |

### CandidateItinerary

A generated RTW itinerary candidate before scoring.

| Field | Type | Description |
|-------|------|-------------|
| `itinerary` | `Itinerary` | Full itinerary |
| `direction` | `Direction` | Eastbound or westbound |
| `route_segments` | `list[RouteSegment]` | Segments with availability |
| `hub_count` | `int` | Number of hub connections used |
| `must_visit_cities` | `list[str]` | Cities the user requested |

### ScoredCandidate

A candidate with computed scores.

| Field | Type | Description |
|-------|------|-------------|
| `candidate` | `CandidateItinerary` | The itinerary |
| `availability_score` | `float` (default 50) | Seat availability score |
| `quality_score` | `float` (default 50) | Route quality score |
| `cost_score` | `float` (default 50) | Cost efficiency score |
| `composite_score` | `float` (default 50) | Weighted overall score |
| `rank` | `int` | Position in results |
| `estimated_cost_usd` | `float` | Estimated total cost |
| `availability_pct` | `float` | % segments with availability |
| `fare_comparison` | `Optional[FareComparison]` | Value analysis vs market |

### FareComparison (rtw/search/fare_comparison.py)

Compares RTW base fare against sum of individual segment market prices.

| Field | Type | Description |
|-------|------|-------------|
| `base_fare_usd` | `float` | RTW ticket base fare |
| `segment_total_usd` | `float` | Sum of segment market prices |
| `segments_priced` | `int` | How many segments had prices |
| `segments_total` | `int` | Total segment count |
| `savings_usd` | `float` | Savings vs buying individually |
| `value_multiplier` | `float` | segment_total / base_fare ratio |

Computed properties:
- `verdict` -- "excellent" (>=3x), "great" (>=2x), "good" (>=1.5x), "fair" (>=1x), "poor"
- `is_complete` -- True if all segments priced

### SearchResult

Complete search result returned to the user.

| Field | Type | Description |
|-------|------|-------------|
| `query` | `SearchQuery` | Original search query |
| `candidates_generated` | `int` | Total candidates evaluated |
| `options` | `list[ScoredCandidate]` | Ranked results |
| `base_fare_usd` | `float` | Base fare for the ticket type |

---

## 6. Verify Models (rtw/verify/models.py)

### FlightAvailability

D-class availability for a single flight option.

| Field | Type | Description |
|-------|------|-------------|
| `carrier` | `Optional[str]` | Carrier code |
| `flight_number` | `Optional[str]` | Flight number |
| `origin` / `destination` | `Optional[str]` | Airport codes |
| `depart_time` / `arrive_time` | `Optional[str]` | Times as strings |
| `aircraft` | `Optional[str]` | Aircraft type |
| `seats` | `int` (0-9) | Seats in booking class |
| `booking_class` | `str` (default "D") | Booking class checked |
| `stops` | `int` (>=0) | Number of stops |

### AlternateDateResult

D-class availability on a nearby date.

| Field | Type | Description |
|-------|------|-------------|
| `date` | `date` | The alternate date |
| `seats` | `int` (0-9) | Seats available |
| `offset_days` | `int` (-3 to +3) | Offset from target date |

### DClassResult

Complete result for one segment's availability check.

| Field | Type | Description |
|-------|------|-------------|
| `status` | `DClassStatus` | Overall status |
| `seats` | `int` (0-9) | Best seat count |
| `flight_number` | `Optional[str]` | Specific flight |
| `carrier` | `str` | Carrier checked |
| `origin` / `destination` | `str` (3 chars) | Airport pair |
| `target_date` | `date` | Date searched |
| `booking_class` | `str` (default "D") | Class searched |
| `checked_at` | `datetime` (UTC) | Timestamp |
| `from_cache` | `bool` | Whether result was cached |
| `error_message` | `Optional[str]` | Error details |
| `alternate_dates` | `list[AlternateDateResult]` | Nearby date results |
| `flights` | `list[FlightAvailability]` | Individual flight options |

Computed properties:
- `available` -- True if status AVAILABLE and seats > 0
- `available_flights` -- flights with seats > 0, sorted by seats desc
- `nonstop_flights` -- nonstop flights matching the O&D with seats > 0
- `has_nonstop` -- at least one nonstop has seats
- `nonstop_seats` -- best nonstop seat count
- `display_code` -- compact display (e.g. "D9 (3 ns)", "D9* (2 conn)", "D0", "D?", "D!")
- `best_alternate` -- best nearby date (highest seats, closest offset)

### SegmentVerification

Verification result for one itinerary segment.

| Field | Type | Description |
|-------|------|-------------|
| `index` | `int` | Segment index |
| `segment_type` | `str` | "FLOWN", "SURFACE", "TRANSIT" |
| `origin` / `destination` | `str` (3 chars) | Airport pair |
| `carrier` | `Optional[str]` | Carrier |
| `flight_number` | `Optional[str]` | Flight number |
| `target_date` | `Optional[date]` | Date to check |
| `dclass` | `Optional[DClassResult]` | Availability result |
| `married_segment_note` | `Optional[str]` | Married segment warning |

### VerifyResult

Complete D-class verification for one itinerary.

| Field | Type | Description |
|-------|------|-------------|
| `option_id` | `int` | Itinerary option number |
| `segments` | `list[SegmentVerification]` | Per-segment results |

Computed properties:
- `flown_segments` -- segments with type "FLOWN"
- `confirmed` -- count with nonstop D-class available
- `confirmed_any` -- count with any D-class (including connections)
- `total_flown` -- count of flown segments
- `percentage` -- confirmed / total_flown * 100
- `fully_bookable` -- True if all flown segments have nonstop D-class
- `connection_only_segments` -- segments available only via connections

---

## 7. YAML Data Files (rtw/data/)

### carriers.yaml

Carrier reference data for all oneworld members (15 eligible + 3 ineligible).

**Structure** (keyed by 2-letter IATA code):

```yaml
AA:
  name: American Airlines
  alliance: oneworld
  eligible: true
  ntp_method: revenue         # or "distance" or null
  yq_tier: low                # very_low | low | medium | high | very_high
  yq_estimate_per_segment: 50 # USD
  rtw_booking_class: H        # H for AA, D for all others
  codeshare_parent: null       # Only JQ has QF here
  notes: "..."
```

**Eligible carriers (15):** AA, BA, CX, FJ, QR, RJ, JL, IB, AY, QF, MH, AS, AT, UL, WY

**Ineligible (3):** S7 (sanctioned), JQ (codeshare only, must be QF-marketed), LA (left oneworld)

**Key special case:** AA uses booking class H (not D) for oneworld Explorer business class.

### fares.yaml

Base fares by origin city and ticket type.

**Structure:**

```yaml
origins:
  CAI:                    # Origin airport code
    name: Cairo
    currency: EGP         # Local filing currency
    notes: "..."
    fares:
      AONE3: 5600         # TicketType -> USD amount
      AONE4: 6400
      DONE3: 3500
      DONE4: 4000
      ...
```

**8 origin cities:** CAI, OSL, JNB, NRT, CMB, LHR, JFK, SYD

**12 ticket types per origin:** AONE3-6, DONE3-6, LONE3-6

Cheapest origin is CAI (EGP devaluation advantage). Most expensive is JFK.

### continents.yaml

Airport-to-continent classification rules.

**Three sections:**

1. **overrides** -- Airport-level overrides for edge cases (45 airports). Examples:
   - `CAI: EU_ME` (Egypt is Middle East, not Africa)
   - `GUM: Asia` (Guam is Asia despite being US territory)
   - `HNL: N_America` (Hawaii is North America)
   - All Australian/NZ airports explicitly mapped to SWP

2. **countries** -- Country-to-continent mapping using ISO 2-letter codes. Six continent groups matching the `Continent` enum. Notable: "NO" (Norway) must be quoted in YAML to avoid boolean parsing.

3. **segment_limits** -- Per-continent segment limits:
   - N_America: 6
   - All others: 4

4. **tariff_conferences** -- TC1/TC2/TC3 to continent group mapping (mirrors `CONTINENT_TO_TC` in Python).

### surcharges.yaml

Carrier-imposed surcharge (YQ/YR) reference data.

**Three sections:**

1. **carrier_yq** -- Per-carrier USD per segment estimate. Range: JL $12 (lowest) to QF $334 (highest).

2. **plating_comparison** -- Total YQ impact for a typical 16-segment DONE4, by plating carrier. QR cheapest ($800), BA most expensive ($2500).

3. **special_rules** -- Notable exceptions: AA domestic zero YQ, surface sectors zero YQ, QR non-linear pricing, UK departure tax.

### ntp_rates.yaml

BA New Tier Points earning rates.

**Two sections:**

1. **revenue_based.carriers** -- List of carriers using revenue method: BA, AA, IB

2. **distance_based** -- Per-carrier NTP percentage by booking class. Example:
   - QR/JL/AY: D class = 50% (most generous)
   - CX/QF/MH/AS/AT/UL/FJ/RJ: D class = 25%
   - WY: D class = 12.5% (lowest in alliance for business)
   - All carriers have full class-by-class breakdowns

3. **ba_bonus** -- BA-marketed flight bonus NTP (permanent from Nov 2025). Club World (long-haul business) = 400 NTP per segment.

### hubs.yaml

Hub connection table for route generation.

**Six inter-TC connection tables:** TC1_to_TC2, TC2_to_TC3, TC3_to_TC1, TC2_to_TC1, TC1_to_TC3, TC3_to_TC2. Each entry:

```yaml
- from_hub: JFK
  to_hub: LHR
  carrier: AA
  priority: 1    # 1=best, 3=worst
```

**Intra-continent section:** lists carriers and hubs per continent for within-continent routing.

### same_cities.yaml

Same-city airport groups. Transfers between airports in the same group are NOT counted as surface sectors per Rule 3015.

**14 city groups:** TYO (NRT/HND), LON (LHR/LGW/STN/LCY/LTN), NYC (JFK/LGA/EWR), PAR (CDG/ORY), SEL (ICN/GMP), WAS (IAD/DCA/BWI), and others.

### through_flights.yaml

Known oneworld through-flights with intermediate stops. Critical for continent counting under Rule 3015 S16.

**Two sections:**

1. **cross_continent** -- Through-flights where the via stop adds a different continent. Key examples:
   - QF1/QF2: SYD-LHR via SIN (adds Asia)
   - BA15/BA16: LHR-SYD via SIN (adds Asia)
   - QR920/QR921: DOH-ADL via SIN (adds Asia)

2. **same_continent_via** -- Through-flights where the via stop is same continent (no impact). e.g. QF5/QF6: SYD-FCO via PER (PER is SWP same as SYD).

### templates/ directory

YAML itinerary templates:
- `done4-eastbound.yaml` -- Sample 4-continent business class eastbound itinerary
- `done5-eastbound.yaml` -- Sample 5-continent variant

### Other data files

- **fares.db** -- SQLite database of fare data (built from spreadsheet)
- **rtw_fares_all.xlsx** -- Source spreadsheet for fare data
- **knowledge.db** -- SQLite knowledge base (FlyerTalk research, booking intelligence)
- **kb_schema.sql** -- Schema for knowledge.db (articles, sections, findings, questions, tags, sources, cross-references, FTS5 indexes)

---

## 8. Airport Resolution System

### airports.py -- Shared Airport Database

The `airportsdata` library is loaded exactly once at import time via `rtw/airports.py`:

```python
airports_db: dict = airportsdata.load("IATA")
```

This is a fail-fast import: if `airportsdata` is not installed, the process exits with code 2 immediately. All modules that need airport data import `airports_db` from this single source.

The database is a dict keyed by 3-letter IATA code, with values containing: `name`, `city`, `country` (ISO 2-letter), `lat`, `lon`, and other fields.

### continents.py -- Airport-to-Continent Classification

Resolution order for `get_continent(airport_code)`:

1. **Explicit overrides** -- Check `continents.yaml` overrides dict (45 airports with non-obvious assignments)
2. **Country lookup** -- Get ISO country code from `airportsdata`, then map country to continent via `continents.yaml` countries dict
3. **None** -- Return None if airport is unknown

Additional functions:
- `get_tariff_conference(continent)` -- Uses `CONTINENT_TO_TC` from models.py
- `get_segment_limit(continent)` -- From continents.yaml segment_limits (N_America=6, others=4)
- `get_same_city_group(airport_code)` -- From same_cities.yaml
- `are_same_city(airport1, airport2)` -- Checks if both airports are in the same city group
- `get_country(airport_code)` -- ISO country code from airportsdata
- `get_country_name(country_code)` -- Full English name from internal dict (62 countries)
- `check_open_jaw_permitted(origin, dest)` -- Rule 3015 S18 open-jaw validation

### Open-Jaw Rules (in continents.py)

Returns `OpenJawResult(permitted: bool, reason: str)`. Permitted when:
1. Same country
2. Bilateral pair: US<->CA, HK<->CN, MY<->SG, MV<->LK/IN
3. Both in Middle East (14 countries)
4. Both in Africa (25 countries)

---

## 9. Carrier Booking Class Resolution (rtw/carriers.py)

`get_booking_class(carrier, cabin)` resolves the correct booking class:

| Cabin | Rule |
|-------|------|
| Business | Check `carriers.yaml` `rtw_booking_class` for the carrier. Default D. AA returns H. |
| Economy | Always L |
| First | Always A |
| Surface (carrier=None) | Default D |

The carriers.yaml data is loaded once at module import time. The function always returns a concrete single-letter string.

---

## 10. Distance Calculation System (rtw/distance.py)

### DistanceCalculator

Uses the `haversine` library for great-circle distance. Single method:

```python
def miles(self, origin: str, dest: str) -> float
```

Resolution:
1. Uppercase both airport codes
2. If origin == dest, return 0.0
3. Look up both airports in `airports_db` (from `rtw/airports.py`)
4. If either unknown, return 0.0
5. Extract `(lat, lon)` from each airport record
6. Compute haversine distance in miles

The calculator is used by:
- **NTP estimator** -- distance * NTP rate percentage for distance-based carriers
- **Value analyzer** -- segment distance for value-per-mile calculations
- **Search scorer** -- route quality assessment

---

## 11. Model Interconnections

### Data Flow Diagram

```
YAML itinerary file
        |
        v
    Itinerary (Pydantic)
    +-- Ticket (type, cabin, origin, plating_carrier)
    +-- [Segment] (from, to, carrier, type, via)
        |
        +----> Validator --> ValidationReport --> [RuleResult]
        |       uses: continents.py, airports.py, carriers.yaml, same_cities.yaml
        |
        +----> CostEstimator --> CostEstimate
        |       uses: fares.yaml (base fares), surcharges.yaml (YQ),
        |             carriers.yaml (per-segment YQ)
        |
        +----> NTP Estimator --> [NTPEstimate]
        |       uses: ntp_rates.yaml, distance.py, carriers.yaml
        |
        +----> Value Analyzer --> [SegmentValue]
        |       uses: distance.py, scraped prices
        |
        +----> Booking Generator --> phone script + GDS commands
        |       uses: carriers.py (booking class resolution)
        |
        +----> Verify Orchestrator --> VerifyResult --> [SegmentVerification]
                uses: ExpertFlyer scraper, carriers.py, through_flights.yaml
```

### Search Pipeline Flow

```
SearchQuery
    |
    v
Route Generator (uses hubs.yaml, continents.py)
    |
    v
[CandidateItinerary] (each wraps an Itinerary + RouteSegments)
    |
    v
Scorer (availability, quality, cost)
    |
    v
[ScoredCandidate] (with FareComparison)
    |
    v
SearchResult (ranked options)
```

### Key Foreign Key Relationships

- `Itinerary.ticket.type` determines which row in `fares.yaml` to look up
- `Itinerary.ticket.origin` determines which origin column in `fares.yaml`
- `Segment.carrier` keys into `carriers.yaml` for YQ, NTP method, booking class
- `Segment.from_airport` / `to_airport` key into `airportsdata` for coordinates and country
- Country codes key into `continents.yaml` countries dict for continent assignment
- Continent enum values key into `CONTINENT_TO_TC` for tariff conference
- `Segment.via` references intermediate airports in through-flights, mapped via `through_flights.yaml`
