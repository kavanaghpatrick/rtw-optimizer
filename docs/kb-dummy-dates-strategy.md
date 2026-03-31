# The Dummy Dates Booking Strategy for oneworld Explorer RTW Tickets

Knowledge base covering the dummy dates strategy -- the technique of booking RTW segments with placeholder dates and changing them later for free. This is one of the most important operational strategies for RTW ticket construction.

**Sources**: FlyerTalk oneworld Explorer User Guide (#2008084, pages 1-15), oneworld Explorer Ticket FAQs (#338667), segment dropping KB, GDS stitching KB, revenue management KB, segment bank strategy, Oslo origin KB, host agency research (Propeller Travel / Daniel), IATA Rule 3015 (April 2025 update), real-world booking data points.

---

## 1. What the Dummy Dates Strategy Is

### The Core Concept

The dummy dates strategy is the practice of booking oneworld Explorer RTW segments with **placeholder dates** -- dates you have no intention of flying -- with the plan to change them to your actual preferred dates later, for free. It separates the problem of "building a valid routing" from the problem of "finding D-class availability on specific dates."

### Why It Exists: The 365-Day Booking Window

Airlines sell seats up to **approximately 355-365 days** before departure. This creates a fundamental problem for RTW tickets:

- An RTW ticket spans up to **12 months** of travel from first departure
- At booking time, flights toward the end of the itinerary may be **12+ months in the future**
- Those flights simply do not exist in any airline's reservation system yet

**Example**: You book in January 2026 for a trip starting February 2026. Your final segments in October-December 2026 cannot be booked on their actual dates because airlines have not opened those flights for sale yet.

### The Solution

Book those far-future segments on dates that ARE within the current booking window -- even if those dates are meaningless for your actual travel plans. Then change the dates for free once the real dates become available in the airline's system.

> "We plan to start the trip in late February/early March 2024, thus book every flight after GRU with dummy dates and rebook them as they become available."
> -- pye1201, FlyerTalk User Guide thread

> "Everything after the dotted line is for travel after March 2025, so not on the fare calendar. The dummy dates for the remaining 14 segments were booked into available dates/flight numbers over the subsequent 18 days remaining on the fare calendar."
> -- dvs7310, FlyerTalk User Guide thread (first-time xONEx booking report)

---

## 2. How It Works

### Step-by-Step Process

```
1. Design your full RTW routing (all cities, carriers, directions)
2. Identify which segments can be booked on real dates (within booking window)
3. For remaining segments, pick ANY available date within the booking window
4. Book the entire itinerary -- real dates on near-term segments, dummy dates on far-future ones
5. Fly your first segment to lock the fare
6. As real dates enter the booking window, call to change dummy dates to actual dates
7. Repeat until all segments have real dates
```

### What Counts as a "Dummy Date"

A dummy date is any date assigned to a segment purely to satisfy the GDS requirement that every segment must have a date. It could be:

- A date within the next few weeks (the nearest available D-class date)
- A date clustered with other dummy segments (e.g., 14 segments crammed into an 18-day window)
- Any date where the specific flight/carrier has D-class inventory

The key requirement: **D-class must be available on the dummy date for the GDS to confirm the segment.** You cannot book a segment with D0 (zero availability) even as a placeholder.

### Practical Example

dvs7310 on FlyerTalk reported booking a DONE3 with AA:

| Segment Group | Date Treatment | Notes |
|---------------|---------------|-------|
| Segments 1-2 | Real dates (Jan 2025) | Within booking window, actual travel dates |
| Segments 3-16 | Dummy dates (Feb 2025) | All 14 segments crammed into 18 days at end of fare calendar |

The traveler's actual trip would run January through August 2025, but segments 3-16 were all assigned dates in early February 2025 because that was the edge of the booking window at the time of purchase.

---

## 3. The Repricing Rules: What Is Free vs What Triggers a Reprice

This is the **most critical distinction** in RTW ticket management. Getting it wrong can cost thousands.

### Tier 1: Free Changes (No Fee, No Repricing)

| Change | Conditions |
|--------|------------|
| **Date/time changes on any segment except the first** | Unlimited, any number of times, subject to D-class availability |
| **Carrier substitution on the same route** | E.g., switching SIN-HKG from CX to MH (same airports) |
| **Flight number changes** | Earlier/later flight, same day, same carrier, same route |

**This is the foundation of the entire dummy dates strategy.** Date changes to non-first segments are free and unlimited, both before and after departure.

### Tier 2: $125 Fee Changes (Routing Changes)

| Change | Fee |
|--------|-----|
| Add/remove a city | $125 per event |
| Reorder cities | $125 per event |
| Stopover-to-transit conversion (or vice versa) | $125 per event |
| Drop a segment | $125 per event |
| Add a segment | $125 per event |

The $125 fee is per change **event**, not per segment. Bundle all routing changes into one phone call to pay only once.

### Tier 3: Repricing Triggers (Fare Recalculation)

| Change | Risk |
|--------|------|
| **Changing the first segment (date, carrier, or route) before flying it** | HIGH -- triggers full fare recalculation |
| **Changing ticketed points before first departure** | May trigger repricing if fare has increased |
| **Adding a continent** | Automatic repricing (e.g., DONE3 to DONE4) |
| **Upgrading cabin class** | Automatic repricing |

### The Critical Pre-Departure vs Post-Departure Distinction

From the FlyerTalk wiki and confirmed by pandaperth:

> "If you are making the changes before departure, then changes to ticketed points or to the first segment (even just a simple date change) will result in a re-price if the fare has increased."

> "Ticketed point changes are changes to the list of airports in the itinerary -- dropping or adding points, reordering the list, and also changing stopovers to transits or vice versa."

**But date changes to non-first segments do NOT trigger repricing, even before departure.** This was explicitly confirmed:

> "A change of date to any segment other than the first one should not trigger a reprice, even before departure."
> -- iwillflytheworld, confirmed by pandaperth as "Correct."

This means the dummy dates strategy is safe: you can change dates on segments 2-16 freely at any time, before or after flying the first segment.

---

## 4. The Fare-Locking Rule: Fly First Segment to Lock Base Fare Permanently

### How It Works

The oneworld Explorer fare is a published IATA fare subject to periodic increases. The base fare is not permanently locked until the first coupon is "lifted" (i.e., the first flight is flown).

| Timing | Change first segment | Change later segments |
|--------|---------------------|----------------------|
| **Before first flight** | DANGEROUS -- triggers repricing | Dates: free. Routing: $125 (but may reprice if fare increased) |
| **After first flight** | N/A (already flown) | Dates: free. Routing: $125. **Base fare locked permanently.** |

### The Strategy

1. Book with the first segment on a date you can **actually fly**
2. Fly it as soon as possible, even if only a short domestic hop
3. The base fare is now permanently locked at the rate you booked
4. All subsequent changes (dates, routing) only recalculate taxes and surcharges, not the base fare

### Why This Matters for Dummy Dates

The fare-locking rule means you should **never** use a dummy date on your first segment. The first segment must have a real, flyable date because:

1. Changing the first segment date before flying triggers repricing
2. You need to fly it to lock the fare before making other changes
3. Fare increases between booking and flying can cost $500-2,000+

**Real-world report**: A FlyerTalk user changed their first segment date before flying and was hit with a $6,000+ repricing because the base fare had increased between original booking and the change date.

### Optimal First Segment

Choose a first segment that is:
- **Short and cheap**: Minimize YQ and taxes on this fare-locking flight
- **Available immediately**: Fly within days of booking
- **On a low-YQ carrier**: Finnair AY (~$10 YQ) is ideal, e.g., OSL-HEL
- **On a date you can actually fly**: Never a dummy date

### The 12-Month Clock

Flying the first segment starts the 12-month validity clock. All remaining segments must be completed within 12 months of this date. The exact interpretation: if your first flight is June 1, your last segment must commence by May 31 of the following year (one FlyerTalk data point from a BA-ticketed itinerary).

---

## 5. Optimal Strategy: Which Segments Get Real Dates, Which Get Dummies

### Decision Framework

| Segment | Date Strategy | Reason |
|---------|---------------|--------|
| **First segment** | REAL date, fly immediately | Locks fare. NEVER use a dummy date here. |
| **Segments with fixed travel dates** (weddings, events, meetings) | REAL date if within booking window | These are non-negotiable dates |
| **High-demand segments** (JL to Japan, QR Qsuite) | REAL date if within window, dummy if not | Secure D-class on the best date available |
| **Easy segments** (AY intra-Europe, AA domestic) | Dummy date, change later | D-class is generally abundant; no rush |
| **Far-future segments** (beyond 355-day window) | Dummy date, mandatory | Cannot book real dates -- flights don't exist yet |

### Practical Booking Sequence

**Phase 1: Initial Booking (Day 0)**

1. Book segment 1 with a real date (fly within 1-2 weeks)
2. Book segments 2-3 with real dates if within the booking window and dates are known
3. Book remaining segments with dummy dates, clustering them into available D-class dates near the edge of the booking window
4. Pay for the ticket; it is now issued with all segments confirmed

**Phase 2: Fare Locking (Week 1-2)**

5. Fly segment 1 to permanently lock the base fare
6. You now have 12 months to complete the itinerary

**Phase 3: Rolling Date Changes (Ongoing)**

7. As real travel dates enter the booking window (~330-355 days out), call to change dummy dates to actual dates
8. Each call is free (date change only, no routing change)
9. Check D-class availability before calling; have backup dates ready
10. Repeat until all segments have real dates

### The "Cascade" Problem

dvs7310 identified a practical challenge with dummy dates:

> "I can't wrap my head around how and when I change the dates to something that is wanted and is available. [...] If we want to travel BKK-HKG around 18 February, I'll be able to see that next week. But I can't change the subsequent 13 segments at that time because they're off the calendar."

The issue: when you change one segment's date, the GDS may require subsequent segments to also have dates that come after it chronologically. If those later segments are still on dummy dates that are BEFORE the new date, you may need to adjust them simultaneously.

**Solution**: When changing a dummy date to a real date, also move the immediately-following segment's dummy date to a date that is chronologically after the new real date. Work forward through the itinerary incrementally.

### Waitlisting + Dummy Dates

A hybrid approach:

1. Book the segment on a dummy date (any available D-class date)
2. Place a waitlist request for the preferred date/flight
3. If the waitlist clears, make a free date change
4. If it does not clear, adjust the date closer to departure when more D-class opens

---

## 6. GDS Handling of Dummy Dates and Far-Future Segments

### Sabre (AA RTW Desk)

| Feature | Behavior |
|---------|----------|
| Booking window | ~355 days (varies by carrier) |
| Open-dated segments | **Cannot e-ticket open segments** |
| Dummy date segments | Must have a specific date with confirmed D-class |
| Chronological ordering | Segments should be in date order; out-of-order may require agent override |
| Reissue for date changes | Agent processes a reissue; new e-ticket coupons generated |

Sabre's inability to e-ticket open-dated segments is why dummy dates are required rather than simply leaving segments "open." Every segment on a Sabre-issued e-ticket must have a specific date.

### Amadeus (BA, CX, QR, Travel Agents)

| Feature | Behavior |
|---------|----------|
| Booking window | ~355 days (varies by carrier) |
| Open-dated segments | **Can e-ticket with open dates** (more flexible than Sabre) |
| Dummy date segments | Can use specific dates OR open dates |
| Reissue for date changes | More robust cross-carrier revalidation |
| Dummy dates handling | "Dummy dates more robust" per GDS comparison |

Amadeus's ability to handle open-dated segments means travel agents using Amadeus have slightly more flexibility. From the FlyerTalk FAQs thread, the nuance is carrier-specific:

> "CX, JL and AA are the only OW carriers who do not support open dated sectors on e-tickets."
> -- Bukhara, FlyerTalk FAQs

However, even CX's rules are more permissive than believed. From a travel agent who reviewed the CX e-ticketing guide:

> "What they cannot do is issue an entirely open-dated ticket. Their e-ticketing guidelines explicitly state that the minimum requirement to be able to issue an e-ticket is for one booked (confirmed or waitlisted) segment, which doesn't need to be the first segment. All other segments can be issued open."

In practice, most agents still prefer specific dummy dates over open dates because:
- Open dates can cause complications with some carriers' inventory systems
- A specific date requires confirmed D-class, proving the route is bookable
- Schedule changes on dummy-date segments are a minor nuisance; open segments have no schedule to change

### GDS Command Flow for Date Changes

When changing a dummy date to a real date, the agent:

```
1. Pulls up the PNR
2. Cancels the existing segment (XE command in Amadeus)
3. Sells a new segment on the desired date (SS command)
4. Reprices (FXP) -- should show no base fare change
5. Reissues the ticket (TTP)
6. Verifies new e-ticket coupons match the updated itinerary
```

### PNR Synchronization After Date Changes

After any date change:
- Allow 24-48 hours for cross-system synchronization
- Verify the full itinerary on AA.com or by calling the ticketing airline
- Check that the operating carrier shows the updated date in their system
- Do not assume the change is complete until verified in both the ticketing and operating carrier's systems

---

## 7. Risks and Edge Cases

### Risk 1: D-Class Unavailability on the Dummy Date

To book a segment, D-class must be available on the selected date. If the only available dates within the booking window have D0, you cannot book that segment at all.

**Mitigation**: Use a different carrier on the same route, or pick a date with D-class even if it means a tight clustering of dummy dates.

### Risk 2: Changing Dummy to Real Date -- No D-Class on Preferred Date

When the time comes to change the dummy date to your real travel date, D-class may not be available.

**Mitigations**:
- Monitor D-class availability using ExpertFlyer alerts as the date enters the booking window
- Book exactly 330-355 days out when initial D-class allocation is released
- Have 2-3 backup dates ready
- Consider alternative carriers on the same route (carrier change is free if route stays the same)
- Use the waitlisting approach described in section 5

### Risk 3: The First-Segment Trap

Changing the date of the first segment before flying it triggers a full repricing. If you accidentally book segment 1 with a dummy date and then need to change it, you are exposed to any fare increase since booking.

**Mitigation**: Never use a dummy date on segment 1. Book it on a real, flyable date. Fly it immediately.

### Risk 4: Fare Calendar vs Ticket Validity Confusion

dvs7310 documented confusion between:
- **Fare calendar** (booking window): How far out airlines sell seats (~355 days)
- **Ticket validity**: 12 months from first departure

These are independent concepts. The ticket validity is 12 months from when you fly segment 1. The booking window is how far out you can see and book specific flights. Your ticket can be valid for travel in November 2026 even though in January 2026 you cannot yet see November flights.

### Risk 5: QF Ticketing Issues

Multiple FlyerTalk reports indicate Qantas agents struggle with dummy date changes and RTW ticket modifications:

> "QF only allows change in the 12 months of issue date."
> -- kayzng, FlyerTalk (unconfirmed; may reflect agent confusion)

The Rule 3015 standard is 12 months from first departure, not from issue date. However, QF agents have been reported to apply incorrect rules. If your ticket is issued on QF stock, date changes beyond QF's interpreted window may be refused.

**Mitigation**: Issue on AA stock (AA RTW desk is the most competent for modifications) or through a knowledgeable travel agent on Amadeus.

### Risk 6: Schedule Changes Interfering with Dummy Dates

Airlines regularly change schedules. A flight you booked on a dummy date may be cancelled, retimed, or renumbered. Since you were never planning to fly that date, this should not matter -- but the airline may proactively rebook you or send confusing notifications.

**Mitigation**: Ignore schedule change notifications for dummy-date segments. When you change to your real date, the current schedule will be used.

### Risk 7: Chronological Date Order in the GDS

Some GDS implementations require segments to be in chronological order. If you change segment 5 from a dummy date of February 15 to a real date of July 20, but segment 6 still has a dummy date of February 16, the system may reject the change or require segment 6 to also be updated.

**Mitigation**: When changing one segment, be prepared to also adjust the subsequent dummy date to maintain chronological ordering. Work forward through the itinerary.

### Risk 8: Cross-Carrier PNR Sync

When a dummy date is changed, the PNR update must propagate from the ticketing carrier's GDS to all operating carriers. This can take 24-48 hours and may fail silently.

**Mitigation**: After every date change, verify the updated itinerary with both the ticketing carrier and the operating carrier. Do not assume success without verification.

---

## 8. How Specialist Agents Use This Operationally

### Daniel at Propeller Travel (UK)

Daniel (DK) at Propeller Travel is the most frequently cited specialist agent on FlyerTalk for RTW ticketing. His approach to dummy dates is embedded in his standard RTW booking workflow:

1. **Build the full routing first**: Validate against Rule 3015, optimize carriers for YQ, plan segment ordering
2. **Identify the booking window boundary**: Determine which segments fall within and beyond the ~355-day window
3. **Book in-window segments on optimal dates**: Target D-class on the best available dates for segments within the window
4. **Assign dummy dates to far-future segments**: Cluster them on available D-class dates near the booking window edge
5. **Lock the fare**: Ensure the first segment is booked on a real, near-term date; instruct the client to fly it immediately
6. **Rolling date management**: As new dates enter the booking window, rebook dummy segments onto real dates

Daniel's pricing for an RTW ticket is GBP 80 for initial issuance and GBP 35 per subsequent reissue (date change). For a 16-segment itinerary where 10 segments use dummy dates, the total cost of rolling date changes would be approximately GBP 80 + (10 x GBP 35) = GBP 430 (~$540).

### AA RTW Desk Agents

The AA RTW desk (+1-800-247-3247, Mon-Fri 0700-2230 CT) handles dummy date changes as routine:

- Date changes are processed in real-time during the call
- Each change involves cancelling the old segment and selling the new one in Sabre
- The agent reissues the ticket after each set of changes
- Budget 15-30 minutes per call for simple date changes, longer for multiple segments

### The "One at a Time" Approach

Experienced agents recommend feeding segments to the booking agent one at a time, confirming D-class on each before proceeding. For dummy dates, this same principle applies:

1. Tell the agent which segment you want to change
2. Specify the new date and preferred flight
3. Wait for D-class confirmation
4. Move to the next segment if changing multiple
5. Have the agent reissue the ticket once all changes are made

Bundling multiple date changes into one call saves time and avoids repeated reissue processing.

---

## 9. Implications for Our RTW Optimizer Tool

### Current Implementation Gaps

The RTW optimizer currently has no awareness of the dummy dates strategy. The following enhancements would add significant value:

### Enhancement 1: Booking Window Awareness

Given a first-departure date, flag which segments fall beyond the ~355-day booking window and would require dummy dates.

```
Segment 1:  OSL-HEL  15 Mar 2026  [WITHIN WINDOW - book real date]
Segment 2:  HEL-DOH  18 Mar 2026  [WITHIN WINDOW - book real date]
...
Segment 10: SYD-NRT  15 Jan 2027  [BEYOND WINDOW - requires dummy date]
Segment 11: NRT-LAX  20 Jan 2027  [BEYOND WINDOW - requires dummy date]
```

### Enhancement 2: Dummy Date Assignment

For segments beyond the booking window, suggest optimal dummy dates:
- Pick dates near the booking window edge where D-class is likely available
- Cluster dummy-date segments within a 2-3 week window
- Ensure chronological ordering is maintained
- Flag carrier-specific booking window limits (JL opens exactly 360 days out; BA closer to 355)

### Enhancement 3: Rolling Date Change Calendar

Generate a timeline of when each dummy-date segment's real travel date will enter the booking window, so the user knows when to call for date changes:

```
Date Change Schedule:
  2026-04-10: BKK-HKG segment (Aug 2026 travel) enters window - call to change
  2026-05-15: HKG-NRT segment (Sep 2026 travel) enters window - call to change
  2026-06-20: NRT-LAX segment (Oct 2026 travel) enters window - call to change
```

### Enhancement 4: Fare Lock Warning

In the booking script output, prominently flag:
- "SEGMENT 1 MUST BE FLOWN IMMEDIATELY TO LOCK FARE"
- "DO NOT USE A DUMMY DATE ON SEGMENT 1"
- "Fare increase risk if segment 1 date is changed before flying"

### Enhancement 5: D-Class Monitoring Integration

For segments on dummy dates, integrate with the `scan-dates` command to monitor D-class availability as real dates enter the booking window. Alert the user when D-class opens on their preferred real date.

### Enhancement 6: Phone Script Adaptation

The `booking` command's phone script should include dummy-date context:

```
"I'd like to book segment 10, NRT to LAX on Japan Airlines.
 The date will be January 15 -- this is a placeholder date.
 I'll call back to change it to the actual date once the
 schedule opens for that period."
```

This sets expectations with the agent and prevents confusion.

---

## 10. Summary: The Dummy Dates Playbook

### The Rules in One Table

| Rule | Detail |
|------|--------|
| Date changes are **free** | No fee, no repricing (except first segment before departure) |
| First segment: **never a dummy** | Book on a real date, fly immediately to lock fare |
| D-class must exist on dummy date | Cannot book without confirmed inventory |
| 12-month validity from first flight | All segments must complete within this window |
| Routing stays the same | Date changes only; city/carrier changes are separate ($125) |
| Carrier substitution is free | Same route, different carrier = no fee |
| Chronological order required | Dummy dates must maintain segment sequence |
| Verify after every change | Cross-system PNR sync can fail silently |

### The Optimal Workflow

```
BOOK
  1. Design routing with all cities, carriers, directions
  2. Book segment 1 on a real date you can fly this week
  3. Book near-term segments on real dates
  4. Book far-future segments on dummy dates (any available D-class)
  5. Issue ticket

LOCK
  6. Fly segment 1 within days of booking
  7. Base fare is now permanently locked

ROLL
  8. Monitor booking window for when real dates become available
  9. Call AA RTW desk / TA to change dummy dates to real dates
  10. Change one segment or batch multiple per call
  11. Verify the full itinerary after each change
  12. Repeat until all segments have real dates

FLY
  13. All segments now have real dates with confirmed D-class
  14. Complete the trip within 12 months of segment 1
```

### Common Mistakes to Avoid

| Mistake | Consequence | Prevention |
|---------|-------------|------------|
| Dummy date on segment 1 | Must change it later, triggering repricing | Always book segment 1 on a real, flyable date |
| Changing segment 1 date before flying | Full fare recalculation (up to $6,000+ reported) | Fly segment 1 immediately |
| Assuming D-class will be available when changing | May get stuck with no availability on real date | Monitor with ExpertFlyer alerts; have backup dates |
| Ignoring chronological ordering | GDS may reject date change | Adjust subsequent dummy dates to maintain order |
| Not verifying after changes | PNR sync may fail silently | Always check with both ticketing and operating carrier |
| Issuing on QF stock | QF agents may refuse changes or apply wrong rules | Issue on AA stock or through competent TA |
| Forgetting the 12-month clock | Segments booked beyond validity will be rejected | Track the expiry date from segment 1 departure |

---

## FlyerTalk Source Threads

| Thread | URL | Key Data Points |
|--------|-----|----------------|
| oneworld Explorer User Guide | [#2008084](https://www.flyertalk.com/forum/oneworld/2008084-oneworld-explorer-user-guide.html) | steveholt dummy date question, pye1201 booking with dummies, dvs7310 first booking report, pandaperth repricing rules |
| oneworld Explorer Ticket FAQs | [#338667](https://www.flyertalk.com/forum/oneworld/338667-oneworld-explorer-ticket-faqs.html) | General ticket management rules |
| Point of Origin and Return | [#1417740](https://www.flyertalk.com/forum/oneworld/1417740-point-origin-return-question.html) | Daniel's advice, fare locking after first segment |
| AA RTW Desk vs ExpertFlyer | [#2152207](https://www.flyertalk.com/forum/oneworld/2152207-aa-rtw-desk-availability-compared-expertflyer-ow-online-booking-tool.html) | D-class availability discrepancies |
| Booking and Pricing Experiences | [#2016-2023](https://www.flyertalk.com/forum/oneworld/2016-2023-oneworld-booking-pricing-experiences.html) | Multiple dummy date data points |
| Propeller Travel | [#1731641](https://www.flyertalk.com/forum/oneworld/1731641-propeller-travel.html) | Daniel's operational approach, BA revocation incident |

---

## Cross-References

- [Segment Dropping & Mid-Trip Changes](kb-segment-dropping.md) -- Section 4 (rebooking rules), Section 7 (fare locking strategy)
- [GDS Segment Stitching](kb-gds-segment-stitching.md) -- Section 1 (Sabre vs Amadeus capabilities), Section 7 (agent tricks)
- [Revenue Management](kb-revenue-management.md) -- Section 4.3 (dummy dates as RM technique)
- [Oslo Origin Strategy](kb-oslo-origin.md) -- Section 9.2 (dummy dates in Oslo booking workflow)
- [Segment Bank Strategy](segment-bank-strategy.md) -- Dummy dates as core operating principle
- [YQ Surcharge Optimization](kb-yq-surcharge-optimization.md) -- Section 7 (Daniel's operational approach)
- [Rule 3015 Fare Rules](../01-fare-rules.md) -- Section 14 (changes and cancellations)
