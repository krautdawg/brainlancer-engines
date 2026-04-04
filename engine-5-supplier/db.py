import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.environ.get("DB_PATH", "supplier_engine.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_conn():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with db_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_name TEXT,
            email TEXT,
            phone TEXT,
            payment_terms TEXT DEFAULT '30 Tage netto',
            address TEXT,
            category TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT UNIQUE NOT NULL,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
            status TEXT DEFAULT 'ordered',
            expected_delivery TEXT,
            actual_delivery TEXT,
            category TEXT,
            total_value REAL DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS po_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            quantity REAL DEFAULT 1,
            unit_price REAL DEFAULT 0,
            total_price REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS price_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER REFERENCES purchase_orders(id),
            supplier_id INTEGER REFERENCES suppliers(id),
            item_description TEXT,
            approved_price REAL,
            invoice_price REAL,
            deviation_pct REAL,
            status TEXT DEFAULT 'green',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS chase_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER NOT NULL REFERENCES purchase_orders(id),
            level INTEGER DEFAULT 1,
            subject TEXT,
            body TEXT,
            generated_at TEXT DEFAULT (datetime('now')),
            approved INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS demo_loaded (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            loaded_at TEXT DEFAULT (datetime('now'))
        );
        """)
