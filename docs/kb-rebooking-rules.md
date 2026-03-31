# Rebooking and Change Rules for oneworld Explorer RTW Tickets

Knowledge base covering the complete change/rebooking framework for oneworld Explorer (Rule 3015) tickets. Compiled from IATA Rule 3015 Section 16 (April 2025 update), FlyerTalk community reports (400+ data points across 8 threads), and real-world booking experiences with AA, QF, BA, CX, and JL ticketing desks.

**Sources**: Rule 3015 Section 16 (Voluntary Changes / Rerouting / Penalties), FlyerTalk threads #2008084 (User Guide, 60+ pages), #2155530 (QF change fee disputes), #2161590 (QF charging changing fee), #2182642 (ticket number changes on reissue), #2170176 (downgrade/re-upgrade), #1417740 (origin/return), #2183904 (cancellation/refund), #185111 (BA vs AA >16 segments).

---

## 1. Complete Change Fee Structure

### The Three Tiers

Rule 3015 Section 16 defines three distinct tiers of changes, each with different cost implications:

#### Tier 1: Free Changes (No Fee, No Repricing)

| Change Type | Conditions | Rule Reference |
|-------------|------------|----------------|
| Date/time changes | Any segment, unlimited times, subject to D-class availability | 16(a)1.a / 16(a)2.a |
| Carrier substitution (same route) | Same origin-destination airports, different oneworld carrier | Implicit in 16(a)2.a |
| Flight number changes | Earlier/later flight same day, same carrier, same route | Implicit in 16(a)2.a |

**Key principle**: Date changes are free because Rule 16(a)2.a states "Changes are permitted provided ticketed points remain the same" with no fee mentioned. This is the foundation of the "dummy dates" strategy -- book with placeholder dates, change to actual dates when ready.

**Critical distinction**: A date change is NOT a rebooking, rerouting, or reissue within the meaning of Rule 16. It is a simple schedule adjustment that preserves all ticketed points.

#### Tier 2: $125 Changes (Routing Changes)

| Change Type | Fee | Notes |
|-------------|-----|-------|
| Add/remove a city | $125 per transaction | Adding or dropping a ticketed point |
| Reorder cities | $125 per transaction | Changing the sequence of ticketed points |
| Stopover to transfer conversion | $125 per transaction | Changing a >24h stay to <24h or vice versa |
| Transfer to stopover conversion | $125 per transaction | Reverse of above |
| Drop a segment | $125 per transaction | Removing a flight from the itinerary |
| Add a segment | $125 per transaction | Adding a new flight (within 16-segment limit) |
| No-show rebooking (after departure) | $125 per transaction | Rule 16(a)2.c |

**The per-transaction rule**: The $125 fee is per change TRANSACTION, not per segment changed. A "transaction" is a single interaction where changes are processed. Bundle all routing changes into a single phone call and they should be processed as one $125 fee. This is confirmed by a professional ticketing agent on FlyerTalk: "I ticket these oneworld fares on a regular basis. I can confirm that if you change 4 flights in one go where the stopover points or routing changes, it's a single 125 USD charge, plus any fare/tax difference applicable."

**Per-person**: The fee is $125 per person per transaction. Two travelers making the same changes = $250 total.

#### Tier 3: Repricing Triggers (Fare Recalculation)

| Trigger | Cost | When |
|---------|------|------|
| Adding a continent | Fare recalculated to higher tier (e.g., DONE3 to DONE4) | Any time |
| Upgrading cabin class | Fare recalculated to higher cabin | Any time |
| Changes to first segment before departure | Fare difference charged if fare has increased | Pre-departure only |
| Ticketed point changes before departure | Fare difference charged if fare has increased | Pre-departure only |
| Downgrading cabin class | $125 fee, NO refund of fare difference | Any time |

### What Counts as a "Ticketed Point" Change

From the FlyerTalk User Guide wiki (pandaperth): "Ticketed point changes are changes to the list of airports in the itinerary -- dropping or adding points, reordering the list, and also changing stopovers to transits or vice versa."

This means:
- Changing dates = NOT a ticketed point change (free)
- Changing carrier on same route = NOT a ticketed point change (free)
- Changing a transit city (e.g., MIA to JFK on same origin-destination) = IS a ticketed point change ($125)
- Converting a transit to a stopover = IS a ticketed point change ($125)
- Dropping a segment = IS a ticketed point change ($125)

