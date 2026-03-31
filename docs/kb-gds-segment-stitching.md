# Knowledge Base: GDS Segment Stitching for oneworld Explorer RTW Tickets

**Date**: 2026-03-30
**Sources**: FlyerTalk threads (185111, 363343, 1885075, 1955010, 2008084), 12-rtw-optimization-guide.md, existing FlyerTalk research, QR first-carrier research, booking.py GDS commands, IATA Rule 3015

---

## 1. Sabre vs Amadeus: Capabilities and Limitations

### System Overview

| Feature | Sabre (AA, AS) | Amadeus (BA, CX, QR, IB, QF, most TAs) |
|---------|---------------|----------------------------------------|
| E-ticket segment limit | **16 coupons** per ticket | **16 coupons** per ticket (standard), historically could do more |
| Machine-print limit | 16 segments | Can print up to 16 (some sources claim 20 historically for CX) |
| Open-dated segments | Cannot e-ticket open segments | Can e-ticket with open dates (dummy dates more robust) |
| Cross-carrier revalidation | Poor -- known sync problems | Better across oneworld carriers |
| RTW fare pricing | Strong (AA RTW desk specializes here) | Strong for experienced agents; QR's implementation less robust |
| Married segment handling | "Carrier refuses cancellation" error when trying to split | XE command sometimes works, sometimes not (airline-dependent) |
| RTW PNR annotation | OSI YY OW RTW added manually | Same annotation required |
| Validating carrier override | Agent can set manually | FV element in PNR controls this |
| Best used by | AA RTW desk, AS-plated tickets | Travel agents, BA, CX, QR offices |

### Key Insight: The 16-Segment Rule

The oneworld Explorer fare rule (Rule 3015) allows a **maximum of 16 segments** including surface sectors. This aligns with -- but is independent of -- the GDS e-ticket coupon limit. The fare rule limit is the binding constraint for most bookings.

**Historical context**: Before electronic ticketing, the limit was effectively the number of coupons that could fit on paper ticket stock. AA's Sabre could only machine-print 16, requiring handwritten tickets for anything over that. CX (on Amadeus) could reportedly handle more via computer-printed tickets. This is now largely moot since the fare rule itself caps at 16.

### When Systems Differ

- **Sabre excels** at AA-plated tickets, AA domestic segment handling, and the AA RTW desk's deep expertise
- **Amadeus excels** at multi-carrier international itineraries, QR/BA/CX plating, and travel agent flexibility
- **Reissue sync issues**: When a ticket plated on Sabre (AA) needs segments changed on Amadeus-resident carriers, or vice versa, PNR synchronization can break. The segment in one system may not reflect changes made in the other.

---

## 2. The Segment / Coupon Limit Problem

### Rule 3015 Limit: 16 Segments

- Maximum 16 segments total (flown + surface)
- This is the fare construction rule, not a GDS limitation
- Surface sectors count toward this limit

### GDS E-Ticket Coupon Limit

- Standard IATA e-ticket: **16 coupons** per ticket document
- Each flown segment consumes one coupon; surface sectors consume one coupon (ARNK)
- If routing requires more than 16 coupons (which it cannot under Rule 3015), conjunctive tickets would be needed

### Historical Sabre 16-Segment Machine-Print Limit

From the FlyerTalk thread (185111 -- "BA vs AA greater than 16 segments RTW"):

> "One of the limitations of SABRE is that it can not print a ticket with more than 16 segments. My last RTW ticket had to be 'hand written' by an AA CTO."

**Workarounds that were used**:
1. **Handwritten tickets**: AA City Ticket Offices (CTOs) could manually write tickets exceeding the machine-print limit
2. **Split tickets**: LAX AA office split one RTW into two separate ticket documents -- technically no longer a legal single OWE ticket, but functionally worked
3. **Transfer to another carrier**: Send authorization to CX in New York (or similar) to print/issue on their system
4. **Different GDS**: Use Apollo, Worldspan, or Amadeus-equipped agents instead of Sabre

### Modern Implications

