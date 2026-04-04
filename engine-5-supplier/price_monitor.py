from db import db_conn


def get_all_deviations():
    with db_conn() as conn:
        rows = conn.execute("""
            SELECT pr.*, s.name AS supplier_name, po.po_number
            FROM price_records pr
            JOIN suppliers s ON s.id = pr.supplier_id
            LEFT JOIN purchase_orders po ON po.id = pr.po_id
            ORDER BY ABS(pr.deviation_pct) DESC
        """).fetchall()
        return [dict(r) for r in rows]


def add_price_record(data: dict):
    approved = float(data["approved_price"])
    invoice = float(data["invoice_price"])
    deviation = ((invoice - approved) / approved * 100) if approved > 0 else 0
    deviation = round(deviation, 2)

    if abs(deviation) < 5:
        status = "green"
    elif abs(deviation) < 10:
        status = "yellow"
    else:
        status = "red"

    with db_conn() as conn:
        cur = conn.execute(
            """INSERT INTO price_records
               (po_id, supplier_id, item_description, approved_price, invoice_price, deviation_pct, status)
               VALUES (:po_id, :supplier_id, :item_description, :approved_price, :invoice_price, :deviation_pct, :status)""",
            {
                "po_id": data.get("po_id"),
                "supplier_id": data["supplier_id"],
                "item_description": data.get("item_description", ""),
                "approved_price": approved,
                "invoice_price": invoice,
                "deviation_pct": deviation,
                "status": status,
            }
        )
        return cur.lastrowid


def delete_price_record(record_id: int):
    with db_conn() as conn:
        conn.execute("DELETE FROM price_records WHERE id = ?", (record_id,))


def get_deviation_summary():
    with db_conn() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'green' THEN 1 ELSE 0 END) AS green,
                SUM(CASE WHEN status = 'yellow' THEN 1 ELSE 0 END) AS yellow,
                SUM(CASE WHEN status = 'red' THEN 1 ELSE 0 END) AS red,
                AVG(ABS(deviation_pct)) AS avg_abs_deviation
            FROM price_records
        """).fetchone()
        return dict(row)
