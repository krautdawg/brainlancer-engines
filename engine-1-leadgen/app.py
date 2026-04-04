import io
import csv
import os
import secrets

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from db import init_db, save_icp, save_leads, get_session_leads, clear_session_leads
from website_analyzer import analyze_website
from lead_scraper import find_leads

load_dotenv()

APP_PASSWORD = os.getenv("APP_PASSWORD", "brainlancer2026")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
CREDITS_PER_SESSION = int(os.getenv("CREDITS_PER_SESSION", "10"))

app = FastAPI(title="Engine 1 – Lead Generator", docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, session_cookie="leadgen_session")

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup():
    init_db()


# ── Auth helpers ────────────────────────────────────────────────────────────

def is_authenticated(request: Request) -> bool:
    return request.session.get("authenticated") is True


def require_auth(request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")


def ensure_session_id(request: Request) -> str:
    if not request.session.get("session_id"):
        request.session["session_id"] = secrets.token_hex(16)
    return request.session["session_id"]


# ── Pages ────────────────────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request):
    form = await request.form()
    password = form.get("password", "")
    if password == APP_PASSWORD:
        request.session["authenticated"] = True
        request.session["credits"] = CREDITS_PER_SESSION
        ensure_session_id(request)
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Falsches Passwort"})


@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login", status_code=302)
    credits = request.session.get("credits", CREDITS_PER_SESSION)
    return templates.TemplateResponse("index.html", {"request": request, "credits": credits})


# ── API ───────────────────────────────────────────────────────────────────────

@app.post("/api/analyze")
async def api_analyze(request: Request):
    require_auth(request)

    credits = request.session.get("credits", 0)
    if credits <= 0:
        raise HTTPException(status_code=429, detail="Keine Credits mehr. Bitte erneut einloggen.")

    body = await request.json()
    url = body.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL ist erforderlich")

    icp = await analyze_website(url)

    request.session["credits"] = credits - 1
    session_id = ensure_session_id(request)
    icp_id = save_icp(session_id, icp)
    request.session["current_icp_id"] = icp_id

    icp["credits_remaining"] = request.session["credits"]
    return JSONResponse(icp)


@app.post("/api/leads")
async def api_leads(request: Request):
    require_auth(request)

    body = await request.json()
    icp_data = body.get("icp")
    if not icp_data:
        raise HTTPException(status_code=400, detail="ICP-Daten fehlen")

    leads = await find_leads(icp_data)

    session_id = ensure_session_id(request)
    icp_id = request.session.get("current_icp_id")
    # Clear previous leads for this session then save new ones
    clear_session_leads(session_id)
    if icp_id:
        save_leads(session_id, icp_id, leads)

    return JSONResponse({"leads": leads})


@app.get("/api/leads/export")
async def export_leads(request: Request):
    require_auth(request)

    session_id = request.session.get("session_id")
    if not session_id:
        raise HTTPException(status_code=404, detail="Keine Leads gefunden")

    leads = get_session_leads(session_id)
    if not leads:
        raise HTTPException(status_code=404, detail="Keine Leads zum Exportieren")

    output = io.StringIO()
    fieldnames = ["company_name", "website", "contact_name", "role", "email", "phone", "notes", "source"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(leads)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),  # BOM for Excel compatibility
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="leads.csv"'},
    )


@app.get("/api/credits")
async def get_credits(request: Request):
    require_auth(request)
    return JSONResponse({"credits": request.session.get("credits", 0)})
