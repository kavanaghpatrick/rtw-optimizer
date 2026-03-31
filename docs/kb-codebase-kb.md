# RTW Knowledge Base, Scripts, and Tooling

Technical documentation for the knowledge base system, ingestion pipeline, scraping tools, debug scripts, and reference data files.

## 1. Knowledge Base System

### Architecture Overview

The KB is a three-layer system: markdown source files in `docs/` are parsed by an ingestion script into a SQLite database (`rtw/data/knowledge.db`), which is queried through a Python API (`rtw/kb.py`) exposed as CLI subcommands under `python3 -m rtw kb`.

```
docs/kb-*.md  --->  scripts/ingest_kb.py  --->  rtw/data/knowledge.db  --->  rtw/kb.py  --->  CLI (rtw kb ...)
                                                     ^                                          |
                                                     |                                          v
                                           rtw/data/kb_schema.sql                     JSON / Rich / Plain output
```

### Database Schema (`rtw/data/kb_schema.sql`)

The schema uses 8 core tables plus 3 FTS5 virtual tables:

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `articles` | Top-level documents (1 per markdown file) | slug, title, category, tier, content_hash, confidence |
| `sections` | Heading-level chunks within articles | article_id, heading, heading_level, content, parent_id |
| `findings` | Atomic facts extracted from text | article_id, finding, finding_type, carrier, route, amount, currency |
| `tags` | Flexible labels with typed categories | name, tag_type (carrier/airport/topic/tool/fare_type) |
| `questions` | Natural-language questions each section answers | question, article_id, section_id, answer_summary |
| `cross_references` | Directed links between articles | source_article_id, target_article_id, relationship |
| `sources` | External references (FlyerTalk threads, docs, URLs) | source_type, title, url, thread_id, credibility |
| Junction tables | `article_tags`, `section_tags`, `finding_tags`, `article_sources` | Foreign key pairs with optional relevance scores |

**FTS5 Virtual Tables** (porter unicode61 tokenizer):
- `sections_fts` -- primary search surface (heading + content)
- `findings_fts` -- structured fact search
- `questions_fts` -- natural-language question matching

All FTS tables are kept in sync via AFTER INSERT/UPDATE/DELETE triggers.

**Current DB Stats** (as of 2026-03-30):
- 16 articles, 674 sections, 915 findings, 1348 questions, 182 tags

### Ingestion Pipeline (`scripts/ingest_kb.py`)

Reads all `docs/kb-*.md` and `docs/host-agency-research.md` files, parses them into structured data, and upserts into `knowledge.db`.

**Usage:**
```bash
python3 scripts/ingest_kb.py           # Incremental (skip unchanged files)
python3 scripts/ingest_kb.py --force   # Re-ingest all files
python3 scripts/ingest_kb.py --verbose # Show detailed progress
```

**Pipeline stages for each file:**

1. **Hash check** -- SHA-256 of file content compared against `articles.content_hash`; skip if unchanged (unless `--force`)
2. **Title extraction** -- First H1 heading
3. **Summary extraction** -- Text between H1 and first H2 (truncated to 500 chars)
4. **Category inference** -- Keyword matching against predefined category lists (cost, availability, booking, rules, strategy, tools, business, research)
5. **Tier inference** -- Keyword matching for playbook, deep-dive, war-story, research
6. **Section splitting** -- At H2/H3 boundaries; H3 sections track parent H2
7. **Tag extraction** -- Carrier codes from `carriers.yaml`, airport codes (3-letter IATA, filtered against common English words), topic keywords, fare types
8. **Finding extraction** -- Monetary amounts (regex for $, EUR, GBP, etc.), percentages, with carrier/route detection and finding_type classification (cost/comparison/rule/statistic)
9. **Question generation** -- Template-based from section headings ("What is {heading}?", "How does {heading} work?", etc.)
10. **Cross-reference detection** -- Matches slug names and significant keywords across all articles
11. **Upsert** -- Delete old article (CASCADE) then insert fresh data within a transaction
12. **Cross-reference rebuild** -- All cross-references rebuilt after all articles inserted
13. **WAL checkpoint** -- `PRAGMA wal_checkpoint(TRUNCATE)` to consolidate

