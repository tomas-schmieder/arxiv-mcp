# arXiv MCP

An [MCP](https://modelcontextprotocol.io/) server for academic research. It
gives Claude Desktop (or any MCP client) three complementary capabilities:
search the public arXiv API, browse a local SQLite citation library, and
generate a literature-review prompt in a chosen citation style.

No API key is required. `search_papers` talks to the
[public arXiv API](https://info.arxiv.org/help/api/user-manual.html).

## Capabilities

| Kind | Name | What it does |
| --- | --- | --- |
| Resource | `citations://library/{keyword}` | Search a local SQLite library of saved papers by title or author. An empty keyword (`citations://library/`) returns the full table. |
| Tool | `search_papers` | Query arXiv and return title, authors, year, DOI, and abstract. |
| Prompt | `literature_review` | Ask a client LLM to use the tool and resource, then write a short review in APA, MLA, or another citation style. |

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
git clone https://github.com/tomas-schmieder/arxiv-mcp.git
cd arxiv-mcp
uv sync
```

The citation database is created automatically the first time the server
starts. To seed it yourself:

```bash
uv run python db/seed.py
```

## Run with MCP Inspector

```bash
uv run mcp dev server.py
```

Inspector should list:

- one static resource: `citations://library/`
- one resource template: `citations://library/{keyword}`
- the `search_papers` tool
- the `literature_review` prompt

Try these once it is up:

| Surface | Input | Expected result |
| --- | --- | --- |
| Resource | `citations://library/` | All seeded papers |
| Resource | `citations://library/transformer` | Papers whose title or authors mention “transformer” |
| Tool | `search_papers` with query `attention transformers` | Live arXiv hits with abstracts |
| Prompt | `literature_review` with topic `retrieval augmented generation` | A ready-to-run review prompt |

## Connect Claude Desktop

1. Open Claude Desktop settings and edit the MCP config (macOS:
   `~/Library/Application Support/Claude/claude_desktop_config.json`).
2. Copy the `academic-research` entry from
   [`claude_desktop_config.example.json`](claude_desktop_config.example.json).
3. Replace `/ABSOLUTE/PATH/TO/academic-research-mcp` with the real path to
   this directory.
4. Restart Claude Desktop.

The example launches the server with `uv run server.py` from this project
directory, following the
[official MCP server quickstart](https://modelcontextprotocol.io/quickstart/server).

## Security best practices

Two defenses sit in front of the MCP surfaces that talk to SQL and HTTP.

### Input sanitization

The citation resource used to interpolate the keyword into SQL with an
f-string. Keywords are now bound with sqlite3 placeholders, and LIKE
wildcards (`%`, `_`) are escaped so a search is a literal substring match.

Run the exploit demo:

```bash
uv run python exploits/sql_injection.py
```

It replays two payloads against the old query, then against the
parameterized one:

| Payload | Without parameterization | With parameterization |
| --- | --- | --- |
| `zzz_no_such_paper' OR 1=1 --` | Returns every seeded paper | No rows (treated as a literal) |
| `' UNION SELECT ... FROM sqlite_master --` | Leaks `CREATE TABLE` DDL | No rows |

A normal search for `transformer` still returns the transformer paper.

In Inspector, the same UNION payload on `citations://library/{keyword}`
should return “No papers matched that keyword.”

### Error disclosure

Part 1 returned raw `response.text` or `str(exc)` to the client, which can
include tracebacks, URLs, and other internals. Failures now log server-side
and return a generic message:

`Paper search is temporarily unavailable. Please try again later.`

Run the exploit demo:

```bash
uv run python exploits/error_disclosure.py
```

It feeds the old handler a fake HTTP 500 body and a connection error that
contain a marker secret, then shows that `search_papers` returns only the
generic string.

To see the same behavior in Inspector, point the tool at a closed port and
call `search_papers`:

```bash
ARXIV_API_URL=http://127.0.0.1:1 uv run mcp dev server.py
```

You should get the generic message, not a connection-pool traceback.

## Project layout

```
.
├── server.py                          # FastMCP server: resource, tool, prompt
├── errors.py                          # Generic client errors; details stay in logs
├── db/
│   ├── schema.sql                     # papers table
│   ├── seed.py                        # sample citation library
│   └── library.py                     # parameterized citation search
├── exploits/
│   ├── sql_injection.py               # tautology + UNION demo
│   └── error_disclosure.py            # raw error vs generic message
├── claude_desktop_config.example.json # Claude Desktop MCP config
├── requirements.txt
└── pyproject.toml
```

## Notes

- The MCP Python SDK is pinned to `mcp[cli]>=1.2,<2`. Version 2.x renamed
  `mcp.server.fastmcp.FastMCP`.
- arXiv asks clients to keep request volume modest (about one call every few
  seconds). Please do the same.
- `search_papers` uses no credentials. Copy `.env.example` to `.env` only if
  you later add secrets of your own; `.env` is gitignored.