### Local Service Fees

Rule 3015 includes this clause: "Local service fees may apply on rebooking, rerouting, reissue or refund." This is the loophole that some airlines (notably QF and JL) exploit to charge fees for changes that should otherwise be free. See Section 5 for airline-specific behavior.

---

## 2. Pre-Departure vs Post-Departure Rules

### The Fare-Locking Distinction

This is the single most important strategic concept for RTW ticket management. The rules are fundamentally different depending on whether the first segment has been flown.

#### Before First Flight Departure

Rule 16(a)1 applies:

> **1.a**: Changes are permitted provided ticketed points remain the same. **If the first flight coupon is being changed**, and the fare level has increased since ticket issuance, the difference between the old and new fare will be charged. If the fare level has decreased since ticket issuance, no refund will apply.

> **1.b**: Changes to ticketed points are permitted at a charge of USD 125 per transaction. **If the fare level has increased since ticket issuance**, the difference between the old and new fare will also be charged. If the fare level has decreased since ticket issuance, no refund will apply.

**Translation**: Before you fly the first segment, the fare is "live". Two things can trigger repricing:
1. ANY change to the first segment (even just a date change)
2. ANY change to ticketed points (routing changes)

Both of these check whether the published fare has increased since booking. If it has, you pay the difference. If it has decreased, you get no refund.

**Real-world data point**: A FlyerTalk user changed their first segment date before flying and was hit with a repricing of thousands of dollars because the base fare had increased between booking and the change date.

#### After First Flight Departure

Rule 16(a)2 applies:

> **2.a**: Changes are permitted provided ticketed points remain the same. [No mention of fare difference or $125 fee]

> **2.b**: Changes to ticketed points are permitted at a charge of USD 125 per transaction. [No mention of fare difference]

**Translation**: After flying the first segment, the base fare is permanently locked. No repricing occurs for routing changes -- only the $125 fee applies for ticketed point changes, plus any tax/surcharge recalculation. Date changes remain free.

**The one exception**: Rule 16(a)2.d states that if rerouting results in an increase to the number of continents previously charged, the ticket shall be recalculated.

### Summary Matrix

| Timing | Date change | Carrier change (same route) | Routing change | First segment change |
|--------|------------|----------------------------|----------------|---------------------|
| **Before first flight** | Free (but first segment date = repricing risk) | Free | $125 + possible repricing | Repricing if fare increased |
| **After first flight** | Free | Free | $125 only (fare locked) | N/A (already flown) |

---

## 3. Types of Changes: What Triggers What

### Date/Time Changes

- **Fee**: Free at all times (pre- and post-departure)
- **Condition**: D-class must be available on the new date
- **Exception**: Changing the DATE of the first segment before flying it can trigger repricing (see Section 4)
- **Unlimited**: No limit on how many times you can change dates

### Carrier Changes (Same Route)

- **Fee**: Free at all times
- **Example**: Switching SIN-HKG from CX to MH (same airports, different airline)
- **Condition**: D-class must be available on the new carrier
- **Note**: The fare rules do not explicitly call this out as a separate change type. It falls under "changes permitted provided ticketed points remain the same" since the airports do not change.

### Ticketed Point Changes (Routing Changes)

- **Fee**: $125 per transaction
- **Examples**: Adding HKG as a stopover, changing transit from MIA to JFK, dropping the SYD-NRT segment
- **Pre-departure risk**: May also trigger fare repricing if the published fare has increased
- **Post-departure safety**: Only $125 + taxes recalculate (fare locked)

### Cabin Class Changes

**Upgrade (e.g., DONE4 to AONE4)**:
- No separate change fee
- Fare recalculated to the higher cabin
- Pay the difference between old and new fare

**Downgrade (e.g., DONE4 to LONE4)**:
- $125 change fee
- NO refund of fare difference
- Almost never worthwhile financially

### Continent Changes

**Adding a continent (e.g., DONE3 to DONE4)**:
- No separate change fee
- Full fare recalculation at current rates for the new product
- Can be $1,000+ fare increase depending on origin and timing
- Applies both pre- and post-departure

---

## 4. The Repricing Trigger: First Segment and Ticketed Points

### How Repricing Works

When repricing is triggered (pre-departure only), the GDS compares:
1. The fare stored on the ticket at time of original issuance
2. The current published fare for the same fare basis (e.g., DONE4) from the same origin

