# Engine 2: AI Outbound Prospecting & Sales Engagement

Part of the **KI Katapult** Brainlancer Engines suite. Generates personalized multi-touch German B2B email sequences using Gemini Flash.

## Features

- **CSV lead import** — drag-drop or upload, supports German column names
- **Campaign builder** — configure sender, touchpoints (3–5), cadence, tone, goal
- **AI sequence generation** — Gemini Flash writes personalized German emails per lead
- **Kanban sequence editor** — card-based view, click to edit, inline preview
- **Email preview** — see each email as it would appear in an inbox
- **Export** — download as CSV or individual `.eml` files (ZIP)
- **Demo mode** — 5 pre-loaded German B2B leads with generated sequences
- **Session auth** — password gate via `APP_PASSWORD`

## Quick Start

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 3002
```

Open http://localhost:3002 — default password: `brainlancer2026`

## Docker

```bash
docker build -t engine-2-outbound .
docker run -p 3002:3002 \
  -e GOOGLE_API_KEY=your_key \
  -e APP_PASSWORD=brainlancer2026 \
  -v $(pwd)/data:/data \
  engine-2-outbound
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | Google Gemini API key (required for AI generation) |
| `APP_PASSWORD` | `brainlancer2026` | Login password |
| `DB_PATH` | `engine2.db` | SQLite database path |

## CSV Format

```csv
email,company,contact,website,notes
max@firma.de,Firma GmbH,Max Müller,https://firma.de,SaaS startup
```

Supported German aliases: `firma` → company, `ansprechpartner` → contact, `notizen` → notes

## Stack

- **Backend**: Python 3.11 + FastAPI + SQLite
- **AI**: Google Gemini Flash (`gemini-2.0-flash`)
- **Frontend**: Single-page HTML + Tailwind CSS + Alpine.js
- **Port**: 3002
