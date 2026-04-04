import csv
import io
import os
import secrets
import zipfile
from email.mime.text import MIMEText
from email.utils import formatdate
from pathlib import Path
from typing import Any, Dict

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from campaign_manager import (
    add_lead,
    create_campaign,
    delete_campaign,
    get_campaign,
    get_campaign_sequences,
    get_campaign_stats,
    get_leads,
    get_sequence,
    list_campaigns,
    save_sequence,
    update_lead_status,
    update_sequence,
)
from db import init_db
from demo_data import get_demo_data
from lead_importer import parse_csv, validate_leads
from sequence_generator import generate_sequence

# ── App setup ───────────────────────────────────────────────────────────────────

APP_PASSWORD = os.environ.get("APP_PASSWORD", "brainlancer2026")
SESSIONS: Dict[str, bool] = {}

app = FastAPI(title="Engine 2: Outbound Prospecting")


@app.on_event("startup")
def startup():
    init_db()


# ── Auth helpers ────────────────────────────────────────────────────────────────

def require_auth(request: Request):
    sid = request.cookies.get("session_id")
    if not sid or sid not in SESSIONS:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return sid


# ── Pydantic models ─────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    password: str


class CampaignCreate(BaseModel):
    name: str
    sender_name: str
    sender_email: str
    num_touchpoints: int = 4
    cadence: str = "1,3,7,14"
    tone: str = "formal"
    goal: str = "meeting"


class LeadCreate(BaseModel):
    email: str
    company: str = ""
    contact: str = ""
    website: str = ""
    notes: str = ""


class LeadsImport(BaseModel):
    leads: list


class SequenceUpdate(BaseModel):
    subject: str
    body: str


class LeadStatusUpdate(BaseModel):
    status: str


# ── Auth routes ─────────────────────────────────────────────────────────────────

@app.post("/api/auth/login")
async def login(data: LoginRequest, response: Response):
    if data.password != APP_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")
    sid = secrets.token_hex(32)
    SESSIONS[sid] = True
    response.set_cookie(
        "session_id", sid, httponly=True, samesite="lax", max_age=86400 * 7
    )
    return {"success": True}


@app.post("/api/auth/logout")
async def logout(request: Request, response: Response):
    sid = request.cookies.get("session_id")
    if sid and sid in SESSIONS:
        del SESSIONS[sid]
    response.delete_cookie("session_id")
    return {"success": True}


@app.get("/api/auth/check")
async def auth_check(request: Request):
    sid = request.cookies.get("session_id")
    if sid and sid in SESSIONS:
        return {"authenticated": True}
    return {"authenticated": False}


# ── Campaign routes ──────────────────────────────────────────────────────────────

@app.get("/api/campaigns")
async def api_list_campaigns(auth=Depends(require_auth)):
    campaigns = list_campaigns()
    result = []
    for c in campaigns:
        stats = get_campaign_stats(c["id"])
        result.append({**c, "stats": stats})
    return {"campaigns": result}


@app.post("/api/campaigns", status_code=201)
async def api_create_campaign(data: CampaignCreate, auth=Depends(require_auth)):
    cid = create_campaign(
        name=data.name,
        sender_name=data.sender_name,
        sender_email=data.sender_email,
        num_touchpoints=data.num_touchpoints,
        cadence=data.cadence,
        tone=data.tone,
        goal=data.goal,
    )
    return {"campaign_id": cid}


@app.get("/api/campaigns/{cid}")
async def api_get_campaign(cid: int, auth=Depends(require_auth)):
    campaign = get_campaign(cid)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    stats = get_campaign_stats(cid)
    return {**campaign, "stats": stats}


@app.delete("/api/campaigns/{cid}")
async def api_delete_campaign(cid: int, auth=Depends(require_auth)):
    if not get_campaign(cid):
        raise HTTPException(404, "Campaign not found")
    delete_campaign(cid)
    return {"success": True}


