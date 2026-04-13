# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Brainlancer Engines** is a monorepo containing 5 independent AI-powered business automation demo applications, plus a landing page and nginx reverse proxy. All engines share the same tech stack but have independent codebases, databases, and UIs.

### The 5 Engines

1. **Engine 1: Lead Generation** (`engine-1-leadgen`) — Find B2B leads via web scraping + Gemini AI enrichment
2. **Engine 2: Outbound Sales** (`engine-2-outbound`) — Generate personalized sales sequences & talking points
3. **Engine 3: VAT Intelligence** (`engine-3-vat`) — German tax compliance automation with ELSTER integration
4. **Engine 4: Onboarding/Offboarding** (`engine-4-onboarding`) — Employee checklist automation with Slack simulation
5. **Engine 5: Supplier Management** (`engine-5-supplier`) — Supplier onboarding & document management

### Deployment Architecture

- **Landing page** (`landing/`) — FastAPI app serving static index.html with password auth + links to all engines
- **Nginx reverse proxy** (`nginx/`) — Routes all traffic to port 8090 with `.htpasswd` auth, serves engines on subpaths
- **Docker Compose** — Orchestrates all 6 services (landing + 5 engines + nginx)

## Tech Stack

**Consistent across all engines:**
- **Backend:** Python 3.11 + FastAPI 0.115 + Uvicorn
- **Frontend:** Single-page HTML + Tailwind CSS (CDN) + Alpine.js 3.x for reactivity
- **Database:** SQLite per-engine (stored in `/data` volume in Docker)
- **AI:** Google Gemini Flash 2.0 (`google-generativeai` SDK, used in engines 1–3)
- **Auth:** Simple password gate via session cookies (default password: `brainlancer2026`)
- **Deploy:** Docker (each engine has own Dockerfile + image, orchestrated by docker-compose)

**Ports (local development):**
- Landing: 8000
- Engine 1 (Lead Gen): 3001
- Engine 2 (Outbound): 3002
- Engine 3 (VAT): 3003
- Engine 4 (Onboarding): 3004
- Engine 5 (Supplier): 3005
- Nginx proxy: 8090

## Running the Project

### Full Stack (Recommended)

```bash
# Build & start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

Then visit `http://localhost:8090` (nginx proxy, requires auth — see `.htpasswd` in nginx/).

### Single Engine (Local Development)

To work on one engine locally:

```bash
cd engine-4-onboarding
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
export APP_PASSWORD=brainlancer2026
uvicorn app:app --reload --port 3004
```

Visit `http://localhost:3004` — password: `brainlancer2026`

### Testing / Debugging

- Each engine's `app.py` defines the FastAPI server. Run with `--reload` to auto-restart on code changes.
- Most engines include a "Load Demo Data" button in the UI — this populates test data from `demo_data.py`.
- For Gemini API: set `GOOGLE_API_KEY` environment variable (required for engines 1–3).

## Code Patterns & Architecture

### Engine Structure

Each engine follows this layout:

```
engine-X/
  app.py                    # FastAPI app, routes, auth, endpoints
  db.py                     # SQLite init & connection helpers
  checklist_engine.py       # Or: campaign_manager, lead_importer, etc. (domain logic)
  demo_data.py              # Loads test data for demo mode
  notification.py           # (In engine 4) In-app notifications
  requirements.txt          # Python dependencies
  Dockerfile                # Docker image definition
  templates/
    index.html              # Single-page HTML (Tailwind + Alpine.js)
  README.md                 # Engine-specific quick start
```

### Backend Patterns

**Authentication:**
- Simple password check at `/api/login` endpoint
- Session tokens stored as HTTP-only cookies (7-day max age)
- `verify_session()` helper checks cookie validity
- Protected endpoints use `require_auth()` dependency

**Database:**
- `db.py` provides `get_db()` context manager that returns a `sqlite3.Connection`
- Row factory set to `sqlite3.Row` for dict-like access
- Tables initialized in `init_db()` called at app startup
- No ORM (direct SQL for simplicity)

**API Routes:**
- `/` — Serves `templates/index.html` as HTML response
- `/api/login`, `/api/logout`, `/api/me` — Auth endpoints
- `/api/*` — Domain-specific endpoints (employees, tasks, campaigns, leads, etc.)
- All data returned as JSON; protected routes require valid session

**Demo Mode:**
- `demo_data.py` contains static datasets
- UI has "Load Demo Data" button that calls `/api/demo/init` endpoint
- Reloading demo mode is idempotent (checks if data already exists)

### Frontend Patterns

**All frontends use:**
- **HTML template** served from `templates/index.html`
- **Tailwind CSS** via CDN (no build step)
- **Alpine.js 3.x** for reactivity using `x-data`, `x-model`, `x-show`, `x-for`, `x-transition`
- **Fonts:** Outfit (Google Fonts, replacing Inter in recent refactors) + DM Mono for monospace
- **Colors:** KI Katapult brand colors—see BRIEF.md for palette

**Reactive State:**
- Alpine `x-data="app()"` wraps entire app with reactive data object
- State includes: auth, page/view, current data, modal states, filters, form inputs
- Computed getters for derived state (filtered lists, progress bars, unread counts)
- Fetch API for AJAX calls to backend; manual state updates on response

