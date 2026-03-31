# KB: Hub O&D Control — Why ExpertFlyer D-Class Doesn't Mean Bookable

Source: 5-agent research team (FlyerTalk scraping + web research + academic papers)
Scraped: 2026-03-30

---

## Summary

When ExpertFlyer shows D-class available on a segment like CX LAX→HKG, it does NOT mean an agent can book it on an RTW ticket. Modern airlines use Origin-Destination (O&D) revenue management to show different availability depending on the passenger's full journey. This is the primary cause of the "EF shows D9 but agent can't book" problem — not a bug, not stale data, but deliberate airline inventory control.

---

## 1. The Core Mechanism: O&D Revenue Management

### Leg-Based vs O&D Control

| System | How It Works | Who Sees What |
|--------|-------------|---------------|
| **Leg-based** (legacy) | D-class is open or closed per flight, same for everyone | EF = agent = reality |
| **O&D-based** (modern) | D-class availability varies by the passenger's full origin-destination pair | EF sees leg-level cache; agent sees O&D-filtered reality |

Under O&D control, the **same physical seat** on CX882 LAX→HKG has different availability depending on who's asking:

- **LAX→HKG standalone** (local passenger): D-class BLOCKED — CX protects premium HKG-bound revenue seats
- **LAX→CTU via HKG** (connecting passenger): D-class RELEASED — CX wants this through-traffic

### Why Airlines Do This

Airlines use **bid prices** (minimum fare thresholds) per seat per leg. The bid price for a "local" passenger terminating at the hub on a cheap RTW fare is HIGH. For a connecting passenger whose total journey revenue across two legs clears the hurdle, the threshold is met.

The economics: a LAX→HKG local business class passenger might pay $8,000. An RTW D-class passenger pays maybe $400 prorated for that segment. CX would rather hold the seat for the $8,000 passenger. But LAX→CTU via HKG represents "found revenue" — traffic that wouldn't exist otherwise — so they release it.

### CX Specifically

Cathay Pacific has used the **PROS O&D Revenue Management Suite** since 2007. Their system:
- Evaluates every booking request against the full O&D pair
- Applies different bid prices for hub-local vs hub-connecting traffic
- Uses married segment control to enforce the connection requirement after booking
- Asia Miles members see full inventory; partner programs and RTW fares see restricted inventory

---

## 2. How the GDS Query Differs

When availability is checked, the GDS sends an EDIFACT AVLREQ message to the airline. This message **explicitly tells the airline whether the query is standalone or connected:**

### Single Segment Query (ExpertFlyer)
```
ODI = LAX-HKG
TVL = CX882
→ Airline sees: "local passenger terminating at hub"
→ Response: D blocked for RTW fares
```

### Connected Journey Query (Agent booking)
```
ODI = LAX-CTU
TVL = CX882 LAX-HKG + CX### HKG-CTU (with CNX marker)
→ Airline sees: "flow passenger connecting through hub"
→ Response: D released
```

**ExpertFlyer queries leg-level cached availability.** When an agent tries to **sell** a segment, the airline's host system applies O&D controls in real-time, potentially returning more restrictive availability than the cache showed.

### Amadeus Availability Sources

| Source | O&D Aware? | Used By |
|--------|-----------|---------|
| AVS (cached) | No | ExpertFlyer, general queries |
| Polling (real-time) | Partial | Some GDS queries |
| Calculator | Yes | Sell transactions |
| Seamless (real-time host) | Yes | Agent sell with full itinerary context |

Only the calculator and seamless sources carry full O&D context. ExpertFlyer uses AVS (cached), which is O&D-blind.

---

## 3. Confirmed Hub Patterns by Carrier

### Confirmed: Aggressive O&D Control

| Carrier | Hub | Pattern | Severity | Evidence |
|---------|-----|---------|----------|----------|
| **CX** | HKG | Blocks standalone D to/from HKG; releases for connections | **High** | JFK-HKG=0, JFK-HKG-BKK=4 seats. LAX-HKG=FS-, LAX-HKG-SIN=FS+. Uses PROS O&D RM since 2007. |
| **QR** | DOH | Same O&D married segment logic; worst offender | **High** | CMN-OSL=0 vs CMN-LHR via DOH=available. Even >24hr stopovers sometimes fail to break MSC. |

### Confirmed: Different Mechanism

| Carrier | Hub | Pattern | Mechanism |
|---------|-----|---------|-----------|
| **AA** | DFW/ORD | Uses marriage to ADD availability for connections (inverse pattern) | O&D opens MORE seats for connections |
| **BA** | LHR | Varies by journey origin, not married segments | Point of Commencement (POC) restrictions |

### Suspected / Partial

| Carrier | Hub | Evidence |
|---------|-----|----------|
| **QF** | SYD | Refuses to honor EF D-class for RTW; likely agency-level blocking |
| **JL** | NRT | Holds D-class until ~90 days out; some MSC on US-Japan routes |
| **AY** | HEL | Applies MSC to award classes X, U, F specifically |

### Not Observed

