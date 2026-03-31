# Oslo Origin Strategy for oneworld Explorer RTW Tickets

Knowledge base compiled from FlyerTalk threads, fare filings, and project data. Covers why Oslo is the optimal European origin, how to execute the strategy, and comparison with alternatives.

Sources: FlyerTalk threads #2133996 (cheapest Europe fares), #2107664 (carrier fees DONE4 ex-OSL), #2176618 (ex-OSL DONE4 help), #936102 (cheapest country to start), #1637682 (currency movements); project files `fares.yaml`, `surcharges.yaml`, `carriers.yaml`, `segment-bank-strategy.md`, `flyertalk-research-2026-03-30.md`, `12-rtw-optimization-guide.md`.

---

## 1. Complete Origin City Pricing Comparison

### DONE4 (Business, 4 Continents) Base Fare

| Rank | Origin | DONE4 (USD) | Currency Filed | Notes |
|------|--------|-------------|----------------|-------|
| 1 | **CAI (Cairo)** | $4,000 | EGP | Cheapest globally. EGP devaluation advantage. Impractical positioning for UK-based. |
| 2 | **JNB (Johannesburg)** | $5,000 | ZAR | ZAR weakness. Good if Africa is on route. |
| 3 | **CMB (Colombo)** | $5,200 | LKR | SriLankan is oneworld. Occasionally cheap. |
| 4 | **KTM (Kathmandu)** | ~$5,344 | NPR | No oneworld carriers serve KTM; difficult positioning. |
| 5 | **KHI (Karachi)** | ~$5,360 | PKR | PIA not oneworld; difficult positioning. |
| 6 | **OSL (Oslo)** | $5,400 | NOK | Best balance of price + accessibility from UK/Europe. |
| 7 | **DEL (Delhi)** | ~$5,543 | INR | Good QR connectivity. |
| 8 | **CPT (Cape Town)** | ~$5,585 | ZAR | ZAR advantage, moderate positioning. |
| 9 | **ARN (Stockholm)** | ~$6,177 | SEK | ~$400 more than Oslo. |
| 10 | **BUD (Budapest)** | ~$6,457 | HUF | |
| 11 | **NRT (Tokyo)** | $6,360 | JPY | Higher taxes/YQ. Weak JPY helps. |
| 12 | **LHR (London)** | $8,000 | GBP | High base fare + APD penalty. |
| 13 | **SYD (Sydney)** | $8,800 | AUD | |
| 14 | **JFK (New York)** | $10,500 | USD | Most expensive conventional origin. |
| 15 | **ZRH (Zurich)** | ~$11,241 | CHF | Worst in Europe. |

### Full Fare Table (All Ticket Types, USD)

| Origin | DONE3 | DONE4 | DONE5 | DONE6 | AONE3 | AONE4 |
|--------|-------|-------|-------|-------|-------|-------|
| CAI | 3,500 | 4,000 | 4,400 | 5,500 | 5,600 | 6,400 |
| JNB | 4,000 | 5,000 | 5,700 | 6,662 | 6,400 | 8,000 |
| CMB | 4,500 | 5,200 | 6,000 | 7,000 | 7,200 | 8,300 |
| OSL | 4,800 | 5,400 | 5,800 | 6,500 | 7,700 | 8,600 |
| NRT | 5,500 | 6,360 | 7,260 | 8,500 | 8,800 | 10,200 |
| LHR | 7,000 | 8,000 | 9,000 | 10,500 | 11,200 | 12,800 |
| SYD | 7,500 | 8,800 | 10,000 | 12,000 | 12,000 | 14,100 |
| JFK | 9,000 | 10,500 | 12,000 | 14,099 | 14,400 | 16,800 |

### Oslo vs London DONE4 Savings

| Component | LHR | OSL | Saving |
|-----------|-----|-----|--------|
| Base fare | $8,000 | $5,400 | **$2,600** |
| UK APD (J-class long-haul) | ~$330 | $0 | **$330** |
| Norwegian departure tax | $0 | ~$10 | -$10 |
| **Total saving (base + tax)** | | | **~$2,920** |

