# Revenue Management and RTW Ticket Construction

Knowledge base on how airline revenue management (RM) systems affect oneworld Explorer ticket construction, and practical techniques for working within (and around) RM restrictions.

Synthesised from FlyerTalk community expertise (81+ posts across 4 threads), web research on airline inventory systems, and IATA/ATPCO fare rule documentation.

---

## Table of Contents

1. [Why ExpertFlyer D-Class Differs from What Agents Can Book](#1-why-expertflyer-d-class-differs-from-what-agents-can-book)
2. [Point of Sale (POS) vs Point of Commencement (POC)](#2-point-of-sale-pos-vs-point-of-commencement-poc)
3. [How Revenue Management Decides to Release or Block D-Class](#3-how-revenue-management-decides-to-release-or-block-d-class)
4. [Agent Techniques for Getting RM to Release Space](#4-agent-techniques-for-getting-rm-to-release-space)
5. [Direct Carrier-to-Carrier Inventory Requests](#5-direct-carrier-to-carrier-inventory-requests)
6. [Waitlisting in RTW Construction](#6-waitlisting-in-rtw-construction)
7. [Married Segment Control (MSC)](#7-married-segment-control-msc)
8. [Non-Sequential Segment Addition](#8-non-sequential-segment-addition)
9. [The Capacity Limitations Clause](#9-the-capacity-limitations-clause)
10. [Carrier-Specific Behaviours](#10-carrier-specific-behaviours)
11. [Practical Implications for the RTW Optimizer](#11-practical-implications-for-the-rtw-optimizer)

---

## 1. Why ExpertFlyer D-Class Differs from What Agents Can Book

ExpertFlyer queries GDS availability feeds (primarily Amadeus and Sabre) for raw booking class inventory counts. However, what it shows and what an RTW desk agent can actually book are often different things. The gap has multiple causes:

### 1.1 The Availability Stack

What you see in ExpertFlyer is **segment-level availability** -- how many seats the airline has filed as available in booking class D on that specific flight leg. What the RTW desk sees is filtered through multiple additional layers:

```
Raw cabin inventory (physical seats)
  -> Booking class allocation (RM decision)
    -> GDS availability feed (what ExpertFlyer reads)
      -> POS filter (country of sale)
        -> POC filter (country of ticket origin)
          -> O&D filter (origin-destination pair)
            -> Married segment control (connection context)
              -> Agency-level restrictions (who is selling)
                -> Fare-type restrictions (RTW vs revenue vs award)
                  = What the agent can actually book
```

### 1.2 Documented Discrepancy Patterns

From FlyerTalk data (thread: "AA RTW desk availability compared ExpertFlyer"):

| Route | EF Shows | Agent Sees | Likely Cause |
|-------|----------|------------|--------------|
| JFK-LAX (AA F) | A7/F9 | A0 | RTW fare-type block on AA transcontinental |
| SYD-HND (JL F) | A5 | A0 | JAL blocking A-class for AA-ticketed RTW |
| HKG-DOH-MAN (QR J) | D7/D4 | D0 | QR married segment control on connection |
| MAN-LHR-AUS (QF J) | D9 (US POS) | D0 (JP POC) | POC restriction for ex-Japan tickets |
| LAX-SYD (QF J) | D5 | D0 | QF capacity limitation on RTW fares |
| HND-DFW (JL J) | D9+ | D0 | JL blocking D-class for "cheap" RTW fares |

### 1.3 Key Quote

> "ExpertFlyer tool (and the aa.com / jal.com websites) show 'A' seats available for sale / use, but the AA RTW desk doesn't see that availability to book me into, so there is some other filter (beyond the geography/POS option that ExpertFlyer offers) that is being applied somewhere to prevent my taking those seats that show as available." -- littlevoices, FlyerTalk

### 1.4 The Fundamental Rule

**ExpertFlyer availability is necessary but not sufficient.** If EF shows D0, the agent definitely cannot book it. If EF shows D7, the agent _might_ be able to book it -- but there are at least 5 additional filters that can block the sale. Treat EF as an upper bound, not a guarantee.

---

## 2. Point of Sale (POS) vs Point of Commencement (POC)

### 2.1 Definitions

- **Point of Sale (POS)**: The country where the ticket is sold / the agency is located. Historically, this determined which availability and fares were displayed.
- **Point of Commencement (POC)**: The country where the passenger's journey actually begins (first departure point on the ticket). Also called "Point of Origin" (POO) in some airline systems.

### 2.2 How They Affect Inventory

Airlines file different availability by market. The same flight can show different D-class inventory depending on whether you query with US, UK, Japan, or Norway POS/POC:

> "Point of sale: UK/US: lots of DJI 999s across the board. Point of sale: Japan: Zero seats for days on end." -- littlevoices, FlyerTalk

> "Availability fare buckets, and thus fares, are linked to the Point of Sale. If you are in Germany, call up BA on their Germany telephone number, then you will get German Point of Sale availability, rather than (say) UK. Sometimes it makes no difference, sometimes it can make a huge difference." -- corporate-wage-slave, FlyerTalk

### 2.3 The BA POS-to-POC Transition

BA announced a transition from POS to POC-based availability in June 2025, with significant industry impact:

- **Before**: A UK travel agent booking a trip starting in Oslo would get UK-market availability
- **After**: The same booking would get Norwegian-market availability (based on where the journey starts)
- **NDC and direct channels** moved to POC first; GDS channels were planned to follow
- The initial cutover was **paused mid-transition** due to IT failures (only flexible fare classes were displaying)
- Trade partners received notice: "We have temporarily paused our transition from Point of Sale (POS) to Point of Commencement (POC)"

### 2.4 POC Implications for RTW Tickets

For oneworld Explorer tickets, POC = the origin city of the RTW itinerary:

- **Ex-Oslo (OSL) tickets**: Norwegian POC -- generally good availability, cheap base fare
- **Ex-Cairo (CAI) tickets**: Egyptian POC -- carriers have begun restricting availability (cheapest origin = most restricted)
- **Ex-Japan tickets**: Japanese POC -- mixed; some carriers restrict, but fare is competitive
- **Ex-London (LHR) tickets**: UK POC -- generally good availability, expensive base fare + APD

> "Some OW carriers seem to be restricting ex-CAI itineraries quite a bit, ex-Japan is the 2nd most lucrative so could be the next target for POO restrictions. Everything below C seems to be targeted." -- FlyerTalk poster

### 2.5 ExpertFlyer POS vs POC

**Critical limitation**: ExpertFlyer supports POS filtering but does **not** support POC filtering. Changing the "country" dropdown in EF changes POS, not POC.

> "Point of Sale (POS) =/= Point of Commencement (POC). I don't believe EF supports POC yet." -- izzik, FlyerTalk

> "Looking for availability based on POC seems limited to those with an Amadeus terminal access (not even Sabre)." -- FlyerTalk poster

This means ExpertFlyer can show D7 with every POS setting you try, but the agent still sees D0 because the POC-based restriction is invisible to ExpertFlyer.

### 2.6 POC Violation Rules

Airlines actively police POC abuse:

> "Bookings created out of date order sequence and/or with dummy segments, thereby obtaining a class that may otherwise not be available, will be considered as a POC violation." -- Qatar Airways agent guidelines

Penalties for agents caught manipulating POC include fines and potential loss of booking authority.

---

## 3. How Revenue Management Decides to Release or Block D-Class

### 3.1 The EMSR Model

Airlines use **Expected Marginal Seat Revenue (EMSR)** models to decide how many seats to offer in each booking class. The core trade-off:

- Sell a D-class seat now at the RTW prorate rate (~$200-400 per segment)
- OR protect that seat for a later full-fare business class sale (~$2,000-8,000)

The RM computer continuously recalculates this trade-off based on:
- Historical booking curves for the route
- Current load factor
- Days until departure
- Forecast demand by fare class
- Competitive dynamics

### 3.2 Nested Inventory

Airlines use **nested booking class hierarchies**. For business class on most carriers:

```
J (full flex business)     -- highest priority, always open if cabin has seats
C (flexible business)      -- protected after J
D (discounted/RTW business)-- protected after C and J
I (deep discount business) -- protected after D, C, J
```

"Nesting" means closing D also closes everything below it (I, etc.), but closing I does not close D. The RM system sets **booking limits** for each class, and D-class is typically one of the lower-priority business buckets.

### 3.3 Why D-Class Is Especially Vulnerable

D-class on a oneworld Explorer ticket represents one of the lowest revenue-per-seat values in business class:

- The RTW base fare (~$5,000-8,000) is prorated across 8-16 segments
- Each D-class segment might represent only $300-500 of revenue to the operating carrier
- A full-fare J-class ticket on the same route might be $3,000-8,000
- The RM computer sees D-class as barely above award tickets in revenue value

> "The last agent told me it might be that JL does not want to give away D class seats for those 'relatively cheap' RTW fares, not sure how valid this statement is though..." -- FlyerTalk poster

This is entirely valid. Airlines have **explicit capacity limitation clauses** in the RTW fare rules allowing them to restrict D-class at their discretion.

### 3.4 The Time Dimension

D-class availability typically follows a pattern:

1. **Far out (330+ days)**: Often available -- flights are empty, RM is generous
2. **6-9 months out**: Starts tightening on popular routes as RM protects for higher fares
3. **3-6 months out**: Most restricted period -- RM expects full-fare bookings
4. **2-4 weeks out**: Sometimes reopens -- if the flight is not filling, RM releases lower buckets
5. **Close-in (1-7 days)**: Can open dramatically if the flight has unsold seats

> "About 8 days out I was finally able to get MIA-BOS-LAX as an alternative route, and the agent was able to see exactly what ExpertFlyer saw." -- littlevoices, FlyerTalk

### 3.5 O&D (Origin-Destination) Control

Modern RM systems do not just manage availability per flight leg. They manage it per **origin-destination pair**. This means:

- D-class LHR-SYD nonstop might show D5
- D-class LHR-HKG-SYD (via CX connection) might show D0 on the same HKG-SYD leg
- The RM computer values the through-passenger differently from the local passenger

This is the mechanism behind married segment control and explains why connecting itineraries often see less availability than point-to-point searches.

---

## 4. Agent Techniques for Getting RM to Release Space

### 4.1 The Escalation Path

When an agent sees availability blocked despite EF showing seats:

1. **Try the codeshare**: If JL blocks D-class, try the AA codeshare number for the same flight (AA7387 instead of QF12, for example). Different marketing carriers sometimes have different availability.

2. **Contact the operating carrier directly**: The selling carrier (e.g., AA RTW desk) can contact the operating carrier's (e.g., QF's) inventory desk to request space.

3. **Request a one-off space release**: As one experienced poster noted:
   > "There is a procedure by which there's someone they can ask to open the space for you, on a one-off basis."

4. **Use the inter-carrier liaison**: AA has human liaisons with each oneworld carrier. The agent can escalate to the JL or QF liaison to request specific space.
   > "AA has liaisons (i.e., humans) with other OneWorld carriers. You could ask the AA RTW agent if s/he would raise the issue with the JL liaison." -- Dr. HFH, FlyerTalk

5. **Try a different ticketing carrier**: An RTW ticket issued by BA (Amadeus) may see different availability than one issued by AA (Sabre). Some passengers have had success switching their ticketing carrier.
   > "I finally gave up and started using my own Sabre access to book RTWs -- at least that way it's my own issue if I can't book it." -- FlyerTalk poster

### 4.2 The "Dance" Technique

For carriers with complex married segment logic (especially MH), experienced agents use a persistence technique:

> "Malaysian airlines: A bit of a PITA, and lots of married segment issues, but eventually the agent manages to 'dance' and confirm what AA sees -- it ends up being lots of unconfirmed messages first, but perseverance and they get through." -- littlevoices, FlyerTalk

This involves repeatedly querying availability in different configurations until the system accepts the booking.

### 4.3 Dummy Dates Strategy

A well-established technique for RTW construction:

1. Book with placeholder dates for segments beyond the booking window (or where availability is tight)
2. Date changes are free on oneworld Explorer as long as routing stays the same
3. Change to preferred dates as availability opens closer to departure

This is not technically an RM workaround -- it is a legitimate use of the fare rules. But it separates the "build the routing" problem from the "find availability on specific dates" problem.

### 4.4 Persistence and Timing

> "AA advise me to keep calling back to see if it comes available." -- pianoperson, FlyerTalk

This is frustrating but reflects reality. RM systems are dynamic:
- Other passengers cancel, releasing space
- RM models update forecasts and may open D-class
- Close-in releases happen when flights are not filling
- Calling at different times of day can yield different results (RM updates batch-process at certain times)

### 4.5 Alternative Routing

When a specific segment is blocked, finding an alternative route is often more productive than fighting the RM system:

- LAX-SYD blocked on QF? Try SFO-SYD, or LAX-AKL-SYD
- DFW-LHR blocked on BA? Try the AA metal, or route via ORD
- HND-DFW blocked on JL? Try NRT-LAX on JL plus a domestic connection

---

## 5. Direct Carrier-to-Carrier Inventory Requests

### 5.1 How It Works

When the ticketing carrier (e.g., AA) cannot see D-class for an operating carrier (e.g., QF), the agents can make a **direct inventory request**:

1. The AA RTW desk contacts the oneworld support desk
2. The OW support desk contacts QF's inventory control
3. QF decides whether to release space for this specific booking
4. The response comes back through the chain

> "They have got the OW support desk to speak to QF and ask for a seat and according to the agents QF have said no." -- pianoperson, FlyerTalk

### 5.2 Timeline

This process is **not instant**. It can take:
- Same-day for simple requests
- 24-72 hours when it needs to go through pricing/inventory teams
- Up to a week for complex multi-carrier situations

BA's India-based change team refers amendments to the Pricing Team, which can take up to 72 hours per change request.

### 5.3 Success Factors

Direct requests are more likely to succeed when:
- The flight is lightly loaded (carrier has little to lose)
- The request is close to departure (unsold seats have zero value after departure)
- The passenger has status or a relationship with the operating carrier
- It is a single seat (less RM impact than 3+ seats)

---

## 6. Waitlisting in RTW Construction

### 6.1 How Waitlisting Works for RTW

When D-class is not currently available, some GDS agents can place the passenger on a **waitlist** for the desired booking class:

> "The agent seemed to be familiar with this and mentioned it was just blocking, but that I could waitlist. In my case the flight is in 3 months time." -- FlyerTalk poster, re: JFK-LAX A-class

### 6.2 When Waitlists Clear

Waitlists may clear when:
- Another passenger cancels a D-class booking
- The RM system opens more D-class inventory (e.g., as departure approaches and the flight is not full)
- The airline runs a batch process that reassesses allocations

### 6.3 Limitations

- Not all carriers support waitlisting for D-class on RTW fares
- Waitlist clearance is not guaranteed
- The passenger typically needs to have the RTW ticket already issued with a placeholder segment
- Waitlisting is carrier-specific -- some clear automatically, others require manual intervention

### 6.4 Strategy

For RTW construction, waitlisting is best used as a **background strategy**:
1. Book the segment on an available date (or with a dummy date)
2. Place a waitlist request for the preferred date/flight
3. If the waitlist clears, make a free date change
4. If it does not clear, fly the booked alternative

---

## 7. Married Segment Control (MSC)

### 7.1 What It Is

Married Segment Control is an airline inventory mechanism that links two or more flight segments into a single unit for pricing and availability purposes. When segments are "married," availability is assessed for the **entire O&D journey**, not individual legs.

### 7.2 How It Affects RTW Tickets

MSC is triggered when segments are within 24 hours of each other (connection vs. stopover threshold):

| Scenario | MSC Active? | Impact |
|----------|------------|--------|
| LHR-HKG, then HKG-SYD 4 hours later | Yes | Availability assessed as LHR-SYD |
| LHR-HKG, then HKG-SYD 3 days later | No | Each segment assessed independently |
| HKG-DOH, then DOH-MAN same day | Yes | Availability assessed as HKG-MAN via DOH |

### 7.3 The Availability Paradox

MSC creates situations where individual segments show availability but the connection does not:

> "HKG-DOH-MAN: EF shows D7/D4, agent sees no availability. Actually this one seems to be QR married seat logic -- I managed to recreate with a connecting flight in EF that this would only have D2." -- littlevoices, FlyerTalk

This is because the RM system values the through-journey differently. A passenger connecting HKG-DOH-MAN competes with higher-revenue passengers on the full O&D, whereas a local DOH-MAN passenger is assessed against local demand only.

### 7.4 MSC Cannot Be Broken

> "A travel agent doing this [breaking married segments] will be fined and potentially stripped of booking authority. While airlines themselves might get away from the fine of each other, likely the system will cancel segments booked under such violation within minutes. Breaking married segments can only be done under special circumstances such as IRROPS." -- FlyerTalk poster

### 7.5 Workarounds

The only legitimate way to avoid MSC is to **increase connection time beyond 24 hours** (making the connection a stopover instead):

- This changes the trip from MSC-controlled to segment-level availability
- It uses a stopover, which is limited (3 per continent on DONE4)
- Sometimes even >24hr connections are still assessed as married (carrier-dependent)

> "I've also explored the married segments but even when they put in connection greater than 24 hours still don't get availability." -- pianoperson, FlyerTalk

---

## 8. Non-Sequential Segment Addition

### 8.1 The Theory

When building an RTW itinerary, the order in which segments are added to the PNR can affect availability:

- Adding "easy" segments first (routes with generous D-class) fills the itinerary skeleton
- Inserting harder segments later may bypass some O&D restrictions
- The RM system assesses each segment addition in the context of the existing PNR

### 8.2 How It Tricks RM

When a segment is added to an existing PNR, the airline's inventory system receives the full PNR context (all existing segments) along with the new segment request. The O&D algorithm then evaluates:

- Is this a local segment or part of a connection?
- What is the likely O&D for this passenger?
- What revenue class should apply?

By controlling which segments already exist when you add the "hard" segment, you can influence how the RM system categorises the request.

### 8.3 Risks

> "Bookings created out of date order sequence and/or with dummy segments, thereby obtaining a class that may otherwise not be available, will be considered as a POC violation." -- Qatar Airways guidelines

Airlines are aware of this technique. Some will:
- Audit bookings for out-of-sequence construction
- Cancel segments booked under suspected manipulation
- Flag the booking for review at the rate desk

### 8.4 Practical Reality

For RTW tickets, non-sequential construction is common and largely tolerated because:
- Segments genuinely need to be added at different times (booking windows, date changes)
- The fare is a fixed RTW fare, not an O&D-priced itinerary
- Agents frequently modify RTW itineraries throughout the travel period
- The $125 change fee covers any routing modification

The risk is primarily on connecting flights where MSC would apply.

---

## 9. The Capacity Limitations Clause

The IATA Rule 3015 fare rules for oneworld Explorer include an explicit capacity limitation:

> "THE CARRIER SHALL LIMIT THE NUMBER OF PASSENGERS CARRIED ON ANY ONE FLIGHT ON FARES GOVERNED BY THIS RULE AND SUCH FARES WILL NOT NECESSARILY BE AVAILABLE ON ALL FLIGHTS. THE NUMBER OF SEATS WHICH THE CARRIER SHALL MAKE AVAILABLE ON A GIVEN FLIGHT WILL BE DETERMINED BY THE CARRIER'S BEST JUDGEMENT."

This clause gives each operating carrier unilateral authority to block D-class (or A-class) on any flight for any reason. It is the ultimate "get-out clause" that explains why even when all other filters are satisfied, a carrier can simply refuse to sell D-class.

> "The airlines do not need to make available all D class availability for RTW tickets, there is a get-out clause. I have only actually seen this used by AA in practice." -- dave_sทh, FlyerTalk

---

## 10. Carrier-Specific Behaviours

### 10.1 Japan Airlines (JL)

- **Most problematic** for AA-ticketed RTW fares
- Systematically blocks A-class (and sometimes D-class) for AA RTW desk
- ExpertFlyer shows A4/A5 on JL metal, but AA agents cannot book
- Agents report: "JL only releases seats to us 3 months out"
- Sometimes available when checking the AA codeshare flight number
- The OW online booking tool sometimes shows availability the AA desk cannot access

### 10.2 Qantas (QF)

- "Notoriously stingy with D-class availability" (per carriers.yaml)
- Heavy married segment control on connections via SYD
- Will sometimes release space on direct carrier-to-carrier request, but often says no
- Try AA codeshare numbers (AA7387 for QF12) as an alternative

### 10.3 Qatar Airways (QR)

- Aggressive married segment control on DOH connections
- Limits A-class to 2 seats on most flights (even months out)
- F6 seats often do not convert to A-class availability
- MSC on QR connections is a major trap -- search QR segments independently in EF

### 10.4 British Airways (BA)

- Very high YQ (surcharges)
- I-class vs D-class are different inventory buckets
- D-class (RTW) is generally more available than I-class (awards)
- BA's IT system underwent major POS-to-POC migration with multiple failures
- BA change ticket team (India-based) refers to Pricing Team -- 72hr turnaround
- "Brief flash of D class availability" observed -- availability is volatile

### 10.5 American Airlines (AA)

- Uses **H class** for OWE business (not D)
- Blocks A/D-class on transcontinental routes (JFK-LAX, JFK-SFO) for RTW fares
- Agents sometimes cannot see availability on their own metal
- "There is a procedure by which there's someone they can ask to open the space for you, on a one-off basis"
- MIA-JFK-LAX routing particularly problematic; MIA-BOS-LAX often available as alternative

### 10.6 Cathay Pacific (CX)

- Pattern observed: when F2/A1, the AA desk cannot see the final A seat
- CX website may show "Business Essential" availability that the AA desk cannot access
- Sometimes unable to see JL availability for cross-carrier connections through HKG

### 10.7 Malaysia Airlines (MH)

- Lots of married segment issues but can be worked through with persistence
- The agent "dance" -- repeated unconfirmed messages eventually resolve
- More cooperative than JL/QF on releasing space

### 10.8 Finnair (AY)

- Uses MSC on X, U, and F classes
- Agents have reported "I have a trick, let me try that..." suggesting internal workarounds exist
- Very low YQ makes AY segments highly desirable

---

## 11. Practical Implications for the RTW Optimizer

### 11.1 For the `verify` Command

The current ExpertFlyer-based D-class verification provides a **necessary but insufficient** check. When displaying results:

- **D > 0 in EF**: "D-class detected -- confirm with agent (RM restrictions may apply)"
- **D = 0 in EF**: "No D-class -- consider alternatives"
- Flag segments with known problematic carriers (JL, QF, QR) with additional warnings
- Note connected segments (<24hrs) that will trigger MSC

### 11.2 For the `booking` Command

The booking script generator should include:

- **POS/POC awareness**: Note which POS/POC the EF check used; remind agent to verify
- **MSC warnings**: Flag connections <24hrs that may have different availability than shown
- **Escalation language**: Include phrases like "Can you check the codeshare number?" and "Can you escalate to the carrier liaison?"
- **Alternative routing suggestions**: When a problematic carrier/route is detected
- **Waitlist option**: Remind agent that waitlisting is available if preferred date is blocked

### 11.3 For the `analyze` Command

The analysis pipeline should account for RM risk in segment assessment:

- **High-risk segments**: JL first class, QF long-haul, QR connections, AA transcontinental
- **Low-risk segments**: AY intra-Europe, AA domestic (single seats), CX when not F2/A1
- **Timing advice**: Suggest when to book vs. wait based on the RM release patterns

### 11.4 Known Limitations of EF-Based Verification

| Factor | EF Can Detect? | Workaround |
|--------|---------------|------------|
| Raw D-class count | Yes | -- |
| POS restriction | Partial (can change POS) | Try multiple POS settings |
| POC restriction | **No** | Must verify with agent |
| Married segment | Partial (can simulate connection) | Search as connection, not point-to-point |
| Agency restriction | **No** | Must verify with agent |
| Fare-type block | **No** | Must verify with agent |
| Capacity limitation | **No** | Must verify with agent |
| Codeshare availability | Sometimes | Try both operating and marketing carrier codes |

---

## Sources

### FlyerTalk Threads (Scraped)

- [AA RTW desk availability compared ExpertFlyer & OW online booking tool](https://www.flyertalk.com/forum/oneworld/2152207-aa-rtw-desk-availability-compared-expertflyer-ow-online-booking-tool.html) -- 81 posts across 5 pages
- [ExpertFlyer vs BA](https://www.flyertalk.com/forum/oneworld/2213364-expertflyer-vs-ba.html) -- 29 posts across 3 pages
- [BA moving from Point of Sale to Point of Commencement](https://www.flyertalk.com/forum/british-airways-british-airways-club/2197169-ba-moving-point-sale-point-commencement.html) -- 136 posts across 3 pages
- [ExpertFlyer going downhill -- am I doing something wrong?](https://www.flyertalk.com/forum/oneworld/2180862-expertflyer-going-downhill-am-i-doing-something-wrong.html) -- 15 posts (1 page)

### FlyerTalk Threads (Referenced)

- [The Oneworld Explorer User Guide](https://www.flyertalk.com/forum/oneworld/2008084-oneworld-explorer-user-guide.html)
- [The oneworld explorer ticket FAQs](https://www.flyertalk.com/forum/oneworld/338667-oneworld-explorer-ticket-faqs.html)
- [Would Somebody Please Explain Married Segment Logic to Me?](https://www.flyertalk.com/forum/delta-air-lines-skymiles/1511880-would-somebody-please-explain-married-segment-logic-me.html)
- [More award availability restricted by married segments](https://www.flyertalk.com/forum/american-airlines-aadvantage/1885940-more-award-availability-restricted-married-segments-connections.html)

### Industry Sources

- [Qantas Agency Connect: O&D Availability and Married Flights](https://www.qantas.com/agencyconnect/gb/en/policy-and-guidelines/book-and-service/married-flights.html)
- [Qatar Airways: Point of Commencement Guidelines](https://www.qatarairways.com/tradeportal/en/bookingnticketing/POC-Guidelines.html)
- [Travel Industry Blog: What Is a Married Segment?](https://www.travel-industry-blog.com/travel-technology/married-segment/)
- [Amadeus Service Hub: Round the World Booking Options](https://servicehub.amadeus.com/c/portal/view-solution/875457/round-the-world-booking-options-rtw/ct-)
- [ATPCO: Fare Rules Categories](https://atpco.net/single-blog/what-are-atpco-fare-rules-categories/)
- [MIT: Airline Network Seat Inventory Control](https://dspace.mit.edu/handle/1721.1/68123)
- [Takeflite: Nested Inventory, Pricing & Revenue Management](https://tflite.com/airline-software/Passenger-Service-System/price-revenue-management/)

### Raw Scraped Data

- `/tmp/ft_aa_desk_vs_ef.json` -- 81 posts
- `/tmp/ft_ef_vs_ba.json` -- 29 posts
- `/tmp/ft_ba_pos_poc.json` -- 136 posts
- `/tmp/ft_ef_downhill.json` -- 15 posts
