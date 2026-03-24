"""Audit trail for tracking all user actions on contracts."""

import json
import os
import sqlite3
import uuid
from datetime import datetime

import pandas as pd

from utils.config import DB_PATH

_AUDIT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_trail (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    entity_name TEXT,
    details TEXT,
    ip_address TEXT
);
"""


def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_audit_table():
    with _get_conn() as conn:
        conn.executescript(_AUDIT_TABLE_SQL)


# Actions
ACTION_UPLOAD = "upload"
ACTION_EXTRACT = "extract_elements"
ACTION_SAVE = "save_to_repository"
ACTION_DELETE = "delete"
ACTION_GENERATE_DRAFT = "generate_draft"
ACTION_REFINE_DRAFT = "refine_draft"
ACTION_RISK_ANALYSIS = "risk_analysis"
ACTION_COMPARE = "compare_contracts"
ACTION_EXPORT = "export"
ACTION_BULK_UPLOAD = "bulk_upload"
ACTION_EMAIL_ALERT = "email_alert"
ACTION_LOGIN = "login"
ACTION_LOGOUT = "logout"
ACTION_CLAUSE_SAVE = "save_clause"
ACTION_CLAUSE_DELETE = "delete_clause"
ACTION_USER_ADD = "add_user"
ACTION_USER_REMOVE = "remove_user"


def log_action(
    username: str,
    action: str,
    entity_type: str,
    entity_id: str = "",
    entity_name: str = "",
    details: str = "",
):
    """Log an audit event."""
    audit_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO audit_trail
            (id, timestamp, username, action, entity_type, entity_id, entity_name, details)
            VALUES (?,?,?,?,?,?,?,?)""",
            (audit_id, now, username, action, entity_type, entity_id, entity_name, details),
        )


def get_audit_log(limit: int = 100, username: str = None, action: str = None, entity_type: str = None) -> pd.DataFrame:
    """Retrieve audit log with optional filters."""
    query = "SELECT * FROM audit_trail WHERE 1=1"
    params = []

    if username:
        query += " AND username = ?"
        params.append(username)
    if action:
        query += " AND action = ?"
        params.append(action)
    if entity_type:
        query += " AND entity_type = ?"
        params.append(entity_type)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    with _get_conn() as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_user_activity_summary() -> pd.DataFrame:
    """Get activity summary grouped by user."""
    with _get_conn() as conn:
        return pd.read_sql_query(
            """SELECT username, action, COUNT(*) as count,
                      MAX(timestamp) as last_activity
               FROM audit_trail
               GROUP BY username, action
               ORDER BY last_activity DESC""",
            conn,
        )


def get_contract_history(contract_id: str) -> pd.DataFrame:
    """Get all audit events for a specific contract."""
    with _get_conn() as conn:
        return pd.read_sql_query(
            "SELECT * FROM audit_trail WHERE entity_id = ? ORDER BY timestamp DESC",
            conn,
            params=(contract_id,),
        )


# Initialize on import
init_audit_table()
