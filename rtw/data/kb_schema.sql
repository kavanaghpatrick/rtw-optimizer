-- =============================================================================
-- RTW Knowledge Base — SQLite Schema
-- =============================================================================
-- Stores RTW travel booking intelligence, travel business research, and
-- extracted facts from FlyerTalk threads, IATA rules, and real booking data.
--
-- Design principles:
--   1. Articles are the top-level unit (one per markdown file)
--   2. Sections break articles into searchable chunks (~heading-level)
--   3. Findings are atomic facts extracted from text (YQ figures, rules, etc.)
--   4. FTS5 indexes sections, findings, and questions for natural-language search
--   5. Staleness tracking via created_at / updated_at / confidence / last_verified
--   6. Questions map natural-language queries to the content that answers them
-- =============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- 1. ARTICLES — top-level documents (one per markdown KB file)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS articles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slug            TEXT    NOT NULL UNIQUE,
    title           TEXT    NOT NULL,
    category        TEXT    NOT NULL,
    tier            TEXT    NOT NULL DEFAULT 'reference',
    summary         TEXT,
    source_path     TEXT,
    content_hash    TEXT,
    word_count      INTEGER,
    confidence      REAL    DEFAULT 0.8,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    last_verified   TEXT,
    is_archived     INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
CREATE INDEX IF NOT EXISTS idx_articles_tier ON articles(tier);
CREATE INDEX IF NOT EXISTS idx_articles_slug ON articles(slug);

-- ---------------------------------------------------------------------------
-- 2. SECTIONS — heading-level chunks within articles
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sections (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id      INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    heading         TEXT    NOT NULL,
    heading_level   INTEGER NOT NULL DEFAULT 2,
    content         TEXT    NOT NULL,
    parent_id       INTEGER REFERENCES sections(id),
    sort_order      INTEGER NOT NULL DEFAULT 0,
    word_count      INTEGER,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sections_article ON sections(article_id);
CREATE INDEX IF NOT EXISTS idx_sections_parent ON sections(parent_id);

-- ---------------------------------------------------------------------------
-- 3. TAGS — flexible labeling with typed categories
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tags (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    tag_type        TEXT    NOT NULL,
    UNIQUE(name, tag_type)
);

CREATE INDEX IF NOT EXISTS idx_tags_type ON tags(tag_type);
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);

-- Junction: articles <-> tags
CREATE TABLE IF NOT EXISTS article_tags (
    article_id      INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    tag_id          INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    relevance       REAL    DEFAULT 1.0,
    PRIMARY KEY (article_id, tag_id)
);

-- Junction: sections <-> tags
CREATE TABLE IF NOT EXISTS section_tags (
    section_id      INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    tag_id          INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    relevance       REAL    DEFAULT 1.0,
    PRIMARY KEY (section_id, tag_id)
);

-- Junction: findings <-> tags
CREATE TABLE IF NOT EXISTS finding_tags (
    finding_id      INTEGER NOT NULL REFERENCES findings(id) ON DELETE CASCADE,
    tag_id          INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (finding_id, tag_id)
);

-- ---------------------------------------------------------------------------
-- 4. QUESTIONS — natural-language questions each article/section answers
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS questions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    question        TEXT    NOT NULL,
    article_id      INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    section_id      INTEGER REFERENCES sections(id) ON DELETE SET NULL,
    answer_summary  TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_questions_article ON questions(article_id);
CREATE INDEX IF NOT EXISTS idx_questions_section ON questions(section_id);

-- ---------------------------------------------------------------------------
-- 5. CROSS-REFERENCES — directed links between articles
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cross_references (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    source_article_id   INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    target_article_id   INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    relationship        TEXT NOT NULL DEFAULT 'related',
    description         TEXT,
    UNIQUE(source_article_id, target_article_id, relationship)
);

CREATE INDEX IF NOT EXISTS idx_xref_source ON cross_references(source_article_id);
CREATE INDEX IF NOT EXISTS idx_xref_target ON cross_references(target_article_id);

-- ---------------------------------------------------------------------------
-- 6. FINDINGS — atomic facts / data points extracted from articles
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS findings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id      INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    section_id      INTEGER REFERENCES sections(id) ON DELETE SET NULL,
    finding         TEXT    NOT NULL,
    finding_type    TEXT    NOT NULL,
    carrier         TEXT,
    route           TEXT,
    amount          REAL,
    currency        TEXT,
    unit            TEXT,
    confidence      REAL    DEFAULT 0.8,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_findings_article ON findings(article_id);
