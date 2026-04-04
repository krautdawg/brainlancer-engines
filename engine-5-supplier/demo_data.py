"""Pre-load demo procurement data: 5 German suppliers, 25 POs, 3 overdue, 2 price deviations."""
from datetime import date, timedelta
from db import db_conn

TODAY = date(2026, 4, 4)


def _d(delta_days: int) -> str:
    return (TODAY + timedelta(days=delta_days)).isoformat()


SUPPLIERS = [
    {
        "name": "Müller Metallbau GmbH",
        "contact_name": "Thomas Müller",
        "email": "t.mueller@mueller-metallbau.de",
        "phone": "+49 89 12345678",
        "payment_terms": "30 Tage netto",
        "address": "Industriestraße 14, 80339 München",
        "category": "Metall & Fertigung",
        "notes": "Hauptlieferant für Stahlkomponenten",
    },
    {
        "name": "Schmidt Elektronik AG",
        "contact_name": "Sabine Schmidt",
        "email": "s.schmidt@schmidt-elektronik.de",
        "phone": "+49 40 98765432",
        "payment_terms": "14 Tage 2% Skonto, 30 Tage netto",
        "address": "Hafenweg 7, 20459 Hamburg",
        "category": "Elektronik & Komponenten",
        "notes": "Zuverlässiger Elektroniklieferant, ISO 9001 zertifiziert",
    },
    {
        "name": "Weber Kunststoff GmbH",
        "contact_name": "Klaus Weber",
        "email": "k.weber@weber-kunststoff.de",
        "phone": "+49 711 55566677",
        "payment_terms": "45 Tage netto",
        "address": "Gewerbepark 3, 70174 Stuttgart",
        "category": "Kunststoff & Verpackung",
        "notes": "Spezialist für technische Kunststoffteile",
    },
    {
        "name": "Fischer Logistik GmbH",
        "contact_name": "Maria Fischer",
        "email": "m.fischer@fischer-logistik.de",
        "phone": "+49 30 44455566",
        "payment_terms": "30 Tage netto",
        "address": "Logistikzentrum 22, 10115 Berlin",
        "category": "Logistik & Verpackung",
        "notes": "Verpackungsmaterial und Lagerlösungen",
    },
    {
        "name": "Bauer Chemikalien GmbH",
        "contact_name": "Hans Bauer",
        "email": "h.bauer@bauer-chemikalien.de",
        "phone": "+49 221 77788899",
        "payment_terms": "21 Tage netto",
        "address": "Chemiepark Nord, 50667 Köln",
        "category": "Chemikalien & Rohstoffe",
        "notes": "Gefahrgutlieferant – REACH-konform",
    },
]

