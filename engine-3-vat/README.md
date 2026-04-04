# Engine 3: Invoice & VAT Intelligence

**KI Katapult** — Automated German USt-Voranmeldung (quarterly VAT return) workflow.

Port: **3003**

## Features

- **Email scanning** — IMAP connection to download invoice PDFs from any date range
- **PDF analysis** — pdfplumber text extraction with German/US amount parsing, VAT rate detection, country detection
- **Auto-triage** — YAML-based rule engine for automatic classification (VST_19, VST_7, VST_0_EU, VST_0_DRITTLAND, NICHT_ABZIEHBAR)
- **KI-Review** — Gemini Flash second-opinion pass with concern flags
- **Interactive triage UI** — keyboard-first review queue (1=OK, 2=Correct, 3=Delete, Z=Undo)
- **ELSTER calculation** — all Kennzahlen (Kz. 41, 43, 46, 47, 66, 67, 81, 83, 89) with XML export
- **Demo mode** — 30 pre-loaded Q1/2024 invoices, works without any email credentials

## Quick Start

```bash
# Copy env
cp .env.example .env
# Edit .env with your GEMINI_API_KEY (optional)

# Docker
docker build -t engine-3-vat .
docker run -p 3003:3003 -v $(pwd)/data:/app/data engine-3-vat

# Or local dev
pip install -r requirements.txt
uvicorn app:app --port 3003 --reload
```

Open http://localhost:3003 — default password: `brainlancer2026`

## German Tax Reference

| Category | Description | ELSTER |
|---|---|---|
| `VST_19` | Standard 19% Vorsteuer (domestic) | Kz. 66 |
| `VST_7` | Reduced 7% (books, periodicals) | Kz. 66 |
| `VST_0_EU` | Innergemeinschaftl. Erwerb (EU reverse charge) | Kz. 89 + Kz. 67 |
| `VST_0_DRITTLAND` | §13b UStG non-EU (Drittland reverse charge) | Kz. 46 + Kz. 47 + Kz. 67 |
| `NICHT_ABZIEHBAR` | Insurance, entertainment — not deductible | — |
| `UST_19` | Output tax on sales at 19% | Kz. 81 |
| `UST_0_EU_B2B` | Steuerfreie EU-Lieferung | Kz. 41 |
| `UST_0_EXPORT` | Steuerfreie Ausfuhr | Kz. 43 |

**Kz. 83** = Output tax − Input tax (positive = Zahllast, negative = Erstattung)

## Triage Keyboard Shortcuts

| Key | Action |
|---|---|
| `1` | Accept as OK |
| `2` | Open correction form |
| `3` | Delete / mark as private |
| `Z` | Undo last action |
| `↑` / `k` | Previous invoice |
| `↓` / `j` | Next invoice |