### Query Interface (`rtw/kb.py`)

The `KnowledgeBase` class provides 10 public query methods:

| Method | Purpose | Strategy |
|--------|---------|----------|
| `search(query)` | Natural-language full-text search | Synonym expansion -> FTS5 on sections -> FTS5 on findings -> tag fallback |
| `carrier_lookup(carrier)` | All knowledge about a carrier | findings.carrier match -> article_tags carrier -> FTS fallback |
| `fact_lookup(subject, predicate)` | Structured finding lookup | Exact carrier/route match -> LIKE fallback on finding text |
| `answer(question)` | Question answering | questions_fts match -> sections_fts supplement -> boost tips/strategies for "how" questions |
| `related(chunk_id)` | Cross-reference traversal | Cross-referenced articles -> shared tags -> same article |
| `context_brief(origin, ticket_type, carriers, cities)` | Contextual booking briefing | Multi-dimensional: origin advice + carrier warnings + hub knowledge + ticket implications |
| `topic_search(topic)` | Topic-based retrieval | Tag match -> article sections -> FTS fallback |
| `stale_articles(max_age_days)` | Freshness check | Articles older than threshold |
| `freshness_report()` | KB-wide freshness summary | Fresh/stale counts, oldest/newest dates |
| `stats()` | Database statistics | Row counts per table, carrier count, freshness |

**Synonym expansion** -- A built-in dictionary maps domain abbreviations to canonical terms (e.g., "MSC" -> "married segment", "YQ" -> "surcharge", "APD" -> "air passenger duty"). Also checks a `synonyms` table if present.

**Scoring** -- Results scored on a 0-10 scale using FTS5 BM25 rank, boosted by: heading match (+1.5), carrier finding match (+2.0), question term overlap (+1.5), tip/strategy heading (+2.0 for "how" questions).

### CLI Commands

All KB commands are under the `kb` subcommand group:

```bash
python3 -m rtw kb search "married segment CX"           # Natural language search
python3 -m rtw kb search "YQ optimization" --carrier BA  # Carrier-filtered search
python3 -m rtw kb carrier CX                             # All CX knowledge
python3 -m rtw kb lookup BA yq                           # Structured fact lookup
python3 -m rtw kb ask "How do I avoid high surcharges?"  # Question answering
python3 -m rtw kb related 42                             # Related content
python3 -m rtw kb brief --origin OSL --carrier CX,QR     # Contextual briefing
python3 -m rtw kb topic married-segments                 # Topic search
python3 -m rtw kb list                                   # List all articles
python3 -m rtw kb carriers                               # Carrier mention stats
python3 -m rtw kb topics                                 # Topic tag listing
python3 -m rtw kb sources                                # External source listing
python3 -m rtw kb stats                                  # Database statistics
python3 -m rtw kb stale                                  # Stale content check
```

All commands support `--json` for machine-readable output (designed for Claude Code agents) and `--plain` for non-Rich output.

### KB Articles Currently Ingested

| Slug | Category | Tier | Words |
|------|----------|------|-------|
| host-agency-research | business | research | 8,874 |
| kb-apd-avoidance | cost | reference | 3,565 |
| kb-codeshare-strategies | availability | reference | 1,146 |
| kb-current-playbook-2026 | availability | playbook | 1,185 |
| kb-definitive-playbook-2026 | cost | playbook | 7,431 |
| kb-dummy-dates-strategy | availability | research | 4,497 |
| kb-expertflyer-accuracy | availability | reference | 2,866 |
| kb-gds-segment-stitching | booking | reference | 3,766 |
| kb-hub-od-control | availability | research | 1,380 |
| kb-married-segments | availability | deep-dive | 5,651 |
| kb-oslo-origin | cost | reference | 4,526 |
| kb-rebooking-rules | rules | reference | 5,909 |
| kb-revenue-management | availability | deep-dive | 4,324 |
| kb-segment-dropping | rules | reference | 4,162 |
| kb-war-stories | cost | war-story | 1,527 |
| kb-yq-surcharge-optimization | cost | reference | 3,987 |

---

## 2. FlyerTalk Scraper (`scripts/ft_scrape.py`)

