---
spec: via-through-flights
phase: requirements
created: 2026-02-16
generated: auto
---

# Requirements: via-through-flights

## Summary

Add a `via` field to itinerary segments to model through-flight technical stops, enabling the validator to count intermediate continent visits without consuming extra segments. Provide a known through-flight reference table and extend booking intelligence with married segment detection (static patterns + ExpertFlyer live checks).

## User Stories

### US-1: Declare through-flight via stops in YAML

As an RTW planner, I want to add a `via` field to a segment so that the validator counts the intermediate stop's continent for pricing without adding an extra segment.

**Acceptance Criteria**:
- AC-1.1: `via: SIN` (string) and `via: [SIN]` (list) both accepted; normalized to list internally
- AC-1.2: Via airports validated as 3-letter IATA codes, uppercased automatically
- AC-1.3: Omitting `via` field (or `via: null`) has no effect; all existing YAML fixtures remain valid
- AC-1.4: `via` field appears in `rtw show` output when present
- AC-1.5: Multiple via stops supported: `via: [SIN, KUL]`

### US-2: Count via-stop continents for pricing

As an RTW planner, I want via-stop continents to be counted as "visited" for continent pricing so that my ticket type matches reality (e.g., QF1 SYD-SIN-LHR counts Asia).

**Acceptance Criteria**:
- AC-2.1: Via-stop airport resolved to continent using existing `get_continent()` function
- AC-2.2: Via-stop continent added to `continents_visited` if not already present
- AC-2.3: Via-stop does NOT count toward per-continent segment limit (through-flight = one segment)
- AC-2.4: Via-stop does NOT increment `segments_per_continent` for the via continent
- AC-2.5: Same-continent via stops (e.g., PER for SWP->SWP) have no effect on continent count
- AC-2.6: Via-stop continent counting supplements (does not replace) existing implicit EU_ME<->SWP Asia detection

### US-3: Reference known through-flights

As an RTW planner, I want to look up known oneworld through-flights so that I know which routes have cross-continent technical stops.

**Acceptance Criteria**:
- AC-3.1: `rtw/data/through_flights.yaml` contains known through-flights with carrier, flight number, from, to, via, and continents_added fields
- AC-3.2: Data is reference-only; does NOT auto-populate `via` on segments (user must add `via` explicitly)
- AC-3.3: Data includes at minimum: QF1/2, BA15/16, QR920/921, QR908/909
- AC-3.4: Data easily editable (simple YAML, no complex schema)

### US-4: Detect married segment risks (static patterns)

As an RTW planner, I want the validator to warn about married segment risks so that I can plan connections that are actually bookable.

**Acceptance Criteria**:
- AC-4.1: CX hub-connection pattern detected: CX segment where neither endpoint is HKG, but itinerary has CX connection through HKG
- AC-4.2: QF standalone D-class pattern: QF long-haul segment without QF domestic connection
- AC-4.3: Through-flight split warning: segment with `via` field where via-stop city has a stopover (splitting = reissue fee)
- AC-4.4: Same-day transit warning (existing) preserved and enhanced with carrier-specific context
- AC-4.5: Static pattern warnings have severity INFO
- AC-4.6: Married segment rules registered in rule engine via `@register_rule`

### US-5: Detect married segments via ExpertFlyer

As an RTW planner, I want ExpertFlyer verification to always check for married segment patterns so that I get live availability intelligence.

**Acceptance Criteria**:
- AC-5.1: During `rtw verify`, compare direct availability vs. connection availability for known hub carriers (CX/HKG, QR/DOH)
- AC-5.2: If D-class available only via connection but not standalone, flag as "married segment detected" with WARNING severity
- AC-5.3: Rate limiting: paired queries count toward daily soft limit; throttled appropriately
- AC-5.4: Married segment check runs automatically during verify (not opt-in)
- AC-5.5: Results include married segment flag on `DClassResult` or `SegmentVerification`

### US-6: Enhanced booking script warnings

As an RTW planner, I want the booking phone script to include through-flight and married segment warnings so the booking agent handles them correctly.

**Acceptance Criteria**:
- AC-6.1: Through-flight segments show via-stop info: "Through-flight via {stop} -- one segment, counts {continent}"
- AC-6.2: Married segment risk segments show warning: "Married segment risk: {carrier} D-class may require connection through {hub}"
- AC-6.3: Through-flight split warning: "Stopping over at {via} converts 1 segment to 2 + $125 reissue"
- AC-6.4: GDS commands for through-flights book as single segment (no split)

## Functional Requirements

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| FR-1 | Add optional `via` field to Segment model: `Optional[str \| list[str]] = None` | Must | US-1 |
| FR-2 | Pydantic validator normalizes `via` to `list[str]`, uppercases airport codes | Must | US-1 |
| FR-3 | `build_context()` resolves via-stop continents, adds to `continents_visited` | Must | US-2 |
| FR-4 | Via-stop continents tracked separately in ValidationContext (`via_continents` field) | Must | US-2 |
| FR-5 | Via-stop does NOT affect `segments_per_continent` counts | Must | US-2 |
| FR-6 | Create `rtw/data/through_flights.yaml` with known through-flights | Should | US-3 |
| FR-7 | Create `rtw/rules/married.py` with static married segment pattern rules | Should | US-4 |
| FR-8 | Register married segment rules in validator's `_discover_rules()` | Should | US-4 |
| FR-9 | CX hub-connection married pattern detection | Should | US-4 |
| FR-10 | QF standalone D-class married pattern detection | Should | US-4 |
| FR-11 | Through-flight split detection (via-stop with stopover = reissue warning) | Should | US-4 |
| FR-12 | ExpertFlyer paired query for married segment detection during verify | Could | US-5 |
| FR-13 | `MarriedSegmentFlag` on verify results | Could | US-5 |
| FR-14 | Booking script through-flight annotations | Should | US-6 |
| FR-15 | Booking script married segment warnings | Should | US-6 |
| FR-16 | GDS commands treat through-flights as single segment | Should | US-6 |
| FR-17 | `rtw show` displays via-stop information when present | Should | US-1 |

## Non-Functional Requirements

| ID | Requirement | Category |
|----|-------------|----------|
| NFR-1 | All existing 1168+ tests pass with no changes (backward compatibility) | Compatibility |
| NFR-2 | All 37+ YAML fixtures remain valid without modification | Compatibility |
| NFR-3 | Through-flight data YAML loads in <10ms on startup | Performance |
| NFR-4 | No mocks for API responses in tests; fixtures and real data only | Testing |
| NFR-5 | Married segment ExpertFlyer queries respect existing rate limiting (5s between, 50/day soft limit) | Performance |
| NFR-6 | New rule file follows `@register_rule` pattern exactly | Consistency |
| NFR-7 | Via field Pydantic validator follows existing `field_validator` patterns in Segment model | Consistency |

## Out of Scope

- Auto-detection of through-flights from route data (user explicitly opted out)
- Seasonal date ranges on through-flight data (separate concern)
- Via field accepting airport names (IATA codes only)
- Connection time threshold refinement (existing same-day check preserved)
- Via stops contributing to per-continent segment limits
- Auto-populating `via` from through-flight lookup table

## Dependencies

- Existing `get_continent()` in `rtw/continents.py` for via-stop continent resolution
- Existing `@register_rule` decorator in `rtw/rules/base.py` for married segment rules
- Existing `ExpertFlyerScraper` in `rtw/scraper/expertflyer.py` for paired queries
- Existing `BookingGenerator` in `rtw/booking.py` for phone script warnings
- Pydantic v2 `field_validator` for via field normalization
