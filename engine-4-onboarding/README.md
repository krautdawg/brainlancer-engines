# Engine 4: Employee Onboarding & Offboarding Engine

KI Katapult automation engine for managing employee onboarding and offboarding checklists.

## Quick Start

### Docker
```bash
docker build -t engine-4-onboarding .
docker run -p 3004:3004 -e APP_PASSWORD=brainlancer2026 engine-4-onboarding
```

### Local Development
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 3004
```

Visit http://localhost:3004 — default password: `brainlancer2026`

## Demo Mode

Click **Load Demo Data** in the sidebar to populate 3 example employees:
- **Sarah Chen** (Developer) — Day 3, 60% complete, 2 overdue tasks
- **Max Rodriguez** (Designer) — Day 1, ~17% complete, on track
- **Lisa Wagner** (Offboarding) — 80% complete, last day April 15

## Features

- YAML-driven checklist templates (developer, designer, offboarding)
- Kanban task board with drag-and-drop
- Assignee color coding: HR (purple), IT (blue), Manager (green), New Hire (orange)
- Overdue detection with escalation indicators
- In-app notifications with bell icon
- Progress bars per employee on dashboard
- Session authentication