For two DONE4 tickets (segment bank strategy), Oslo saves approximately **$5,840** vs London before surcharges.

---

## 2. Why Oslo Is Cheapest in Europe

### 2.1 Base Fare Filing Advantage

Oneworld Explorer fares are filed with IATA in local currencies per origin country. The IATA published fare for Norway is approximately $2,374 lower than the UK filing. This is the single largest factor -- the base fare differential accounts for roughly 80% of the total saving vs London.

The fare differential exists because:
- IATA fare filings reflect local market conditions and competitive dynamics.
- Norway is not a major hub for premium travel demand, so fares are filed lower.
- The Norwegian market has less premium-cabin demand compared to London, which is the world's largest premium air travel market.

### 2.2 No Air Passenger Duty (APD)

The UK imposes APD on departures from UK airports. From April 2026:

| Distance Band | Premium (J/F) Rate |
|---------------|--------------------|
| Band B (2,001-5,500mi) | **GBP 244** (~$330) |
| Band C (5,501+mi) | **GBP 253** (~$340) |

Norway has a minimal aviation tax of approximately NOK 88-110 (~GBP 7-9). This saves roughly GBP 235-245 per premium departure.

APD rules:
- Triggers per UK departure where passenger has been on ground 24+ hours.
- Connection under 24 hours = NO APD (transit exemption on same ticket).
- Stopover of 24+ hours = APD charged based on cabin class and distance band.

Strategy: Fly INTO the UK. Never depart from the UK on a premium long-haul segment.

### 2.3 NOK Currency Filing

**Important correction**: The project's `fares.yaml` incorrectly lists Oslo's currency as `EUR`. Oslo fares are filed in **NOK (Norwegian Krone)**, not EUR.

This matters because:
- NOK has been structurally weak against USD/GBP since 2020.
- When NOK weakens, the USD-equivalent base fare drops even if the NOK-denominated fare stays the same.
- IATA fare filings in NOK are updated periodically but lag currency movements, creating windows of opportunity.
- The same fare filing that costs $5,400 when NOK/USD = 10.5 would cost $5,100 when NOK/USD = 11.0.

### 2.4 Low Local Taxes and Fees

Norwegian airport taxes and security fees are minimal compared to UK equivalents:

| Fee Type | LHR | OSL |
|----------|-----|-----|
| Departure tax | GBP 244-253 (APD) | NOK 88-110 (~GBP 7-9) |
| Airport charge | High (Heathrow surcharges) | Moderate |
| Security fee | Included | Included |

---

## 3. Positioning Flight Strategies (London to Oslo)

### 3.1 Overview

For UK-based travelers, the positioning flight LHR/LGW/STN to OSL is a separate cash or miles ticket, **not** part of the oneworld Explorer itinerary.

### 3.2 Options

| Method | Typical Cost | Notes |
|--------|-------------|-------|
| **BA Avios** | 4,000-7,500 Avios + ~GBP 30 taxes | Best value. Short-haul reward flights. |
| **Norwegian Air** | GBP 30-80 | Budget carrier, frequent LGW-OSL service. |
| **Ryanair** | GBP 20-60 | STN-OSL Gardermoen or Torp. Cheapest cash option. |
| **SAS** | GBP 60-150 | LHR-OSL. Full service. |
| **BA cash** | GBP 80-200 | LHR-OSL. Convenient but most expensive. |

### 3.3 Positioning Cost Analysis

Even with a GBP 100 positioning flight each way (GBP 200 round trip), the total cost is:

| | LHR Origin | OSL Origin + Positioning |
|--|-----------|--------------------------|
| DONE4 base fare | $8,000 | $5,400 |
| APD/departure tax | $330 | $10 |
| Positioning (RT) | $0 | $260 (GBP 200) |
| **Total** | **$8,330** | **$5,670** |
| **Saving** | | **$2,660** |

