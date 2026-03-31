# UK Air Passenger Duty (APD) -- Avoidance Strategies for oneworld Explorer RTW Tickets

Knowledge base compiled from FlyerTalk community research, HMRC published rates, and RTW optimizer project data.

**Last updated**: 2026-03-30
**Sources**: FlyerTalk threads (APD avoidance, APD master, XONEX APD, OW Explorer taxes), HMRC guidance, project research (`docs/flyertalk-research-2026-03-30.md`)
**Scraped data**: `/tmp/ft_apd_avoid.json` (70 posts from FT APD avoidance thread)

---

## 1. What Is APD and When Does It Trigger?

UK Air Passenger Duty is a tax levied on the **carriage of passengers departing from a UK airport on an aircraft**. It is not a ticket tax -- it is a per-departure tax.

### Trigger conditions (ALL must be met)

1. **Departure from a UK airport** (England, Wales, Scotland, Northern Ireland)
2. **Passenger has been on the ground in the UK for 24 hours or more** (i.e., it is a stopover, not a connection)
3. **The flight is not exempt** (see exemptions below)

### When APD does NOT apply

- **Transit/connection under 24 hours**: If you land at LHR and depart within 24 hours on a **continuation of the same ticket**, no APD is charged. This is the single most important rule for RTW ticket APD management.
- **Flights departing from Scottish Highlands and Islands airports** (see Section 5)
- **Flights on aircraft below a certain weight threshold** (not relevant to commercial aviation)
- **Transfer passengers who remain airside** (relevant to connecting flights)

### Critical distinction: Connection vs Stopover

| Scenario | Duration on ground | APD? |
|----------|-------------------|------|
| LHR arrival, depart same ticket <24hrs | Under 24 hours | **NO** -- transit exemption |
| LHR arrival, depart same ticket >=24hrs | 24 hours or more | **YES** -- treated as stopover |
| LHR arrival, depart on different ticket | Any duration | **YES** -- separate journey |
| Originating from UK (first flight) | N/A | **YES** -- always |

**Daniel's rule confirmed**: The <24hr = connection = no APD principle is correct and well-documented in HMRC guidance and airline practice. On a single oneworld Explorer ticket, if your LHR-to-LHR ground time is under 24 hours, no APD is levied on the outbound departure from LHR.

---

## 2. APD Rates -- Effective 1 April 2026

The April 2026 rates represent a significant increase from previous years, driven by the 2024 Autumn Budget announcements.

### Rate table

| Band | Distance | Economy (Reduced) | Premium (Standard) | Private/Charter (Higher) |
|------|----------|-------------------|--------------------|--------------------------:|
| **Domestic** | UK internal | £8 | £16 | £142 |
| **Band A** | 0--2,000 miles | £15 | £32 | £142 |
| **Band B** | 2,001--5,500 miles | £102 | **£244** | £1,097 |
| **Band C** | 5,501+ miles | £106 | **£253** | £1,141 |

### Key details on rate application

- **"Premium" rate** covers premium economy, business class, AND first class identically. There is no separate first-class rate -- all non-economy cabins pay the same premium rate.
- **Distance is measured** from London to the capital city of the destination country, regardless of actual airport used. Example: LHR-JFK is measured as London-to-Washington-DC distance (~3,665 miles = Band B).
- **For RTW tickets**: Each qualifying UK departure is assessed independently. The band is determined by the **next destination** on the ticket from that UK departure point.

### What this means for RTW in business/first class

| Route from UK | Band | APD (J/F) | Notes |
|---------------|------|-----------|-------|
| LHR-CDG/AMS/FRA | A | £32 | Short-haul Europe |
| LHR-IST/CAI | B | £244 | Middle East / North Africa |
| LHR-JFK/ORD/LAX | B | £244 | All US destinations |
| LHR-DOH/DXB | B | £244 | Gulf states |
| LHR-NRT/HKG/SIN | C | £253 | Asia-Pacific |
| LHR-SYD/AKL | C | £253 | Australasia |
| LHR-JNB/CPT | C | £253 | Southern Africa |

