import os
import secrets
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from db import init_db
from demo_data import load_demo_data
import supplier_manager as sm
import po_tracker as pt
import price_monitor as pm
import chase_engine as ce
import spend_reporter as sr

APP_PASSWORD = os.environ.get("APP_PASSWORD", "brainlancer2026")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Engine 5 – Supplier & PO Monitor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_HTML_PATH = os.path.join(os.path.dirname(__file__), "templates", "index.html")

# ---------- Auth ----------

SESSIONS: set = set()


def require_auth(request: Request):
    token = request.cookies.get("session")
    if not token or token not in SESSIONS:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token


class LoginRequest(BaseModel):
    password: str


@app.post("/api/auth/login")
def login(body: LoginRequest, response: Response):
    if body.password != APP_PASSWORD:
        raise HTTPException(status_code=401, detail="Wrong password")
    token = secrets.token_hex(32)
    SESSIONS.add(token)
    response.set_cookie("session", token, httponly=True, samesite="lax")
    return {"ok": True}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get("session")
    SESSIONS.discard(token)
    response.delete_cookie("session")
    return {"ok": True}


@app.get("/api/auth/status")
def auth_status(request: Request):
    token = request.cookies.get("session")
    return {"authenticated": token in SESSIONS if token else False}


# ---------- Frontend ----------

@app.get("/", response_class=HTMLResponse)
def index():
    with open(_HTML_PATH, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


# ---------- Demo ----------

@app.post("/api/demo/load")
def demo_load(_: str = Depends(require_auth)):
    loaded = load_demo_data()
    return {"loaded": loaded, "message": "Demo-Daten geladen" if loaded else "Demo-Daten bereits vorhanden"}


# ---------- Suppliers ----------

@app.get("/api/suppliers")
def list_suppliers(_: str = Depends(require_auth)):
    return sm.get_all_suppliers()


@app.get("/api/suppliers/{supplier_id}")
def get_supplier(supplier_id: int, _: str = Depends(require_auth)):
    s = sm.get_supplier(supplier_id)
    if not s:
        raise HTTPException(404, "Lieferant nicht gefunden")
    s["scorecard"] = sm.get_supplier_scorecard(supplier_id)
    s["orders"] = sm.get_supplier_orders(supplier_id)
    return s


@app.post("/api/suppliers")
def create_supplier(data: dict, _: str = Depends(require_auth)):
    sid = sm.create_supplier(data)
    return {"id": sid}


@app.put("/api/suppliers/{supplier_id}")
def update_supplier(supplier_id: int, data: dict, _: str = Depends(require_auth)):
    sm.update_supplier(supplier_id, data)
    return {"ok": True}


@app.delete("/api/suppliers/{supplier_id}")
def delete_supplier(supplier_id: int, _: str = Depends(require_auth)):
    sm.delete_supplier(supplier_id)
    return {"ok": True}


# ---------- Purchase Orders ----------

@app.get("/api/pos")
def list_pos(status: Optional[str] = None, supplier_id: Optional[int] = None,
             _: str = Depends(require_auth)):
    return pt.get_all_pos(status=status, supplier_id=supplier_id)


@app.get("/api/pos/overdue")
def overdue_pos(_: str = Depends(require_auth)):
    return pt.get_overdue_pos()


@app.get("/api/pos/{po_id}")
def get_po(po_id: int, _: str = Depends(require_auth)):
    po = pt.get_po(po_id)
    if not po:
        raise HTTPException(404, "Bestellung nicht gefunden")
    return po


@app.post("/api/pos")
def create_po(data: dict, _: str = Depends(require_auth)):
    po_id = pt.create_po(data)
    return {"id": po_id}


@app.put("/api/pos/{po_id}/status")
def update_po_status(po_id: int, data: dict, _: str = Depends(require_auth)):
    pt.update_po_status(po_id, data["status"])
    return {"ok": True}


@app.put("/api/pos/{po_id}")
def update_po(po_id: int, data: dict, _: str = Depends(require_auth)):
    pt.update_po(po_id, data)
    return {"ok": True}


@app.delete("/api/pos/{po_id}")
def delete_po(po_id: int, _: str = Depends(require_auth)):
    pt.delete_po(po_id)
    return {"ok": True}


@app.post("/api/pos/upload-csv")
async def upload_csv(file: UploadFile = File(...), _: str = Depends(require_auth)):
    content = await file.read()
    parsed = pt.parse_csv_upload(content)
    created = []
    errors = []
    for po_data in parsed:
        try:
            supplier_name = po_data.pop("supplier_name", "")
            with __import__("db").db_conn() as conn:
                row = conn.execute(
                    "SELECT id FROM suppliers WHERE name = ? LIMIT 1", (supplier_name,)
                ).fetchone()
                if row:
                    po_data["supplier_id"] = row["id"]
                else:
                    cur = conn.execute(
                        "INSERT INTO suppliers (name) VALUES (?)", (supplier_name,)
                    )
                    po_data["supplier_id"] = cur.lastrowid
            po_id = pt.create_po(po_data)
            created.append(po_id)
        except Exception as e:
            errors.append({"po_number": po_data.get("po_number", "?"), "error": str(e)})
    return {"created": len(created), "errors": errors}


# ---------- Price Monitor ----------

@app.get("/api/price-deviations")
def list_deviations(_: str = Depends(require_auth)):
    return pm.get_all_deviations()


@app.post("/api/price-deviations")
def add_deviation(data: dict, _: str = Depends(require_auth)):
    rid = pm.add_price_record(data)
    return {"id": rid}


@app.delete("/api/price-deviations/{record_id}")
def delete_deviation(record_id: int, _: str = Depends(require_auth)):
    pm.delete_price_record(record_id)
    return {"ok": True}


# ---------- Chase Emails ----------

@app.get("/api/chase-emails")
def list_chase_emails(_: str = Depends(require_auth)):
    return ce.get_all_chase_emails()


@app.post("/api/chase-emails/generate/{po_id}")
def generate_chase(po_id: int, data: dict = None, _: str = Depends(require_auth)):
    level = (data or {}).get("level")
    email = ce.generate_chase_email(po_id, level=level)
    return email


@app.post("/api/chase-emails/{email_id}/approve")
def approve_chase(email_id: int, _: str = Depends(require_auth)):
    ce.approve_chase_email(email_id)
    return {"ok": True}


@app.delete("/api/chase-emails/{email_id}")
def delete_chase(email_id: int, _: str = Depends(require_auth)):
    ce.delete_chase_email(email_id)
    return {"ok": True}


# ---------- Spend / Analytics ----------

@app.get("/api/spend/summary")
def spend_summary(_: str = Depends(require_auth)):
    return sr.get_summary()


@app.get("/api/spend/by-supplier")
def spend_by_supplier(_: str = Depends(require_auth)):
    return sr.get_spend_by_supplier()


@app.get("/api/spend/by-category")
def spend_by_category(_: str = Depends(require_auth)):
    return sr.get_spend_by_category()


@app.get("/api/spend/trend")
def spend_trend(_: str = Depends(require_auth)):
    return sr.get_spend_trend()


@app.get("/api/spend/anomalies")
def spend_anomalies(_: str = Depends(require_auth)):
    return sr.get_top_anomalies()


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=3005, reload=False)
