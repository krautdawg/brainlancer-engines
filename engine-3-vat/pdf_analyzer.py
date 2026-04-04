"""PDF text extraction and invoice field recognition."""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import pdfplumber; fail gracefully in demo mode
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    logger.warning("pdfplumber not available — PDF extraction disabled")

# ---- Tax category keywords ----
DRITTLAND_VENDORS = [
    "github", "openai", "anthropic", "dropbox", "zoom", "loom",
    "twilio", "sendgrid", "stripe", "mailchimp", "hubspot",
    "cloudflare", "vercel", "netlify", "heroku", "digitalocean",
    "figma", "notion", "canva", "slack", "airtable",
    "amazon web services", "aws.amazon.com",
]

EU_VENDORS = [
    "atlassian", "jira", "confluence", "microsoft", "linkedin",
    "stripe payments europe", "adobe systems", "spotify",
    "booking.com", "airbnb", "elastic", "mongodb",
]

GERMAN_VENDORS = [
    "hetzner", "ionos", "strato", "1&1", "netcup", "contabo",
    "telekom", "vodafone", "o2", "sipgate", "datev", "lexware",
    "sevdesk", "fastbill", "billomat", "viking", "otto",
    "mediamarkt", "saturn", "rewe", "dm markt", "dm-markt",
]

NOT_DEDUCTIBLE_KEYWORDS = [
    "versicherung", "insurance", "haftpflicht", "restaurant",
    "gasthaus", "café", "cafe", "bewirtung", "privat",
    "sky entertainment", "netflix", "amazon prime",
]

BOOK_KEYWORDS = ["isbn", "buchhandlung", "verlag", "buch", "thalia",
                 "hugendubel", "osiander", "fachbuch", "o'reilly"]

# ---- Amount patterns ----
# German format: 1.234,56 EUR  or  1.234,56 €
AMOUNT_PATTERN_DE = re.compile(
    r"(?:EUR|€)\s*([\d]{1,3}(?:\.[\d]{3})*,[\d]{2})"
    r"|"
    r"([\d]{1,3}(?:\.[\d]{3})*,[\d]{2})\s*(?:EUR|€)",
    re.IGNORECASE
)
# US/international format: 1,234.56 USD or $1,234.56
AMOUNT_PATTERN_US = re.compile(
    r"(?:USD|\$)\s*([\d]{1,3}(?:,[\d]{3})*\.[\d]{2})"
    r"|"
    r"([\d]{1,3}(?:,[\d]{3})*\.[\d]{2})\s*(?:USD)",
    re.IGNORECASE
)

# VAT rate detection
VAT_RATE_PATTERN = re.compile(
    r"(?:mwst|ust|umsatzsteuer|vat|mehrwertsteuer)[.\s]*"
    r"(7|19)[\s]*%",
    re.IGNORECASE
)

# Invoice number patterns
INVOICE_NUMBER_PATTERN = re.compile(
    r"(?:rechnungs?(?:nummer|nr\.?)|invoice\s*(?:no\.?|number|#)|re-nr\.?)\s*:?\s*([A-Z0-9/_\-]{4,30})",
    re.IGNORECASE
)

# Date patterns (German DD.MM.YYYY or ISO YYYY-MM-DD)
DATE_PATTERN = re.compile(
    r"(?:rechnungsdatum|datum|date)\s*:?\s*"
    r"(\d{1,2}[./]\d{1,2}[./]\d{2,4}"
    r"|\d{4}-\d{2}-\d{2})",
    re.IGNORECASE
)

# Country / EU reverse charge indicators
REVERSE_CHARGE_PATTERN = re.compile(
    r"reverse\s*charge|§\s*13b\s*ustg|§13b|"
    r"innergemeinschaftlich|intra-community|"
    r"steuerfreie.*lieferung",
    re.IGNORECASE
)

EU_VAT_ID_PATTERN = re.compile(
    r"(?:vat\s*(?:id|reg|number)|ust-?id(?:nr)?\.?)\s*:?\s*"
    r"([A-Z]{2}[A-Z0-9]{2,12})",
    re.IGNORECASE
)

EU_COUNTRY_CODES = {
    "AT", "BE", "BG", "CY", "CZ", "DK", "EE", "FI", "FR",
    "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
    "NL", "PL", "PT", "RO", "SE", "SI", "SK",
}


def parse_german_amount(text: str) -> Optional[float]:
    """Convert German-format amount string '1.234,56' to float 1234.56."""
    try:
        return float(text.replace(".", "").replace(",", "."))
    except (ValueError, AttributeError):
        return None