Since Rule 3015 limits to 16 segments, the GDS coupon limit is no longer the binding constraint. However, **through-flights** (single flight number with intermediate stops) are relevant: a QF1 SYD-SIN-LHR counts as ONE segment/coupon but touches THREE cities across TWO additional continents.

---

## 3. Segment Addition: Sequential vs Non-Sequential Ordering

### The Segment-by-Segment Method (Dr. HFH's Technique)

This is the gold-standard approach from the FlyerTalk community, recommended by Dr. HFH (who booked "two or three RTW per year for a decade"):

1. **Feed the agent ONE flight at a time** -- do not present the full itinerary upfront
2. **Wait for D-class confirmation** before moving to the next segment
3. **Never present two segments as a "connection"** -- this invites married-segment restrictions

### Sequential vs Non-Sequential

**Sequential (recommended for phone booking)**:
- Give segments in chronological order of travel
- Agent builds the PNR linearly
- Each segment is confirmed individually in D-class before proceeding
- GDS naturally creates the itinerary in travel order

**Non-sequential (agent technique for difficult segments)**:
- Add "easy" segments first to establish the PNR
- Insert harder-to-book segments later
- Useful when D-class availability is tight on certain legs
- Agent can rearrange segment order in the PNR after all segments are sold
- **Risk**: Some GDS autovalidation may reject non-sequential builds

### GDS Segment Ordering Mechanics

In Amadeus, segments can be added in any order and rearranged:
```
SS D1 QR920 15MAR DOHADL    -- Add a segment
SS D1 AY089 10MAR HELDOH    -- Add earlier segment
/R                            -- Rearrange chronologically
```

In Sabre, similar flexibility exists but the AA RTW desk typically builds sequentially.

### The "Easy Segments First" Strategy

From FlyerTalk research on agent techniques:
- **Multi-city workaround**: Multi-destination search sometimes bypasses married segment control
- **POS/POC manipulation**: Different Point of Sale reveals different inventory
- **Dummy dates**: Book with placeholder dates, change for free later (avoids availability-constrained dates during initial build)
- **Direct carrier requests**: Selling carrier contacts operating carrier's inventory desk to release D-class

---

## 4. The Validation / Pricing Team Step

### BA Fares Team Process

When booking via BA:
1. BA frontline agent takes the itinerary request
2. Itinerary is passed to the **BA Fares Team** for validation against Rule 3015
3. Fares Team checks: routing validity, continent counts, segment limits, direction of travel, backtracking rules, stopover limits
4. Fares Team prices the ticket: base fare + taxes + YQ surcharges
5. Price quote returned to frontline agent or customer

**Turnaround**: Reported as approximately **2 business days** in the FlyerTalk first-time-buyer thread. The poster described being told to wait while BA's back-office team validated and priced the itinerary.

### AA RTW Desk Process

- AA's RTW desk agents perform validation **in real-time** during the call
- Experienced agents know the rules and can validate on the fly
- Pricing is generated immediately via the GDS fare quote command
- **Much faster** than BA's offline fares team process
- However, complex routings may still require supervisor review

### QR Process

- QR has **no RTW desk** -- they redirect to the website
- Cannot book RTW directly through QR call center
- Must use a travel agent who can plate on QR stock
- The agent handles all validation through their own GDS

### CX Process

- CX offices (particularly Sydney and Bangkok) handle RTW by email
- Customer emails itinerary request, CX builds and confirms
- Changes can be made in person at CX offices worldwide
- CX was historically able to handle more complex ticketing than AA

### Validation Steps (All Systems)

| Step | What Happens | Who Does It |
|------|-------------|-------------|
| Route legality | Check against Rule 3015 (direction, continents, backtracks) | Agent or fares team |
| Segment limits | Verify 16 max, per-continent limits | Automated + manual |
| D-class availability | Confirm each segment has D inventory | Real-time GDS query |
| Fare calculation | Base fare for origin + ticket type | GDS fare display (FQD) |
| Tax/surcharge calc | YQ per carrier, airport taxes, departure taxes | GDS auto-calc + manual |
| Ticket issuance | Generate e-ticket number, associate with PNR | Automated after payment |

