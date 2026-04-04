"""Engine 3: Invoice & VAT Intelligence — FastAPI application."""

import os
import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from dotenv import load_dotenv

load_dotenv()

# Internal modules
import db
from demo_data import load_demo_data, get_demo_stats
from triage_engine import batch_triage
from ai_reviewer import review_invoices_with_ai, apply_ai_review_results
from elster_calculator import (
    calculate_elster, format_elster_summary, generate_elster_xml
)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
APP_PASSWORD = os.environ.get("APP_PASSWORD", "brainlancer2026")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
SESSION_TTL_HOURS = 24
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
DEMO_QUARTER = int(os.environ.get("DEMO_QUARTER", "1"))
DEMO_YEAR = int(os.environ.get("DEMO_YEAR", "2024"))

# In-memory session store: {token: expires_at}
_sessions: dict[str, datetime] = {}

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="Engine 3: VAT Intelligence", version="1.0.0")
templates = Jinja2Templates(directory="templates")

db.init_db()


# ── Auth helpers ─────────────────────────────────────────────────────────────

def get_session_token(request: Request) -> Optional[str]:
    return request.cookies.get("vat_session")


def is_authenticated(request: Request) -> bool:
    token = get_session_token(request)
    if not token or token not in _sessions:
        return False
    if datetime.utcnow() > _sessions[token]:
        del _sessions[token]
        return False
    return True


def require_auth(request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")


# ── Pydantic models ───────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    password: str


class StatusUpdateRequest(BaseModel):
    status: str  # ok | corrected | deleted | to_review
    correction_category: Optional[str] = None
    correction_reason: Optional[str] = None
    correction_percentage: Optional[float] = None


class ScanRequest(BaseModel):
    imap_host: Optional[str] = None
    imap_port: Optional[int] = 993
    imap_user: Optional[str] = None
    imap_password: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    quarter: Optional[int] = 1
    year: Optional[int] = 2024


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Auth

@app.post("/api/auth/login")
async def login(body: LoginRequest, response: Response):
    if body.password != APP_PASSWORD:
        raise HTTPException(status_code=401, detail="Falsches Passwort")
    token = str(uuid.uuid4())
    _sessions[token] = datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS)
    response.set_cookie(
        key="vat_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_TTL_HOURS * 3600,
    )
    return {"ok": True, "message": "Angemeldet"}


@app.post("/api/auth/logout")
async def logout(request: Request, response: Response):
    token = get_session_token(request)
    if token and token in _sessions:
        del _sessions[token]
    response.delete_cookie("vat_session")
    return {"ok": True}


@app.get("/api/auth/status")
async def auth_status(request: Request):
    return {"authenticated": is_authenticated(request)}


# Demo

@app.post("/api/demo/load")
async def load_demo(request: Request):
    require_auth(request)
    invoices = load_demo_data(quarter=DEMO_QUARTER, year=DEMO_YEAR)
    stats = get_demo_stats()
    return {
        "ok": True,
        "message": f"{len(invoices)} Demo-Rechnungen geladen",
        "stats": stats,
        "demo_mode": True,
    }


@app.delete("/api/demo/clear")
async def clear_demo(request: Request):
    require_auth(request)
    db.clear_all_invoices()
    return {"ok": True, "message": "Alle Daten gelöscht"}


# Invoices

@app.get("/api/invoices")
async def get_invoices(
    request: Request,
    direction: Optional[str] = None,
    status: Optional[str] = None,
    quarter: Optional[int] = None,
    year: Optional[int] = None,
):
    require_auth(request)
    invoices = db.get_invoices(
        direction=direction,
        status=status,
        quarter=quarter,
        year=year,
    )
    return {"invoices": invoices, "total": len(invoices)}