If the current fare is higher, you pay the difference. If lower, you get no refund. This is a one-way ratchet that only costs you money.

### The First Segment Rule

Rule 16(a)1.a is explicit: "If the first flight coupon is being changed, and the fare level has increased since ticket issuance, the difference between the old and new fare will be charged."

This means:
- Changing the DATE of segment 1 before flying = repricing risk
- Changing the CARRIER of segment 1 before flying = repricing risk (it is a change to the first flight coupon)
- Changing any OTHER segment's date before flying = NO repricing risk (as long as ticketed points remain the same)

### The "Fly First to Lock Fare" Strategy

This is the most important tactical advice for RTW ticket holders:

```
1. Book RTW ticket at current published fare
2. Fly first segment as soon as possible (even a short domestic hop)
3. Base fare is now permanently locked at the rate you booked
4. Make any routing changes needed ($125 per event, but no repricing)
5. Change dates freely (no fee)
6. Complete itinerary within 12 months of first departure
```

**Optimal first segment characteristics**:
- Short and cheap (minimize YQ and taxes)
- Available soon (fly within days of booking)
- On a low-YQ carrier (Finnair is ideal at ~$10 YQ; e.g., OSL-HEL)
- Practical (ideally useful for the actual itinerary)

**Risk quantification**: Fare increases are unpredictable. FlyerTalk reports document increases ranging from $500 to $2,000+ between filing periods. One ex-CAI ticket holder reported QF quoting AUD 3,733 and later AUD 10,065 for repricing after the Egyptian pound fare was discontinued.

### The "Segment 1 Date Change" Trap

Changing the date of the first segment before flying it is the riskiest action on an RTW ticket. The safest approach:
1. Book segment 1 with a date you can actually fly
2. Fly it
3. Then make all other changes

If you must change the first segment date before flying:
- Do it as close to the original booking date as possible (before the next fare filing period)
- Confirm with the agent that the base fare has not changed
- If the fare has increased, consider cancelling within 24 hours and rebooking (if within the US DOT 24-hour window)

---

## 5. Ticketing Airline Differences

### American Airlines (AA)

**Rating: Best for changes and flexibility**

- **Dedicated RTW desk**: +1-800-247-3247 (Mon-Fri 0700-2230 CT, Sat-Sun 0700-2000 CT)
- **International**: +1-817-267-1151
- **Real-time changes**: Agents validate and process changes during the call
- **Rule compliance**: Agents know and follow Rule 3015; will admit when wrong if you cite the applicable rule
- **Date changes**: Consistently free, no disputes
- **Routing changes**: $125 per transaction, correctly applied
- **Processing time**: Changes processed during the call (30-60 minutes typically)
- **Ticket number behavior**: AA issues new ticket numbers after most changes, including minor date changes and airline schedule changes. Not consistent -- some date changes retain the same ticket number while others generate a new one (see Section 6).
- **Best call time**: 7 AM DFW time (CT) for the most experienced agents

**Data point** (Dr. HFH, who does 3-4 DONE3s per year): "I only deal with the AA RTW desk. They're nice, knowledgeable, and have no problem admitting when they're wrong if you show/quote the applicable rule to them."

### Qantas (QF)

**Rating: Worst for changes -- avoid if possible**

- **The QF problem**: Since approximately 2024, QF has become the default ticketing airline for most oneworld Explorer tickets booked through the online tool, even when no QF segments are in the itinerary
- **Improper fee charging**: Multiple FlyerTalk reports of QF charging $125 for simple date changes that should be free under Rule 16(a)2.a
- **Agent knowledge**: Post-pandemic QF agents are described as "hopeless" with minimal understanding of oneworld Explorer rules
- **Call centers**: South Africa, Fiji, Auckland, Hobart (Tasmania, for QF top-tier status holders). System auto-directs; you cannot choose.
- **Date change disputes**: QF agents have told passengers "we don't care about the ticket rule for RTW ticket, he has to pay if changing"
- **Workaround**: QF Twitter/X DM team is more knowledgeable than phone agents. One user successfully pushed back by quoting Rule 16(a)2.a and got date changes processed at no charge
- **ACCC threat**: Mentioning the Australian Competition and Consumer Commission may provide leverage, given QF's recent ACCC fines for selling non-existent flights
- **Call-back pattern**: Changes often require 2-3 calls over multiple days. Agents encounter "fare not found" errors and need back-office support.
- **Schedule of fees**: QF's own published schedule states "No Change Booking Fees will apply for changes to a booking in Business or First, including date and time changes" -- contradicting their agents' behavior