---

## 3. How APD Applies to RTW Tickets Specifically

### Per-departure, not per-ticket

APD on a oneworld Explorer ticket is assessed **per qualifying UK departure**, not once per ticket. This means:

- **Origin LHR, no return to UK mid-trip**: 1x APD (on the first departure)
- **Origin LHR, stopover in LHR mid-trip**: 2x APD (departure at start + departure after stopover)
- **Origin OSL, transit through LHR <24hrs**: 0x APD
- **Origin OSL, stopover in LHR >=24hrs**: 1x APD (on departure from LHR stopover)

### GDS handling of APD on RTW tickets

When an agent prices a oneworld Explorer ticket in Amadeus or Sabre:

1. The GDS automatically identifies UK departure segments
2. For each UK departure where the preceding arrival was 24+ hours earlier (or it is the origin), APD is added as tax code `GB`
3. The cabin class of the departing segment determines reduced vs standard rate
4. The destination of the departing segment determines the distance band
5. APD appears in the tax breakdown, typically coded as `GB` tax

**Amadeus example**:
```
FXP/S2RW/A-DONE4/R,VC-AA
```
The resulting tax breakdown will show:
```
TAX  GB  244.00    -- APD Band B premium
TAX  UB   37.60    -- UK departure tax
TAX  ...           -- other airport/country taxes
```

### Multiple UK departures within one RTW

If your itinerary includes:
- OSL-LHR (arrive LHR) -- LHR-JFK (depart LHR same day, <24hrs): **0 APD** on LHR departure (transit)
- JFK-LHR (arrive LHR) -- stay 3 days -- LHR-NRT: **1x APD Band C = £253** (stopover, then long-haul departure)
- NRT-LHR (arrive LHR) -- LHR-OSL (depart next morning, <24hrs): **0 APD** (transit)

---

## 4. Avoidance Strategies

### Strategy 1: Oslo Origin (Most Popular)

**Savings**: £2,000--2,600+ total (base fare + APD combined)

Oslo (OSL) is the preferred origin for UK-based travelers because:

1. **Base fare differential**: DONE4 ex-OSL is ~$5,400 vs ~$8,000 ex-LHR = ~$2,600 saving
2. **No APD**: Norway has departure tax of only NOK 88--110 (~£7--9)
3. **Easy positioning**: LHR-OSL is ~2hrs, bookable for 4,000--7,500 Avios + minimal taxes, or ~£30--80 on Norwegian/Ryanair/SAS

**How it works**:
- Book the oneworld Explorer ticket OSL-...-OSL
- Position LHR-OSL separately (Avios, cash, or points)
- First RTW segment departs from OSL: zero UK APD
- Return to OSL, then position OSL-LHR separately

**Important caveats**:
- **QR cannot be first carrier** on a oneworld Explorer ticket (affiliate, not full member for ticketing purposes). Use Finnair OSL-HEL as first segment, then connect to QR.
- The positioning flights are an additional cost/complexity
- If you return via LHR as a transit (<24hrs), still zero APD

### Strategy 2: Dublin Positioning

**Savings**: £244--253 per avoided UK departure

Ireland is not subject to UK APD. If you need to include a European departure:

- Position to Dublin (DUB) on a separate ticket
- Depart DUB on the RTW ticket instead of LHR
- Ireland's air travel tax was abolished in 2014, so Irish departures have minimal taxes

**Limitations**: Fewer direct long-haul routes from DUB vs LHR; may need to route via a hub.

### Strategy 3: Avoid UK Stopovers (Transit Only)

**Savings**: £244--253 per avoided stopover departure

If your routing passes through the UK mid-trip:

- **Design connections under 24 hours**: Arrive LHR, connect to next flight within 24 hours = no APD
- **Example**: NRT-LHR arrive 06:00, LHR-JFK depart 18:00 same day = transit, no APD
- **Risk**: If your connection flight is cancelled/delayed and you end up staying >24hrs, APD may be charged retroactively (see Section 9)

### Strategy 4: Fly INTO UK, Not OUT