| Carrier | Hub | Notes |
|---------|-----|-------|
| **MH** | KUL | Broad partner restriction, not hub-specific MSC |

---

## 4. Can You Drop the Onward Leg Later?

The "add a sacrificial onward to unlock hub availability, then drop it" technique:

### GDS Behavior

| Action | Sabre | Amadeus |
|--------|-------|---------|
| Cancel one leg of married pair | "Carrier refuses cancellation" | XE command: inconsistent results |
| Drop via $125 routing change on RTW | Theoretically possible post-ticketing | May trigger re-evaluation |
| Drop after flying the first leg | **Safe** — coupon is consumed | **Safe** |

### Risk Assessment

| Risk | Severity | Details |
|------|----------|---------|
| CX re-evaluates and blocks | **Medium** | Reissue may trigger fresh O&D check |
| QR flags as policy violation | **High** | QR explicitly monitors for dummy segments |
| ADM penalty to agent | **Medium** | $300+/segment if carrier detects manipulation |
| Retroactive cancellation of ticketed seat | **Low** | Not documented on FlyerTalk |

### Safer Alternatives (What Daniel Probably Does)

1. **Make the onward useful** — route through a city you want to visit, not a sacrificial dummy
2. **Sell segments individually** — query standalone availability, which may differ from connected search
3. **Try codeshare numbers** — same physical CX flight under a different airline code
4. **Direct carrier inventory request** — escalate to CX to request D-class release
5. **Fly first, drop later** — once LAX→HKG coupon is used, drop CTU safely for $125
6. **Non-sequential segment building** — add the "easy" segments first, insert hub segments later in PNR context

### Cost of the Trick (If Used)

- Add onward: $125 routing change
- Drop later: $125 routing change (separate transaction)
- Total: $250 in fees, plus risk of re-evaluation

---

## 5. What This Means for Our Tool

### Current State

Our ExpertFlyer scraper (`rtw/scraper/expertflyer.py`) queries **leg-level availability only** — the AVS cache layer. It cannot see O&D restrictions, POC filtering, or real-time seamless availability. This means:

- D9 on EF for a hub segment could be a **false positive** (unbookable standalone)
- D0 on EF for a hub connection could be a **false negative** (bookable as married pair)

### Existing Code

- `rtw/verify/verifier.py` has `_MARRIED_CHECK_HUBS` for CX and QR
- `rtw/rules/married.py` has `_HUB_CARRIERS` but only CX — **QR needs adding**
- POS is hardcoded to "USA (Default)" at `expertflyer.py:295`

### Recommended Enhancements

1. **Hub transit warnings**: When a segment routes through CX/HKG or QR/DOH, add: "O&D control active — availability may only be bookable with onward connection. Verify with agent."

2. **Dual EF query**: For hub transit segments, run BOTH standalone (LAX→HKG) and the full connection (LAX→next city via HKG). Flag discrepancies.

3. **Add QR to `_HUB_CARRIERS`** in married.py

4. **POS configuration**: Make configurable; default based on itinerary origin country

5. **Booking script enhancement**: When generating phone scripts for agents, flag hub transits with: "Present as connected routing (LAX-CTU via HKG), not standalone LAX-HKG"

---

## Source Threads

- [AA RTW Desk Availability vs ExpertFlyer](https://www.flyertalk.com/forum/oneworld/2152207-aa-rtw-desk-availability-compared-expertflyer-ow-online-booking-tool.html)
- [ExpertFlyer vs BA](https://www.flyertalk.com/forum/oneworld/2213364-expertflyer-vs-ba.html)
- [Booking & Pricing Experiences p182](https://www.flyertalk.com/forum/oneworld/1776577-oneworld-booking-pricing-experiences-182.html)
- [Issues with Married Segment Control (Finnair)](https://www.flyertalk.com/forum/finnair-finnair-plus/1888592-issues-married-segment-control-oneworld-award.html)
- [Sage Advice for Getting Award Space on Married Segments](https://www.flyertalk.com/forum/united-mileage-plus-pre-merger/1189269-sage-advice-getting-award-space-married-segments.html)
- [OW Explorer FAQs p174](https://www.flyertalk.com/forum/oneworld/338667-oneworld-explorer-ticket-faqs-174.html)
- [OW Explorer User Guide p46](https://www.flyertalk.com/forum/oneworld/2008084-oneworld-explorer-user-guide-46.html)
- [Amadeus: Breaking Married Segments](https://www.flyertalk.com/forum/online-travel-booking-bidding-agencies/1885075-amadeus-breaking-married-segments-can-t-broken-using-xe.html)
- [Is ExpertFlyer Going Downhill?](https://www.flyertalk.com/forum/oneworld/2180862-expertflyer-going-downhill-am-i-doing-something-wrong.html)

## Academic / Technical Sources

- MIT research on O&D revenue management
- PMC/NIH O&D management study (Zero Displacement Cost model)
- EDIFACT AVLREQ specification (ODI/TVL/CNX segments)
- Amadeus availability source documentation (AVS/polling/calculator/seamless)
- PROS Revenue Management Suite documentation
- Sabre product dictionary (seamless availability)
