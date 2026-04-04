from datetime import date
from db import db_conn
from po_tracker import get_po

TEMPLATES = {
    1: {
        "subject": "Erinnerung: Lieferung ausstehend – Bestellung {po_number}",
        "body": """Sehr geehrte/r {contact_name},

ich hoffe, diese Nachricht erreicht Sie gut. Ich möchte Sie freundlich an die
noch ausstehende Lieferung unserer Bestellung {po_number} erinnern.

Bestelldetails:
- Bestellnummer: {po_number}
- Ursprüngliches Lieferdatum: {expected_delivery}
- Tage überfällig: {days_overdue}
- Bestellwert: {total_value} €

Könnten Sie uns bitte den aktuellen Status der Lieferung mitteilen und ein
voraussichtliches Lieferdatum bestätigen?

Für Rückfragen stehe ich gerne zur Verfügung.

Mit freundlichen Grüßen
Einkaufsabteilung
""",
    },
    2: {
        "subject": "DRINGEND: Ausstehende Lieferung – Bestellung {po_number} ({days_overdue} Tage überfällig)",
        "body": """Sehr geehrte/r {contact_name},

ich beziehe mich auf meine vorherige Nachricht bezüglich Bestellung {po_number},
auf die wir bislang keine Antwort erhalten haben.

Die Lieferung ist nun {days_overdue} Tage überfällig und verursacht bei uns
erhebliche betriebliche Schwierigkeiten.

Bestelldetails:
- Bestellnummer: {po_number}
- Ursprüngliches Lieferdatum: {expected_delivery}
- Tage überfällig: {days_overdue}
- Bestellwert: {total_value} €
- Bestellte Artikel: {items_summary}

Wir fordern Sie dringend auf, innerhalb von 24 Stunden zu antworten und entweder:
1. Ein verbindliches neues Lieferdatum zu bestätigen, oder
2. Den Grund für die Verzögerung zu erläutern

Sollten wir keine Rückmeldung erhalten, sehen wir uns gezwungen, weitere
Maßnahmen zu ergreifen.

Mit freundlichen Grüßen
Einkaufsleitung
""",
    },
    3: {
        "subject": "ESKALATION: Nicht erfüllte Lieferverpflichtung – Bestellung {po_number}",
        "body": """Sehr geehrte Geschäftsleitung,

trotz mehrfacher Nachfragen wurde unsere Bestellung {po_number} bislang nicht
geliefert. Die Verzögerung beträgt nunmehr {days_overdue} Tage.

Dies ist eine formelle Eskalationsbenachrichtigung.

Bestelldetails:
- Bestellnummer: {po_number}
- Ursprüngliches Lieferdatum: {expected_delivery}
- Tage überfällig: {days_overdue}
- Bestellwert: {total_value} €
- Artikel: {items_summary}

Wir machen Sie darauf aufmerksam, dass Sie Ihre vertraglichen Verpflichtungen
nicht erfüllt haben. Wir fordern innerhalb von 48 Stunden:

1. Sofortige Lieferung der bestellten Waren, ODER
2. Vollständige Rückerstattung und schriftliche Erklärung

Andernfalls behalten wir uns vor, die Bestellung zu stornieren und einen
alternativen Lieferanten zu beauftragen, sowie etwaige Mehrkosten in Rechnung
zu stellen.

Hochachtungsvoll
Geschäftsführung / Einkaufsleitung
""",
    },
}


def generate_chase_email(po_id: int, level: int = None):
    po = get_po(po_id)
    if not po:
        raise ValueError(f"PO {po_id} not found")

    with db_conn() as conn:
        existing = conn.execute(
            "SELECT level FROM chase_emails WHERE po_id = ? ORDER BY level DESC LIMIT 1",
            (po_id,)
        ).fetchone()

    if level is None:
        level = (existing["level"] + 1) if existing else 1
    level = min(max(level, 1), 3)

    expected = po.get("expected_delivery", "Unbekannt")
    days_overdue = 0
    if expected and expected != "Unbekannt":
        try:
            delta = date.today() - date.fromisoformat(expected)
            days_overdue = max(delta.days, 0)
        except ValueError:
            pass

    items_summary = ", ".join(
        f"{i['description']} (x{int(i['quantity'])})"
        for i in (po.get("items") or [])
    ) or "Siehe Bestelldetails"

    total_value = f"{po.get('total_value', 0):,.2f}"

    ctx = {
        "po_number": po["po_number"],
        "contact_name": po.get("supplier_contact") or po.get("supplier_name", "Lieferant"),
        "supplier_name": po.get("supplier_name", ""),
        "expected_delivery": expected,
        "days_overdue": days_overdue,
        "total_value": total_value,
        "items_summary": items_summary,
        "today": date.today().isoformat(),
    }

    tmpl = TEMPLATES[level]
    subject = tmpl["subject"].format(**ctx)
    body = tmpl["body"].format(**ctx)

    with db_conn() as conn:
        cur = conn.execute(
            """INSERT INTO chase_emails (po_id, level, subject, body)
               VALUES (?, ?, ?, ?)""",
            (po_id, level, subject, body)
        )
        email_id = cur.lastrowid

    return {
        "id": email_id,
        "po_id": po_id,
        "po_number": po["po_number"],
        "supplier_name": po.get("supplier_name", ""),
        "supplier_email": po.get("supplier_email", ""),
        "level": level,
        "subject": subject,
        "body": body,
        "days_overdue": days_overdue,
    }


def get_all_chase_emails():
    with db_conn() as conn:
        rows = conn.execute("""
            SELECT ce.*, po.po_number, po.expected_delivery, po.total_value,
                   s.name AS supplier_name, s.email AS supplier_email
            FROM chase_emails ce
            JOIN purchase_orders po ON po.id = ce.po_id
            JOIN suppliers s ON s.id = po.supplier_id
            ORDER BY ce.generated_at DESC
        """).fetchall()
        return [dict(r) for r in rows]


def approve_chase_email(email_id: int):
    with db_conn() as conn:
        conn.execute("UPDATE chase_emails SET approved = 1 WHERE id = ?", (email_id,))


def delete_chase_email(email_id: int):
    with db_conn() as conn:
        conn.execute("DELETE FROM chase_emails WHERE id = ?", (email_id,))