A Playwright-based headless scraper that extracts post content from FlyerTalk forum threads.

**Usage:**
```bash
python3 scripts/ft_scrape.py URL                    # Scrape first 3 pages
python3 scripts/ft_scrape.py URL --pages 10         # Scrape up to 10 pages
python3 scripts/ft_scrape.py URL --out posts.json   # Save to file
```

**How it works:**

1. Launches headless Chromium via Playwright with a desktop user agent
2. Navigates to the thread URL
3. Closes cookie banners if present
4. Attempts multiple CSS selectors for post containers (`div.post`, `article.post`, `li.postbit`, `div[id^="post_message_"]`, `div.postbody`)
5. Falls back to `table.post`, `blockquote.postcontent`, and finally body text splitting by FlyerTalk-specific patterns ("Join Date", "Senior Member", etc.)
6. For multi-page threads, derives page URLs by inserting `-N` before `.html` in the URL
7. Each post text is truncated to 3,000 characters

**Rate limiting:** 2-second delay between pages.

**Output format (JSON):**
```json
[
  {
    "index": 0,
    "text": "Post content...",
    "page": 1,
    "url": "https://www.flyertalk.com/forum/..."
  }
]
```

---

## 3. Other Scripts

### `scripts/build_fares_db.py` -- Fares Database Builder

Converts the Excel file `rtw/data/rtw_fares_all.xlsx` into SQLite at `rtw/data/fares.db`.

Creates 3 tables:
- `fares` (34,693 rows) -- All individual fare filings: origin, carrier, fare_basis, booking_class, cabin, fare_usd, validity dates
- `cheapest` (631 rows) -- Cheapest fare by type/origin
- `summary` (634 rows) -- Summary statistics

Indexes on origin, fare_basis, carrier, cabin, and composite origin+fare_basis.

```bash
python3 scripts/build_fares_db.py
```

### `scripts/explore_expertflyer.py` -- Initial EF Session Capture

Opens a visible Chromium browser for manual ExpertFlyer login. Captures screenshots at each stage and saves session cookies to `~/.rtw/expertflyer_session.json` for reuse by other scripts. Dumps DOM analysis of form elements, tables, and availability-related selectors.

### `scripts/explore_ef_pages.py` -- EF Page Explorer

Uses the saved session to systematically explore ExpertFlyer pages. Tests direct URLs, navigates to Flight Availability and Awards & Upgrades pages, captures DOM structure and screenshots. Includes a 2-minute monitoring period for interactive exploration.

### `scripts/ef_test_search.py` -- EF Search Results Capture

Opens a browser with saved session, waits for the user to fill in a search form and click Search. Monitors for results (detects booking class patterns like "D2", "F3") and captures screenshots, HTML, and detailed DOM analysis including availability-specific patterns (flight numbers, booking classes, "sold out"/"waitlist" keywords).

### `scripts/ef_debug_page.py` -- Quick EF Debug

Programmatic diagnostic that uses the `ExpertFlyerScraper` class directly. Builds a results URL for NRT-LAX, captures a screenshot and HTML, then checks for specific CSS selectors. Useful for testing scraper selector correctness.

### `scripts/validate_harness.py` -- Claude Code Harness Validator

Validates the Claude Code configuration files (CLAUDE.md, settings.json, commands, rules). Checks file existence, section headings, tech stack mentions, permission allowlists/denylists, command frontmatter, path-scoped rules, and .gitignore entries. Exits non-zero on failure.

```bash
python3 scripts/validate_harness.py
```

### `scripts/scrape_worldvia_reddit.py` -- WorldVia Research Scraper

Async Playwright scraper that searches Reddit and Google for WorldVia / Travel Quest Network agent experiences. Runs in 5 phases:
1. Reddit search pages (old.reddit.com for easier parsing)
2. Google searches for review sites
3. Reddit thread content extraction (posts + comments)
4. Direct Reddit URL attempts with broader queries
5. Review site scraping (BBB, HostAgencyReviews, Glassdoor)

Output saved to `scripts/worldvia_research.json`.

---

## 4. Data Files (`rtw/data/`)

