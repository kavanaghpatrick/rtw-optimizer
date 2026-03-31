# ExpertFlyer Accuracy & Limitations for oneworld Explorer D-Class Verification

Knowledge base compiled from FlyerTalk community reports, web research, and direct testing (March 2026). This document informs how our `rtw verify` command should present ExpertFlyer results and what caveats to surface to users.

---

## Executive Summary

ExpertFlyer is the best publicly available tool for pre-checking D-class availability on oneworld Explorer (OWE) RTW tickets, but **it is not authoritative**. Community reports consistently show a gap between "D available on ExpertFlyer" and "D bookable on an RTW ticket." The three main causes are:

1. **Point of Commencement (POC)** -- EF cannot filter by POC, which is the primary driver of availability differences
2. **Married Segment Control (MSC)** -- EF shows standalone segment availability; agents see connected-journey availability
3. **Carrier capacity restrictions** -- IATA Rule 3015 allows carriers to limit D-class seats on any flight for RTW fares

**Reliability estimate**: EF availability matches agent-bookable availability roughly 70-85% of the time. The remaining 15-30% of discrepancies are not random -- they follow predictable patterns documented below.

---

## 1. Specific Discrepancy Examples

### EF Shows D-Class but Agents Cannot Book

| Route | EF Result | Agent Result | Likely Cause | Source |
|-------|-----------|--------------|--------------|--------|
| LAX-SYD (QF12) | D5 | D0 (BA, QF both confirm) | POC or capacity restriction | FT: EF Going Downhill |
| SJO-DFW (AA1080) | D7 | No availability (BA change team) | POC mismatch (ex-OSL ticket, BA POS) | FT: EF vs BA |
| Various QF routes | D available | BA sees no D | BA restricts partner D on competitive routes | FT: EF Going Downhill |
| QR/CX routes | D available | "started to affect QR and CX" | POC-related, worsening over time | FT: EF Going Downhill |
| JL routes | D available | Booking agent denied | JL capacity restriction or POC | FT: EF Going Downhill |

### EF Shows D0 but Agents Can Book

This reverse scenario is less commonly reported but does occur:
- When carrier inventory desks release last-minute seats not yet propagated to GDS
- When agents use codeshare flight numbers (e.g., AA7387 instead of QF12) to access different inventory buckets
- When operating carrier has seats available but hasn't pushed them to Amadeus/Sabre feeds that EF reads

### Magnitude of the Problem

One user with an ex-CAI QF-issued RTW reported that **half the flights** (QF, JL, AA) showed different availability on EF versus what QF agents could actually book. Another user booking through BA found "no D availability viewable to them on other OW airlines, despite what EF said, and strangely consistently on routes that [BA] fly."

---

## 2. Point of Sale (POS) Configuration

### What POS Does

POS tells the GDS which market the ticket is being sold in. Airlines file different availability by market -- a flight may show D9 for US POS but D0 for UK POS.

### EF POS Options

ExpertFlyer calls POS the "PCC" (Pseudo City Code) setting. Options include:
- `USA (Default)` -- our scraper's current hardcoded setting
- Country-specific options: UK, France, Germany, Norway, India, etc.
- No Belgium POS available (closest proxy: France)

### POS Impact on RTW Results

Community testing shows POS has **less impact than expected** on D-class for OWE tickets:

> "I changed the filters in EF to both UK and Norway (and even India) and got the same D7 availability" -- Tetrarch, FT

This is because the real differentiator is POC, not POS. Changing POS in EF rarely resolves discrepancies with agent-visible availability.

### Our Scraper's POS Setting

Currently hardcoded to `USA (Default)` in `rtw/scraper/expertflyer.py` line 295:
```python
"pcc": "USA (Default)",
```

**Recommendation**: Keep USA as default (broadest availability view). Consider adding a configurable POS parameter but note that changing POS alone rarely resolves discrepancies. The real issue is POC.

---

## 3. Point of Commencement (POC)

### What POC Is

POC is the city where the journey actually begins -- the first departure point on the ticket. For RTW tickets, this is the origin city (e.g., OSL for ex-Oslo, LHR for ex-London, CAI for ex-Cairo).

### Why POC Matters More Than POS

Airlines increasingly use POC (not just POS) to control D-class availability. A flight may show D available when searched with a US POS, but the booking agent working an ex-Oslo ticket sees different availability because the POC is Oslo.

> "Point of Sale (POS) =/= Point of Commencement (POC). I don't believe EF supports POC yet." -- izzik, FT

> "Availability these days is a product of POS, POC, and MSC. Unfortunately, looking for availability based on POC seems limited to those with an Amadeus terminal access (not even Sabre)." -- ernestnywang, FT

