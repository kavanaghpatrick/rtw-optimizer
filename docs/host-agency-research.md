# Host Agency Research: GDS Access & Virtuoso-Tier Hosts for RTW Ticket Self-Service

Last updated: 2026-03-29. Based on ~200 research queries across Reddit, FlyerTalk, Host Agency Reviews,
Google Reviews, BBB, Glassdoor, and web sources. Includes Virtuoso-tier host research (GTC, Direct Travel,
Travel Edge, Fora, MVT) and verified Reddit payment UX findings.

## Executive Summary

To self-service oneworld Explorer RTW bookings via GDS, you need a host agency with ARC accreditation + GDS cryptic access. After exhaustive research:

- **Nexion**: Confirmed GDS cryptic access, but terrible tech (AgentMate = "2005 Windows with Clippy"), no upgrade plans, 70/30 starting commission, service fees subject to commission split. Multiple agents left for WorldVia.
- **KHM**: NO GDS access at all. Eliminated.
- **Outside Agents**: NO GDS access (non-ARC, uses consolidators). US citizens only. Eliminated.
- **WorldVia**: FULLY RESEARCHED. $29/mo self-ticketing (Sabre+Worldspan cryptic), 90/10 commission, 4.89/5 on HAR (166 reviews), A+ BBB, dedicated Air Services team for complex intl/multi-city. TRIO platform launched 2025 (Sabre+NDC). Key risk: no confirmed RTW fare experience; self-ticketing = agent bears debit memo risk. Best option of the four.

## Nexion Travel Group — Detailed Findings

### Pricing (Confirmed from nexion.com/plans)
| Plan | Monthly | Non-ARC Split | ARC Airline Split | SNAP Split |
|------|---------|--------------|-------------------|------------|
| Nexion 90 Plus | $159 | 90% | 80% | N/A |
| Nexion 90 | $39 | 90% | 70% | 50% |
| Nexion 80 | $15 | 80% | 60% | 50% |
| Nexion 70 | $0 (yr1), $5 after | 70% | 60% | 50% |

GDS add-on: Standard $39/mo, Deluxe $99/mo. Setup $199 + $99 GDS.

### Technology (Reddit/Forum Consensus)
- AgentMate: "spaghetti code," opens new browser windows, times out constantly
- Nexion told agents at event: "no plans to upgrade"
- Most agents buy external CRM (Travefy $39/mo) and duplicate work
- NexionTown forum: "clunky at best"

### Payment Rails
- **AgentMate Pay Now!**: Card COLLECTION link (not processor). Client enters card on secure form, stored 96hr CVV. Agent manually enters into GDS.
- **myNexion Merchant POS**: Virtual terminal for service fees. Nexion is merchant of record. Takes commission split on fees.
- **ARC Pay**: 3.5% flat rate, payment links, integrates with GDS. Must be enabled by Nexion (tied to ARC number). Unknown if available to ICs.
- **Service fee trap**: Fees processed through Nexion POS are subject to commission split (lose 30% on Nexion 70 plan).

### Ticketing
- Agent builds PNR → queues to Nexion → ResReview QC (24/7 automated) → auto-tickets in seconds
- Complex fares → manual desk review (business hours)
- Agent CANNOT self-ticket

### Debit Memo Risk
- Agent bears full liability (passed through via IC agreement)
- E&O does NOT cover debit memos
- BA ex-SEZ horror story: $5,000+ debit memos per ticket, agency threatened with BA ticketing ban

### Why Agents Leave (Reddit r/travelagents)
- Outdated tech, no upgrade plans
- Weak agent community
- Training has broken links, incorrect info
- Where they go: WorldVia, Cruise Planners, smaller modern agencies

## WorldVia (formerly Travel Quest Network) — FULLY RESEARCHED

Last researched: 2026-03-29. Sources: Host Agency Reviews (166 reviews), Google Reviews (62 reviews),
BBB profile, Reddit r/travelagents (10+ threads), Glassdoor (17 reviews), worldviatravelnetwork.com,
Travel Agent Central, Find A Host, Wanderlog.

### Company Overview
- Founded: 1998 (as Travel Quest Network, rebranded to WorldVia)
- HQ: Roswell, Georgia (formerly Alpharetta)
- US members: 3,250 independent contractors
- Annual sales: $319.8 million
- CEO: Jason Block | Founder: Bonnie Lee
- Accreditations: ARC, CLIA, IATA
- Consortium: Travel Leaders Network (same consortium as Nexion)
- BBB Rating: A+ (accredited since Oct 2023)
- Awards: 4x Travel Weekly Magellan Awards (2024), 8x (2025), Power List 2024

### Ratings Across Platforms
| Platform | Rating | Count | Notes |
|----------|--------|-------|-------|
| Host Agency Reviews (Host) | 4.89/5 | 166 reviews | Overwhelmingly positive |
| Host Agency Reviews (Consortium) | 4.89/5 | 166 reviews | Same pool |
| Google Reviews (Wanderlog) | 4.5/5 | 62 reviews | 53 five-star, 7 one-star |
| Glassdoor (Employee) | 4.2/5 | 17 reviews | 89% recommend |
| BBB | A+ | 3 complaints (3yr) | Complaints are for Quest Travel Group tours, not host agency |

### GDS Access & Air Ticketing (CONFIRMED)

**Supported GDS systems:** Amadeus, Galileo, Sabre, Travelport, Worldspan
(Profile lists all five; ticketing plans currently focus on Sabre + Worldspan)

**Requirement:** 2 years prior GDS experience + fluency interview

**Three ticketing plan tiers:**

| Plan | Monthly | GDS | Who Tickets | Domestic | Intl | Changes/Refunds |
|------|---------|-----|-------------|----------|------|-----------------|
| Auto-Ticketing | $9/user | Sabre | WorldVia | $1 | $10 | $6 dom / $15 intl |
| Self-Ticketing | $29/user | Sabre + Worldspan | Agent (optional WV support) | Free | Free | Free (self) |
| PRO Auto-Ticketing | $129/user | Sabre | WorldVia | Included | Included | Included |

Setup: $59 (1st user), $59 (2nd), $29 (additional)

**Auto-ticketing protections:** Commission debit memo protection on auto-ticketed reservations.
WorldVia reviews reservations for airline policy compliance and identifies commission opportunities.

**Self-ticketing:** Agent does own ticketing; can escalate to WorldVia support ($6-$20 per transaction).

**Complex booking support:** Dedicated Air Services team available 24/7 for "complex bookings
such as international travel and multi-city itineraries."

### TRIO Booking Platform (NEW — launched 2025)
- Built in collaboration with Sabre
- Unified air + hotel + car in single interface
- NDC fare integration (no cryptic GDS commands needed for basic bookings)
- Automated ticketing and schedule change notifications
- Real-time commission rate visibility before checkout
- Access to 80+ airline commission programs
- 24/7 expert Air Services team for complex bookings
- Note: Agent can still use GDS cryptic (Sabre) directly on self-ticketing plan

### Commission Structure (CONFIRMED)

| Plan | Monthly | Commission Split | Notes |
|------|---------|-----------------|-------|
| Jumpstart | $0/mo* | 60-70% | For new agents; *$9/mo on lowest tier |
| Growth / Pro 80 | ~$29/mo | 80% | Mid-tier |
| Team / Pro 90 | ~$45/mo | 90% | Most popular for experienced agents |
| Enterprise | Custom | Up to 97% | Requires $2M+ annual ticketed sales |

- Startup fee: $199 (waived for agents with $500K+ trailing-12-month sales)
- No annual fee
- Minimum activity: 1 booking per year
- No non-compete clause
- Weekly commission deposits (every Friday via direct deposit)
- Residual commissions paid even after leaving (for bookings made while active)
- GDS plan does NOT affect commission split

### Technology & Tools
- **CRM:** AgentMate (complimentary) — described as improving but not best-in-class
- **Email Marketing:** Email+ platform
- **Website Builder:** Sites platform (branded websites)
- **Lead Generation:** Agent Profiler system
- **Proposal Builder:** Itinerary proposals
- **Payment:** Secure payment system (launched 2024, details sparse)
- **E&O Insurance:** Provided
- **Training:** Hundreds of hours online + in-person events, weekly Thursday Q&A

