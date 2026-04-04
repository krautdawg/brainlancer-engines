import os
import json
from datetime import date, datetime
from pathlib import Path

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import uvicorn

from db import get_db, init_db
from checklist_engine import generate_tasks, get_available_templates
from notification import (
    create_notification, get_notifications,
    mark_all_read, mark_read, get_unread_count,
)
from demo_data import init_demo

APP_PASSWORD = os.getenv("APP_PASSWORD", "brainlancer2026")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-engine4")

app = FastAPI(title="Engine 4: Onboarding Engine")

# ── Auth helpers ──────────────────────────────────────────────────────────────
SESSION_COOKIE = "onboarding_session"

def create_session_token():
    from itsdangerous import URLSafeTimedSerializer
    s = URLSafeTimedSerializer(SECRET_KEY)
    return s.dumps("authenticated")

def verify_session(request: Request) -> bool:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return False
    try:
        from itsdangerous import URLSafeTimedSerializer
        s = URLSafeTimedSerializer(SECRET_KEY)
        s.loads(token, max_age=86400 * 7)
        return True
    except Exception:
        return False

def require_auth(request: Request):
    if not verify_session(request):
        raise HTTPException(status_code=401, detail="Not authenticated")

# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    init_db()

# ── Serve frontend ────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    html_path = Path("templates/index.html")
    return HTMLResponse(html_path.read_text())

# ── Auth routes ───────────────────────────────────────────────────────────────
class LoginBody(BaseModel):
    password: str

@app.post("/api/login")
def login(body: LoginBody, response: Response):
    if body.password != APP_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")
    token = create_session_token()
    response.set_cookie(
        SESSION_COOKIE, token,
        httponly=True, samesite="lax", max_age=86400 * 7,
    )
    return {"success": True}

@app.get("/api/me")
def me(request: Request):
    return {"authenticated": verify_session(request)}

@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)
    return {"success": True}

# ── Overdue detection helper ──────────────────────────────────────────────────
def sync_overdue(employee_id: int = None):
    today = date.today().isoformat()
    conn = get_db()
    if employee_id:
        rows = conn.execute(
            "SELECT id, title, employee_id FROM tasks WHERE status = 'todo' AND due_date < ? AND employee_id = ?",
            (today, employee_id),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, title, employee_id FROM tasks WHERE status = 'todo' AND due_date < ?",
            (today,),
        ).fetchall()
    for row in rows:
        conn.execute("UPDATE tasks SET status = 'overdue' WHERE id = ?", (row["id"],))
        emp = conn.execute("SELECT name FROM employees WHERE id = ?", (row["employee_id"],)).fetchone()
        emp_name = emp["name"] if emp else "Unknown"
        # Create notification only if not already created
        existing = conn.execute(
            "SELECT id FROM notifications WHERE task_id = ? AND type = 'warning'", (row["id"],)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO notifications (message, employee_id, task_id, type) VALUES (?, ?, ?, 'warning')",
                (f"Overdue: '{row['title']}' for {emp_name}", row["employee_id"], row["id"]),
            )
    conn.commit()
    conn.close()

# ── Employee routes ───────────────────────────────────────────────────────────
@app.get("/api/employees")
def list_employees(request: Request):
    require_auth(request)
    sync_overdue()
    conn = get_db()
    employees = conn.execute(
        "SELECT * FROM employees WHERE status != 'deleted' ORDER BY created_at DESC"
    ).fetchall()
    result = []
    for emp in employees:
        emp_dict = dict(emp)
        total = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE employee_id = ?", (emp["id"],)
        ).fetchone()[0]
        done = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE employee_id = ? AND status = 'done'", (emp["id"],)
        ).fetchone()[0]
        overdue = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE employee_id = ? AND status = 'overdue'", (emp["id"],)
        ).fetchone()[0]
        emp_dict["total_tasks"] = total
        emp_dict["done_tasks"] = done
        emp_dict["overdue_count"] = overdue
        emp_dict["progress"] = round((done / total * 100) if total > 0 else 0)
        result.append(emp_dict)
    conn.close()
    return result

class NewEmployee(BaseModel):
    name: str
    email: str
    role: str
    department: Optional[str] = ""
    manager_name: Optional[str] = ""
    manager_email: Optional[str] = ""
    office_location: Optional[str] = ""
    start_date: str
    type: Optional[str] = "onboarding"
    template: Optional[str] = "developer"

@app.post("/api/employees")
def create_employee(body: NewEmployee, request: Request):
    require_auth(request)
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO employees (name, email, role, department, manager_name, manager_email,
            office_location, start_date, type, status, template)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
    """, (body.name, body.email, body.role, body.department, body.manager_name,
          body.manager_email, body.office_location, body.start_date, body.type, body.template))
    emp_id = cur.lastrowid
    conn.commit()
    conn.close()

    start = date.fromisoformat(body.start_date)
    tasks = generate_tasks(body.template, start, emp_id)
    conn = get_db()
    for t in tasks:
        conn.execute("""
            INSERT INTO tasks (employee_id, title, description, assignee, category, due_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (t["employee_id"], t["title"], t["description"],
              t["assignee"], t["category"], t["due_date"], t["status"]))
    conn.commit()
    conn.close()

    sync_overdue(emp_id)

    conn = get_db()
    conn.execute("""
        INSERT INTO activity_log (employee_id, employee_name, action, details)
        VALUES (?, ?, 'Onboarding started', ?)
    """, (emp_id, body.name, f"{body.type.title()} initiated — template: {body.template}"))
    conn.commit()
    conn.close()

    create_notification(
        f"New {'onboarding' if body.type == 'onboarding' else 'offboarding'} started for {body.name}",
        emp_id, None, "info",
    )

    return {"employee_id": emp_id, "task_count": len(tasks)}

