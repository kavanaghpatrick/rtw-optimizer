# Knowledge Base: Hawaiian Airlines oneworld Integration

**Date**: 2026-04-24
**Effective date of membership**: 2026-04-22
**Sources**: oneworld press release (2026-04-23), Alaska Air Group news (2026-04-23), PR Newswire (2026-04-22), One Mile at a Time (2026-04-22, code-retirement piece), LoyaltyLobby (2026-04-24), Head for Points (2026-04-24), Prince of Travel (2026-04-22), Simple Flying (2026-04 livery piece), Beat of Hawaii (Tahiti frequency bump), The Flight Expert (HA fare classes), Australian Frequent Flyer (oneworld Explorer RTW guide), RTW Optimizer codebase (`rtw/data/carriers.yaml`, `rtw/rules/geography.py`, `rtw/rules/carriers.py`).

---

## Table of Contents

1. [Membership Summary](#1-membership-summary)
2. [The Code Collision: HA → AS](#2-the-code-collision-ha--as)
3. [RTW Explorer Eligibility](#3-rtw-explorer-eligibility)
4. [Rule 3015 Interaction](#4-rule-3015-interaction)
5. [Route Network That Matters for RTW](#5-route-network-that-matters-for-rtw)
6. [Booking Class, YQ, and NTP — Open Questions](#6-booking-class-yq-and-ntp--open-questions)
7. [Implications for the RTW Optimizer](#7-implications-for-the-rtw-optimizer)
8. [Validator Integration](#8-validator-integration)
9. [Open Items / Wait-and-See](#9-open-items--wait-and-see)
10. [Sources](#10-sources)

---

## 1. Membership Summary

Hawaiian Airlines (HA) became the **16th full oneworld member airline** on **2026-04-22**, simultaneously with the overnight Amadeus-to-Sabre passenger service system migration. The effective operational date of 22 April aligns the PSS cutover with alliance launch; oneworld's own press release is dated 23 April, and Alaska Air Group's news release matches.

Hawaiian joined as a **distinct member** — not oneworld connect, not under Alaska's umbrella. The oneworld press release lists "Alaska Airlines" and "Hawaiian Airlines" as separate entries among the 16. However, the two airlines operate on a **single operating certificate** (consolidated in October 2025) and now share the same reservation system, loyalty program backend, and IATA flight code.

**Confidence: confirmed** (three independent official sources).

## 2. The Code Collision: HA → AS

This is the single most important operational fact for RTW ticket construction:

> **The "HA" IATA flight code was retired on 2026-04-22. All Hawaiian-operated flights are now marketed under the "AS" code.**

Source: One Mile at a Time, 2026-04-22 — "starting today, Hawaiian Airlines will begin using the 'AS' IATA code, which belongs to Alaska Airlines." Corroborated by Simple Flying.

**Consequence for the RTW Optimizer:**

- A Honolulu-to-Tokyo flight that was `HA441` on 2026-04-21 is `AS441` (or similar) on 2026-04-22.
- Passenger Name Records, GDS displays, ExpertFlyer results, and booking confirmations will carry `AS` as the marketing carrier for ex-Hawaiian routes.
- An itinerary from an agent's system or a legacy booking before 22 April may still reference `HA` — this is a **historical artifact**, not a live code.

For the validator: treating `AS` as the canonical code for all Hawaiian-operated segments is correct. The `HA:` entry in `carriers.yaml` exists as an alias for historical/ticketed-under-HA segments and for alliance completeness; it should not be the expected marketing code on new segments.

**Confidence: confirmed** (primary source is OMAAT reporting the GDS cutover in real time; corroborated by Simple Flying and the Alaska Air Group communications around the PSS migration).

## 3. RTW Explorer Eligibility

The oneworld Explorer round-the-world ticket is defined by Rule 3015 and the oneworld Explorer Conditions of Travel. Eligibility flows from full oneworld membership — when a carrier becomes a full member, its flights become eligible for Explorer fare construction automatically, provided the carrier files the required fare basis and makes the requisite booking classes available.

As of 2026-04-24:

- **Alliance-level eligibility**: yes. Hawaiian is a full member; its flights are within the Explorer universe. **Confirmed** via oneworld's own "Round the World with oneworld" page, though that page at fetch time (24 April) had not yet been refreshed to drop the "set to join in 2026" language — a cache lag.
- **Practical ticketing**: not yet independently confirmed. No public FlyerTalk or agent-facing report yet confirms that a BA (125) or AA (001) plate has cleanly ticketed a Hawaiian-operated segment on a conjunction Explorer ticket post-integration. Partner programs are live for Avios (Head for Points, 2026-04-24) and AAdvantage (anecdotal OMAAT comment, 2026-04-22), suggesting interline filings are in place.

**Confidence: likely yes** (alliance-level); **unknown** (RTW-ticketing operational confirmation).

## 4. Rule 3015 Interaction

The Hawaii routing restriction in Rule 3015 is **unchanged** by HA's oneworld entry:

- Hawaii airports (HNL, OGG, KOA, LIH, ITO) remain classified in **North America (TC1)**.
- The directional rule remains: Asia/SWP → HNL → US/Canada mainland is allowed; US mainland → HNL → back to US mainland is not; HNL is a single-visit point within the RTW routing.
- **Backtracking to Hawaii after leaving is prohibited.**

In the RTW Optimizer codebase, `rtw/rules/geography.py::HawaiiAlaskaRule` implements this restriction as a **purely airport-set-based check** — it references the airport codes in `_HAWAII_AIRPORTS` and makes no reference to any carrier. HA joining oneworld therefore requires **zero modification** to this rule.

What *does* change is the **eligible carrier universe** for Hawaii-involving segments: previously the only oneworld metal into/out of HNL was JL (HNL-NRT), QF (HNL-SYD), and AS feeders from the US West Coast; now the full former-HA transpacific grid (HND, NRT, KIX, SYD, AKL, PPT, RAR, PPG) is on oneworld metal.

**Confidence: confirmed** (Australian Frequent Flyer RTW guide + direct codebase reading).

## 5. Route Network That Matters for RTW

Hawaiian's intercontinental network as of April 2026, under the new AS code:

| Origin | Destination | Frequency | Aircraft | Notes |
|--------|-------------|-----------|----------|-------|
| HNL | HND (Tokyo Haneda) | 14 wk | A330-200 | Up from 12 late 2025 |
| HNL | NRT (Tokyo Narita) | ~daily | A330-200 | Part of 31 wk HNL-Japan |
| HNL | KIX (Osaka) | ~daily | A330-200 | |
| HNL | SYD (Sydney) | Daily | A330-200 | Boosted from 5x wk |
| HNL | AKL (Auckland) | Seasonal | A330-200 | |
| HNL | PPT (Papeete, Tahiti) | 2x wk (from 2026-03) | A330-200 | Up from 1x |
| HNL | RAR (Rarotonga, Cook Is.) | Weekly | A330-200 | |
| HNL | PPG (Pago Pago, Am. Samoa) | Weekly | — | |
| SEA | NRT | Daily | 787-9 | Launched 2025-05-12, Alaska livery |
| SEA | ICN | 5x wk | 787-9 | Launched 2025-09-12 |

**Suspended routes (2025-2026)**: HNL-BOS (2025-11-19), HNL-FUK (2025-11-19), HNL-ICN (2025-11-21, replaced by SEA-ICN).

**New RTW possibilities not previously available on oneworld metal:**

- Hawaii-South Pacific (PPT/RAR/PPG) — first-ever oneworld metal to these exotic points.
- SEA as a transpacific gateway via 787-9 — an alternative to JL NRT/HND out of US West Coast.
- HNL as a Pacific hub — not previously viable with only JL and QF serving.

**Confidence: confirmed** (official Alaska Air Group news + Beat of Hawaii + Simple Flying + AirlineGeeks on the suspensions).

## 6. Booking Class, YQ, and NTP — Open Questions

**All three data points below are provisional.** Post-integration (48 hours old at time of writing), partner programs have not yet published earning charts, and the Sabre inventory for partner-award classes on Hawaiian-operated flights has not yet fully populated.

- **RTW booking class**: unknown. The historical HA fare-class map (The Flight Expert) lists D as HA's "discount F/J — partner award" bucket. oneworld Explorer business typically books into D on most members (BA, CX, IB, JL, QF, QR, FJ). AA is the exception at H. **Likely** D, but **unverified** on a real conjunction ticket.
- **YQ filings**: historically Hawaiian files almost no YQ. Expect per-segment YQ in the very-low tier (<$50); placeholder value of $30 reasonable pending real filings visible in Sabre.
- **NTP earning (BA Executive Club, AA AAdvantage, QF Frequent Flyer, JL Mileage Bank)**: mileage crediting is live (confirmed by Head for Points for Avios; OMAAT anecdotal report for AA), but published earning charts (percentage by booking class) are not yet released by any of the major partner programs. Treat HA NTP as distance-based with a "rates TBD" placeholder.

See also: `kb-yq-surcharge-optimization` for the per-carrier YQ pattern; `kb-revenue-management` for how partner-award classes get filed.

## 7. Implications for the RTW Optimizer

- **`rtw/data/carriers.yaml`**: add an `HA:` entry with `eligible: true`. This propagates through the data-driven eligibility rule automatically.
- **Rules engine**: no rule logic changes required. The Hawaii geographic rule is orthogonal; the carrier eligibility rule is fully data-driven.
- **Scraper / carrier name mapping**: for completeness, add "hawaiian" / "hawaiian airlines" to any hardcoded name→IATA maps used by flight scrapers. Low-priority since new flights market as AS anyway.
- **Hubs**: HNL is a new oneworld Pacific hub with HA joining. Consider promoting it in `rtw/data/hubs.yaml` for search-time hub routing, but not required for validation correctness.
- **Fares**: `rtw/data/fares.db` indexes base fares by origin; HA does not change the Explorer origin universe (RTW is not sold ex-HNL), so no change needed.

## 8. Validator Integration

The validator requires a **single change** to accept Hawaiian-operated segments in a oneworld Explorer itinerary:

Add to `rtw/data/carriers.yaml`:

```yaml
HA:
  name: Hawaiian Airlines
  alliance: oneworld
  eligible: true
  ntp_method: distance
  yq_tier: low
  yq_estimate_per_segment: 30
  rtw_booking_class: D
  notes: "Joined oneworld 2026-04-22 as 16th full member. HA IATA code retired same day; Hawaiian-operated flights now marketed under AS on single Alaska Air Group operating certificate. Values are provisional; booking class and YQ unverified until partner inventory stabilizes and partner earning charts publish."
```

This triggers the following automatically:

- `rtw/rules/carriers.py::EligibleCarrierRule` loads `_ELIGIBLE_CODES` from `carriers.yaml` at import time — HA becomes an eligible code without code changes.
- `rtw/rules/geography.py::HawaiiAlaskaRule` is unchanged (purely geographic, no carrier checks).
- `rtw/rules/carriers.py::QRNotFirstRule` is QR-specific, unaffected.
- `rtw/rules/carriers.py::QFJQCodeshareRule.restricted_plating = {"AS", "IB"}` — not extended to HA. If future research confirms HA-plated stock also has JQ codeshare restrictions, that set should be reopened; for now the conservative default is to leave it.

**No rule file needs editing.** The design pays off here: new members integrate via a single YAML block.

See also: `kb-codebase-architecture` for the rules-engine topology.

## 9. Open Items / Wait-and-See

1. **Confirm RTW booking class** via ExpertFlyer on a real HNL-Asia or SEA-Asia Hawaiian-operated segment in D class. Update the `rtw_booking_class` field once observed.
2. **Wait for partner earning charts** (BA, AA, QF, JL). Once published, populate `rtw/data/ntp_rates.yaml` with HA-specific rates.
3. **Confirm actual YQ filings** in Sabre; most likely near-zero but current value is a placeholder.
4. **Verify interline ticketing** on a conjunction Explorer ticket (BA-plate or AA-plate) includes an AS-marketed Hawaiian-operated segment. FlyerTalk and OMAAT should produce first-hand reports within weeks.
5. **Check for any Rule 3015 amendment** specifically referencing Hawaii transpacific carriage by oneworld metal. No public amendment is visible as of 2026-04-24; IATA fare rule updates are often behind ATPCO paywalls.

## 10. Sources

- [oneworld welcomes Hawaiian Airlines (oneworld.com, 2026-04-23)](https://www.oneworld.com/news/oneworld-welcomes-hawaiian-airlines)
- [Hawaiian Airlines joins oneworld alliance (Alaska Air Group news, 2026-04-23)](https://news.alaskaair.com/company/hawaiian-airlines-joins-oneworld-alliance-connecting-hawaii-to-the-world/)
- [Aloha! oneworld welcomes Hawaiian Airlines (PR Newswire, 2026-04-22)](https://www.prnewswire.com/news-releases/aloha-oneworld-welcomes-hawaiian-airlines-to-alliance-302751822.html)
- [End of an era: HA code retired, replaced by AS (One Mile at a Time, 2026-04-22)](https://onemileatatime.com/news/hawaiian-ha-code-retired-replaced/)
- [Hawaiian Airlines finally joins oneworld (One Mile at a Time, 2026-04-22)](https://onemileatatime.com/news/hawaiian-airlines-oneworld/)
- [Earn and spend Avios on Hawaiian Airlines (Head for Points, 2026-04-24)](https://www.headforpoints.com/2026/04/24/hawaiian-airlines-joins-oneworld-alliance/)
- [Hawaiian Airlines now a new member of oneworld (LoyaltyLobby, 2026-04-24)](https://loyaltylobby.com/2026/04/24/hawaiian-airlines-now-a-new-member-of-oneworld/)
- [oneworld Welcomes Hawaiian as 16th Member (Prince of Travel, 2026-04-22)](https://princeoftravel.com/news/hawaiian-airlines-joins-oneworld/)
- [Hawaiian Cuts Three Long-Haul Routes (AirlineGeeks, 2025-08-13)](https://airlinegeeks.com/2025/08/13/hawaiian-cuts-three-long-haul-routes/)
- [Alaska Air Group launches global gateway in Seattle (news.alaskaair.com, 2025)](https://news.alaskaair.com/destinations/alaska-air-group-launches-new-global-gateway-in-seattle-with-unveiling-of-nonstop-routes-on-hawaiian-airlines-to-tokyo-narita-and-seoul-incheon/)
- [Twice-Weekly Tahiti From March 2026 (Beat of Hawaii)](https://beatofhawaii.com/twice-weekly-tahiti-flights-coming-to-hawaiian-starting-march-2026/)
- [oneworld Explorer RTW Guide (Australian Frequent Flyer)](https://www.australianfrequentflyer.com.au/oneworld-explorer-rtw-guide/) — Hawaii routing rules summary
- [oneworld Explorer Rule 3015 PDF (oneworld.com asset)](https://assets.ctfassets.net/m9ph4qvas97u/7DV0fxwM9hSh41URJye4Mr/9de5375cc98e390f6261704e35d7f37f/231005-oneworld-alliance-round-the-world-oneworld-explorer.pdf)
- [Hawaiian fare classes (The Flight Expert)](https://www.theflightexpert.com/hawaiian-airlines-fare-classes/)
- [FlyerTalk: Hawaiian joining Oneworld thread](https://www.flyertalk.com/forum/british-airways-british-airways-club/2174109-hawaiian-joining-oneworld-2026-a.html) — sparse at research time