# ── Lead routes ──────────────────────────────────────────────────────────────────

@app.get("/api/campaigns/{cid}/leads")
async def api_get_leads(cid: int, auth=Depends(require_auth)):
    if not get_campaign(cid):
        raise HTTPException(404, "Campaign not found")
    return {"leads": get_leads(cid)}


@app.post("/api/campaigns/{cid}/leads", status_code=201)
async def api_add_lead(cid: int, data: LeadCreate, auth=Depends(require_auth)):
    if not get_campaign(cid):
        raise HTTPException(404, "Campaign not found")
    lid = add_lead(
        campaign_id=cid,
        email=data.email,
        company=data.company,
        contact=data.contact,
        website=data.website,
        notes=data.notes,
    )
    return {"lead_id": lid}


@app.post("/api/campaigns/{cid}/leads/batch", status_code=201)
async def api_add_leads_batch(cid: int, data: LeadsImport, auth=Depends(require_auth)):
    if not get_campaign(cid):
        raise HTTPException(404, "Campaign not found")
    added = []
    for lead in data.leads:
        lid = add_lead(
            campaign_id=cid,
            email=lead.get("email", ""),
            company=lead.get("company", ""),
            contact=lead.get("contact", ""),
            website=lead.get("website", ""),
            notes=lead.get("notes", ""),
        )
        added.append(lid)
    return {"added": len(added), "lead_ids": added}


@app.post("/api/campaigns/{cid}/leads/import")
async def api_import_csv(cid: int, file: UploadFile = File(...), auth=Depends(require_auth)):
    if not get_campaign(cid):
        raise HTTPException(404, "Campaign not found")
    content = (await file.read()).decode("utf-8-sig", errors="replace")
    leads, parse_errors = parse_csv(content)
    valid_leads, val_errors = validate_leads(leads)
    errors = parse_errors + val_errors

    added_ids = []
    for lead in valid_leads:
        lid = add_lead(
            campaign_id=cid,
            email=lead["email"],
            company=lead.get("company", ""),
            contact=lead.get("contact", ""),
            website=lead.get("website", ""),
            notes=lead.get("notes", ""),
        )
        added_ids.append(lid)

    return {"added": len(added_ids), "errors": errors, "lead_ids": added_ids}


@app.patch("/api/leads/{lid}/status")
async def api_update_lead_status(lid: int, data: LeadStatusUpdate, auth=Depends(require_auth)):
    update_lead_status(lid, data.status)
    return {"success": True}


# ── Sequence routes ──────────────────────────────────────────────────────────────

@app.get("/api/campaigns/{cid}/sequences")
async def api_get_sequences(cid: int, auth=Depends(require_auth)):
    if not get_campaign(cid):
        raise HTTPException(404, "Campaign not found")
    leads_with_seqs = get_campaign_sequences(cid)
    return {"leads": leads_with_seqs}


@app.post("/api/campaigns/{cid}/generate")
async def api_generate_sequences(cid: int, auth=Depends(require_auth)):
    campaign = get_campaign(cid)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    leads = get_leads(cid)
    if not leads:
        raise HTTPException(400, "No leads in this campaign")

    results = []
    for lead in leads:
        try:
            sequences = generate_sequence(lead, campaign)
            for seq in sequences:
                save_sequence(
                    lead_id=lead["id"],
                    touchpoint_num=seq["touchpoint_num"],
                    subject=seq["subject"],
                    body=seq["body"],
                    scheduled_day=seq["scheduled_day"],
                )
            results.append({"lead_id": lead["id"], "company": lead["company"], "success": True, "count": len(sequences)})
        except Exception as exc:
            results.append({"lead_id": lead["id"], "company": lead["company"], "success": False, "error": str(exc)})

    leads_with_seqs = get_campaign_sequences(cid)
    return {"results": results, "leads": leads_with_seqs}


