# Output Formatting Layer

How the RTW optimizer renders CLI output across three formatters (Rich, Plain, JSON) plus a standalone search formatter.

## Architecture

### File Layout

```
rtw/output/
  __init__.py            # Formatter protocol + factory (get_formatter)
  rich_formatter.py      # Rich tables/panels with ANSI color
  plain_formatter.py     # Pure text, no escapes -- safe for piping
  json_formatter.py      # Machine-readable JSON for jq / scripting
  search_formatter.py    # Standalone search result formatters (not behind protocol)
```

### Formatter Protocol

Defined in `__init__.py` as a `typing.Protocol` with five methods:

| Method | Input | Purpose |
|--------|-------|---------|
| `format_validation` | `ValidationReport` | Rule 3015 validation pass/fail |
| `format_ntp` | `list[NTPEstimate]` | BA New Tier Points per segment |
| `format_cost` | `CostEstimate` | Base fare + YQ + total breakdown |
| `format_value` | `list[SegmentValue]` | Per-segment value rating |
| `format_booking` | `BookingScript` | Phone script + GDS commands |

All methods return `str`. The protocol is structural (duck typing) -- formatters do not inherit from a base class.

### Factory: `get_formatter(name)`

```python
get_formatter("rich")   # -> RichFormatter
get_formatter("plain")  # -> PlainFormatter
get_formatter("json")   # -> JsonFormatter
```

Raises `ValueError` for unrecognized names.

## CLI Format Selection

The CLI resolves which formatter to use via `_get_format()` in `rtw/cli.py`:

```
Priority: --json > --plain > TTY auto-detect
```

1. `--json` flag: always returns `"json"`
2. `--plain` flag: always returns `"plain"`
3. No flag, stdout is a TTY: returns `"rich"` (colored output)
4. No flag, stdout is piped/redirected: returns `"plain"` (no ANSI escapes)

The flags are declared as Typer annotated types:

```python
PlainFlag = Annotated[bool, typer.Option("--plain", help="Output as plain text (no color).")]
JsonFlag  = Annotated[bool, typer.Option("--json", help="Output as JSON.")]
```

Every analysis command (`validate`, `cost`, `ntp`, `value`, `booking`, `analyze`) passes these flags through `_get_format()` to `get_formatter()`.

## Rich Formatter

**File**: `rtw/output/rich_formatter.py`

Uses the Rich library (`Console`, `Panel`, `Table`, `Text`) to produce colored terminal output. All rendering goes through a private `_render()` helper that captures Rich output to a `StringIO` buffer with `force_terminal=True` and a fixed width of 120 columns.

### Color / Style Maps

**Severity styles** (validation issues):

| Severity | Style |
|----------|-------|
| VIOLATION | `bold red` |
| WARNING | `yellow` |
| INFO | `blue` |

**Verdict styles** (segment value):

| Verdict | Style |
|---------|-------|
| Excellent | `bold green` |
| Good | `blue` |
| Moderate | `yellow` |
| Low | `bold red` |

### What Each Method Renders

**`format_validation`** -- Three-section layout:
- **Summary Panel**: cyan border, shows PASS (green) or FAIL (red), ticket type, passenger count, segment counts, rule pass rate, violation/warning counts (color-coded when non-zero)
- **Issues Table**: red border, `show_lines=True`, columns: #, Severity (styled), Rule (cyan), Detail (includes fix suggestion in dim, rule reference in dim)
- **Passed Rules Table**: green border, compact (`show_lines=False`), columns: Rule (cyan), Status (green "OK"), Detail
- **Info Table**: blue border, dim detail text

**`format_ntp`** -- Single table with `show_lines=True`:
- Columns: #, Route (cyan), Carrier, Distance (right-aligned), Method, Rate, NTP (bold green, right-aligned), Confidence, Notes
- Final row: TOTAL (bold) with summed distance and NTP (bold green)

**`format_cost`** -- Single panel with green border:
- Key-value pairs: Origin, Ticket Type, Base Fare, Total YQ, Per Person, Passengers, Total All Pax, Plating Carrier, Notes (if present)
- All amounts formatted as `$X,XXX.XX`

**`format_value`** -- Single table with `show_lines=True`:
- Columns: #, Route (cyan), Carrier, J Cost (right-aligned), Verdict (styled per verdict map), Suggestion, Source (dim)

**`format_booking`** -- Multi-panel layout:
- **Opening Script**: cyan border panel
- **Per-Segment Panels**: green border (clean) or yellow border (has warnings); includes `WARNING:` lines appended to content
- **Closing Checklist**: cyan border panel
- **GDS Commands**: blue border panel, commands joined by newlines
- **Warnings Summary**: yellow border panel (only if warnings exist), bulleted list

## Plain Formatter

**File**: `rtw/output/plain_formatter.py`

Produces pure ASCII text with no ANSI escape sequences. Designed for piping to files, `grep`, or other tools. Uses two header helpers:

- `_header(title)`: `===...===` box (60-char wide)
- `_subheader(title)`: `--- title ---`

### What Each Method Renders

**`format_validation`**:
- Header: "Validation Summary"
- Key-value block: Status (PASS/FAIL), Ticket, Passengers, Segments, Rules, Violations, Warnings
- Issues sub-section: numbered list with `[VIOLATION]`/`[WARNING]`/`[INFO]` tags, message, fix suggestion
- Passed Rules sub-section: `OK` prefix, left-aligned rule name (35 chars), message
- Info sub-section: indented rule name + message

