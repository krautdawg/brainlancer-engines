# Engine 1: Lead Generator — Build Spec

## Goal
Rebuild the existing lead generator (from brainlancer repo) as a polished, working Python/FastAPI app with KI Katapult branding. This is the HERO DEMO — it must look stunning and actually work.

## Existing Code Reference
The existing code in `../lead-engine/` (cloned from github.com/krautdawg/brainlancer) has:
- `app.py` — FastAPI main
- `website_analyzer.py` — scrapes URL, uses AI for ICP generation
- `lead_scraper.py` — Google search + directory scraping for leads
- `db.py` — SQLite schema
- `templates/index.html` — frontend
- `SPEC.md` — full original spec

## What to Build
A complete rewrite/polish of the lead engine. Keep the same user flow but upgrade everything:

### User Flow
1. **Login** — password gate (env `APP_PASSWORD`, default `brainlancer2026`)
2. **Enter URL** — user enters a company website URL
3. **AI Analysis** — scrape the URL, analyze with Gemini Flash, generate ICP
4. **Review ICP** — editable form with company name, industry, target titles, location, pain signals
5. **Find Leads** — scrape Google + public directories for matching leads
6. **CRM View** — table of found leads with contact info, notes, export to CSV

### Technical Requirements
- FastAPI backend with session auth
- Gemini Flash for ICP analysis and lead notes (use `google-generativeai` SDK, API key from env `GOOGLE_API_KEY`)
- If GOOGLE_API_KEY not set, use demo/mock data that looks realistic
- BeautifulSoup for web scraping
- SQLite for sessions, ICPs, leads
- Single-page frontend (Tailwind + Alpine.js)
- 10 scrape credits per session
- CSV export
- Docker-ready

### UI Design
- Dark navy hero section (#132A3E)
- Step-by-step wizard with smooth transitions
- Loading spinners during AI/scrape operations
- Clean CRM table with hover states
- Mobile responsive
- KI Katapult branding (see ../BRIEF.md)

### Files to Create
```
engine-1-leadgen/
├── app.py
├── website_analyzer.py
├── lead_scraper.py
├── db.py
├── templates/
│   └── index.html
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

### Demo Data Fallback
When AI/scraping is unavailable (no API key, rate limited), serve realistic demo data:
- 3 sample ICPs for different industries
- 10 sample leads per ICP with German B2B companies (Potsdam, Berlin, Brandenburg area)
- This ensures the demo always works in live presentations

### Port: 3001