**Successful QF change strategy** (from pandaperth, experienced RTW booker):
1. Have four windows open: fare rules (copy from purchase date), QF Conditions of Carriage, QF Schedule of Fees, and your change log
2. Quote the specific rule section that supports your position
3. If the agent refuses, HUCA (Hang Up, Call Again) -- different agents have different knowledge levels
4. QF Twitter DM team is generally better than the call center
5. Expect 2-3 day turnaround via Twitter DM

**Ex-CAI tickets**: QF has been particularly hostile toward tickets purchased from Cairo during the March 2024 Egyptian pound devaluation. Agents claim the fare was "undervalued" and refuse to follow normal change rules, demanding full repricing on routing changes that should cost only $125 post-departure.

### British Airways (BA)

**Rating: Slow but generally compliant**

- **Process**: Changes must go through the offline BA Fares Team
- **Turnaround**: Approximately 2 business days for validation and pricing
- **Email-based**: Many changes handled via email, creating a paper trail
- **Historically trained agents**: BA had well-trained RTW specialists, though post-pandemic staffing has reduced their availability
- **APD complications**: Any change that adds a UK departure adds Air Passenger Duty (~GBP 244-253 for premium class)
- **Not recommended for frequent changers**: The 2-day turnaround per change makes BA impractical for travelers who need iterative modifications

### Cathay Pacific (CX)

**Rating: Good, and sometimes generous**

- **Email-based booking**: CX offices handle RTW by email, creating documentation
- **Changes in person**: CX offices worldwide can process changes
- **Fee waiver reports**: One FlyerTalk user made 3 changes with CX, none charged -- including one that should have been charged $125. "Two of them shouldn't have been charged, but one actually should have and they still elected not to charge for it."
- **Good for complex itineraries**: CX historically handles multi-carrier international itineraries well on Amadeus

### Japan Airlines (JL)

**Rating: Charges service fees**

- **Service fees**: JL is known in the FlyerTalk community for charging local service fees on changes
- **Amount**: Different from the $125 routing change fee; amount varies
- **Rule basis**: Permitted under the "Local service fees may apply" clause in Rule 16

### Summary: Ticketing Airline Ranking for Change Flexibility

| Rank | Airline | Strengths | Weaknesses |
|------|---------|-----------|------------|
| 1 | **AA** | Dedicated desk, rule-compliant, real-time | Hours limited, 30-60 min calls |
| 2 | **CX** | Sometimes waives fees, email paper trail | Email turnaround varies |
| 3 | **BA** | Generally compliant | 2-day turnaround, slow for changes |
| 4 | **JL** | Competent | Service fees on changes |
| 5 | **QF** | Widespread OW tool default | Agents uninformed, disputes free changes, hostile to ex-CAI |

### Getting AA to Take Over a QF-Ticketed RTW

Multiple FlyerTalk users have attempted to transfer ticketing from QF to AA. Results are mixed:
- AA Twitter team has rejected takeover requests
- Some users report success by calling the AA RTW desk directly during the trip
- No guaranteed method exists -- AA generally requires the ticket to be on their stock from the start
- Best approach: Book through the AA RTW desk from the outset instead of using the oneworld online tool

---

## 6. Ticket Number Changes on Reissue

### The Problem

AA issues new e-ticket numbers after changes to RTW tickets. This is not limited to routing changes -- it can happen after:
- Date/time changes
- Airline schedule changes (even a 5-minute departure time shift)
- Flight number changes by the operating carrier

This creates problems for frequent flyer mileage credit claims.

### How Ticket Numbers Work

| Ticketing Airline | Number Prefix | Example |
|-------------------|---------------|---------|
| American Airlines (AA) | 001 | 001-1234567890 |
| Qatar Airways (QR) | 157 | 157-1234567890 |
| British Airways (BA) | 125 | 125-1234567890 |
| Qantas (QF) | 081 | 081-1234567890 |

Ticket numbers are 13 digits. If you see 14 digits, the last digit may be a check digit or coupon number, which can be ignored for mileage claim purposes.

### The Reissue Behavior

From FlyerTalk user SP0 (with multiple RTW tickets): "I've now discovered that AA is issuing new ticket numbers after each minor change, eg an airline changes a flight time or I change a flight date. I've been assuming that the ticket numbers initially sent to me are valid unless I made an actual routing change."

