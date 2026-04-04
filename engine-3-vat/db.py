"""SQLite database layer for Engine 3: VAT Intelligence."""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.environ.get("DB_PATH", "vat_engine.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_tag TEXT NOT NULL DEFAULT 'default',
                filename TEXT,
                vendor TEXT,
                invoice_date TEXT,
                invoice_number TEXT,
                amount_net REAL DEFAULT 0,
                amount_vat REAL DEFAULT 0,
                amount_gross REAL DEFAULT 0,
                vat_rate REAL DEFAULT 0,
                category TEXT,
                correction_category TEXT,
                country TEXT DEFAULT 'DE',
                status TEXT DEFAULT 'to_review',
                confidence REAL DEFAULT 0,
                ai_flag INTEGER DEFAULT 0,
                ai_reason TEXT,
                correction_reason TEXT,
                correction_percentage REAL DEFAULT 100,
                source TEXT DEFAULT 'email',
                direction TEXT DEFAULT 'incoming',
                quarter INTEGER DEFAULT 1,
                year INTEGER DEFAULT 2024,
                raw_text TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS undo_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                previous_status TEXT,
                previous_category TEXT,
                previous_correction_category TEXT,
                previous_correction_reason TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
    conn.close()


def row_to_dict(row) -> dict:
    if row is None:
        return None
    d = dict(row)
    return d


def get_invoices(direction: str = None, status: str = None,
                 quarter: int = None, year: int = None) -> list:
    conn = get_conn()
    query = "SELECT * FROM invoices WHERE 1=1"
    params = []
    if direction:
        query += " AND direction = ?"
        params.append(direction)
    if status:
        query += " AND status = ?"
        params.append(status)
    if quarter:
        query += " AND quarter = ?"
        params.append(quarter)
    if year:
        query += " AND year = ?"
        params.append(year)
    query += " ORDER BY created_at ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def get_invoice(invoice_id: int) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


def update_invoice_status(invoice_id: int, status: str,
                           correction_category: str = None,
                           correction_reason: str = None,
                           correction_percentage: float = None) -> dict:
    """Update invoice status and optionally apply correction. Saves undo state."""
    conn = get_conn()
    with conn:
        # Save current state for undo
        current = conn.execute(
            "SELECT status, category, correction_category, correction_reason FROM invoices WHERE id = ?",
            (invoice_id,)
        ).fetchone()
        if current:
            conn.execute(
                """INSERT INTO undo_log
                   (invoice_id, previous_status, previous_category,
                    previous_correction_category, previous_correction_reason, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (invoice_id, current["status"], current["category"],
                 current["correction_category"], current["correction_reason"],
                 datetime.utcnow().isoformat())
            )

        # Apply update
        fields = ["status = ?"]
        vals = [status]
        if correction_category is not None:
            fields.append("correction_category = ?")
            vals.append(correction_category)
        if correction_reason is not None:
            fields.append("correction_reason = ?")
            vals.append(correction_reason)
        if correction_percentage is not None:
            fields.append("correction_percentage = ?")
            vals.append(correction_percentage)
        vals.append(invoice_id)
        conn.execute(f"UPDATE invoices SET {', '.join(fields)} WHERE id = ?", vals)

    row = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


def undo_last_action() -> Optional[dict]:
    """Undo the last triage action."""
    conn = get_conn()
    with conn:
        last = conn.execute(
            "SELECT * FROM undo_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not last:
            conn.close()
            return None

        conn.execute(
            """UPDATE invoices SET
               status = ?,
               correction_category = ?,
               correction_reason = ?
               WHERE id = ?""",
            (last["previous_status"], last["previous_correction_category"],
             last["previous_correction_reason"], last["invoice_id"])
        )
        conn.execute("DELETE FROM undo_log WHERE id = ?", (last["id"],))

    row = conn.execute("SELECT * FROM invoices WHERE id = ?", (last["invoice_id"],)).fetchone()
    conn.close()
    return row_to_dict(row)


def insert_invoice(data: dict) -> dict:
    conn = get_conn()
    with conn:
        cur = conn.execute(
            """INSERT INTO invoices
               (session_tag, filename, vendor, invoice_date, invoice_number,
                amount_net, amount_vat, amount_gross, vat_rate, category,
                correction_category, country, status, confidence,
                ai_flag, ai_reason, correction_reason, correction_percentage,
                source, direction, quarter, year, raw_text, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                data.get("session_tag", "default"),
                data.get("filename", ""),
                data.get("vendor", ""),
                data.get("invoice_date", ""),
                data.get("invoice_number", ""),
                data.get("amount_net", 0),
                data.get("amount_vat", 0),
                data.get("amount_gross", 0),
                data.get("vat_rate", 0),
                data.get("category", ""),
                data.get("correction_category"),
                data.get("country", "DE"),
                data.get("status", "to_review"),
                data.get("confidence", 0),
                1 if data.get("ai_flag") else 0,
                data.get("ai_reason"),
                data.get("correction_reason"),
                data.get("correction_percentage", 100),
                data.get("source", "email"),
                data.get("direction", "incoming"),
                data.get("quarter", 1),
                data.get("year", 2024),
                data.get("raw_text", ""),
                datetime.utcnow().isoformat(),
            )
        )
        invoice_id = cur.lastrowid
    row = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


def clear_all_invoices():
    conn = get_conn()
    with conn:
        conn.execute("DELETE FROM invoices")
        conn.execute("DELETE FROM undo_log")
    conn.close()


def get_setting(key: str, default=None):
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row["value"])
        except Exception:
            return row["value"]
    return default


def set_setting(key: str, value):
    conn = get_conn()
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, json.dumps(value))
        )
    conn.close()
