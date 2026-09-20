"""Create the local citation SQLite database and insert sample papers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent
DB_PATH = DB_DIR / "citations.db"
SCHEMA_PATH = DB_DIR / "schema.sql"

# Made-up but plausible papers across several topics so keyword filtering
# has distinct subsets (transformers, climate, quantum, HCI, databases, etc.).
SAMPLE_PAPERS = [
    (
        "Scaling Attention for Long-Context Transformers",
        "Maya Chen; Priya Natarajan",
        2023,
        "10.1234/arxiv.2304.11001",
        "Surveys sparse and linear attention variants for 100k-token contexts.",
    ),
    (
        "Retrieval-Augmented Generation for Scholarly Search",
        "Owen Blake; Linh Tran",
        2024,
        "10.1234/arxiv.2401.04412",
        "Compares dense retrievers against lexical baselines on academic QA.",
    ),
    (
        "Graph Neural Networks for Citation Recommendation",
        "Sofia Alvarez; Kenji Mori",
        2022,
        "10.1234/jcdl.2022.88110",
        "Treats the citation graph as a heterogeneous GNN over papers and authors.",
    ),
    (
        "Estimating Terrestrial Carbon Flux from Multi-Satellite Observations",
        "Hannah Cole; Yusuf Rahman",
        2021,
        "10.1234/rse.2021.55902",
        "Fuses MODIS and OCO-2 time series to estimate regional carbon flux.",
    ),
    (
        "Variational Quantum Algorithms for Combinatorial Optimization",
        "Elena Voss; Marcus Hill",
        2023,
        "10.1234/qst.2023.01844",
        "Benchmarks QAOA and VQE on Max-Cut instances up to 20 qubits.",
    ),
    (
        "Differential Privacy in Large Language Model Fine-Tuning",
        "Aisha Rahman; Tomasz Zielinski",
        2024,
        "10.1234/sp.2024.22109",
        "Measures utility loss when DP-SGD is applied to instruction tuning.",
    ),
    (
        "An Empirical Study of Code Review Latency in Open Source",
        "Jordan Hale; Mei Ling",
        2020,
        "10.1234/icse.2020.77321",
        "Analyzes wait time from pull request to first review across 200 repos.",
    ),
    (
        "Predicting Protein Folding Pathways with Geometric Deep Learning",
        "Nora Ibrahim; David Cho",
        2022,
        "10.1234/bioinf.2022.44108",
        "Uses SE(3)-equivariant networks to rank intermediate fold states.",
    ),
    (
        "Human-AI Collaboration Patterns in Academic Writing",
        "Clara Nguyen; Samir Patel",
        2025,
        "10.1234/chi.2025.01933",
        "Qualitative study of how researchers draft with LLM writing assistants.",
    ),
    (
        "Approximate Query Processing for Interactive Data Exploration",
        "Leo Martins; Rina Kapoor",
        2019,
        "10.1234/vldb.2019.31207",
        "Online aggregation with confidence bounds for dashboard workloads.",
    ),
]


def ensure_database() -> Path:
    """Create db/citations.db from schema.sql and seed it if empty."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(schema)
        existing = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        if existing == 0:
            conn.executemany(
                "INSERT INTO papers (title, authors, year, doi, notes) VALUES (?, ?, ?, ?, ?)",
                SAMPLE_PAPERS,
            )
            conn.commit()
    finally:
        conn.close()

    return DB_PATH


if __name__ == "__main__":
    path = ensure_database()
    print(f"Citation library ready at {path}")