**Inconsistent behavior**: Dr. HFH reports: "I just (five days ago) made a date/time change on one of the flights on my current itinerary and retained the same ticket number, no reissue." This suggests the behavior is not uniform -- sometimes AA revalidates the existing ticket (same number), sometimes it reissues (new number).

### The Mileage Credit Problem

When a ticket is reissued with a new number:
- All segments flown AFTER the reissue are associated with the NEW ticket number
- Segments flown BEFORE the reissue remain associated with the OLD ticket number
- Mileage retro-credit claims must use the ticket number that was active when the segment was flown
- If you use the wrong ticket number, the claim will be rejected

**Real-world example**: One user had 5 different ticket numbers over the course of their RTW. Only ticket number 3 (out of 5) successfully processed mileage credit for Alaska Airlines segments. Each ticket number attempt showed different data in the retro-credit form.

### How to Track Ticket Numbers

**On AA.com**:
1. Go to "Manage Trips"
2. Click the small "i" icon -- a popup shows current ticket numbers
3. OR: Click "Show more" > "Print trip and receipt" for the complete itinerary with ticket number (note: this option may not appear for all bookings)

**On boarding passes**:
- Paper and electronic boarding passes include the ticket number
- If not explicitly printed, scan the barcode/QR code with a phone scanner -- the ticket number is embedded

**Email notifications from AA**:
- AA sends ticket numbers in change confirmation emails
- Known issue: AA sometimes only includes one passenger's ticket number when multiple passengers are on the booking

### Best Practices for Ticket Number Tracking

1. After EVERY change (even minor schedule adjustments by the airline), check and record the current ticket number
2. Note the date of each ticket number change
3. Keep a log mapping ticket numbers to the date ranges they were active
4. Save all boarding passes (paper or electronic) -- they show the ticket number valid at time of flight
5. For mileage retro-credit claims, use the ticket number that was active when the specific segment was flown, not necessarily the most recent ticket number

---

## 7. Upgrade and Downgrade Rules for Individual Segments

### The Whole-Ticket Rule

oneworld Explorer tickets are priced at a single cabin class for the entire ticket. You cannot mix cabins -- if even one segment is booked in business (D class), the entire ticket is priced as DONEx.

### Upgrading the Entire Ticket

- **Fee**: No separate change fee
- **Cost**: Pay the fare difference between old and new cabin tier (e.g., DONE4 to AONE4)
- **Timing**: Can be done at any time
- **Practical consideration**: Upgrading from DONE to AONE requires A-class availability on ALL segments, not just the ones you want to fly in first class

### Downgrading the Entire Ticket

- **Fee**: $125 change fee
- **Refund**: NO refund of fare difference
- **Practical implication**: This is almost never worthwhile financially. You pay $125 and lose the fare difference.

### Individual Segment Cabin Changes

**Not possible**: The RTW ticket is one cabin class. You cannot selectively upgrade or downgrade individual segments.

**Workaround for involuntary downgrades**: If an airline involuntarily downgrades you on one segment (e.g., aircraft swap to equipment without business class):

1. **Request rebooking**: Call the ticketing airline and request rebooking to a date/flight where D-class is available. This is a free date change if the route stays the same.
2. **Request carrier change**: If another oneworld carrier flies the route with D-class available, request a free carrier substitution.
3. **Accept and claim compensation**: Fly in economy on that segment and claim the fare difference under EU261 (EU departures) or US DOT rules (US departures/carriers).
4. **Post-departure upgrade**: If D-class opens up after ticketing but before the flight, some carriers will process a free upgrade:
   - CX has reissued with "NO ADC" (no additional charge) when D became available
   - AA desk can process post-ticketing upgrades
   - QF resists initially but has done it under pressure

### Premium Economy

There is no premium economy fare tier on oneworld Explorer. Economy (LONEx) ticket holders can pay a per-segment surcharge to fly premium economy on select carriers (AA, BA, CX, IB, JL, QF), shown as "-Q-" in the fare calculation.

---

## 8. Timeline: How Long Changes Take to Process

### By Ticketing Airline