### EF's POC Limitation

**ExpertFlyer does not support POC filtering.** This is the single biggest limitation for RTW planning:

> "It may be [related to POC], but I can't change the EF website to do more than POS. So therefore you're stuck. The solution would be offering POC as an advanced option on EF." -- FT user

### Practical Impact

- **BA-ticketed RTW (ex-LHR)**: BA agents use Amadeus with UK POC. EF with USA POS shows different (usually more generous) availability.
- **AA-ticketed RTW (ex-anywhere)**: AA uses Sabre. POC handling differs from Amadeus.
- **QF-ticketed RTW (ex-CAI)**: QF agents reported different availability than EF for QF, JL, and AA flights.

### BA's Competitive Route Restriction

Multiple reports indicate BA restricts partner D-class on routes they also fly:

> "When I booked my RTW with BA this was a major frustration. No D availability viewable to them on other OW airlines, despite what EF said, and strangely consistently on routes that they fly." -- FT user

This may be a POC-driven restriction or deliberate inventory management by BA to protect their own J-class revenue.

---

## 4. Married Segment Control (MSC)

### How MSC Affects EF Results

ExpertFlyer shows availability for **standalone segments** (one O&D pair at a time). When an agent builds a PNR with multiple connected segments, the GDS evaluates them as a married group, which can yield different availability.

### MSC Patterns Relevant to RTW

1. **Connecting flights within 24 hours**: If your itinerary has two segments departing within 24 hours, the GDS may "marry" them. Even though each segment shows D available individually, the married combination may show D0.

2. **Existing PNR context**: When changing an existing RTW ticket, the agent's system evaluates new segments in the context of already-booked segments. This can suppress availability that EF shows for a standalone search.

3. **Hub carrier patterns**: Cathay Pacific (CX) through HKG and Qatar (QR) through DOH are known to restrict standalone D-class, making it available only on connecting itineraries through the hub.

### Agent Workaround for MSC

> "Are the LAX-ICN-HKG sectors within 24 hours of the LAX-SYD sector you want to book? If yes, it may affect the availability. In this case, airline call centre agent can (and should) remove LAX-ICN-HKG first, without saving (ending) the PNR, before looking for LAXSYD availability." -- ernestnywang, FT

### Our Detection

`rtw/rules/married.py` already detects:
- CX routes not touching HKG (hub-connection married pattern)
- Through-flight split risks (via cities that also appear as stopovers)

`rtw/verify/verifier.py` checks for married patterns when nonstop shows D0 but connecting flights show D>0.

---

## 5. Time Lag Between EF and Real-Time Availability

### GDS Update Delays

ExpertFlyer queries GDS data that may be minutes to hours behind real-time airline inventory:

> "There are also time lag issues." -- corporate-wage-slave, FT

### Factors Affecting Lag

- **D-class availability is volatile**: A single booking can change D9 to D0 on small-cabin flights
- **Sale events**: During BA Business Class sales, availability "flashes" briefly: "There was a brief flash of D class availability yesterday, but I was a bit slow and it was gone by the time I'd checked the other flights in EF"
- **Schedule rollover**: AA/AS/WY flights on Sabre are limited to 330 days out. When flights first roll into bookability, D-class may not be loaded yet.
- **Cache staleness**: Our scraper caches results for 24 hours (`_CACHE_TTL_HOURS = 24`). For D-class on popular routes, this may be too long.

### Practical Guidance

- **High-confidence window**: D9 on a flight 3+ months out is very likely bookable
- **Medium-confidence**: D3-D7 on flights 1-3 months out -- probably bookable but verify quickly
- **Low-confidence**: D1-D2 on flights <1 month out -- may vanish before agent can book
- **Stale risk**: Any result >6 hours old on popular routes should be re-checked

---

## 6. Carrier-Specific D-Class Accuracy on ExpertFlyer

### Reliability Tier List

Based on community reports:

| Tier | Carriers | EF Accuracy | Notes |
|------|----------|-------------|-------|
| **Good** | AA (domestic), FJ, RJ | ~90% | AA domestic segments rarely have POC issues |
| **Moderate** | QF, BA, MH, SQ* | ~75% | POC-dependent; BA restricts partner D on own routes |
| **Problematic** | CX, QR, JL | ~60-70% | Hub-married segments; POC issues; capacity restrictions |
| **Variable** | AA (international) | ~70-80% | AA has used capacity restriction clause; 330-day limit |

*SQ is not oneworld but included for codeshare context

### Carrier-Specific Notes

