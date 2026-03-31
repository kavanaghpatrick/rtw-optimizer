# KB: Codeshare Strategies for oneworld Explorer RTW Tickets

Source: 6-agent research team (FlyerTalk scraping + web research + EF testing)
Scraped: 2026-03-30

---

## Summary

Codeshare flight numbers can affect D-class availability and YQ surcharges on RTW tickets, but they do NOT reliably bypass operating carrier O&D controls. The biggest value is in **YQ optimization** (marketing carrier determines surcharge) rather than availability bypass.

---

## 1. Key Finding: Marketing Carrier Determines YQ

The ATPCO S1 record is filed by the **marketing carrier**. On an RTW ticket:

- AA8888 (operated by BA LHR→SEA): You pay **AA's YQ** (~$80)
- BA53 (same flight, BA code): You pay **BA's YQ** (~£500-700)

**Same seat, same plane, ~£500 difference in surcharges.**

### Real Savings Documented

| Segment | Original Code | Codeshare Code | Saving |
|---------|--------------|----------------|--------|
| DFW→SYD | QF8 | AA codeshare | **EUR 1,156** |
| JNB→JFK | BA code | AA code | **~$320** |
| DFW→HNL | AA direct | QF codeshare | **~$100** (fuel surcharge avoided) |

### Plating Carrier Layer

| Plating Carrier | Surcharge Collection | Best For |
|----------------|---------------------|----------|
| **AA** | Only collects AA surcharges | Minimizing YQ |
| **QR** | Collects selectively | Cheapest overall via agent |
| **BA** | Collects from everyone | Worst for YQ |
| **QF** | Collects from everyone | **AVOID** |

---

## 2. Codeshare Does NOT Reliably Bypass O&D Control

### The Technical Reality

Most oneworld codeshares use **free-flow** (real-time dynamic) inventory, not block-space. The operating carrier's RM system has final say:

1. GDS sends booking request to operating carrier's host
2. Operating carrier evaluates against its O&D bid prices
3. Operating carrier accepts or rejects
4. Marketing carrier cannot override

**Source**: Sabre patent EP2605197A1 — "final availability = minimum of both carriers' assessments"

### When Codeshare DOES Help

| Scenario | Why It Works |
|----------|-------------|
| QF code on AA domestic | Block-space arrangement — QF has independent allocation |
| Class mapping difference | Marketing carrier's D maps to different operating carrier bucket |
| POS difference | Different carrier code triggers different POS evaluation |

### When It Doesn't

| Scenario | Why |
|----------|-----|
| AA code on JAL | JL blocks all A/D for AA RTW regardless of code |
| AA code on CX at HKG | CX O&D control applies to free-sale codeshares |
| Generic codeshare swap | Operating carrier still makes the decision |

---

## 3. ExpertFlyer and Codeshares

### What EF Shows

Our EF test (LAX→HKG, Oct 15 2026):
- **CX-coded**: D9 on nonstops
- **AA-coded**: D7 on nonstops (same physical flights)

EF format: `IB ( BA ) 3524` — marketing carrier, then operating carrier in parentheses.

### What Our Parser Misses

**Critical gap**: Our scraper at `expertflyer.py:485` does NOT detect the `MARKETING ( OPERATING )` pattern. We only capture the marketing carrier. From our own test fixtures:
- BA 31 LHR→HKG: **D5**
- IB 3524 (same flight): **D3**

We're missing this data entirely.

### Recommended Parser Enhancement

Add `operating_carrier` and `is_codeshare` fields to `FlightAvailability`. Detect the `XX ( YY )` pattern in EF results.

---

## 4. D-Class Allocation by Codeshare Partner

### BA-operated LHR→SEA (EF test, Oct 2026)

| Marketing Code | D-class | Notes |
|---------------|---------|-------|
| BA (own) | D9 | Full allocation |
| QR | D9 | JBA partner — full access |
| AY | D9 | JBA partner — full access |
| AA | D7 | Good but not full |
| IB | D5 | IAG sister — less generous |
| QF | D0 | Nothing |

### CX-operated LAX→HKG (EF test, Oct 2026)

| Marketing Code | D-class | Notes |
|---------------|---------|-------|
| CX (own) | D9 | Full allocation |
| QF | D9 | Deep SWP partnership |
| BA | D9 | JBA |
| QR | D9 | JBA |
| JL | D9 | Strong partner |
| AA | D7 | Good but consistently 2 less |

**Key insight**: AA consistently gets D7 while JBA partners get D9. The 2-seat difference suggests AA has a capped allocation.

---

## 5. Codeshare Success Stories (from FlyerTalk)

1. **LAX→ORD on QF code** (AA-operated): Couldn't get D on AA number, worked on QF codeshare — same physical flight
2. **BKK→HND on JAL**: AA codeshare showed A-class, used as proxy to confirm AA desk could book it
3. **DONE3 with 9/16 codeshare segments**: "QF codes on every sector where bookable in D, AA codes on transpac (JL), transatl (QR), and intra-Asia (CX)"
4. **DFW→HNL on QF/AA codeshare**: Avoided $100 fuel surcharge
5. **LHR→DXB as AA code** (BA-operated): Worked, but DXB→LHR failed due to traffic restriction

### Failures
- **HND→DFW**: D-class on EF but AA desk couldn't book under any code
- **DXB→LHR as AA code**: Traffic restriction — AA doesn't have rights for standalone DXB→LHR
- **MH agents**: Refused to book codeshares entirely
- **ITM→HND booked as BA**: Auto-corrected to JL at ticketing

---

## 6. Codeshare Gotchas

1. **Traffic restrictions**: Some codeshare pairs only work with onward connections to the marketing carrier
2. **YQ can increase**: AA code on CX flight may trigger AA's own YQ instead of CX's lower surcharge
3. **Code auto-correction at ticketing**: BA code may flip to operating carrier during ticket issuance
4. **Mileage credit varies**: Same L-class BA flight earns 25% QF under BA code but 100% under QF codeshare
5. **Married segment carrythrough**: Operating carrier's MSC rules apply to codeshare bookings
6. **AA desk doesn't systematically try codeshares**: They search by route/city pair, not by carrier code

---

## 7. Practical Strategy

### For YQ Optimization (High Value)
1. Check if high-YQ segment (BA, QF long-haul) has an AA codeshare
2. Book under AA code to pay AA's lower surcharges
3. Verify with agent that the codeshare is bookable on RTW

### For Availability (Lower Reliability)
1. If operating carrier blocks D standalone, try codeshare codes
2. Use AA codeshare availability as a **proxy indicator** that AA desk can book
3. Don't rely on this as a systematic bypass

### Best Codeshare Pairs for RTW

| Route Type | Best Codeshare Strategy |
|-----------|----------------------|
| BA long-haul ex-LHR | **AA code** — saves £500+ in YQ |
| QF transpacific | **AA code** — saves EUR 1,100+ in YQ |
| CX via HKG | Try QF/BA/JL code — may get D9 vs AA's D7 |
| QR via DOH | BA code — deepest JBA |
| AA domestic | Try QF code — block-space may show different availability |

---

## Source Reports

- `/tmp/ft_codeshare_research.md` — Original research (301 lines)
- `/tmp/ft_codeshare_success.md` — Success stories (232 lines)
- `/tmp/ft_codeshare_rm_technical.md` — RM technical deep dive (365 lines)
- `/tmp/ft_codeshare_mechanics.md` — Inventory mechanics
- `/tmp/ft_codeshare_mapping.md` — EF mapping and parser gaps
- `/tmp/ft_codeshare_yq.md` — YQ surcharge impact
