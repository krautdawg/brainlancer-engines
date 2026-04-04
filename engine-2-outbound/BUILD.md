# Engine 2: AI Outbound Prospecting & Sales Engagement — Build Spec

## Goal
Build an outbound sales automation engine that takes leads (from Engine 1 or CSV upload) and creates personalized multi-touch email campaigns. Natural extension of the Lead Generator.

## What to Build

### User Flow
1. **Login** — same auth pattern
2. **Import Leads** — CSV upload OR paste from Engine 1 (company, contact, email, website, notes)
3. **Campaign Setup** — define campaign parameters:
   - Sender name/email
   - Number of touchpoints (3-5 emails)
   - Cadence (Day 1, Day 3, Day 7, Day 14)
   - Tone (formal/casual/provocative)
   - Goal (meeting, demo, call, reply)
4. **AI Sequence Generation** — Gemini generates personalized email sequences per lead:
   - Researches company website for personalization hooks
   - Writes subject lines + body for each touchpoint
   - Different angle per email (value prop, social proof, case study, urgency, breakup)
5. **Review & Edit** — user reviews generated sequences, edits if needed
6. **Campaign Dashboard** — overview of all campaigns:
   - Leads per stage (draft, sent, replied, meeting booked)
   - Timeline view of upcoming sends
   - Reply detection status

### MVP Constraints
- No actual email sending in MVP (would need SMTP setup per customer)
- Instead: "Export ready-to-send" — generates email files/CSV for import into any ESP
- AI generates the sequences, user reviews, exports
- Reply tracking shown as mock/demo feature

### Technical Stack
- FastAPI + SQLite
- google-generativeai (Gemini Flash) for sequence generation
- CSV import/export
- Tailwind + Alpine.js frontend

### Key Pages
1. **Import** — drag-drop CSV or paste leads
2. **Campaign Builder** — setup parameters + generate
3. **Sequence Editor** — card-based view of each lead's email sequence, editable
4. **Dashboard** — campaign overview with stats
5. **Export** — download sequences as CSV or individual .eml files

### Demo Mode
Pre-loaded campaign with 5 German B2B leads, each with a 4-email sequence already generated. User can browse, edit, and see the full flow without needing AI.

### UI Notes
- Sequence editor should feel like a Kanban board — each lead is a column, each email is a card
- Drag to reorder, click to edit
- Preview mode shows the email as it would appear in inbox
- KI Katapult branding throughout

### Files
```
engine-2-outbound/
├── app.py
├── sequence_generator.py   # AI email sequence creation
├── lead_importer.py        # CSV parsing + validation
├── campaign_manager.py     # Campaign CRUD + state machine
├── demo_data.py            # Pre-loaded demo campaign
├── db.py
├── templates/
│   └── index.html
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

### Port: 3002
