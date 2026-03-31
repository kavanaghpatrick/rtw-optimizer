# Knowledge Base: Married Segments in RTW Ticketing

**Date**: 2026-03-30
**Sources**: FlyerTalk threads (1888592, 1330185, 1676534, 1914757, 1885075, 2152207, 2008084, 1511880, 1885940), existing KB articles (revenue management, GDS segment stitching, ExpertFlyer accuracy), Qantas AgencyConnect documentation, IATA/ATPCO fare rule data, RTW optimizer codebase (`rtw/rules/married.py`, `rtw/data/through_flights.yaml`)

---

## Table of Contents

1. [What Married Segments Are](#1-what-married-segments-are)
2. [Technical Mechanics in GDS Systems](#2-technical-mechanics-in-gds-systems)
3. [Which Airlines Enforce MSC Most Aggressively](#3-which-airlines-enforce-msc-most-aggressively)
4. [How MSC Affects D-Class on RTW Tickets](#4-how-msc-affects-d-class-on-rtw-tickets)
5. [Stopovers and MSC: The 24-Hour Question](#5-stopovers-and-msc-the-24-hour-question)
6. [Real Examples from FlyerTalk](#6-real-examples-from-flyertalk)
7. [Agent Workarounds and Techniques](#7-agent-workarounds-and-techniques)
8. [Implications for the RTW Optimizer](#8-implications-for-the-rtw-optimizer)

---

## 1. What Married Segments Are

### 1.1 Definition

Married Segment Control (MSC) is an airline inventory management mechanism that links two or more flight segments into a single unit for availability and pricing purposes. When segments are "married," the airline's revenue management system evaluates availability for the **combined origin-destination (O&D) journey**, not for each individual flight leg.

In practical terms: the airline decides how many seats to sell in a given booking class based on where the passenger is travelling *from* and *to*, not just which individual flight they are on.

### 1.2 Why Airlines Use MSC

Airlines use MSC to implement **Origin & Destination (O&D) revenue management** -- the practice of pricing seats based on the full journey context rather than a simple per-segment model.

The economic logic is straightforward:

- A passenger flying LAS-IAH as a standalone trip competes with other LAS-IAH travellers. The airline prices based on local demand.
- A passenger flying LAS-IAH-LHR (connecting) represents a different market. The airline might offer cheaper availability on the LAS-IAH leg to fill seats on the transatlantic LHR service, since the combined fare is higher.
- Without MSC, a savvy traveller could buy the cheap connecting fare LAS-IAH-LHR and skip the LHR leg, effectively getting a discounted LAS-IAH ticket. MSC prevents this by ensuring the cheaper availability **only exists** when both segments are booked together.

As one FlyerTalk poster explained:

> "Airlines do this to offer different things to different subsets of their market. E.g. they want to offer a lower priced fare for passengers buying a connecting ticket. If each segment could be separated, that lower pricing would also affect each segment."

### 1.3 The Fundamental Concept

The simplest way to understand married segments: **the same physical seat on the same physical flight can have different availability depending on what other flights are (or are not) on the same ticket.**

- Flight UA902 IAD-MUC: searched standalone = S0 (zero seats in S class)
- Flight UA902 IAD-MUC: searched as part of CLE-IAD-MUC = S9 (nine seats in S class)
- Flight UA902 IAD-MUC: paired with UA4796 from CLE = S1
- Flight UA902 IAD-MUC: paired with UA4319 from CLE = S0

The airline has not added or removed physical seats. It has simply decided that S-class availability on UA902 depends on the full passenger journey.

---

## 2. Technical Mechanics in GDS Systems

### 2.1 How MSC Works in the Booking System

When an agent (or automated system) queries availability, the GDS sends the request to the airline's inventory system. The response depends on the query structure:

**Standalone query** (single segment):
```
AN15MARIADMUC/DUALH    -- "What's available IAD-MUC on 15MAR on LH?"
```
Returns: availability based on IAD-MUC as the complete O&D.

**Connection query** (married journey):
```
AN15MARCLECLJ/DUA       -- "What's available CLE-CLJ on 15MAR on UA?"
```
Returns: availability where each segment is assessed as part of the CLE-CLJ O&D. The airline's inventory system decides which flight combinations to offer and at what fare classes.

The critical distinction: ExpertFlyer and similar tools perform **standalone queries** by default. They query each segment individually. The GDS agent's system, when building a PNR with connecting flights, performs **connection queries** that trigger MSC.

### 2.2 The Availability Stack and Where MSC Fits

From our ExpertFlyer accuracy KB, the availability filtering pipeline is:

```
Raw cabin inventory (physical seats)
  -> Booking class allocation (RM decision)
    -> GDS availability feed (what ExpertFlyer reads)      <-- standalone
      -> POS filter (country of sale)
        -> POC filter (country of ticket origin)
          -> O&D filter (origin-destination pair)           <-- MSC lives here
            -> Married segment control (connection context)
              -> Agency-level restrictions
                -> Fare-type restrictions (RTW vs revenue vs award)
                  = What the agent can actually book
```

MSC operates at layers 6-7 of this stack. ExpertFlyer reads layer 3. This is why EF-to-agent discrepancies are common.

### 2.3 Sabre vs Amadeus Handling

From our GDS segment stitching KB:

| Feature | Sabre (AA) | Amadeus (BA/CX/QR) |
|---------|-----------|-------------------|
| Married segment display | Asterisk (*) on married segments | Similar notation |
| Breaking married segments | "Carrier refuses cancellation" error | XE command -- sometimes works, sometimes not |
| Connection time threshold (domestic) | 4 hours (US domestic) triggers marriage | Varies by carrier |
| Connection time threshold (international) | 24 hours | 24 hours |
| MSC override capability | Very limited; requires carrier cooperation | Agent-dependent; inconsistent |

### 2.4 How Airlines Define Marriage Rules

Airlines can marry **any set of flights** into a saleable inventory unit with unique availability, provided they meet valid transfer rules. From the FlyerTalk lesson thread:

> "Airlines can (and do) marry any set of flights together into a saleable inventory unit, with unique inventory, provided that they meet valid transfer rules. For an international fare, that's a 24-hour window, leading to a lot of possible combinations."

The marriage is highly granular -- it can differ by:
- Specific flight number pairing (UA4796+UA902 = S1, but UA4319+UA902 = S0)
- Direction (outbound vs inbound)
- Day of week
- Booking class
- Season

### 2.5 The Inventory Model

The simplistic model of MSC is that married availability is the **intersection** of standalone availability. This is partly true but oversimplified:

> "The simplistic model of 'each segment has its standalone inventory, and married inventory is the set intersection of underlying inventory' is mostly accurate, and accounts for perhaps 90% of the influence of inventory. It is also the only rule for combinations of flights that have no married segment control. But any flight can have any inventory depending on how you search it."

In reality, airlines can set completely independent inventory for married combinations. A flight might have D0 standalone but D7 when married with a specific connecting flight -- or vice versa.

---

## 3. Which Airlines Enforce MSC Most Aggressively

### 3.1 Tier Ranking for oneworld RTW Impact

Based on community reports and our revenue management KB:

| Tier | Carrier | MSC Severity | Key Patterns |
|------|---------|-------------|--------------|
| **Aggressive** | Qatar Airways (QR) | High | Hub-married through DOH; limits A-class to 2 seats; D-class connections often blocked |
| **Aggressive** | Cathay Pacific (CX) | High | Hub-married through HKG; D-class may only be available on connecting itineraries |
| **Aggressive** | Lufthansa Group (LH/LX/OS) | High | "Insane married segment control on awards" -- applies to codeshare flights on UA/LH |
| **Significant** | Finnair (AY) | Medium-High | MSC on X, U, and F classes; applies to both awards and revenue fares |
| **Significant** | Malaysia Airlines (MH) | Medium | Lots of married segment issues, but workable with agent persistence |
| **Moderate** | American Airlines (AA) | Medium | MSC on domestic connections <4 hours; H-class (OWE business) can be affected |
| **Low** | British Airways (BA) | Low-Medium | MSC less aggressive, but BA restricts partner D-class on competitive routes (separate issue) |
| **Low** | Japan Airlines (JL) | Low-Medium | MSC less documented; primary issue is POC-based D-class blocking |

### 3.2 Qatar Airways (QR)

QR is the most problematic carrier for MSC on RTW tickets. Their Doha hub is a natural connection point for many RTW routings (EU_ME to Asia, EU_ME to SWP), and QR applies aggressive MSC to connections through DOH.

From the AA-desk-vs-ExpertFlyer thread:

> "HKG-DOH-MAN: EF shows D7/D4, agent sees no availability. Actually this one seems to be QR married seat logic -- I managed to recreate with a connecting flight in EF that this would only have D2."

This illustrates the paradox perfectly: D7 and D4 on the individual legs, but only D2 (or D0 to the agent) when searched as a connection.

QR also has an explicit anti-manipulation policy:

> "Bookings created out of date order sequence and/or with dummy segments, thereby obtaining a class that may otherwise not be available, will be considered as a POC violation." -- Qatar Airways agent guidelines

### 3.3 Cathay Pacific (CX)

CX enforces strong hub-married patterns through Hong Kong. D-class on CX flights that do not touch HKG may only exist as married availability through HKG connections.

Our `rtw/rules/married.py` already flags this: CX segments where neither origin nor destination is HKG get an INFO warning that D-class may only be available on connecting itineraries through HKG.

### 3.4 Lufthansa Group (LH/LX/OS)

The Lufthansa Group applies MSC not only to their own flights but to flights marketed under their codeshare agreements. This particularly affects UA codeshare flights used on Star Alliance awards, but the pattern is relevant to RTW planning when LH Group flights appear as intra-European connections.

From FlyerTalk:

> "MSC rules harshly suppress premium inventory on connections through high-value hubs" (referring to UA domestic hubs, but the same principle applies to LH's FRA/MUC hubs)

### 3.5 Finnair (AY)

Finnair applies MSC to award-relevant booking classes (X, U, F), which is notable because many carriers do not use MSC on award inventory. This directly affects RTW D-class availability on Finnair-operated flights.

The canonical example from FlyerTalk:

> "Yesterday I found there was plenty availability of business award ticket (U class) on HKG-HEL-Any major European city in both directions in almost every day in Jul/Aug 2024. Every flight has 4 tickets available. It can be seen on JL, CX, AA website as well as ExpertFlyer search. But there is no availability on direct HKG-HEL flight."

The availability only existed as married HKG-HEL-[European city] -- not on HKG-HEL alone. This is because Finnair wanted to offer award seats for the **HKG-Europe market** but not for the **HKG-HEL market** (where it could sell premium revenue tickets).

### 3.6 Malaysia Airlines (MH)

MH presents significant MSC challenges but, unlike QR, can often be worked through with agent persistence:

> "Malaysian Airlines: A bit of a PITA, and lots of married segment issues, but eventually the agent manages to 'dance' and confirm what AA sees -- it ends up being lots of unconfirmed messages first, but perseverance and they get through."

---

## 4. How MSC Affects D-Class on RTW Tickets

### 4.1 The Availability Paradox

The core problem for RTW ticket construction is what we call the **availability paradox**: individual segments show D-class available (D7, D9), but when combined as a connecting journey on the RTW ticket, availability drops to D0.

This manifests in three specific ways:

**Pattern 1: Hub connection suppression**
- EF shows: DOH-SIN D7, SIN-SYD D5
- Agent sees: DOH-SYD (via SIN) D0
- Cause: QR married segment control treats the connection as a single DOH-SYD O&D

**Pattern 2: Domestic feed suppression**
- EF shows: LAS-IAH D9, IAH-LHR D7
- Agent sees: LAS-LHR (via IAH) D0 on LAS-IAH leg
- Cause: LAS-IAH availability is "married" to the transatlantic segment; standalone LAS-IAH D-class is different from connecting LAS-IAH-LHR D-class

**Pattern 3: Award/RTW-specific suppression**
- EF shows: HKG-HEL U4 (4 award seats)
- Agent sees: HKG-HEL U0
- But: HKG-HEL-CDG U4 is available
- Cause: Finnair only releases U-class for the through-journey, not the local market

### 4.2 Why D-Class Is Particularly Vulnerable to MSC

D-class on a oneworld Explorer ticket represents some of the lowest revenue-per-seat values in business class. From our revenue management KB:

- The RTW base fare (~$5,000-8,000) is prorated across 8-16 segments
- Each D-class segment represents only ~$300-500 of revenue to the operating carrier
- A full-fare J-class ticket on the same route might be $3,000-8,000
- The RM computer sees D-class as barely above award tickets in revenue value

Airlines therefore have strong incentive to restrict D-class, and MSC provides a mechanism to do so selectively. They can offer D-class to passengers who book a "difficult" connecting journey (filling seats that might otherwise go empty) while blocking D-class for passengers on high-demand point-to-point routes.

### 4.3 ExpertFlyer Cannot Detect MSC

This is the fundamental limitation. ExpertFlyer queries availability for **individual segments** (standalone O&D). It does not query as a connected journey. Therefore:

- EF shows D7 on DOH-SIN = "7 D-class seats available for someone flying DOH-SIN"
- Agent queries DOH-SYD via SIN = "0 D-class seats available for someone connecting DOH-SIN-SYD"

ExpertFlyer does support searching **as a connection** (advanced mode), which can reveal MSC. One poster demonstrated this:

> "I managed to recreate with a connecting flight in EF that this would only have D2."

However, our automated scraper (`rtw/scraper/expertflyer.py`) queries segments individually, not as connections. This means the scraper's results inherently cannot account for MSC.

### 4.4 The Compounding Effect

MSC compounds with other availability restrictions:

| Restriction | Detectable by EF? | Impact on RTW D-Class |
|-------------|-------------------|----------------------|
| MSC (married segments) | Partial (advanced mode only) | Connection availability differs from standalone |
| POC (point of commencement) | No | Ex-Cairo/ex-Japan may see less D than ex-UK |
| POS (point of sale) | Yes (can change POS) | Minor effect compared to POC |
| Capacity limitation | No | Carrier can block D on any flight per Rule 3015 |
| Fare-type restriction | No | Some carriers block D specifically for RTW fares |

When MSC and POC restrictions combine, availability can be effectively zero even when EF shows D9.

---

## 5. Stopovers and MSC: The 24-Hour Question

### 5.1 The Standard Rule

The standard rule for international flights is that a connection becomes a **stopover** when the time between arrival and next departure exceeds **24 hours**. Connections under 24 hours are **transfers** (or transits).

MSC is triggered when segments fall within the transfer window (<24 hours). The theory is that converting a transit to a stopover (>24 hours) should break the marriage and cause each segment to be assessed independently.

### 5.2 Does Exceeding 24 Hours Always Break MSC?

**No.** This is one of the most important findings from the FlyerTalk research. While the 24-hour threshold is the standard rule, carriers do not always honour it:

> "I've also explored the married segments but even when they put in connection greater than 24 hours still don't get availability." -- pianoperson, FlyerTalk (re: QR connections through DOH)

This means that some carriers -- notably QR -- may apply MSC-like O&D control even when the connection formally qualifies as a stopover.

### 5.3 Why the 24-Hour Rule Fails Sometimes

Several factors can cause >24-hour connections to still be treated as married:

1. **O&D control is route-level, not connection-level**: The RM system may classify the passenger's full O&D (e.g., HKG-MAN) regardless of whether there is a stopover in DOH. The availability calculation considers the overall journey structure.

2. **PNR context**: When the agent adds a segment to an existing PNR, the GDS evaluates it in the context of all existing segments. Even with a >24hr gap, the system may recognise the overall O&D pattern.

3. **POC interaction**: The POC (origin city of the RTW) persists regardless of stopover placement. A carrier that restricts D-class based on POC will continue to do so whether there is a 4-hour or 4-day gap.

4. **Carrier-specific policies**: Some carriers simply apply broader O&D control that ignores the 24-hour threshold for certain booking classes.

### 5.4 When Stopovers Do Help

Converting a transit to a stopover **does** help in many cases, particularly:

- **Same-carrier domestic connections**: AA domestic connections <4 hours are almost always married; >4 hours often breaks the marriage; >24 hours nearly always breaks it.
- **Non-hub carriers**: Carriers without aggressive hub-MSC (e.g., BA intra-European connections) generally respect the 24-hour boundary.
- **Revenue fares on most carriers**: The 24-hour rule is more reliably observed on revenue fares than on deeply discounted classes like D.

### 5.5 The Stopover Trade-Off for RTW

Using a stopover to break MSC has costs under Rule 3015:

- Stopovers are limited (typically 2 per continent after departing origin on DONE4)
- Each stopover uses a finite resource on the ticket
- If the carrier does not respect the 24-hour threshold (as QR sometimes does not), you have consumed a stopover for nothing

**Recommendation**: Do not rely on converting transits to stopovers as an MSC workaround without confirming with the specific carrier that it will actually release D-class availability for the standalone segment.

### 5.6 FlyerTalk Case Study: LAS-IAH-LHR

A poster wanted to fly LAS-IAH (23 hours) IAH-LHR. The 23-hour gap was technically a transit (under 24 hours), and married segment availability applied:

> "LAS-IAH is showing married segment availability. As a standalone, the best avail is E8. Married with the IAH-LHR segment it's V9."

The twist: even though V9 was available as a married set, ua.com would not let the traveller book it because the website treated LAS-IAH as a separate standalone segment, showing only E8.

The follow-up was definitive:

> "The married segment availability is quite specific. It isn't possible to generally link to a TATL flight -- only specific combinations are allowed, otherwise the availability on the domestic leg drops back to standalone availability. If I was booking LAS-IAH-LON straight through, it would be available down to T class. If LAS-IAH is split in any way from the specific IAH-LON flight, it goes back up to U class."

This demonstrates that MSC is highly granular -- specific flight pairings matter, not just the general route.

---

## 6. Real Examples from FlyerTalk

### 6.1 Finnair: HKG-HEL Award Availability

**Thread**: Issues with Married Segment Control and oneworld Award (1888592)

**Scenario**: Traveller sees U4 (4 business award seats) on HKG-HEL-[European city] in every day of Jul/Aug. Every flight shows 4 tickets available on JL, CX, AA websites and ExpertFlyer. But HKG-HEL standalone shows zero availability.

**Diagnosis**: Finnair releases U-class only for the through-journey (HKG-Europe) and not for the local market (HKG-HEL). This is deliberate MSC -- Finnair protects the HKG-HEL market for revenue fares while stimulating the less-competitive HKG-Europe connecting market.

**Community response**: "Waitlisting for the fourth seat is the only tool."

**Finnair agent**: "I have a trick, let me try that..." -- suggesting internal tools can override MSC, but this is unreliable and status-dependent.

### 6.2 Qatar: HKG-DOH-MAN Phantom D-Class

**Thread**: AA RTW desk availability compared ExpertFlyer (2152207)

**Scenario**: ExpertFlyer shows D7 on HKG-DOH and D4 on DOH-MAN. But the AA RTW desk agent cannot book HKG-DOH-MAN with any D-class availability.

**Diagnosis**: QR married segment control evaluates HKG-MAN as the O&D. The through-journey availability is different (D2 in EF connection mode, D0 for the agent).

**Key quote**: "Actually this one seems to be QR married seat logic -- I managed to recreate with a connecting flight in EF that this would only have D2."

### 6.3 United: CLE-IAD-MUC S-Class Mystery

**Thread**: Married Segment Availability and Stopovers (1330185)

**Scenario**: Traveller searches CLE-CLJ (one fare), needs to connect through IAD and MUC. The exact same flight (UA902 IAD-MUC) shows different availability depending on how it is searched:

- Searched as CLE-CLJ: UA902 is S0
- Searched as IAD-MUC standalone: UA902 is S9
- Paired with UA4796 from CLE: UA902 is S1
- Paired with UA4319 from CLE: UA902 is S0
- Multi-city search CLE-IAD, IAD-CLJ: UA902 is S9

**Key insight**: Different search methods -- round trip, multi-city, standalone -- trigger different MSC evaluations. Multi-destination search sometimes bypasses MSC that round-trip search enforces.

### 6.4 United Awards: KOA-DEN-EWR

**Thread**: Married Segments Award Tickets (1676534)

**Scenario**: KOA-DEN-EWR shows XN9/X9 as a married journey. The same DEN-EWR segment shows XN0/X0 when searched separately. The entire itinerary successfully ticketed in XN.

**Significance**: This confirms MSC applies to award inventory, not just revenue fares. Some FlyerTalk posters initially claimed "married segments do not apply to [Star Alliance] award inventory," but multiple data points proved otherwise.

### 6.5 Melbourne-Singapore-Helsinki: Cross-Carrier MSC

**Thread**: Issues with Married Segment Control and oneworld Award (1888592)

**Scenario**: Traveller trying to fly MEL-SIN (Qantas) then SIN-HEL (Finnair) on a oneworld award. Can book SIN-HEL and MEL-SIN individually, but cannot book MEL-SIN-HEL as a connection unless there is a stopover (>24 hours) in Singapore.

**Significance**: MSC can apply **cross-carrier**, not just within a single airline. The GDS evaluates the full connection context even when different operating carriers are involved.

### 6.6 Revenue Fare Granularity: MID-IAH-SAN

**Thread**: Need a Lesson on Fare Quote and Married Segments (1914757)

**Scenario**: On a BKK-NRT-IAH-MID/MID-IAH-SAN itinerary, P-class is available on MID-IAH with a long IAH layover but only Z-class with a short layover -- even though the onward IAH-SAN segment shows P-class in both cases.

**Expert analysis**: The married segment inventory is "a really bad example for learning purposes because it's so complicated." The inventory displayed depends on:

1. The O&D of the search, not just the individual segment
2. Whether the GDS is using standalone or married availability
3. The fare construction logic (where fare breaks fall)
4. The specific flight number pairing
5. How multi-city search evaluates versus round-trip search

---

## 7. Agent Workarounds and Techniques

### 7.1 Segment-by-Segment Booking (Primary Defence)

The single most effective technique for avoiding MSC on RTW tickets is to **present each segment individually** to the agent, never as a connection:

> "Feed the agent ONE flight at a time. Do not present the full itinerary upfront. Wait for D-class confirmation before moving to the next segment. Never present two segments as a 'connection' -- this invites married-segment restrictions." -- Dr. HFH, FlyerTalk

This works because when the agent sells a standalone segment (e.g., `SS D1 QR303 15MAR HELDOH`), the GDS queries standalone availability, bypassing the O&D married evaluation.

**Limitation**: Once multiple segments are in the PNR and the agent saves/ends the record, the system may retroactively assess MSC on subsequent operations. This technique is most effective during initial PNR construction.

### 7.2 Multi-City Search Bypass

Multiple FlyerTalk reports confirm that multi-city (multi-destination) searches can bypass MSC that round-trip and simple O&D searches enforce:

> "The multiple-destinations fare is the 'correct' fare, complying with all the fare rules and consistent with availability, so it will ticket correctly and be honored."

> "Multi-destination search sometimes bypasses married segment control."

**How it works**: When searching multi-city, the booking engine may treat each city-pair as a separate O&D, querying standalone availability rather than connection availability. This effectively sidesteps the MSC evaluation.

**Risk level**: Low. FlyerTalk consensus is that tickets booked via multi-city search are legitimate and will be honoured, because the fare rules and availability are technically valid for each component.

### 7.3 The XE Command (Amadeus)

In Amadeus GDS, the `XE` (cancel segment) command can sometimes break married segments:

From our GDS stitching KB:

> "XE command sometimes works, sometimes not -- airline-dependent"
> "Segments with asterisk (*) indicates married in some displays; without asterisk = may be breakable"

The technique involves:
1. Booking the full connection (married)
2. Using `XE` to cancel one of the married segments
3. Re-selling the segment individually in the desired booking class

**Risks**: "A travel agent doing this will be fined and potentially stripped of booking authority. While airlines themselves might get away from the fine of each other, likely the system will cancel segments booked under such violation within minutes." This makes XE a high-risk manoeuvre that should only be attempted by experienced agents who understand the specific carrier's policies.

### 7.4 The Finnair "Trick"

Finnair platinum-line agents have access to an internal workaround for MSC on their flights:

> "I have a trick, let me try that... (silence, hacking away)... yeah, let me work on that and get back to you."

This is likely one of:
- Direct RM override to release inventory for a specific booking
- Use of an internal tool that bypasses the GDS MSC logic
- Manual seat allocation by the revenue management team

**Availability**: Only through Finnair's own agents, particularly platinum-tier service. Not accessible through partner airline desks.

### 7.5 Non-Sequential Segment Addition

Adding "easy" segments first, then inserting harder ones later, can influence how the RM system categorises new segment requests:

- The agent builds a PNR with segments that have generous D-class
- When the "hard" segment is added, the existing PNR context may cause the RM system to evaluate the new segment differently
- This can sometimes result in D-class being available when it would not have been for a fresh query

**Risk**: QR explicitly flags out-of-sequence construction as a POC violation. Other carriers may audit similarly.

### 7.6 Dummy Dates Strategy

Book with placeholder dates where D-class is available, then change to preferred dates later:

- Date changes are **free** on oneworld Explorer (as long as routing stays the same)
- This separates the "construct the routing" problem from the "find availability on specific dates" problem
- MSC may apply differently on different dates (e.g., Tuesday flights may have different married availability than Saturday flights)

### 7.7 Direct Carrier Inventory Requests

When MSC blocks D-class through standard channels, the escalation path is:

1. AA RTW desk contacts the oneworld support desk
2. OW support desk contacts the operating carrier's inventory control
3. The carrier decides whether to release space for this specific booking
4. Response comes back through the chain

**Timeline**: Same-day to 72 hours. Success varies by carrier.

### 7.8 Codeshare Flight Number Switch

The same physical flight may have different availability under different marketing carrier codes:

- QF12 LAX-SYD might show D0 due to QF MSC
- AA7387 (same flight, AA codeshare) might show D5

Ask the agent: "Can you check the codeshare number?"

### 7.9 Workaround Summary Table

| Technique | Effectiveness | Risk | Who Can Do It |
|-----------|--------------|------|---------------|
| Segment-by-segment booking | High | Low | Any agent |
| Multi-city search | Medium-High | Low | Agent or self-service |
| Dummy dates + change later | Medium | None | Any agent |
| Codeshare number check | Medium | None | Any agent |
| Non-sequential segment addition | Medium | Medium (QR flags this) | Experienced agent |
| XE command (Amadeus) | Variable | High (fines possible) | Experienced TA only |
| Direct carrier inventory request | Variable | None | AA RTW desk |
| Finnair platinum trick | Situational | None | AY agents only |

---

## 8. Implications for the RTW Optimizer

### 8.1 Current Implementation

The RTW optimizer already has basic married segment detection in two places:

**`rtw/rules/married.py` (MarriedSegmentRule)**:
- Detects CX segments not touching HKG (hub-connection married pattern)
- Detects through-flight split risks (via cities that overlap with stopover cities)
- Returns INFO-level warnings

**`rtw/verify/verifier.py`**:
- Detects married patterns when nonstop shows D0 but connecting flights show D>0
- References `_MARRIED_CHECK_HUBS` which includes QR/DOH

**`rtw/booking.py`**:
- Generates warnings for transit segments on the same day
- Flags through-flight via stops
- Warns about CX non-HKG married risk

### 8.2 Recommended Enhancements

Based on the research compiled here, several enhancements would improve married segment handling:

#### 8.2.1 Expand Hub-Carrier MSC Detection

Currently only CX/HKG is flagged. Add:

```python
_HUB_CARRIERS = {
    "CX": ("HKG", "Cathay Pacific often requires HKG stopover for D-class availability"),
    "QR": ("DOH", "Qatar Airways applies aggressive MSC through Doha hub"),
    "MH": ("KUL", "Malaysia Airlines has MSC issues through Kuala Lumpur hub"),
}
```

#### 8.2.2 Transit-Pair MSC Warning

When two consecutive segments have a connection time <24 hours and involve a known MSC-aggressive carrier, flag the risk:

```
WARNING: Segments 5-6 (HEL-DOH, DOH-SYD) connect in 3h45m on QR.
Qatar applies aggressive married segment control on DOH connections.
D-class shown by ExpertFlyer may not be available for this connection.
Consider: (a) adding a DOH stopover (uses 1 of your stopover allowance),
or (b) booking segments individually with the agent.
```

#### 8.2.3 Finnair Award-Class MSC Warning

When Finnair segments appear, specifically warn about U/X/F class MSC:

```
NOTE: Segments 2-3 (HKG-HEL, HEL-LHR) include Finnair.
AY applies married segment control on X, U, and F classes.
D-class on AY flights may only be available when booked as
part of a connecting journey (e.g., HKG-HEL-LHR), not standalone.
```

#### 8.2.4 Connection-Mode EF Verification

The most impactful improvement would be to add a **connection-mode query** to the ExpertFlyer scraper. When two consecutive segments connect within 24 hours, query them as a married pair in addition to standalone:

- Standalone: D7 on DOH-SIN, D5 on SIN-SYD
- Connection: D2 on DOH-SYD (via SIN)

Display both results with an MSC flag when they differ.

#### 8.2.5 Booking Script Enhancements

The phone booking script (`rtw/booking.py`) should include:

1. **MSC briefing**: When MSC-risky segments are detected, add a note: "Present each segment individually. Do NOT mention this as a connection."
2. **Escalation language**: "If D-class is not available for this segment, can you check the codeshare number? Can you try the operating carrier's inventory desk?"
3. **Stopover alternative**: When a transit through a known MSC hub is detected, note the option to convert to a stopover and assess the trade-off.

### 8.3 Verify Command Output

The `rtw verify` output should clearly distinguish between:

```
Segment 5: HEL-DOH (QR)
  ExpertFlyer (standalone): D7        -- individual segment availability
  ExpertFlyer (connection): D2        -- married with Seg 6 (DOH-SYD)
  MSC Risk: HIGH (QR DOH hub)
  Agent bookability: UNCERTAIN
```

This gives the user actionable information: the standalone D7 is encouraging, but the connection D2 (and high MSC risk) means the agent may not be able to book it without workarounds.

### 8.4 Known Limitations

| Factor | Our Tool Can Detect | Workaround |
|--------|-------------------|------------|
| Hub-carrier MSC patterns | Yes (CX, QR, MH) | Flag in warnings |
| Transit-pair MSC risk | Yes (connection time + carrier) | Flag in warnings |
| Standalone vs connection D-class | Partial (if we add connection queries) | Add EF connection mode |
| Cross-carrier MSC (e.g., QF+AY) | No | Document as known limitation |
| POC-MSC interaction | No | EF does not support POC |
| Carrier-specific flight-pair granularity | No | Too variable to model |
| Whether >24hr stopover breaks MSC | Carrier-dependent | Warn user to verify |

### 8.5 Decision Framework for Users

When the optimizer detects MSC risk, present this decision tree:

```
MSC risk detected on connection through [HUB]:

1. Is a stopover at [HUB] acceptable?
   YES -> Convert transit to stopover (uses 1 stopover allowance)
          Note: May still not break MSC on QR connections
   NO  -> Continue to step 2

2. Can you accept alternative routing?
   YES -> Search for routes avoiding [HUB]
   NO  -> Continue to step 3

3. Book with agent using segment-by-segment method
   -> Present each segment individually
   -> If blocked, ask agent to try codeshare numbers
   -> If still blocked, request direct carrier inventory release
   -> Last resort: waitlist and use dummy dates
```

---

## Appendix A: Key FlyerTalk Quotes

**On the nature of MSC:**
> "Married segments is a term to describe the fact that availability only exists when two or more segments are tied together. Separately, the segments may have zero availability." -- FlyerTalk, Finnair thread

**On the specificity of marriage rules:**
> "The married segment availability is quite specific. It isn't possible to generally link to a TATL flight -- only specific combinations are allowed, otherwise the availability on the domestic leg drops back to standalone availability." -- FlyerTalk, UA stopovers thread

**On multi-destination bypassing MSC:**
> "The multi-destination is not enforcing the married segments (for whatever reasons, in this case) hence the availability." -- WineCountryUA, FlyerTalk

**On breaking married segments in GDS:**
> "A travel agent doing this will be fined and potentially stripped of booking authority. Breaking married segments can only be done under special circumstances such as IRROPS." -- FlyerTalk, Amadeus thread

**On MSC for awards:**
> "Most airlines do this on revenue fares. Not all airlines do it on awards, but Finnair does." -- FlyerTalk, Finnair thread

**On the futility of >24hr workaround with QR:**
> "I've also explored the married segments but even when they put in connection greater than 24 hours still don't get availability." -- pianoperson, FlyerTalk

**On inventory being O&D-specific:**
> "Inventory is only defined for a specific origin, destination, and routing. Any flight can have any inventory depending on how you search it." -- findark, FlyerTalk

---

## Appendix B: FlyerTalk Source Threads

| Thread | URL | Key Topics |
|--------|-----|------------|
| Issues with married segment control and oneworld award | [1888592](https://www.flyertalk.com/forum/finnair-finnair-plus/1888592-issues-married-segment-control-oneworld-award.html) | Finnair MSC on X/U/F, HKG-HEL paradox, agent tricks |
| Married Segment Availability and Stopovers | [1330185](https://www.flyertalk.com/forum/united-airlines-mileageplus/1330185-married-segment-availability-stopovers.html) | 24-hour threshold, multi-city bypass, flight-pair granularity |
| Married Segments Award Tickets | [1676534](https://www.flyertalk.com/forum/united-airlines-mileageplus/1676534-married-segments-award-tickets.html) | MSC on award inventory, KOA-DEN-EWR example |
| Need a Lesson on Fare Quote and Married Segments | [1914757](https://www.flyertalk.com/forum/united-airlines-mileageplus/1914757-need-lesson-fare-quote-married-segments.html) | Revenue fare construction, Expert Mode, fare break logic |
| AA RTW desk availability vs ExpertFlyer | [2152207](https://www.flyertalk.com/forum/oneworld/2152207-aa-rtw-desk-availability-compared-expertflyer-ow-online-booking-tool.html) | QR DOH MSC, EF-to-agent discrepancies |
| Amadeus breaking married segments | [1885075](https://www.flyertalk.com/forum/online-travel-booking-bidding-agencies/1885075) | XE command, carrier-specific methods |
| Would Somebody Please Explain Married Segment Logic | [1511880](https://www.flyertalk.com/forum/delta-air-lines-skymiles/1511880-would-somebody-please-explain-married-segment-logic-me.html) | General MSC education |
| More award availability restricted by married segments | [1885940](https://www.flyertalk.com/forum/american-airlines-aadvantage/1885940-more-award-availability-restricted-married-segments-connections.html) | AA-specific MSC patterns |
| The oneworld Explorer User Guide | [2008084](https://www.flyertalk.com/forum/oneworld/2008084-oneworld-explorer-user-guide.html) | Comprehensive RTW construction guide |

## Appendix C: Related Knowledge Base Articles

| Article | Relevance |
|---------|-----------|
| [kb-revenue-management.md](kb-revenue-management.md) | Section 7 covers MSC in the context of RM; Section 10 covers carrier-specific behaviours |
| [kb-gds-segment-stitching.md](kb-gds-segment-stitching.md) | Section 7 covers agent tricks for breaking MSC; Amadeus XE command details |
| [kb-expertflyer-accuracy.md](kb-expertflyer-accuracy.md) | Section 4 covers MSC as a cause of EF-to-agent discrepancies |
| [kb-segment-dropping.md](kb-segment-dropping.md) | Dropping married segments has specific risks and penalties |

---

*Last updated: 2026-03-30*