The positioning flight pays for itself many times over.

### 3.4 Timing Considerations

- Book the positioning flight to arrive in Oslo the day before your first RTW segment.
- Oslo Gardermoen (OSL) is the airport for all oneworld Explorer segments.
- Budget airlines may fly to Oslo Torp (TRF) or Moss (RYG) -- these are 1-2 hours from central Oslo. Factor in transfer time.
- The positioning flight is a separate ticket -- if it's delayed, you have no protection for the RTW ticket. Build in a buffer day.

---

## 4. First Segment Logistics from Oslo

### 4.1 The QR First Carrier Problem

Qatar Airways **cannot** be the first carrier when booking through the oneworld online tool. This is a tool limitation, not a fare rule (see `docs/research-qr-first-carrier.md` for full analysis). QR IS listed as permitted ticket stock in Rule 3015.

Implications for Oslo: The natural routing OSL-DOH on QR cannot be the first segment when using the online booking tool. When booking via AA RTW desk or a travel agent, QR CAN be the first operating carrier if a different airline (e.g., AA) is the validating/plating carrier.

### 4.2 Popular First Segment: OSL-HEL on Finnair

The most common ex-Oslo strategy on FlyerTalk:

```
OSL → HEL (AY, ~2h) → onward connections from Helsinki
```

Why Finnair OSL-HEL works:
- **Finnair is oneworld** -- legitimate first carrier, no restrictions.
- **Ultra-low YQ**: AY charges approximately $10/segment, the lowest in the alliance.
- **Helsinki is a major hub**: Excellent connections to Asia (HEL-HKG, HEL-NRT, HEL-SIN, HEL-BKK, HEL-DEL).
- **Solves the QR problem**: AY is first carrier, then you can fly QR on segment 2+.
- **Good D-class availability**: AY guarantees 2 J seats per long-haul flight.

### 4.3 Recommended First Segment Routings

| Routing | Direction | Notes |
|---------|-----------|-------|
| **OSL-HEL (AY)** → HEL-HKG (AY) | Eastbound | Most popular. AY nonstop HEL-HKG. |
| **OSL-HEL (AY)** → HEL-NRT (AY) | Eastbound | Caution: AY HEL-NRT has JV surcharges ($270-480). Use JL for Japan instead. |
| **OSL-HEL (AY)** → HEL-DOH (QR) | Eastbound | Connect to QR network from DOH. |
| **OSL-LHR (BA)** → LHR-DFW (BA/AA) | Westbound | Position to LHR hub, then transatlantic. BA YQ is high ($321/seg). |
| **OSL-LHR (BA)** → LHR-JFK (BA/AA) | Westbound | Alternative transatlantic. |
| **OSL-MAD (IB)** → MAD-onward (IB) | Westbound | Iberia hub connections to Americas. |

### 4.4 Fare Lock Strategy

Once you fly the first segment (e.g., OSL-HEL), the base fare is permanently locked. This is critical:
- If NOK weakens further after booking, your fare stays the same (good).
- If NOK strengthens after booking but before flying, DO NOT change the first segment date (risk of repricing).
- Fly the first segment as early as possible to lock the fare.
- One FlyerTalk user reported a $6,000+ increase from changing the first segment date.

---

## 5. The "Close the Loop" Problem

### 5.1 The Requirement

Rule 3015 requires the itinerary to return to the origin city. For ex-Oslo tickets, the last segment must arrive at OSL.

### 5.2 The Challenge

Most interesting destinations are far from Oslo. Returning to Oslo "wastes" one of your 16 segments and a European stopover/transit slot on a short positioning flight back to OSL.

### 5.3 Solutions

#### Option A: Short Intra-European Return (Most Common)

End the trip with a short European hop back to Oslo:
```
... → LHR → OSL (BA or AY, ~2h)
```
or:
```
... → HEL → OSL (AY, ~2h)
```

This uses 1 segment but is only 2 hours of flying. The segment is "low value" per mile but necessary.