---

## 5. Cross-System PNR Behavior

### The Problem

Each GDS (Sabre, Amadeus, Travelport/Apollo/Galileo) maintains its own PNR record. When a ticket involves multiple carriers on different systems, the PNRs must synchronize.

### How It Works

1. **Master PNR**: Created in the ticketing agent's GDS (e.g., AA creates in Sabre)
2. **Mirror PNRs**: Other airlines' systems create "passive" or "mirror" segments
3. **Synchronization**: Changes in one system should propagate to others via AIRIMP messages
4. **Reality**: Sync is imperfect and delayed

### Known Cross-System Issues

| Issue | Description | Impact |
|-------|-------------|--------|
| **Missing segments** | Amadeus PNR may not show all Sabre-originated segments (and vice versa) | Airlines may not see the full itinerary |
| **Schedule change desync** | One system updates for schedule change, others don't | Passenger shows wrong flight time |
| **Reissue failures** | Reissuing in one GDS doesn't always update mirrors | Can cause duplicate bookings or orphaned segments |
| **Status code mismatches** | Confirmed (HK) in one system may show request (RQ) in another | Check-in problems |
| **Cancellation cascades** | Cancelling in one system may not propagate, or may cancel too much | Lost segments |

### Practical Recommendations

1. **After ANY change, verify the full itinerary in ALL relevant systems** -- call the ticketing airline AND check online (AA.com, BA.com, etc.)
2. **Keep the PNR and ticket numbers offline** -- printed or saved digitally for reference at airports
3. **Allow 24-48 hours after changes** before assuming systems are in sync
4. **AA.com is the best self-service view** for AA-plated tickets -- you can see the itinerary online
5. **BA "Manage My Booking" can show weird interim states** -- partially updated itineraries, missing segments, or incorrect sequence during processing

---

## 6. Ticketing Airline Comparison for Complex RTW

### Ranking for Complex Itineraries

| Rank | Airline | GDS | Strengths | Weaknesses |
|------|---------|-----|-----------|------------|
| 1 | **AA** | Sabre | Dedicated RTW desk, real-time validation, agents know rules, AA.com visibility, best for mid-trip changes | Higher YQ than QR, desk hours limited (Mon-Fri 0700-2230 CT), can be slow (30-60 min calls) |
| 2 | **CX** | Amadeus | Email-based booking (good paper trail), handles complex ticketing, offices worldwide, historically printed >16 segments | Less convenient for US-based travelers, email turnaround varies |
| 3 | **QR** (via TA) | Amadeus | **Cheapest YQ** (saves EUR 800-1,273 vs AA), good for cost optimization | No RTW desk, must use travel agent, limited change flexibility via TA |
| 4 | **BA** | Amadeus | Large network, UK-based travelers convenient | Offline fares team (2-day turnaround), email-only changes (weeks of delays), highest YQ+APD, poor for modifications |
| 5 | **JL** | Amadeus | Good for ex-Japan bookings, dedicated RTW team | Limited English support, less accessible outside Japan |
| 6 | **QF** | Amadeus | Australian travelers | "Hopeless" post-COVID agents, 10+ calls for changes, not recommended |

### Decision Matrix

| Priority | Best Choice | Why |
|----------|------------|-----|
| **Flexibility** (changes, modifications) | AA | Dedicated desk, real-time changes, best agent expertise |
| **Cost** (lowest total price) | QR via TA | EUR 800-1,273 YQ savings, but accept reduced flexibility |
| **UK-based traveler** | AA or CX | Avoid BA's slow fares team; AA via Skype, CX via email |
| **Complex routing** (many segments, through-flights) | AA | Real-time validation catches rule violations immediately |
| **Paper trail** | CX | Email-based booking creates documentation |
| **After-hours emergency** | TA with 24/7 Amadeus | AA desk closes 2230 CT; TA covers gaps |

### Plating Carrier vs Ticketing Airline

