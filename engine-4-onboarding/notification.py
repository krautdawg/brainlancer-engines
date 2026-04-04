from db import get_db

def create_notification(message: str, employee_id: int = None, task_id: int = None, notif_type: str = "info"):
    conn = get_db()
    conn.execute(
        "INSERT INTO notifications (message, employee_id, task_id, type) VALUES (?, ?, ?, ?)",
        (message, employee_id, task_id, notif_type),
    )
    conn.commit()
    conn.close()

def get_notifications(limit: int = 50) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_all_read():
    conn = get_db()
    conn.execute("UPDATE notifications SET read = 1 WHERE read = 0")
    conn.commit()
    conn.close()

def mark_read(notif_id: int):
    conn = get_db()
    conn.execute("UPDATE notifications SET read = 1 WHERE id = ?", (notif_id,))
    conn.commit()
    conn.close()

def get_unread_count() -> int:
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM notifications WHERE read = 0").fetchone()[0]
    conn.close()
    return count
