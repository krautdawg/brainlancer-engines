from db import db_conn


def get_all_suppliers():
    with db_conn() as conn:
        rows = conn.execute("""
            SELECT s.*,
                COUNT(DISTINCT po.id) AS total_orders,
                COALESCE(SUM(po.total_value), 0) AS total_spend,
                SUM(CASE WHEN po.status = 'paid' THEN 1 ELSE 0 END) AS completed_orders,
                SUM(CASE WHEN po.actual_delivery <= po.expected_delivery
                         AND po.actual_delivery IS NOT NULL THEN 1 ELSE 0 END) AS on_time_count
            FROM suppliers s
            LEFT JOIN purchase_orders po ON po.supplier_id = s.id
            GROUP BY s.id
            ORDER BY s.name
        """).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            total = d["total_orders"] or 0
            on_time = d["on_time_count"] or 0
            d["on_time_pct"] = round((on_time / total * 100) if total > 0 else 100, 1)
            result.append(d)
        return result


def get_supplier(supplier_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
        return dict(row) if row else None


def create_supplier(data: dict):
    with db_conn() as conn:
        cur = conn.execute(
            """INSERT INTO suppliers (name, contact_name, email, phone, payment_terms, address, category, notes)
               VALUES (:name, :contact_name, :email, :phone, :payment_terms, :address, :category, :notes)""",
            {
                "name": data.get("name"),
                "contact_name": data.get("contact_name", ""),
                "email": data.get("email", ""),
                "phone": data.get("phone", ""),
                "payment_terms": data.get("payment_terms", "30 Tage netto"),
                "address": data.get("address", ""),
                "category": data.get("category", ""),
                "notes": data.get("notes", ""),
            }
        )
        return cur.lastrowid


def update_supplier(supplier_id: int, data: dict):
    with db_conn() as conn:
        conn.execute(
            """UPDATE suppliers SET
               name = COALESCE(:name, name),
               contact_name = COALESCE(:contact_name, contact_name),
               email = COALESCE(:email, email),
               phone = COALESCE(:phone, phone),
               payment_terms = COALESCE(:payment_terms, payment_terms),
               address = COALESCE(:address, address),
               category = COALESCE(:category, category),
               notes = COALESCE(:notes, notes)
               WHERE id = :id""",
            {**data, "id": supplier_id}
        )


def delete_supplier(supplier_id: int):
    with db_conn() as conn:
        conn.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))


def get_supplier_orders(supplier_id: int):
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM purchase_orders WHERE supplier_id = ? ORDER BY created_at DESC",
            (supplier_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_supplier_scorecard(supplier_id: int):
    with db_conn() as conn:
        stats = conn.execute("""
            SELECT
                COUNT(*) AS total_orders,
                COALESCE(SUM(total_value), 0) AS total_spend,
                SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN actual_delivery <= expected_delivery
                         AND actual_delivery IS NOT NULL THEN 1 ELSE 0 END) AS on_time,
                SUM(CASE WHEN actual_delivery > expected_delivery THEN 1 ELSE 0 END) AS late
            FROM purchase_orders
            WHERE supplier_id = ?
        """, (supplier_id,)).fetchone()

        price_stats = conn.execute("""
            SELECT
                COUNT(*) AS total_checks,
                SUM(CASE WHEN status = 'green' THEN 1 ELSE 0 END) AS green,
                SUM(CASE WHEN status = 'yellow' THEN 1 ELSE 0 END) AS yellow,
                SUM(CASE WHEN status = 'red' THEN 1 ELSE 0 END) AS red,
                AVG(ABS(deviation_pct)) AS avg_deviation
            FROM price_records
            WHERE supplier_id = ?
        """, (supplier_id,)).fetchone()

        d = dict(stats)
        p = dict(price_stats)
        total = d["total_orders"] or 1
        on_time = d["on_time"] or 0
        d["on_time_pct"] = round(on_time / total * 100, 1)
        d["price_adherence_pct"] = round(
            ((p["green"] or 0) / max(p["total_checks"] or 1, 1)) * 100, 1
        )
        d["avg_price_deviation"] = round(p["avg_deviation"] or 0, 1)
        d["price_flags_yellow"] = p["yellow"] or 0
        d["price_flags_red"] = p["red"] or 0

        # Composite score (0-100)
        score = (d["on_time_pct"] * 0.6) + (d["price_adherence_pct"] * 0.4)
        d["score"] = round(score, 1)

        return d
