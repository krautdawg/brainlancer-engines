import csv
import io
from datetime import date
from db import db_conn

STATUSES = ["ordered", "shipped", "received", "invoiced", "paid"]


def get_all_pos(status: str = None, supplier_id: int = None):
    with db_conn() as conn:
        query = """
            SELECT po.*, s.name AS supplier_name, s.email AS supplier_email,
                   s.contact_name AS supplier_contact,
                   CASE WHEN po.status NOT IN ('received','invoiced','paid')
                             AND po.expected_delivery < date('now')
                        THEN 1 ELSE 0 END AS is_overdue
            FROM purchase_orders po
            JOIN suppliers s ON s.id = po.supplier_id
            WHERE 1=1
        """
        params = []
        if status:
            query += " AND po.status = ?"
            params.append(status)
        if supplier_id:
            query += " AND po.supplier_id = ?"
            params.append(supplier_id)
        query += " ORDER BY po.created_at DESC"
        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["items"] = get_po_items_inline(conn, d["id"])
            result.append(d)
        return result


def get_po(po_id: int):
    with db_conn() as conn:
        row = conn.execute("""
            SELECT po.*, s.name AS supplier_name, s.email AS supplier_email,
                   s.contact_name AS supplier_contact,
                   CASE WHEN po.status NOT IN ('received','invoiced','paid')
                             AND po.expected_delivery < date('now')
                        THEN 1 ELSE 0 END AS is_overdue
            FROM purchase_orders po
            JOIN suppliers s ON s.id = po.supplier_id
            WHERE po.id = ?
        """, (po_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["items"] = get_po_items_inline(conn, d["id"])
        return d


def get_po_items_inline(conn, po_id: int):
    rows = conn.execute(
        "SELECT * FROM po_items WHERE po_id = ? ORDER BY id", (po_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def create_po(data: dict):
    with db_conn() as conn:
        cur = conn.execute(
            """INSERT INTO purchase_orders
               (po_number, supplier_id, status, expected_delivery, category, total_value, notes)
               VALUES (:po_number, :supplier_id, :status, :expected_delivery, :category, :total_value, :notes)""",
            {
                "po_number": data["po_number"],
                "supplier_id": data["supplier_id"],
                "status": data.get("status", "ordered"),
                "expected_delivery": data.get("expected_delivery"),
                "category": data.get("category", ""),
                "total_value": data.get("total_value", 0),
                "notes": data.get("notes", ""),
            }
        )
        po_id = cur.lastrowid
        items = data.get("items", [])
        total = 0
        for item in items:
            qty = float(item.get("quantity", 1))
            price = float(item.get("unit_price", 0))
            line_total = qty * price
            total += line_total
            conn.execute(
                """INSERT INTO po_items (po_id, description, quantity, unit_price, total_price)
                   VALUES (?, ?, ?, ?, ?)""",
                (po_id, item["description"], qty, price, line_total)
            )
        if items:
            conn.execute(
                "UPDATE purchase_orders SET total_value = ? WHERE id = ?",
                (total, po_id)
            )
        return po_id


def update_po_status(po_id: int, new_status: str):
    if new_status not in STATUSES:
        raise ValueError(f"Invalid status: {new_status}")
    with db_conn() as conn:
        updates = {"status": new_status, "id": po_id}
        if new_status == "received":
            updates["actual_delivery"] = date.today().isoformat()
            conn.execute(
                "UPDATE purchase_orders SET status=:status, actual_delivery=:actual_delivery, updated_at=datetime('now') WHERE id=:id",
                updates
            )
        else:
            conn.execute(
                "UPDATE purchase_orders SET status=:status, updated_at=datetime('now') WHERE id=:id",
                updates
            )


def update_po(po_id: int, data: dict):
    with db_conn() as conn:
        conn.execute(
            """UPDATE purchase_orders SET
               expected_delivery = COALESCE(:expected_delivery, expected_delivery),
               category = COALESCE(:category, category),
               notes = COALESCE(:notes, notes),
               updated_at = datetime('now')
               WHERE id = :id""",
            {**data, "id": po_id}
        )


def delete_po(po_id: int):
    with db_conn() as conn:
        conn.execute("DELETE FROM purchase_orders WHERE id = ?", (po_id,))


def get_overdue_pos():
    with db_conn() as conn:
        rows = conn.execute("""
            SELECT po.*, s.name AS supplier_name, s.email AS supplier_email,
                   s.contact_name AS supplier_contact,
                   julianday('now') - julianday(po.expected_delivery) AS days_overdue
            FROM purchase_orders po
            JOIN suppliers s ON s.id = po.supplier_id
            WHERE po.status NOT IN ('received','invoiced','paid')
              AND po.expected_delivery < date('now')
            ORDER BY po.expected_delivery ASC
        """).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["days_overdue"] = int(d["days_overdue"] or 0)
            d["items"] = get_po_items_inline(conn, d["id"])
            result.append(d)
        return result


def parse_csv_upload(content: bytes):
    """Parse CSV with columns: po_number, supplier_name, item_description,
       quantity, unit_price, expected_delivery, category"""
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    pos_by_number = {}
    for row in reader:
        po_num = row.get("po_number", "").strip()
        if not po_num:
            continue
        if po_num not in pos_by_number:
            pos_by_number[po_num] = {
                "po_number": po_num,
                "supplier_name": row.get("supplier_name", "").strip(),
                "expected_delivery": row.get("expected_delivery", "").strip(),
                "category": row.get("category", "").strip(),
                "items": [],
            }
        desc = row.get("item_description", "").strip()
        qty = float(row.get("quantity", 1) or 1)
        price = float(row.get("unit_price", 0) or 0)
        if desc:
            pos_by_number[po_num]["items"].append({
                "description": desc,
                "quantity": qty,
                "unit_price": price,
            })
    return list(pos_by_number.values())
