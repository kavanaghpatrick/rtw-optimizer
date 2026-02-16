---
spec: via-through-flights
phase: tasks
total_tasks: 13
created: 2026-02-16
generated: auto
---

# Tasks: via-through-flights

## Phase 1: Make It Work (POC)

Focus: Via field on model + continent counting in validator. End-to-end proof that `via: SIN` on a segment causes Asia to appear in `continents_visited`.

- [ ] 1.1 Add `via` field to Segment model with normalization
  - **Do**: In `rtw/models.py`, add `via: Optional[str | list[str]] = None` to the `Segment` class. Add a `@field_validator("via", mode="before")` that normalizes: `None` -> `None`, `str` -> `[str.upper()]`, `list` -> `[x.upper() for x in list]`. Add `has_via` property (returns `bool`) and `via_airports` property (returns `self.via or []`).
  - **Files**: `rtw/models.py`
  - **Done when**: `Segment(**{"from": "SYD", "to": "LHR", "carrier": "QF", "via": "sin"})` produces `via=["SIN"]`. `Segment(**{"from": "SYD", "to": "LHR", "carrier": "QF"})` produces `via=None`. `Segment(**{"from": "DOH", "to": "ADL", "carrier": "QR", "via": ["sin", "kul"]})` produces `via=["SIN", "KUL"]`.
  - **Verify**: `uv run pytest tests/test_models.py -x`
  - **Commit**: `feat(models): add via field to Segment for through-flight stops`
  - _Requirements: FR-1, FR-2_
  - _Design: Component A_

- [ ] 1.2 Extend ValidationContext and build_context() for via-continent counting
  - **Do**: In `rtw/validator.py`, add two new fields to `ValidationContext`: `via_continents: list[Continent]` and `via_continent_segments: dict[Continent, list[tuple[int, str]]]` (both with `default_factory`). In `build_context()`, after the main segment loop and BEFORE `_detect_implicit_continents()`, add a second loop over segments: for each segment's `via_airports`, call `get_continent(via_apt)`. If continent found and not in `seen_continents`, append it. Track in `via_continent_segments` as `(segment_index, via_airport)`. Assign to context fields.
  - **Files**: `rtw/validator.py`
  - **Done when**: An itinerary with segment `SYD->LHR via SIN` has `Asia` in `ctx.continents_visited` and `ctx.via_continents == [Continent.ASIA]`. An itinerary with `SYD->FCO via PER` does NOT add a new continent (PER is SWP, already counted).
  - **Verify**: `uv run pytest tests/test_validator.py -x`
  - **Commit**: `feat(validator): count via-stop continents in build_context`
  - _Requirements: FR-3, FR-4, FR-5_
  - _Design: Component B_

- [ ] 1.3 POC Checkpoint — end-to-end via continent counting
  - **Do**: Create test fixture `tests/fixtures/via_through_flight.yaml` with a DONE4 itinerary that includes a QF SYD-LHR segment with `via: SIN`. Verify that full validation counts Asia as visited, via-stop does NOT increment segments_per_continent for Asia, and existing tests still pass. Create `tests/test_rules/test_via_counting.py` with 3-5 targeted tests.
  - **Files**: `tests/fixtures/via_through_flight.yaml`, `tests/test_rules/test_via_counting.py`
  - **Done when**: New fixture validates successfully. Asia appears in continents_visited. `segments_per_continent` for Asia is 0 (or whatever the non-via count is). All existing tests pass.
  - **Verify**: `uv run pytest -x` (full suite)
  - **Commit**: `feat(via): complete POC — via field with continent counting`
  - _Requirements: AC-2.1 through AC-2.6_
  - _Design: Components A, B_

## Phase 2: Core Features

After POC validated, build out remaining features: through-flight data, married segment rules, booking warnings.