def parse_us_amount(text: str) -> Optional[float]:
    """Convert US-format amount string '1,234.56' to float 1234.56."""
    try:
        return float(text.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def extract_text_from_pdf(filepath: str) -> str:
    """Extract all text from a PDF file using pdfplumber."""
    if not HAS_PDFPLUMBER:
        return ""
    try:
        with pdfplumber.open(filepath) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
            return "\n".join(pages)
    except Exception as e:
        logger.warning("PDF extraction failed for %s: %s", filepath, e)
        return ""


def extract_amounts(text: str) -> dict:
    """
    Extract net, VAT, and gross amounts from invoice text.
    Returns {net, vat, gross, vat_rate}.
    """
    # Find all EUR amounts
    amounts = []
    for m in AMOUNT_PATTERN_DE.finditer(text):
        raw = m.group(1) or m.group(2)
        val = parse_german_amount(raw)
        if val is not None and val > 0:
            amounts.append(val)

    # Fallback to USD amounts (convert approximately)
    if not amounts:
        for m in AMOUNT_PATTERN_US.finditer(text):
            raw = m.group(1) or m.group(2)
            val = parse_us_amount(raw)
            if val is not None and val > 0:
                amounts.append(val)

    if not amounts:
        return {"net": 0, "vat": 0, "gross": 0, "vat_rate": 0}

    amounts_sorted = sorted(set(amounts))

    # Detect VAT rate
    vat_rate = 19.0  # default assumption
    rate_match = VAT_RATE_PATTERN.search(text)
    if rate_match:
        vat_rate = float(rate_match.group(1))

    # Try to identify gross/net/vat from amounts
    if len(amounts_sorted) >= 3:
        # Usually: net, vat, gross
        net = amounts_sorted[-3]
        vat = amounts_sorted[-2]
        gross = amounts_sorted[-1]
        # Sanity check
        if abs((net + vat) - gross) < 0.05:
            return {"net": net, "vat": vat, "gross": gross, "vat_rate": vat_rate}

    if len(amounts_sorted) >= 2:
        # Could be net + gross, or gross + vat
        a, b = amounts_sorted[-2], amounts_sorted[-1]
        # Try: a=net, b=gross
        expected_vat_19 = round(a * 0.19, 2)
        expected_vat_7 = round(a * 0.07, 2)
        if abs((a + expected_vat_19) - b) < 0.10:
            return {"net": a, "vat": expected_vat_19, "gross": b, "vat_rate": 19.0}
        if abs((a + expected_vat_7) - b) < 0.10:
            return {"net": a, "vat": expected_vat_7, "gross": b, "vat_rate": 7.0}

    # Last resort: largest amount = gross
    gross = max(amounts_sorted)
    vat = round(gross * (vat_rate / (100 + vat_rate)), 2)
    net = round(gross - vat, 2)
    return {"net": net, "vat": vat, "gross": gross, "vat_rate": vat_rate}


def detect_country(text: str, vendor_name: str = "") -> str:
    """
    Detect invoice country (DE, EU country code, US, etc.).
    Returns 2-letter country code.
    """
    combined = f"{text} {vendor_name}".lower()

    # Look for EU VAT ID (e.g. IE9700053D → IE)
    vat_match = EU_VAT_ID_PATTERN.search(text)
    if vat_match:
        country_code = vat_match.group(1)[:2].upper()
        if country_code in EU_COUNTRY_CODES:
            return country_code
        if country_code == "DE":
            return "DE"

    # Country hints from vendor name
    for v in DRITTLAND_VENDORS:
        if v in combined:
            # Check if it's actually US/non-EU
            if any(hint in combined for hint in ["inc.", "llc", "corp.", "ltd.", "san francisco", "seattle", "new york"]):
                return "US"
            if "australia" in combined or "pty" in combined:
                return "AU"

    # German domestic
    for v in GERMAN_VENDORS:
        if v in combined:
            return "DE"

    # EU hints
    for v in EU_VENDORS:
        if v in combined:
            return "IE"  # Many EU SaaS are Irish-registered

    # Explicit country mentions
    if "germany" in combined or "deutschland" in combined:
        return "DE"
    if "ireland" in combined or "dublin" in combined:
        return "IE"
    if "netherlands" in combined or "amsterdam" in combined:
        return "NL"
    if "usa" in combined or "united states" in combined or "san francisco" in combined:
        return "US"

    return "DE"  # Default assumption


def assign_tax_category(text: str, vendor_name: str, country: str,
                        vat_rate: float, vat_amount: float) -> tuple[str, float]:
    """
    Assign German VAT tax category and confidence score.

    Returns: (category, confidence)

    Categories:
      VST_19         — Domestic 19% Vorsteuer
      VST_7          — Domestic 7% Vorsteuer (books, food)
      VST_0_EU       — Innergemeinschaftlicher Erwerb (EU reverse charge)
      VST_0_DRITTLAND — §13b Leistungsempfänger (non-EU reverse charge)
      NICHT_ABZIEHBAR — Not deductible (insurance, entertainment)
    """
    combined = f"{text} {vendor_name}".lower()
    confidence = 0.5

    # Not deductible check first
    not_deductible_score = sum(
        1 for kw in NOT_DEDUCTIBLE_KEYWORDS if kw in combined
    )
    if not_deductible_score >= 2:
        return "NICHT_ABZIEHBAR", min(0.5 + not_deductible_score * 0.1, 0.92)

    # Reverse charge indicator
    has_reverse_charge = bool(REVERSE_CHARGE_PATTERN.search(text))
    has_zero_vat = vat_amount == 0

    # Non-EU (Drittland)
    if country not in EU_COUNTRY_CODES and country != "DE":
        if has_reverse_charge or has_zero_vat:
            return "VST_0_DRITTLAND", 0.88 if has_reverse_charge else 0.72

    # EU (innergemeinschaftlicher Erwerb)
    if country in EU_COUNTRY_CODES:
        if has_reverse_charge or has_zero_vat:
            return "VST_0_EU", 0.87 if has_reverse_charge else 0.70

    # Book / educational material (7%)
    book_score = sum(1 for kw in BOOK_KEYWORDS if kw in combined)
    if book_score >= 1 or vat_rate == 7.0:
        return "VST_7", min(0.75 + book_score * 0.05, 0.92)

    # German domestic 19%
    if country == "DE" and vat_rate == 19.0 and vat_amount > 0:
        de_vendor_score = sum(1 for v in GERMAN_VENDORS if v in combined)
        conf = min(0.75 + de_vendor_score * 0.05, 0.97)
        return "VST_19", conf

    # EU with actual VAT charged (billed with German VAT by EU entity)
    if country in EU_COUNTRY_CODES and vat_rate > 0:
        return "VST_19", 0.78

    # Fallback
    return "VST_19", 0.45


def score_invoice_likelihood(text: str) -> float:
    """Score how likely this PDF is actually an invoice (0-1)."""
    keywords = [
        "rechnung", "invoice", "faktura", "receipt",
        "netto", "brutto", "mwst", "umsatzsteuer", "vat",
        "steuernummer", "ust-id", "iban", "fällig",
        "zahlbar", "due date", "total", "subtotal",
    ]
    score = sum(0.1 for kw in keywords if kw in text.lower())
    return min(score, 1.0)


def extract_vendor_name(text: str) -> str:
    """
    Heuristic: extract vendor name from first few lines of invoice.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return "Unbekannt"
    # First non-empty line is often the company name
    for line in lines[:5]:
        if len(line) > 3 and not line.lower().startswith(("re", "invoice", "rechnung")):
            return line[:60]
    return lines[0][:60] if lines else "Unbekannt"


def analyze_invoice_file(filepath: str, filename: str = None) -> dict:
    """
    Full pipeline: extract text from PDF, analyze, return invoice data dict.
    """
    if filename is None:
        import os
        filename = os.path.basename(filepath)

    text = extract_text_from_pdf(filepath)

    if not text or score_invoice_likelihood(text) < 0.2:
        return {
            "filename": filename,
            "vendor": "Unbekannt (nicht lesbar)",
            "invoice_date": "",
            "invoice_number": "",
            "amount_net": 0,
            "amount_vat": 0,
            "amount_gross": 0,
            "vat_rate": 0,
            "category": "VST_19",
            "country": "DE",
            "status": "to_review",
            "confidence": 0.1,
            "ai_flag": True,
            "ai_reason": "PDF konnte nicht gelesen werden (Scan oder beschädigte Datei).",
            "raw_text": text[:500],
        }

    amounts = extract_amounts(text)
    vendor = extract_vendor_name(text)
    country = detect_country(text, vendor)
    category, confidence = assign_tax_category(
        text, vendor, country, amounts["vat_rate"], amounts["vat"]
    )

    # Extract invoice number
    inv_num = ""
    num_match = INVOICE_NUMBER_PATTERN.search(text)
    if num_match:
        inv_num = num_match.group(1)

    # Extract date
    inv_date = ""
    date_match = DATE_PATTERN.search(text)
    if date_match:
        inv_date = date_match.group(1)

    # AI flag for low confidence or special cases
    ai_flag = confidence < 0.70
    ai_reason = None
    if confidence < 0.50:
        ai_reason = "Niedrige Erkennungssicherheit — manuelle Prüfung empfohlen."
    elif category == "VST_0_EU":
        ai_reason = "Innergemeinschaftliche Leistung erkannt. Bitte Reverse Charge bestätigen."
    elif category == "VST_0_DRITTLAND":
        ai_reason = "Drittlandsleistung erkannt. §13b UStG Reverse Charge prüfen."

    return {
        "filename": filename,
        "vendor": vendor,
        "invoice_date": inv_date,
        "invoice_number": inv_num,
        "amount_net": amounts["net"],
        "amount_vat": amounts["vat"],
        "amount_gross": amounts["gross"],
        "vat_rate": amounts["vat_rate"],
        "category": category,
        "country": country,
        "status": "to_review" if ai_flag else "ok",
        "confidence": round(confidence, 2),
        "ai_flag": ai_flag,
        "ai_reason": ai_reason,
        "raw_text": text[:2000],
    }