| Airline | Date Change | Routing Change | Full Reissue |
|---------|------------|----------------|--------------|
| **AA RTW desk** | 15-60 minutes (during call) | 30-60 minutes (during call) | Same call |
| **QF call center** | 30 min - 3 days | 1-3 days (often requires escalation) | 1-3+ days |
| **QF Twitter DM** | 1-3 days (async messaging) | 2-5 days | 3-5+ days |
| **BA Fares Team** | ~2 business days | ~2 business days | ~2 business days |
| **CX (email)** | 1-3 business days | 1-3 business days | Variable |

### Post-Change Verification Timeline

After any change is processed:
- **GDS update**: Immediate in the ticketing airline's system
- **Cross-system PNR sync**: 24-48 hours for changes to propagate between Sabre (AA) and Amadeus (BA, CX, QR)
- **Online view (aa.com, ba.com)**: Minutes to hours; may show interim states
- **Ticket reissuance email**: Minutes to 24 hours from AA; inconsistent from QF
- **Operating carrier systems**: 24-48 hours for operating carriers to see the updated booking

### "Fare Not Found" Errors

QF agents frequently encounter "fare not found" errors when processing changes to RTW tickets, particularly:
- Ex-CAI tickets with discontinued fare filings
- Tickets with dummy dates being moved to actual dates
- Changes that require D-class revalidation across multiple carriers

These errors typically require back-office escalation and add 1-3 days to the process.

---

## 9. Best Practices for Minimizing Risk and Cost

### Before Booking

| # | Practice | Why |
|---|----------|-----|
| 1 | **Book through AA RTW desk, not the oneworld online tool** | Avoids QF as ticketing airline; AA agents handle changes better |
| 2 | **Choose a first segment you can fly immediately** | Locks fare before any increases |
| 3 | **Use dummy dates for uncertain segments** | Date changes are free; avoids commitment to dates you will change |
| 4 | **Save a copy of the fare rules on the day of purchase** | Evidence in case airline disputes the applicable rules later |
| 5 | **Plan routing carefully before booking** | Each routing change costs $125; planning avoids multiple transactions |

### At Time of Booking

| # | Practice | Why |
|---|----------|-----|
| 1 | **Record the PNR, e-ticket number, fare basis, and purchase date** | Essential for all future interactions |
| 2 | **Save the fare breakdown (base fare + taxes + YQ)** | AA.com only shows this briefly at purchase; may be unavailable later |
| 3 | **Fly the first segment within days of booking** | Permanently locks the base fare |
| 4 | **Bundle ALL known routing changes into one call** | Pay one $125 fee instead of multiple fees |

### During the Trip

| # | Practice | Why |
|---|----------|-----|
| 1 | **Check itinerary on AA.com weekly** | Airlines make silent schedule changes |
| 2 | **NEVER no-show without calling first** | All downstream segments cancelled (coupon-order rule) |
| 3 | **Call BEFORE departure time, not after** | Once departure passes, the no-show cascade triggers |
| 4 | **Record ticket numbers after every change** | AA may reissue with new number; old numbers needed for mileage claims |
| 5 | **Keep boarding passes (paper and electronic)** | Contains ticket number for mileage retro-credit |
| 6 | **Monitor D-class on upcoming segments** | If availability drops to 0, call to get protection or rebook early |
| 7 | **Verify full itinerary 24-48h after any change** | Automated systems can silently revert changes or desync |

### Change Cost Minimization

| Strategy | Savings |
|----------|---------|
| Bundle all routing changes into one call | Multiple $125 fees reduced to one |
| Use involuntary schedule changes as leverage | Fee waiver for bundled voluntary + involuntary changes |
| Change dates instead of routes where possible | Free vs $125 |
| Fly first segment before making any routing changes | Eliminates repricing risk entirely |
| Avoid QF as ticketing airline | Avoids disputes over free date changes |
| Call AA RTW desk at 7 AM CT | Best agent quality and shortest wait |

### Dealing with QF-Ticketed RTW Tickets

If you are stuck with QF as ticketing airline:

1. **Try QF Twitter/X DM first** (not the call center) -- more knowledgeable, but slower
2. **Quote the specific rule section** (e.g., "Rule 16(a)2.a states changes are permitted provided ticketed points remain the same, with no mention of a fee")
3. **Reference QF's own Schedule of Fees** ("No Change Booking Fees will apply for changes to a booking in Business or First")
4. **HUCA if the first agent refuses** -- different agents, different call centers, different outcomes
5. **Keep records of all interactions** -- dates, agent names, what was quoted
6. **Mention the ACCC** as a last resort (Australian Competition and Consumer Commission)
7. **Try to consolidate all changes** into a single interaction to minimize friction
8. **Expect 2-3 calls and 1-3 days** for what AA could do in 30 minutes

