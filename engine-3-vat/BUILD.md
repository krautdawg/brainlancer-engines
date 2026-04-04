# Engine 3: Invoice & VAT Intelligence — Build Spec

## Goal
Build the full USt-Voranmeldung automation workflow from the detailed technical brief. This is a serious tool — Tim actually uses this process for his own taxes. Build the complete MVP.

## Full Technical Brief
See the complete spec below. This was written by Tim describing his actual quarterly tax workflow.

## What to Build — MVP Scope

### Phase 1-2: Email Scanner + PDF Analysis
- IMAP connection to email accounts (configurable via YAML)
- Download invoice PDFs from configurable date range
- PDF text extraction with `pdfplumber`
- Invoice recognition scoring system (keywords + amount patterns)
- Amount extraction (German + US formats)
- VAT rate detection (7%, 19%, reverse charge)
- Country detection (DE/EU/Drittland)
- Tax category assignment (VST_19, VST_7, VST_0_EU, VST_0_DRITTLAND, NICHT_ABZIEHBAR)

### Phase 3: Auto-Triage
- YAML-based rule system for automatic classification
- Business/private keyword matching
- Duplicate detection (invoice vs receipt, cross-account)
- Learning from previous quarters

### Phase 4: AI Second Opinion
- Send batch to Gemini Flash for review
- Flag potential misclassifications

### Phase 5-6: Interactive Review UI (THE KEY FEATURE)
- Triage queue design (NOT a boring table)
- Keyboard-first navigation (1=OK, 2=Correct, 3=Delete, Z=Undo)
- Progress bar showing completion
- Tabs: To Review / All / OK / Corrected / Deleted
- Detail panel with PDF preview link
- Correction form (category, business class, percentage)
- LocalStorage auto-save
- JSON export

### Phase 7-8: Income Analysis + ELSTER Calculation
- Read outgoing invoices from folder
- Categorize (UST_19, UST_0_EXPORT, UST_0_EU_B2B)
- Calculate all ELSTER Kennzahlen (Kz. 81, 89, 46, 47, 66, 67, 83)
- Generate XML output
- Human-readable summary with manual entry instructions

### Phase 9-10: Submit + Learn
- Summary page with values to enter in Mein ELSTER
- Update triage rules from user decisions

### DEMO MODE (Critical!)
When no email credentials are configured, the app MUST work with demo data:
- Pre-loaded sample invoices (mix of DE/EU/Drittland)
- ~30 demo invoices already analyzed
- ~20 auto-triaged, ~10 for manual review
- Working ELSTER calculation from demo data
- Label clearly as "DEMO MODE — Simulated Data"
- This is what we show potential clients

### Technical Stack
- FastAPI backend
- pdfplumber for PDF extraction
- pyyaml for rules configuration
- google-generativeai for AI features (Gemini Flash)
- Single-page frontend (Tailwind + Alpine.js)
- SQLite for data storage
- Session auth (same pattern as other engines)

### UI Design
- Same KI Katapult branding
- The review UI is the hero — it should feel fast and satisfying
- Keyboard shortcuts are essential
- Progress bar is motivating
- Color coding: green (OK), yellow (corrected), red (deleted), blue (to review)
- ELSTER summary page should look clean and trustworthy

### Files to Create
```
engine-3-vat/
├── app.py                    # FastAPI routes
├── email_fetcher.py          # IMAP email scanning
├── pdf_analyzer.py           # PDF text extraction + invoice detection
├── triage_engine.py          # Rule-based auto-triage
├── ai_reviewer.py            # Gemini-powered second opinion
├── elster_calculator.py      # ELSTER Kennzahlen + XML
├── demo_data.py              # Demo mode data generator
├── db.py                     # SQLite models
├── config.example.yaml       # Example config
├── triage_rules.example.yaml # Example triage rules
├── templates/
│   └── index.html            # Single page app
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

### Port: 3003

## German Tax Reference (for correct implementation)
- VST_19: Standard 19% Vorsteuer (domestic)
- VST_7: Reduced 7% (books, food, etc.)
- VST_0_EU: Innergemeinschaftlicher Erwerb (reverse charge EU) — Kz. 89 + Kz. 67
- VST_0_DRITTLAND: §13b (reverse charge non-EU) — Kz. 46/47 + Kz. 67
- NICHT_ABZIEHBAR: Insurance, representation costs
- UST_19: Output tax on sales at 19% — Kz. 81
- UST_0_EXPORT: Tax-free export to non-EU — not on UStVA
- Kz. 83: Final result (positive = pay, negative = refund)
