# Engine 3: Invoice & VAT Intelligence

USt-Voranmeldung automation — triage incoming invoices, classify for German VAT law, calculate ELSTER Kennzahlen.

## Features

- **Email Scanner**: IMAP-based PDF attachment fetching
- **PDF Analysis**: `pdfplumber` extraction with German/US amount parsing
- **Auto-Triage**: YAML rule engine + duplicate detection
- **AI Review**: Gemini Flash second-opinion on classifications
- **Interactive Queue**: Keyboard-first triage UI (1=OK, 2=Correct, 3=Delete, Z=Undo)
- **ELSTER Calculator**: Kz. 66, 67, 81, 83, 89 + XML export
- **Demo Mode**: 30 realistic Q1/2024 invoices, works without email credentials

## Quick Start

```bash
cp .env.example .env
# Edit .env with your settings

pip install -r requirements.txt
python app.py
# → http://localhost:3003
# Default password: brainlancer2026
```

## Docker

```bash
docker build -t engine-3-vat .
docker run -p 3003:3003 -v $(pwd)/data:/app/data engine-3-vat
```

## Tax Categories

| Category | Description | ELSTER |
|----------|-------------|--------|
| `VST_19` | German 19% input VAT | Kz. 66 |
| `VST_7` | German 7% input VAT (books etc.) | Kz. 66 |
| `VST_0_EU` | EU innergemeinschaftlicher Erwerb | Kz. 89 + 67 |
| `VST_0_DRITTLAND` | §13b reverse charge (non-EU) | Kz. 46 + 47 + 67 |
| `NICHT_ABZIEHBAR` | Not deductible (insurance, entertainment) | — |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_PASSWORD` | `brainlancer2026` | Login password |
| `GEMINI_API_KEY` | — | Enable AI review (optional) |
| `SECRET_KEY` | dev key | Session security |
| `DB_PATH` | `vat_engine.db` | SQLite database path |

## API Endpoints

- `POST /api/auth/login` — authenticate
- `GET /api/invoices` — list invoices (filter: direction, status, quarter, year)
- `PATCH /api/invoices/{id}` — update status/correction
- `POST /api/invoices/undo` — undo last action
- `POST /api/demo/load` — load demo dataset
- `GET /api/elster/calculate` — compute Kennzahlen
- `GET /api/elster/xml` — download XML
- `POST /api/scan/email` — trigger IMAP scan

## Port: 3003