@app.put("/api/sequences/{seq_id}")
async def api_update_sequence(seq_id: int, data: SequenceUpdate, auth=Depends(require_auth)):
    seq = get_sequence(seq_id)
    if not seq:
        raise HTTPException(404, "Sequence not found")
    update_sequence(seq_id, data.subject, data.body)
    return {"success": True}


# ── Export routes ────────────────────────────────────────────────────────────────

@app.get("/api/campaigns/{cid}/export/csv")
async def api_export_csv(cid: int, auth=Depends(require_auth)):
    campaign = get_campaign(cid)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    leads_with_seqs = get_campaign_sequences(cid)
    num_tp = campaign["num_touchpoints"]

    output = io.StringIO()
    headers = ["company", "contact", "email", "website", "status"]
    for i in range(1, num_tp + 1):
        headers += [f"tp{i}_day", f"tp{i}_subject", f"tp{i}_body"]

    writer = csv.DictWriter(output, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()

    for lead in leads_with_seqs:
        row: Dict[str, Any] = {
            "company": lead["company"],
            "contact": lead["contact"],
            "email": lead["email"],
            "website": lead["website"],
            "status": lead["status"],
        }
        for seq in lead.get("sequences", []):
            n = seq["touchpoint_num"]
            if n <= num_tp:
                row[f"tp{n}_day"] = seq["scheduled_day"]
                row[f"tp{n}_subject"] = seq["subject"]
                row[f"tp{n}_body"] = seq["body"].replace("\n", " | ")
        writer.writerow(row)

    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="campaign_{cid}_sequences.csv"'},
    )


@app.get("/api/campaigns/{cid}/export/eml")
async def api_export_eml(cid: int, auth=Depends(require_auth)):
    campaign = get_campaign(cid)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    leads_with_seqs = get_campaign_sequences(cid)

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for lead in leads_with_seqs:
            company_slug = "".join(c if c.isalnum() else "_" for c in lead["company"])[:40]
            for seq in lead.get("sequences", []):
                msg = MIMEText(seq["body"], "plain", "utf-8")
                msg["From"] = f"{campaign['sender_name']} <{campaign['sender_email']}>"
                to_name = lead["contact"] or lead["company"]
                msg["To"] = f"{to_name} <{lead['email']}>"
                msg["Subject"] = seq["subject"]
                msg["Date"] = formatdate(localtime=True)
                fname = f"{company_slug}_tp{seq['touchpoint_num']}_day{seq['scheduled_day']}.eml"
                zf.writestr(fname, msg.as_string())

    zip_buf.seek(0)
    return Response(
        content=zip_buf.read(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="campaign_{cid}_emails.zip"'},
    )


# ── Demo route ───────────────────────────────────────────────────────────────────

@app.post("/api/demo")
async def api_load_demo(auth=Depends(require_auth)):
    campaign_data, leads_data, sequences_data = get_demo_data()

    cid = create_campaign(
        name=campaign_data["name"],
        sender_name=campaign_data["sender_name"],
        sender_email=campaign_data["sender_email"],
        num_touchpoints=campaign_data["num_touchpoints"],
        cadence=campaign_data["cadence"],
        tone=campaign_data["tone"],
        goal=campaign_data["goal"],
        is_demo=True,
    )

    for lead_data in leads_data:
        lid = add_lead(
            campaign_id=cid,
            email=lead_data["email"],
            company=lead_data["company"],
            contact=lead_data["contact"],
            website=lead_data["website"],
            notes=lead_data["notes"],
            status=lead_data["status"],
        )
        seqs = sequences_data.get(lead_data["company"], [])
        for seq in seqs:
            save_sequence(
                lead_id=lid,
                touchpoint_num=seq["touchpoint_num"],
                subject=seq["subject"],
                body=seq["body"],
                scheduled_day=seq["scheduled_day"],
            )

    return {"campaign_id": cid, "message": "Demo campaign loaded"}


# ── Frontend ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def index():
    return FileResponse(Path(__file__).parent / "templates" / "index.html")