#### Option B: Use the Return Segment Productively

Route through a city you actually want to visit:
```
... → JFK → LHR (BA, stopover in London) → LHR → OSL (BA)
```
or:
```
... → DOH → LHR (QR, stopover in London) → LHR → ATH (BA, stopover in Athens) → ATH → HEL (AY) → HEL → OSL (AY)
```

This uses more segments but extracts value from the return journey. The eastbound segment bank itinerary in `itineraries/osl-eastbound-segment-bank.yaml` shows this pattern: JFK-LHR (stopover), LHR-ATH (transit), ATH-HEL (transit), HEL-OSL (final).

#### Option C: Drop the Last Segment (Risky)

Some travelers plan to simply not fly the final segment back to Oslo. This is:
- **Practically tolerated**: No FlyerTalk member has reported fare recalculation being enforced for skipping the final segment.
- **Theoretically risky**: The airline can recalculate on a point-to-point basis (could exceed RTW fare).
- **Luggage issue**: Bags must be offloaded if passenger no-shows. Travel carry-on only on the penultimate leg.

This is NOT recommended as a primary strategy but is a known fallback.

#### Option D: Surface Sector Before Return

If you end up in a European city that is not Oslo:
```
... → LHR (surface) OSL
```

A surface sector from London to Oslo uses one of your 16 segments but avoids flying an actual segment. You get yourself to Oslo independently (budget airline, train, etc.) and the RTW ticket records it as a surface sector.

### 5.4 Impact on Continent Limits

The return to Oslo uses EU/ME segments. Be careful with the 2-stopover limit in the origin continent:
- Maximum 2 stopovers in EU/ME (continent of origin).
- Transits (under 24 hours) do NOT count as stopovers.
- The return journey's intermediate stops should be transits, not stopovers, to preserve the limit.

Example from `osl-eastbound-segment-bank.yaml`:
```
JFK → LHR (stopover)     ← EU/ME stopover #1
LHR → ATH (transit)      ← NOT a stopover (under 24h)
ATH → HEL (transit)      ← NOT a stopover (under 24h)
HEL → OSL (final)        ← Return to origin
```

---

## 6. Currency Impact Analysis

### 6.1 Filing Currency Mechanics

Oneworld Explorer fares are filed with IATA in the origin country's local currency. When you purchase, the fare is converted to your payment currency at the prevailing exchange rate. This means:

| Origin | Filing Currency | Conversion Path |
|--------|----------------|-----------------|
| Oslo | NOK | NOK → GBP (or your card currency) |
| London | GBP | Direct (no conversion) |
| Cairo | EGP | EGP → GBP |
| Tokyo | JPY | JPY → GBP |
| Stockholm | SEK | SEK → GBP |

### 6.2 NOK Exchange Rate Advantage

The Norwegian Krone has been structurally weak since 2020:
- NOK/USD ranged from ~8.5 (2020) to ~11.0+ (2023-2025).
- NOK/GBP has similarly weakened.
- A weak NOK means the same NOK-denominated fare converts to fewer USD/GBP.

Historical impact example:
- If DONE4 ex-OSL is filed at NOK 56,000:
  - At NOK/USD = 9.0: cost = $6,222
  - At NOK/USD = 10.5: cost = $5,333
  - At NOK/USD = 11.0: cost = $5,091
- The same filing becomes ~$1,100 cheaper as NOK weakens from 9.0 to 11.0.

### 6.3 Currency Timing Strategy

- IATA updates fare filings periodically (typically quarterly or semi-annually).
- Exchange rates move daily.
- The optimal booking window is when: (a) the NOK fare filing has not been updated recently, AND (b) NOK is at a local low vs your payment currency.
- After booking, fly the first segment immediately to lock the fare -- subsequent currency movements won't affect your ticket.

### 6.4 Other Weak-Currency Origins