### Agent Reviews: POSITIVE Themes

**Support & Responsiveness (dominant theme):**
- "Live chat, and you can actually call and talk to a real person" (Curtis Buechler, Jul 2025)
- "If I email them, they always respond back" (Karen Holmes, Nov 2024)
- "Called me to see if I needed anything" — proactive outreach (Karen Holmes)
- "Training received immediately after joining had me ready to go within days"
- Direct access to CEO Jason Block and Founder Bonnie Lee

**Commission & Value:**
- "Ability to pay lower monthly fee while training is fantastic" (Patrick Noce, Oct 2024)
- "Very fair rates" with weekly Friday payouts
- "Best travel host agency I've been with by far" (Blessing Nneji, Jun 2025)

**Ticketing & Air Support:**
- "Air ticketing team jumps in fast when flight issues pop up" (Aaron Bergman)
- "Rearrange things without making agents feel like they're on their own"
- "Right beside me as I took on my first cruise group"

**vs Competitors (Reddit r/travelagents):**
- "You're not with an MLM... Way better commission split for way less money" (re: switching from Inteletravel)
- "World Via is great for new agents. Low monthly costs" (vs CruisePlanners/OA)
- "Recommend WorldVia or TPI" as alternatives to Outside Agents
- Multiple ex-Nexion agents switched to WorldVia

**Reddit thread: "Fora v. WorldVia" (Dec 2024):**
- WorldVia praised for commission splits, FAMs, lead generation
- Concern: learning curve with tech, paying for external apps
- Response from WV agent: "If you are just part time you don't need all the tech"

### Agent Reviews: NEGATIVE Themes

**Termination dispute (1 review):**
- Jennifer Suski (1-star, Jul 2024): Terminated after 1 week citing "conflict of interest"
- Disputed company's interpretation of contract discount policy
- Company invoked "terminate at will" clause
- Wasted onboarding hours, damage to client reputation

**Recruiter quality (1-2 reviews):**
- K G (2-star Google, Oct 2024): Recruiter Jonathan Lott focused on pricing, not value
- Startup fees "JUST" reinstated despite website claiming "No Startup fee"

**Booking support failures (2 Google reviews):**
- Christine A. (1-star, Apr 2025): Unresolved cruise booking with missing flights/deviations
- Paul P. Foster (1-star, May 2025): Unresponsive support for Diamond Member check-in issues

**Leadership criticism (1 Google review):**
- M J (1-star, Sep 2025): "CEO Jason and CRO Joshua don't take their jobs seriously"

**Training gaps (Reddit):**
- New agents wish onboarding had more hands-on booking platform training
- "Training focused more on how to actually use the booking platform and less on general sales concepts"
- "Intro videos are just lacking for me" — took self-guided exploration to learn

**Missing commission tracking (Reddit/HAR):**
- "Process to submit inquiries about missing commissions is quite lengthy"

**No weekend support:**
- Business hours: 9am-6pm M-F CST only (private Facebook group for after-hours)

### RTW/Complex Fare Assessment

**Strengths for our use case:**
- Self-ticketing plan ($29/mo) gives direct Sabre + Worldspan cryptic access
- 2-year GDS experience + fluency interview ensures competent agents
- Dedicated Air Services team explicitly handles "international travel and multi-city itineraries"
- ARC + IATA accredited (required for oneworld Explorer ticketing)
- Same consortium (Travel Leaders Network) as Nexion
- Auto-ticketing includes debit memo protection
- TRIO platform supports NDC fares alongside traditional GDS

**Risks for our use case:**
- No specific mention of RTW/oneworld Explorer fare experience
- Self-ticketing = agent bears debit memo risk (no protection like auto-ticketing plan)
- Support hours M-F only (no weekend/evening complex fare support)
- Sabre RTW pricing queue may reject itineraries without AA transoceanic segment (industry-wide issue)
- New agents report CRM/tech learning curve
- Commission inquiry process described as lengthy
- No confirmed ARC Pay integration (card collection method unclear)

**Open questions (still unconfirmed):**
- Has WorldVia Air Services team ticketed oneworld Explorer fares before?
- Can auto-ticketing handle RTW fare construction, or only simple point-to-point?
- What is the debit memo policy for self-ticketing agents?
- Is ARC Pay available to IC agents?
- Can the Air Services team handle Amadeus-native fares if Sabre pricing rejects?

### BBB Complaints (Quest Travel Group entity)
3 complaints in 3 years. All relate to Quest Travel Group's tour operations (Israel tour cancellations
due to war), NOT to the host agency/WorldVia Travel Network business:
- Mar 2024: Couple sought refund for cancelled Israel tour ($5,386 retained), unresolved
- Dec 2023: Similar Israel tour refund, partially resolved ($2,749 refund)
- 1 additional complaint, details unavailable

### Glassdoor Employee Reviews (WorldVia corporate staff)
- 4.2/5 stars, 17 reviews, 89% recommend, 82% positive outlook
- Pros: Kind/supportive team, work-life balance, innovation encouraged, no micromanagement
- Cons: Sales metrics possibly unrealistic, small-company benefits, shared office space
- One "Be careful!" warning review exists but content behind paywall

## KHM Travel Group — ELIMINATED
- NO GDS access ("Not Offered" per Host Agency Reviews)
- Leisure/cruise focused
- Good training but irrelevant for our use case

## Outside Agents — ELIMINATED
- Non-ARC agency, uses consolidators
- US citizens only, 3:1 client-to-personal booking ratio required
- No GDS access at all

## ICTravel (Incentive Connection Travel) — Potential Alternative
- $25/month Sabre access
- Self-ticketing after proving proficiency
- 30 years operating
- Voids $5, refunds $7.50, exchanges $7.50
- One negative FlyerTalk review ("family business of non-savvy people")

## Industry Payment Reality

### The Fundamental Problem
- Airline ticket payment must go through GDS/ARC pipeline
- PCI-compliant tools (Stripe, TravelJoy) tokenize cards — agent never sees number
- But GDS requires raw card number as Form of Payment
- These are architecturally incompatible
- No host agency has solved this gap

### WorldVia Payment Tools (Confirmed)
| Tool | What It Does | Client-Facing? |
|------|-------------|----------------|
| **CRM Payments Tool** (WorldVia PRO) | Secure card auth form with passphrase | Yes |
| **AgentMate Pay Now!** | Payment link in invoice, card collection | Yes |
| **TRIO** | Booking platform with service fee bundling | Agent-facing |
| **ARC Pay** | Not confirmed available through WorldVia | Unknown |

Card flow: Pay Now! link → client enters card → saved in profile (CVV 96hrs) → agent enters FOP in Sabre.
Service fees: Collect independently (Stripe/Venmo) at 100% retention, or via ARC at 3.5%.
CA/FL agents cannot charge service fees under WorldVia Seller of Travel licenses.
Commission payment: Weekly (Fridays) via direct deposit.