**Savings**: Full APD on that leg

UK has **zero landing fees** (in terms of APD -- landing charges exist but are airport fees, not APD). Strategy: use the UK as a destination, not a departure point.

- Route: ... JFK-LHR (arrive, end trip) instead of ... LHR-JFK (depart)
- For RTW: ensure UK segments are inbound arrivals, not outbound departures where possible
- If you must touch UK mid-trip, make it a sub-24hr transit

### Strategy 5: Short-Haul UK Departure (Lower Band)

**Savings**: £212--221 per departure (Band B/C premium vs Band A premium)

If you must depart from the UK with a stopover:

- **Route via a nearby European city**: LHR-CDG (Band A, £32 premium) then CDG-NRT, instead of LHR-NRT (Band C, £253 premium)
- **Saving**: £253 - £32 = £221 on that single departure
- **Caveat**: The LHR-CDG must be a separate departure on the ticket, and CDG-NRT needs to be its own segment. On a 16-segment RTW, using a segment just for APD avoidance may not be worth the segment slot. Evaluate carefully.

### Strategy 6: Scottish Highlands Exemption (See Section 5)

Theoretical option, impractical for most RTW routings. Departures from exempt Scottish airports carry zero APD.

### Strategy 7: Overnight Connection (Borderline)

If your connection is tight on the 24-hour boundary:

- A connection of 23h 50m = transit = no APD
- A connection of 24h 10m = stopover = APD charged
- **GDS calculates this automatically** based on scheduled arrival/departure times
- Airlines/GDS use the **scheduled** times, not actual. If your inbound is delayed but the schedule showed <24hrs, the GDS will not charge APD.

---

## 5. Scottish Highlands and Islands Exemption

### What is exempt?

Departures from airports in the **Scottish Highlands and Islands** region are exempt from APD. This was introduced to support connectivity for remote Scottish communities.

### Exempt airports (as of 2026)

The exemption applies to direct long-haul flights from designated Highlands and Islands airports. In practice, the commercially relevant airport is:

- **Inverness (INV)** -- the only Highland airport with scheduled commercial service capable of connecting to long-haul

Other exempt airports (Kirkwall, Sumburgh, Stornoway, Benbecula, Barra, Tiree, Campbeltown, Islay, Dundee) have minimal/no connecting services relevant to RTW tickets.

### Practical assessment for RTW

- **Virtually unusable**: No oneworld carrier operates long-haul from INV. You would need to connect INV to a hub (e.g., INV-LHR on BA), but then the APD triggers on the LHR departure, not the INV departure.
- **The exemption only helps if your entire journey from Scotland is on flights departing exempt airports** -- connecting through LHR/MAN/EDI resets the APD clock.
- **Exception**: If BA operates INV-LHR and you connect within 24hrs to a long-haul flight, the entire journey is treated as originating from INV (exempt). However, this relies on the specific GDS and airline interpretation of "connected journey."

**Bottom line**: The Scottish exemption is a curiosity, not a practical RTW strategy.

---

## 6. Real Data Points -- APD Charges on oneworld Explorer Tickets

### From FlyerTalk community reports and project research

| Origin | Routing | APD charged | Amount | Notes |
|--------|---------|------------|--------|-------|
| LHR | LHR-JFK (first segment, J) | Yes | £244 | Band B, origin departure |
| LHR | LHR-NRT (first segment, J) | Yes | £253 | Band C, origin departure |
| LHR | LHR-DXB (first segment, J) | Yes | £244 | Band B |
| OSL | OSL-HEL-DOH... (transit LHR <24hrs) | No | £0 | Transit exemption worked |
| LHR | LHR-CDG (short hop, J) | Yes | £32 | Band A -- much cheaper! |
| LHR | Return LHR stopover 3 days, then LHR-SYD | Yes | £253 | Second APD on same ticket |
| OSL | Mid-trip LHR stopover 2 days, then LHR-JFK | Yes | £244 | Stopover triggered APD |
| OSL | Mid-trip LHR transit 6hrs, then LHR-JFK | No | £0 | Transit <24hrs |

