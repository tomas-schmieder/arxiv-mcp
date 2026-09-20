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

## Project layout

```
.
├── server.py                          # FastMCP server: resource, tool, prompt
├── db/
│   ├── schema.sql                     # papers table
│   └── seed.py                        # sample citation library
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
