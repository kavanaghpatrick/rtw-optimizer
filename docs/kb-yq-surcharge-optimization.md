# YQ/YR Surcharge Optimization — oneworld Explorer RTW Tickets

Knowledge base for minimizing carrier-imposed surcharges (YQ/YR) on oneworld Explorer round-the-world tickets. Compiled from FlyerTalk threads (#2107664, #2126962, #1776577, #2130008), real booking data, and cross-referenced with `rtw/data/surcharges.yaml` and `rtw/data/carriers.yaml`.

Last updated: 2026-03-30

---

## 1. Carrier YQ Surcharge Hierarchy

Carrier-imposed surcharges (YQ/YR) are the single largest variable cost on RTW tickets after the base fare. The operating carrier on each segment determines the surcharge, but the plating (issuing) carrier affects how those surcharges are calculated across the entire ticket.

### Per-Segment YQ Estimates (USD)

| Tier | Carrier | YQ/Segment | Notes |
|------|---------|-----------|-------|
| **Very Low** | AY (Finnair) | ~$10 | Historically zero; small amounts recently |
| **Very Low** | JL (Japan Airlines) | ~$12 | Consistently lowest among major carriers |
| **Very Low** | FJ (Fiji Airways) | ~$20 | New oneworld member (April 2025) |
| **Low** | AS (Alaska Airlines) | ~$40 | Erratic D-class availability |
| **Low** | AA (American Airlines) | ~$50 | Only charges on own marketed long-haul; zero on US domestic |
| **Low** | UL (SriLankan Airlines) | ~$50 | Modest surcharges |
| **Low** | MH (Malaysia Airlines) | ~$60 | Second cheapest plating option |
| **Low** | WY (Oman Air) | ~$90 | Joined oneworld June 2025 |
| **Medium** | AT (Royal Air Maroc) | ~$100 | Limited network |
| **Medium** | QR (Qatar Airways) | ~$150 | Non-linear structure (see Section 3) |
| **Medium** | RJ (Royal Jordanian) | ~$170 | Moderate but small network |
| **Medium** | CX (Cathay Pacific) | ~$200 | Good service offsets moderate YQ |
| **High** | IB (Iberia) | ~$220 | High for European carrier |
| **Very High** | BA (British Airways) | ~$321 | Plus UK APD if departing UK |
| **Very High** | QF (Qantas) | ~$334 | Highest in the alliance |

*Sources: pandaperth comparison (ex-LHR), dutch_122 (ex-OSL), carriers.yaml*

### The 10x Rule

The cheapest carrier (AY at ~$10/segment) charges roughly **one-thirtieth** of the most expensive (QF at ~$334/segment). On a 16-segment itinerary, this difference can exceed $5,000 in surcharges alone. Even replacing 2-3 high-YQ segments with low-YQ alternatives can save $500-900.

---

## 2. The QF Surcharge Trap

Qantas carries the highest per-segment surcharges in the oneworld alliance and is the most frequently cited YQ trap on FlyerTalk.

### The Classic Example

A QF-operated DFW-SYD sector on a DONE4 ticket can add approximately **EUR 1,240** (~$1,350 USD) in carrier-imposed surcharges for a single segment. This is because QF applies hefty YQ on its ultra-long-haul routes, and the surcharge scales with route distance on QF metal.

### The AA Metal Alternative

The same DFW-SYD route is also operated by American Airlines (AA codeshare). Switching from QF metal to AA metal on this sector reportedly saved approximately **$1,160** in surcharges on a real DONE4 ticket. AA charges substantially lower YQ on its own operated flights, even on identical city pairs.

### How to Avoid the QF Trap

| Instead of | Use | Savings (approx.) |
|-----------|-----|-------------------|
| QF DFW-SYD | AA DFW-SYD | ~$1,160 |
| QF SYD-LAX | AA SYD-LAX or FJ NAN-LAX | ~$800-1,000 |
| QF MEL-SIN | MH KUL-SIN + positioning | ~$600-800 |
| QF SYD-HKG | CX HKG-SYD (reverse) | ~$100-200 |
| QF domestic (SYD-MEL) | JL codeshare if available | ~$300+ |

### Additional QF Problems

- QF is "notoriously stingy" with D-class availability -- over 30 J seats on 787 but D rarely released
- QF agents "don't understand RTW" and have reportedly cancelled reservations mid-call
- The oneworld online booking tool defaults to QF ticketing for ex-Europe bookings -- always override this
- QF plating applies QF-level surcharges across the entire ticket, not just QF-operated segments

---

## 3. BA Surcharge Levels by Route

British Airways has the second-highest per-segment surcharges, compounded by UK Air Passenger Duty (APD) when departing from the UK.

### BA YQ by Route Type

| Route Type | Example | Approx. YQ | Notes |
|-----------|---------|-----------|-------|
| UK long-haul | LHR-JFK | ~$321 + APD | APD adds GBP 244-253 in premium cabin |
| UK short-haul | LHR-CDG | ~$150-200 | Lower but still significant |
| Partner metal | BA-marketed, QR-operated | Varies | Marketing carrier matters |
| I-class (award) | LHR-NRT | ~$600-800 one-way | Club World awards carry extreme YQ |

### UK APD Tax (Effective April 2026)

| Band | Premium Cabin (J/F) |
|------|-------------------|
| Domestic | GBP 16 |
| Band A (0-2,000mi) | GBP 32 |
| Band B (2,001-5,500mi) | **GBP 244** |
| Band C (5,501+mi) | **GBP 253** |

APD triggers per UK departure where the passenger has been on the ground 24+ hours. Connections under 24 hours are transit-exempt.

### BA Avoidance Strategies

1. **Fly INTO the UK, depart from elsewhere** -- zero charges to land, significant charges to leave
2. **Use Finnair (AY) for Europe-Asia instead of BA** -- AY charges ~$10 vs BA's ~$321
3. **Route through non-UK European gateways** -- MAD, CDG, HEL all avoid APD
4. **Never let BA plate your RTW ticket** -- BA plating = highest total YQ + email-only changes with weeks of delays
5. **Scottish Highlands exemption** -- Inverness (INV) departures are fully APD-exempt

---

## 4. CX, QR, JL, MH Surcharge Profiles

### Qatar Airways (QR) -- Non-Linear Structure

QR has a unique YQ structure that differs from other carriers:

- **Flat charge on the first QR segment** (the bulk of QR's surcharge)
- **Small incremental amounts for each additional QR segment** (diminishing cost per segment)
- Adding more QR-coded segments has decreasing marginal YQ cost
- Breaking a single long QR segment into two shorter ones (adding a DOH stopover) can reduce total QR YQ

**Practical impact**: On an itinerary with 3 QR segments, the first might add ~$150, the second ~$40-60, and the third ~$20-30. Total: ~$210-240, not 3 x $150 = $450.

**QR plating advantage**: QR as the plating carrier produces the cheapest total ticket taxes on identical routings. Dutch_122 documented QR plating at EUR 1,985 vs AA/BA at EUR 3,258 on the same DONE4 routing ex-OSL -- a saving of EUR 1,273 (~$1,390).

**QR plating disadvantage**: QR has no RTW desk. Cannot book directly. Must use a travel agent who can issue on QR 157 ticket stock.

### Japan Airlines (JL) -- The Gold Standard

- Consistently ~$12 per segment across all route types
- Best YQ value for Pacific crossings (NRT-SFO, NRT-LAX)
- D-class availability is scarce but when available, JL offers the best YQ/value combination
- **JL is NOT on ExpertFlyer** -- use JAL website, AwardFares, or seats.aero to check D-class
- Stingy with D-class: typically 2 seats per long-haul flight, released exactly 360 days out

### Cathay Pacific (CX) -- Moderate, Steady

- ~$200 per segment, consistent across routes
- Good D-class availability on A350 routes
- Severe married segment control -- only works reliably if HKG is a stopover (not transit)
- ExpertFlyer may show D5 but CX can refuse to confirm in the booking system

### Malaysia Airlines (MH) -- Low-Cost Plating Option

- ~$60 per segment on own metal
- Second cheapest plating carrier after QR (total YQ ~$900 on typical 16-segment DONE4)
- Limited RTW booking experience at their desk
- Good for KUL hub connectivity to Asia, SWP, and Middle East

### Finnair (AY) -- The Hidden Gem

- ~$10 per segment, almost nothing
- Excellent for Europe-Asia routing via HEL
- **CAUTION**: AY Japan JV surcharges on HEL-NRT are $270-480 extra (joint venture pricing)
- Use AY for HEL-HKG, HEL-BKK, HEL-SIN. Use JL for NRT/HND connections instead

---

## 5. Codeshare vs Marketing Carrier -- How It Affects YQ

### The Core Rule

On oneworld Explorer RTW tickets, the **marketing carrier** (the 2-letter code on your ticket) determines the YQ charged, not the operating carrier that actually flies the plane.

### Key Implications

| Physical Flight | Marketing Carrier | YQ Impact |
|----------------|-------------------|-----------|
| AA-operated DFW-SYD | AA code | ~$50 YQ |
| AA-operated DFW-SYD | QF code | ~$334 YQ |
| QR-operated DOH-SIN | QR code | ~$150 YQ |
| QR-operated DOH-SIN | BA code | ~$321 YQ |
| JL-operated NRT-SFO | JL code | ~$12 YQ |
| JL-operated NRT-SFO | AA code | ~$50 YQ |
| AY-operated HEL-HKG | AY code | ~$10 YQ |

### Codeshare NTP vs YQ Trade-off

The same physical flight under different carrier codes earns dramatically different NTP (tier points) AND has different YQ:

- KUL-NRT under **MH code**: 30 Qpoints / ~$60 YQ
- KUL-NRT under **QR code**: 81 Qpoints / ~$150 YQ

Higher NTP-earning codes (QR at 50% distance, JL at 50% distance) sometimes carry higher YQ than low-NTP codes (MH at 25% distance). Decide whether NTP or YQ savings matter more for your goals.

### How to Request Specific Codeshares

When booking through the AA RTW desk:
1. Specify the exact flight number with the desired carrier code
2. Ask "Can this segment be booked under [carrier] code?"
3. If the desired codeshare is unavailable, ask about alternatives on the same physical flight
4. Note that AA desk may not accommodate all codeshare preferences on RTW tickets

---

## 6. Carrier Substitution Strategies by Route

### Transatlantic

| Priority | Carrier | YQ/seg | Route Examples |
|----------|---------|--------|---------------|
| 1st | AA | ~$50 | JFK-LHR, MIA-LHR, DFW-LHR |
| 2nd | AY | ~$10 | JFK-HEL (or via HEL to anywhere in EU) |
| 3rd | IB | ~$220 | JFK-MAD, MIA-MAD |
| **Avoid** | BA | ~$321 + APD | Any LHR departure |

### Transpacific

| Priority | Carrier | YQ/seg | Route Examples |
|----------|---------|--------|---------------|
| 1st | JL | ~$12 | NRT-SFO, NRT-LAX (2 seats, book 360d out) |
| 2nd | AA | ~$50 | LAX-NRT, DFW-NRT, LAX-SYD |
| 3rd | FJ | ~$20 | NAN-SFO, NAN-LAX (A350, good availability) |
| **Avoid** | QF | ~$334 | SYD-LAX, SYD-DFW, MEL-LAX |

### Europe to Asia

| Priority | Carrier | YQ/seg | Route Examples |
|----------|---------|--------|---------------|
| 1st | AY | ~$10 | HEL-HKG, HEL-SIN, HEL-BKK |
| 2nd | QR | ~$150 | DOH-NRT, DOH-SIN, DOH-HKG |
| **Avoid** | AY JV | ~$270-480 | HEL-NRT (JV surcharges apply) |
| **Avoid** | BA | ~$321 | LHR-HKG, LHR-NRT |

### Intra-Asia

| Priority | Carrier | YQ/seg | Route Examples |
|----------|---------|--------|---------------|
| 1st | JL | ~$12 | NRT-HKG, NRT-SIN, NRT-BKK |
| 2nd | MH | ~$60 | KUL-NRT, KUL-HKG |
| 3rd | CX | ~$200 | HKG-anything (only with HKG stopover) |

### US Domestic

| Priority | Carrier | YQ/seg | Notes |
|----------|---------|--------|-------|
| 1st | AA | **$0** | Zero YQ on AA domestic US segments |
| 2nd | AS | ~$40 | Best from SEA hub |
| Rule | -- | -- | Only 1 nonstop transcontinental allowed |

---

## 7. Specialist Agent Approaches to Surcharge Minimization

### Daniel/DK at Propeller Travel

Daniel at Propeller Travel (UK-based, GBP 80 for RTW ticketing) is frequently cited on FlyerTalk for YQ optimization. His approach includes:

1. **Origin arbitrage**: Booking ex-Oslo, ex-Brussels, or ex-Dublin for UK-based customers, saving GBP 2,000-3,000 in base fare + APD compared to ex-LHR
2. **Plating carrier selection**: Using QR or MH ticket stock via Amadeus GDS to minimize total surcharges
3. **Carrier substitution on high-YQ routes**: Replacing QF and BA segments with AA, JL, or AY alternatives on the same city pairs
4. **Post-departure fare lock**: Advising clients to fly the first segment immediately to lock the base fare, then make routing changes ($125 fee) that improve YQ

**The BA revocation incident** (2015): Daniel's ex-EU booking volume grew 300-400% after blog publicity, triggering BA to revoke his BA plating rights, alleging "ticketing from fictitious points of origin." He lost GBP 68,000 over 6 weeks. Service was eventually restored under a new agency agreement. This illustrates the airline sensitivity to systematic surcharge avoidance.

### dutch_122 and e-Businesstravel Netherlands

FlyerTalk user dutch_122 documented detailed price comparisons and booked through a Dutch travel agent (e-Businesstravel, EUR 75 fee) who:

1. Issued 7 QR-plated RTW tickets in a single month
2. Achieved EUR 1,273 savings per ticket vs AA/BA plating on identical DONE4 routings
3. Provided after-hours Amadeus GDS access (EUR 25-50 per call)

### Key Agent Techniques

| Technique | How It Works | Savings |
|-----------|-------------|---------|
| QR plating via TA | Agent issues on QR 157 ticket stock | EUR 800-1,273 per ticket |
| MH plating via TA | Agent issues on MH 232 ticket stock | EUR 700-1,100 per ticket |
| Carrier code swaps | Request AA code on QF-operated flights | $200-1,000+ per segment |
| First-segment lock | Fly segment 1 to freeze base fare | Protects against fare increases |
| Consolidated changes | Bundle all routing changes into one call | $125 per event vs per change |
| POS manipulation | Different Point of Sale reveals different inventory | Access to D-class otherwise hidden |

---

## 8. Tax Breakdown Examples from Real Tickets

### DONE4 ex-OSL -- Plating Carrier Comparison

Same routing, different plating carrier (source: dutch_122 on FlyerTalk):

| Component | QR Plating | CX Plating | AA/BA Plating |
|-----------|-----------|-----------|--------------|
| Base fare (DONE4) | EUR 5,392 | EUR 5,392 | EUR 5,392 |
| Carrier surcharges (YQ/YR) | ~EUR 600 | ~EUR 1,750 | ~EUR 1,850 |
| Airport taxes | ~EUR 385 | ~EUR 400 | ~EUR 408 |
| Departure taxes | ~EUR 100 | ~EUR 100 | ~EUR 100 |
| Government fees | ~EUR 900 | ~EUR 900 | ~EUR 900 |
| **Total taxes/fees** | **EUR 1,985** | **EUR 3,150** | **EUR 3,258** |
| **Grand total** | **EUR 7,377** | **EUR 8,542** | **EUR 8,650** |
| **Savings vs AA/BA** | **EUR 1,273** | **EUR 108** | Baseline |

### DONE4 ex-LHR -- The APD Penalty

| Component | ex-LHR | ex-OSL | Difference |
|-----------|--------|--------|-----------|
| Base fare | ~$8,000 | ~$5,400 | $2,600 |
| UK APD (premium long-haul departure) | ~$330 | $0 | $330 |
| Norwegian departure tax | $0 | ~$9 | -$9 |
| Carrier surcharges (typical AA plating) | ~$1,800 | ~$1,800 | $0 |
| **Total per person** | **~$10,130** | **~$7,209** | **~$2,921** |

### Typical Tax Components on RTW Tickets

| Tax Code | Description | Typical Amount |
|----------|------------|----------------|
| YQ | Carrier fuel/insurance surcharge | $10-334 per segment |
| YR | Carrier service surcharge | $0-50 per segment |
| GB | UK APD | GBP 32-253 per UK departure |
| US | US departure tax | ~$40 |
| AY | US arrival tax | ~$7 |
| XA | US APHIS fee | ~$3.96 |
| XY | US immigration fee | ~$7 |
| YC | US customs fee | ~$6.50 |
| NO | Norwegian departure tax | NOK 88-110 (~$9) |
| QZ | Japan passenger service | ~JPY 2,610 |
| SW | Japan security | ~JPY 100 |
| OI | Australia departure tax | ~AUD 60 |
| HK | Hong Kong departure tax | ~HKD 120 |
| SG | Singapore passenger service | ~SGD 50 |

---

## 9. Ticketing Airline and Surcharge Calculation

### How It Works

The "plating carrier" or "validating carrier" is the airline whose ticket stock is used to issue the e-ticket. This is NOT necessarily the airline you fly on -- it is the airline that "owns" the ticket in the GDS.

### Plating Carrier Impact on Total Cost

| Plating Carrier | Typical Total YQ (16-seg DONE4) | Flexibility | RTW Desk? |
|----------------|-------------------------------|-------------|-----------|
| **QR (Qatar)** | ~$800 | Low (no desk, need TA) | No |
| **MH (Malaysia)** | ~$900 | Low (limited RTW experience) | Limited |
| **CX (Cathay)** | ~$1,500 | Medium | Yes |
| **AA (American)** | ~$1,800 | **High** (gold standard desk) | **Yes** |
| **BA (British)** | ~$2,500 | **Very Low** (email-only, weeks of delays) | Barely |

### The Flexibility vs Cost Trade-off

- **AA plating**: Best customer service for mid-trip changes. AA RTW desk (+1-800-247-3247) is experienced, phone-accessible, and can handle complex modifications. Costs ~$1,000 more in YQ than QR plating.
- **QR plating**: Cheapest surcharges but QR has no RTW desk. All changes must go through the travel agent. If your TA is unavailable during a disruption at 2 AM in Fiji, you are stranded.
- **Recommendation**: For simple itineraries with low change likelihood, QR plating saves money. For complex itineraries (16 segments, multiple carrier changes likely), AA plating is worth the premium.

### AA as Plating Carrier -- Special Advantage

AA charges YQ **only on its own marketed long-haul segments**. Partner segments carry NO additional AA-imposed YQ. This means:

- QR, CX, FJ, JL, AY, and RJ segments = their own YQ only (no AA markup)
- AA domestic US segments = **zero YQ**
- Only AA-marketed international segments add AA's ~$50/segment YQ

### GDS Differences Affect Plating Options

| GDS | Plating Options | Segment Limit | Notes |
|-----|----------------|---------------|-------|
| Sabre (AA) | AA, AS | 16 (machine-print) | Best for AA plating |
| Amadeus (BA/CX/QR) | BA, CX, QR, MH, IB | 20 (CX can print) | Required for QR plating |

Travel agents with Amadeus access can plate on QR/MH. AA's own Sabre system cannot issue QR-plated tickets.

---

## 10. DGLOB vs DONE -- When Distance-Based Fares Win

### What Is DGLOB?

DGLOB (also written DGLOB34) is the **distance-based** oneworld RTW fare (Global Explorer), compared to DONE which is the **continent-based** fare (oneworld Explorer). Key differences:

| Feature | DONE (oneworld Explorer) | DGLOB (Global Explorer) |
|---------|------------------------|------------------------|
| Pricing basis | Number of continents (3-6) | Total mileage (up to 34,000nm) |
| Mileage cap | **None** | 34,000nm maximum |
| Segment limit | 16 | 16 |
| Base fare | Fixed by continent count | Scales with distance |
| Per-continent limits | 4 segments (6 in NA) | Different structure |

### When DGLOB Is Cheaper

DGLOB tends to be cheaper when:

1. **Short total routing** -- If your RTW is well under 34,000nm, the distance-based fare may undercut the continent-based fare
2. **Many continents, short distances** -- DONE5/DONE6 prices jump significantly per additional continent. DGLOB charges by miles regardless of continent count
3. **Specific origins** -- DGLOB pricing from certain origins (particularly ex-US) can be competitive with DONE for compact routings

### When DONE Is Cheaper

DONE tends to be cheaper when:

1. **High-mileage routings** -- Any itinerary approaching or exceeding 34,000nm cannot use DGLOB at all. DONE has no mileage cap
2. **4 continents or fewer** -- DONE3 and DONE4 are often cheaper than equivalent DGLOB mileage charges
3. **Cheap origins** -- Ex-CAI, ex-OSL, ex-JNB DONE4 fares are hard to beat on any fare basis
4. **Segment-heavy routings** -- Maximizing 16 segments with long routes favors DONE

### Surcharge Differences

The surcharge calculation methodology can differ between DONE and DGLOB:

- DONE surcharges are calculated per segment based on operating/marketing carrier
- DGLOB may have different surcharge structures in some GDS filings
- **The plating carrier effect is the same** -- QR plating saves on both DONE and DGLOB
- In practice, most FlyerTalk reports indicate similar YQ levels for identical routings regardless of DONE vs DGLOB fare basis

### Decision Framework

```
IF total_routing_miles > 30,000nm:
    USE DONE (DGLOB has 34,000nm cap, no margin for changes)

IF continents <= 3 AND total_miles < 25,000nm:
    COMPARE DONE3 vs DGLOB (DGLOB may win)

IF continents == 4 AND total_miles < 28,000nm:
    COMPARE DONE4 vs DGLOB (usually DONE4 wins from cheap origins)

IF continents >= 5:
    COMPARE DONE5+ vs DGLOB (DGLOB competitive if miles are low)

DEFAULT:
    Price both through AA RTW desk and compare
```

### Real-World Guidance

Most experienced FlyerTalk RTW travelers prefer DONE (oneworld Explorer) because:

1. No mileage cap gives flexibility for routing changes without repricing risk
2. Date changes remain free after first flight (same as DGLOB)
3. The base fare from cheap origins (CAI, OSL, JNB) is extremely competitive
4. Eliminating the mileage constraint simplifies planning enormously

**Always ask the AA RTW desk to price both** -- they can compare in seconds. The online tool may not offer DGLOB pricing.

---

## 11. Quick Reference: YQ Optimization Checklist

### Before Booking

- [ ] Compare total cost with at least 2 plating carriers (AA vs QR)
- [ ] Identify all QF and BA segments -- these are your highest YQ exposure
- [ ] For each QF/BA segment, check if AA, JL, AY, or MH serve the same city pair
- [ ] Calculate APD exposure -- any UK departure with 24h+ ground time triggers APD
- [ ] Consider origin city: OSL saves ~$2,900 vs LHR; CAI saves ~$6,000 vs JFK
- [ ] Ask AA desk to price DONE vs DGLOB for your specific routing

### During Booking

- [ ] Specify marketing carrier codes on each segment (not just "any carrier")
- [ ] Confirm zero YQ on AA domestic US segments
- [ ] For QR segments, understand the non-linear YQ structure (first segment = bulk of charge)
- [ ] Avoid AY on HEL-NRT (JV surcharges $270-480); use JL for Japan instead
- [ ] Request QR or MH plating through TA if cost minimization is the priority

### After Booking

- [ ] Verify marketing carrier codes within 24 hours (AA system may auto-change)
- [ ] If fare-locked (first segment flown), consider routing changes that improve YQ
- [ ] Monitor for schedule changes that might offer free rerouting opportunities

---

## 12. Impact Modeling

### Scenario: 16-Segment DONE4 ex-OSL

**Worst case (all high-YQ carriers, BA plating):**

| Segments | Carrier Mix | Total YQ |
|----------|-----------|----------|
| 4x BA | $321 x 4 = $1,284 | |
| 4x QF | $334 x 4 = $1,336 | |
| 4x IB | $220 x 4 = $880 | |
| 4x CX | $200 x 4 = $800 | |
| **Total** | | **~$4,300** |

**Optimized (low-YQ carriers, QR plating):**

| Segments | Carrier Mix | Total YQ |
|----------|-----------|----------|
| 4x JL | $12 x 4 = $48 | |
| 4x AY | $10 x 4 = $40 | |
| 4x AA | $50 x 4 = $200 | |
| 2x QR | ~$190 (non-linear) | |
| 2x FJ | $20 x 2 = $40 | |
| **Total** | | **~$518** |

**Savings: ~$3,782 per person** by optimizing carrier mix and plating.

For 2 passengers: **~$7,564 saved**.

---

## Sources

### FlyerTalk Threads

| Thread | ID | Content |
|--------|-----|---------|
| Carrier Imposed Fees DONE4 ex OSL | #2107664 | YQ comparison by carrier, plating options |
| RTW Price Hike | #2126962 | Fare increases, surcharge changes |
| oneworld Booking/Pricing Experiences | #1776577 (pp. 82-106) | Real booking data, tax breakdowns |
| DGLOB34 vs DONE4 | #2130008 | Distance vs continent fare comparison |
| oneworld Explorer User Guide | #2008084 (60 pages) | Comprehensive RTW guide |
| Fuel Surcharge Differences | #919981 | Historical YQ data |

### Project Data Files

| File | Content |
|------|---------|
| `rtw/data/surcharges.yaml` | Per-carrier YQ estimates, plating comparison |
| `rtw/data/carriers.yaml` | Carrier reference with yq_estimate_per_segment |
| `rtw/data/fares.yaml` | Base fares by origin city |
| `12-rtw-optimization-guide.md` | Full optimization guide with YQ sections |
| `docs/segment-bank-strategy.md` | Carrier strategy by route type |
| `docs/flyertalk-research-2026-03-30.md` | APD, Oslo pricing, ExpertFlyer data |
