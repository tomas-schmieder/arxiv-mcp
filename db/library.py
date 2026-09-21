"""Query the local citation SQLite library.

Placeholders follow the sqlite3 docs:
https://docs.python.org/3/library/sqlite3.html#how-to-use-placeholders-to-bind-values-in-sql-queries

LIKE wildcard escaping follows the SQLite expression language:
https://www.sqlite.org/lang_expr.html#like

Query parameterization as a defense follows the OWASP SQL Injection
Prevention Cheat Sheet:
https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
"""

from __future__ import annotations

import sqlite3

from db.seed import DB_PATH

_SELECT_PAPERS = "SELECT id, title, authors, year, doi, notes FROM papers"


def like_contains_pattern(keyword: str) -> str:
    """Build a LIKE pattern that matches keyword as a literal substring."""
    escaped = (
        keyword.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    return f"%{escaped}%"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_matching_papers(
    keyword: str, conn: sqlite3.Connection | None = None
) -> list[sqlite3.Row]:
    """Return papers whose title or authors contain keyword (case-insensitive)."""
    pattern = like_contains_pattern(keyword)
    # ESCAPE '\' makes %, _, and \ in the bound pattern literal characters.
    sql = (
        f"{_SELECT_PAPERS} "
        "WHERE title LIKE ? ESCAPE '\\' OR authors LIKE ? ESCAPE '\\'"
    )
    owns_connection = conn is None
    if owns_connection:
        conn = _connect()
    try:
        return conn.execute(sql, (pattern, pattern)).fetchall()
    finally:
        if owns_connection and conn is not None:
            conn.close()


def format_papers(rows: list[sqlite3.Row]) -> str:
    if not rows:
        return "No papers matched that keyword."

    blocks = []
    for row in rows:
        blocks.append(
            f"[{row['id']}] {row['title']} ({row['year']})\n"
            f"    Authors: {row['authors']}\n"
            f"    DOI: {row['doi']}\n"
            f"    Notes: {row['notes']}"
        )
    return "\n\n".join(blocks)


def search_citation_library(keyword: str) -> str:
    """Search the citation library and return a formatted string."""
    return format_papers(fetch_matching_papers(keyword))
