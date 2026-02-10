---
description: RTW Optimizer domain knowledge — route building, D-class patterns, NTP rates, CLI usage, Python API
globs:
  - "rtw/**"
  - "tests/**"
  - "*.yaml"
---

# RTW Domain Knowledge

## CLI Usage Patterns

**Commands that take YAML files:**
```bash
python3 -m rtw validate itinerary.yaml        # Validate a YAML file
python3 -m rtw analyze itinerary.yaml          # Full pipeline on YAML file
python3 -m rtw cost itinerary.yaml             # Cost estimate on YAML file
python3 -m rtw ntp itinerary.yaml              # NTP calculation on YAML file
python3 -m rtw scrape availability FILE.yaml   # D-class check on YAML file (NOT `verify`)
python3 -m rtw booking itinerary.yaml          # Booking script from YAML file
```

**Commands that do NOT take YAML files:**
```bash
python3 -m rtw verify                          # Verifies LAST SEARCH results (option IDs)
python3 -m rtw verify --option 1               # Verify specific search option
python3 -m rtw check-nonstop --route "..."     # Nonstop check (route string, not YAML)
python3 -m rtw scan-dates DOH LAX QR --from .. # Date scan (positional args, not YAML)
python3 -m rtw build --route "..." --validate  # Build YAML from route string
```

**Common mistake**: `rtw verify FILE.yaml` does NOT work — use `rtw scrape availability FILE.yaml` for D-class checks on YAML files.

## Python API Quick Reference

**SerpAPI (nonstop/pricing):**
```python
from rtw.scraper.serpapi_flights import search_serpapi, search_serpapi_all
import datetime

date = datetime.date(2026, 4, 1)  # MUST be datetime.date, NOT string

# Single cheapest flight → FlightPrice | None
result = search_serpapi("LAX", "HND", date, max_stops=0)

# All flights → SerpAPIFlightsResponse | None
resp = search_serpapi_all("LAX", "HND", date, max_stops=0)
for f in resp.flights:  # SerpAPIFlight objects
    f.carrier          # "JL" (2-letter IATA)
    f.airline_name     # "JAL"
    f.flight_number    # "JL 15"
    f.stops            # 0
    f.duration_minutes # 705
    f.price_usd        # 3200.0
```

**ExpertFlyer (D-class availability):**
```python
from rtw.scraper.expertflyer import ExpertFlyerScraper
import datetime

scraper = ExpertFlyerScraper()
result = scraper.check_availability("DOH", "LAX", datetime.date(2026, 4, 1),
                                     carrier="QR", booking_class="D")
# result: DClassResult | None
result.seats           # 9 (max across all flights)
result.status          # DClassStatus.AVAILABLE
result.flights         # list[FlightAvailability]
result.nonstop_flights # list[FlightAvailability] (stops=0 only)
result.nonstop_seats   # 9 (max nonstop seats)
result.has_nonstop     # True
scraper.close()
```

**Nonstop checker (SerpAPI-based):**
```python
from rtw.nonstop.checker import NonstopChecker

checker = NonstopChecker()
result = checker.check("LAX", "HND", "JL")  # NonstopResult
result.has_nonstop     # True
result.nonstop_count   # 3
result.alternatives    # ["AA"] (other oneworld carriers with nonstop)
```

**NTP calculator:**
```python
from rtw.ntp import NTPCalculator
from rtw.models import Itinerary

calc = NTPCalculator()
itin = Itinerary(**yaml_data)
estimates = calc.calculate(itin)  # list[NTPEstimate], NOT object with .segments
for e in estimates:
    e.route            # "LAX-HND"
    e.carrier          # "JL"
    e.distance_miles   # 5476
    e.rate             # 0.5
    e.estimated_ntp    # 2738
total = sum(e.estimated_ntp for e in estimates)
```

**Validator:**
```python
from rtw.validator import Validator
from rtw.models import Itinerary

validator = Validator()
itin = Itinerary(**yaml_data)
report = validator.validate(itin)  # ValidationReport
report.passed          # True/False
report.results         # list[RuleResult] (all rules)
report.violations      # list[RuleResult] (failures only)
len(report.results)    # total rules checked
```

## Route Building Knowledge

### Airport Preferences
- **HND > NRT** for Tokyo: AY flies HND-HEL nonstop, JL flies HND-SYD nonstop; neither from NRT
- Always verify nonstop service with `rtw check-nonstop` before building — many plausible pairs have no nonstop

### Nonstop Gotchas (NO nonstop despite seeming plausible)
- NRT-SYD (JL) — JL nonstops are from HND
- NRT-HEL (AY) — AY nonstops are from HND
- SYD-LHR (QF) — no nonstop, goes via SIN or PER

### D-class Patterns
- **QR**: Generous — D9 common on DOH routes (DOH-LAX, DOH-LHR, etc.)
- **JL**: Good availability, especially HND-SYD
- **AY**: Tight on long-haul nonstops — HEL-LAX AY1 showed 0/12 dates nonstop D-class
- **BA**: D9 common on LHR-LAX (5+ daily flights)

### NTP Earning Rates (for route optimization)
- **Tier 1 (50% distance)**: JL, QR, AY, FJ, RJ, S7, WY
- **Tier 2 (25% distance)**: CX, QF, MH, SL
- **Revenue-based (~0 on D-class)**: BA, AA, IB, AS

### Proven LAX Westbound Routes
- **V1 Direct** (4 seg): LAX→HND:JL → SYD:JL → DOH:QR → LAX:QR — 13,158 NTP, all D-class confirmed
- **V2 London** (5 seg): LAX→HND:JL → SYD:JL → DOH:QR → LHR:QR → LAX:BA — 11,684 NTP, all D-class confirmed

### AY1 HEL-LAX Schedule
- Operates Mon/Wed/Thu ONLY
- D-class extremely scarce on nonstop (0 across all dates checked Apr 2026)
