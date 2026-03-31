#!/usr/bin/env python3
"""Ingest RTW knowledge base markdown files into SQLite.

Reads all docs/kb-*.md and docs/host-agency-research.md files, parses them
into articles/sections/findings/tags/questions, and upserts into knowledge.db.

Usage:
    python3 scripts/ingest_kb.py
    python3 scripts/ingest_kb.py --verbose
    python3 scripts/ingest_kb.py --force   # re-ingest even if unchanged
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
SCHEMA_PATH = PROJECT_ROOT / "rtw" / "data" / "kb_schema.sql"
DB_PATH = PROJECT_ROOT / "rtw" / "data" / "knowledge.db"
CARRIERS_YAML = PROJECT_ROOT / "rtw" / "data" / "carriers.yaml"

# ---------------------------------------------------------------------------
# Category / tier inference from article content
# ---------------------------------------------------------------------------
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "cost": ["surcharge", "yq", "yr", "fare", "pricing", "apd", "duty", "cost", "saving"],
    "availability": ["married", "availability", "d-class", "expertflyer", "inventory", "o&d"],
    "booking": ["booking", "gds", "sabre", "amadeus", "segment stitching", "pnr", "ticketing"],
    "rules": ["rule 3015", "iata", "coupon", "sequential", "rebooking", "change fee"],
    "strategy": ["playbook", "strategy", "optimization", "dummy dates", "codeshare", "war story"],
    "tools": ["expertflyer", "ita matrix", "gcmap"],
    "business": ["host agency", "worldvia", "nexion", "khm", "commission", "arc"],
    "research": ["research", "analysis", "revenue management"],
}

TIER_KEYWORDS: dict[str, list[str]] = {
    "playbook": ["playbook", "step by step", "phase 1", "phase 2"],
    "deep-dive": ["deep-dive", "technical mechanics", "table of contents"],
    "war-story": ["war stor", "real experience", "booking narrative"],
    "research": ["host agency research", "revenue management", "academic"],
}

# ---------------------------------------------------------------------------
# Question generation templates
# ---------------------------------------------------------------------------
QUESTION_TEMPLATES = [
    "What is {heading}?",
    "How does {heading} work?",
    "What should I know about {heading}?",
]

QUESTION_TEMPLATES_HOW = [
    "How do I {heading}?",
    "What is the best approach to {heading}?",
]

QUESTION_TEMPLATES_LIST = [
    "What are the {heading}?",
    "Can you list the {heading}?",
]

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Section:
    heading: str
    heading_level: int
    content: str
    sort_order: int
    parent_idx: int | None = None  # index into parent section list
    word_count: int = 0
    db_id: int | None = None


@dataclass
class Finding:
    finding: str
    finding_type: str
    carrier: str | None = None
    route: str | None = None
    amount: float | None = None
    currency: str | None = None
    unit: str | None = None
    confidence: float = 0.8
    section_idx: int | None = None  # index into section list


@dataclass
class Question:
    question: str
    answer_summary: str | None = None
    section_idx: int | None = None


@dataclass
class Article:
    slug: str
    title: str
    category: str
    tier: str
    summary: str | None
    source_path: str
    content_hash: str
    word_count: int
    confidence: float = 0.8
    sections: list[Section] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)
    tags: list[tuple[str, str]] = field(default_factory=list)  # (name, tag_type)
    cross_ref_slugs: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Carrier codes from carriers.yaml
# ---------------------------------------------------------------------------

def load_carrier_codes() -> set[str]:
    """Load 2-letter IATA carrier codes from carriers.yaml (simple parse, no PyYAML needed)."""
    codes: set[str] = set()
    if not CARRIERS_YAML.exists():
        return codes
    for line in CARRIERS_YAML.read_text().splitlines():
        # Top-level keys like "AA:", "BA:", etc.
        m = re.match(r"^([A-Z][A-Z0-9]):\s*$", line)
        if m:
            codes.add(m.group(1))
    return codes


CARRIER_CODES: set[str] = set()  # populated at runtime


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def slug_from_path(path: Path) -> str:
    """Derive slug from filename: kb-yq-surcharge-optimization.md -> kb-yq-surcharge-optimization."""
    return path.stem


def infer_category(title: str, content: str) -> str:
    """Infer article category from title + content keywords."""
    text_lower = (title + " " + content[:2000]).lower()
    scores: dict[str, int] = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for kw in keywords if kw in text_lower)
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "reference"


def infer_tier(title: str, content: str) -> str:
    """Infer article tier from title + content keywords."""
    text_lower = (title + " " + content[:3000]).lower()
    for tier, keywords in TIER_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return tier
    return "reference"


def extract_title(lines: list[str]) -> str:
    """Extract title from the first H1 heading."""
    for line in lines[:10]:
        if line.startswith("# ") and not line.startswith("##"):
            return line[2:].strip()
    return "Untitled"


def extract_summary(lines: list[str]) -> str | None:
    """Extract summary from text after H1 but before first H2.

    Looks for Executive Summary section or first substantive paragraph.
    """
    in_preamble = False
    summary_lines: list[str] = []
    for line in lines:
        if line.startswith("# ") and not line.startswith("##"):
            in_preamble = True
            continue
        if in_preamble:
            if line.startswith("## "):
                break
            stripped = line.strip()
            if stripped and not stripped.startswith("---") and not stripped.startswith("**Source"):
                # Skip metadata lines like "Last updated:", "Date:", etc.
                if not re.match(r"^(Last updated|Date|Source|Scraped|Knowledge base compiled)", stripped, re.IGNORECASE):
                    summary_lines.append(stripped)
    text = " ".join(summary_lines).strip()
    # Truncate to ~500 chars
    if len(text) > 500:
        text = text[:497] + "..."
    return text if text else None


def split_sections(lines: list[str]) -> list[Section]:
    """Split markdown into sections at H2/H3 boundaries."""
    sections: list[Section] = []
    current_heading: str | None = None
    current_level: int = 2
    current_lines: list[str] = []
    sort_order = 0

    # Track H2 parent for H3 sections
    last_h2_idx: int | None = None

    for line in lines:
        heading_match = re.match(r"^(#{2,3})\s+(.+)$", line)
        if heading_match:
            # Save previous section
            if current_heading is not None:
                content = "\n".join(current_lines).strip()
                if content:
                    parent = last_h2_idx if current_level == 3 else None
                    sec = Section(
                        heading=current_heading,
                        heading_level=current_level,
                        content=content,
                        sort_order=sort_order,
                        parent_idx=parent,
                        word_count=len(content.split()),
                    )
                    sections.append(sec)
                    if current_level == 2:
                        last_h2_idx = len(sections) - 1
                    sort_order += 1

            level = len(heading_match.group(1))
            current_heading = heading_match.group(2).strip()
            current_level = level
            current_lines = []
        else:
            current_lines.append(line)

    # Final section
    if current_heading is not None:
        content = "\n".join(current_lines).strip()
        if content:
            parent = last_h2_idx if current_level == 3 else None
            sec = Section(
                heading=current_heading,
                heading_level=current_level,
                content=content,
                sort_order=sort_order,
                parent_idx=parent,
                word_count=len(content.split()),
            )
            sections.append(sec)
            if current_level == 2:
                last_h2_idx = len(sections) - 1

    return sections


# ---------------------------------------------------------------------------
# Tag extraction
# ---------------------------------------------------------------------------

def extract_tags(title: str, content: str) -> list[tuple[str, str]]:
    """Extract (name, tag_type) pairs from article content."""
    tags: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(name: str, tag_type: str) -> None:
        key = (name, tag_type)
        if key not in seen:
            seen.add(key)
            tags.append(key)

    full_text = title + " " + content

    # Carrier codes
    for code in CARRIER_CODES:
        # Match carrier codes as whole words (not inside longer words)
        if re.search(rf"\b{code}\b", full_text):
            add(code, "carrier")

    # Airport codes: 3-letter uppercase surrounded by word boundaries
    # but not matching common English words or carrier codes
    COMMON_WORDS = {
        "THE", "AND", "FOR", "BUT", "NOT", "YOU", "ALL", "CAN", "HER", "WAS",
        "ONE", "OUR", "OUT", "DAY", "HAD", "HAS", "HIS", "HOW", "ITS", "MAY",
        "NEW", "NOW", "OLD", "SEE", "WAY", "WHO", "BOY", "DID", "GET", "HIM",
        "LET", "SAY", "SHE", "TOO", "USE", "KEY", "PER", "VIA", "MAX", "ANY",
        "FEE", "USD", "EUR", "GBP", "NOK", "SEK", "CHF", "AUD", "JPY", "ZAR",
        "INR", "LKR", "EGP", "NPR", "PKR", "HUF", "TOP", "TIP", "YES", "WHY",
        "TAX", "PAY", "ADD", "ASK", "BIG", "END", "FAR", "FLY", "GOT", "OWN",
        "RUN", "SET", "TRY", "TWO", "APD", "YQR", "MSC", "FAQ", "GDS", "PNR",
        "POC", "POS", "RTW", "NTP", "FTS", "SQL", "BBB", "CRM", "HAR", "URL",
        "CVV", "ARC", "SWP", "JAL", "SGD", "INV", "HKD", "NDC",
    }
    airport_pattern = re.compile(r"\b([A-Z]{3})\b")
    for m in airport_pattern.finditer(full_text):
        code = m.group(1)
        if code not in COMMON_WORDS and code not in CARRIER_CODES:
            add(code, "airport")

    # Topic tags from content
    topic_map = {
        "yq": "YQ", "surcharge": "surcharges", "d-class": "D-class",
        "married segment": "married-segments", "codeshare": "codeshare",
        "apd": "APD", "rebooking": "rebooking", "dummy date": "dummy-dates",
        "plating carrier": "plating-carrier", "first segment": "first-segment",
        "o&d": "O&D-control", "availability": "availability",
        "expertflyer": "ExpertFlyer", "sabre": "Sabre", "amadeus": "Amadeus",
        "host agency": "host-agency", "gds": "GDS-access",
        "worldvia": "WorldVia", "nexion": "Nexion",
        "rule 3015": "Rule-3015",
    }
    text_lower = full_text.lower()
    for keyword, tag_name in topic_map.items():
        if keyword in text_lower:
            tag_type = "tool" if tag_name in ("ExpertFlyer", "Sabre", "Amadeus") else "topic"
            add(tag_name, tag_type)

    # Fare types
    for fare in ("DONE4", "DONE3", "AONE4", "AONE3", "LONE4", "LONE3"):
        if fare in full_text:
            add(fare, "fare_type")

    return tags


# ---------------------------------------------------------------------------
# Finding extraction
# ---------------------------------------------------------------------------

# Currency symbols and codes
CURRENCY_MAP = {
    "$": "USD", "USD": "USD", "US$": "USD",
    "EUR": "EUR", "€": "EUR",
    "GBP": "GBP", "£": "GBP",
    "NOK": "NOK", "SEK": "SEK", "CHF": "CHF",
    "AUD": "AUD", "JPY": "JPY", "ZAR": "ZAR",
}

# Pattern: $1,234 or EUR 1,234 or £1,234.56
MONEY_PATTERN = re.compile(
    r"(?:(?P<sym>[$€£]))\s*(?P<amount1>[\d,]+(?:\.\d{1,2})?)"
    r"|(?P<code>USD|EUR|GBP|NOK|SEK|CHF|AUD|JPY|ZAR|US\$)\s*(?P<amount2>[\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)

# Percentage pattern
PCT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*%")

# Route pattern: 3-letter codes joined by dash or arrow
ROUTE_PATTERN = re.compile(r"\b([A-Z]{3})\s*[-→]\s*([A-Z]{3})\b")


def extract_findings(sections: list[Section], full_text: str) -> list[Finding]:
    """Extract monetary amounts, percentages, and rule-like statements as findings."""
    findings: list[Finding] = []
    seen_findings: set[str] = set()

    for sec_idx, section in enumerate(sections):
        content = section.content
        lines = content.split("\n")

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("---"):
                continue

            # Extract monetary findings
            for m in MONEY_PATTERN.finditer(stripped):
                sym = m.group("sym")
                code = m.group("code")
                amount_str = m.group("amount1") or m.group("amount2")
                if not amount_str or not amount_str.strip():
                    continue

                try:
                    amount = float(amount_str.replace(",", ""))
                except ValueError:
                    continue
                if amount == 0:
                    continue

                currency = CURRENCY_MAP.get(sym or code or "", "USD")

                # Get context: the sentence containing this amount
                context = stripped
                if len(context) > 200:
                    # Find the sentence containing the match
                    pos = m.start()
                    start = max(0, context.rfind(".", 0, pos) + 1)
                    end = context.find(".", pos)
                    if end == -1:
                        end = len(context)
                    context = context[start:end + 1].strip()

                # Deduplicate
                dedup_key = f"{amount}:{currency}:{context[:80]}"
                if dedup_key in seen_findings:
                    continue
                seen_findings.add(dedup_key)

                # Detect carrier and route
                carrier = None
                for cc in CARRIER_CODES:
                    if re.search(rf"\b{cc}\b", context):
                        carrier = cc
                        break

                route = None
                route_m = ROUTE_PATTERN.search(context)
                if route_m:
                    route = f"{route_m.group(1)}-{route_m.group(2)}"

                # Determine finding_type
                finding_type = "cost"
                ctx_lower = context.lower()
                if "sav" in ctx_lower:
                    finding_type = "comparison"
                elif "rule" in ctx_lower or "fee" in ctx_lower or "penalty" in ctx_lower:
                    finding_type = "rule"

                # Determine unit
                unit = None
                if "per segment" in ctx_lower or "/segment" in ctx_lower or "/seg" in ctx_lower:
                    unit = "per segment"
                elif "per transaction" in ctx_lower:
                    unit = "per transaction"
                elif "per person" in ctx_lower or "/person" in ctx_lower or "pp" in ctx_lower:
                    unit = "per person"
                elif "per month" in ctx_lower or "/month" in ctx_lower or "/mo" in ctx_lower:
                    unit = "per month"

                findings.append(Finding(
                    finding=context[:500],
                    finding_type=finding_type,
                    carrier=carrier,
                    route=route,
                    amount=amount,
                    currency=currency,
                    unit=unit,
                    section_idx=sec_idx,
                ))

            # Extract percentage findings (only meaningful ones)
            for m in PCT_PATTERN.finditer(stripped):
                pct = float(m.group(1))
                if pct == 0 or pct == 100:
                    continue
                context = stripped
                if len(context) > 200:
                    pos = m.start()
                    start = max(0, context.rfind(".", 0, pos) + 1)
                    end = context.find(".", pos)
                    if end == -1:
                        end = len(context)
                    context = context[start:end + 1].strip()

                dedup_key = f"pct:{pct}:{context[:80]}"
                if dedup_key in seen_findings:
                    continue
                seen_findings.add(dedup_key)

                carrier = None
                for cc in CARRIER_CODES:
                    if re.search(rf"\b{cc}\b", context):
                        carrier = cc
                        break

                findings.append(Finding(
                    finding=context[:500],
                    finding_type="statistic",
                    carrier=carrier,
                    amount=pct,
                    currency=None,
                    unit="%",
                    section_idx=sec_idx,
                ))

    return findings


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------

def generate_questions(sections: list[Section]) -> list[Question]:
    """Generate natural-language questions from section headings."""
    questions: list[Question] = []

    for sec_idx, section in enumerate(sections):
        heading = section.heading
        # Strip leading numbering like "1.2" or "3."
        clean = re.sub(r"^\d+(\.\d+)*\.?\s*", "", heading).strip()
        if not clean or len(clean) < 5:
            continue

        clean_lower = clean.lower()

        # Choose templates based on heading style
        if clean_lower.startswith("how to") or clean_lower.startswith("how do"):
            templates = QUESTION_TEMPLATES_HOW
        elif any(clean_lower.startswith(w) for w in ("the ", "key ", "complete ", "common ")):
            templates = QUESTION_TEMPLATES_LIST
        else:
            templates = QUESTION_TEMPLATES

        # Generate 1-2 questions per section
        for template in templates[:2]:
            q = template.format(heading=clean)
            # Generate a brief answer from first ~100 chars of content
            answer = section.content[:200].replace("\n", " ").strip()
            if len(answer) > 150:
                answer = answer[:147] + "..."

            questions.append(Question(
                question=q,
                answer_summary=answer if answer else None,
                section_idx=sec_idx,
            ))

    return questions


# ---------------------------------------------------------------------------
# Cross-reference detection
# ---------------------------------------------------------------------------

def detect_cross_references(slug: str, content: str, all_slugs: list[str]) -> list[str]:
    """Detect references to other KB articles in the content."""
    refs: list[str] = []
    content_lower = content.lower()

    for other_slug in all_slugs:
        if other_slug == slug:
            continue

        # Match by slug mention (e.g., "kb-yq-surcharge-optimization")
        if other_slug.lower() in content_lower:
            refs.append(other_slug)
            continue

        # Match by descriptive reference patterns
        # Convert slug to keywords: "kb-married-segments" -> ["married", "segments"]
        keywords = [w for w in other_slug.replace("kb-", "").split("-") if len(w) > 3]
        if len(keywords) >= 2:
            # Check if all significant keywords appear close together
            if all(kw in content_lower for kw in keywords):
                refs.append(other_slug)

    return refs


# ---------------------------------------------------------------------------
# Parse a single markdown file into an Article
# ---------------------------------------------------------------------------

def parse_article(path: Path, all_slugs: list[str]) -> Article:
    """Parse a markdown file into an Article with sections, findings, tags, questions."""
    raw = path.read_text(encoding="utf-8")
    content_hash = compute_hash(raw)
    lines = raw.splitlines()

    title = extract_title(lines)
    slug = slug_from_path(path)
    summary = extract_summary(lines)
    word_count = len(raw.split())

    category = infer_category(title, raw)
    tier = infer_tier(title, raw)

    sections = split_sections(lines)
    findings = extract_findings(sections, raw)
    questions = generate_questions(sections)
    tags = extract_tags(title, raw)
    cross_refs = detect_cross_references(slug, raw, all_slugs)

    source_path = f"docs/{path.name}"

    return Article(
        slug=slug,
        title=title,
        category=category,
        tier=tier,
        summary=summary,
        source_path=source_path,
        content_hash=content_hash,
        word_count=word_count,
        sections=sections,
        findings=findings,
        questions=questions,
        tags=tags,
        cross_ref_slugs=cross_refs,
    )


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------

def init_db(db: sqlite3.Connection) -> None:
    """Create tables from schema if they don't exist."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    # Split on statement boundaries and execute each
    # We need to handle triggers which contain semicolons inside BEGIN...END
    db.executescript(schema_sql)


