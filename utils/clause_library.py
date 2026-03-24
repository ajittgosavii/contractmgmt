"""Clause Library — save, search, and reuse favorite contract clauses."""

import json
import os
import sqlite3
import uuid
from datetime import datetime

import pandas as pd

from utils.config import DB_PATH

_CLAUSE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS clause_library (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    clause_text TEXT NOT NULL,
    tags TEXT,
    contract_type TEXT,
    notes TEXT,
    created_by TEXT,
    created_at TEXT,
    updated_at TEXT,
    usage_count INTEGER DEFAULT 0
);
"""

CLAUSE_CATEGORIES = [
    "Termination",
    "Indemnification",
    "Limitation of Liability",
    "Confidentiality",
    "Force Majeure",
    "Intellectual Property",
    "Non-Compete",
    "Non-Solicitation",
    "Data Protection / GDPR",
    "Payment Terms",
    "Warranty",
    "Dispute Resolution",
    "Governing Law",
    "Insurance",
    "Compliance",
    "Amendment",
    "Assignment",
    "Severability",
    "Entire Agreement",
    "Other",
]


def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_clause_table():
    with _get_conn() as conn:
        conn.executescript(_CLAUSE_TABLE_SQL)


def save_clause(
    title: str,
    category: str,
    clause_text: str,
    tags: str = "",
    contract_type: str = "",
    notes: str = "",
    created_by: str = "",
) -> str:
    clause_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO clause_library
            (id, title, category, clause_text, tags, contract_type, notes, created_by, created_at, updated_at, usage_count)
            VALUES (?,?,?,?,?,?,?,?,?,?,0)""",
            (clause_id, title, category, clause_text, tags, contract_type, notes, created_by, now, now),
        )
    return clause_id


def update_clause(clause_id: str, title: str, category: str, clause_text: str, tags: str = "", notes: str = ""):
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        conn.execute(
            """UPDATE clause_library SET title=?, category=?, clause_text=?, tags=?, notes=?, updated_at=?
               WHERE id=?""",
            (title, category, clause_text, tags, notes, now, clause_id),
        )


def delete_clause(clause_id: str):
    with _get_conn() as conn:
        conn.execute("DELETE FROM clause_library WHERE id=?", (clause_id,))


def increment_usage(clause_id: str):
    with _get_conn() as conn:
        conn.execute("UPDATE clause_library SET usage_count = usage_count + 1 WHERE id=?", (clause_id,))


def load_clauses() -> pd.DataFrame:
    with _get_conn() as conn:
        return pd.read_sql_query("SELECT * FROM clause_library ORDER BY usage_count DESC, created_at DESC", conn)


def search_clauses(query: str = "", category: str = "") -> pd.DataFrame:
    where_parts = ["1=1"]
    params = []
    if query:
        where_parts.append("(title LIKE ? OR clause_text LIKE ? OR tags LIKE ?)")
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
    if category:
        where_parts.append("category = ?")
        params.append(category)

    sql = f"SELECT * FROM clause_library WHERE {' AND '.join(where_parts)} ORDER BY usage_count DESC"
    with _get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def get_clause(clause_id: str) -> dict | None:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM clause_library WHERE id=?", (clause_id,)).fetchone()
    return dict(row) if row else None


def get_popular_clauses(limit: int = 10) -> pd.DataFrame:
    with _get_conn() as conn:
        return pd.read_sql_query(
            "SELECT * FROM clause_library ORDER BY usage_count DESC LIMIT ?",
            conn,
            params=(limit,),
        )


# Initialize on import
init_clause_table()