---

## 10. Implications for RTW Optimizer Tool

### Current Relevant Implementation

| Feature | Module | Status |
|---------|--------|--------|
| Rule 3015 validation | `rtw/rules/` | 31 rules across 10 files |
| Phone booking script (segment-by-segment) | `rtw/booking.py` | Implemented |
| GDS commands (Amadeus) | `rtw/booking.py` | Implemented |
| Married segment warnings | `rtw/booking.py` | Implemented |
| D-class availability verification | `rtw/verify/` | Implemented |

### Potential Enhancements

#### Change Impact Calculator
When a user proposes a change to an existing itinerary, the tool could:
- Classify the change type (date, carrier, routing, cabin, continent)
- Determine the fee ($0, $125, or repricing)
- Warn about repricing risk if the first segment has not been flown
- Calculate the tax/surcharge impact of the change (e.g., adding a UK departure = +GBP 244-253 APD)

#### Fare Lock Status Tracker
Track whether the first segment has been flown:
- If not flown: warn about all changes to first segment or ticketed points
- If flown: indicate that base fare is locked; only $125 + taxes apply for routing changes

#### Ticketing Airline Advisor
Based on the first segment carrier and user preferences:
- Recommend AA as ticketing airline for maximum change flexibility
- Warn if the oneworld online tool will default to QF
- Suggest booking by phone through AA RTW desk (+1-800-247-3247) instead of the online tool

#### Change Bundling Optimizer
When multiple changes are desired:
- Group all routing changes together as one transaction ($125 total, not $125 each)
- Separate date-only changes (free) from routing changes ($125)
- Suggest making date changes in a separate call from routing changes to avoid confusion

#### Ticket Number Change Tracker
After the `verify` command confirms D-class availability:
- Remind users to record their current ticket number
- After any recommended changes, note that the ticket number may change
- Include ticket number prefix reference (001=AA, 125=BA, 157=QR, 081=QF)

#### Dummy Date Strategy Support
The `build` and `scan-dates` commands could:
- Flag segments beyond the booking window as candidates for dummy dates
- Suggest nearby dates with known D-class availability as placeholders
- Note that date changes to these segments will be free once the first segment is flown

---

## Appendix A: Rule 3015 Section 16 — Full Text

> **16. VOLUNTARY CHANGES / REROUTING / PENALTIES**
>
> Fees as described below may be waived in case of certified death/illness of the passenger or passenger's immediate family member or accompanying passenger.
>
> Local service fees may apply on rebooking, rerouting, reissue or refund.
>
> **(a) Rebooking / Rerouting**
>
> **1. Prior to departure:**
> - a. Changes are permitted provided ticketed points remain the same. If the first flight coupon is being changed, and the fare level has increased since ticket issuance, the difference between the old and new fare will be charged. If the fare level has decreased since ticket issuance, no refund will apply.
> - b. Changes to ticketed points are permitted at a charge of USD 125 per transaction. If the fare level has increased since ticket issuance, the difference between the old and new fare will also be charged. If the fare level has decreased since ticket issuance, no refund will apply.
>
> **2. After departure:**
> - a. Changes are permitted provided ticketed points remain the same.
> - b. Changes to ticketed points are permitted at a charge of USD 125 per transaction.
> - c. No Show requires rebooking at a charge of USD 125.
> - d. If the rerouting results in an increase to the number of continents previously charged, the ticket shall be recalculated. Ticket may be reissued to any applicable Explorer fare validating all rules of the new fare except for restrictions on retroactive use. Rerouting fee applies when the resulting fare is less than or equal to the original fare. No refund applies. See Upgrading provisions when recalculation results in a new fare basis at a higher value.
>
> **(b) Cancellations and Refunds**
> - 1. After ticket issuance - Cancellation/No Show: Forfeit 10% of ticketed fare for Economy Class fares. Forfeit 5% of ticketed fare for Business/First Class fares.
> - 2. In case of refusal of official documents/entry permit/visa a full refund will be made.

---

## Appendix B: Decision Tree for Common Change Scenarios

