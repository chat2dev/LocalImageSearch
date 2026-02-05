"""
Index building and search module

Builds two types of indexes based on the tags and description fields of the image_tags table:

1. Inverted index (tag_index table)
   - Splits comma-separated tags into individual tags
   - Mapping: tag -> [image_id, ...]
   - Supports exact tag matching, multi-tag intersection/union queries
   - Use case: user selects a specific tag to filter images

2. FTS5 full-text search index (image_fts virtual table)
   - Builds a full-text index on the tags and description text
   - Commas in tags are replaced with spaces so each tag becomes an independent search token
   - Supports keyword search and multi-word matching
   - Use case: user enters free text to search for related images

Usage (CLI):
    python src/index_builder.py build                        # Build indexes
    python src/index_builder.py search "AI"                  # Exact tag search
    python src/index_builder.py search "AI" --mode fts       # Full-text search
    python src/index_builder.py search "AI,code" --mode tags --match any  # Multi-tag union
    python src/index_builder.py search "AI,code" --mode tags --match all  # Multi-tag intersection
    python src/index_builder.py stats                        # View index statistics
"""

import argparse
import sqlite3
import time
from pathlib import Path
from typing import Dict, List


# ─── Utility functions ────────────────────────────────────────


def _parse_tags(tags_str: str) -> List[str]:
    """Split and clean a comma-separated tags string, filtering out empty values"""
    if not tags_str:
        return []
    return [t.strip() for t in tags_str.split(",") if t.strip()]


# ─── Index builder ────────────────────────────────────────────


class IndexBuilder:
    """Builds the tag_index inverted index table and the image_fts FTS5 full-text search table.

    Each call to build() performs a full rebuild of both indexes (DROP + INSERT),
    suitable for refreshing after batch processing or manual repair scenarios.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    # ─── Public interface ─────────────────────────────────────

    def build(self) -> Dict[str, int]:
        """Build all indexes and return statistics."""
        tag_rows = self._build_tag_index()
        fts_rows = self._build_fts_index()
        self.conn.commit()
        return {
            "tag_index_rows": tag_rows,
            "fts_index_rows": fts_rows,
        }

    def close(self):
        if self.conn:
            self.conn.close()

    # ─── Inverted index (tag_index) ───────────────────────────

    def _build_tag_index(self) -> int:
        """Create the tag_index table and populate it fully.

        Schema:
            tag             - Individual tag text (value after comma split)
            image_id        - Corresponds to image_tags.id (foreign key)
            image_unique_id - Corresponds to image_tags.image_unique_id

        Indexes:
            idx_ti_tag      - Fast lookup by tag (primary query path)
            idx_ti_image_id - Reverse lookup of all tags for an image

        Returns: Number of rows inserted
        """
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tag_index (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                tag             TEXT    NOT NULL,
                image_id        INTEGER NOT NULL,
                image_unique_id TEXT    NOT NULL,
                UNIQUE(tag, image_id)
            )
        """)
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ti_tag      ON tag_index(tag)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ti_image_id ON tag_index(image_id)"
        )

        # Full rebuild
        self.cursor.execute("DELETE FROM tag_index")

        self.cursor.execute("""
            SELECT id, image_unique_id, tags
            FROM image_tags
            WHERE status = 'success'
        """)
        rows = self.cursor.fetchall()

        insert_count = 0
        for row in rows:
            for tag in _parse_tags(row["tags"]):
                self.cursor.execute(
                    """INSERT OR IGNORE INTO tag_index
                       (tag, image_id, image_unique_id)
                       VALUES (?, ?, ?)""",
                    (tag, row["id"], row["image_unique_id"]),
                )
                insert_count += 1

        return insert_count

    # ─── FTS5 full-text search index (image_fts) ─────────────

    def _build_fts_index(self) -> int:
        """Create the image_fts FTS5 virtual table and populate it fully.

        - rowid is aligned with image_tags.id; JOIN uses rowid = id directly
        - tags field: commas replaced with spaces so each tag becomes an independent token
        - description field: NULL converted to empty string
        - tokenize = unicode61: default tokenizer, CJK characters treated as contiguous tokens

        Returns: Number of rows inserted
        """
        self.cursor.execute("DROP TABLE IF EXISTS image_fts")
        self.cursor.execute("""
            CREATE VIRTUAL TABLE image_fts USING fts5(
                tags,
                description,
                tokenize = 'unicode61'
            )
        """)
        self.cursor.execute("""
            INSERT INTO image_fts(rowid, tags, description)
            SELECT
                id,
                REPLACE(tags, ',', ' '),
                COALESCE(description, '')
            FROM image_tags
            WHERE status = 'success'
        """)
        self.cursor.execute("SELECT COUNT(*) FROM image_fts")
        return self.cursor.fetchone()[0]