# (supplier_index, po_number, status, expected_delivery_delta,
#  actual_delivery_delta_or_None, category, items, notes)
PO_DATA = [
    # Müller Metallbau – 5 POs
    (0, "PO-2026-001", "paid", -75, -72, "Metall & Fertigung",
     [("Stahlplatten 10mm (A36)", 50, 85.00), ("Schrauben M12 (Box 100)", 20, 12.50)], ""),
    (0, "PO-2026-002", "paid", -60, -57, "Metall & Fertigung",
     [("Aluminiumprofile 40x40", 100, 22.00), ("Schweißdraht 1kg Rolle", 30, 8.50)], ""),
    (0, "PO-2026-003", "invoiced", -30, -25, "Metall & Fertigung",
     [("Edelstahlrohre DN50 (2m)", 40, 45.00)], "Rechnung erhalten, Prüfung ausstehend"),
    (0, "PO-2026-004", "shipped", -10, None, "Metall & Fertigung",
     [("Stahlbleche verzinkt 2mm", 80, 32.00), ("Nieten Sortiment", 10, 18.00)], ""),
    (0, "PO-2026-010", "ordered", 14, None, "Metall & Fertigung",
     [("Präzisionswellen Ø20mm", 25, 65.00)], "Eilbestellung"),

    # Schmidt Elektronik – 5 POs
    (1, "PO-2026-005", "paid", -80, -78, "Elektronik & Komponenten",
     [("Leiterplatten PCB v2.1", 200, 4.50), ("Kondensatoren 100µF (100er Pack)", 15, 22.00)], ""),
    (1, "PO-2026-006", "paid", -55, -53, "Elektronik & Komponenten",
     [("Mikrocontroller STM32F4", 50, 8.75), ("USB-C Stecker (50er Pack)", 20, 15.00)], ""),
    (1, "PO-2026-007", "received", -20, -18, "Elektronik & Komponenten",
     [("Sensoren NTC 10kΩ (25er Pack)", 30, 35.00), ("Kabel AWG22 (10m)", 50, 6.50)], "Qualitätsprüfung läuft"),
    (1, "PO-2026-008", "shipped", -8, None, "Elektronik & Komponenten",
     [("Treiber-ICs L298N", 100, 3.20), ("Platinenmaterial FR4 (5 Stk)", 20, 45.00)], ""),
    (1, "PO-2026-015", "ordered", 21, None, "Elektronik & Komponenten",
     [("Spannungsregler LM317 (25er)", 40, 12.00)], ""),

    # Weber Kunststoff – 5 POs
    (2, "PO-2026-009", "paid", -90, -88, "Kunststoff & Verpackung",
     [("ABS-Granulat 25kg Sack", 20, 78.00), ("PA66 Rohstoff 10kg", 10, 95.00)], ""),
    (2, "PO-2026-011", "invoiced", -35, -30, "Kunststoff & Verpackung",
     [("POM Formteile (Satz)", 60, 14.50)], ""),
    (2, "PO-2026-012", "shipped", -12, None, "Kunststoff & Verpackung",
     [("PE-Folie 500m Rolle", 5, 125.00), ("Schutzfolie 3m (50m Rolle)", 10, 42.00)], ""),
    (2, "PO-2026-016", "ordered", 10, None, "Kunststoff & Verpackung",
     [("PTFE-Stab Ø25mm (500mm)", 30, 28.00)], ""),
    (2, "PO-2026-020", "ordered", 18, None, "Kunststoff & Verpackung",
     [("Schaumstoffstreifen 10mm (Rolle)", 15, 22.50)], ""),

    # Fischer Logistik – 5 POs
    (3, "PO-2026-013", "paid", -65, -63, "Logistik & Verpackung",
     [("Kartonagen 600x400x300 (100er)", 5, 85.00), ("Luftpolsterfolie 50m Rolle", 20, 18.00)], ""),
    (3, "PO-2026-014", "received", -25, -22, "Logistik & Verpackung",
     [("Paletten EURO 1200x800 (10er)", 3, 120.00), ("Stretchfolie 500mm (6 Rollen)", 10, 22.00)], ""),
    (3, "PO-2026-017", "invoiced", -28, -24, "Logistik & Verpackung",
     [("Versandkartons A3 (50er)", 8, 35.00)], ""),
    (3, "PO-2026-021", "ordered", 7, None, "Logistik & Verpackung",
     [("Klebeband braun 50m (6er Pack)", 25, 8.50), ("Beschriftungsetiketten (500er)", 10, 12.00)], ""),
    (3, "PO-2026-024", "ordered", 15, None, "Logistik & Verpackung",
     [("Schutzkanten 35mm (25m Rolle)", 12, 24.00)], ""),

    # Bauer Chemikalien – 5 POs
    (4, "PO-2026-018", "paid", -85, -83, "Chemikalien & Rohstoffe",
     [("Isopropanol 99% (5L Kanister)", 40, 28.00), ("Aceton techn. (5L)", 20, 18.50)], "Gefahrgut"),
    (4, "PO-2026-019", "paid", -50, -47, "Chemikalien & Rohstoffe",
     [("Epoxidharz L + Härter (5kg Set)", 15, 95.00)], ""),
    (4, "PO-2026-022", "ordered", 5, None, "Chemikalien & Rohstoffe",
     [("Reinigungsmittel Neutral (10L)", 30, 22.00), ("Schmierfett Mehrzweck 1kg", 20, 15.00)], ""),
    (4, "PO-2026-023", "received", -18, -15, "Chemikalien & Rohstoffe",
     [("Trennmittel Spray 500ml (12er)", 20, 14.50)], ""),
    (4, "PO-2026-025", "ordered", 12, None, "Chemikalien & Rohstoffe",
     [("Lösungsmittel MEK (5L)", 10, 42.00)], ""),
]

