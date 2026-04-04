from db import db_conn


def get_summary():
    with db_conn() as conn:
        totals = conn.execute("""
            SELECT
                COUNT(*) AS total_pos,
                COALESCE(SUM(total_value), 0) AS total_spend,
                SUM(CASE WHEN status = 'paid' THEN total_value ELSE 0 END) AS paid_spend,
                SUM(CASE WHEN status NOT IN ('received','invoiced','paid')
                             AND expected_delivery < date('now') THEN 1 ELSE 0 END) AS overdue_count,
                COUNT(DISTINCT supplier_id) AS supplier_count
            FROM purchase_orders
        """).fetchone()

        price_flags = conn.execute("""
            SELECT
                SUM(CASE WHEN status = 'yellow' THEN 1 ELSE 0 END) AS yellow_flags,
                SUM(CASE WHEN status = 'red' THEN 1 ELSE 0 END) AS red_flags
            FROM price_records
        """).fetchone()

        d = dict(totals)
        d.update(dict(price_flags))
        return d


def get_spend_by_supplier():
    with db_conn() as conn:
        rows = conn.execute("""
            SELECT s.name AS supplier_name,
                   COALESCE(SUM(po.total_value), 0) AS total_spend,
                   COUNT(po.id) AS order_count
            FROM suppliers s
            LEFT JOIN purchase_orders po ON po.supplier_id = s.id
            GROUP BY s.id, s.name
            ORDER BY total_spend DESC
        """).fetchall()
        return [dict(r) for r in rows]


def get_spend_by_category():
    with db_conn() as conn:
        rows = conn.execute("""
            SELECT
                COALESCE(NULLIF(category, ''), 'Sonstiges') AS category,
                SUM(total_value) AS total_spend,
                COUNT(*) AS order_count
            FROM purchase_orders
            GROUP BY category
            ORDER BY total_spend DESC
        """).fetchall()
        return [dict(r) for r in rows]


def get_spend_trend():
    with db_conn() as conn:
        rows = conn.execute("""
            SELECT
                strftime('%Y-%m', created_at) AS month,
                SUM(total_value) AS total_spend,
                COUNT(*) AS order_count
            FROM purchase_orders
            GROUP BY month
            ORDER BY month ASC
        """).fetchall()
        return [dict(r) for r in rows]


def get_top_anomalies():
    with db_conn() as conn:
        rows = conn.execute("""
            SELECT pr.*, s.name AS supplier_name, po.po_number
            FROM price_records pr
            JOIN suppliers s ON s.id = pr.supplier_id
            LEFT JOIN purchase_orders po ON po.id = pr.po_id
            WHERE pr.status IN ('yellow', 'red')
            ORDER BY ABS(pr.deviation_pct) DESC
            LIMIT 10
        """).fetchall()
        return [dict(r) for r in rows]


def get_monthly_by_supplier():
    with db_conn() as conn:
        rows = conn.execute("""
            SELECT
                strftime('%Y-%m', po.created_at) AS month,
                s.name AS supplier_name,
                SUM(po.total_value) AS total_spend
            FROM purchase_orders po
            JOIN suppliers s ON s.id = po.supplier_id
            GROUP BY month, s.id
            ORDER BY month ASC
        """).fetchall()
        return [dict(r) for r in rows]
