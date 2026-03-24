"""SQLite persistence layer for contracts, drafts, risk analyses, and comparisons."""

import json
import os
import sqlite3
import uuid
from datetime import datetime

import pandas as pd

from utils.config import DB_PATH

_CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS contracts (
    id TEXT PRIMARY KEY,
    filename TEXT,
    contract_type TEXT,
    status TEXT DEFAULT 'Draft',
    upload_date TEXT,
    effective_date TEXT,
    expiration_date TEXT,
    parties TEXT,
    obligations TEXT,
    penalties TEXT,
    payment_terms TEXT,
    risk_score INTEGER,
    risk_level TEXT,
    full_text TEXT,
    extracted_elements TEXT,
    file_path TEXT,
    tags TEXT,
    notes TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS drafts (
    id TEXT PRIMARY KEY,
    contract_type TEXT,
    parameters TEXT,
    draft_text TEXT,
    version INTEGER DEFAULT 1,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS risk_analyses (
    id TEXT PRIMARY KEY,
    contract_id TEXT,
    analysis_json TEXT,
    created_at TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE TABLE IF NOT EXISTS comparisons (
    id TEXT PRIMARY KEY,
    contract_a_id TEXT,
    contract_b_id TEXT,
    comparison_json TEXT,
    created_at TEXT
);
"""


def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_conn() as conn:
        conn.executescript(_CREATE_TABLES_SQL)


def save_contract(metadata: dict) -> str:
    contract_id = metadata.get("id", str(uuid.uuid4()))
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO contracts
            (id, filename, contract_type, status, upload_date, effective_date,
             expiration_date, parties, obligations, penalties, payment_terms,
             risk_score, risk_level, full_text, extracted_elements, file_path,
             tags, notes, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                contract_id,
                metadata.get("filename", ""),
                metadata.get("contract_type", ""),
                metadata.get("status", "Draft"),
                metadata.get("upload_date", now),
                metadata.get("effective_date", ""),
                metadata.get("expiration_date", ""),
                json.dumps(metadata.get("parties", [])),
                json.dumps(metadata.get("obligations", [])),
                json.dumps(metadata.get("penalties", [])),
                json.dumps(metadata.get("payment_terms", {})),
                metadata.get("risk_score"),
                metadata.get("risk_level", ""),
                metadata.get("full_text", ""),
                json.dumps(metadata.get("extracted_elements", {})),
                metadata.get("file_path", ""),
                metadata.get("tags", ""),
                metadata.get("notes", ""),
                metadata.get("created_at", now),
                now,
            ),
        )
    return contract_id


def load_contracts() -> pd.DataFrame:
    with _get_conn() as conn:
        df = pd.read_sql_query("SELECT * FROM contracts ORDER BY created_at DESC", conn)
    return df


def get_contract(contract_id: str) -> dict | None:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM contracts WHERE id=?", (contract_id,)).fetchone()
    if row is None:
        return None
    return dict(row)


def delete_contract(contract_id: str):
    with _get_conn() as conn:
        conn.execute("DELETE FROM contracts WHERE id=?", (contract_id,))


def search_contracts(query: str) -> pd.DataFrame:
    with _get_conn() as conn:
        df = pd.read_sql_query(
            "SELECT * FROM contracts WHERE filename LIKE ? OR contract_type LIKE ? OR tags LIKE ? ORDER BY created_at DESC",
            conn,
            params=(f"%{query}%", f"%{query}%", f"%{query}%"),
        )
    return df


def save_draft(contract_type: str, parameters: dict, draft_text: str, version: int = 1) -> str:
    draft_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO drafts (id, contract_type, parameters, draft_text, version, created_at) VALUES (?,?,?,?,?,?)",
            (draft_id, contract_type, json.dumps(parameters), draft_text, version, now),
        )
    return draft_id


def save_risk_analysis(contract_id: str, analysis: dict) -> str:
    analysis_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO risk_analyses (id, contract_id, analysis_json, created_at) VALUES (?,?,?,?)",
            (analysis_id, contract_id, json.dumps(analysis), now),
        )
        if analysis.get("overall_risk_score") is not None:
            conn.execute(
                "UPDATE contracts SET risk_score=?, risk_level=?, updated_at=? WHERE id=?",
                (analysis["overall_risk_score"], analysis.get("risk_level", ""), now, contract_id),
            )
    return analysis_id


def save_comparison(contract_a_id: str, contract_b_id: str, comparison: dict) -> str:
    comp_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO comparisons (id, contract_a_id, contract_b_id, comparison_json, created_at) VALUES (?,?,?,?,?)",
            (comp_id, contract_a_id, contract_b_id, json.dumps(comparison), now),
        )
    return comp_id


def get_dashboard_stats() -> dict:
    with _get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]
        by_status = dict(
            conn.execute("SELECT status, COUNT(*) FROM contracts GROUP BY status").fetchall()
        )
        by_type = dict(
            conn.execute("SELECT contract_type, COUNT(*) FROM contracts GROUP BY contract_type").fetchall()
        )
        avg_risk = conn.execute("SELECT AVG(risk_score) FROM contracts WHERE risk_score IS NOT NULL").fetchone()[0]
        high_risk = conn.execute("SELECT COUNT(*) FROM contracts WHERE risk_score >= 60").fetchone()[0]
        expiring = conn.execute(
            "SELECT COUNT(*) FROM contracts WHERE expiration_date != '' AND expiration_date <= date('now', '+30 days') AND status='Active'"
        ).fetchone()[0]
    return {
        "total": total,
        "by_status": by_status,
        "by_type": by_type,
        "avg_risk": round(avg_risk, 1) if avg_risk else 0,
        "high_risk_count": high_risk,
        "expiring_soon": expiring,
    }


# Initialize DB on import
init_db()
