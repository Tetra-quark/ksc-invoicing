"""
SQLite-based invoice store.

Manages invoice numbering, history, and payment status tracking.
DB lives at kscinvoicing_data/invoices.db alongside other app data.
No Streamlit dependency — independently testable.
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("kscinvoicing_data/invoices.db")


def init_db(db_path: Path = DB_PATH) -> None:
    """Create tables if they don't exist."""
    db_path.parent.mkdir(exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                number      TEXT NOT NULL UNIQUE,
                date        TEXT,
                due_date    TEXT,
                sender_name TEXT,
                client_name TEXT,
                currency    TEXT,
                subtotal    REAL,
                discount    REAL,
                tax_rate    REAL,
                total       REAL,
                status      TEXT NOT NULL DEFAULT 'unpaid'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS line_items (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id     INTEGER NOT NULL REFERENCES invoices(id),
                description    TEXT,
                quantity       INTEGER,
                price_per_unit REAL
            )
        """)
        conn.commit()


def get_next_invoice_number(db_path: Path = DB_PATH) -> str:
    """Return the next invoice number as a zero-padded 4-digit string."""
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT MAX(CAST(number AS INTEGER)) FROM invoices"
        ).fetchone()
        prev = row[0] if row[0] is not None else 0
        return f"{prev + 1:04}"


def log_invoice(invoice_data, db_path: Path = DB_PATH) -> int:
    """Insert invoice and its line items into the DB. Returns the new invoice row id."""
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO invoices
                (number, date, due_date, sender_name, client_name, currency,
                 subtotal, discount, tax_rate, total, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'unpaid')
            """,
            (
                invoice_data.invoice_number,
                invoice_data.date.strftime("%Y-%m-%d"),
                invoice_data.due_date.strftime("%Y-%m-%d") if invoice_data.due_date else None,
                invoice_data.sender.name,
                invoice_data.recipient.name,
                invoice_data.currency,
                float(invoice_data.subtotal),
                float(invoice_data.discount),
                float(invoice_data.tax_rate),
                float(invoice_data.total),
            ),
        )
        invoice_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO line_items (invoice_id, description, quantity, price_per_unit) VALUES (?, ?, ?, ?)",
            [
                (invoice_id, item.description, item.quantity, float(item.price_per_unit))
                for item in invoice_data.items
            ],
        )
        conn.commit()
        return invoice_id


def get_all_invoices(db_path: Path = DB_PATH) -> list[dict]:
    """Return all invoices ordered by invoice number descending."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM invoices ORDER BY CAST(number AS INTEGER) DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def get_invoice_line_items(invoice_id: int, db_path: Path = DB_PATH) -> list[dict]:
    """Return line items for a given invoice."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM line_items WHERE invoice_id = ?", (invoice_id,)
        ).fetchall()
        return [dict(row) for row in rows]


def update_invoice_status(invoice_id: int, status: str, db_path: Path = DB_PATH) -> None:
    """Update the payment status of an invoice. status: 'unpaid' | 'paid' | 'overdue'"""
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE invoices SET status = ? WHERE id = ?", (status, invoice_id))
        conn.commit()


def migrate_from_json(json_path: Path, db_path: Path = DB_PATH) -> int:
    """
    Import entries from a legacy log.json into the DB.
    Skips entries whose number already exists. Returns count of migrated entries.
    """
    if not json_path.exists():
        return 0
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    migrated = 0
    with sqlite3.connect(db_path) as conn:
        for number, entry in data.items():
            exists = conn.execute(
                "SELECT 1 FROM invoices WHERE number = ?", (number,)
            ).fetchone()
            if exists:
                continue
            try:
                date_str = datetime.strptime(entry["date"], "%d/%m/%Y").strftime("%Y-%m-%d")
            except (ValueError, KeyError):
                date_str = None
            conn.execute(
                """
                INSERT INTO invoices (number, date, sender_name, client_name, total, status)
                VALUES (?, ?, ?, ?, ?, 'unpaid')
                """,
                (
                    number,
                    date_str,
                    entry.get("invoice_from", ""),
                    entry.get("invoice_to", ""),
                    float(entry.get("total amount", 0)),
                ),
            )
            migrated += 1
        conn.commit()
    return migrated
