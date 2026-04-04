import sqlite3
import json
import os

DB_PATH = os.getenv("DB_PATH", "leadgen.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS icp_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                company_name TEXT,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                icp_id INTEGER,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def save_icp(session_id: str, icp_data: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO icp_profiles (session_id, company_name, data) VALUES (?, ?, ?)",
            (session_id, icp_data.get("company_name", ""), json.dumps(icp_data)),
        )
        conn.commit()
        return cur.lastrowid


def save_leads(session_id: str, icp_id: int, leads: list):
    with get_conn() as conn:
        for lead in leads:
            conn.execute(
                "INSERT INTO leads (session_id, icp_id, data) VALUES (?, ?, ?)",
                (session_id, icp_id, json.dumps(lead)),
            )
        conn.commit()


def get_session_leads(session_id: str) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT data FROM leads WHERE session_id = ? ORDER BY created_at DESC",
            (session_id,),
        ).fetchall()
        return [json.loads(row["data"]) for row in rows]


def clear_session_leads(session_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM leads WHERE session_id = ?", (session_id,))
        conn.commit()