- [ ] 2.1 Create through-flight reference data YAML
  - **Do**: Create `rtw/data/through_flights.yaml` with the known through-flights from research: QF1/2 (SYD-SIN-LHR), BA15/16 (LHR-SIN-SYD), QR920/921 (DOH-SIN-ADL), QR908/909 (DOH-SIN-MEL), QF5/6 (SYD-PER-FCO, no continent impact), QF3/4 (SYD-AKL-JFK, no continent impact). Follow schema from design: carrier, flights (list), from, to, via (list), continents_added (list), notes (optional string). Add a loader function in a new `rtw/through_flights.py` module (or inline in data loading).
  - **Files**: `rtw/data/through_flights.yaml`, optionally `rtw/through_flights.py`
  - **Done when**: YAML file exists and is loadable with `yaml.safe_load()`. Data has at least 6 entries. Tests for data integrity (carrier codes valid, airport codes 3-letter).
  - **Verify**: `python3 -c "import yaml; d=yaml.safe_load(open('rtw/data/through_flights.yaml')); print(len(d['through_flights']), 'through-flights loaded')"`
  - **Commit**: `feat(data): add known through-flights reference YAML`
  - _Requirements: FR-6, AC-3.1 through AC-3.4_
  - _Design: Component C_

- [ ] 2.2 Create married segment rules file
  - **Do**: Create `rtw/rules/married.py` with `@register_rule` class `MarriedSegmentRule`. Implement three checks: (1) CX hub-connection — CX segments where neither endpoint is HKG, warn about married risk through HKG; (2) Through-flight split — segment has `via` stop and that via-stop city appears as a stopover destination elsewhere in the itinerary, warn about $125 reissue; (3) Return INFO pass result if no issues. All warnings use `Severity.INFO`. Register the module in `rtw/validator.py:_discover_rules()` by adding `import rtw.rules.married`.
  - **Files**: `rtw/rules/married.py`, `rtw/validator.py` (one import line)
  - **Done when**: Married rule appears in `get_registered_rules()`. CX segment NRT-SIN on a CX-heavy itinerary triggers INFO warning. Through-flight via SIN with SIN stopover elsewhere triggers split warning. Itinerary with no CX and no via fields gets "No married segment risks detected."
  - **Verify**: `uv run pytest tests/test_validator.py -x && uv run pytest -x`
  - **Commit**: `feat(rules): add married segment pattern detection`
  - _Requirements: FR-7, FR-8, FR-9, FR-11, AC-4.1 through AC-4.6_
  - _Design: Component D_

- [ ] 2.3 Enhance booking script with through-flight and married segment warnings
  - **Do**: In `rtw/booking.py:_segment_scripts()`, add through-flight annotation block: if `seg.has_via`, resolve via-stop continents, add warning string, and append via info to phone instruction. For GDS commands in `_gds_commands()`, through-flights should be booked as single segment (already the case — no change needed, but add a comment). Enhance existing married segment warning text with carrier-specific context when carrier is CX (mention HKG hub).
  - **Files**: `rtw/booking.py`
  - **Done when**: Booking script for QF SYD-LHR with `via: SIN` includes "Through-flight via SIN" in phone instructions and warnings. GDS commands still show single SS command for the segment.
  - **Verify**: `uv run pytest tests/test_booking.py -x`
  - **Commit**: `feat(booking): add through-flight and married segment warnings`
  - _Requirements: FR-14, FR-15, FR-16, AC-6.1 through AC-6.4_
  - _Design: Component E_

- [ ] 2.4 Add married_segment_note to SegmentVerification and detect in verifier
  - **Do**: In `rtw/verify/models.py`, add `married_segment_note: Optional[str] = None` to `SegmentVerification`. In `rtw/verify/verifier.py`, after checking direct availability for a segment, check if the carrier is in `_MARRIED_CHECK_HUBS` dict (`{"CX": "HKG", "QR": "DOH"}`). If direct result has `seats == 0` but `flights` list contains connecting flights with seats > 0, set `married_segment_note` on the SegmentVerification. This uses existing ExpertFlyer results (no extra queries needed for the basic version).
  - **Files**: `rtw/verify/models.py`, `rtw/verify/verifier.py`
  - **Done when**: SegmentVerification has `married_segment_note` field. CX segment with 0 nonstop D-class but connecting D-class available gets note "D-class only via connection (likely married through HKG)".
  - **Verify**: `uv run pytest tests/test_verify_models.py -x`
  - **Commit**: `feat(verify): detect married segment patterns from ExpertFlyer results`
  - _Requirements: FR-12, FR-13, AC-5.1, AC-5.2, AC-5.5_
  - _Design: Component F_

## Phase 3: Testing

