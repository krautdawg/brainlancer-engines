# Engine 5 — Supplier & Purchase Order Monitoring

KI Katapult · Brainlancer Engine 5 · Port 3005

## What it does

- **PO Tracker** — Kanban board (Ordered → Shipped → Received → Invoiced → Paid), overdue flags
- **Supplier Directory** — Contact info, performance scorecards, order history
- **Auto-Chase Engine** — 3-level escalation email templates for overdue deliveries
- **Price Monitor** — Green/yellow/red deviation flags vs approved rates
- **Spend Dashboard** — Bar, pie, and line charts via Chart.js

## Quick Start

```bash
cp .env.example .env
pip install -r requirements.txt
python app.py
```

Open http://localhost:3005 · Password: `brainlancer2026`

Click **"Demo-Daten laden"** in the sidebar to load 5 suppliers, 25 POs, 3 overdue deliveries and 2 price deviations.

## Docker

```bash
docker build -t engine-5-supplier .
docker run -p 3005:3005 -v $(pwd)/data:/app/data engine-5-supplier
```

## CSV Upload Format

```csv
po_number,supplier_name,item_description,quantity,unit_price,expected_delivery,category
PO-2026-100,Beispiel GmbH,Artikel A,10,25.00,2026-05-01,Elektronik
```

Download the template from the PO Tracker view.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `APP_PASSWORD` | `brainlancer2026` | Login password |
| `DB_PATH` | `supplier_engine.db` | SQLite database path |
