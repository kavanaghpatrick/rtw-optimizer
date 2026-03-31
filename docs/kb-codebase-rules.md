# Rules Engine Architecture

Complete reference for the RTW Optimizer's IATA Rule 3015 validation engine.

## 1. Rule Registry (base.py)

The rule engine uses a **decorator-based global registry** pattern.

### Protocol

Every rule class must satisfy the `Rule` protocol defined in `rtw/rules/base.py`:

```python
class Rule(Protocol):
    rule_id: str        # Machine-readable identifier (e.g. "segment_count")
    rule_name: str      # Human-readable name (e.g. "Segment Count")
    rule_reference: str # Source reference (e.g. "Rule 3015 SS4")

    def check(self, itinerary: Itinerary, context: ValidationContext) -> list[RuleResult]: ...
```

### Registration

Rules register themselves via the `@register_rule` class decorator:

```python
_RULE_REGISTRY: list[type] = []

def register_rule(cls: type) -> type:
    _RULE_REGISTRY.append(cls)
    return cls
```

The registry is a **module-level list**. Decorated classes are appended at import time. There is no priority ordering, dependency resolution, or deduplication -- rules execute in the order their modules are imported.

### Discovery

The `Validator.__init__()` method triggers registration by importing all rule modules explicitly:

```python
def _discover_rules(self) -> None:
    import rtw.rules.segments        # 3 rules
    import rtw.rules.direction       # 3 rules
    import rtw.rules.stopovers       # 4 rules
    import rtw.rules.surface         # 3 rules
    import rtw.rules.geography       # 4 rules
    import rtw.rules.carriers        # 3 rules
    import rtw.rules.validity        # 6 rules
    import rtw.rules.hemisphere      # 2 rules
    import rtw.rules.intercontinental # 1 rule
    import rtw.rules.country         # 2 rules
    import rtw.rules.married         # 1 rule
```

Import order determines execution order.

---

## 2. ValidationContext

`ValidationContext` is a dataclass built by `build_context(itinerary)` before any rules run. It pre-computes expensive lookups so individual rules don't repeat the same work.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `segment_continents` | `list[Optional[Continent]]` | Destination continent for each segment |
| `segment_tcs` | `list[Optional[TariffConference]]` | TC zone for each segment destination |
| `origin_continent` | `Optional[Continent]` | Continent of the ticket origin airport |
| `origin_tc` | `Optional[TariffConference]` | TC zone of the ticket origin |
| `continents_visited` | `list[Continent]` | Ordered unique list of all continents visited (including implicit and via) |
| `segments_per_continent` | `dict[Continent, int]` | Count of **intra-continental** segments per continent |
| `stopovers_per_continent` | `dict[Continent, int]` | Stopover count per continent (by destination) |
| `same_city_pairs` | `list[tuple[int, int]]` | Consecutive segment pairs where arrival/departure are same-city different codes (e.g. NRT/HND) |
| `tc_sequence` | `list[TariffConference]` | Ordered list of TC zone transitions (cross-TC only) |
| `is_intercontinental` | `list[bool]` | Per-segment flag: `from_continent != to_continent` |
| `intercontinental_arrivals` | `dict[Continent, int]` | Count of intercontinental arrivals per destination continent |
| `intercontinental_departures` | `dict[Continent, int]` | Count of intercontinental departures per origin continent |
| `implicit_continents` | `list[Continent]` | Continents visited implicitly (e.g. Asia for EU_ME<->SWP direct flights) |
| `implicit_continent_segments` | `dict[Continent, list[int]]` | Which segments triggered implicit continent detection |
| `via_continents` | `list[Continent]` | Continents visited via through-flight technical stops |
| `via_continent_segments` | `dict[Continent, list[tuple[int, str]]]` | Which segments/airports triggered via-continent detection |

### Build Process

`build_context()` processes all segments in a single pass:

1. **Resolve origin** -- look up continent and TC for `ticket.origin`
2. **Per-segment loop** -- for each segment:
   - Determine `from_continent` and `to_continent`
   - Classify intercontinental vs. intra-continental
   - For intra-continental: increment `segments_per_continent`
   - For intercontinental: increment `intercontinental_arrivals` and `intercontinental_departures`
   - Count stopovers per continent (always by destination)
   - Track unique continent visits
   - Track TC transitions (cross-TC only, for direction detection)
3. **Same-city detection** -- find consecutive segment pairs where arrival != departure but airports are in the same city group
4. **Via-continent detection** (`_detect_via_continents`) -- through-flight intermediate stops count their continent as visited for pricing but do NOT add to per-continent segment limits
5. **Implicit continent detection** (`_detect_implicit_continents`) -- direct EU_ME<->SWP flights imply travelling via Asia per Rule 3015 SS16

### Key Design Decision: Segment Counting Split

Segments are split into two buckets:
- **Intra-continental** (from_continent == to_continent) -- counted in `segments_per_continent`, validated by `PerContinentLimitRule`
- **Intercontinental** (from_continent != to_continent) -- counted in `intercontinental_arrivals`/`departures`, validated by `IntercontinentalLimitRule`

This prevents a segment like LHR->JFK from consuming both a Europe slot and a North America slot.

---

## 3. Rule Execution

### Flow

```
Validator.validate(itinerary)
  |
  +-- build_context(itinerary)           # Pre-compute shared context
  |
  +-- for rule_cls in get_registered_rules():
  |     rule = rule_cls()                # Fresh instance per rule
  |     results = rule.check(itinerary, context)
  |     all_results.extend(results)      # Accumulate all results
  |
  +-- return ValidationReport(itinerary, all_results)
```

### Execution Properties

- **No short-circuit**: All rules run regardless of earlier failures. Every rule's results are accumulated.
- **No ordering dependency**: Rules receive the same immutable `context` and `itinerary`. No rule modifies shared state.
- **Error isolation**: If a rule raises an exception, it is caught and converted to a failed `RuleResult` with the error message. Other rules still execute.
- **Multiple results per rule**: A single rule can return multiple `RuleResult` objects (e.g. one per continent, one per violation found).

### RuleResult Model

```python
class RuleResult(BaseModel):
    rule_id: str                    # Links to rule class
    rule_name: str                  # Human-readable
    rule_reference: str = ""        # "Rule 3015 SS4" etc.
    passed: bool                    # True = OK, False = fail
    severity: Severity = VIOLATION  # VIOLATION | WARNING | INFO
    message: str                    # Explanation
    fix_suggestion: str = ""        # How to fix
    segments_involved: list[int] = []  # 0-based segment indices
```

### ValidationReport

```python
class ValidationReport(BaseModel):
    itinerary: Itinerary
    results: list[RuleResult]

    @property
    def passed(self) -> bool:
        # Only VIOLATION-severity failures cause overall failure
        return all(r.passed for r in self.results if r.severity == Severity.VIOLATION)
```

A report passes if no results with `severity=VIOLATION` have `passed=False`. Warnings and info messages do not affect overall pass/fail.

### Severity Levels

| Level | Meaning | Affects `report.passed`? |
|-------|---------|--------------------------|
| `VIOLATION` | Rule broken, ticket invalid | Yes |
| `WARNING` | Ambiguous or risky, may need desk confirmation | No |
| `INFO` | Informational note | No |

---

## 4. Complete Rule Reference

### Module: segments.py (Rule 3015 SS4)

#### SegmentCountRule
- **rule_id**: `segment_count`
- **Reference**: Rule 3015 SS4
- **Checks**: Total segment count (including surface sectors) is 3-16
- **Pass**: 3 <= total segments <= 16
- **Fail (VIOLATION)**: `< 3` segments or `> 16` segments