| Origin | Currency | Why It's Cheap |
|--------|----------|----------------|
| Cairo (CAI) | EGP | Massive devaluation since 2022. EGP has lost ~60% of value. |
| Johannesburg (JNB) | ZAR | Persistent ZAR weakness. |
| Colombo (CMB) | LKR | Sri Lanka economic crisis devalued LKR. |
| Tokyo (NRT) | JPY | JPY at multi-decade lows vs USD. |
| Budapest (BUD) | HUF | Moderate HUF weakness. |

Cairo is the cheapest globally due to the EGP collapse, but positioning is impractical for UK-based travelers. Oslo offers the best combination of cheap fare + easy positioning.

---

## 7. YQ/Carrier Surcharge Optimization

### 7.1 Per-Carrier YQ Rates

| Carrier | YQ/Segment (USD) | YQ Tier |
|---------|-------------------|---------|
| AY (Finnair) | ~$10 | Very low |
| JL (JAL) | ~$12 | Very low |
| FJ (Fiji) | ~$20 | Very low |
| AS (Alaska) | ~$40 | Low |
| AA (American) | ~$50 | Low |
| UL (SriLankan) | ~$50 | Low |
| MH (Malaysia) | ~$60 | Low |
| WY (Oman Air) | ~$90 | Low |
| AT (Royal Air Maroc) | ~$100 | Medium |
| QR (Qatar) | ~$150 | Medium (non-linear) |
| RJ (Royal Jordanian) | ~$170 | Medium |
| CX (Cathay) | ~$200 | Medium |
| IB (Iberia) | ~$220 | High |
| BA (British Airways) | ~$321 | Very high |
| QF (Qantas) | ~$334 | Very high |

### 7.2 Plating Carrier Impact on Total YQ

The plating (validating) carrier determines the YQ charged across the ENTIRE itinerary. Same routing, different plating:

| Plating Carrier | Typical Total YQ (16-seg DONE4) | Notes |
|-----------------|---------------------------------|-------|
| **QR (Qatar)** | ~$800 | Cheapest. No RTW desk -- must use travel agent. |
| **MH (Malaysia)** | ~$900 | Second cheapest. Limited RTW experience. |
| **CX (Cathay)** | ~$1,500 | Moderate. Good service. |
| **AA (American)** | ~$1,800 | Best flexibility for mid-trip changes. AA RTW desk is gold standard. |
| **BA (British Airways)** | ~$2,500 | Most expensive. Email-only changes, weeks of delays. |

Source: dutch_122 on FlyerTalk, comparing identical DONE4 routing ex-OSL. QR plating saved EUR 1,273 vs AA/BA.

### 7.3 Surcharge Optimization Strategies

**Strategy 1: Avoid QF and BA metal where possible.**
- QF charges $334/segment. If you need to fly SYD-LAX, use AA codeshare on QF metal or JL transpacific instead.
- BA charges $321/segment. Use AY for Europe-Asia instead of BA.

**Strategy 2: Use AA on US domestic.**
- AA charges zero YQ on domestic US segments.
- Use AA for all US internal flights (JFK-LAX, SFO-JFK, etc.).

**Strategy 3: Maximize AY and JL segments.**
- Both charge very low YQ ($10-12/segment).
- AY for Europe and Europe-Asia. JL for Asia and transpacific.
- AY HEL-HKG is excellent (nonstop, low YQ, good D-class).
- Caution: AY HEL-NRT has JV surcharges of $270-480. Use JL for Japan.

**Strategy 4: QR YQ is non-linear.**
- Flat charge on the first QR segment, then small incremental per additional QR segment.
- Adding more QR segments has diminishing YQ cost.
- If using QR, use it for multiple segments (DOH-SIN, DOH-NRT, etc.) to amortize the flat charge.

**Strategy 5: Consider QR plating via travel agent.**
- Saves ~$800-1,273 vs AA plating on a typical 16-segment itinerary.
- Trade-off: QR has no RTW desk. All changes must go through your travel agent.
- AA plating gives best customer service for mid-trip changes.
- If your itinerary is stable (unlikely to change), QR plating is the cost-optimal choice.

