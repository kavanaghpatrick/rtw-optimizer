"""RTW Knowledge Base -- query interface for travel intelligence SQLite DB.

Provides search, carrier lookup, fact lookup, question answering,
cross-reference traversal, freshness checking, and contextual briefings
against the knowledge.db FTS5-indexed SQLite database.

Three consumers:
1. CLI commands (python3 -m rtw kb search/lookup/carrier/ask/stats/stale)
2. Claude Code agents (via --json flag for machine-readable output)
3. Direct Python import for programmatic access

Actual DB schema (built by ingestion agent):
- articles: id, slug, title, category, tier, summary, source_path, ...
- sections: id, article_id, heading, content (FTS via sections_fts)
- findings: id, article_id, section_id, finding, carrier, route, amount, ...
  (FTS via findings_fts)
- questions: id, question, article_id, section_id, answer_summary
  (FTS via questions_fts)
- tags: id, name, tag_type (carrier, airport, topic, ...)
- article_tags: article_id, tag_id, relevance
- section_tags: section_id, tag_id, relevance
- finding_tags: finding_id, tag_id
- cross_references: source_article_id, target_article_id, relationship
- sources: id, source_type, title, url, thread_id, credibility
- article_sources: article_id, source_id
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


# Default DB location
DEFAULT_DB_PATH = Path(__file__).parent / "data" / "knowledge.db"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class SearchResult:
    """A single search result with relevance scoring."""

    chunk_id: int  # Actually section.id in this schema
    article_slug: str
    article_title: str
    section: str  # Parent section heading
    heading: str
    body: str
    score: float  # Combined relevance score (0-10)
    match_type: str  # 'fts', 'fact', 'tag', 'carrier', 'question'
    highlights: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize for JSON output."""
        return {
            "chunk_id": self.chunk_id,
            "score": round(self.score, 1),
            "article": self.article_slug,
            "title": self.article_title,
            "section": self.section,
            "heading": self.heading,
            "body": self.body,
            "match_type": self.match_type,
            "highlights": self.highlights,
            "sources": self.source_refs,
        }


@dataclass
class Fact:
    """A structured finding from the KB."""

    category: str  # finding_type in DB
    subject: str  # carrier or route
    predicate: str  # finding_type
    value: str  # the finding text
    confidence: float
    source_quote: Optional[str]  # from section content
    article_slug: str

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "subject": self.subject,
            "predicate": self.predicate,
            "value": self.value,
            "confidence": self.confidence,
            "source_quote": self.source_quote,
            "article": self.article_slug,
        }


@dataclass
class RelatedItem:
    """A cross-reference result."""

    chunk_id: int
    heading: str
    body_preview: str  # First 200 chars
    relation: str  # 'cross_reference', 'shared_tag', 'same_article'
    strength: float  # 0-1

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "heading": self.heading,
            "body_preview": self.body_preview,
            "relation": self.relation,
            "strength": round(self.strength, 2),
        }


# ---------------------------------------------------------------------------
# Fallback synonym dict for query expansion
# ---------------------------------------------------------------------------

_FALLBACK_SYNONYMS: dict[str, str] = {
    "MSC": "married segment",
    "married": "married segment",
    "O&D": "origin destination",
    "OD control": "origin destination",
    "hub control": "origin destination",
    "APD": "air passenger duty",
    "departure tax": "air passenger duty",
    "YQ": "surcharge",
    "YR": "surcharge",
    "fuel surcharge": "surcharge",
    "carrier surcharge": "surcharge",
    "POC": "point of commencement",
    "POS": "point of sale",
    "EF": "expertflyer",
    "D class": "D-class",
    "booking class": "D-class",
    "RTW desk": "booking desk",
    "AA desk": "booking desk",
    "plating": "plating carrier",
    "ticketing": "plating carrier",
    "codeshare": "codeshare",
    "code share": "codeshare",
    "through flight": "through-flight",
    "thru flight": "through-flight",
    "dummy date": "dummy dates",
    "open date": "dummy dates",
    "EMSR": "revenue management",
    "RM": "revenue management",
    "inventory": "revenue management",
    "blocked": "availability block",
    "cannot book": "availability block",
    "agent cant book": "availability block",
    "GDS": "amadeus sabre",
    "Sabre": "amadeus sabre",
    "Amadeus": "amadeus sabre",
    "xONEx": "oneworld online",
    "XONEX": "oneworld online",
}


class KnowledgeBaseError(Exception):
    """Raised when the KB is missing or inaccessible."""


