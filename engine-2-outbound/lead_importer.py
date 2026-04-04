import csv
import io
from typing import List, Dict, Tuple

# Field name aliases (supports German column names)
FIELD_ALIASES = {
    "email": ["email", "e-mail", "mail", "email_address"],
    "company": ["company", "firma", "unternehmen", "organization", "organisation"],
    "contact": ["contact", "name", "ansprechpartner", "kontakt", "full_name", "fullname", "person"],
    "website": ["website", "url", "web", "homepage", "site"],
    "notes": ["notes", "notizen", "comment", "kommentar", "description", "beschreibung"],
}


def normalize_headers(headers: List[str]) -> Dict[str, str]:
    """Map raw headers to canonical field names."""
    mapping = {}
    for raw in headers:
        key = raw.strip().lower().replace(" ", "_").replace("-", "_")
        for canonical, aliases in FIELD_ALIASES.items():
            if key in aliases:
                mapping[raw] = canonical
                break
        else:
            mapping[raw] = key
    return mapping


def parse_csv(content: str) -> Tuple[List[Dict], List[str]]:
    """Parse CSV content. Returns (leads, errors)."""
    reader = csv.DictReader(io.StringIO(content.strip()))
    if not reader.fieldnames:
        return [], ["CSV has no headers"]

    header_map = normalize_headers(list(reader.fieldnames))
    leads = []
    errors = []

    for i, row in enumerate(reader, 1):
        normalized = {}
        for raw_key, value in row.items():
            if raw_key is None:
                continue
            canonical = header_map.get(raw_key, raw_key.lower())
            normalized[canonical] = (value or "").strip()

        email = normalized.get("email", "").strip()
        if not email:
            errors.append(f"Row {i}: missing email — skipped")
            continue

        leads.append({
            "email": email,
            "company": normalized.get("company", ""),
            "contact": normalized.get("contact", ""),
            "website": normalized.get("website", ""),
            "notes": normalized.get("notes", ""),
        })

    if not leads and not errors:
        errors.append("No valid rows found in CSV")

    return leads, errors


def validate_leads(leads: List[Dict]) -> Tuple[List[Dict], List[str]]:
    """Basic validation of lead records."""
    valid = []
    errors = []
    seen_emails = set()

    for lead in leads:
        email = lead.get("email", "").strip()
        if not email or "@" not in email:
            errors.append(f"Invalid email: {email!r}")
            continue
        if email in seen_emails:
            errors.append(f"Duplicate email: {email} — skipped")
            continue
        seen_emails.add(email)
        valid.append(lead)

    return valid, errors