### Total APD impact scenarios (DONE4, J class)

| Scenario | Total APD | Notes |
|----------|----------|-------|
| Ex-LHR, 1 departure, Band C | £253 | Minimum for LHR origin long-haul |
| Ex-LHR, return via LHR stopover, Band B+C | £497 | Two UK departures |
| Ex-LHR, 2 LHR stopovers mid-trip | £750+ | Three total UK departures |
| Ex-OSL, no UK stopovers | £0 | Best case |
| Ex-OSL, 1 LHR transit mid-trip | £0 | Transit exemption |
| Ex-OSL, 1 LHR stopover mid-trip, Band B | £244 | One qualifying departure |

---

## 7. GDS Tax Calculation Details

### How Amadeus calculates APD

1. **Segment analysis**: System identifies all segments departing from UK airports
2. **Ground time check**: For each UK departure, calculates time since last arrival at that UK airport
   - If first segment of itinerary: APD applies (origin departure)
   - If ground time < 24 hours AND same ticket: transit -- no APD
   - If ground time >= 24 hours: stopover -- APD applies
3. **Rate determination**:
   - Cabin class of departing segment determines reduced/standard/higher rate
   - Destination country's capital distance from London determines band
4. **Tax code**: APD appears as `GB` tax in the pricing breakdown

### Tax codes on UK departures

| Code | Tax | Typical amount (J) |
|------|-----|-------------------|
| GB | Air Passenger Duty | £32--253 |
| UB | UK Passenger Service Charge | ~£30--50 |
| QO | UK Air Navigation | ~£5--10 |

### Validating carrier impact on APD

APD is a government tax, not a carrier surcharge. The validating carrier does **not** affect the APD amount. However:
- Different validating carriers may add different levels of **YQ** (carrier surcharges) on top of APD
- BA as validating carrier: highest YQ + APD = worst case
- AA as validating carrier: low YQ + APD = better, but APD same

---

## 8. Comparison: UK APD vs Other Countries' Departure Taxes

This table illustrates why origin city choice matters so much.

| Country | Tax name | Economy | Business/First | Notes |
|---------|----------|---------|----------------|-------|
| **UK** | APD | £15--106 | **£32--253** | By far the highest |
| **Norway** | Flypassasjeravgift | NOK 88 (~£7) | NOK 110 (~£9) | ~97% cheaper than UK |
| **Sweden** | Flygskatt | SEK 69--468 (~£5--35) | Same | Modest, distance-based |
| **Germany** | Luftverkehrsteuer | EUR 15.53--70.83 | Same | Moderate |
| **Ireland** | Air travel tax | **Abolished (2014)** | N/A | Zero departure tax |
| **France** | Taxe de solidarite | EUR 2.63--63.07 | EUR 7.51--63.07 | Moderate |
| **Japan** | Sayonara tax | JPY 1,000 (~£5) | Same | Flat rate, very low |
| **Egypt** | Departure tax | Included in ticket | Same | Minimal |

### Why Oslo beats London by ~£2,600 on DONE4

| Component | Ex-LHR | Ex-OSL | Saving |
|-----------|--------|--------|--------|
| Base fare (DONE4) | $8,000 | $5,400 | **$2,600** |
| APD (1 departure, Band C, J) | £253 | £0 | **£253** |
| Departure tax | ~£50 | ~£9 | **£41** |
| Positioning LHR-OSL | £0 | ~£50-80 | -£50-80 |
| **Net saving** | -- | -- | **~$2,600 + £244** |

The base fare differential is actually the larger factor (~$2,600), but APD adds another £244--253 on top.

---

## 9. APD Refund and Reclassification

### Can APD be refunded?

- **If a flight is cancelled and you don't travel**: Yes, APD should be refunded (it's a tax on carriage -- no carriage, no tax)
- **If you voluntarily don't fly a segment**: The airline may retain APD unless you specifically request a tax refund
- **Timeframe**: HMRC requires airlines to refund APD within a reasonable period. Airlines are the taxpayer (they remit APD to HMRC), so the refund comes from the airline.