#### PerContinentLimitRule
- **rule_id**: `per_continent_limit`
- **Reference**: Rule 3015 SS4
- **Checks**: Intra-continental segment count per continent does not exceed limit (4 for most continents, 6 for North America)
- **Pass**: Each continent's intra-continental count <= its limit
- **Fail (VIOLATION)**: Any continent exceeds its limit
- **Note**: Only intra-continental segments (from_continent == to_continent) count here. Intercontinental segments are handled by `IntercontinentalLimitRule`.

#### SegmentConnectivityRule
- **rule_id**: `segment_connectivity`
- **Reference**: Rule 3015 SS4
- **Checks**: Consecutive segments form a connected chain (arrival airport of seg N == departure airport of seg N+1, allowing same-city groups)
- **Pass**: All segments connected, or gap followed by a surface sector
- **Fail (WARNING)**: Gap found between consecutive non-surface segments

### Module: direction.py (Rule 3015 SS5)

#### DirectionOfTravelRule
- **rule_id**: `direction_of_travel`
- **Reference**: Rule 3015 SS5
- **Checks**: TC transitions follow a consistent circular direction (eastbound or westbound) with no reversals
- **Pass**: All TC transitions follow the same direction (eastbound: TC index +1 mod 3; westbound: TC index +2 mod 3)
- **Fail (VIOLATION)**: Direction reversal detected in TC transition sequence
- **Note**: Direction is determined from the first two distinct TCs in the sequence. Consecutive same-TC segments are collapsed.

#### OceanCrossingRule
- **rule_id**: `ocean_crossings`
- **Reference**: Rule 3015 SS5
- **Checks**: Exactly one Pacific (TC3<->TC1) and exactly one Atlantic (TC1<->TC2) ocean crossing, both on flown (non-surface) segments
- **Pass**: Exactly 1 Pacific crossing AND exactly 1 Atlantic crossing
- **Fail (VIOLATION)**: 0 or >1 Pacific crossings; 0 or >1 Atlantic crossings (separate results for each ocean)

#### CityPairDirectionRule
- **rule_id**: `city_pair_direction`
- **Reference**: Rule 3015 SS8
- **Checks**: No city-pair in the same direction is flown more than once (uses same-city group resolution, e.g. NRT/HND are the same city)
- **Pass**: All directional city-pairs are unique
- **Fail (VIOLATION)**: Duplicate city-pair detected (reports which segments)

### Module: stopovers.py (Rule 3015 SS6)

#### MinimumStopoverRule
- **rule_id**: `minimum_stopovers`
- **Reference**: Rule 3015 SS6
- **Checks**: At least 2 segments are marked as stopovers
- **Pass**: >= 2 stopovers
- **Fail (VIOLATION)**: < 2 stopovers

#### OriginContinentStopoverRule
- **rule_id**: `origin_continent_stopovers`
- **Reference**: Rule 3015 SS6
- **Checks**: Maximum 2 stopovers in the continent of origin
- **Pass**: <= 2 stopovers in origin continent
- **Fail (WARNING)**: > 2 stopovers (warning because return-leg counting is ambiguous -- advises checking with AA RTW desk)

#### OriginCountryStopoverPerDirectionRule
- **rule_id**: `origin_country_stopover_direction`
- **Reference**: Rule 3015 SS6
- **Checks**: Maximum 1 stopover per direction (outbound/return) in the country of origin. Outbound = initial chain while in origin country; return = final chain arriving back.
- **Pass**: <= 1 stopover outbound AND <= 1 stopover return
- **Fail (VIOLATION)**: > 1 stopover in either direction

#### SameCityVisitLimitRule
- **rule_id**: `same_city_visit_limit`
- **Reference**: Rule 3015 SS6
- **Checks**: Same city (by same-city group) visited at most 4 times (5 in North America). Counts arrivals per city.
- **Pass**: All cities within their visit limit
- **Fail (VIOLATION)**: Any city exceeds its limit

### Module: surface.py (Rule 3015 SS7)

