---
spec: via-through-flights
phase: research
created: 2026-02-16
---

# Research: via-through-flights

## Executive Summary

Through-flights (single flight numbers with intermediate stops) are well-defined in aviation: they count as ONE segment but trigger continent counting at each stop. Adding a `via` field to the Segment model is technically straightforward (Optional[str | list[str]], backward compatible). Married segment detection is achievable via static pattern rules + ExpertFlyer live checks, though airline-specific married segment logic is not publicly documented in full and will require community knowledge + empirical validation.

## External Research

### Through-Flights: Definition and Rules

A through-flight is "a direct flight between two points with no change in flight number. It may or may not include a stop at an intermediate point" (Qantas AgencyConnect). The FlyerTalk oneworld Explorer User Guide confirms: "a segment is a flight with a single flight number between two cities, whether or not it stops between the origin and destination."

**Critical rule from Rule 3015 SS16**: "A continent is counted even if all you do is change planes there; even if your plane merely lands there." This means through-flight stops at intermediate airports trigger continent counting for pricing.

**Sources**:
| Source | Key Point |
|--------|-----------|
| [Qantas AgencyConnect](https://www.qantas.com/agencyconnect/us/en/policy-and-guidelines/book-and-service/through-flight-information.html) | Through-flight = single flight number, must be booked as one segment |
| [FlyerTalk User Guide](https://www.flyertalk.com/forum/oneworld/2008084-oneworld-explorer-user-guide.html) | Segment = single flight number regardless of stops |
| [FlyerTalk FAQs p174](https://www.flyertalk.com/forum/oneworld/338667-oneworld-explorer-ticket-faqs-174.html) | BA15 LHR-SYD is one segment containing 2 married sectors with SIN stop |
| `01-fare-rules.md` SS16 (project root) | "Even technical plane stops count" for continent counting |

### Known oneworld Through-Flights (Cross-Continent Stops)

Compiled from flight tracking, airline sources, and community data:

| Carrier | Flight | Route | Via Stop | Continents Crossed |
|---------|--------|-------|----------|-------------------|
| QF | QF1/QF2 | SYD-LHR | SIN | SWP -> **Asia** -> EU_ME |
| QF | QF5/QF6 | SYD-ROM | PER | SWP (no cross-continent; PER is SWP) |
| QF | QF3/QF4 | SYD-JFK | AKL | SWP -> SWP -> N_America (AKL is SWP, no extra continent) |
| BA | BA15/BA16 | LHR-SYD | SIN | EU_ME -> **Asia** -> SWP |
| QR | QR920/921 | DOH-ADL | SIN | EU_ME -> **Asia** -> SWP |
| QR | QR908/909 | DOH-MEL | SIN | EU_ME -> **Asia** -> SWP |
| CX | (various) | via HKG | HKG | Always Asia; CX hub is already in Asia |

**Key observations**:
1. SIN is the primary cross-continent via stop (Asia) for EU_ME <-> SWP flights
2. PER and AKL stops are same-continent (SWP), so no extra continent triggered
3. CX flights via HKG don't add extra continents since HKG is already in Asia
4. QR flights DOH->SWP via SIN are the most impactful: they add Asia to continent count

### Married Segments: Patterns and Detection

**Definition**: Airlines link inventory on two or more flight segments so they must be booked/cancelled together. Availability may differ for married vs. individual segments.

**Key patterns identified**:

| Pattern | Carrier | Description | Detection Method |
|---------|---------|-------------|-----------------|
| Hub connection lock | CX | D-class often only available when connecting through HKG (not as standalone segment) | Static: CX segment where from/to != HKG, but itinerary has CX HKG connection |
| Stingy standalone D | QF | D-class rare on long-haul as standalone; more available as married with domestic connection | Static: QF transoceanic segment without QF domestic connection |
| H-class fallback | AA | Uses H class (not D) for OWE business; POS/POO rules affect availability | Static: AA segments (already handled in carriers.yaml) |
| Same-day connection | Any | Transit segments on same day have married segment risk | Static: transit + same date on consecutive segments (already in booking.py) |
| Through-flight split | BA/QF | BA15 LHR-SYD is married at SIN; splitting to stopover in SIN requires reissue ($125) | Static: known through-flight with via stop where user wants stopover |

**Sources**:
| Source | Key Point |
|--------|-----------|
| [One Mile at a Time](https://onemileatatime.com/guides/airline-married-segment/) | Married segments = linked inventory; common on CX, QR, AA, Lufthansa |
| [AwardFares Blog](https://blog.awardfares.com/married-segments/) | Cannot "divorce" segments after booking |
| [ATPA (ANA)](https://atpa.fly-ana.com/ticketing-and-policies/married-segment-control) | Rules and penalties on married segment control |
| [AA SalesLink](https://saleslink.aa.com/en-US/resources/html/ticketing-information.html) | AA shifted to Point of Commencement availability (Aug 2024) |

### ExpertFlyer Capabilities for Married Segment Detection

ExpertFlyer can detect married segment patterns indirectly:
- **Connection search**: Shows availability for connecting itineraries (married inventory)
- **Individual search**: Shows standalone segment availability
- **Comparison**: If connecting shows D9 but individual shows D0, that's a married segment signal
- **Limitation**: Flight Alerts are per-segment only; cannot alert on married availability
- **Limitation**: Cannot directly query "is this a married segment?"

**Source**: [ExpertFlyer User Guide](https://www.expertflyer.com/media/user-guide.pdf)

### Pitfalls to Avoid

1. **Auto-detection temptation**: User explicitly said they do NOT want through-flight auto-detection from route data. Only explicit `via` field triggers continent counting.
2. **Over-counting continents**: A via stop in the same continent as origin/destination should NOT add a new continent (e.g., QF5 via PER — both SWP).
3. **Married segment false positives**: Not all connections are married. Many carriers offer standalone D-class on long-haul.
4. **Stale through-flight data**: Airlines change through-flight routes seasonally. Data should be easy to update.

## Codebase Analysis

### Existing Patterns

**Segment model** (`rtw/models.py:131-163`): Pydantic v2 BaseModel with `model_config = {"populate_by_name": True}`. Uses `Field(alias="from")` for `from_airport`. Adding optional `via` field follows exact same pattern.

**Continent detection** (`rtw/validator.py:141-175`): `_detect_implicit_continents()` already handles EU_ME <-> SWP phantom Asia detection. Via-stop continent counting should supplement (not replace) this, since the implicit rule handles the nonstop EU_ME-SWP case (e.g., QF Perth-London nonstop still counts Asia).

**Booking warnings** (`rtw/booking.py:179-196`): Already has basic married segment detection for same-day transit connections. This is the natural extension point for richer married segment warnings.

**Data pattern** (`rtw/data/`): YAML files for carriers, fares, continents, hubs, same_cities. Through-flight lookup data fits this pattern perfectly as `rtw/data/through_flights.yaml`.

**ExpertFlyer scraper** (`rtw/scraper/expertflyer.py`): Queries by O&D pair + date + carrier. To detect married segments, would need to compare results of `check_availability(A, C)` (direct) vs checking `check_availability(A, B)` + `check_availability(B, C)` (via hub). This is a meaningful extension but doubles query count.

**Verify models** (`rtw/verify/models.py`): `FlightAvailability` already has a `stops` field. Results already distinguish nonstop vs connecting flights. `DClassResult.connection_only_segments` property exists.

### Dependencies

- **Pydantic v2**: Optional field with union type is straightforward: `via: Optional[str | list[str]] = None`
- **YAML parsing**: Existing YAML loader in `rtw/continents.py` can be used as pattern for through-flight data
- **airportsdata**: Already used for continent lookup; via-stop airports would use same `get_continent()` function
- **ExpertFlyer integration**: Already operational; extension needs new query patterns, not new auth/session logic

### Constraints

1. **Backward compatibility**: All existing YAML fixtures (37 files) lack `via` field. Optional field with `None` default ensures zero breakage.
2. **Test count**: 1168+ tests. New features must not break existing tests.
3. **No mocks for API responses**: Tests use real fixtures. Through-flight data should be testable with YAML fixtures.
4. **Rule engine architecture**: Rules are separate files registered via decorator. New married segment rules should follow this pattern.

### Related Specs

| Spec | Relevance | mayNeedUpdate |
|------|-----------|---------------|
| 002-dclass-verify | **High** — ExpertFlyer integration directly relevant; married segment detection extends verify logic | true |
| 004-route-builder | **Medium** — `rtw build` may want to suggest through-flights; `rtw scan-dates` could check married availability | false |
| 001-rtw-optimizer | **Low** — Core validator; this spec extends it but doesn't change fundamentals | false |
| 003-nonstop-preverify | **Low** — Nonstop check; tangential to through-flight/married segment work | false |

## Quality Commands

| Type | Command | Source |
|------|---------|--------|
| Lint | `ruff check rtw/ tests/` | CLAUDE.md |
| Unit Test | `uv run pytest` | pyproject.toml / CLAUDE.md |
| Unit Test (fast) | `uv run pytest -m "not slow and not integration"` | CI config |
| Build | N/A (pure Python, no build step) | - |
| TypeCheck | Not configured | - |

**Local CI**: `ruff check rtw/ tests/ && uv run pytest -m "not slow and not integration"`

## Feasibility Assessment

| Aspect | Assessment | Notes |
|--------|------------|-------|
| Via field on Segment | **High** — trivial Pydantic change | Optional field, fully backward compatible |
| Continent counting from via | **High** — extends existing `_detect_implicit_continents()` | Clear algorithm: resolve via-stop continent, add to visited |
| Through-flight lookup YAML | **High** — follows existing data pattern | YAML file with carrier/flight/via mappings |
| Married segment static rules | **High** — extends existing booking.py warnings | Pattern-based: CX/HKG, QF standalone, same-day transit |
| ExpertFlyer married segment detection | **Medium** — requires paired queries | Doubles query count; rate limiting concern; empirical validation needed |
| Booking script enhancements | **High** — natural extension of existing warning system | Add through-flight notes and married segment warnings to phone script |

| Aspect | Assessment | Notes |
|--------|------------|-------|
| Technical Viability | **High** | All components extend existing architecture cleanly |
| Effort Estimate | **M** | ~20-30 tasks across model, validator, data, booking, tests |
| Risk Level | **Low-Medium** | Main risk: married segment patterns are empirical, not documented by airlines |

## Recommendations for Requirements

1. **Via field type**: Use `Optional[str | list[str]] = None`. Single string for common case (one via stop), list for rare multi-stop (QF1 SYD-SIN-LHR has one via, but future routes could have two). Validator normalizes to list internally.

2. **Supplement, don't replace implicit detection**: The existing EU_ME <-> SWP implicit Asia rule handles nonstop flights (e.g., QF PER-LHR). Via-stop counting handles through-flights. Both are needed — they cover different cases.

3. **YAML data file for through-flights**: Create `rtw/data/through_flights.yaml` with structure:
   ```yaml
   QF1:
     carrier: QF
     from: SYD
     via: [SIN]
     to: LHR
     continents_added: [Asia]
   ```
   This is reference data only — validator uses explicit `via` field on segments, not auto-lookup.

4. **Married segment rules as a new rule file**: Create `rtw/rules/married.py` with `MarriedSegmentRule` registered in the rule engine. This keeps it alongside other rules and follows the existing pattern.

5. **ExpertFlyer married detection as opt-in**: When ExpertFlyer credentials are configured and `--check-married` flag is passed to `rtw verify`, run paired queries (direct vs. connecting) to detect married segment availability differences. Do NOT make this the default due to doubled query count.

6. **Booking script warnings**: Add three new warning types:
   - "Through-flight: {route} via {stop} — one segment, counts {continent} for pricing"
   - "Married segment risk: {carrier} D-class may require connection through {hub}"
   - "Through-flight split: Stopping over at {via} converts one segment to two + $125 reissue fee"

## Open Questions

1. **Via field in YAML — should it also accept airport names?** Currently the model uses 3-letter IATA codes. Should `via: Singapore` be accepted or only `via: SIN`?

2. **Multiple through-flight stops**: QF5 SYD-PER-ROM has one via stop. Are there any oneworld through-flights with 2+ intermediate stops? Research found none currently, but the data model should support it.

3. **Through-flight data maintenance**: Should the YAML lookup be versioned by date range (seasonal routes like QF5/6 only operate May-Sep)? Or is a simple static list sufficient?

4. **Married segment severity**: Should married segment warnings be `WARNING` or `INFO`? They don't make the ticket invalid, but they affect bookability.

5. **Connection time threshold**: The existing same-day transit check in `booking.py` uses `seg.date == nxt.date`. Should this be refined to use actual time analysis (e.g., <4 hours = likely married)?

## Sources

- [Qantas AgencyConnect: Through Flight Information](https://www.qantas.com/agencyconnect/us/en/policy-and-guidelines/book-and-service/through-flight-information.html)
- [FlyerTalk: oneworld Explorer User Guide](https://www.flyertalk.com/forum/oneworld/2008084-oneworld-explorer-user-guide.html)
- [FlyerTalk: oneworld Explorer FAQs p174](https://www.flyertalk.com/forum/oneworld/338667-oneworld-explorer-ticket-faqs-174.html)
- [One Mile at a Time: Married Segments Guide](https://onemileatatime.com/guides/airline-married-segment/)
- [AwardFares: Married Segments Guide](https://blog.awardfares.com/married-segments/)
- [AA SalesLink: Ticketing Information](https://saleslink.aa.com/en-US/resources/html/ticketing-information.html)
- [Australian Frequent Flyer: oneworld Explorer Guide](https://www.australianfrequentflyer.com.au/oneworld-explorer-rtw-guide/)
- [Point Hacks: QF1 Guide](https://www.pointhacks.com.au/guides/flights/qantas-qf1/)
- [Point Hacks: QF3 Guide](https://www.pointhacks.com.au/guides/flights/qantas-qf3/)
- [Australian Frequent Flyer: QF5 Guide](https://www.australianfrequentflyer.com.au/qf5/)
- [ExpertFlyer User Guide](https://www.expertflyer.com/media/user-guide.pdf)
- [Pydantic v2 Fields Documentation](https://docs.pydantic.dev/latest/concepts/fields/)
- Codebase: `rtw/models.py`, `rtw/validator.py`, `rtw/rules/geography.py`, `rtw/booking.py`, `rtw/continents.py`, `rtw/scraper/expertflyer.py`, `rtw/verify/models.py`

---QUESTIONS FOR USER---

1. **Should the through-flight YAML include seasonal date ranges?**
   - Why: QF5/6 SYD-PER-ROM only operates May-September. Static data without dates could show stale routes.
   - Options: A) Simple static list (carrier/flight/via/route) B) Add `season: [May, Jun, Jul, Aug, Sep]` field C) Add `active_from/active_to` date fields
   - Recommend: A — simpler, and the data is reference-only (user puts `via` on their actual segments). Seasonal awareness is a separate concern for route search.

2. **What severity level for married segment warnings?**
   - Why: Married segments don't violate Rule 3015 but affect practical bookability.
   - Options: A) `WARNING` (yellow, prominent) B) `INFO` (blue, informational) C) New severity `BOOKING_RISK` (separate from validation)
   - Recommend: B (INFO) for static pattern detection, A (WARNING) for ExpertFlyer-confirmed married segments. No new severity level — adds complexity without clear benefit.

3. **Should `rtw verify --check-married` compare direct vs. connecting availability automatically?**
   - Why: This doubles ExpertFlyer queries (2x per segment for connection hubs). Rate limiting + daily soft limit (50 queries) is a concern.
   - Options: A) Always check married when verifying B) `--check-married` opt-in flag C) Skip ExpertFlyer married detection entirely, rely on static rules only
   - Recommend: B — opt-in flag. Most users want basic D-class check; married detection is for advanced optimization.

4. **Should the `via` field accept a single string or always require a list?**
   - Why: 99% of through-flights have exactly one via stop. Requiring `via: [SIN]` for every case is verbose.
   - Options: A) `str | list[str]` (accept both, normalize to list) B) Always `list[str]` C) Always `str` (single via stop only)
   - Recommend: A — accept both for user convenience, normalize internally. Pydantic v2 supports this with a validator.

5. **How should via-stop continents interact with per-continent segment limits?**
   - Why: A via stop counts the continent as "visited" for pricing, but the through-flight is still ONE segment. Should it count toward the via-continent's segment limit?
   - Options: A) Via stop adds continent to visited list but does NOT count toward per-continent segment limit B) Via stop counts as a segment in that continent C) Via stop counts as 0.5 segments
   - Recommend: A — the through-flight is one segment (Rule 3015 is clear on this). The via stop affects pricing/continent count only, not segment limits.

---END QUESTIONS---