| File | Format | Purpose | Size/Content |
|------|--------|---------|--------------|
| `carriers.yaml` | YAML | oneworld carrier reference: name, eligibility, YQ tier, booking class, NTP method | 17 carriers (AA through WY) |
| `fares.yaml` | YAML | Base fares by origin city (CAI, OSL, LHR, etc.) for AONE/DONE/LONE x 3-6 continents | ~8 origin cities |
| `continents.yaml` | YAML | Airport-to-continent overrides (edge cases like CAI=EU_ME, GUM=Asia, Hawaii=N_America) + country-to-continent defaults | 211 lines |
| `surcharges.yaml` | YAML | Per-carrier YQ estimates (USD/segment), plating carrier comparisons | JL: $12 to QF: $334 |
| `hubs.yaml` | YAML | Hub connection table for route generation: inter-TC hub pairs with carrier and priority | TC1-TC2, TC2-TC3, etc. |
| `same_cities.yaml` | YAML | Airport groups treated as same city (TYO: NRT/HND, LON: LHR/LGW/STN/LCY/LTN, etc.) | ~15 city groups |
| `ntp_rates.yaml` | YAML | BA New Tier Points earning rates: revenue-based carriers + distance-based by booking class | Per carrier, per booking class |
| `through_flights.yaml` | YAML | Known through-flights with cross-continent impact (QF1/2 SYD-SIN-LHR, BA15/16, etc.) | Cross-continent and same-continent categories |
| `kb_schema.sql` | SQL | Knowledge base schema definition (tables, indexes, FTS5, triggers) | 255 lines |
| `knowledge.db` | SQLite | Populated KB database | 16 articles, 674 sections, 915 findings |
| `fares.db` | SQLite | Fare filing database from Excel source | 34,693 fares, 631 cheapest, 634 summary |
| `rtw_fares_all.xlsx` | Excel | Source fare data (3 sheets: All Fares, Cheapest by Fare Type, Summary) | Input for build_fares_db.py |
| `templates/` | YAML | Itinerary templates: `done4-eastbound.yaml`, `done5-eastbound.yaml` | Pre-built route templates |

---

## 5. KB Integration with the Codebase

### Three Consumer Paths

1. **CLI users** -- `python3 -m rtw kb search/carrier/ask/...` with Rich-formatted tables and panels. Registered as a Typer subcommand group in `rtw/cli.py` (line 57-67).

2. **Claude Code agents** -- Same CLI with `--json` flag for machine-readable output. Agents call `python3 -m rtw kb search "query" --json` via the Bash tool and parse the JSON response. The `context_brief` command is particularly designed for agents building booking scenarios.

3. **Programmatic Python** -- Direct import: `from rtw.kb import KnowledgeBase; kb = KnowledgeBase(); results = kb.search("married segments")`. Used internally by any module that needs travel intelligence.

### Data Flow

```
FlyerTalk threads -----> ft_scrape.py -----> JSON -----> Manual curation -----> docs/kb-*.md
                                                                                     |
                                                                                     v
Excel fare filings -----> build_fares_db.py -----> fares.db               ingest_kb.py
                                                                                     |
                                                                                     v
                                                                              knowledge.db
                                                                                     |
                                                                                     v
                                                                         rtw/kb.py (KnowledgeBase)
                                                                                     |
                                                               +---------------------+--------------------+
                                                               |                     |                    |
                                                           CLI output          JSON for agents     Python import
```

### Key Design Decisions

- **SQLite + FTS5** over a vector database: Simpler, no external dependencies, porter stemming + BM25 ranking is sufficient for a domain-specific corpus of ~60K words
- **Content-addressed caching**: SHA-256 hashes skip re-ingestion of unchanged files
- **Cascading deletes**: Removing an article cascades to all sections, findings, questions, and tag associations
- **Confidence tracking**: Articles and findings carry confidence scores (0.0-1.0) for quality weighting
- **Staleness tracking**: Articles have `created_at`/`updated_at` timestamps; `kb stale` identifies content older than 90 days
- **Domain synonym expansion**: Query "MSC" automatically expands to "married segment"; "YQ" expands to "surcharge"
- **Multi-strategy search**: FTS5 sections -> FTS5 findings -> tag-based fallback -> carrier-specific fallback, with score merging and deduplication