These are the same thing in modern e-ticketing:
- **Plating/validating carrier**: Determines YQ charges across the ENTIRE itinerary
- **Ticketing airline**: The carrier whose stock the ticket is issued on (3-digit code)
- Same routing, different plating: AA-plated = ~EUR 1,748 taxes, QR-plated = ~EUR 475 taxes (dutch_122 data, DONE4 ex-OSL)

---

## 7. Agent Tricks for Hard-to-Book Segments

### Married Segment Avoidance

**The #1 cause of phantom D-class** is married segments. ExpertFlyer shows individual segment availability, but the GDS bundles connected flights, blocking booking.

| Technique | How It Works | When to Use |
|-----------|-------------|-------------|
| **One-at-a-time booking** | Feed agent single segments, never connections | Always -- default approach |
| **4+ hour AA domestic gaps** | Shorter gaps trigger automatic marriage | AA domestic connections |
| **24+ hour international gaps** | Creates stopovers instead of transits | International connections |
| **Dummy dates** | Book with placeholder dates, change later for free | When target dates show no D-class |
| **Non-sequential build** | Add easy segments first, hard ones later | When D-class is tight |

### Breaking Married Segments

From the FlyerTalk Amadeus thread (1885075):

- **XE command** (Amadeus): Can sometimes break married segments, but inconsistent
- **Segments with asterisk (*)**: Indicates married in some displays; without asterisk = may be breakable
- **"Carrier refuses cancellation"** error (Sabre): Indicates truly married segments
- **Call the operating carrier directly**: They can de-couple married segments "when there is a valid reason"
- **Methods are airline-specific**: "All methods for all airlines are different" (per FT agent poster)
- **Manual ticket issuance**: Can sometimes override married restrictions, but at potentially higher fare

### D-Class Availability Tricks

| Trick | Source | Details |
|-------|--------|---------|
| **POS manipulation** | FlyerTalk research | US POS may show BA D0; UK POS shows D7. Agent can change POS in GDS |
| **Multi-city search** | FlyerTalk research | Multi-destination search sometimes bypasses married segment control |
| **Waitlisting** | FlyerTalk research | Place on waitlist; carriers sometimes clear closer to departure |
| **Direct carrier inventory request** | FlyerTalk research | Selling carrier contacts operating carrier's inventory desk |
| **Finnair agent trick** | FlyerTalk research | Finnair agent: "I have a trick, let me try that..." (undisclosed method) |
| **Book and hold** | Industry practice | Some carriers allow 72-hour hold on D-class without ticketing |
| **Call at 7 AM DFW time** | FlyerTalk (PresRDC) | Best AA RTW desk agents are available at desk opening |

---

## 8. "Manage My Booking" Interim Itinerary Issues

### The Problem

When viewing an in-progress or recently-modified RTW booking online (BA.com "Manage My Booking", AA.com, etc.), passengers frequently see **weird interim states**:

### Symptoms

| Issue | Description |
|-------|-------------|
| **Missing segments** | Some legs don't appear in the online view, despite being confirmed in the PNR |
| **Wrong segment order** | Segments displayed out of chronological order |
| **Partial updates** | Some segments show new dates/flights while others show old ones |
| **Ghost segments** | Cancelled segments still appearing |
| **Surface sectors invisible** | ARNK segments don't display in passenger-facing views |
| **Status inconsistencies** | "Confirmed" in PNR but "Pending" in Manage My Booking |
| **Through-flight display** | SYD-SIN-LHR may show as one segment or two, inconsistently |

### Root Causes

1. **Asynchronous PNR synchronization**: GDS changes propagate to airline websites with delay (minutes to hours)
2. **Cross-system lag**: Changes made in Sabre (AA) may take 24-48 hours to appear in Amadeus-based airline views (BA, CX)
3. **RTW ticket complexity**: Standard online booking management tools are designed for simple A-B-A trips, not 16-segment multi-carrier itineraries
4. **Reissue processing**: During the reissue process (which can take hours or days), the online view shows a hybrid of old and new itinerary
5. **Surface sector handling**: GDS surface sectors (ARNK) have no passenger-facing equivalent, creating gaps in the online itinerary display

