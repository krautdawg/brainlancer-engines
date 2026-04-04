# Brainlancer Engines — Monorepo Build Brief

## Overview
5 standalone AI automation engine demos for B2B SME market. Each engine is a self-contained web app with consistent KI Katapult branding. All open source, free to use, MIT licensed.

## Brand: KI Katapult Style Guide
- Primary BG: #132A3E (Deep Navy)
- Accent: #00B3FF (Sky Blue — buttons, links, interactive)
- Highlight: #00FFC5 (Electric Mint — accents, success states)
- White text on dark backgrounds, #333333 on light
- Light sections: #FFFFFF / #F5F5F5
- Font: Inter (Google Fonts) weights 400, 600, 700
- Vibe: Clean, professional, forward-thinking, modern tech
- No emojis in production UI (use subtle icons instead)

## Shared Stack
- **Backend:** Python 3.11 + FastAPI
- **Frontend:** Single-page HTML, Tailwind CSS via CDN, Alpine.js for reactivity
- **DB:** SQLite (per-engine)
- **AI:** Google Gemini Flash (free tier) — `gemini-2.0-flash` via `google-generativeai` Python SDK
- **Auth:** Simple password gate, env var `APP_PASSWORD` (default: `brainlancer2026`)
- **Deploy:** Docker (each engine has own Dockerfile)
- **Port:** Each engine runs on different port (3001-3005)
