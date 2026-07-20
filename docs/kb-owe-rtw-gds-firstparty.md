# First-Party GDS Entries for oneworld Explorer RTW Fares

**Date**: 2026-07-20
**Tier**: authoritative / first-party
**Sources**: Carrier- and alliance-published agent reference material (PDFs preserved in `docs/first-party/`). This document supersedes `kb-gds-segment-stitching.md` for anything concerning GDS *entry syntax* — that older doc reverse-documents `rtw/booking.py` and cites FlyerTalk, so it is **not** an independent source.

This is the authoritative reference for how a oneworld Explorer (OWE) round-the-world fare is **displayed and priced** in the GDS. Every command below is quoted verbatim from a carrier or alliance publication, not inferred. Where a required PNR-build step is *not* covered by a first-party source, it is listed explicitly under "Not first-party confirmed" so it is never mistaken for verified syntax.

## Provenance

| File (`docs/first-party/`) | Publisher | What it establishes |
|---|---|---|
| `qantas-oneworld-quick-reference-guide.pdf` | Qantas (oneworld carrier) | Amadeus/Galileo/Sabre command table: display availability, display RTW fare, **quote RTW fare** |
| `qantas-oneworld-fare-products.pdf` | Qantas | Fare basis codes per cabin; Amadeus/Galileo/Sabre quote entries; **"Auto-pricing available: No"** |
| `qantas-global-explorer-31Mar21.pdf` | Qantas | Global Explorer fare rule (sibling product; endorsement + validating-carrier guidance) |
| `oneworld-alliance-explorer-rule3015.pdf` | oneworld alliance | Rule 3015 itself: fare basis table, RBD fallback, ticket endorsement text |

Amadeus **Service Hub** (`servicehub.amadeus.com`) solution pages were cited by automated research but are **auth-gated (HTTP 403)** — they could not be independently read and are treated as *unverified*.

## Amadeus GDS entries (verbatim, from the Qantas oneworld clue card)

```
Display availability   AN*O25AUGSYDLAX
Display RTW fare        FQDSYDSYD/VRW/10APR
Quote / price RTW       FXP/S2RW/A-LONE4
```

From the fare-products card (shows the fare-owner qualifier and the Circle variant):

```
Display RTW    FQDLHRLHR/VRW/ABA/1FEB      (/A BA = restrict to fare owner BA)
Quote RTW      FXP/S2RW/L-LGLOB26          (Global Explorer, /L- override form)
Display Circle FQDLHRLHR/VCT/ABA/1FEB      (VCT = Circle global indicator)
Quote Circle   FXP/S2CT/L-LCIR22
```

**Anatomy of the pricing entry `FXP/S2RW/A-LONE4`:**
- `FXP` — price the itinerary and store the TST.
- `/S2RW` — apply the **`RW` (round-the-world) global indicator** to a segment. The card states verbatim: *"'2' refers to the 1st flight sector in the itinerary."* The number is the PNR line/tattoo of the **first flown segment** (surface sectors count in numbering), **not** a literal `2`.
- `/A-LONE4` — force the OWE **fare basis**. `/A-` is the *guaranteed* form used for oneworld Explorer (`ONE` fares). Global Explorer / Circle use `/L-` (override). Substitute the actual ticket's fare basis (`DONE4`, `AONE3`, …).

**Cross-GDS equivalents** (from the same cards, for reference):

| | Amadeus | Galileo | Sabre/Abacus |
|---|---|---|---|
| Display RTW | `FQDSYDSYD/VRW/10APR` | `FQSYD10APRSYD/QF-RTW` | `FQSYDSYD10APRRW-QF` |
| Quote RTW | `FXP/S2RW/A-LONE4` | `FQ@LONE4` | `WPRW` |

## Root cause: auto-pricing does not work

The Qantas fare-products card states **"Auto-pricing available: No"** for these fare products. This is the authoritative explanation for why `rtw/booking.py` currently emits a non-RTW ticket: a bare `FXP` invokes auto-pricing, which for an OWE itinerary either fails or returns the cheapest published fare — never the RTW fare. The RTW identity comes **only** from the explicit `/S{N}RW` global indicator plus the forced `/A-{fare basis}`.

## Fare basis codes (oneworld alliance Rule 3015)

The fare basis is determined by cabin (leading letter) and continent count (trailing digit) — it is the tool's `TicketType` value verbatim:

| Continents | Economy | Business | First |
|---|---|---|---|
| 3 | LONE3 | IONE3* / DONE3 | AONE3 |
| 4 | LONE4 | DONE4 | AONE4 |
| 5 | LONE5 | DONE5 | AONE5 |
| 6 | LONE6 | DONE6 | AONE6 |

`* IONE3` = business 3-continent, offered from select markets only. Child/infant tickets append `CH` / `IN` to the base fare basis. See also [`fares.db`], which files `DONE4` etc. as `fare_basis` with `booking_class = D` across every eligible carrier.

## Reservation booking designators (RBD) and fallback

Primary business RBD is **D**. First-party fallback rule (Rule 3015, reservations section, verbatim):

> "Passengers travelling on DONE\* Business Class fares may book **B Class (except AA) or H Class on AA**."
> First Class fares may fall back to **Y Class**.

This corroborates `rtw/data/carriers.yaml` (`rtw_fallback_class: B`, AA `= H`). See `kb`-cross-reference to the per-carrier RBD table.

## Ticket endorsement (oneworld alliance Rule 3015, §18)

Endorsement text, verbatim:

> "The original and reissued ticket must be annotated **Valid on oneworld only / non ref** in the endorsement box."

The correct endorsement string is therefore **`VALID ON ONEWORLD ONLY / NON REF`**. (Reissues additionally require `NON REF/ XXX` where `XXX` = the OWE fare basis code.) Endorsement fare-basis references: First `AONE*`, Business `IONE3/DONE*`, Economy `LONE*`.

## Not first-party confirmed (require live-terminal / agent confirmation)

The clue cards cover fare **display and pricing** only. The following PNR-build mechanics are standard Amadeus but were **not** found in any first-party source (only in auth-gated / unverified references). They must be confirmed by an agent on a live Amadeus terminal before being trusted or emitted as tool output:

- Long-sell segment entry format (`SS…`)
- Surface sector entry (`SIARNK` vs bare `ARNK`)
- OSI advisory element (`OS YY …`)
- Validating/plating carrier element (`FV…`) and the `/R,VC-` pricing qualifier
- Diagnostic/quote-only pricing (`FXX`), TST display (`TQT`), fare selection (`FXT`)
- Tour code (`FT`) — OWE is a published fare; a tour code is likely not required

## Implications for `rtw/booking.py`

1. **Replace bare `FXP`** with `FXP/S{N}RW/A-{fare_basis}` where `{N}` is the first flown segment's line number and `{fare_basis}` is `ticket.type.value`. This is the single change that makes the output an RTW ticket.
2. Keep `FQD…/VRW` (the `/VRW` global-indicator qualifier is first-party correct); match the first-party date form (`/1FEB`, no `/D`).
3. Emit the endorsement `VALID ON ONEWORLD ONLY / NON REF`.
4. **Omit** the "not first-party confirmed" PNR-build lines until an agent confirms their syntax, rather than emitting plausible-but-unverified commands an agent might type.