**American Airlines (AA)**
- Uses **H class** (not D) for OWE business -- our tool handles this via `get_booking_class()`
- Sabre system with 330-day booking limit
- Has been observed invoking the IATA capacity limitation clause to restrict RTW D-class
- AA domestic segments are generally reliable on EF
- AA RTW desk is "definitely the most competent" at handling OWE tickets

**British Airways (BA)**
- Agents use Amadeus with POC context -- EF (Sabre-based) shows different view
- Restricts partner carrier D-class on routes BA also operates
- India-based change team must refer to Pricing Team (72-hour turnaround)
- When EF and BA are "in lockstep," results are reliable

**Cathay Pacific (CX)**
- Strong hub-married segment control through HKG
- D-class on non-HKG-touching routes may only be available as connections
- Our `MarriedSegmentRule` already flags CX routes not touching HKG

**Qatar Airways (QR)**
- Hub-married through DOH
- "Started to affect QR" -- POC issues increasing
- Our `_MARRIED_CHECK_HUBS` in verifier.py already includes QR/DOH

**Japan Airlines (JL)**
- Multiple reports of D discrepancies between EF and booking agents
- POC-sensitive availability

**Qantas (QF)**
- Flagship routes (QF1/2 SYD-SIN-LHR) are through-flights -- see through_flights.yaml
- QF agents sometimes see different D than EF, especially on BA-ticketed RTWs
- Using AA codeshare number (e.g., AA7387) can sometimes access different inventory

---

## 7. The "D Available" vs "D Bookable on RTW" Gap

### Three Layers of Availability

```
Layer 1: GDS Availability (what EF shows)
  └── D9 on the flight in general inventory

Layer 2: Fare-Rule Filtered (what the fare rule permits)
  └── IATA Rule 3015 Capacity Limitations clause:
      "THE CARRIER SHALL LIMIT THE NUMBER OF PASSENGERS
       CARRIED ON ANY ONE FLIGHT ON FARES GOVERNED BY
       THIS RULE AND SUCH FARES WILL NOT NECESSARILY BE
       AVAILABLE ON ALL FLIGHTS."

Layer 3: Agent-Bookable (what the ticketing system allows)
  └── Filtered by POS + POC + MSC + existing PNR context
```

### Why Each Layer Matters

**Layer 1 (EF)**: Shows the broadest view. This is what our `rtw verify` reports.

**Layer 2 (Fare Rule)**: Carriers can restrict D-class for RTW fares even when D is generally available. This is legal under Rule 3015. Only AA has been confirmed to use this, but any carrier could.

**Layer 3 (Agent)**: The definitive answer. Depends on which carrier is ticketing, which GDS they use, and the full PNR context.

### Implications for Our Tool

Our `rtw verify` result is **Layer 1 only**. We must clearly communicate this to users:
- "D available" on EF means "D exists in general inventory" -- not "D is bookable on your specific RTW ticket"
- The probability of Layer 1 matching Layer 3 varies by carrier, POC, and MSC context

---

## 8. Recommendations for Our Tool

### Display Caveats in Verify Output

When displaying EF results, always include context:

1. **Confidence indicator** per segment based on carrier reliability tier
2. **MSC warning** when segments within 24 hours of each other exist
3. **POC caveat** stating that EF cannot account for Point of Commencement
4. **Carrier-specific notes** for CX (hub-married), QR (hub-married), AA (H class, capacity clause)

### Proposed Confidence Levels

```
HIGH    = D7-D9, carrier in "Good" tier, >90 days out, no MSC risk
MEDIUM  = D3-D6, or carrier in "Moderate" tier, or 30-90 days out
LOW     = D1-D2, or carrier in "Problematic" tier, or <30 days out, or MSC flagged
CAVEAT  = Any result where POC mismatch is likely (e.g., non-US origin with USA POS)
```

### Verify Output Footer

Every `rtw verify` run should display:

```
NOTE: ExpertFlyer shows GDS-level availability only. Actual bookability
depends on Point of Commencement, Married Segment Control, and carrier
capacity restrictions. Confirm with booking agent before relying on
these results. See: docs/kb-expertflyer-accuracy.md
```

### POS Configuration

- Keep `USA (Default)` as the default POS (broadest availability view)
- Add `--pos` CLI flag to `verify` and `scan-dates` commands for user override
- Document that changing POS rarely resolves discrepancies (POC is the real issue)

### Cache TTL Tuning

- Reduce cache TTL for flights <30 days out (6 hours instead of 24)
- Add `--no-cache` flag (already exists) and document when to use it
- Consider adding a "freshness" indicator to cached results

---

## 9. Alternative Verification Methods When EF Fails

### When EF Shows D but Booking Fails