### Mitigations

1. **Always verify via the PNR directly** -- call the ticketing airline and have them read back all segments
2. **AA.com is the most reliable** online view for AA-plated tickets
3. **Don't panic** at interim states -- wait 24-48 hours after any change before assuming something is wrong
4. **Keep printed/offline copy** of confirmed itinerary with PNR and e-ticket numbers
5. **Cross-reference segment count** -- if you should have 14 segments and only see 12 online, call the airline

---

## 9. How the Fares Team Validates and Prices RTW Tickets

### The Validation Pipeline

```
Customer Request --> Agent Builds PNR --> Fare Validation --> Pricing --> Payment --> Ticketing
```

### Step 1: PNR Construction

Agent enters segments into GDS:
```
SS D1 AY123 15MAR OSLHEL       -- Sell segment: D-class, 1 seat, flight, date, route
SS D1 QR303 15MAR HELDOH       -- Next segment
ARNK                             -- Surface sector
SS D1 CX700 20MAR HKGNRT       -- Continue building...
```

### Step 2: Fare Display and Validation

```
FQD OSL OSL/VRW/D15MAR          -- Fare quote display: origin-origin, RTW fare, departure date
```

The GDS returns applicable fare basis codes (DONE4, AONE5, etc.) with base fares. The agent or automated system then validates:

| Check | Rule | How Validated |
|-------|------|---------------|
| Direction of travel | Continuous forward between TCs | Manual review + GDS route validation |
| Segment count | Max 16 total | GDS counts automatically |
| Per-continent segments | Max 4 (6 for North America) | Manual count by agent |
| Continent count | Must match ticket type (e.g., DONE4 = 4 continents) | Manual check |
| Intercontinental departures | 1 per continent (exceptions for NA, Asia, EU_ME+Africa) | Manual check |
| Stopover limits | 2 per continent after departing origin | Manual count |
| Backtracking | No returning to previously visited TC | Manual review |
| Carrier eligibility | Must be oneworld member or approved codeshare | GDS carrier validation |
| Origin match | Must return to origin city | GDS checks |

### Step 3: Pricing Calculation

```
FXP                              -- Price the PNR
```

The GDS calculates:
1. **Base fare**: From IATA published fare for origin city + ticket type
2. **YQ/YR surcharges**: Per-segment carrier-imposed charges (determined by plating carrier)
3. **Airport taxes**: Per-departure and per-arrival taxes
4. **Government taxes**: APD (UK), departure taxes, etc.
5. **Total**: Base + all taxes and surcharges

### Step 4: Manual Overrides

For complex RTW tickets, automated pricing may fail. The agent may need to:
- **Force the fare basis** (e.g., override DONE4 when system wants DONE5)
- **Manually calculate YQ** when the GDS auto-calc is wrong
- **Override validating carrier** (`/R,VC-QR` in Amadeus, or equivalent in Sabre)
- **Add OSI message**: `OSI YY OW RTW` (required annotation identifying this as a oneworld RTW)

### Step 5: Ticketing

```
/R,VC-AA                         -- Set validating carrier
TTP                              -- Ticket the PNR (issue e-ticket)
```

E-ticket numbers are generated and associated with the PNR. At this point, the booking is live and segments are confirmed with all operating carriers.

### BA Fares Team Specifics

When booking via BA:
1. Frontline agent collects itinerary details
2. Sends to **offline fares team** for validation
3. Fares team reviews against Rule 3015 (reported ~2 business day turnaround)
4. Returns price quote to frontline or customer
5. Customer confirms, payment taken
6. Ticket issued

This is **significantly slower** than the AA RTW desk, where validation and pricing happen in real-time during a single phone call. The BA process is better suited to customers who have a firm itinerary and don't need iterative changes.

---

## 10. Implications for RTW Optimizer Tool

### Current Implementation Status