#### FirstSegmentNotSurfaceRule
- **rule_id**: `first_segment_not_surface`
- **Reference**: Rule 3015 SS7
- **Checks**: First segment is a flown segment, not a surface sector
- **Pass**: First segment is flown
- **Fail (VIOLATION)**: First segment is surface

#### SameCityResolutionRule
- **rule_id**: `same_city_resolution`
- **Reference**: Rule 3015 SS7
- **Checks**: Identifies same-city airport pairs in consecutive segments (e.g. arriving NRT, departing HND). These are NOT surface sectors.
- **Pass**: Always passes. Emits INFO messages identifying detected same-city pairs.
- **Severity**: INFO only

#### TransoceanicSurfaceRule
- **rule_id**: `transoceanic_surface`
- **Reference**: Rule 3015 SS7
- **Checks**: Surface sectors cannot cross oceans (TC1<->TC2 or TC1<->TC3). TC2<->TC3 surface is allowed. SWP-origin gets a 1-sector exemption.
- **Pass**: No transoceanic surface sectors; or SWP-origin with exactly 1
- **Fail (VIOLATION)**: Any transoceanic surface for non-SWP origin; or >1 for SWP origin

### Module: geography.py (Rule 3015 SS9-10)

#### HawaiiAlaskaRule
- **rule_id**: `hawaii_alaska`
- **Reference**: Rule 3015 SS5, SS10
- **Checks**: (1) No backtracking to Hawaii after leaving. (2) Alaska: max 1 flight to and max 1 flight from.
- **Pass**: No Hawaii backtrack AND Alaska within limits
- **Fail (VIOLATION)**: Hawaii backtrack detected; or >1 flights to/from Alaska

#### TranscontinentalUSRule
- **rule_id**: `transcontinental_us`
- **Reference**: Rule 3015 SS10
- **Checks**: Maximum 1 nonstop transcontinental flight within the US (east coast <-> west coast, defined by specific airport sets per Rule 3015 SS4(k))
- **Pass**: <= 1 transcontinental US flight
- **Fail (VIOLATION)**: > 1 transcontinental US flights

#### TranscontinentalAURule
- **rule_id**: `transcontinental_au`
- **Reference**: Rule 3015 SS9
- **Checks**: Maximum 1 transcontinental flight within Australia per pair group (east coast<->Perth, east coast<->Darwin, east coast<->Broome/Karratha). Has exemptions for Perth-origin with JNB connection and NZ-origin with JNB connection.
- **Pass**: <= 1 per pair group, or exempt
- **Fail (VIOLATION)**: >= 2 in any pair group (without exemption)

#### ImplicitAsiaRule
- **rule_id**: `implicit_asia`
- **Reference**: Rule 3015 SS16
- **Checks**: Detects EU_ME<->SWP direct flights that implicitly count Asia as visited. Informational only.
- **Pass**: Always passes. Emits INFO when implicit Asia visit detected.
- **Severity**: INFO only

### Module: carriers.py (Rule 3015 SS15, SS19)

#### QRNotFirstRule
- **rule_id**: `qr_not_first`
- **Reference**: oneworld booking tool
- **Checks**: Qatar Airways (QR) is not the first carrier in the itinerary. The online booking tool cannot issue tickets starting with QR.
- **Pass**: First flown segment is not QR
- **Fail (WARNING)**: First flown segment is QR (bookable by phone via AA RTW desk)

#### EligibleCarrierRule
- **rule_id**: `eligible_carriers`
- **Reference**: Rule 3015 SS15
- **Checks**: All carriers are eligible oneworld members. Recognizes codeshare parents (e.g. JQ -> QF).
- **Pass**: All carriers eligible (codeshares noted as INFO)
- **Fail (VIOLATION)**: Non-oneworld carrier found