- [ ] 3.1 Unit tests for via field and continent counting
  - **Do**: In `tests/test_models.py`, add tests for: via=None (default), via="sin" (normalized to ["SIN"]), via=["sin","kul"] (normalized to ["SIN","KUL"]), via_airports property, has_via property, invalid via (non-string elements). In `tests/test_rules/test_via_counting.py`, add tests for: via-stop adds continent, via-stop same continent no effect, multiple via stops, via-stop does NOT increment segments_per_continent, via-stop combined with implicit Asia rule (both should work independently).
  - **Files**: `tests/test_models.py`, `tests/test_rules/test_via_counting.py`
  - **Done when**: At least 10 new tests pass covering all acceptance criteria from US-1 and US-2.
  - **Verify**: `uv run pytest tests/test_models.py tests/test_rules/test_via_counting.py -v`
  - **Commit**: `test(via): add unit tests for via field and continent counting`
  - _Requirements: AC-1.1 through AC-1.5, AC-2.1 through AC-2.6_

- [ ] 3.2 Unit tests for married segment rules
  - **Do**: Create `tests/test_rules/test_married.py`. Test scenarios: (1) CX segment not through HKG triggers INFO warning, (2) CX segment through HKG does NOT trigger warning, (3) through-flight split: segment with via SIN + SIN stopover elsewhere triggers warning, (4) through-flight no split: via SIN but no SIN stopover, (5) no CX no via = pass result, (6) multiple CX segments produce multiple warnings.
  - **Files**: `tests/test_rules/test_married.py`
  - **Done when**: At least 6 tests covering all married segment patterns pass.
  - **Verify**: `uv run pytest tests/test_rules/test_married.py -v`
  - **Commit**: `test(married): add unit tests for married segment rules`
  - _Requirements: AC-4.1 through AC-4.6_

- [ ] 3.3 Unit tests for booking script through-flight warnings
  - **Do**: In `tests/test_booking.py`, add tests for: (1) segment with via produces through-flight warning in phone script, (2) segment with via shows via info in instruction text, (3) segment without via has no through-flight warning, (4) GDS command for via segment is single SS entry (not split).
  - **Files**: `tests/test_booking.py`
  - **Done when**: At least 4 new booking tests pass.
  - **Verify**: `uv run pytest tests/test_booking.py -v`
  - **Commit**: `test(booking): add through-flight warning tests`
  - _Requirements: AC-6.1 through AC-6.4_

- [ ] 3.4 Integration test with through-flight itinerary
  - **Do**: In `tests/test_integration.py` or `tests/test_new_fixtures.py`, add a test that loads the `via_through_flight.yaml` fixture, runs full validation, and asserts: (1) validation passes, (2) continents_visited includes the via-stop continent, (3) married segment rule produces results, (4) booking script includes through-flight annotations.
  - **Files**: `tests/test_integration.py` or `tests/test_new_fixtures.py`
  - **Done when**: Integration test exercises full pipeline: YAML -> model -> validator -> rules -> booking for a through-flight itinerary.
  - **Verify**: `uv run pytest tests/test_integration.py -v -k via`
  - **Commit**: `test(integration): add through-flight end-to-end test`

## Phase 4: Quality Gates

- [ ] 4.1 Local quality check
  - **Do**: Run full test suite, lint check, and verify no regressions. Ensure all 1168+ existing tests still pass plus new tests. Run `ruff check` on all modified files.
  - **Verify**: `ruff check rtw/ tests/ && uv run pytest -x`
  - **Done when**: All commands pass with 0 errors. Total test count has increased.
  - **Commit**: `fix(via): address lint/type issues` (if needed)

- [ ] 4.2 Create PR and verify CI
  - **Do**: Push branch, create PR with gh CLI. PR title: "feat: add via field for through-flight stops + married segment detection". PR body: summary of changes, link to spec, test plan.
  - **Verify**: `gh pr checks --watch` all green
  - **Done when**: PR ready for review with all CI checks passing.

## Notes

- **POC shortcuts taken**: Phase 1 skips married rules, booking warnings, and ExpertFlyer integration. Just model + validator.
- **Production TODOs**: ExpertFlyer paired query for married detection uses existing connection results (no extra queries). Full paired query implementation deferred if basic detection is sufficient.
- **Backward compatibility**: All changes are additive. `via: null` default means zero impact on existing YAML files.
- **Rule count**: After adding married.py, total rules will be 25 across 11 files.
