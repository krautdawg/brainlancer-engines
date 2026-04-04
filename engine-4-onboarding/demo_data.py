from datetime import date, timedelta, datetime
from db import get_db
from checklist_engine import generate_tasks
from notification import create_notification

TODAY = date(2026, 4, 4)

def is_demo_loaded() -> bool:
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM employees WHERE name = 'Sarah Chen'").fetchone()[0]
    conn.close()
    return count > 0

def create_employee_record(data: dict) -> int:
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO employees (name, email, role, department, manager_name, manager_email,
            office_location, start_date, type, status, template)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
    """, (
        data["name"], data["email"], data["role"], data["department"],
        data["manager_name"], data["manager_email"], data["office_location"],
        data["start_date"], data["type"], data["template"],
    ))
    emp_id = cur.lastrowid
    conn.commit()
    conn.close()
    return emp_id

def bulk_insert_tasks(tasks: list[dict]):
    conn = get_db()
    for t in tasks:
        conn.execute("""
            INSERT INTO tasks (employee_id, title, description, assignee, category, due_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (t["employee_id"], t["title"], t["description"],
              t["assignee"], t["category"], t["due_date"], t["status"]))
    conn.commit()
    conn.close()

def update_task_status(employee_id: int, task_index_zero_based: int, status: str, notes: str = ""):
    conn = get_db()
    tasks = conn.execute(
        "SELECT id FROM tasks WHERE employee_id = ? ORDER BY id", (employee_id,)
    ).fetchall()
    if task_index_zero_based < len(tasks):
        task_id = tasks[task_index_zero_based]["id"]
        completed_at = datetime.now().isoformat() if status == "done" else None
        conn.execute(
            "UPDATE tasks SET status = ?, notes = ?, completed_at = ? WHERE id = ?",
            (status, notes, completed_at, task_id),
        )
    conn.commit()
    conn.close()

def log_activity(employee_id: int, employee_name: str, action: str, details: str = ""):
    conn = get_db()
    conn.execute("""
        INSERT INTO activity_log (employee_id, employee_name, action, details)
        VALUES (?, ?, ?, ?)
    """, (employee_id, employee_name, action, details))
    conn.commit()
    conn.close()

def init_demo():
    if is_demo_loaded():
        return {"message": "Demo data already loaded"}

    # --- Sarah Chen: Developer, Day 3 (started 2026-04-01), 60% complete, 2 overdue ---
    sarah_start = date(2026, 4, 1)
    sarah_id = create_employee_record({
        "name": "Sarah Chen", "email": "sarah.chen@acme.com",
        "role": "Developer", "department": "Engineering",
        "manager_name": "Alex Kim", "manager_email": "alex.kim@acme.com",
        "office_location": "Berlin HQ", "start_date": sarah_start.isoformat(),
        "type": "onboarding", "template": "developer",
    })
    sarah_tasks = generate_tasks("developer", sarah_start, sarah_id)
    bulk_insert_tasks(sarah_tasks)

    # 30 tasks: indices 0-29
    # Pre-boarding (0-9): all DONE
    for i in range(10):
        update_task_status(sarah_id, i, "done")
    # Day 1 tasks (10-16 = 7 tasks):
    # indices 10,11,12,13,14 DONE; 15,16 OVERDUE
    for i in range(10, 15):
        update_task_status(sarah_id, i, "done")
    update_task_status(sarah_id, 15, "overdue", "Waiting for IT availability")
    update_task_status(sarah_id, 16, "overdue", "Manager travel delayed meeting")
    # Week 1 (17-24): 17 DONE, 18 DONE, 19 IN_PROGRESS, rest TODO
    update_task_status(sarah_id, 17, "done")
    update_task_status(sarah_id, 18, "done")
    update_task_status(sarah_id, 19, "in_progress", "Currently working through modules")
    # 20-29: todo (default)

    log_activity(sarah_id, "Sarah Chen", "Onboarding started", "Developer onboarding — Day 3")
    log_activity(sarah_id, "Sarah Chen", "Task completed", "Pre-boarding checklist finished")
    create_notification(
        "2 overdue tasks for Sarah Chen require attention",
        sarah_id, None, "warning"
    )

    # --- Max Rodriguez: Designer, Day 1 (started 2026-04-04), ~17% complete, on track ---
    max_start = date(2026, 4, 4)
    max_id = create_employee_record({
        "name": "Max Rodriguez", "email": "max.rodriguez@acme.com",
        "role": "Designer", "department": "Product Design",
        "manager_name": "Sophie Müller", "manager_email": "sophie.mueller@acme.com",
        "office_location": "Berlin HQ", "start_date": max_start.isoformat(),
        "type": "onboarding", "template": "designer",
    })
    max_tasks = generate_tasks("designer", max_start, max_id)
    bulk_insert_tasks(max_tasks)

    # Pre-boarding (0-9): 5 done, 4 in_progress (tasks with past due dates being set up)
    # Mark done: offer letter(0), payroll(1), MacBook order(3), email(4), Slack(7)
    for i in [0, 1, 3, 4, 7]:
        update_task_status(max_id, i, "done")
    # Mark in_progress: insurance(2), Figma(5), Adobe CC(6), Notion(8)
    for i in [2, 5, 6, 8]:
        update_task_status(max_id, i, "in_progress")
    # welcome email(9): done
    update_task_status(max_id, 9, "done")
    # Day 1: office tour(10) in_progress
    update_task_status(max_id, 10, "in_progress")
    # rest todo (default)

    log_activity(max_id, "Max Rodriguez", "Onboarding started", "Designer onboarding — Day 1")
    create_notification(
        "Max Rodriguez has started onboarding today — Day 1",
        max_id, None, "info"
    )

    # --- Lisa Wagner: Offboarding, 80% complete (last day 2026-04-15) ---
    lisa_last_day = date(2026, 4, 15)
    lisa_id = create_employee_record({
        "name": "Lisa Wagner", "email": "lisa.wagner@acme.com",
        "role": "Senior Designer", "department": "Product Design",
        "manager_name": "Sophie Müller", "manager_email": "sophie.mueller@acme.com",
        "office_location": "Berlin HQ", "start_date": lisa_last_day.isoformat(),
        "type": "offboarding", "template": "offboarding",
    })
    lisa_tasks = generate_tasks("offboarding", lisa_last_day, lisa_id)
    bulk_insert_tasks(lisa_tasks)

    # 25 tasks: mark first 20 as done (80%)
    for i in range(20):
        update_task_status(lisa_id, i, "done")
    # tasks 20-24: todo

    log_activity(lisa_id, "Lisa Wagner", "Offboarding initiated", "Last day: 15 April 2026")
    log_activity(lisa_id, "Lisa Wagner", "Knowledge transfer", "Documentation 80% complete")
    create_notification(
        "Lisa Wagner offboarding 80% complete — 5 tasks remaining",
        lisa_id, None, "info"
    )

    return {"message": "Demo data loaded", "employees": 3}