### How Agents Actually Collect Payment (2025/2026)
1. Phone call (client reads card) — most common, dated
2. OAF/authorization form (client fills out form) — standard
3. AgentMate Pay Now! (card collection link) — WorldVia + Nexion
4. CRM Payments Tool (secure passphrase form) — WorldVia PRO
5. ARC Pay (payment link + GDS integration) — if host enables it
6. TravelJoy — service fees ONLY, NOT airline FOP (cards tokenized, can't enter into GDS)

### Service Fee Best Practices
- 55% of advisors now charge planning fees
- Average fee per trip: $1,200 (2025)
- RTW itinerary: $300-1,000+ justified
- Process through own Stripe/TravelJoy to keep 100% (minus ~3% processing)
- Do NOT process through host POS (they take commission split)

## Sabre RTW-Specific Issues (CONFIRMED — Eliminates Sabre for OWE)
- Sabre's pricing queue rejects RTW itineraries without AA transoceanic segment
- Sabre CANNOT auto-price oneworld Explorer fares — "N/A" in Qantas Quick Reference Guide
- Sabre has only 3 tax fields (multi-segment RTW needs many more)
- Sabre Phase-IV mask field may not be long enough for RTW fare calculations
- This is agency-specific — AA RTW desk handles it differently
- **Conclusion: Amadeus is required for OWE fare construction. Sabre-only hosts (WorldVia,
  Nexion) cannot efficiently handle this fare type.**

## GDS API Access — NOT POSSIBLE
- Amadeus Enterprise API requires separate WSAP provisioning + contract
- Amadeus Self-Service APIs shutting down July 17, 2026
- Sabre API via host: blocked (host must request, most say no)
- No precedent for host agency sub-agent API access
- Sabre Scribe (in-terminal scripting) is the practical automation layer

## The Realistic Architecture
```
rtw validate trip.yaml      → 37 rules (debit memo protection)
rtw booking trip.yaml       → GDS commands (Amadeus or Sabre)
Copy → Paste into GDS       → manual but instant
Host tickets (or self-ticket) → done
```

## FlyerTalk Community Consensus
- AA RTW Desk (+1-800-247-3247) remains most reliable for initial RTW booking
- GDS self-ticketing for RTW = high power, high risk (debit memos)
- ExpertFlyer + phone booking scripts = optimal for most users
- Host agency GDS access saves time on ongoing changes (10-20/year)
- Amadeus better than Sabre for BA-native oneworld Explorer fares
- But Sabre has the RTW AA transoceanic segment requirement

## Virtuoso-Tier Host Agency Research

Researched 2026-03-29. Sources: Host Agency Reviews (profile, reviews, questions pages), foratravel.com,
Reddit r/travelagents (13 threads via Grok web search + PullPush archive). All findings below are from
verified web fetches only — no training data.

### Cross-Host Finding: Payment UX Is Never Documented

No host agency publicly documents the client-facing payment experience for flights. Across Travel Edge,
GTC, Direct Travel, and Fora — all list "payment solutions" but none describe what the client sees.
This is consistent across the entire industry.

### Comparison Table — Verified Data Only

| | MVT | GTC | Direct Travel | Fora | Travel Edge |
|---|---|---|---|---|---|
| **Commission** | Unknown | Undisclosed | 70-95% | 70-80% | Unknown |
| **Startup** | Unknown | $0 | $250 | $0 | Unknown |
| **Annual** | Unknown | $0 | $0-900 | $299 | Unknown |
| **GDS** | Unknown | Sabre | All (Apollo, Sabre, Amadeus, Galileo, Worldspan) | **None** | Unknown |
| **Consortium** | Virtuoso | Virtuoso + TLN | Virtuoso | Virtuoso | Unknown |
| **Air desk** | Unknown | Yes (strong reviews) | Yes ("excellent contracts") | Pro-only ($100k+) | Yes (Air Connect, $50-100/ticket) |
| **Accepts** | Unknown | Experienced only | Experienced only | Beginners + experienced | Unknown |
| **Agents** | Unknown | 1,700 | 630 | Unknown | Unknown |
| **Sales vol** | Unknown | $1.5B | $1B | Unknown | Unknown |
| **Payment UX** | Unknown | Not documented | Not documented | Portal (no detail) | ADX (no detail) |
| **Reddit** | Zero presence | Mentioned for air | Not mentioned | Mentioned (CC portal) | Not mentioned |

### MVT (Montecito Village Travel) — FULLY RESEARCHED

Last researched: 2026-03-29. Sources: join.montecitovillagetravel.com (12 pages), montecitovillagetravel.com,
Host Agency Reviews (profile + 32 reviews), Luxury Travel Report, Travel Weekly (search snippets),
Reddit r/travelagents (4 threads via PullPush), BBB, Find A Host, Propeller Travel website, FROSCH website,
Virtuoso agency listing. All findings verified from web fetches.

#### Company Overview

**Legal entity:** Your Travel Center, Inc. dba Montecito Village Travel
**Founded:** 1972 by Phil & Louise Emrich as "Your Travel Center" in Santa Barbara, CA
**HQ:** 3329 State Street, Santa Barbara, CA 93105
**Owner/CEO/Chairman:** Colin Weatherhead (former geography teacher from England; joined 1988, purchased 1995)
**President:** Robin Sanchez, CTIE (30+ years with company, promoted April 2022)
**CMO:** Chris Weatherhead (Colin's son, joined ~2010)
**COO:** Shane LeFeber (Colin's son-in-law)
**Co-owner:** Brenda Weatherhead
**Family-run business** — "not positioning itself for sale," building for next generation.

#### Scale

| Metric | Value |
|--------|-------|
| Annual sales | $500M+ (end 2025), up from $18M in 1995 |
| Independent contractors | ~600-800 across 37 states, 3 countries |
| Full-time staff | 49 |
| Physical offices | 2 primary (CA, NE); formerly 16 |
| Agency acquisitions | 24 across 28 locations since 1991 |
| Travel Weekly Power List | #41 (2025), #40 (2024), #39 (2023) |
| President's Club | 108 advisors at $1M+; 38 at $2.5M+; 24 at $4M+ |

#### Awards & Recognition
- Virtuoso Awards finalist 2024 (3 categories: Top Producing Cruise, Tour, Specialty)
- Virtuoso Top Year-Over-Year Revenue Growth Finalist (2017, 2018, 2019)
- Virtuoso Most Hospitable Agency Nominee (2019)
- Robb Report 2024 Travel Masters List (inaugural)
- Condé Nast Traveler 2024 Top Travel Specialists
- Travel+Leisure A-List — 13 consecutive years
- Travel Weekly Magellan Award 2021 (Crisis Communication)

#### Hosted Programs

Four tracks:
1. **Leisure Travel Agent** — non-GDS agents use BookYTC booking engine
2. **Luxury Leisure Travel Agent** — adds Virtuoso advisor status, access to 1,700+ preferred suppliers
3. **Corporate Travel Agent** — full GDS access, automated ticketing/fulfillment, 24/7 support
4. **Partner Agency** — existing agencies retain own brand, MVT works in background; eliminates need
   for own ARC bond, GDS fees, consortia fees; claims 20-25% revenue increase

Accepts: Experienced agents only (2+ years). Sub-agents may join with no experience requirement.

#### Fees & Commission

| Item | Detail |
|------|--------|
| Startup fee | $125 |
| Annual fee | $0 |
| Monthly fee | $0 (pay only for optional services) |
| Commission split | 60% to 90% (tiered by annual gross commissions) |
| Payment | Monthly via direct deposit |
| Client ownership | Clients belong to the IC |
| E&O insurance | Not included |

President's Club tiers: $100K+ settled revenue → $150K+ → $250K+ (or $5M+ for affiliate groups).

Reddit user u/Guatemala103105 claims MVT also offers a flat-fee option where high-volume agents keep
100% of commission: "I think the latter you can pay a set fee and keep 100 percent of commission."

Reddit user u/Sanzy11: "Montecito Village Travel if your sales are high enough. But they don't accept
new to industry."

#### GDS Access — ALL FOUR SYSTEMS

- **Amadeus** (BA-native for oneworld Explorer fares)
- **Apollo** (Travelport)
- **Sabre**
- **Worldspan** (Travelport)

Available with automated ticketing, fulfillment, and quality control. GDS access at nominal additional
cost. Non-GDS agents can use BookYTC (online air/hotel engine built on Sabre).

#### Consortia & Accreditations

| Organization | Relationship |
|-------------|-------------|
| **Virtuoso** | Full member (luxury travel consortium, 1,700+ preferred partners) |
| **FROSCH** | Air ticketing alliance (worldwide air agreements, airline help desks, specialty fares) |
| **ARC** | Accredited (Airlines Reporting Corporation) |
| **IATA** | Member |
| **CLIA** | Member |
| **ASTA** | Premium member |
| **PATH** | Member (Professional Association of Travel Hosts) |

MVT describes the combination as: "The strength of Virtuoso and the power of FROSCH makes you
unbeatable in the industry."

#### FROSCH Relationship (Clarified)

FROSCH is NOT an owner of MVT. It is a services partnership specifically for air ticketing.
FROSCH (now FROSCH by Chase Travel, a JPMorgan Chase subsidiary since May 2022) provides:

- Worldwide air agreements and specialty fares
- Preferred airline executive help desks
- Upfront commissions on domestic and international carriers
- Aircom database: 100+ airline commission programs
- Air desk: full-service ticketing for non-GDS agents (bookings, changes, refunds, after-hours)
- GDS infrastructure for GDS-trained agents

**Critical structural detail:** FROSCH left Virtuoso at end of 2005 and joined Signature Travel Network.
FROSCH and Virtuoso are competitors at the consortium level. MVT bridges both ecosystems: Virtuoso for
luxury hotels/cruises/tours, FROSCH for air ticketing infrastructure. This dual affiliation is rare
and distinctive.

Agent testimonial from MVT website:
> "Air commissions increased by $15,000 (414%)" after joining — Carol, California

Agents must review the FROSCH Aircom User Guide before receiving air access.

#### Technology

| Tool | Purpose |
|------|---------|
| ClientBase | PCI-compliant CRM (client management, invoicing, marketing) |
| BookYTC | Online air/hotel booking engine (Sabre-based, for non-GDS agents) |
| 360 Intranet | Dedicated agent portal |
| Commission tracking | Online, proprietary, no usage fees |
| Document delivery | With mobile app |
| Proactive traveler monitoring | Flight tracking/disruption alerts |
| Corporate booking engines | Multiple options with reporting |
| Marketing tools | Co-op dollars, direct mail, magazine, email, social media |
| Personalized website | Provided at no additional cost (luxury agents) |

Review from Beth King (Jun 2022): "Their in-house system is the best I've seen, offering everything
from tracking commissions, sending brochures, invoicing clients...they don't charge a fee for using
their system."

#### Preferred Suppliers (Partial)

**Luxury Hotels:** Four Seasons (Preferred Partner), Ritz-Carlton (STARS), Mandarin Oriental (Fan Club),
Peninsula (PENCLUB), Dorchester Collection (Diamond Club), Rosewood (Elite), Waldorf Astoria (Impresario),
Belmond (Bellini Club), Sofitel (STEP), Sir Rocco Forte (Knights)

**Cruise:** Crystal (Platinum), Oceania (Connoisseur Club), Regent (Council Club), Viking (Platinum Circle),
Silversea (Excellence Award), Princess (Top Producer), AMA Waterways (Key Account)

**Tour:** Abercrombie & Kent (100 Club), Classic Vacations (Top Producer)

#### Reviews

**HAR: 4.88/5 (32 reviews)** — 19 five-star, 12 four-star, 1 three-star. "First Class" designation.

> "It is the first time in my seven years of being in travel I truly feel like it is my own business
> versus feeling like a 1099 employee." — Paula Iwanski, May 2024 ($1M+ sales)

> "I feel so grateful that I'm an IC with them. I have the support, resources, and backing that I
> didn't even know existed...it feels like you are part of a family." — Marcia Hellman, Jan 2023

> "The best host agency program I've ever experienced" with "superior GDS platforms and air
> commissions." — Craig Buck/Travel Masters, Mar 2013 (20-year IC, former agency owner)

> "Commissions one of the highest in the industry." — Susan Price, Mar 2014

**BBB:** A+ (not accredited). Zero complaints found.
**Yelp:** 12 reviews (content blocked by Yelp scraping protection).
**Find A Host:** 11 reviews, all 5/5 stars.
**Reddit:** Mentioned positively in 4 threads, always listed among top-tier Virtuoso hosts alongside
Departure Lounge, Gifted Travel Network, and Travel Edge.

No negative content found anywhere. Lowest review across all platforms: 3.75/5 (still positive).

#### FlyerTalk Presence

Zero mentions across 15+ threads searched. FlyerTalk discusses Brownell, Protravel International,
Travel Experts, Valerie Wilson Travel, and Signature Travel Network — but never MVT. This is because
FlyerTalk focuses on consumer-facing agents, not host agency infrastructure.

#### Propeller Travel — DEEP DIVE (Closest Competitor)

Last researched: 2026-03-29. Sources: propellertravel.com (full Playwright scrape of 22 URLs),
Trustpilot (132 reviews), UK Companies House.

**CRITICAL FINDING: Propeller Travel Ltd (#11820647) was dissolved May 2021** — possibly after
BA revoked their ticketing authority (FlyerTalk "ex-EU horror story" thread). They now operate
through a multi-entity structure:

- **Propella Travel Ltd** (#11752254, active) — Melmoths' company, IATA TIDS #96042435 only
  (identification, NOT full ticketing authority). Directors: Jonathan + Carla Melmoth.
- **Martin Masik Travel / WOAS CLUB LTD** (#14216217, active) — ticketing entity. Director:
  Martin Masik (Slovak, born 1991). Registered for SIC 79110 (travel agency) + 79120 (tour operator).
  This is who Propeller tickets through (payment form /fop-mmt/ = "Form of Payment - Martin Masik Travel").
- **eGlobalfares** — consolidator/fare aggregation platform used for foreign point-of-sale fares
- **MVT** — Virtuoso hotel access only (luxury branding, upgrades, amenities)

**No ATOL (checked CAA database), no ABTA, no consumer financial protection.** IATA TIDS ≠ full
IATA accreditation. Full IATA requires financial guarantees and grants BSP ticketing authority.
TIDS is just an identification code. Air-only bookings may not legally require ATOL in the UK,
but there is zero financial protection for consumers.

**Company details:**
- Propeller Travel Ltd: UK Company #11820647, incorporated Feb 2019, dissolved May 2021
- Director: Jonathan Frederic William Melmoth (born March 1987, British)
- Current entity: operates as trade name under Martin Masik Travel
- Address: 103 St. John Street, EC1M 4AS, London
- Contact: UK +44 203 917 4699, US +1 646 757 9954
- Founded: "Established in 2003" (16 years before incorporation)
- Team: Daniel/DK (founder, ~9 agents total: Alp, James, Gebie, Naomi, Jamie, Jen, Ruby, Dave)

**Pricing (GBP per issued ticket):**

| Service | Fee |
|---------|-----|
| Air ticket, up to 6 segments | £35 |
| Air ticket, up to 9 segments | £50 |
| Air ticket, 10+ segments OR RTW | £80 |
| Ticket reissue/change/exchange | £35 |
| BA GUF upgrade | £20 on top of standard fee |
| GUF ticket reissue | £55 |
| Trip planning (RTW/tier point/mileage runs) | £50 deposit (redeemable against booking) |
| Hotel bookings | Free |

**How they work:**
- Simple air: submit via web form (accepts ITA Matrix / GDS pastes)
- Complex air: dedicated form for multi-segment/open jaw/mixed class
- Trip planning: £50 deposit, 30 days of collaborative iteration, full booking included
- Payment: client fills out card form, card used directly for ticketing
- Communication: phone, email, WhatsApp

**RTW confirmed from Trustpilot reviews (4.5/5, 132 reviews, 96% 5-star):**
> "Daniel has been great. So good infact we have booked a second rtw in the space of 2 months."
> — Chris, Feb 2026

> "We simply could not have completed our round-the-world trip without Propeller."
> — David Miller, Jan 2026

> "I ended up with a round the world ticket that delivered me what I needed."
> — customer, Jan 2026

**BA Revocation Incident (Nov 2015):** Documented in FlyerTalk thread #1731641 (895 posts,
60 pages). After travel blog publicity drove 300-400% surge in ex-EU bookings through Propeller,
BA revoked their ability to "plate" (issue) BA tickets. Allegations: "Ticketing Abuse,"
"ticketing from fictitious points of origin." Ex-EU = booking from cheaper EU cities (Dublin,
Oslo, Brussels) for UK customers who then dropped the final return segment. Daniel lost £68,000
over 6 weeks, faced £480,000+ ADM exposure. The irony: these tickets were loss leaders at £25-75
(zero airline commission on non-transatlantic) — just a gateway to Virtuoso hotel bookings.
Service eventually restored under new agency agreement. Pivoted to GUF bookings and complex
itineraries. By 2024, BA allowed direct GUF phone bookings, eroding Propeller's main USP.

**Weakness: communication breakdown during disruptions.** Negative reviews (3 of 132) all
cite dropped follow-up on schedule changes, unanswered messages, lack of proactive communication.
Small team stretched thin — great when straightforward, bandwidth-limited during disruptions.

**Hotel partnerships:** Virtuoso, Marriott LUMINOUS, Rocco Forte Knights, Mandarin Oriental Fan Club,
Langham Couture, Dorchester Diamond Club, Belmond Bellini Club, IHG Luxury & Lifestyle, Rosewood Elite.

**FlyerTalk connection confirmed:**
> "Found out about Propeller through FlyerTalk recommendations." — James, Nov 2023

**Competitive assessment:**
- £80 (~$100) for RTW ticketing is passion-project pricing, not sustainable business pricing
- No automated validation (manual Rule 3015 compliance)
- No D-class scanning capability
- No fare optimization tooling
- Communication failures at scale
- Our advantage: automated validation, D-class scanning, fare optimization, NTP calculation,
  and capacity to scale without dropping balls

#### Additional Verified Details (Deep Research Pass 2)

**GDS is "fee based":**
MVT's own pages state: "Four GDS systems (fee based) including Multiple Hotel and Car Programs."
Exact dollar amounts are NOT disclosed anywhere publicly. "Nominal additional cost" is the only
language used. For reference, WorldVia charges $29/mo for self-ticketing GDS.

**Ticketing charge:**
HAR profile lists "Charge for Ticketing: False" — suggesting no per-ticket fee for GDS agents.
Ticketing service IS available for non-GDS agents (BookYTC users).

**FROSCH commission sharing model:**
"In this model, Frosch shares any airline commission with the agency." This applies to both the
GDS model (agent builds PNR, FROSCH handles ticketing) and the air desk model (FROSCH does
everything). FROSCH provides "upfront commissions on airline tickets" and "airline executive help
desks, specialty fares." No per-ticket fees disclosed publicly.

**$125 startup is refundable:**
"$125 start up fee that is refunded once sales goals are met" — the specific sales goal amount
is not disclosed.

**E&O insurance:**
INCLUDED per HAR profile sidebar (corrects earlier finding). MVT's join site doesn't mention E&O,
but the HAR profile explicitly lists "E&O Insurance: Included." Coverage limits/terms undisclosed.

**Client ownership:**
Confirmed: "Your book of business is your book of business, while MVT works in the background."

**Non-compete/contract terms:**
Non-compete clauses, minimum sales requirements, and termination procedures are NOT mentioned
in any public-facing material. This is consistent with their "your business is your business"
messaging but would need confirmation during onboarding.

**Seller of Travel registration:**
California and Florida only. No UK, EU, or other international registrations found.

**Amadeus RTW capabilities (from Amadeus Service Hub + Qantas Quick Reference Guide):**

CRITICAL: Sabre CANNOT auto-price oneworld Explorer fares. The Qantas oneworld Explorer Quick
Reference Guide shows "N/A" for Sabre's Quote RTW column. Sabre also has only 3 tax fields
(RTW needs many more) and Phase-IV mask field length limitations. This eliminates WorldVia's
Sabre-based self-ticketing as a viable path for OWE fare construction.

Amadeus supports RTW fare construction natively:
- `FXP/S2RW/A-DONE4` — price Business RTW and create TST for ticketing
- `FXX/S2RW` — informative pricing without TST
- `FXA/S2RW` — best pricer for RTW
- `FQDSYDSYD/VRW/10APR` — display RTW fares
- `AN*O25AUGSYDLAX` — display oneworld availability
- Amadeus calculates RW fares and taxes automatically
- "The system verifies coded fare rules. It is the agent's responsibility to ensure that all
  free-format conditions of the carrier's rules are applied correctly."
- This is exactly what `rtw validate` does — automated rule verification before ticketing

BA is native to Amadeus — BA uses Altea (Amadeus PSS), so D-class availability is most
accurately reflected in Amadeus. BA fare quoting runs through Amadeus, not Sabre/Travelport.

OWE booking codes for Business Class (DONE*): AA, BA, CX, IB, KA, MH, QF, QR, RJ, UL, S7, AY
all book in D class. Tickets can be issued on stock of AA/AY/BA/CX/IB/JJ/JL/KA/LA/LP/MH/QF/QR/
RJ/S7/UL/XL/4M (Rule 3015, Section 15).

GDS comparison for OWE:
| Capability | Amadeus | Sabre | Galileo |
|-----------|---------|-------|---------|
| Display OW availability | Yes | Yes | Yes |
| Display RTW fare | Yes | Yes | Yes |
| Auto-price/quote RTW | **Yes** | **N/A** | Yes |
| BA inventory native | **Yes (Altea)** | No | No |
| Tax field capacity | Adequate | Only 3 fields | Unknown |
| Platform | Selling Platform Connect | Red 360 | Travelport+ |
| Cryptic terminal | Yes (included) | Yes | Yes |

Source: Qantas oneworld Explorer Quick Reference Guide (PDF) —
qantas.com/content/dam/qac/oneworld-clue-cards/oneworld-quick-reference-guide.pdf
Amadeus Service Hub — servicehub.amadeus.com/c/portal/view-solution/875457

**Propeller Travel UK regulatory status:**
No evidence of ATOL or ABTA registration found for Propeller Travel. They have a UK phone number
(+44 203 917 4699) but appear to operate under MVT's US ARC/IATA accreditation. Air-only bookings
may not require ATOL (which covers flight-inclusive packages). This is a regulatory area to verify.

**MVT's "3 countries":**
MVT operates across "37 states and three countries." The three countries are not named but likely
US, Canada, and UK/Australia based on Propeller Travel's UK presence.

#### MVT Affiliate Agencies — How the Model Works in Practice

10 confirmed MVT affiliates researched (2026-03-29). All operate under own brand names:
StruxTravel (Miami), Premiere Luxury Travel (Franklin TN), The Hello Agency (Charleston SC),
Now and Zen Travel (Dallas), Elevate La Vida (San Antonio), Experience Travel (Dallas),
Sherry Lane Travel (Dallas), Cazavia Travel Architects (MVT subsidiary), Luxiva Travel (ID),
Luna World Travel.

**Pattern across all affiliates:**
- Own brand name, own website, MVT mentioned only in footer fine print
- Footer format: "Independent affiliate of Montecito Village Travel, a Virtuoso Member Agency"
- Use MVT's CST #2019108-10 (some FL affiliates also have own FST)
- No affiliate has own ARC or IATA — all use MVT's
- NONE focus on complex air ticketing — all do hotels, cruises, tours, experiences
- Virtuoso hotel perks are the primary value proposition
- We would be the FIRST MVT affiliate focused on complex RTW air fare construction

**MVT also has Florida SOT: ST38624** (in addition to California CST #2019108-10)

#### FROSCH Air Desk — Verified Fee Structure and Capabilities

FROSCH (now FROSCH by Chase Travel, JPMorgan Chase subsidiary) operates the Air Desk that
powers both Signature Travel Network and MVT's air ticketing.

**FROSCH GDS: Apollo + Sabre ONLY — NOT Amadeus.** This means FROSCH's air desk cannot use
Amadeus for OWE fare construction. For RTW/OWE, you MUST use MVT's direct Amadeus access.

**Two models confirmed (from Travel Market Report, Dec 2024):**
1. GDS Model: advisor does own PNR creation and ticketing (self-ticketing)
2. Air Desk Model: FROSCH does everything (full service)
In both: FROSCH shares airline commission with the agency.

**Client-facing fees (from frosch.com/fees):**

| Service | Fee |
|---------|-----|
| Domestic air (US/Canada/Caribbean/Mexico) | $40/ticket (max $160/PNR) |
| International air | $60/ticket (max $240/PNR) |
| Involuntary exchanges/refunds | No fee |
| Rail | $40/ticket |
| Hotel/car with air | No fee |
| Hotel/car only | $25 |

**FROSCH IC program (separate from MVT):**
- Commission: 50-90% (tiered)
- Startup: $0
- E&O insurance: Included
- GDS: Apollo + Sabre (self-ticketing available with 3-5yr GDS experience)
- Consortia: Signature Travel Network + Virtuoso (via Valerie Wilson Travel acquisition 2021)
- ICs: 500-800
- Aircom database: 100+ airline commission programs
- Global ticketing: 60+ markets, 6 continents
- Travelport+ partnership (Feb 2025): enriched multi-source content, NDC, AI curation

**Debit memo implication:** "Consolidators and air desks shift debit memo liability away from
the individual advisor" (Travel Market Report). FROSCH's air desk likely absorbs debit memo risk,
but this is not explicitly confirmed for FROSCH specifically.

**For MVT agents specifically:** FROSCH Air Desk is included at no charge. GDS access is fee-based.
The choice is: free (FROSCH tickets for you, Apollo/Sabre) vs fee (you ticket yourself, Amadeus
available). For OWE fare construction, Amadeus is required — so the fee-based GDS path is necessary.

#### Remaining Unknowns (Require Direct Contact)

1. Exact commission tier thresholds (what volume triggers 70%, 80%, 90%)
2. GDS monthly fee amount ("fee based" but no dollar figure)
3. Whether GDS-trained ICs can self-ticket or must use FROSCH air desk
4. FROSCH per-ticket fees (if any) for air desk ticketing
5. Whether FROSCH air desk has handled oneworld Explorer fare construction
6. Flat-fee option for 100% commission (Reddit-mentioned, not on MVT site)
7. E&O insurance requirement and recommended providers
8. Specific sales goal to earn back $125 startup fee
9. Contract length and termination terms
10. Whether Amadeus cryptic terminal access is available to ICs (vs only through FROSCH)

### GTC (Global Travel Collection) — Verified from HAR

**Source:** hostagencyreviews.com/hosts/gtc (profile + reviews + questions)

**Confirmed:**
- $0 startup, $0 annual, commission split not disclosed
- Sabre GDS
- ARC + IATA + CLIA accredited
- Virtuoso AND Travel Leaders Network (both!)
- 1,700 contractors, $1.5B annual sales
- Experienced agents only
- Payment solutions listed: ADX, PlanitEasy, Travel Industry Solutions (none described)
- Ticketing service for non-GDS agents included
- E&O insurance included

**Air desk — from reviews:**
> "Having the support of the air department has been such a blessing... Our Revenue Management
> team is a beast!" — Anonymous reviewer, Jan 2026

> "My business partner and I handle large volume of air ticket transactions plus high-end hotels.
> GTC team, air, hotels are always there when needed." — Grace Giso, Jan 2026

> "Best airline contracts/cruise and tour contacts. Back office is top notch." — Anonymous, Apr 2025

**Not documented:** Commission split percentage, monthly fees, client payment method, self-ticketing
capability, minimum sales requirements.

34 reviews, ALL positive. Zero negative. Either exceptional quality or heavy curation.

### Direct Travel — Verified from HAR

**Source:** hostagencyreviews.com/hosts/direct-travel (profile + reviews + questions)

**Confirmed:**
- Commission: 70-95% (no tier breakdown)
- Startup: $250
- Annual: $0-900 (range, no details on tiers)
- GDS: Apollo, Sabre, Amadeus, Galileo, Travelport, Worldspan (comprehensive)
- Virtuoso member
- 630 contractors, $1B annual sales
- Experienced agents only
- Founded 1953
- Hybrid host (host agency + travel agency)
- CRM: ClientBase, Travefy
- Itinerary builders: Axus, Travefy, Umapped
- Lead program available (leads belong to agent, no charge)
- E&O insurance NOT included
- Sub-agents allowed

**Air desk — from reviews:**
> "Our air team has excellent contracts and they are very helpful booking air for our clients."
> — Lynne Adams, Dec 2022

> "They have contracts that are untouchable on all of the major cruise lines, all of the airline."
> — Jesse Taylor, Dec 2024

Ticketing service for non-GDS agents (charges apply, amounts not specified).

**Not documented:** Client payment method, self-ticketing capability, ticketing fees, monthly fees,
minimum sales requirements.

8 reviews, ALL 5 stars. Only 1 Q&A (about seller of travel registration, not relevant to air/payment).

### Travel Edge — Verified from HAR

**Source:** hostagencyreviews.com/hosts/travel-edge (profile + reviews + questions), ADX page

**Key finding:** The earlier claim that Travel Edge has "e-commerce-like payment links" was training
data speculation, NOT verified. On their actual pages:

- ADX is listed as "Payment Solution"
- ADX handles "auto-invoicing"
- Multiple reviewers mention "booking and invoicing"
- Zero description of the client-facing payment experience

**Air Connect desk:** Entirely advisor-facing. Describes a desk that tickets for you at $50-100/ticket
with 20% commission.

**Not documented:** Commission splits, fees, GDS access, consortium membership, minimum sales,
self-ticketing capability, or any detail about how clients actually pay.

### Fora Travel — Verified from HAR + foratravel.com

**Sources:** hostagencyreviews.com/hosts/fora-travel (profile + reviews pages 1-2 of 12 + questions),
foratravel.com (homepage, /join, /join/pricing, /faq, /about-us, /partners)

**Confirmed:**
- Commission: 70-80% (70% shown in all /join examples; 80% likely Pro-tier)
- Commission payment: Weekly, direct deposit
- Startup: $0
- Annual: $299/yr or $99/quarter (14-day money-back guarantee)
- **GDS: NOT OFFERED** (explicitly stated on HAR profile)
- Consortium: Virtuoso, Expedia Group
- Accreditations: IATA, TICO, CLIA
- Minimum sales: None ("At Fora, never")
- Accepts: Beginners AND experienced
- E&O insurance: Included in subscription
- Founded: 2021

**Air ticketing:**
- In-house ticketing desk exists, but Pro-only ($100k+ annual bookings)
- "Head of Flights" on staff: Becca Bower (from /about-us)
- "Air Booking Tool" listed as a feature
- "Book flights through Fora's in-house ticketing desk" — Pro benefit only

**Technology (Advisor Portal):**
- Booking engine: 175K+ hotels, cruises, activities
- Itinerary builder
- AI assistant for research
- "Bookable Quote" feature referenced in blog title but not described
- Community platform ("Forum")
- Training: Live and on-demand

**From Reddit:**
> "Fora has a secure Portal where you can securely collect a clients credit card details
> for payments." — one11travel

> "Fora can handle the billing for planning fees with a 5% fee to cover credit card processing.
> Fora doesn't take any commission from a planning fee." — one11travel

> "I almost signed with Fora till I realized they don't focus on air ticketing." — Sad_Beginning8223

**Reviews:** 116 reviews, 4.9/5 ("First Class" on HAR). Key themes: training, community, commission
reliability, hotel booking platform. One reviewer noted commission tracking errors. One UK advisor
warned about missing ABTA/ATOL compliance. Client poaching concern raised (Fora converting clients
into advisors).

**Not documented:** Client payment UX mechanics, self-ticketing capability, Pro commission split
threshold, air ticketing desk fees/workflow.

## Reddit-Verified Payment UX Findings (r/travelagents)

Researched 2026-03-29. Sources: 15 Reddit threads from r/travelagents accessed via Grok web search
(which can read Reddit) and PullPush Reddit archive API. WebFetch/WebSearch are blocked from reddit.com
by Anthropic's crawler exclusion. All quotes are verbatim from those sources.

### The Dominant Payment Model

Agents collect client credit card details via CRM or secure form, then use those details to pay
suppliers directly. The agent never collects funds into their own account for supplier payments.

> "Most of the time, the agent calls the credit card into the vendor for payments. It's a very rare
> thing that a card would be processed by an agency vendor account and then paid separately to the
> vendor. This is usually reserved only for agent/agency fees." — CSC2377

> "You then go to each individual partner with your clients credit card details and charge each
> individually. You are just a middle man making the payments on behalf of your client in most
> cases." — one11travel

> "I've been a travel agent for 36 years. I use my clients card to book direct almost exclusively.
> I can think of very few situations where I don't book direct with the clients card." — Jabberwocky613

> "My CRM collects their payment info and I use it to pay the supplier." — Ok-Tennis-6607

**Exception — net rate/custom trip model:** Agents doing multi-country FIT itineraries with DMCs
collect payment FROM the client and pay suppliers themselves. This triggers payment processor
high-risk holds.

### CVV Collection Workaround

CRMs collect card number, expiry, billing info digitally via PCI-compliant forms. CVV is often
obtained separately via phone or text (because many CRMs can't store CVV for PCI compliance).

> "Just call the client to get the CVV. I don't collect that through Travefy or TravelJoy.
> Most clients are fine just texting it to me." — Ok-Tennis-6607

### CRMs with Payment Collection

| CRM | Notes |
|-----|-------|
| **Travefy** | Heavily mentioned. PCI-compliant. Used for itineraries AND CC auth forms |
| **TravelJoy** | Can send invoice to pay supplier direct, or pay agent |
| **Vacation CRM** | "Two clicks and send the payment information directly to the supplier" |
| **TESS** (Outside Agents) | "Looks like something out of the 90s." Can't collect CVV |
| **SuiteDash, HubSpot, Zoho** | Also mentioned as CRM options |

### Payment Processors for Service Fees

| Processor | Verdict | Evidence |
|-----------|---------|----------|
| **Stripe** | Consensus winner | "It just works" — saaket1988. Multiple endorsements. 2-day rolling deposits after first week |
| **Square** | Risky for travel | Holds 30% for 120 days (travel = high-risk). Multiple agents hit by this. Threatening to leave sometimes resolves it |
| **PayPal** | Horror stories | Account closures, 6-month fund holds. "Should be illegal for them to keep our money indefinitely" — cheermom31 |
| **Venmo Business** | Alternative | "Haven't had any problems with Venmo for Business. Not yet anyway" — cheermom31 |
| **ACH/bank transfer** | Growing | "More and more we are getting an ACH from our clients which is free from Chase" — kstewart10 |
| **Flywire** | Travel-friendly | Multiple mentions as travel-industry-friendly processor |

**Critical warning — travel is high-risk:**
> "Travel is considered high risk for payment processing. I would recommend against using a payfac
> (Stripe, Square, PayPal, etc) and setting up a direct merchant account." — highriskpayhelp

> "Travel is classed as high risk due to the time difference between paying and going on the trip.
> That window leaves you subject to chargebacks." — MerchantAdvice

### Host-Specific Payment Experiences (Reddit)

**Fora:**
> "Fora has a secure Portal where you can securely collect a clients credit card details for
> payments." — one11travel
> "Fora can handle the billing for planning fees with a 5% fee." — one11travel
> "I almost signed with Fora till I realized they don't focus on air ticketing." — Sad_Beginning8223

**Outside Agents (TESS CRM):**
> "Their CRM they include, TESS, looks like something out of the 90s. You have to use it to get
> paid, but you don't have to use it beyond that." — Emotional_Yam4959
> "Fuck I wish the one my host provides was PCI compliant. It's so fucking stupid that I have to
> pay for Travefy just to finish getting complete CC details." — Emotional_Yam4959

**WorldVia (Travel Quest Network):**
> "Takes about 6% of fees including the Stripe service fee." — Emotional_Yam4959
> "$29 a month for 90/10 split. Month to month not yearly, no set up fee." — Guatemala103105

**Nexion:**
> "Nexion is a host agency in the USA and Canada — You can do airline through them AND use their
> app for service fees." — Sad-Wolverine-1493

**Regulatory warning:**
> "Where I am it isn't even *legal* to take money direct from the client to pay a supplier. Even
> planning fees have to go through my host agency." — Emotional_Yam4959

### Air Ticketing Reality (Reddit Consensus)

> "95% of the agents I know have never directly touched GDS." — Reddit agent

> "Nobody focuses on [air ticketing] because it's not commissionable when booked on its own."
> — Ok-Tennis-6607

> "And they're such a major pain when something goes wrong, which with air is often."
> — secretreddname

**Service fee model for air:**
- $40 domestic, $100 international (standard range from Sad-Wolverine-1493)
- Consolidator markup appears as single charge to client
> "They will allow you to add a commission on, and it comes through as 1 charge. So, you add $299
> on as a service fee and their ticket receipt will say $2499." — Getreadytotravel321

**Planning fee ranges from Reddit:** $50/person, $100-$150 per booking, $300, $500, $750, $1000+
for luxury. Average fee per trip: $1,200 (2025 industry figure). 55% of advisors now charge fees.

### Virtuoso vs TLN (Reddit Agent Sentiment)

> "I've never seen a perk on Virtuoso that can't be matched some way with TLN deals." — Reddit agent

> "Access to brands is basically the same with Virtuoso and TLN with Virtuoso just making it a
> pretty package." — Reddit agent

This challenges the assumption that Virtuoso membership is a major differentiator.

### New Hosts Worth Investigating (from Reddit)

- **ProTravel International** — repeatedly recommended as quality Virtuoso host (now merged into GTC)
- **Travelmation** — recommended for experienced agents
- Only Nexion and GTC have meaningful Reddit mentions for air ticketing capability

## Strategic Implications for RTW Optimizer Business

### The Competitive Moat

Air ticketing is the orphan of the travel agent world. 95% of agents never touch GDS, nobody focuses
on air because it's not commissionable standalone, and hosts don't document flight payment UX because
it's secondary to their cruise/hotel business. The RTW optimizer's automated Rule 3015 validation,
fare optimization, and D-class scanning fill a gap that NO host or competitor addresses.

### Host Selection Considerations

**UPDATED RECOMMENDATION (post-deep research):**

**MVT is the clear choice for OWE fare construction.** Sabre (WorldVia, Nexion) cannot auto-price
oneworld Explorer fares — confirmed "N/A" in the Qantas Quick Reference Guide. Amadeus is required,
and MVT offers Amadeus + 3 other GDS systems + Virtuoso + FROSCH air desk.

**WorldVia is eliminated for OWE:** $29/mo self-ticketing uses Sabre + Worldspan. Neither can auto-
price RTW fares. Would require manual fare construction — defeating the purpose of automation.

**MVT advantages confirmed:**
- Amadeus access (fee-based) for native OWE fare construction
- Virtuoso branding for luxury RTW clients
- FROSCH air desk as safety net (JPMorgan Chase-backed)
- Partner Agency model (keep own brand)
- Proven model (Propeller Travel does RTW planning through MVT)
- $125 startup (refundable), $0 annual, 60-90% commission
- "Charge for Ticketing: False" on HAR profile
- Client ownership confirmed

**10 questions remain for onboarding call with Connie Miller (805-456-2545).**

## Sources

### Reddit r/travelagents (Payment UX Research)

- Switching from Square to Stripe — r/travelagents/comments/1kljdgh
- Credit card handling to book offline — r/travelagents/comments/1qd4xsu
- Best way to gather payments for group bookings — r/travelagents/comments/1qnppz1
- Outside Agents or Travel Quest Network — r/travelagents/comments/1edyyb2
- How to handle payments — r/travelagents/comments/16gcdj9
- Advice re: breaking into TA world / Fora — r/travelagents/comments/1ins59j
- Payment Processing (credit cards) — r/travelagents/comments/16gdfpg
- How to Safely Accept Credit Card Info — r/travelagents/comments/17b7o5r
- Credit card authorizations — r/travelagents/comments/11se5hu
- Host Agency Specializing in Airline Ticket Booking — r/travelagents/comments/14jgx4w
- Getting Started as a Travel Agent — r/travelagents/comments/1jzeua9
- Can travel agents pay with own credit cards — r/travelagents/comments/1qm5udl
- For independent travel agents: flexible payment — r/travelagents/comments/1oqbtn0
- Credit Card payments from overseas — r/travelagents/comments/185luwx
- Booking/payments — r/travelagents/comments/1c5zcrc

### Host Agency Reviews (Virtuoso-Tier Research)

- GTC Profile — hostagencyreviews.com/hosts/gtc
- GTC Reviews — hostagencyreviews.com/hosts/gtc/reviews
- GTC Questions — hostagencyreviews.com/hosts/gtc/questions
- Direct Travel Profile — hostagencyreviews.com/hosts/direct-travel
- Direct Travel Reviews — hostagencyreviews.com/hosts/direct-travel/reviews
- Direct Travel Questions — hostagencyreviews.com/hosts/direct-travel/questions
- Travel Edge Profile — hostagencyreviews.com/hosts/travel-edge
- Travel Edge Reviews — hostagencyreviews.com/hosts/travel-edge/reviews
- Fora Travel Profile — hostagencyreviews.com/hosts/fora-travel
- Fora Travel Reviews — hostagencyreviews.com/hosts/fora-travel/reviews
- Fora Travel Questions — hostagencyreviews.com/hosts/fora-travel/questions

### Fora Official

- Homepage — foratravel.com
- Join/Pricing — foratravel.com/join, foratravel.com/join/pricing
- FAQ — foratravel.com/faq
- About — foratravel.com/about-us
- Partners — foratravel.com/partners

### Montecito Village Travel (MVT)

**Official:**
- Join site — join.montecitovillagetravel.com
- About Us — join.montecitovillagetravel.com/about-us
- History — join.montecitovillagetravel.com/why-montecito-village-travel/history
- Hosted Programs — join.montecitovillagetravel.com/hosted-programs
- Partner Agency — join.montecitovillagetravel.com/hosted-programs/partner-agency
- Leisure Agent — join.montecitovillagetravel.com/hosted-programs/leisure-travel-agent
- Corporate Agent — join.montecitovillagetravel.com/hosted-programs/corporate-travel-agent
- Affiliations — join.montecitovillagetravel.com/why-montecito-village-travel/affiliations
- Benefits — join.montecitovillagetravel.com/why-montecito-village-travel/benefits
- Preferred Suppliers — join.montecitovillagetravel.com/why-montecito-village-travel/preferred-suppliers
- Team — join.montecitovillagetravel.com/agent-support/team
- Consumer site — montecitovillagetravel.com

**Reviews & Directories:**
- Host Agency Reviews Profile — hostagencyreviews.com/hosts/montecito-village-travel
- Host Agency Reviews Reviews (32) — hostagencyreviews.com/hosts/montecito-village-travel/reviews
- Find A Host Profile (11 reviews) — findahosttravelagency.com/host-agencies/montecito-village-travel/
- BBB Profile (A+) — bbb.org/us/ca/santa-barbara/profile/travel-agency/montecito-village-travel-1236-14001188
- Virtuoso Agency Page — virtuoso.com/agencies/1246/montecito-village-travel (login required)

**Press & Industry:**
- Luxury Travel Report: Half-Billion-Dollar Business — luxurytravelreport.com/compass/articles/how-montecito-village-travel-built-a-half-billion-dollar-travel-business
- Travel Weekly: From Mom-and-Pop to Host — travelweekly.com/Travel-News/Travel-Agent-Issues/Insights/The-story-of-Montecito-Village-Travel (403 paywall)
- Travel Weekly: Robin Sanchez Promoted — travelweekly.com/Travel-News/Travel-Agent-Issues/Robin-Sanchez-promoted-Montecito-Village-Travel
- Travel Weekly Power List 2025 — travelweekly.com/Power-List-2025/Montecito-Village-Travel (403 paywall)
- TravelPulse: 20 Years in Arizona — travelpulse.com/news/host/where-innovation-meets-connection-montecito-village-travel-celebrates-20-years-in-arizona

**FROSCH:**
- FROSCH website — frosch.com
- FROSCH ITA program — froschvacations.com/itas
- Travel Weekly: FROSCH leaving Virtuoso — travelweekly.com/Travel-News/Travel-Agent-Issues/Frosch-International-Travel-leaving-Virtuoso-for-Signature-Travel
- Travel Market Report: FROSCH Air Desk — travelmarketreport.com/air/articles/with-air-travel-surging-should-advisors-rethink-air-bookings

**Propeller Travel (MVT Affiliate):**
- Homepage — propellertravel.com/home/
- RTW Planning — propellertravel.com/trip-tier-points-and-mileage-run-planning-by-nufnuf77/
- Air Travel — propellertravel.com/air-travel/
- Virtuoso page — propellertravel.com/virtuoso/
- Trustpilot (4.5/5, 132 reviews) — trustpilot.com/review/propellertravel.com

**Reddit r/travelagents:**
- Virtuoso Program — r/travelagents/comments/1jrj06w
- Fora Email or Personal Email — r/travelagents/comments/1elyyhr
- Is Fora an MLM? — r/travelagents/comments/1exyfx7
- Host Agency with Access to Major Consortia — r/travelagents/comments/1bbaa7i

### Host Agency Reviews
- WorldVia Host Profile — hostagencyreviews.com/hosts/worldvia-travel-network
- WorldVia Host Reviews (166) — hostagencyreviews.com/hosts/worldvia-travel-network/reviews
- WorldVia Consortium Reviews — hostagencyreviews.com/consortia/worldvia-travel-network/reviews
- WorldVia (Travel Quest) Profile — hostagencyreviews.com/hosts/worldvia-travel-quest
- Travel Quest Network Reviews — hostagencyreviews.com/hosts/travel-quest/reviews
- WorldVia Q&A — hostagencyreviews.com/hosts/worldvia-travel-network/questions

### WorldVia Official
- GDS Air Ticketing Plans — worldviatravelnetwork.com/gds
- TRIO Platform — worldviatravelnetwork.com/trio
- Enterprise Program — worldviatravelnetwork.com/enterprise
- FAQ — worldviatravelnetwork.com/faq

### Industry & Review Sites
- BBB Profile (A+) — bbb.org/us/ga/roswell/profile/travel-services/worldvia-travel-group-0443-91826391
- Quest Travel Group BBB Complaints — bbb.org/us/ga/atlanta/profile/travel-agency/the-quest-travel-group-inc-0443-6000296/complaints
- Glassdoor (4.2/5, 17 reviews) — glassdoor.com/Reviews/WorldVia-Reviews-E2006859.htm
- Google Reviews (4.5/5, 62 reviews) — via wanderlog.com/place/details/10763445/worldvia-travel-network
- TRIO Launch Article — travelagentcentral.com/your-business/worldvia-launches-travel-booking-platform-trio
- Find A Host Profile — findahosttravelagency.com/host-agencies/worldvia-travel-network/

### FlyerTalk
- ICTravel or Nexion? — flyertalk.com/forum/travelbuzz/764589
- GDS access for personal bookings — flyertalk.com/forum/travelbuzz/471561
- Booking RTW through Sabre — flyertalk.com/forum/oneworld/905449
- Should I offer RTW booking services? — flyertalk.com/forum/oneworld/2156987
- No WorldVia-specific threads found on FlyerTalk (searched via Playwright + Google)

### Reddit r/travelagents
- FWIW new agent's thoughts on Nexion — r/travelagents/comments/1qdq8xl
- Narrowed to 3: Nexion vs KHM vs TPI — r/travelagents/comments/1rr6p1n
- Call with Nexion — r/travelagents/comments/1r75spk
- Fora vs Nexion — r/travelagents/comments/1n55hzj
- Info calls with 5 Host Agencies — r/travelagents/comments/1nf5ihu
- Career Change: Fora v. WorldVia — r/travelagents/comments/1rvh706
- Switching from Inteletravel to WorldVia — r/travelagents/comments/1rmv85x
- Questions as a new advisor (WorldVia) — r/travelagents/comments/1rl1w5g
- Getting ready to take that step (WorldVia/OA/CP) — r/travelagents/comments/1s4h7sq
- Disney Cruise TA rates (WorldVia agent) — r/travelagents/comments/1rcq3zw