**Common UI Components:**
- Sidebar navigation with active state styling
- Task cards / kanban boards (used in engines 4 & 5 with drag-drop)
- Modal dialogs (`fixed inset-0 z-50` overlays with transitions)
- Toast notifications (brief messages at bottom-right)
- Progress bars (styling by status: todo, in-progress, done, overdue)
- Notifications bell with dropdown (counts unread items)

### Design System Notes

**Typography:**
- Headings: Outfit, extrabold (weight 800) in recent updates
- Body: Outfit, regular (400) / semibold (600)
- Monospace data (IDs, dates, codes): DM Mono
- No generic Inter font in new work — use Outfit for consistency

**Colors (KI Katapult):**
- Primary background: `#132A3E` (deep navy, used in dark themes)
- Accent: `#00B3FF` (sky blue — buttons, links, interactive)
- Highlight: `#00FFC5` (electric mint — success, highlights)
- Light theme: `#FFFFFF` / `#F5F5F5` backgrounds (current demo default)
- Text on light: `#333333` / grayscale utilities

**Shadow & Spacing:**
- Subtle shadows: `shadow-sm` on interactive elements (buttons, cards)
- Rounded corners: `rounded-2xl` for cards, `rounded-lg` for small elements
- Padding: standard Tailwind scale (`px-4`, `py-3`, etc.)

**Responsive:**
- Tailwind's mobile-first responsive prefixes (`sm:`, `md:`, `lg:`)
- Most engines are not heavily optimized for mobile (demo focus)

## Common Development Tasks

### Adding a Feature to an Engine

1. **Backend:** Add database schema to `db.py` `init_db()`, add endpoints to `app.py`, add domain logic to your engine module
2. **Frontend:** Update the `x-data` state object in `index.html`, add computed getters/methods, add HTML sections with `x-show` and `x-model`
3. **Test:** Load demo data, interact in browser, check Network tab for API calls and responses

### Adding a New Engine

1. Create `engine-X/` directory with structure above (copy from engine-4 as template)
2. Update `docker-compose.yml` with new service (port, environment, volumes)
3. Update `nginx/nginx.conf` with new upstream/location block if using reverse proxy
4. Ensure `requirements.txt` includes `fastapi`, `uvicorn`, and domain-specific packages

### Running Tests

Currently no test framework configured. For validation:
- Use browser DevTools to inspect API responses and state
- Click "Load Demo Data" to verify demo data generation
- Check SQLite directly: `sqlite3 /path/to/engine.db "SELECT * FROM table_name;"`

### Updating Fonts / Design System

- **Old:** Inter font (Google Fonts link in `<head>`)
- **New:** Outfit + DM Mono (Google Fonts CDN links)
- Update `<link>` tags in `templates/index.html`
- Change `font-family` in Tailwind config within `<script>` tag
- Update heading font-weights to `font-extrabold` (800) for new look

## Key Files & Dependencies

**Root-level:**
- `BRIEF.md` — Brand guidelines & tech stack overview
- `docker-compose.yml` — Orchestrates all services
- `nginx/` — Reverse proxy config & auth
- `landing/` — FastAPI landing page with login

**Per-engine:**
- `app.py` — FastAPI server (routes, auth, static file serving)
- `db.py` — SQLite initialization and connection management
- `templates/index.html` — Complete single-page app
- `requirements.txt` — Python package list
- `Dockerfile` — Image definition (based on `python:3.11-slim`)

**External:**
- `google-generativeai` — Gemini API client (engines 1–3 only)
- `beautifulsoup4` — HTML scraping (engine 1)
- `pyyaml` — YAML parsing for checklists (engine 4)

## Browser Compatibility & Notes

- All engines tested in modern browsers (Chrome, Firefox, Safari, Edge)
- Alpine.js 3.x requires ES6 support
- CSS Grid & Flexbox used throughout (no IE11 support)
- Tailwind CSS CDN build includes all utilities (not optimized for production)

## Deployment & Environment Variables

**Environment variables per engine:**
- `APP_PASSWORD` — Login password (default: `brainlancer2026`)
- `GOOGLE_API_KEY` — Google Gemini API key (required for engines 1–3, optional for 4–5)
- `SECRET_KEY` — Session signing secret (auto-generated dev defaults if not set)

**Docker volumes:**
- `e1-data:` — Engine 1 SQLite database
- `e2-data:` — Engine 2 SQLite database
- Other engines store data in container (can add volumes as needed)

**Nginx auth:**
- `.htpasswd` file in `nginx/` directory controls access to `http://localhost:8090`
- Generate with: `htpasswd -c .htpasswd admin` (or use existing file)

## Recent Work & Themes

**Latest commits focus on:**
- Translating UI from German to English (engines 2, 3, 5 fully translated)
- Converting dark theme to light theme for video demos
- Adding fake OAuth / Slack-like integrations (engine 3 Google Sign-In, engine 4 Slack simulation)
- Landing page with password auth + FastAPI

**Current UI philosophy:**
- Light theme backgrounds (white/light gray) with dark text
- Outfit font for all text (no Inter)
- DM Mono for monospace code/IDs
- Authentic-looking integrations (Google Sign-In spinner, Slack-branded sidebar)
- Full-screen overlay modals for complex interactions

## Reference Links

- FastAPI docs: https://fastapi.tiangolo.com/
- Alpine.js docs: https://alpinejs.dev/
- Tailwind CSS: https://tailwindcss.com/
- Google Gemini API: https://ai.google.dev/