#### QFJQCodeshareRule
- **rule_id**: `qf_jq_codeshare`
- **Reference**: Rule 3015 SS15
- **Checks**: When JQ (Jetstar) segments are present, certain plating carriers (AS, IB) cannot issue the ticket.
- **Pass**: No JQ segments, or plating carrier is compatible
- **Fail (WARNING)**: JQ segments with incompatible plating carrier

### Module: validity.py (Rule 3015 SS7, SS12, SS16, SS18)

#### ReturnToOriginRule
- **rule_id**: `return_to_origin`
- **Reference**: Rule 3015 SS18
- **Checks**: Last segment destination matches ticket origin (same-city group). If not, checks if it qualifies as a permitted open jaw.
- **Pass**: Returns to origin city, or permitted open jaw
- **Fail (VIOLATION)**: Does not return and open jaw not permitted

#### OpenJawPairsRule
- **rule_id**: `open_jaw_pairs`
- **Reference**: Rule 3015 SS18
- **Checks**: If the itinerary is an open jaw (does not return to origin), verifies the open-jaw pair is permitted: same country, US<->CA, HK<->CN, MY<->SG, MV<->LK/IN, within Middle East, within Africa.
- **Pass**: Returns to origin (not an open jaw), or open jaw pair is permitted
- **Fail (VIOLATION)**: Open jaw pair not in permitted list

#### ContinentCountRule
- **rule_id**: `continent_count`
- **Reference**: Rule 3015 SS16
- **Checks**: Number of continents visited (including implicit and via-stop continents) matches ticket type (e.g. DONE4 expects 4 continents)
- **Pass**: Actual continent count == ticket's expected continent count
- **Fail (WARNING)**: Mismatch (suggests adjusting ticket type or routing)

#### TicketValidityRule
- **rule_id**: `ticket_validity`
- **Reference**: Rule 3015 SS12
- **Checks**: Trip duration is 10-365 days (based on first and last segment dates)
- **Pass**: 10 <= days <= 365
- **Fail (VIOLATION)**: < 10 days or > 365 days

#### OriginMatchesFirstSegmentRule
- **rule_id**: `origin_matches_first_segment`
- **Reference**: Rule 3015 SS7
- **Checks**: Ticket origin field matches the departure airport of the first segment (same-city group)
- **Pass**: Origin matches first departure
- **Fail (WARNING)**: Mismatch (origin-based rules may produce incorrect results)

#### DateSequenceRule
- **rule_id**: `date_sequence`
- **Reference**: Rule 3015 SS4
- **Checks**: All dated segments are in chronological order
- **Pass**: Dates strictly non-decreasing
- **Fail (VIOLATION)**: Any segment date precedes a previous segment's date

### Module: hemisphere.py (Rule 3015 SS11)

#### HemisphereRevisitRule
- **rule_id**: `hemisphere_revisit`
- **Reference**: Rule 3015 SS11
- **Checks**: Northern hemisphere continents (Asia, EU/ME, N_America) may be visited at most 2 times. Southern hemisphere continents (Africa, SWP, S_America) may be visited at most 1 time. The origin continent gets +1 allowance if it appears at the end of the transition sequence (return leg).
- **Pass**: All continents within their hemisphere visit limits
- **Fail (VIOLATION)**: Any continent exceeds its limit
- **Note**: Tracks an Asia SWP-Europe bridge exception -- two Asia visits are flagged with an informational note when the itinerary also includes SWP and EU_ME.

#### EuMeAfricaZoneRule
- **rule_id**: `eu_me_africa_zone`
- **Reference**: Rule 3015 SS11
- **Checks**: If ALL intercontinental flights touching Africa go to/from EU_ME, then South Africa (ZA) and Mauritius (MU) cannot be included.
- **Pass**: Rule does not apply (Africa has non-EU/ME intercontinental connection), or no ZA/MU airports present
- **Fail (VIOLATION)**: Both Africa IC flights are EU_ME-only AND itinerary includes ZA or MU airports