def get_existing_hash(db: sqlite3.Connection, slug: str) -> str | None:
    """Get the content_hash for an existing article, or None if not found."""
    row = db.execute(
        "SELECT content_hash FROM articles WHERE slug = ?", (slug,)
    ).fetchone()
    return row[0] if row else None


def delete_article(db: sqlite3.Connection, slug: str) -> None:
    """Delete an article and all cascading data (sections, findings, etc.)."""
    db.execute("DELETE FROM articles WHERE slug = ?", (slug,))


def get_or_create_tag(db: sqlite3.Connection, name: str, tag_type: str) -> int:
    """Get existing tag ID or create a new one."""
    row = db.execute(
        "SELECT id FROM tags WHERE name = ? AND tag_type = ?", (name, tag_type)
    ).fetchone()
    if row:
        return row[0]
    cur = db.execute(
        "INSERT INTO tags (name, tag_type) VALUES (?, ?)", (name, tag_type)
    )
    return cur.lastrowid


def insert_article(db: sqlite3.Connection, article: Article) -> int:
    """Insert an article and all its related data. Returns article ID."""
    cur = db.execute(
        """INSERT INTO articles (slug, title, category, tier, summary, source_path,
           content_hash, word_count, confidence)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (article.slug, article.title, article.category, article.tier,
         article.summary, article.source_path, article.content_hash,
         article.word_count, article.confidence),
    )
    article_id = cur.lastrowid

    # --- Sections ---
    section_id_map: dict[int, int] = {}  # section index -> db id
    for idx, sec in enumerate(article.sections):
        parent_db_id = None
        if sec.parent_idx is not None and sec.parent_idx in section_id_map:
            parent_db_id = section_id_map[sec.parent_idx]

        cur = db.execute(
            """INSERT INTO sections (article_id, heading, heading_level, content,
               parent_id, sort_order, word_count)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (article_id, sec.heading, sec.heading_level, sec.content,
             parent_db_id, sec.sort_order, sec.word_count),
        )
        section_id_map[idx] = cur.lastrowid

    # --- Tags ---
    for tag_name, tag_type in article.tags:
        tag_id = get_or_create_tag(db, tag_name, tag_type)
        db.execute(
            "INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (?, ?)",
            (article_id, tag_id),
        )

    # --- Findings ---
    for finding in article.findings:
        section_db_id = None
        if finding.section_idx is not None and finding.section_idx in section_id_map:
            section_db_id = section_id_map[finding.section_idx]

        cur = db.execute(
            """INSERT INTO findings (article_id, section_id, finding, finding_type,
               carrier, route, amount, currency, unit, confidence)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (article_id, section_db_id, finding.finding, finding.finding_type,
             finding.carrier, finding.route, finding.amount, finding.currency,
             finding.unit, finding.confidence),
        )
        finding_id = cur.lastrowid

        # Tag findings with their carrier and route airports
        if finding.carrier:
            tag_id = get_or_create_tag(db, finding.carrier, "carrier")
            db.execute(
                "INSERT OR IGNORE INTO finding_tags (finding_id, tag_id) VALUES (?, ?)",
                (finding_id, tag_id),
            )
        if finding.route:
            for airport in finding.route.split("-"):
                airport = airport.strip()
                if len(airport) == 3 and airport.isalpha():
                    tag_id = get_or_create_tag(db, airport, "airport")
                    db.execute(
                        "INSERT OR IGNORE INTO finding_tags (finding_id, tag_id) VALUES (?, ?)",
                        (finding_id, tag_id),
                    )

    # --- Questions ---
    for question in article.questions:
        section_db_id = None
        if question.section_idx is not None and question.section_idx in section_id_map:
            section_db_id = section_id_map[question.section_idx]

        db.execute(
            """INSERT INTO questions (question, article_id, section_id, answer_summary)
               VALUES (?, ?, ?, ?)""",
            (question.question, article_id, section_db_id, question.answer_summary),
        )

    return article_id


def insert_cross_references(
    db: sqlite3.Connection, articles: list[Article]
) -> int:
    """Insert cross-references between articles. Returns count inserted."""
    count = 0
    for article in articles:
        source_row = db.execute(
            "SELECT id FROM articles WHERE slug = ?", (article.slug,)
        ).fetchone()
        if not source_row:
            continue

        for target_slug in article.cross_ref_slugs:
            target_row = db.execute(
                "SELECT id FROM articles WHERE slug = ?", (target_slug,)
            ).fetchone()
            if not target_row:
                continue

            db.execute(
                """INSERT OR IGNORE INTO cross_references
                   (source_article_id, target_article_id, relationship)
                   VALUES (?, ?, 'related')""",
                (source_row[0], target_row[0]),
            )
            count += 1
    return count


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------

def collect_files() -> list[Path]:
    """Collect all KB markdown files to ingest."""
    files: list[Path] = []

    # docs/kb-*.md
    for f in sorted(DOCS_DIR.glob("kb-*.md")):
        files.append(f)

    # docs/host-agency-research.md
    har = DOCS_DIR / "host-agency-research.md"
    if har.exists():
        files.append(har)

    return files


def print_stats(db: sqlite3.Connection) -> None:
    """Print database statistics."""
    tables = [
        ("articles", "articles"),
        ("sections", "sections"),
        ("tags", "tags"),
        ("findings", "findings"),
        ("questions", "questions"),
        ("cross_references", "cross_references"),
        ("sources", "sources"),
    ]
    print("\n  Database contents:")
    for label, table in tables:
        row = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        print(f"    {label:20s}: {row[0]:>5d}")

    # FTS check
    for fts_table in ("sections_fts", "findings_fts", "questions_fts"):
        row = db.execute(f"SELECT COUNT(*) FROM {fts_table}").fetchone()
        print(f"    {fts_table:20s}: {row[0]:>5d}")

    # Top tags
    rows = db.execute(
        """SELECT tag_type, COUNT(*) FROM tags GROUP BY tag_type ORDER BY COUNT(*) DESC"""
    ).fetchall()
    print("\n  Tag types:")
    for tag_type, cnt in rows:
        print(f"    {tag_type:20s}: {cnt:>5d}")


def main() -> None:
    global CARRIER_CODES

    parser = argparse.ArgumentParser(description="Ingest KB markdown files into SQLite")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--force", "-f", action="store_true", help="Re-ingest even if unchanged")
    args = parser.parse_args()

    # Load carrier codes
    CARRIER_CODES = load_carrier_codes()
    if args.verbose:
        print(f"Loaded {len(CARRIER_CODES)} carrier codes: {sorted(CARRIER_CODES)}")

    # Collect files
    files = collect_files()
    if not files:
        print("No KB files found in docs/")
        return
    print(f"Found {len(files)} KB files")

    # All slugs for cross-reference detection
    all_slugs = [slug_from_path(f) for f in files]

    # Initialize DB
    db = sqlite3.connect(str(DB_PATH))
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    init_db(db)

    # Parse and ingest each file
    ingested = 0
    skipped = 0
    articles: list[Article] = []

    for path in files:
        slug = slug_from_path(path)
        raw = path.read_text(encoding="utf-8")
        content_hash = compute_hash(raw)

        # Check if unchanged
        existing_hash = get_existing_hash(db, slug)
        if existing_hash == content_hash and not args.force:
            if args.verbose:
                print(f"  SKIP {slug} (unchanged)")
            skipped += 1
            # Still parse for cross-references
            article = parse_article(path, all_slugs)
            articles.append(article)
            continue

        # Parse
        article = parse_article(path, all_slugs)
        articles.append(article)

        # Upsert: delete old + insert new in a transaction
        action = "UPDATE" if existing_hash else "INSERT"
        if existing_hash:
            delete_article(db, slug)

        insert_article(db, article)
        ingested += 1

        print(
            f"  {action:6s} {slug}"
            f"  ({len(article.sections)} sections, "
            f"{len(article.findings)} findings, "
            f"{len(article.questions)} questions, "
            f"{len(article.tags)} tags)"
        )

    # Cross-references (needs all articles inserted first)
    # Clear and rebuild
    db.execute("DELETE FROM cross_references")
    xref_count = insert_cross_references(db, articles)
    if xref_count > 0:
        print(f"  Cross-references: {xref_count}")

    db.commit()

    # Stats
    print(f"\nIngested: {ingested}, Skipped (unchanged): {skipped}")
    print_stats(db)

    # Checkpoint WAL so main file has full size, then close
    db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    db.close()

    db_size_bytes = DB_PATH.stat().st_size
    if db_size_bytes > 1024 * 1024:
        print(f"\nDatabase: {DB_PATH} ({db_size_bytes / (1024*1024):.1f} MB)")
    else:
        print(f"\nDatabase: {DB_PATH} ({db_size_bytes / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
