from db import db_conn
from typing import List, Dict, Optional


# ── Campaigns ──────────────────────────────────────────────────────────────────

def create_campaign(
    name: str,
    sender_name: str,
    sender_email: str,
    num_touchpoints: int = 4,
    cadence: str = "1,3,7,14",
    tone: str = "formal",
    goal: str = "meeting",
    is_demo: bool = False,
) -> int:
    with db_conn() as conn:
        cursor = conn.execute(
            """INSERT INTO campaigns
               (name, sender_name, sender_email, num_touchpoints, cadence, tone, goal, is_demo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, sender_name, sender_email, num_touchpoints, cadence, tone, goal, 1 if is_demo else 0),
        )
        return cursor.lastrowid


def get_campaign(campaign_id: int) -> Optional[Dict]:
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
        return dict(row) if row else None


def list_campaigns() -> List[Dict]:
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM campaigns ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


def update_campaign_status(campaign_id: int, status: str) -> None:
    with db_conn() as conn:
        conn.execute("UPDATE campaigns SET status = ? WHERE id = ?", (status, campaign_id))


def delete_campaign(campaign_id: int) -> None:
    with db_conn() as conn:
        conn.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))


# ── Leads ───────────────────────────────────────────────────────────────────────

def add_lead(
    campaign_id: int,
    email: str,
    company: str = "",
    contact: str = "",
    website: str = "",
    notes: str = "",
    status: str = "draft",
) -> int:
    with db_conn() as conn:
        cursor = conn.execute(
            """INSERT INTO leads (campaign_id, email, company, contact, website, notes, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (campaign_id, email, company, contact, website, notes, status),
        )
        return cursor.lastrowid


def get_leads(campaign_id: int) -> List[Dict]:
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM leads WHERE campaign_id = ? ORDER BY id",
            (campaign_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def update_lead_status(lead_id: int, status: str) -> None:
    with db_conn() as conn:
        conn.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))


# ── Sequences ───────────────────────────────────────────────────────────────────

def save_sequence(
    lead_id: int,
    touchpoint_num: int,
    subject: str,
    body: str,
    scheduled_day: int,
) -> int:
    with db_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM email_sequences WHERE lead_id = ? AND touchpoint_num = ?",
            (lead_id, touchpoint_num),
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE email_sequences SET subject = ?, body = ?, scheduled_day = ? WHERE id = ?",
                (subject, body, scheduled_day, existing["id"]),
            )
            return existing["id"]
        else:
            cursor = conn.execute(
                """INSERT INTO email_sequences (lead_id, touchpoint_num, subject, body, scheduled_day)
                   VALUES (?, ?, ?, ?, ?)""",
                (lead_id, touchpoint_num, subject, body, scheduled_day),
            )
            return cursor.lastrowid


def update_sequence(sequence_id: int, subject: str, body: str) -> None:
    with db_conn() as conn:
        conn.execute(
            "UPDATE email_sequences SET subject = ?, body = ? WHERE id = ?",
            (subject, body, sequence_id),
        )


def get_sequence(sequence_id: int) -> Optional[Dict]:
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM email_sequences WHERE id = ?", (sequence_id,)).fetchone()
        return dict(row) if row else None


def get_sequences_for_lead(lead_id: int) -> List[Dict]:
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM email_sequences WHERE lead_id = ? ORDER BY touchpoint_num",
            (lead_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_campaign_sequences(campaign_id: int) -> List[Dict]:
    """Return all leads with their sequences for the given campaign."""
    leads = get_leads(campaign_id)
    result = []
    for lead in leads:
        seqs = get_sequences_for_lead(lead["id"])
        result.append({**lead, "sequences": seqs})
    return result


# ── Stats ───────────────────────────────────────────────────────────────────────

def get_campaign_stats(campaign_id: int) -> Dict:
    with db_conn() as conn:
        total = conn.execute(
            "SELECT COUNT(*) as c FROM leads WHERE campaign_id = ?", (campaign_id,)
        ).fetchone()["c"]

        status_rows = conn.execute(
            "SELECT status, COUNT(*) as c FROM leads WHERE campaign_id = ? GROUP BY status",
            (campaign_id,),
        ).fetchall()
        status_counts = {r["status"]: r["c"] for r in status_rows}

        seq_count = conn.execute(
            """SELECT COUNT(*) as c FROM email_sequences es
               JOIN leads l ON es.lead_id = l.id
               WHERE l.campaign_id = ?""",
            (campaign_id,),
        ).fetchone()["c"]

    return {
        "total_leads": total,
        "status_counts": status_counts,
        "sequences_count": seq_count,
    }
