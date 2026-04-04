# Engine 5: Supplier & Purchase Order Monitoring — Build Spec

## Goal
Build a PO tracking and supplier management engine. Upload purchase orders, monitor deliveries, auto-chase overdue suppliers, flag price deviations, generate spend reports. SMEs lose money here silently — this engine makes procurement visible.

## What to Build

### User Flow
1. **Login** — same auth pattern
2. **Import POs** — CSV/Excel upload of purchase orders:
   - PO number, supplier, items, quantities, unit prices, expected delivery date
   - Or manual entry form
3. **PO Tracker** — status board:
   - Columns: Ordered → Shipped → Received → Invoiced → Paid
   - Click to update status
   - Auto-flags overdue (past expected delivery with no update)
4. **Supplier Directory** — list of all suppliers with:
   - Contact info, payment terms
   - Performance scorecard (on-time %, price adherence)
   - Order history
5. **Auto-Chase** — for overdue POs:
   - Pre-written chase email templates
   - Escalation levels (gentle reminder → firm follow-up → escalation)
   - Shows generated emails, user approves before "sending"
   - MVP: export emails, don't actually send
6. **Price Monitor** — compares invoice prices vs approved rates:
   - Green: within tolerance (<5% deviation)
   - Yellow: 5-10% deviation
   - Red: >10% deviation — needs review
7. **Spend Dashboard** — weekly/monthly reports:
   - Spend by supplier (bar chart)
   - Spend by category (pie chart)
   - Trend over time (line chart)
   - Top anomalies highlighted

### Demo Mode
Pre-loaded with realistic procurement data:
- 5 suppliers (German companies)
- 25 POs across 3 months
- 3 overdue deliveries with chase emails ready
- 2 price deviations flagged
- Spend dashboard showing trends

### Technical Stack
- FastAPI + SQLite
- pandas for data analysis
- Chart.js for dashboards (via CDN)
- Tailwind + Alpine.js
- CSV parsing with Python csv module

### UI Design
- PO tracker feels like a Kanban board
- Spend dashboard with clean charts (dark theme variants of Chart.js)
- Supplier scorecard with clear visual indicators
- Chase email preview in a clean modal
- Red/yellow/green color coding for urgency
- KI Katapult branding

### Files
```
engine-5-supplier/
├── app.py
├── po_tracker.py         # PO status management
├── supplier_manager.py   # Supplier CRUD + scoring
├── price_monitor.py      # Price deviation detection
├── chase_engine.py       # Auto-chase email generation
├── spend_reporter.py     # Analytics + chart data
├── demo_data.py          # Pre-loaded demo procurement data
├── db.py
├── templates/
│   └── index.html
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

### Port: 3005