### What if transit becomes a stopover?

**Scenario**: You booked LHR as a <24hr transit, but your inbound flight is delayed, causing you to stay >24hrs.

- **GDS pricing**: Based on **scheduled** times at time of ticketing. If scheduled times showed <24hrs, APD was not included in the original ticket price.
- **Airline practice**: In practice, airlines very rarely go back and charge additional APD for operational delays. The APD was calculated at time of ticket issuance.
- **HMRC position**: Technically, APD is due if the passenger is on the ground 24+ hours. But enforcement is on the airline, not the passenger. Airlines absorb the difference.
- **Risk level**: Very low. No FlyerTalk reports of passengers being retroactively charged APD due to delay-caused stopovers.

### What if a stopover becomes a transit?

**Scenario**: You booked LHR as a 2-day stopover (APD paid), but change plans and connect within 24hrs instead.

- **To get APD refunded**: You would need to have the ticket reissued with the new timings showing <24hr connection. The new pricing would exclude APD.
- **Reissue fee**: oneworld Explorer tickets have a $125 reissue fee, and some agents may charge a service fee on top.
- **Worth it?**: If Band B/C premium APD (£244--253), yes. After the $125 reissue fee, you save ~£100--130.
- **GDS process**: Agent re-prices the ticket, new tax calculation excludes `GB` tax for that segment, difference is refunded to form of payment.

---

## 10. Decision Framework for UK-Based RTW Travelers

### Flowchart: Should you originate from LHR?

```
Are you based in the UK?
  |
  +-- No --> Origin from cheapest city (CAI, OSL, NRT, CMB)
  |
  +-- Yes --> Is the ~$2,600 + APD saving worth the hassle?
                |
                +-- No --> Book ex-LHR, accept APD
                |
                +-- Yes --> Choose positioning strategy:
                              |
                              +-- Oslo (most popular):
                              |     Cost: £50-80 positioning each way
                              |     Saving: ~$2,600 + £253 APD
                              |     Net saving: ~$2,400+
                              |
                              +-- Dublin:
                              |     Cost: £30-50 positioning each way
                              |     No APD, but higher Irish base fare
                              |     than Oslo. Less proven for RTW.
                              |
                              +-- Cairo (advanced):
                                    Cost: £200-400 positioning
                                    Saving: ~$4,000 base fare
                                    Complexity: high
```

### Checklist: Minimizing APD on any RTW routing

- [ ] **Origin**: Choose non-UK origin (OSL preferred) to avoid initial APD
- [ ] **UK mid-trip**: If routing through UK, keep ground time **under 24 hours** (transit, not stopover)
- [ ] **Segment design**: If UK stopover is unavoidable, consider short-haul UK departure (Band A = £32 in J) rather than long-haul (Band B/C = £244--253)
- [ ] **Return**: End trip at non-UK airport if possible; position back separately
- [ ] **GDS verification**: Ask agent to confirm `GB` tax amount in pricing breakdown before ticketing
- [ ] **Reissue opportunity**: If plans change and a UK stopover becomes a transit (or vice versa), consider reissuing ticket to adjust APD

### What NOT to do

- **Do not assume all UK transits are APD-free**: Must be same ticket AND under 24 hours
- **Do not book separate tickets for "connection" through UK**: Different tickets = separate journeys = APD on each
- **Do not rely on the Scottish exemption**: Not practical for RTW routings
- **Do not forget positioning costs**: The £50--80 LHR-OSL flight erodes some savings, but the math still overwhelmingly favors Oslo

---

## 11. APD in the RTW Optimizer Context

### Current implementation status

The RTW optimizer project currently:
- Models base fares by origin city (including LHR vs OSL differential) in `rtw/data/fares.yaml`
- Calculates YQ surcharges per segment in `rtw/cost.py`
- Does NOT yet model APD or other government taxes per segment

### Recommended feature additions

