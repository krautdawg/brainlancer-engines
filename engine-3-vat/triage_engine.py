"""Rule-based auto-triage engine — YAML rules + duplicate detection."""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

VALID_CATEGORIES = {
    "VST_19", "VST_7", "VST_0_EU", "VST_0_DRITTLAND", "NICHT_ABZIEHBAR"
}

DEFAULT_RULES = [
    {"name": "US Cloud", "pattern": r"(aws|dropbox|github|openai|figma|canva|zoom|notion|anthropic|cloudflare|vercel|netlify|digitalocean|twilio|sendgrid|stripe inc|hubspot)", "category": "VST_0_DRITTLAND", "confidence": 0.88},
    {"name": "EU SaaS", "pattern": r"(atlassian|jira|confluence|stripe payments europe|spotify ab)", "category": "VST_0_EU", "confidence": 0.85},
    {"name": "German Hosting", "pattern": r"(hetzner|ionos|strato|netcup|contabo|uberspace|all-inkl)", "category": "VST_19", "confidence": 0.95},
    {"name": "German Telecom", "pattern": r"(telekom|vodafone|o2 telefonica|sipgate)", "category": "VST_19", "confidence": 0.95},
    {"name": "German Software", "pattern": r"(datev|lexware|sevdesk|fastbill|billomat)", "category": "VST_19", "confidence": 0.93},
    {"name": "Books 7%", "pattern": r"(isbn|buchhandlung|thalia|hugendubel|springer verlag|o'reilly)", "category": "VST_7", "confidence": 0.88},
    {"name": "Insurance", "pattern": r"(versicherung|insurance|haftpflicht|allianz|axa|ergo)", "category": "NICHT_ABZIEHBAR", "confidence": 0.92},
    {"name": "Restaurants", "pattern": r"(restaurant|gasthaus|café|cafe|bewirtung|speisen)", "category": "NICHT_ABZIEHBAR", "confidence": 0.80},
]


def load_rules(rules_path: str = "triage_rules.yaml") -> list[dict]:
    """Load triage rules from YAML file, falling back to defaults."""
    if not HAS_YAML:
        return DEFAULT_RULES

    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            rules = data.get("rules", [])
            if rules:
                return rules
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning("Could not load rules from %s: %s", rules_path, e)

    return DEFAULT_RULES


def apply_rules(vendor: str, raw_text: str, rules: list[dict]) -> Optional[dict]:
    """
    Apply triage rules to an invoice.
    Returns best matching rule result or None.
    """
    combined = f"{vendor} {raw_text}".lower()

    best_match = None
    best_confidence = 0.0

    for rule in rules:
        pattern = rule.get("pattern", "")
        if not pattern:
            continue
        try:
            if re.search(pattern, combined, re.IGNORECASE):
                conf = float(rule.get("confidence", 0.7))
                if conf > best_confidence:
                    best_confidence = conf
                    best_match = {
                        "rule_name": rule.get("name", ""),
                        "category": rule.get("category", "VST_19"),
                        "confidence": conf,
                        "note": rule.get("note", ""),
                    }
        except re.error as e:
            logger.warning("Bad regex pattern in rule '%s': %s", rule.get("name"), e)

    return best_match


def check_business_keywords(text: str, private_keywords: list = None,
                             business_keywords: list = None) -> dict:
    """
    Check for business vs. private keywords.
    Returns {is_business: bool, is_private: bool, score: float}
    """
    if private_keywords is None:
        private_keywords = ["privat", "private", "personal", "hobby",
                            "drogerie", "apotheke", "lebensmittel", "supermarkt"]
    if business_keywords is None:
        business_keywords = ["rechnung", "invoice", "faktura", "netto",
                              "mwst", "umsatzsteuer", "steuernummer", "ust-id"]

    text_lower = text.lower()
    private_hits = sum(1 for kw in private_keywords if kw in text_lower)
    business_hits = sum(1 for kw in business_keywords if kw in text_lower)

    total = private_hits + business_hits
    if total == 0:
        return {"is_business": True, "is_private": False, "score": 0.5}

    business_score = business_hits / total
    return {
        "is_business": business_score >= 0.5,
        "is_private": private_hits > business_hits,
        "score": business_score,
    }