# ─── Index searcher ───────────────────────────────────────────


class IndexSearcher:
    """Provides multiple search interfaces based on tag_index and image_fts."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    # ─── Single tag exact match ───────────────────────────────

    def search_by_tag(self, tag: str) -> List[Dict]:
        """Exact match on a single tag; returns all image records containing that tag."""
        self.cursor.execute("""
            SELECT it.id, it.image_path, it.tags, it.description
            FROM tag_index ti
            JOIN image_tags it ON ti.image_id = it.id
            WHERE ti.tag = ?
            ORDER BY it.id
        """, (tag.strip(),))
        return [dict(row) for row in self.cursor.fetchall()]

    # ─── Multi-tag match ──────────────────────────────────────

    def search_by_tags(self, tags: List[str], mode: str = "any") -> List[Dict]:
        """Multi-tag query.

        Args:
            tags: List of tags
            mode: 'any' = match any single tag (union)
                  'all' = must contain all tags simultaneously (intersection)
        """
        if not tags:
            return []

        clean = [t.strip() for t in tags if t.strip()]
        if not clean:
            return []

        ph = ",".join(["?"] * len(clean))

        if mode == "any":
            sql = f"""
                SELECT DISTINCT it.id, it.image_path, it.tags, it.description
                FROM tag_index ti
                JOIN image_tags it ON ti.image_id = it.id
                WHERE ti.tag IN ({ph})
                ORDER BY it.id
            """
            params = clean
        else:  # all — intersection: each image must contain all queried tags
            sql = f"""
                SELECT it.id, it.image_path, it.tags, it.description
                FROM tag_index ti
                JOIN image_tags it ON ti.image_id = it.id
                WHERE ti.tag IN ({ph})
                GROUP BY it.id
                HAVING COUNT(DISTINCT ti.tag) = ?
                ORDER BY it.id
            """
            params = clean + [len(clean)]

        self.cursor.execute(sql, params)
        return [dict(row) for row in self.cursor.fetchall()]

    # ─── FTS5 full-text search ────────────────────────────────

    def search_fulltext(self, query: str) -> List[Dict]:
        """FTS5 full-text search.

        Query syntax (FTS5 standard):
            Single word:   artificial_intelligence
            Multi-word AND: artificial_intelligence agent
            Phrase:        "city street"
            OR:            artificial_intelligence OR machine_learning
            NOT:           intelligence NOT machine

        Results are sorted by relevance (rank).
        """
        if not query or not query.strip():
            return []
        try:
            self.cursor.execute("""
                SELECT it.id, it.image_path, it.tags, it.description
                FROM image_fts fts
                JOIN image_tags it ON fts.rowid = it.id
                WHERE image_fts MATCH ?
                ORDER BY rank
            """, (query.strip(),))
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"FTS search error: {e}")
            return []

    # ─── Smart keyword search (FTS + LIKE fallback) ──────────

    def search_keyword(self, keyword: str) -> List[Dict]:
        """Smart keyword search: first attempts FTS5 exact token matching;
        if no results, falls back to a LIKE substring search on tag_index.

        Suitable for scenarios where the user enters any keyword (including substrings of tags).
        For example, entering "intelli" can match tags like "artificial_intelligence", "intelligent_agent", etc.
        """
        # Step 1: FTS5 match (most effective when description has content)
        results = self.search_fulltext(keyword)
        if results:
            return results

        # Step 2: fallback — substring search via tag_index LIKE
        keyword = keyword.strip()
        if not keyword:
            return []
        self.cursor.execute("""
            SELECT DISTINCT it.id, it.image_path, it.tags, it.description
            FROM tag_index ti
            JOIN image_tags it ON ti.image_id = it.id
            WHERE ti.tag LIKE ?
            ORDER BY it.id
        """, (f"%{keyword}%",))
        return [dict(row) for row in self.cursor.fetchall()]

    # ─── Statistics and auxiliary queries ─────────────────────

    def get_tag_stats(self) -> List[Dict]:
        """Get all unique tags and their occurrence counts, sorted by frequency descending."""
        self.cursor.execute("""
            SELECT tag, COUNT(*) as count
            FROM tag_index
            GROUP BY tag
            ORDER BY count DESC
        """)
        return [{"tag": row[0], "count": row[1]} for row in self.cursor.fetchall()]

    def get_similar_tags(self, keyword: str, limit: int = 10) -> List[Dict]:
        """Fuzzy match tags (LIKE %keyword%), suitable for keyword search within tags."""
        self.cursor.execute("""
            SELECT tag, COUNT(*) as count
            FROM tag_index
            WHERE tag LIKE ?
            GROUP BY tag
            ORDER BY count DESC
            LIMIT ?
        """, (f"%{keyword.strip()}%", limit))
        return [{"tag": row[0], "count": row[1]} for row in self.cursor.fetchall()]

    def close(self):
        if self.conn:
            self.conn.close()


# ─── CLI entry point ──────────────────────────────────────────


def _cli_build(args):
    """Build index subcommand."""
    print(f"Building indexes (db: {args.db}) ...")
    t0 = time.time()
    builder = IndexBuilder(args.db)
    stats = builder.build()
    builder.close()
    elapsed = time.time() - t0
    print(f"Build complete ({elapsed:.2f}s)")
    print(f"  Inverted index (tag_index): {stats['tag_index_rows']} rows")
    print(f"  Full-text index (image_fts): {stats['fts_index_rows']} rows")


def _cli_search(args):
    """Search subcommand."""
    searcher = IndexSearcher(args.db)

    if args.mode == "tag":
        results = searcher.search_by_tag(args.query)
    elif args.mode == "tags":
        tag_list = [t.strip() for t in args.query.split(",")]
        results = searcher.search_by_tags(tag_list, mode=args.match)
    else:  # fts — smart search: FTS first, LIKE fallback when no results
        results = searcher.search_keyword(args.query)

    searcher.close()

    print(f"Search '{args.query}' (mode: {args.mode}), found {len(results)} result(s):\n")
    for r in results:
        fname = Path(r["image_path"]).name
        print(f"  [{r['id']}] {fname}")
        print(f"       tags: {r['tags']}")
        if r.get("description"):
            print(f"       desc: {r['description']}")
        print()


def _cli_stats(args):
    """Statistics subcommand."""
    searcher = IndexSearcher(args.db)
    tags = searcher.get_tag_stats()
    print(f"Index statistics: {len(tags)} unique tag(s)\n")
    print(f"  {'tag':<20} {'count':>5}")
    print(f"  {'─' * 20} {'─' * 5}")
    for item in tags[:30]:
        print(f"  {item['tag']:<20} {item['count']:>5}")
    searcher.close()


def main():
    """CLI main entry point."""
    parser = argparse.ArgumentParser(description="Image tag index building and search")
    sub = parser.add_subparsers(dest="command", help="Subcommands")

    # ── build ──
    build_p = sub.add_parser("build", help="Build/rebuild indexes")
    build_p.add_argument("--db", default="./data/image_tags.db", help="DB Path")

    # ── search ──
    search_p = sub.add_parser("search", help="Search images")
    search_p.add_argument("query", help="Search term (use commas to separate multiple tags)")
    search_p.add_argument(
        "--mode",
        choices=["tag", "tags", "fts"],
        default="tag",
        help="tag=single tag exact match | tags=multi-tag (comma-separated) | fts=full-text search",
    )
    search_p.add_argument(
        "--match",
        choices=["any", "all"],
        default="any",
        help="Multi-tag match mode: any=union, all=intersection (only effective with --mode tags)",
    )
    search_p.add_argument("--db", default="./data/image_tags.db", help="DB Path")

    # ── stats ──
    stats_p = sub.add_parser("stats", help="Show index statistics")
    stats_p.add_argument("--db", default="./data/image_tags.db", help="DB Path")

    args = parser.parse_args()

    dispatch = {
        "build": _cli_build,
        "search": _cli_search,
        "stats": _cli_stats,
    }

    if args.command in dispatch:
        dispatch[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