### Module: intercontinental.py (Rule 3015 SS4(e))

#### IntercontinentalLimitRule
- **rule_id**: `intercontinental_limit`
- **Reference**: Rule 3015 SS4(e)
- **Checks**: Max 1 intercontinental arrival and 1 intercontinental departure per continent, with exceptions:
  - **North America**: always 2
  - **Asia**: always 2 (updated April 2025 -- unconditional)
  - **EU/ME**: 2 when itinerary includes Africa
- **Pass**: Each continent within its limit for both arrivals and departures
- **Fail (VIOLATION)**: Arrivals or departures exceed limit for any continent

### Module: country.py (Rule 3015 SS4(f), SS6)

#### OriginCountryIntlLimitRule
- **rule_id**: `origin_country_intl_limit`
- **Reference**: Rule 3015 SS4(f)
- **Checks**: International departures and arrivals from the origin country. Departures limited to 1 (US gets 2 if one is transit). Arrivals limited to 1. Also: max 4 international transfers from any single country. US<->CA movements are NOT international.
- **Pass**: Departures, arrivals, and per-country transfers all within limits
- **Fail (VIOLATION)**: Any limit exceeded

#### OriginCountryReturnRule
- **rule_id**: `origin_country_return`
- **Reference**: Rule 3015 SS6
- **Checks**: No mid-journey return to origin country. Initial departure chain and final return chain are exempt. US gets a single-transit exception (1 transit, not stopover, permitted mid-journey).
- **Pass**: No mid-journey returns, or US with exactly 1 transit return
- **Fail (VIOLATION)**: Mid-journey return detected (non-US), or US with stopover/multiple returns

### Module: married.py (Community Knowledge)

#### MarriedSegmentRule
- **rule_id**: `married_segment`
- **Reference**: Community knowledge (FlyerTalk), Qantas AgencyConnect
- **Checks**: Two patterns:
  1. **Hub O&D control**: CX (HKG hub) and QR (DOH hub) use origin-destination revenue management. Segments on these carriers that don't touch their hub may have D-class availability only for connecting itineraries.
  2. **Through-flight split risk**: If a segment has a via stop and that via city also appears as a stopover destination elsewhere, splitting the through-flight into separate segments may require reissue and fees.
- **Pass (INFO)**: No married segment risks detected
- **Fail (INFO)**: Risk patterns detected -- informational only, never blocks validation

---

## 5. Complete Rule Summary Table