### 7.4 Example YQ Comparison (Typical OSL Eastbound DONE4)

| Segment | Carrier | YQ (AA plating) | YQ (QR plating) |
|---------|---------|------------------|------------------|
| OSL-HEL | AY | ~$10 | ~$5 |
| HEL-HKG | AY | ~$10 | ~$5 |
| HKG-NRT | CX | ~$200 | ~$100 |
| NRT-LAX | JL | ~$12 | ~$8 |
| LAX-SFO | AS | ~$40 | ~$20 |
| SFO-JFK | AA | ~$50 | ~$25 |
| JFK-LHR | BA | ~$321 | ~$160 |
| LHR-ATH | BA | ~$321 | ~$160 |
| ATH-HEL | AY | ~$10 | ~$5 |
| HEL-OSL | AY | ~$10 | ~$5 |
| **Total** | | **~$984** | **~$493** |

Approximate figures. Actual amounts vary by route, date, and filing.

---

## 8. Comparison with Other Cheap Origins

### 8.1 Cairo (CAI) -- Cheapest Globally

| Aspect | CAI | OSL |
|--------|-----|-----|
| DONE4 base | $4,000 | $5,400 |
| Saving vs OSL | $1,400 | -- |
| Currency | EGP (collapsing) | NOK (weak) |
| Positioning from LHR | Moderate (BA direct, ~5h, $200-500) | Easy (2h, $30-100) |
| First segment options | CAI-AMM (RJ) typical | OSL-HEL (AY) typical |
| APD | None (not UK) | None (not UK) |
| Practical for UK-based | Moderate | Easy |
| Risk | EGP fare could be repriced upward; Egypt visa required | Low risk |
| Fare lock urgency | **Critical** -- fly first segment immediately | Important but less urgent |

Cairo is $1,400 cheaper but requires more effort: longer positioning flight, Egypt visa (if stopping over), and urgent fare-locking due to EGP instability.

### 8.2 Budapest (BUD)

| Aspect | BUD | OSL |
|--------|-----|-----|
| DONE4 base | ~$6,457 | $5,400 |
| Saving vs OSL | -- | **$1,057** |
| Currency | HUF | NOK |
| Positioning from LHR | Easy (BA/Wizz, ~2.5h, $50-150) | Easy (2h, $30-100) |
| First segment | Limited oneworld options from BUD | AY OSL-HEL excellent |
| Notes | Higher base fare negates positioning ease | Clear winner |

Oslo is clearly cheaper than Budapest.

### 8.3 Stockholm (ARN)

| Aspect | ARN | OSL |
|--------|-----|-----|
| DONE4 base | ~$6,177 | $5,400 |
| Saving vs OSL | -- | **$777** |
| Currency | SEK | NOK |
| Positioning from LHR | Easy (BA/SAS/Norwegian, ~2h, $50-150) | Easy (2h, $30-100) |
| First segment | AY ARN-HEL possible, or BA ARN-LHR | AY OSL-HEL preferred |
| Notes | Close to Oslo pricing but consistently ~$400-800 more | Oslo wins |

Stockholm is the nearest competitor to Oslo in Scandinavia but consistently costs ~$777 more for DONE4.

### 8.4 Johannesburg (JNB) / Cape Town (CPT)

| Aspect | JNB/CPT | OSL |
|--------|---------|-----|
| DONE4 base | $5,000 / $5,585 | $5,400 |
| Currency | ZAR | NOK |
| Positioning from LHR | Expensive (11h, $500-1,500) | Easy (2h, $30-100) |
| First segment | BA/QF to Asia or NA | AY OSL-HEL |
| Notes | Cheap base but positioning cost erases advantage | Oslo wins on total cost for UK-based |

JNB is nominally cheaper but the positioning flight from London (11 hours, $500+) wipes out the saving.

### 8.5 Tokyo (NRT)

