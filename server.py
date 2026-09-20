"""Academic Research MCP server: citation library, paper search, and review prompt."""

from __future__ import annotations

import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from dotenv import load_dotenv

# FastMCP server pattern from the official MCP Python SDK:
# https://github.com/modelcontextprotocol/python-sdk
from mcp.server.fastmcp import FastMCP

from db.seed import DB_PATH, ensure_database

# python-dotenv usage: https://pypi.org/project/python-dotenv/
load_dotenv(Path(__file__).resolve().parent / ".env")

ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"

mcp = FastMCP("Academic Research")
ensure_database()


def _format_papers(rows: list[sqlite3.Row]) -> str:
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


def _search_citation_library(keyword: str) -> str:
    """Return papers whose title or authors contain keyword (case-insensitive)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        # TODO(part2): parameterize this query, it is vulnerable to SQL injection
        sql = (
            "SELECT id, title, authors, year, doi, notes FROM papers "
            f"WHERE title LIKE '%{keyword}%' OR authors LIKE '%{keyword}%'"
        )
        rows = conn.execute(sql).fetchall()
    finally:
        conn.close()
    return _format_papers(rows)


@mcp.resource("citations://library/{keyword}")
def citation_library(keyword: str) -> str:
    """Search the local citation library by keyword in title or authors.

    An empty keyword (citations://library/) returns every saved paper.
    """
    return _search_citation_library(keyword)


@mcp.resource("citations://library/")
def citation_library_all() -> str:
    """Return the full local citation library (empty-keyword form of the template)."""
    return _search_citation_library("")


def _arxiv_doi(entry: ET.Element) -> str | None:
    doi = entry.findtext(f"{ARXIV_NS}doi")
    if doi:
        return doi.strip()
    arxiv_url = entry.findtext(f"{ATOM_NS}id") or ""
    arxiv_id = arxiv_url.rsplit("/", 1)[-1]
    if not arxiv_id:
        return None
    return f"10.48550/arXiv.{arxiv_id.split('v')[0]}"


@mcp.tool()
def search_papers(query: str, max_results: int = 5) -> list[dict] | str:
    """Search arXiv for papers matching a query.

    Returns title, authors, year, doi, and abstract for each hit. No API key
    is required.
    """
    response = None
    try:
        # arXiv API user manual:
        # https://info.arxiv.org/help/api/user-manual.html
        response = requests.get(
            "https://export.arxiv.org/api/query",
            params={
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
            },
            headers={"User-Agent": "academic-research-mcp/0.1"},
            timeout=30,
        )
        response.raise_for_status()
        root = ET.fromstring(response.text)

        results = []
        for entry in root.findall(f"{ATOM_NS}entry"):
            published = entry.findtext(f"{ATOM_NS}published") or ""
            year = int(published[:4]) if published[:4].isdigit() else None
            results.append(
                {
                    "title": " ".join((entry.findtext(f"{ATOM_NS}title") or "").split()),
                    "authors": [
                        name
                        for author in entry.findall(f"{ATOM_NS}author")
                        if (name := author.findtext(f"{ATOM_NS}name"))
                    ],
                    "year": year,
                    "doi": _arxiv_doi(entry),
                    "abstract": " ".join((entry.findtext(f"{ATOM_NS}summary") or "").split()),
                }
            )
        return results
    except Exception as exc:
        # TODO(part2): this leaks internal detail, sanitize before returning
        if response is not None:
            return response.text or str(exc)
        return str(exc)


@mcp.prompt()
def literature_review(topic: str, citation_style: str = "APA") -> str:
    """Build a prompt that asks a client LLM to write a short literature review."""
    return (
        f'Write a short literature review on the topic "{topic}".\n\n'
        "Follow these steps:\n"
        f'1. Call the search_papers tool to find 4 to 6 relevant sources on "{topic}".\n'
        "2. Check the citations://library/{keyword} resource for anything already "
        "saved on a related keyword.\n"
        f"3. Write a short synthesized literature review paragraph citing the "
        f"sources in {citation_style} format.\n"
    )


if __name__ == "__main__":
    mcp.run()