CREATE INDEX IF NOT EXISTS idx_findings_type ON findings(finding_type);
CREATE INDEX IF NOT EXISTS idx_findings_carrier ON findings(carrier);
CREATE INDEX IF NOT EXISTS idx_findings_route ON findings(route);

-- ---------------------------------------------------------------------------
-- 7. SOURCES — external references (FlyerTalk threads, docs, URLs)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sources (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type     TEXT    NOT NULL,
    title           TEXT,
    url             TEXT,
    thread_id       TEXT,
    credibility     REAL    DEFAULT 0.7
);

CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(source_type);
CREATE INDEX IF NOT EXISTS idx_sources_thread ON sources(thread_id);

-- Junction: articles <-> sources
CREATE TABLE IF NOT EXISTS article_sources (
    article_id      INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    source_id       INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, source_id)
);

-- ---------------------------------------------------------------------------
-- 8. FULL-TEXT SEARCH — FTS5 virtual tables (porter unicode61 tokenizer)
-- ---------------------------------------------------------------------------

-- FTS on section content (the main search surface)
CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5(
    heading,
    content,
    content=sections,
    content_rowid=id,
    tokenize='porter unicode61'
);

-- Triggers to keep FTS in sync with sections table
CREATE TRIGGER IF NOT EXISTS sections_ai AFTER INSERT ON sections BEGIN
    INSERT INTO sections_fts(rowid, heading, content)
    VALUES (new.id, new.heading, new.content);
END;

CREATE TRIGGER IF NOT EXISTS sections_ad AFTER DELETE ON sections BEGIN
    INSERT INTO sections_fts(sections_fts, rowid, heading, content)
    VALUES ('delete', old.id, old.heading, old.content);
END;

CREATE TRIGGER IF NOT EXISTS sections_au AFTER UPDATE ON sections BEGIN
    INSERT INTO sections_fts(sections_fts, rowid, heading, content)
    VALUES ('delete', old.id, old.heading, old.content);
    INSERT INTO sections_fts(rowid, heading, content)
    VALUES (new.id, new.heading, new.content);
END;

-- FTS on findings (for searching extracted facts)
CREATE VIRTUAL TABLE IF NOT EXISTS findings_fts USING fts5(
    finding,
    content=findings,
    content_rowid=id,
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS findings_ai AFTER INSERT ON findings BEGIN
    INSERT INTO findings_fts(rowid, finding)
    VALUES (new.id, new.finding);
END;

CREATE TRIGGER IF NOT EXISTS findings_ad AFTER DELETE ON findings BEGIN
    INSERT INTO findings_fts(findings_fts, rowid, finding)
    VALUES ('delete', old.id, old.finding);
END;

CREATE TRIGGER IF NOT EXISTS findings_au AFTER UPDATE ON findings BEGIN
    INSERT INTO findings_fts(findings_fts, rowid, finding)
    VALUES ('delete', old.id, old.finding);
    INSERT INTO findings_fts(rowid, finding)
    VALUES (new.id, new.finding);
END;

-- FTS on questions (for matching user queries to known questions)
CREATE VIRTUAL TABLE IF NOT EXISTS questions_fts USING fts5(
    question,
    answer_summary,
    content=questions,
    content_rowid=id,
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS questions_ai AFTER INSERT ON questions BEGIN
    INSERT INTO questions_fts(rowid, question, answer_summary)
    VALUES (new.id, new.question, new.answer_summary);
END;

CREATE TRIGGER IF NOT EXISTS questions_ad AFTER DELETE ON questions BEGIN
    INSERT INTO questions_fts(questions_fts, rowid, question, answer_summary)
    VALUES ('delete', old.id, old.question, old.answer_summary);
END;

CREATE TRIGGER IF NOT EXISTS questions_au AFTER UPDATE ON questions BEGIN
    INSERT INTO questions_fts(questions_fts, rowid, question, answer_summary)
    VALUES ('delete', old.id, old.question, old.answer_summary);
    INSERT INTO questions_fts(rowid, question, answer_summary)
    VALUES (new.id, new.question, new.answer_summary);
END;