| # | rule_id | Module | Reference | Severity | What It Checks |
|---|---------|--------|-----------|----------|----------------|
| 1 | `segment_count` | segments | SS4 | VIOLATION | 3-16 total segments |
| 2 | `per_continent_limit` | segments | SS4 | VIOLATION | Intra-continental segments per continent (4, or 6 for N_America) |
| 3 | `segment_connectivity` | segments | SS4 | WARNING | Consecutive segments form connected chain |
| 4 | `direction_of_travel` | direction | SS5 | VIOLATION | Continuous eastbound or westbound TC progression |
| 5 | `ocean_crossings` | direction | SS5 | VIOLATION | Exactly 1 Pacific + 1 Atlantic crossing, both flown |
| 6 | `city_pair_direction` | direction | SS8 | VIOLATION | No duplicate directional city-pairs |
| 7 | `minimum_stopovers` | stopovers | SS6 | VIOLATION | At least 2 stopovers |
| 8 | `origin_continent_stopovers` | stopovers | SS6 | WARNING | Max 2 stopovers in origin continent |
| 9 | `origin_country_stopover_direction` | stopovers | SS6 | VIOLATION | Max 1 stopover per direction in origin country |
| 10 | `same_city_visit_limit` | stopovers | SS6 | VIOLATION | Max 4 visits per city (5 in N_America) |
| 11 | `first_segment_not_surface` | surface | SS7 | VIOLATION | First segment must be flown |
| 12 | `same_city_resolution` | surface | SS7 | INFO | Identifies same-city airport pairs (informational) |
| 13 | `transoceanic_surface` | surface | SS7 | VIOLATION | No transoceanic surface sectors (SWP gets 1) |
| 14 | `hawaii_alaska` | geography | SS5, SS10 | VIOLATION | No Hawaii backtrack; Alaska max 1 in + 1 out |
| 15 | `transcontinental_us` | geography | SS10 | VIOLATION | Max 1 US transcontinental nonstop |
| 16 | `transcontinental_au` | geography | SS9 | VIOLATION | Max 1 AU transcontinental per pair group |
| 17 | `implicit_asia` | geography | SS16 | INFO | Flags EU_ME<->SWP flights counting Asia (informational) |
| 18 | `qr_not_first` | carriers | booking tool | WARNING | QR not first carrier (booking tool limitation) |
| 19 | `eligible_carriers` | carriers | SS15 | VIOLATION | All carriers oneworld members |
| 20 | `qf_jq_codeshare` | carriers | SS15 | WARNING | JQ plating carrier compatibility |
| 21 | `return_to_origin` | validity | SS18 | VIOLATION | Returns to origin or permitted open jaw |
| 22 | `open_jaw_pairs` | validity | SS18 | VIOLATION | Open jaw pairs in permitted list |
| 23 | `continent_count` | validity | SS16 | WARNING | Continent count matches ticket type |
| 24 | `ticket_validity` | validity | SS12 | VIOLATION | Trip duration 10-365 days |
| 25 | `origin_matches_first_segment` | validity | SS7 | WARNING | Ticket origin matches first segment departure |
| 26 | `date_sequence` | validity | SS4 | VIOLATION | Segment dates in chronological order |
| 27 | `hemisphere_revisit` | hemisphere | SS11 | VIOLATION | Northern continents max 2 visits, southern max 1 |
| 28 | `eu_me_africa_zone` | hemisphere | SS11 | VIOLATION | ZA/MU excluded when both Africa IC flights are EU_ME |
| 29 | `intercontinental_limit` | intercontinental | SS4(e) | VIOLATION | Max 1 IC arrival + 1 departure per continent (with exceptions) |
| 30 | `origin_country_intl_limit` | country | SS4(f) | VIOLATION | Origin country international flight limits |
| 31 | `origin_country_return` | country | SS6 | VIOLATION | No mid-journey return to origin country |
| 32 | `married_segment` | married | FlyerTalk | INFO | Hub O&D control and through-flight split risks |

**Total: 32 rules across 11 modules.**

---

## 6. Key Source Files

| File | Purpose |
|------|---------|
| `rtw/rules/base.py` | Rule protocol, registry, `@register_rule` decorator |
| `rtw/validator.py` | `ValidationContext`, `build_context()`, `Validator` class |
| `rtw/models.py` | `RuleResult`, `Severity`, `ValidationReport`, domain enums |
| `rtw/rules/segments.py` | Segment count, per-continent limit, connectivity |
| `rtw/rules/direction.py` | Direction of travel, ocean crossings, city-pair direction |
| `rtw/rules/stopovers.py` | Minimum stopovers, origin continent/country limits, city visits |
| `rtw/rules/surface.py` | First segment, same-city resolution, transoceanic surface |
| `rtw/rules/geography.py` | Hawaii/Alaska, US/AU transcontinental, implicit Asia |
| `rtw/rules/carriers.py` | QR first carrier, eligible carriers, JQ codeshare |
| `rtw/rules/validity.py` | Return to origin, open jaw, continent count, ticket validity, dates |
| `rtw/rules/hemisphere.py` | Hemisphere revisit limits, EU/ME-Africa zone |
| `rtw/rules/intercontinental.py` | Intercontinental arrival/departure limits |
| `rtw/rules/country.py` | Origin country international limits, mid-journey return ban |
| `rtw/rules/married.py` | Married segment and through-flight split detection |