| Feature | Status | Location |
|---------|--------|----------|
| Amadeus GDS commands | Implemented | `rtw/booking.py` -- `_gds_commands()` |
| Married segment warnings | Implemented | `rtw/booking.py` -- transit + same-day detection |
| Through-flight annotations | Implemented | `rtw/booking.py` -- via-stop warnings |
| CX hub-connection warning | Implemented | `rtw/booking.py` -- CX non-HKG married risk |
| Phone booking script | Implemented | `rtw/booking.py` -- segment-by-segment method |
| Rule 3015 validation | Implemented | `rtw/rules/` -- 31 rules across 10 files |

### Potential Enhancements

1. **GDS system recommendation**: Based on plating carrier, suggest which GDS/desk to use
2. **Cross-system PNR sync warnings**: When itinerary spans carriers on different GDS platforms, warn about sync risks
3. **BA fares team timeline warning**: If BA is selected as plating carrier, note the ~2-day validation turnaround
4. **Segment ordering advisor**: Suggest which segments to book first (easy D-class) vs last (tight availability)
5. **Married segment risk scoring**: Beyond same-day transit detection, flag known problematic carrier/route combinations (CX via HKG, AA domestic <4hr)
6. **Manage My Booking guidance**: Post-booking checklist warning about interim display issues
7. **Multi-GDS command generation**: Currently generates Amadeus only; could add Sabre commands for AA-plated tickets

---

## Appendix: GDS Command Reference

### Amadeus Commands (Used by BA, CX, QR, most TAs)

| Command | Purpose | Example |
|---------|---------|---------|
| `FQD` | Fare quote display | `FQD OSL OSL/VRW/D15MAR` |
| `SS` | Sell segment | `SS D1 QR303 15MAR HELDOH` |
| `ARNK` | Surface sector | `ARNK` |
| `FXP` | Price PNR | `FXP` |
| `OSI` | Other service info | `OSI YY OW RTW` |
| `/R,VC-` | Set validating carrier | `/R,VC-AA` |
| `TTP` | Issue ticket | `TTP` |
| `XE` | Cancel segment | `XE3` (cancel segment 3) |
| `FV` | Force validating carrier | `FV AA` |

### Sabre Commands (Used by AA RTW desk)

| Command | Purpose | Example |
|---------|---------|---------|
| `WPNCB` | Price itinerary | `WPNCB` |
| `0` + sell | Sell segment | `0AA100Y15MARDFW LAX` |
| `/ARNK/` | Surface sector | Inline ARNK |
| `5-` | OSI message | `5-OW RTW` |
| `W/` | Ticket designator | `W/VC*AA` |
| `ET` | End and ticke | `ET` |

### Key Differences in Command Syntax

- Amadeus uses `SS` (sell segment) prefix; Sabre uses `0` (zero) prefix
- Amadeus pricing: `FXP`; Sabre pricing: `WPNCB`
- Both support ARNK for surface sectors
- Both require manual OSI annotation for RTW identification

---

## Appendix: FlyerTalk Source Threads

| Thread | URL | Key Topics |
|--------|-----|------------|
| BA vs AA >16 segments | flyertalk.com/forum/oneworld/185111 | Sabre 16-segment limit, handwritten tickets, split tickets |
| RTW desk use | flyertalk.com/forum/oneworld/363343 | AA vs CX vs BA desks, handwritten vs printed, mid-trip changes |
| Amadeus breaking married segments | flyertalk.com/forum/online-travel-booking-bidding-agencies/1885075 | XE command, carrier-specific methods, GDS differences |
| First time buyer via BA | flyertalk.com/forum/oneworld/1955010 | BA booking process, fares team validation, UK-based experience |
| oneworld Explorer User Guide | flyertalk.com/forum/oneworld/2008084 | Comprehensive 50+ page thread covering all aspects |
| AA RTW desk availability vs EF | flyertalk.com/forum/oneworld/2152207 | ExpertFlyer vs actual bookable inventory |
| Married segment control (Finnair) | flyertalk.com/forum/finnair-finnair-plus/1888592 | MSC on X, U, F classes; agent tricks |