# ---------------------------------------------------------------------------
# KnowledgeBase class
# ---------------------------------------------------------------------------


class KnowledgeBase:
    """Query interface for the RTW travel intelligence database.

    Designed for three consumers:
    1. CLI commands (rtw kb search/lookup/carrier/ask/stats/stale)
    2. Claude Code agents (via Bash tool calling python3 -m rtw kb ...)
    3. Direct Python import for programmatic access
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        if not self.db_path.exists():
            raise KnowledgeBaseError(
                f"Knowledge base not found at {self.db_path}. "
                "Run the KB ingestion pipeline to create it."
            )
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")

    def close(self) -> None:
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ------------------------------------------------------------------
    # Table existence checks (DB may be partially built)
    # ------------------------------------------------------------------

    def _table_exists(self, name: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ?",
            (name,),
        ).fetchone()
        return row is not None

    # ------------------------------------------------------------------
    # 1. Natural language search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        min_score: float = 0.5,
        carrier: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> list[SearchResult]:
        """Full-text search with synonym expansion and domain-aware ranking.

        Strategy:
        1. Expand query using synonym dict
        2. Run FTS5 on sections_fts with BM25 ranking
        3. Run FTS5 on findings_fts for structured matches
        4. Boost results matching carrier/topic filters
        5. Deduplicate and merge scores
        6. Return ranked results with highlighted snippets
        """
        expanded = self._expand_query(query)
        fts_query = self._build_fts_query(expanded, carrier=carrier)

        results: list[SearchResult] = []

        # Phase 1: FTS5 section search (primary)
        if self._table_exists("sections_fts"):
            try:
                rows = self.conn.execute(
                    """
                    SELECT s.id, s.heading, s.content, s.heading_level,
                           a.slug, a.title,
                           rank AS fts_rank
                    FROM sections_fts
                    JOIN sections s ON sections_fts.rowid = s.id
                    JOIN articles a ON s.article_id = a.id
                    WHERE sections_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (fts_query, limit * 3),
                ).fetchall()

                for row in rows:
                    score = self._score_section(row, query, carrier)
                    if score >= min_score:
                        results.append(
                            SearchResult(
                                chunk_id=row["id"],
                                article_slug=row["slug"],
                                article_title=row["title"],
                                section=row["heading"] or "",
                                heading=row["heading"] or "",
                                body=row["content"] or "",
                                score=score,
                                match_type="fts",
                                highlights=self._extract_highlights(
                                    row["content"] or "", query
                                ),
                            )
                        )
            except sqlite3.OperationalError:
                pass

        # Phase 2: Finding search (supplement)
        if self._table_exists("findings_fts"):
            try:
                finding_rows = self.conn.execute(
                    """
                    SELECT f.id, f.finding, f.finding_type, f.carrier,
                           f.route, f.amount, f.currency, f.confidence,
                           f.section_id,
                           a.slug, a.title,
                           rank AS fts_rank
                    FROM findings_fts
                    JOIN findings f ON findings_fts.rowid = f.id
                    JOIN articles a ON f.article_id = a.id
                    WHERE findings_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (fts_query, limit),
                ).fetchall()

                for row in finding_rows:
                    sid = row["section_id"]
                    # Boost existing section result if present
                    if sid and any(r.chunk_id == sid for r in results):
                        for r in results:
                            if r.chunk_id == sid:
                                r.score += 1.5
                                break
                        continue

                    subject = row["carrier"] or row["route"] or ""
                    results.append(
                        SearchResult(
                            chunk_id=sid or 0,
                            article_slug=row["slug"],
                            article_title=row["title"],
                            section="",
                            heading=f"[Finding] {subject} -- {row['finding_type'] or ''}",
                            body=row["finding"] or "",
                            score=self._score_finding(row, query, carrier) + 2.0,
                            match_type="fact",
                        )
                    )
            except sqlite3.OperationalError:
                pass

        # Phase 3: Tag-based fallback if FTS yielded few results
        if len(results) < 3 and carrier:
            tag_results = self._search_by_carrier_tag(
                carrier, limit=limit - len(results)
            )
            results.extend(tag_results)

        # Deduplicate, sort, truncate
        seen: set[int] = set()
        deduped: list[SearchResult] = []
        for r in sorted(results, key=lambda x: x.score, reverse=True):
            if r.chunk_id not in seen:
                seen.add(r.chunk_id)
                deduped.append(r)
        return deduped[:limit]

    # ------------------------------------------------------------------
    # 2. Carrier lookup
    # ------------------------------------------------------------------

    def carrier_lookup(
        self,
        carrier: str,
        *,
        context: Optional[str] = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        """Get all knowledge about a specific carrier.

        Uses findings.carrier for direct matches, article_tags for
        carrier-tagged articles, then falls back to FTS.
        """
        carrier = carrier.upper()
        results: list[SearchResult] = []

        # Primary: findings with this carrier
        if self._table_exists("findings"):
            rows = self.conn.execute(
                """
                SELECT f.id, f.finding, f.finding_type, f.carrier,
                       f.route, f.amount, f.currency, f.confidence,
                       f.section_id,
                       a.slug, a.title,
                       s.heading, s.content
                FROM findings f
                JOIN articles a ON f.article_id = a.id
                LEFT JOIN sections s ON f.section_id = s.id
                WHERE f.carrier = ?
                ORDER BY f.confidence DESC
                LIMIT ?
                """,
                (carrier, limit),
            ).fetchall()

            seen_sections: set[int] = set()
            for row in rows:
                sid = row["section_id"]
                if sid and sid in seen_sections:
                    continue
                if sid:
                    seen_sections.add(sid)

                score = 7.0  # High base: exact carrier match
                if row["confidence"]:
                    score += row["confidence"]

                body = row["content"] or row["finding"] or ""
                results.append(
                    SearchResult(
                        chunk_id=sid or 0,
                        article_slug=row["slug"],
                        article_title=row["title"],
                        section=row["heading"] or "",
                        heading=row["heading"] or f"[Finding] {carrier}",
                        body=body,
                        score=score,
                        match_type="carrier",
                    )
                )

        # Secondary: sections from carrier-tagged articles
        if len(results) < limit and self._table_exists("article_tags"):
            existing_sids = {r.chunk_id for r in results}
            rows = self.conn.execute(
                """
                SELECT s.id, s.heading, s.content,
                       a.slug, a.title
                FROM article_tags at_
                JOIN tags t ON at_.tag_id = t.id
                JOIN articles a ON at_.article_id = a.id
                JOIN sections s ON s.article_id = a.id
                WHERE t.name = ? AND t.tag_type = 'carrier'
                ORDER BY at_.relevance DESC, s.sort_order
                LIMIT ?
                """,
                (carrier, limit * 2),
            ).fetchall()

            for row in rows:
                if row["id"] in existing_sids:
                    continue
                # Only include sections that mention the carrier
                content = (row["content"] or "").upper()
                heading = (row["heading"] or "").upper()
                if carrier not in content and carrier not in heading:
                    continue
                existing_sids.add(row["id"])
                results.append(
                    SearchResult(
                        chunk_id=row["id"],
                        article_slug=row["slug"],
                        article_title=row["title"],
                        section=row["heading"] or "",
                        heading=row["heading"] or "",
                        body=row["content"] or "",
                        score=6.0,
                        match_type="tag",
                        highlights=self._extract_highlights(
                            row["content"] or "", carrier
                        ),
                    )
                )

        # Fallback: FTS for untagged mentions
        if len(results) < 5:
            fts_extra = self.search(
                carrier, limit=limit - len(results), carrier=carrier
            )
            # Avoid duplicates
            existing = {r.chunk_id for r in results}
            for r in fts_extra:
                if r.chunk_id not in existing:
                    results.append(r)

        return sorted(results, key=lambda x: x.score, reverse=True)[:limit]

    # ------------------------------------------------------------------
    # 3. Fact lookup (findings)
    # ------------------------------------------------------------------

    def fact_lookup(
        self,
        subject: str,
        predicate: Optional[str] = None,
    ) -> list[Fact]:
        """Look up structured findings by subject (carrier/route) and optional type.

        Examples:
            fact_lookup("BA", "cost") -> all BA cost findings
            fact_lookup("BA") -> all BA findings
        """
        if not self._table_exists("findings"):
            return []

        # Try carrier match first
        sql = """
            SELECT f.*, a.slug, s.content AS section_content
            FROM findings f
            JOIN articles a ON f.article_id = a.id
            LEFT JOIN sections s ON f.section_id = s.id
            WHERE 1=1
        """

        # Match on carrier or route
        rows = self.conn.execute(
            sql + " AND (f.carrier = ? OR f.carrier = ?)"
            + (" AND f.finding_type LIKE ?" if predicate else "")
            + " ORDER BY f.confidence DESC LIMIT 30",
            [subject.upper(), subject]
            + ([f"%{predicate}%"] if predicate else []),
        ).fetchall()

        if not rows:
            # Try LIKE on carrier, route, or finding text
            like_sql = (
                sql
                + " AND (f.carrier LIKE ? OR f.route LIKE ? OR f.finding LIKE ?)"
            )
            like_params: list = [f"%{subject}%", f"%{subject}%", f"%{subject}%"]
            if predicate:
                like_sql += " AND f.finding_type LIKE ?"
                like_params.append(f"%{predicate}%")
            like_sql += " ORDER BY f.confidence DESC LIMIT 30"
            rows = self.conn.execute(like_sql, like_params).fetchall()

        return [
            Fact(
                category=r["finding_type"] or "",
                subject=r["carrier"] or r["route"] or "",
                predicate=r["finding_type"] or "",
                value=r["finding"] or "",
                confidence=r["confidence"] or 0.0,
                source_quote=(r["section_content"] or "")[:200] or None,
                article_slug=r["slug"],
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # 4. Question answering
    # ------------------------------------------------------------------

    def answer(self, question: str, *, limit: int = 5) -> list[SearchResult]:
        """Answer a natural-language question using questions_fts and sections_fts.

        Strategy:
        1. Search the questions FTS table for matching questions
        2. Also search sections for additional context
        3. Boost tip/strategy/example sections for "how" questions
        """
        results: list[SearchResult] = []

        # Phase 1: Match against questions table
        if self._table_exists("questions_fts"):
            # Strip stop words for better FTS matching
            import re

            stop_words = {
                "what", "how", "why", "when", "where", "which", "who",
                "is", "the", "a", "an", "do", "does", "did", "can", "could",
                "should", "would", "i", "my", "me", "we", "our", "to", "for",
                "about", "of", "in", "on", "at", "from", "with", "this", "that",
            }
            # Strip punctuation from each word before checking stop words
            words = [re.sub(r"[^\w-]", "", w) for w in question.lower().split()]
            terms = [w for w in words if w and w not in stop_words]
            clean_query = " ".join(terms) if terms else question

            expanded = self._expand_query(clean_query)
            fts_query = self._build_fts_query(expanded)

            try:
                rows = self.conn.execute(
                    """
                    SELECT q.id, q.question, q.answer_summary,
                           q.article_id, q.section_id,
                           a.slug, a.title,
                           rank AS fts_rank
                    FROM questions_fts
                    JOIN questions q ON questions_fts.rowid = q.id
                    JOIN articles a ON q.article_id = a.id
                    WHERE questions_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (fts_query, limit * 2),
                ).fetchall()

                for row in rows:
                    fts_rank = abs(row["fts_rank"])
                    score = min(10.0, max(0.0, 10.0 - fts_rank))
                    # Boost questions that closely match
                    if any(t in (row["question"] or "").lower() for t in terms):
                        score += 1.5

                    results.append(
                        SearchResult(
                            chunk_id=row["section_id"] or 0,
                            article_slug=row["slug"],
                            article_title=row["title"],
                            section=row["question"] or "",
                            heading=row["question"] or "",
                            body=row["answer_summary"] or "",
                            score=score,
                            match_type="question",
                            highlights=self._extract_highlights(
                                row["answer_summary"] or "", clean_query
                            ),
                        )
                    )
            except sqlite3.OperationalError:
                pass

        # Phase 2: Also search sections for broader context
        section_results = self.search(question, limit=limit)
        results.extend(section_results)

        # Boost tip/example sections for "how do I" questions
        is_how_question = question.lower().startswith(
            ("how", "what should", "what do")
        )
        if is_how_question:
            for r in results:
                heading_lower = r.heading.lower()
                if "tip" in heading_lower or "strategy" in heading_lower:
                    r.score += 2.0
                if "example" in heading_lower or "war stor" in heading_lower:
                    r.score += 1.5
                if "step" in heading_lower or "method" in heading_lower:
                    r.score += 1.0

        # Deduplicate and sort
        seen: set[int] = set()
        deduped: list[SearchResult] = []
        for r in sorted(results, key=lambda x: x.score, reverse=True):
            if r.chunk_id not in seen:
                seen.add(r.chunk_id)
                deduped.append(r)
        return deduped[:limit]

    # ------------------------------------------------------------------
    # 5. Cross-reference traversal
    # ------------------------------------------------------------------

    def related(
        self,
        chunk_id: int,
        *,
        limit: int = 10,
    ) -> list[RelatedItem]:
        """Find content related to a specific section (chunk_id = section.id).

        Strategy: find sections in cross-referenced articles, sections
        sharing tags, or same article.
        """
        candidates: dict[int, float] = {}
        relations: dict[int, str] = {}

        # Get the article_id for this section
        section_row = self.conn.execute(
            "SELECT article_id FROM sections WHERE id = ?", (chunk_id,)
        ).fetchone()
        if not section_row:
            return []
        my_article_id = section_row["article_id"]

        # 1. Cross-referenced articles (strongest signal)
        if self._table_exists("cross_references"):
            xref_rows = self.conn.execute(
                """
                SELECT target_article_id FROM cross_references
                WHERE source_article_id = ?
                UNION
                SELECT source_article_id FROM cross_references
                WHERE target_article_id = ?
                """,
                (my_article_id, my_article_id),
            ).fetchall()

            for xref in xref_rows:
                target_id = xref["target_article_id"] if "target_article_id" in xref.keys() else xref[0]
                section_rows = self.conn.execute(
                    """
                    SELECT id, heading, content FROM sections
                    WHERE article_id = ? AND id != ?
                    ORDER BY sort_order LIMIT 3
                    """,
                    (target_id, chunk_id),
                ).fetchall()
                for s in section_rows:
                    candidates[s["id"]] = candidates.get(s["id"], 0) + 3.0
                    relations[s["id"]] = "cross_reference"

        # 2. Shared article tags
        if self._table_exists("article_tags"):
            my_tags = self.conn.execute(
                "SELECT tag_id FROM article_tags WHERE article_id = ?",
                (my_article_id,),
            ).fetchall()
            my_tag_ids = [r["tag_id"] for r in my_tags]

            if my_tag_ids:
                placeholders = ",".join("?" * len(my_tag_ids))
                tag_articles = self.conn.execute(
                    f"""
                    SELECT DISTINCT at_.article_id
                    FROM article_tags at_
                    WHERE at_.tag_id IN ({placeholders})
                      AND at_.article_id != ?
                    """,
                    [*my_tag_ids, my_article_id],
                ).fetchall()

                for ta in tag_articles:
                    section_rows = self.conn.execute(
                        """
                        SELECT id, heading, content FROM sections
                        WHERE article_id = ? AND id != ?
                        ORDER BY sort_order LIMIT 2
                        """,
                        (ta["article_id"], chunk_id),
                    ).fetchall()
                    for s in section_rows:
                        candidates[s["id"]] = candidates.get(s["id"], 0) + 1.5
                        relations.setdefault(s["id"], "shared_tag")

        # 3. Same article sections
        same_article = self.conn.execute(
            "SELECT id, heading, content FROM sections WHERE article_id = ? AND id != ? ORDER BY sort_order",
            (my_article_id, chunk_id),
        ).fetchall()
        for s in same_article:
            candidates[s["id"]] = candidates.get(s["id"], 0) + 0.5
            relations.setdefault(s["id"], "same_article")

        # Fetch top candidates
        top_ids = sorted(candidates, key=candidates.get, reverse=True)[:limit]
        if not top_ids:
            return []

        placeholders = ",".join("?" * len(top_ids))
        rows = self.conn.execute(
            f"SELECT id, heading, content FROM sections WHERE id IN ({placeholders})",
            top_ids,
        ).fetchall()
        chunk_map = {r["id"]: r for r in rows}

        max_score = max(candidates.values()) if candidates else 1
        return [
            RelatedItem(
                chunk_id=cid,
                heading=chunk_map[cid]["heading"] or "",
                body_preview=(chunk_map[cid]["content"] or "")[:200],
                relation=relations.get(cid, "unknown"),
                strength=candidates[cid] / max_score,
            )
            for cid in top_ids
            if cid in chunk_map
        ]

    # ------------------------------------------------------------------
    # 6. Source tracking
    # ------------------------------------------------------------------

    def get_sources(
        self,
        *,
        source_type: Optional[str] = None,
        article_slug: Optional[str] = None,
    ) -> list[dict]:
        """List all sources, optionally filtered by type or article."""
        if not self._table_exists("sources"):
            return []

        sql = """
            SELECT DISTINCT s.*,
                   a.slug AS article_slug, a.title AS article_title
            FROM sources s
            LEFT JOIN article_sources as_ ON s.id = as_.source_id
            LEFT JOIN articles a ON as_.article_id = a.id
            WHERE 1=1
        """
        params: list = []

        if source_type:
            sql += " AND s.source_type = ?"
            params.append(source_type)
        if article_slug:
            sql += " AND a.slug = ?"
            params.append(article_slug)

        rows = self.conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # 7. Freshness check
    # ------------------------------------------------------------------

    def stale_articles(
        self,
        max_age_days: int = 90,
    ) -> list[dict]:
        """Find articles older than a threshold.

        Uses created_at since the actual schema doesn't have source_date.
        """
        cutoff = (datetime.now() - timedelta(days=max_age_days)).strftime(
            "%Y-%m-%d"
        )
        rows = self.conn.execute(
            """
            SELECT slug, title, source_path, created_at,
                   julianday('now') - julianday(created_at) AS age_days
            FROM articles
            WHERE created_at < ? OR created_at IS NULL
            ORDER BY created_at ASC
            """,
            (cutoff,),
        ).fetchall()
        return [dict(r) for r in rows]

    def freshness_report(self) -> dict:
        """Overall KB freshness summary."""
        row = self.conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN julianday('now') - julianday(created_at) <= 90
                         THEN 1 ELSE 0 END) AS fresh,
                SUM(CASE WHEN julianday('now') - julianday(created_at) > 90
                         THEN 1 ELSE 0 END) AS stale,
                MIN(created_at) AS oldest,
                MAX(created_at) AS newest
            FROM articles
            """
        ).fetchone()
        return dict(row)

    # ------------------------------------------------------------------
    # 8. Contextual briefing
    # ------------------------------------------------------------------

    def context_brief(
        self,
        *,
        origin: Optional[str] = None,
        ticket_type: Optional[str] = None,
        carriers: Optional[list[str]] = None,
        cities: Optional[list[str]] = None,
    ) -> list[SearchResult]:
        """Generate a contextual briefing for a specific booking scenario.

        Assembles relevant knowledge from multiple dimensions:
        - Origin city advice (Oslo-specific tips, APD avoidance)
        - Carrier warnings (CX married segments, O&D control)
        - City/hub advice (HKG hub control)
        - Ticket type implications
        - General booking strategy
        """
        all_results: list[SearchResult] = []

        # Origin-specific knowledge
        if origin:
            origin_results = self.search(origin, limit=5)
            for r in origin_results:
                r.score += 1.0
            all_results.extend(origin_results)

            # Scandinavian origins -> APD and currency
            if origin.upper() in ("OSL", "ARN", "CPH"):
                all_results.extend(self.search("APD avoidance", limit=3))
                all_results.extend(self.search("currency timing NOK", limit=2))

        # Carrier-specific warnings
        for carrier_code in carriers or []:
            carrier_results = self.carrier_lookup(carrier_code, limit=5)
            for r in carrier_results:
                r.score += 2.0
            all_results.extend(carrier_results)

        # Hub-specific knowledge
        hub_airports = {"HKG", "DOH", "SIN", "NRT", "DFW", "LAX", "LHR", "HEL"}
        for city in cities or []:
            if city.upper() in hub_airports:
                hub_results = self.search(
                    f"{city} hub O&D control married segment", limit=5
                )
                for r in hub_results:
                    r.score += 1.5
                all_results.extend(hub_results)

        # Ticket type implications
        if ticket_type:
            continent_count = ticket_type[-1] if ticket_type[-1].isdigit() else None
            if continent_count and int(continent_count) == 3:
                all_results.extend(
                    self.search("3 continent routing constraint backtrack", limit=3)
                )

        # General booking strategy
        all_results.extend(
            self.search("booking strategy segment by segment", limit=3)
        )

        # Deduplicate and re-rank
        seen: set[int] = set()
        deduped: list[SearchResult] = []
        for r in sorted(all_results, key=lambda x: x.score, reverse=True):
            if r.chunk_id not in seen:
                seen.add(r.chunk_id)
                deduped.append(r)

        return deduped[:15]

    # ------------------------------------------------------------------
    # 9. Topic search
    # ------------------------------------------------------------------

    def topic_search(
        self,
        topic: str,
        *,
        limit: int = 15,
    ) -> list[SearchResult]:
        """Retrieve everything on a topic.

        Uses tags table to find topic-tagged articles, then retrieves
        sections from those articles. Falls back to FTS.
        """
        if self._table_exists("tags") and self._table_exists("article_tags"):
            # Try to find a matching tag
            tag_row = self.conn.execute(
                """
                SELECT id, name FROM tags
                WHERE (name = ? COLLATE NOCASE
                       OR name LIKE ? COLLATE NOCASE)
                  AND tag_type = 'topic'
                LIMIT 1
                """,
                (topic, f"%{topic}%"),
            ).fetchone()

            if tag_row:
                rows = self.conn.execute(
                    """
                    SELECT s.id, s.heading, s.content,
                           a.slug, a.title,
                           at_.relevance
                    FROM article_tags at_
                    JOIN articles a ON at_.article_id = a.id
                    JOIN sections s ON s.article_id = a.id
                    WHERE at_.tag_id = ?
                    ORDER BY at_.relevance DESC, s.sort_order
                    LIMIT ?
                    """,
                    (tag_row["id"], limit),
                ).fetchall()

                if rows:
                    return [
                        SearchResult(
                            chunk_id=r["id"],
                            article_slug=r["slug"],
                            article_title=r["title"],
                            section=r["heading"] or "",
                            heading=r["heading"] or "",
                            body=r["content"] or "",
                            score=(r["relevance"] or 0.5) * 10,
                            match_type="tag",
                        )
                        for r in rows
                    ]

        # Fallback to FTS search
        return self.search(topic, limit=limit)

    # ------------------------------------------------------------------
    # 10. Listing and stats
    # ------------------------------------------------------------------

    def list_articles(self) -> list[dict]:
        """List all articles in the KB."""
        rows = self.conn.execute(
            """
            SELECT slug, title, category, tier, created_at, word_count,
                   (SELECT COUNT(*) FROM sections WHERE article_id = a.id) AS section_count,
                   (SELECT COUNT(*) FROM findings WHERE article_id = a.id) AS finding_count
            FROM articles a
            ORDER BY created_at DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]

    def list_topics(self) -> list[dict]:
        """List all topic tags with article counts."""
        if not self._table_exists("tags"):
            return []
        rows = self.conn.execute(
            """
            SELECT t.name, t.name AS display, t.tag_type AS description,
                   COUNT(at_.article_id) AS chunk_count
            FROM tags t
            LEFT JOIN article_tags at_ ON t.id = at_.tag_id
            WHERE t.tag_type = 'topic'
            GROUP BY t.id
            ORDER BY chunk_count DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]

    def list_carriers(self) -> list[dict]:
        """List all carriers mentioned, with finding counts by type."""
        if not self._table_exists("findings"):
            return []

        rows = self.conn.execute(
            """
            SELECT carrier,
                   COUNT(*) AS total_mentions,
                   SUM(CASE WHEN finding_type = 'cost' THEN 1 ELSE 0 END) AS yq_mentions,
                   SUM(CASE WHEN finding_type = 'risk' THEN 1 ELSE 0 END) AS msc_mentions,
                   SUM(CASE WHEN finding_type = 'availability' THEN 1 ELSE 0 END) AS avail_mentions,
                   SUM(CASE WHEN finding_type = 'warning' THEN 1 ELSE 0 END) AS warnings
            FROM findings
            WHERE carrier IS NOT NULL AND carrier != ''
            GROUP BY carrier
            ORDER BY total_mentions DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> dict:
        """KB-wide statistics."""
        result: dict = {}
        table_map = {
            "articles": "articles",
            "sections": "sections",
            "findings": "findings",
            "questions": "questions",
            "sources": "sources",
            "tags": "tags",
        }
        for key, table in table_map.items():
            if self._table_exists(table):
                result[key] = self.conn.execute(
                    f"SELECT COUNT(*) FROM {table}"  # noqa: S608
                ).fetchone()[0]
            else:
                result[key] = 0

        # Carrier count from findings
        if self._table_exists("findings"):
            result["carriers_tracked"] = self.conn.execute(
                "SELECT COUNT(DISTINCT carrier) FROM findings WHERE carrier IS NOT NULL AND carrier != ''"
            ).fetchone()[0]
        else:
            result["carriers_tracked"] = 0

        # Freshness info
        if result["articles"] > 0:
            freshness = self.freshness_report()
            result["fresh_articles"] = freshness.get("fresh", 0)
            result["stale_articles"] = freshness.get("stale", 0)
            result["oldest_article"] = freshness.get("oldest")
            result["newest_article"] = freshness.get("newest")

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _expand_query(self, query: str) -> list[str]:
        """Expand query terms using the fallback synonym dict."""
        words = query.split()
        expanded = list(words)

        # Try multi-word phrases first (up to 3 words), then single words
        for n in (3, 2, 1):
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i : i + n])
                # Try synonyms table if it exists
                if self._table_exists("synonyms"):
                    rows = self.conn.execute(
                        "SELECT canonical FROM synonyms WHERE term = ? COLLATE NOCASE",
                        (phrase,),
                    ).fetchall()
                    for r in rows:
                        if r["canonical"] not in expanded:
                            expanded.append(r["canonical"])
                else:
                    # Use fallback dict (case-insensitive)
                    for key, val in _FALLBACK_SYNONYMS.items():
                        if key.lower() == phrase.lower() and val not in expanded:
                            expanded.append(val)

        return expanded

    def _build_fts_query(
        self,
        terms: list[str],
        *,
        carrier: Optional[str] = None,
    ) -> str:
        """Build an FTS5 query string from expanded terms.

        Uses OR between terms for broad recall; BM25 handles ranking.
        If carrier is specified, it becomes mandatory (implicit AND).
        """
        if carrier:
            non_carrier = [t for t in terms if t.upper() != carrier.upper()]
            if non_carrier:
                inner = " OR ".join(
                    f'"{t}"' if " " in t else t for t in non_carrier
                )
                return f"({inner}) {carrier}"
            return carrier

        parts = []
        seen: set[str] = set()
        for t in terms:
            key = t.lower()
            if key not in seen:
                seen.add(key)
                parts.append(f'"{t}"' if " " in t else t)
        return " OR ".join(parts) if parts else (terms[0] if terms else "")

    def _score_section(
        self,
        row: sqlite3.Row,
        query: str,
        carrier: Optional[str],
    ) -> float:
        """Score a section result on a 0-10 scale."""
        fts_rank = abs(row["fts_rank"])
        base_score = min(10.0, max(0.0, 10.0 - fts_rank))

        # Boost for heading match
        heading = (row["heading"] or "").lower()
        query_lower = query.lower()
        if any(term in heading for term in query_lower.split()):
            base_score += 1.5

        # Boost for carrier mentions in findings
        if carrier and self._table_exists("findings"):
            cm_count = self.conn.execute(
                "SELECT COUNT(*) FROM findings WHERE section_id = ? AND carrier = ?",
                (row["id"], carrier.upper()),
            ).fetchone()[0]
            if cm_count:
                base_score += 2.0

        return min(10.0, base_score)

    def _score_finding(
        self, row: sqlite3.Row, query: str, carrier: Optional[str]
    ) -> float:
        """Score a finding result."""
        base = 5.0
        if carrier and carrier.upper() == (row["carrier"] or "").upper():
            base += 3.0
        if row["confidence"]:
            base *= row["confidence"]
        return min(10.0, base)

    def _extract_highlights(
        self, body: str, query: str, max_highlights: int = 3
    ) -> list[str]:
        """Extract text snippets around matching terms."""
        highlights: list[str] = []
        body_lower = body.lower()
        terms = query.lower().split()

        for term in terms:
            idx = body_lower.find(term)
            if idx >= 0:
                start = max(0, idx - 60)
                end = min(len(body), idx + len(term) + 60)
                snippet = body[start:end].strip()
                if start > 0:
                    snippet = "..." + snippet
                if end < len(body):
                    snippet = snippet + "..."
                highlights.append(snippet)
                if len(highlights) >= max_highlights:
                    break

        return highlights

    def _search_by_carrier_tag(
        self, carrier: str, limit: int = 5
    ) -> list[SearchResult]:
        """Search sections via carrier tag for fallback results."""
        if not self._table_exists("article_tags"):
            return []

        rows = self.conn.execute(
            """
            SELECT s.id, s.heading, s.content,
                   a.slug, a.title
            FROM article_tags at_
            JOIN tags t ON at_.tag_id = t.id
            JOIN articles a ON at_.article_id = a.id
            JOIN sections s ON s.article_id = a.id
            WHERE t.name = ? COLLATE NOCASE AND t.tag_type = 'carrier'
            ORDER BY at_.relevance DESC, s.sort_order
            LIMIT ?
            """,
            (carrier.upper(), limit),
        ).fetchall()

        return [
            SearchResult(
                chunk_id=r["id"],
                article_slug=r["slug"],
                article_title=r["title"],
                section=r["heading"] or "",
                heading=r["heading"] or "",
                body=r["content"] or "",
                score=5.0,
                match_type="tag",
            )
            for r in rows
        ]