| Aspect | NRT | OSL |
|--------|-----|-----|
| DONE4 base | $6,360 | $5,400 |
| Currency | JPY (very weak) | NOK |
| Positioning from LHR | Expensive (11h, $800-2,000+) | Easy (2h, $30-100) |
| First segment | JL NRT-anywhere, excellent | AY OSL-HEL |
| Notes | Weak JPY helps but still $960 more + expensive positioning | Oslo wins for UK-based |

NRT is attractive if you're already in Japan or Asia. For UK-based travelers, Oslo is definitively better.

### 8.6 Summary Ranking (UK-Based Traveler, DONE4)

| Rank | Origin | Total Cost (base + positioning + APD) | Verdict |
|------|--------|---------------------------------------|---------|
| 1 | **CAI** | ~$4,400 | Cheapest if you're willing to position to Cairo |
| 2 | **OSL** | ~$5,670 | **Best balance of cost + convenience** |
| 3 | **JNB** | ~$5,800 | Only if Africa is on route |
| 4 | **CMB** | ~$6,000 | Niche |
| 5 | **ARN** | ~$6,500 | Close to Oslo but always more expensive |
| 6 | **NRT** | ~$7,600 | Only if already in Asia |
| 7 | **BUD** | ~$6,700 | Not competitive |
| 8 | **LHR** | ~$8,330 | Convenient but expensive |

---

## 9. The Oslo Strategy in Practice

### 9.1 The Dual Ticket (Segment Bank) Approach

Buy 2x DONE3 or DONE4 ex-OSL (one eastbound, one westbound). Total base cost for 2x DONE4: approximately $10,800. This gives 32 segments of business class over 12 months, usable as an ad-hoc "segment bank."

At 20 segments actually used = ~$540/segment for business class. This is extraordinary value.

See `docs/segment-bank-strategy.md` for the full playbook.

### 9.2 Step-by-Step Execution

1. **Position to Oslo**: Book a cheap flight LHR/LGW/STN to OSL for the day before your first segment.

2. **First segment: OSL-HEL on Finnair**: Fly this immediately to lock the fare. AY OSL-HEL operates multiple times daily, D-class availability is generally good.

3. **Continue eastbound or westbound**: From Helsinki, connect to your preferred routing:
   - Eastbound: HEL-HKG (AY), HEL-DOH (QR), HEL-NRT (AY/JL)
   - Westbound: HEL-LHR (AY/BA), then LHR-JFK (AA/BA)

4. **Build remaining segments with dummy dates**: Book with placeholder dates, change for free later.

5. **Close the loop**: Final segment(s) return to OSL via any European routing. Common patterns:
   - LHR-OSL (BA)
   - HEL-OSL (AY)
   - ATH-HEL-OSL (AY-AY)

6. **Position home**: Separate cheap flight OSL to LHR/home.

### 9.3 Example Itinerary: Eastbound DONE3 ex-OSL

From `itineraries/osl-eastbound-segment-bank.yaml`:

```
1. OSL → HEL  (AY, stopover)     EU/ME
2. HEL → HKG  (AY, stopover)     Asia
3. HKG → NRT  (CX, stopover)     Asia
4. NRT → LAX  (JL, stopover)     Pacific crossing → NA
5. LAX → SFO  (AS, stopover)     NA
6. SFO → JFK  (AA, stopover)     NA
7. JFK → LHR  (BA, stopover)     Atlantic crossing → EU/ME
8. LHR → ATH  (BA, transit)      EU/ME
9. ATH → HEL  (AY, transit)      EU/ME
10. HEL → OSL (AY, final)        EU/ME return
```

Continents: EU/ME + Asia + NA = 3 (DONE3). 10 segments used of 16.

### 9.4 Example Itinerary: Westbound DONE3 ex-OSL

From `itineraries/osl-westbound-segment-bank.yaml`:

```
1. OSL → LHR  (BA, stopover)     EU/ME
2. LHR → DFW  (BA, stopover)     Atlantic crossing → NA
3. DFW → LAX  (AA, stopover)     NA
4. LAX → SFO  (AS, stopover)     NA
5. SFO → NRT  (JL, stopover)     Pacific crossing → Asia
6. NRT → SIN  (JL, stopover)     Asia
7. SIN → DOH  (QR, transit)      Asia → EU/ME
8. DOH → LHR  (QR, transit)      EU/ME
9. LHR → OSL  (BA, final)        EU/ME return
```

Continents: EU/ME + NA + Asia = 3 (DONE3). 9 segments used of 16.

---

## 10. Key Gotchas and Risks

### 10.1 Fare Filing Changes

IATA can update the NOK-denominated fare filing at any time. If they increase the filing, the advantage narrows. Mitigation: book and fly the first segment quickly to lock the fare.

### 10.2 Currency Reversal

If NOK strengthens significantly against USD/GBP, the advantage shrinks. Mitigation: the base fare differential ($2,600 vs LHR) is primarily from the filing, not just currency. Even with NOK strengthening, Oslo should remain cheaper.

### 10.3 D-Class Availability on Short Hops

Short intra-European segments (OSL-HEL, HEL-OSL, LHR-OSL) have limited business class seats. AY typically guarantees 2 D-class seats per flight. Book early for the first and last segments.

### 10.4 Origin Continent Stopover Limit

With Oslo as origin, EU/ME is the origin continent. Maximum 2 stopovers in EU/ME. The first segment (OSL-HEL) and return segments consume EU/ME capacity. Plan carefully:
- Make short connections transits (under 24h), not stopovers.
- Save EU/ME stopovers for high-value cities (London, Athens, etc.).

### 10.5 12-Month Validity

All segments must be completed within 12 months of the first departure. For a segment bank strategy using two tickets, plan the first segment dates 12 months apart to maximize the window.

---

## 11. FlyerTalk Source Threads

| Thread | Topic | Key Data |
|--------|-------|----------|
| [#2133996](https://www.flyertalk.com/forum/oneworld/2133996-cheapest-place-europe-one-world-explorer-fares.html) | Cheapest Europe fares | Origin city price comparison; Oslo vs Stockholm vs Budapest |
| [#2107664](https://www.flyertalk.com/forum/oneworld/2107664-carrier-imposed-fees-done4-ex-osl.html) | Carrier fees DONE4 ex-OSL | YQ breakdown; plating carrier comparison; dutch_122's EUR 1,273 saving |
| [#2176618](https://www.flyertalk.com/forum/oneworld/2176618-ex-osl-done-4-help.html) | Ex-OSL DONE4 help | First segment strategy; QR workaround; close-the-loop solutions |
| [#936102](https://www.flyertalk.com/forum/oneworld/936102-rtw-tickets-business-cheapest-country-start.html) | Cheapest country to start | Global origin comparison; Cairo vs Oslo vs others |
| [#1637682](https://www.flyertalk.com/forum/oneworld/1637682-impact-recent-currency-movements-ow-explorer-rtw-fare.html) | Currency movement impact | NOK/EGP/JPY effects on fares; filing currency mechanics |
| [#2008084](https://www.flyertalk.com/forum/oneworld/2008084-oneworld-explorer-user-guide.html) | User Guide (50+ pages) | Comprehensive booking and rules reference |

---

## 12. Action Items for RTW Optimizer

### 12.1 Bug Fix

`rtw/data/fares.yaml` lists Oslo currency as `EUR`. Should be `NOK`.

### 12.2 Feature Opportunities

1. **APD calculator**: Model APD costs for UK origin/stopover segments; flag avoidance strategies.
2. **Origin comparison command**: Enhance `rtw cost` to show total-cost-of-ownership including positioning and departure taxes.
3. **Positioning flight estimator**: Given a home city and origin city, estimate positioning cost.
4. **Currency exposure indicator**: Flag origins with volatile currencies and note the filing currency.
5. **Close-the-loop validator**: Check that the final segment returns to origin and warn about EU/ME stopover limit consumption.