def detect_duplicates(new_invoice: dict, existing_invoices: list[dict]) -> Optional[dict]:
    """
    Check if new_invoice is a duplicate of any existing invoice.
    Returns the duplicate invoice dict if found, else None.
    """
    new_vendor = (new_invoice.get("vendor") or "").lower().strip()
    new_amount = round(new_invoice.get("amount_gross", 0), 2)
    new_date = new_invoice.get("invoice_date", "")
    new_number = (new_invoice.get("invoice_number") or "").strip()

    for inv in existing_invoices:
        if inv.get("id") == new_invoice.get("id"):
            continue

        # Exact invoice number match (strongest signal)
        existing_number = (inv.get("invoice_number") or "").strip()
        if new_number and existing_number and new_number == existing_number:
            return inv

        # Same vendor + amount + date
        existing_vendor = (inv.get("vendor") or "").lower().strip()
        existing_amount = round(inv.get("amount_gross", 0), 2)
        existing_date = inv.get("invoice_date", "")

        if (new_vendor and existing_vendor and
                new_vendor == existing_vendor and
                new_amount > 0 and new_amount == existing_amount and
                new_date and new_date == existing_date):
            return inv

    return None


def auto_triage(invoice: dict, existing_invoices: list[dict],
                rules: list[dict] = None) -> dict:
    """
    Full auto-triage pipeline for a single invoice.

    Returns updated invoice dict with:
      - status: 'ok' (auto-triaged) or 'to_review' (needs human)
      - category (updated if rule matched)
      - confidence (updated)
      - ai_flag, ai_reason (if concerns found)
    """
    if rules is None:
        rules = DEFAULT_RULES

    result = dict(invoice)
    flags = []

    # 1. Duplicate check
    duplicate = detect_duplicates(invoice, existing_invoices)
    if duplicate:
        result["status"] = "to_review"
        result["ai_flag"] = True
        flags.append(
            f"Mögliches Duplikat: identische Rechnung #{duplicate.get('invoice_number')} "
            f"von {duplicate.get('vendor')} bereits vorhanden."
        )

    # 2. Apply triage rules
    vendor = invoice.get("vendor", "")
    raw_text = invoice.get("raw_text", "")
    rule_match = apply_rules(vendor, raw_text, rules)

    if rule_match:
        matched_category = rule_match["category"]
        if matched_category in VALID_CATEGORIES:
            # If rule gives higher confidence, update category
            current_conf = invoice.get("confidence", 0)
            if rule_match["confidence"] > current_conf:
                result["category"] = matched_category
                result["confidence"] = rule_match["confidence"]

    # 3. Business/private check
    biz = check_business_keywords(raw_text)
    if biz["is_private"]:
        result["status"] = "to_review"
        result["ai_flag"] = True
        flags.append("Mögliche Privatausgabe erkannt — bitte prüfen.")

    # 4. Confidence threshold
    final_confidence = result.get("confidence", 0)
    if final_confidence < 0.60:
        result["status"] = "to_review"
        result["ai_flag"] = True
        flags.append(f"Niedrige Erkennungssicherheit ({int(final_confidence * 100)}%)")

    # 5. Zero amount check
    if result.get("amount_gross", 0) == 0:
        result["status"] = "to_review"
        result["ai_flag"] = True
        flags.append("Kein Betrag erkannt — manuelle Eingabe erforderlich.")

    # Update AI reason
    if flags:
        result["ai_reason"] = " | ".join(flags)
        result["ai_flag"] = True

    # Auto-approve if high confidence and no flags
    if not flags and final_confidence >= 0.80:
        result["status"] = "ok"

    return result


def batch_triage(invoices: list[dict], rules_path: str = "triage_rules.yaml") -> list[dict]:
    """
    Run auto-triage on a batch of invoices.
    Earlier invoices are passed as context for duplicate detection.
    """
    rules = load_rules(rules_path)
    results = []
    processed = []

    for inv in invoices:
        triaged = auto_triage(inv, processed, rules)
        results.append(triaged)
        processed.append(triaged)

    auto_ok = sum(1 for r in results if r["status"] == "ok")
    to_review = sum(1 for r in results if r["status"] == "to_review")
    logger.info(
        "Batch triage: %d total, %d auto-OK, %d to review",
        len(results), auto_ok, to_review
    )

    return results
