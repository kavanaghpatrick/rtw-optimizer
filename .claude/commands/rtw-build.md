---
description: Full route-building workflow (search, build, verify)
allowed-tools: AskUserQuestion, Read, Write, Bash(python3:*), Glob, Grep
model: opus
---

# RTW Route Builder

Orchestrate the full route-building workflow: define segments, verify nonstop service, build YAML, check D-class availability.

## Step 1: Gather Parameters

Use AskUserQuestion to collect trip parameters:

Question 1:
- header: "Origin"
- question: "Which city will you start and end your trip from?"
- options:
  - label: "LAX (Los Angeles)"
    description: "DONE4: ~$7,200 — strong Pacific connections"
  - label: "SYD (Sydney)"
    description: "DONE4: $8,800 — QF/JL hub"
  - label: "LHR (London)"
    description: "DONE4: ~$6,800 — BA hub, most connections"
  - label: "DOH (Doha)"
    description: "DONE4: ~$5,200 — QR hub, generous D-class"
- multiSelect: false

Question 2:
- header: "Direction"
- question: "Which direction around the world?"
- options:
  - label: "Westbound"
    description: "Origin → Asia → SWP → Middle East/Europe → Origin"
  - label: "Eastbound"
    description: "Origin → Europe → Americas → Asia → Origin"
- multiSelect: false

Question 3:
- header: "Ticket"
- question: "Which ticket type?"
- options:
  - label: "DONE4 (Recommended)"
    description: "Business class, 4 continents"
  - label: "DONE3"
    description: "Business class, 3 continents"
  - label: "LONE4"
    description: "Economy, 4 continents"
- multiSelect: false

Question 4:
- header: "Dates"
- question: "When do you want to depart?"
- options:
  - label: "Apr 2026"
    description: "Northern spring, good availability"
  - label: "Jun 2026"
    description: "Early summer"
  - label: "Sep 2026"
    description: "Northern autumn, good availability"
  - label: "Flexible"
    description: "Will optimize around D-class availability"
- multiSelect: false

## Step 2: Design Route Variants

Based on origin and direction, propose 2-3 route variants. Use domain knowledge from CLAUDE.md:

**Key carrier routing knowledge:**
- JL: HND-SYD nonstop, HND-LAX nonstop (NOT from NRT)
- QR: DOH is hub — DOH-LAX D9, DOH-LHR D9, DOH-SYD, DOH-HND all nonstop
- AY: HND-HEL nonstop (NOT from NRT). HEL-LAX Mon/Wed/Thu only, D-class very scarce
- BA: LHR-LAX D9 (5+ daily), LHR-JFK
- CX: HKG hub (lower NTP: 25% rate)

**NTP optimization:** Prefer JL, QR, AY (50% rate) over CX, QF (25%) or BA, AA (~0 on D-class).

For each variant, write the route string, e.g.: `LAX-HND:JL,HND-SYD:JL,SYD-DOH:QR,DOH-LAX:QR`

Present variants to user with AskUserQuestion.

## Step 3: Verify Nonstop Service

For EACH variant the user selects, run nonstop verification:

```
python3 -m rtw check-nonstop --route "ROUTE_STRING"
```

If any segment has NO nonstop service:
1. Report which segments failed
2. Suggest alternatives (e.g., HND instead of NRT, DOH-LAX instead of HEL-LAX)
3. Ask user to choose a fix or try a different variant

**Do NOT proceed to Step 4 until all segments are nonstop-verified.**

## Step 4: Build Itinerary

Build the YAML itinerary:

```
python3 -m rtw build --route "ROUTE_STRING" --origin ORIGIN --type TICKET_TYPE --departure DATE --validate --ntp
```

Review the output:
- Confirm validation PASS (20/20 rules)
- Note the NTP total
- Check segment dates make sense

If validation fails, diagnose and fix (adjust route, dates, or type).

Write to file:

```
python3 -m rtw build --route "ROUTE_STRING" --origin ORIGIN --type TICKET_TYPE --departure DATE --out itineraries/FILENAME.yaml
```

## Step 5: D-class Availability Check

Run full D-class verification:

```
python3 -m rtw verify itineraries/FILENAME.yaml
```

Review results. For any segment WITHOUT nonstop D-class, scan dates to find availability:

```
python3 -m rtw scan-dates ORIGIN DEST CARRIER --from DATE --to DATE
```

Use `--dow` filter if carrier has limited schedule (e.g., AY HEL-LAX: `--dow mon,wed,thu`).

## Step 6: Optimize & Finalize

If any segments lack D-class nonstop:
1. Suggest date adjustments
2. Suggest carrier/routing swaps
3. Ask user which approach to take

Once all segments confirmed:

```
python3 -m rtw analyze itineraries/FILENAME.yaml
```

Present the final summary:
- Route overview with all segments
- Total NTP
- D-class status per segment
- Estimated cost
- Booking readiness assessment

Use AskUserQuestion:
- header: "Next"
- question: "Route is ready. What would you like to do?"
- options:
  - label: "Generate booking script"
    description: "Create phone booking script for travel agent"
  - label: "Build another variant"
    description: "Try a different routing for comparison"
  - label: "Done"
    description: "Save and finish"
- multiSelect: false