@app.get("/api/employees/{emp_id}")
def get_employee(emp_id: int, request: Request):
    require_auth(request)
    conn = get_db()
    emp = conn.execute("SELECT * FROM employees WHERE id = ?", (emp_id,)).fetchone()
    conn.close()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return dict(emp)

@app.delete("/api/employees/{emp_id}")
def delete_employee(emp_id: int, request: Request):
    require_auth(request)
    conn = get_db()
    conn.execute("UPDATE employees SET status = 'deleted' WHERE id = ?", (emp_id,))
    conn.commit()
    conn.close()
    return {"success": True}

# ── Task routes ───────────────────────────────────────────────────────────────
@app.get("/api/employees/{emp_id}/tasks")
def get_tasks(emp_id: int, request: Request):
    require_auth(request)
    sync_overdue(emp_id)
    conn = get_db()
    tasks = conn.execute(
        "SELECT * FROM tasks WHERE employee_id = ? ORDER BY due_date, id", (emp_id,)
    ).fetchall()
    conn.close()
    return [dict(t) for t in tasks]

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    assignee: Optional[str] = None

@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, body: TaskUpdate, request: Request):
    require_auth(request)
    conn = get_db()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_status = task["status"]
    updates = {}
    if body.status is not None:
        updates["status"] = body.status
    if body.notes is not None:
        updates["notes"] = body.notes
    if body.assignee is not None:
        updates["assignee"] = body.assignee

    if "status" in updates and updates["status"] == "done" and old_status != "done":
        updates["completed_at"] = datetime.now().isoformat()
    elif "status" in updates and updates["status"] != "done":
        updates["completed_at"] = None

    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [task_id]
        conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)

        emp = conn.execute("SELECT * FROM employees WHERE id = ?", (task["employee_id"],)).fetchone()
        emp_name = emp["name"] if emp else "Unknown"

        if "status" in updates:
            conn.execute("""
                INSERT INTO activity_log (employee_id, employee_name, task_id, task_title, action, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (task["employee_id"], emp_name, task_id, task["title"],
                  f"Status changed to {updates['status']}",
                  f"{old_status} → {updates['status']}"))

            if updates["status"] == "done":
                create_notification(
                    f"Task completed: '{task['title']}' for {emp_name}",
                    task["employee_id"], task_id, "success",
                )

    conn.commit()
    updated = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(updated)

# ── Notifications routes ──────────────────────────────────────────────────────
@app.get("/api/notifications")
def list_notifications(request: Request):
    require_auth(request)
    notifs = get_notifications(50)
    return {"notifications": notifs, "unread_count": sum(1 for n in notifs if not n["read"])}

@app.put("/api/notifications/read-all")
def read_all_notifications(request: Request):
    require_auth(request)
    mark_all_read()
    return {"success": True}

@app.put("/api/notifications/{notif_id}/read")
def read_notification(notif_id: int, request: Request):
    require_auth(request)
    mark_read(notif_id)
    return {"success": True}

# ── Dashboard route ───────────────────────────────────────────────────────────
@app.get("/api/dashboard")
def dashboard(request: Request):
    require_auth(request)
    sync_overdue()
    conn = get_db()
    employees = conn.execute(
        "SELECT * FROM employees WHERE status != 'deleted' ORDER BY created_at DESC"
    ).fetchall()
    emp_list = []
    for emp in employees:
        total = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE employee_id = ?", (emp["id"],)
        ).fetchone()[0]
        done = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE employee_id = ? AND status = 'done'", (emp["id"],)
        ).fetchone()[0]
        overdue = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE employee_id = ? AND status = 'overdue'", (emp["id"],)
        ).fetchone()[0]
        in_progress = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE employee_id = ? AND status = 'in_progress'", (emp["id"],)
        ).fetchone()[0]
        emp_dict = dict(emp)
        emp_dict["total_tasks"] = total
        emp_dict["done_tasks"] = done
        emp_dict["overdue_count"] = overdue
        emp_dict["in_progress_count"] = in_progress
        emp_dict["progress"] = round((done / total * 100) if total > 0 else 0)
        emp_list.append(emp_dict)

    activity = conn.execute(
        "SELECT * FROM activity_log ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return {
        "employees": emp_list,
        "activity": [dict(a) for a in activity],
        "total_employees": len(emp_list),
        "total_overdue": sum(e["overdue_count"] for e in emp_list),
    }

# ── Activity route ────────────────────────────────────────────────────────────
@app.get("/api/activity")
def get_activity(request: Request, limit: int = 20):
    require_auth(request)
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM activity_log ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Demo route ────────────────────────────────────────────────────────────────
@app.post("/api/demo/init")
def demo_init(request: Request):
    require_auth(request)
    return init_demo()

# ── Templates list ────────────────────────────────────────────────────────────
@app.get("/api/templates")
def templates(request: Request):
    require_auth(request)
    return get_available_templates()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=3004, reload=True)