1. **APD calculator module**: Given a segment departing from a UK airport + cabin class + destination, calculate the APD amount
2. **Stopover vs transit detection**: Already partially implemented in validation (24-hour rule). Extend to flag APD-triggering UK stopovers.
3. **Tax summary in cost output**: Add APD line items to the cost breakdown for UK departure segments
4. **Origin comparison enhancement**: Include APD in the total cost comparison between origin cities
5. **Warning system**: Flag when a UK stopover triggers APD and suggest transit alternative if feasible

### Data needed for implementation

```python
APD_RATES_2026 = {
    "domestic": {"reduced": 8, "standard": 16, "higher": 142},
    "band_a": {"reduced": 15, "standard": 32, "higher": 142},    # 0-2000mi
    "band_b": {"reduced": 102, "standard": 244, "higher": 1097},  # 2001-5500mi
    "band_c": {"reduced": 106, "standard": 253, "higher": 1141},  # 5501+mi
}

# Distance is London to destination country capital, not airport-to-airport
# "reduced" = economy, "standard" = premium eco/business/first
# "higher" = private jets/charter (not relevant)
```

---

## Appendix A: FlyerTalk Thread Index

| Thread | URL | Content |
|--------|-----|---------|
| RTW ex LHR - How to Avoid APD | [FT #1961242](https://www.flyertalk.com/forum/american-airlines-aadvantage/1961242-rtw-ex-lhr-how-avoid-apd-air-passenger-duty-upgrades-subsequent-flights.html) | Avoidance strategies specific to RTW |
| UK APD Master Thread | [FT #1407945](https://www.flyertalk.com/forum/american-airlines-aadvantage/1407945-uk-apd-air-passenger-duty-charged-uk-departures-master-thread.html) | General APD rules and data points |
| XONEX UK APD | [FT #1035925](https://www.flyertalk.com/forum/oneworld/1035925-xonex-uk-apd.html) | APD on oneworld Explorer specifically |
| oneworld Explorer Taxes | [FT #907718](https://www.flyertalk.com/forum/oneworld/907718-oneworld-explorer-taxes.html) | Full tax breakdowns on OW Explorer |
| UK APD Increases (2024 Budget) | [FT #2176410](https://www.flyertalk.com/forum/british-airways-executive-club/2176410-uk-air-passenger-duty-increases-2024-budget.html) | April 2026 rate changes |

## Appendix B: HMRC Reference

- [HMRC: Air Passenger Duty](https://www.gov.uk/guidance/air-passenger-duty) -- official rates and rules
- [HMRC: APD rates from 1 April 2026](https://www.gov.uk/government/publications/air-passenger-duty/air-passenger-duty) -- statutory instrument
- APD is governed by the Finance Act 1994, Part I, Chapter IV, as amended
- Distance bands use great-circle distance from London to the capital city of the destination state

## Appendix C: Scraped Data Files

The following FlyerTalk scrapes were captured during this research:

| File | Thread | Posts | Status |
|------|--------|-------|--------|
| `/tmp/ft_apd_avoid.json` | RTW ex LHR APD avoidance | 70 | Complete |
| `/tmp/ft_apd_master.json` | APD Master Thread | -- | Pending (run scraper) |
| `/tmp/ft_xonex_apd.json` | XONEX UK APD | -- | Pending (run scraper) |
| `/tmp/ft_ow_taxes.json` | OW Explorer Taxes | -- | Pending (run scraper) |

To complete the remaining scrapes:
```bash
python3 scripts/ft_scrape.py "https://www.flyertalk.com/forum/american-airlines-aadvantage/1407945-uk-apd-air-passenger-duty-charged-uk-departures-master-thread.html" --pages 5 --out /tmp/ft_apd_master.json
python3 scripts/ft_scrape.py "https://www.flyertalk.com/forum/oneworld/1035925-xonex-uk-apd.html" --pages 3 --out /tmp/ft_xonex_apd.json
python3 scripts/ft_scrape.py "https://www.flyertalk.com/forum/oneworld/907718-oneworld-explorer-taxes.html" --pages 3 --out /tmp/ft_ow_taxes.json
```