```
Want to change something on your RTW ticket?
|
+-- What type of change?
    |
    +-- DATE/TIME only (same route, same carrier)
    |   |
    |   +-- Is it the first segment?
    |   |   |
    |   |   +-- YES: Have you flown it?
    |   |   |   +-- YES: N/A (already flown)
    |   |   |   +-- NO: FREE but REPRICING RISK if fare increased
    |   |   |
    |   |   +-- NO: FREE (no fee, no repricing risk)
    |   |
    |   +-- D-class available on new date?
    |       +-- YES: Proceed
    |       +-- NO: Check other dates or carriers
    |
    +-- CARRIER change (same airports)
    |   +-- FREE (no fee)
    |   +-- D-class must be available on new carrier
    |
    +-- ROUTING change (different airports/cities)
    |   |
    |   +-- Have you flown the first segment?
    |   |   |
    |   |   +-- YES: $125 per transaction. Fare locked. Only taxes recalculate.
    |   |   |
    |   |   +-- NO: $125 per transaction PLUS repricing risk if fare increased.
    |   |
    |   +-- Does the change add a continent?
    |       +-- YES: Full fare recalculation (no $125 fee, but fare difference payable)
    |       +-- NO: $125 only (post-departure) or $125 + possible repricing (pre-departure)
    |
    +-- CABIN change
    |   +-- UPGRADE: Pay fare difference (no $125 fee)
    |   +-- DOWNGRADE: $125 fee, NO refund
    |
    +-- CANCEL entirely
        +-- Pre-departure: Forfeit 5% (J/F) or 10% (Y) of fare + cancellation penalty
        +-- Post-departure: Likely $0 refund (point-to-point recalculation trap)
```

---

## Appendix C: Key Contacts

| Contact | Number | Hours |
|---------|--------|-------|
| **AA RTW Desk (US toll-free)** | +1-800-247-3247 | Mon-Fri 0700-2230 CT |
| **AA RTW Desk (international)** | +1-817-267-1151 | Same hours |
| **AA RTW Desk (weekend)** | Same numbers | Sat-Sun 0700-2000 CT |
| **QF Australia** | 13 13 13 | 24/7 |
| **QF New Zealand** | 0800 808 767 | 24/7 |
| **QF International** | +64 9 357 8900 | 24/7 |
| **QF Twitter/X DM** | @QantasAirways | Async, 1-3 day turnaround |
| **Skype** | Can call US toll-free numbers for free | Use for international calls to AA |

**Budget 30-60 minutes per AA call. Budget 1-3 days for QF interactions.**

---

## FlyerTalk Source Threads

| Thread | URL | Key Topics |
|--------|-----|------------|
| oneworld Explorer User Guide | [#2008084](https://www.flyertalk.com/forum/oneworld/2008084-oneworld-explorer-user-guide.html) | Master reference: all rules, dummy dates, fare lock, repricing |
| Terrible fare changing RTW ticket issued QF | [#2155530](https://www.flyertalk.com/forum/oneworld/2155530-terrible-fare-changing-rtw-ticket-issued-qf.html) | QF charging $125 per segment (incorrectly), per-transaction rule |
| RTW ticket through Qantas but they charging changing fee | [#2161590](https://www.flyertalk.com/forum/oneworld/2161590-rtw-ticket-through-qantas-but-they-charging-changing-fee.html) | QF date change disputes, Twitter DM workaround, ex-CAI fare fights |
| Tip: keep track of your RTW ticket numbers | [#2182642](https://www.flyertalk.com/forum/oneworld/2182642-tip-keep-track-your-rtw-ticket-numbers-they-may-change.html) | AA reissue behavior, mileage credit problems, ticket number tracking |
| RTW oneworld downgraded one flight, possible to re-upgrade | [#2170176](https://www.flyertalk.com/forum/oneworld/2170176-rtw-oneworld-downgraded-one-flight-possible-re-upgrade.html) | Involuntary downgrade handling, EU261, re-upgrade options |
| Point of origin and return - a question | [#1417740](https://www.flyertalk.com/forum/oneworld/1417740-point-origin-return-question.html) | Dropping last segment, fare lock, origin strategies |
| RTW ticket cancellation/refund | [#2183904](https://www.flyertalk.com/forum/oneworld/2183904-rtw-ticket-cancellation-refund.html) | Cancellation penalties, point-to-point recalculation trap |
| BA vs AA greater than 16 segments RTW | [#185111](https://www.flyertalk.com/forum/oneworld/185111-ba-vs-aa-greater-than-16-segments-rtw.html) | Sabre vs Amadeus, reissue mechanics, cross-system sync |