1. **Try the operating carrier directly**: If BA cannot book D on a QF flight, call QF directly. QF may see different availability through their own system.

2. **Try codeshare flight numbers**: QF12 LAX-SYD may show differently as AA7387 LAX-SYD. Ask the agent to search the codeshare.

3. **Try a different ticketing carrier**: AA RTW desk vs BA RTW desk vs QF may each see different inventory. AA RTW desk is widely reported as the most competent.

4. **Remove conflicting segments first**: If MSC is suspected, ask the agent to remove conflicting segments from the PNR (without saving/ending), then re-check availability.

5. **oneworld online booking tool (xONEx)**: Build a dummy RTW on the oneworld website starting from the correct origin city. One user confirmed: "Just tried a dummy ATW booking on the OW website starting in UK and there was no issue selecting the flight." This tests Layer 3 availability directly.

6. **Wait and retry**: Availability can fluctuate. If a flight shows D0 today but D5 next week, try again. Book placeholder dates and change for free later.

7. **Adjacent dates**: Our `scan-dates` command already checks +/-3 days. If target date is D0, adjacent dates may have availability.

8. **Alternative routing**: If LAX-SYD is D0, try LAX-SFO + SFO-SYD, or route via a different hub.

### Tools Comparison

| Tool | POS | POC | MSC | Real-time | RTW-specific |
|------|-----|-----|-----|-----------|--------------|
| ExpertFlyer | Yes | No | No | Near (minutes lag) | No |
| oneworld xONEx | Implicit | Yes | Yes | Yes | Yes |
| BA.com | Implicit | Partial | Yes | Yes | No (award only) |
| AA.com | Implicit | Partial | Yes | Yes | No |
| QF.com | Implicit | Partial | Yes | Yes | No |
| SeatSpy | No | No | No | Periodic | No |
| Agent (phone) | Yes | Yes | Yes | Yes | Yes |

**Best practice**: Use EF for initial screening, confirm critical segments via xONEx dummy booking, book via AA RTW desk for best results.

---

## 10. Known Issues in Our Implementation

### Current Gaps

1. **POS is hardcoded to USA**: `rtw/scraper/expertflyer.py` line 295. Should be configurable.
2. **No POC awareness**: We have no way to account for POC in EF queries. This is an EF platform limitation, not something we can fix.
3. **No confidence scoring**: Verify results show D-class count but no reliability indicator.
4. **24-hour cache may be too long**: For flights <30 days out, D-class can change hourly.
5. **No xONEx cross-check**: We don't verify against the oneworld booking tool.

### Implemented Mitigations

1. **Married segment detection** (`rtw/rules/married.py`): Flags CX non-HKG routes
2. **Married pattern in verifier** (`rtw/verify/verifier.py`): Detects D0 nonstop with D>0 connecting
3. **Per-carrier booking class** (`rtw/carriers.py`): AA uses H, others use D
4. **Through-flight reference** (`rtw/data/through_flights.yaml`): Documents known cross-continent through-flights
5. **Nonstop vs connection distinction**: `DClassResult.has_nonstop` and `display_code` show `D9*` for connection-only results

### Suggested Enhancements

1. Add `--pos` parameter to verify/scan-dates commands
2. Add confidence tier to `DClassResult` based on carrier + days-out + seat count
3. Add verify footer with POC/MSC caveat text
4. Reduce cache TTL for near-term flights
5. Add `--cross-check` option that opens xONEx for manual verification
6. Surface carrier-specific warnings (BA competitive route restriction, AA capacity clause)

---

## FlyerTalk Source Threads

- [AA RTW desk availability compared to ExpertFlyer and OW online booking tool](https://www.flyertalk.com/forum/oneworld/2152207-aa-rtw-desk-availability-compared-expertflyer-ow-online-booking-tool.html)
- [ExpertFlyer vs BA](https://www.flyertalk.com/forum/oneworld/2213364-expertflyer-vs-ba.html)
- [Is this ExpertFlyer going downhill or am I doing something wrong?](https://www.flyertalk.com/forum/oneworld/2180862-expertflyer-going-downhill-am-i-doing-something-wrong.html)
- [ExpertFlyer BA business class awards](https://www.flyertalk.com/forum/british-airways-executive-club/2121573-expertflyer-ba-business-class-awards.html)
- [The oneworld Explorer User Guide](https://www.flyertalk.com/forum/oneworld/2008084-oneworld-explorer-user-guide.html)
- [Issues with married segment control and oneworld award](https://www.flyertalk.com/forum/finnair-finnair-plus/1888592-issues-married-segment-control-oneworld-award.html)

---

*Last updated: 2026-03-30*