**`format_ntp`**:
- Header: "NTP Estimates"
- Fixed-width columnar table with dash separators
- Columns: #, Route, Carrier, Distance, Method, Rate, NTP, Confidence, Notes
- Footer: TOTAL row with summed distance and NTP

**`format_cost`**:
- Header: "Cost Estimate"
- Key-value pairs, dollar amounts as `$X,XXX.XX`

**`format_value`**:
- Header: "Segment Value Analysis"
- Fixed-width columnar table
- Columns: #, Route, Carrier, J Cost, Verdict, Suggestion, Source

**`format_booking`**:
- Header: "Booking Script"
- Sub-sections: Opening, per-segment (with `WARNING:` lines), Closing Checklist, GDS Commands (indented), Warnings (bulleted)

## JSON Formatter

**File**: `rtw/output/json_formatter.py`

Outputs `json.dumps(..., indent=2)` with Pydantic `model_dump(mode="json")` serialization. Each method wraps the data in an object with a `"type"` discriminator field.

| Method | `type` value | Extra fields |
|--------|-------------|--------------|
| `format_validation` | `"validation_report"` | `summary` (passed, violation_count, warning_count, total_rules), `ticket`, `results[]` |
| `format_ntp` | `"ntp_estimates"` | `summary` (total_ntp, total_distance_miles, segment_count), `estimates[]` |
| `format_cost` | `"cost_estimate"` | All `CostEstimate` fields spread at top level |
| `format_value` | `"segment_value_analysis"` | `segment_count`, `values[]` |
| `format_booking` | `"booking_script"` | All `BookingScript` fields spread at top level |

## Search Formatter (Standalone)

**File**: `rtw/output/search_formatter.py`

Not part of the `Formatter` protocol. Exports six standalone functions called directly by the `search` CLI command:

| Function | Phase | Format |
|----------|-------|--------|
| `format_search_skeletons_rich` | Phase 1 (route skeleton) | Rich markup |
| `format_search_skeletons_plain` | Phase 1 | Plain text |
| `format_search_results_rich` | Phase 2 (with availability) | Rich table per option |
| `format_search_results_plain` | Phase 2 | Plain text |
| `format_search_json` | Final | JSON |

**Rich skeleton** (Phase 1): Header with candidate count, per-option block with rank, direction, score, segment count, route string (arrow-separated), carrier codes (dim).

**Rich results** (Phase 2): One `Table` per option with columns: #, Route (cyan), Carrier, Flight, Date, Stops, Availability (color-coded by `AvailabilityStatus`). Fare comparison line below table using verdict styling.

**Availability status colors**:

| Status | Color | Label |
|--------|-------|-------|
| AVAILABLE | `bold green` | AVAILABLE |
| LIKELY | `yellow` | LIKELY |
| UNKNOWN | `dim` | UNKNOWN |
| NOT_AVAILABLE | `bold red` | NOT AVAIL |
| NOT_CHECKED | `dim` | - |

**Fare comparison** (Rich): Shows RTW fare, segment total (X/Y priced), savings, value multiplier + verdict with Rich style markup.

**Fare comparison** (Plain): Same data in flat text format: `Value: RTW $X vs Individual $Y (N/M priced) = $Z savings (Nx)`.

**JSON**: Full structured output with query params, summary, per-option segments with availability details and fare comparison object.

The search command falls back from Rich to Plain on `ImportError` (Rich not installed).

## Verify Display (Inline in CLI)

**Location**: `_display_verify_result()` in `rtw/cli.py` (lines 873-1039)

Not part of the formatter layer. Renders D-class verification results directly in the CLI using Rich or a plain-text fallback. Outputs to **stderr** (not stdout).

**Rich mode** features:
- Table with columns: #, Route, Carrier, Date, D-Class, Seats
- Color coding: green (available), red (not available), yellow (error), dim (surface/unchecked)
- `TIGHT` badge (bold red) when 2 or fewer flights have D availability
- Per-flight sub-rows showing flight number, departure time, aircraft, stops, D-class seat count
- D0 flight count note (dim)
- Alternate date hints for unavailable segments (cyan)
- Connection-only segment callout (yellow) with `check-nonstop` command suggestion
- Summary line: green bold "All confirmed" or yellow partial percentage

**Plain fallback**: Same data in simple indented text, one line per segment and sub-flight.

## Test Coverage

**File**: `tests/test_output.py` (~560 lines)

| Test Class | What It Covers |
|------------|----------------|
| `TestGetFormatter` | Factory returns correct types, unknown raises `ValueError` |
| `TestRichFormatter` | Non-empty output, contains expected content (rule names, amounts, verdicts, GDS commands) |
| `TestPlainFormatter` | Non-empty output, **no ANSI escapes** (regex check), contains expected content |
| `TestJsonFormatter` | Valid JSON parse, correct `type` discriminators, expected structure and field presence |
| `TestProtocolConformance` | All three formatters have all five methods, return strings, return non-empty output |

The ANSI escape check in `TestPlainFormatter._assert_no_ansi()` uses a regex for ESC-bracket sequences and CSI codes to guarantee the plain formatter is truly pipe-safe.
