# Engine 4: Employee Onboarding & Offboarding Engine — Build Spec

## Goal
Build a checklist-driven onboarding/offboarding automation engine. When a new hire is entered, a 30-step checklist auto-generates with tasks assigned to different people (HR, IT, Manager, New Hire). Tracks completion, sends notifications, escalates overdue items.

## What to Build

### User Flow
1. **Login** — same auth pattern
2. **New Onboarding** — form to start onboarding:
   - Employee name, email, start date
   - Role/Department (dropdown)
   - Manager name/email
   - Office location
3. **Checklist Generation** — auto-creates tasks from YAML template:
   - Pre-Day-1: Send welcome email, ship laptop, prepare desk
   - Day 1: Office tour, IT setup, security briefing, team intro
   - Week 1: Complete training modules, shadow sessions, 1:1 with manager
   - Month 1: Performance check-in, feedback form, full access review
4. **Task Board** — Kanban view of all tasks:
   - Columns: To Do / In Progress / Done / Overdue
   - Each task has: assignee, due date, status, notes
   - Click to mark complete, reassign, or add notes
5. **Dashboard** — overview of all active onboardings:
   - Progress bars per employee
   - Overdue task count (red badges)
   - Recent activity feed
6. **Offboarding** — reverse checklist:
   - Revoke accounts, return equipment, exit survey, knowledge transfer

### Checklist Templates (YAML-driven)
```yaml
templates:
  developer:
    - task: "Send offer letter"
      assignee: "hr"
      due: "start_date - 14d"
      category: "pre-boarding"
    - task: "Order laptop + peripherals"
      assignee: "it"
      due: "start_date - 7d"
      category: "pre-boarding"
    - task: "Create GitHub account"
      assignee: "it"
      due: "start_date - 1d"
      category: "accounts"
    # ... 30 tasks total
```

### Notification System (MVP)
- In-app notifications (bell icon with badge count)
- Optional: webhook URL for Slack/Teams integration
- Email notification stubs (shows what WOULD be sent)

### Demo Mode
Pre-loaded with 3 employees at different stages:
- Sarah (Developer) — Day 3, 60% complete, 2 overdue
- Max (Designer) — Day 1, 15% complete, on track
- Lisa (Offboarding) — 80% complete

### Technical Stack
- FastAPI + SQLite
- YAML for checklist templates
- Tailwind + Alpine.js
- No external dependencies for MVP

### UI Design
- Task board feels like Trello/Linear
- Smooth drag-and-drop for task status changes
- Color-coded by assignee type (HR=purple, IT=blue, Manager=green, NewHire=orange)
- Timeline view option (Gantt-lite)
- KI Katapult branding

### Files
```
engine-4-onboarding/
├── app.py
├── checklist_engine.py    # YAML template processing + task generation
├── notification.py        # In-app + webhook notifications
├── demo_data.py          # Pre-loaded demo employees
├── db.py
├── templates/
│   ├── developer.yaml     # Developer onboarding template
│   ├── designer.yaml      # Designer onboarding template
│   ├── offboarding.yaml   # Universal offboarding template
│   └── index.html         # Frontend
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

### Port: 3004