# 3 overdue POs: set expected_delivery in the past, status = ordered/shipped
OVERDUE_OVERRIDES = {
    "PO-2026-004": -18,  # Müller – shipped 18 days ago, expected 10 days ago
    "PO-2026-012": -22,  # Weber  – shipped 22 days ago, expected 12 days ago
    "PO-2026-022": -8,   # Bauer  – ordered, expected 8 days ago
}

# Price deviation records
PRICE_DEVIATIONS = [
    # (po_number, supplier_index, item_desc, approved_price, invoice_price)
    ("PO-2026-003", 0, "Edelstahlrohre DN50 (2m)", 45.00, 48.60),   # +8% yellow
    ("PO-2026-017", 3, "Versandkartons A3 (50er)", 35.00, 39.90),   # +14% red
]


def is_demo_loaded():
    with db_conn() as conn:
        row = conn.execute("SELECT id FROM demo_loaded LIMIT 1").fetchone()
        return row is not None


def load_demo_data():
    if is_demo_loaded():
        return False

    with db_conn() as conn:
        # Insert suppliers
        supplier_ids = []
        for sup in SUPPLIERS:
            cur = conn.execute(
                """INSERT INTO suppliers (name, contact_name, email, phone, payment_terms, address, category, notes)
                   VALUES (:name, :contact_name, :email, :phone, :payment_terms, :address, :category, :notes)""",
                sup,
            )
            supplier_ids.append(cur.lastrowid)

        po_id_map = {}

        for (sup_idx, po_num, status, exp_delta, act_delta, category, items, notes) in PO_DATA:
            sup_id = supplier_ids[sup_idx]

            if po_num in OVERDUE_OVERRIDES:
                exp_delta = OVERDUE_OVERRIDES[po_num]

            expected = _d(exp_delta)
            actual = _d(act_delta) if act_delta is not None else None

            total = sum(qty * price for (_, qty, price) in items)

            # Spread created_at over past 3 months
            created_offset = max(exp_delta - 14, exp_delta - 20)
            created_at = _d(created_offset)

            cur = conn.execute(
                """INSERT INTO purchase_orders
                   (po_number, supplier_id, status, expected_delivery, actual_delivery,
                    category, total_value, notes, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (po_num, sup_id, status, expected, actual, category, total, notes,
                 created_at, created_at),
            )
            po_id = cur.lastrowid
            po_id_map[po_num] = po_id

            for (desc, qty, price) in items:
                conn.execute(
                    "INSERT INTO po_items (po_id, description, quantity, unit_price, total_price) VALUES (?,?,?,?,?)",
                    (po_id, desc, qty, price, qty * price),
                )

        # Price deviations
        for (po_num, sup_idx, item_desc, approved, invoice) in PRICE_DEVIATIONS:
            sup_id = supplier_ids[sup_idx]
            po_id = po_id_map.get(po_num)
            deviation = round((invoice - approved) / approved * 100, 2)
            status = "yellow" if abs(deviation) < 10 else "red"
            conn.execute(
                """INSERT INTO price_records
                   (po_id, supplier_id, item_description, approved_price, invoice_price, deviation_pct, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (po_id, sup_id, item_desc, approved, invoice, deviation, status),
            )

        # Mark demo as loaded
        conn.execute("INSERT OR IGNORE INTO demo_loaded (id) VALUES (1)")

    return True