@app.get("/api/invoices/{invoice_id}")
async def get_invoice(request: Request, invoice_id: int):
    require_auth(request)
    inv = db.get_invoice(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
    return inv


@app.patch("/api/invoices/{invoice_id}")
async def update_invoice(
    request: Request,
    invoice_id: int,
    body: StatusUpdateRequest,
):
    require_auth(request)

    valid_statuses = {"ok", "corrected", "deleted", "to_review"}
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Ungültiger Status: {body.status}")

    updated = db.update_invoice_status(
        invoice_id=invoice_id,
        status=body.status,
        correction_category=body.correction_category,
        correction_reason=body.correction_reason,
        correction_percentage=body.correction_percentage,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
    return updated


@app.post("/api/invoices/undo")
async def undo_action(request: Request):
    require_auth(request)
    restored = db.undo_last_action()
    if not restored:
        raise HTTPException(status_code=404, detail="Keine Aktion zum Rückgängigmachen")
    return {"ok": True, "restored": restored}


@app.get("/api/invoices/export/json")
async def export_json(request: Request):
    require_auth(request)
    incoming = db.get_invoices(direction="incoming")
    outgoing = db.get_invoices(direction="outgoing")
    export = {
        "exported_at": datetime.utcnow().isoformat(),
        "incoming_invoices": incoming,
        "outgoing_invoices": outgoing,
        "total": len(incoming) + len(outgoing),
    }
    content = json.dumps(export, ensure_ascii=False, indent=2)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=vat_export.json"},
    )


# AI Review

@app.post("/api/ai/review")
async def ai_review(request: Request):
    require_auth(request)

    # Get all to_review invoices
    invoices = db.get_invoices(direction="incoming", status="to_review")
    if not invoices:
        return {"ok": True, "message": "Keine Rechnungen zur Überprüfung", "reviewed": 0}

    # Run AI review
    results = review_invoices_with_ai(
        invoices,
        api_key=GEMINI_API_KEY or None,
    )

    # Apply results back to DB
    updated_invoices = apply_ai_review_results(invoices, results)
    updated_count = 0
    for inv in updated_invoices:
        original = next((i for i in invoices if i["id"] == inv["id"]), None)
        if original and (
            inv.get("ai_flag") != original.get("ai_flag") or
            inv.get("ai_reason") != original.get("ai_reason") or
            inv.get("status") != original.get("status")
        ):
            db.update_invoice_status(
                inv["id"],
                inv["status"],
            )
            updated_count += 1

    return {
        "ok": True,
        "reviewed": len(results),
        "updated": updated_count,
        "results": results,
        "used_gemini": bool(GEMINI_API_KEY),
    }


# ELSTER Calculation

@app.get("/api/elster/calculate")
async def elster_calculate(
    request: Request,
    quarter: Optional[int] = None,
    year: Optional[int] = None,
):
    require_auth(request)

    q = quarter or DEMO_QUARTER
    y = year or DEMO_YEAR

    incoming = db.get_invoices(direction="incoming", quarter=q, year=y)
    outgoing = db.get_invoices(direction="outgoing", quarter=q, year=y)

    if not incoming and not outgoing:
        return {
            "error": "Keine Rechnungen vorhanden. Bitte erst Demo laden oder E-Mails scannen.",
            "quarter": q,
            "year": y,
        }

    result = calculate_elster(incoming, outgoing, quarter=q, year=y)
    return result


@app.get("/api/elster/summary")
async def elster_summary(request: Request, quarter: Optional[int] = None, year: Optional[int] = None):
    require_auth(request)

    q = quarter or DEMO_QUARTER
    y = year or DEMO_YEAR

    incoming = db.get_invoices(direction="incoming", quarter=q, year=y)
    outgoing = db.get_invoices(direction="outgoing", quarter=q, year=y)
    result = calculate_elster(incoming, outgoing, quarter=q, year=y)
    summary = format_elster_summary(result)
    return PlainTextResponse(summary)


@app.get("/api/elster/xml")
async def elster_xml(request: Request, quarter: Optional[int] = None, year: Optional[int] = None):
    require_auth(request)

    q = quarter or DEMO_QUARTER
    y = year or DEMO_YEAR

    incoming = db.get_invoices(direction="incoming", quarter=q, year=y)
    outgoing = db.get_invoices(direction="outgoing", quarter=q, year=y)
    result = calculate_elster(incoming, outgoing, quarter=q, year=y)
    xml = generate_elster_xml(result)
    return Response(
        content=xml,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=UStVA_{q}_{y}.xml"},
    )


# Email scan (real IMAP)

@app.post("/api/scan/email")
async def scan_email(request: Request, body: ScanRequest):
    require_auth(request)

    if not body.imap_host or not body.imap_user or not body.imap_password:
        raise HTTPException(
            status_code=400,
            detail="IMAP-Zugangsdaten erforderlich (host, user, password)"
        )

    try:
        from email_fetcher import EmailFetcher
        from pdf_analyzer import analyze_invoice_file
        import tempfile

        fetcher = EmailFetcher(
            host=body.imap_host,
            port=body.imap_port or 993,
            user=body.imap_user,
            password=body.imap_password,
            ssl=True,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher.connect()
            attachments = fetcher.fetch_pdf_attachments(
                date_from=body.date_from,
                date_to=body.date_to,
                output_dir=tmpdir,
            )
            fetcher.disconnect()

            inserted = []
            for att in attachments:
                analysis = analyze_invoice_file(att["filepath"], att["filename"])
                analysis["source"] = "email"
                analysis["quarter"] = body.quarter or DEMO_QUARTER
                analysis["year"] = body.year or DEMO_YEAR
                inv = db.insert_invoice(analysis)
                inserted.append(inv)

            # Run triage on all new invoices
            for inv in inserted:
                triaged = batch_triage([inv], "triage_rules.yaml")
                if triaged:
                    db.update_invoice_status(inv["id"], triaged[0]["status"])

        return {
            "ok": True,
            "scanned": len(attachments),
            "inserted": len(inserted),
        }

    except ConnectionError as e:
        raise HTTPException(status_code=400, detail=f"IMAP-Verbindung fehlgeschlagen: {e}")
    except Exception as e:
        logger.error("Email scan error: %s", e)
        raise HTTPException(status_code=500, detail=f"Scan-Fehler: {str(e)}")


# Stats

@app.get("/api/stats")
async def get_stats(request: Request):
    require_auth(request)
    incoming = db.get_invoices(direction="incoming")
    outgoing = db.get_invoices(direction="outgoing")

    by_status = {}
    by_category = {}
    for inv in incoming:
        s = inv.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1
        c = inv.get("correction_category") or inv.get("category", "unknown")
        if inv.get("status") not in ("deleted",):
            by_category[c] = by_category.get(c, 0) + 1

    total_incoming = len(incoming)
    reviewed = sum(1 for i in incoming if i.get("status") in ("ok", "corrected", "deleted"))
    to_review = by_status.get("to_review", 0)

    return {
        "total_incoming": total_incoming,
        "total_outgoing": len(outgoing),
        "by_status": by_status,
        "by_category": by_category,
        "reviewed": reviewed,
        "to_review": to_review,
        "progress_pct": round(reviewed / total_incoming * 100) if total_incoming else 0,
        "has_data": total_incoming > 0 or len(outgoing) > 0,
        "demo_mode": db.get_setting("demo_mode", False),
    }


@app.post("/api/settings/demo-mode")
async def set_demo_mode(request: Request):
    require_auth(request)
    db.set_setting("demo_mode", True)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=3003, reload=True)
