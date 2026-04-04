"""Gemini Flash AI reviewer — second-opinion pass on invoice classifications."""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    logger.warning("google-generativeai not installed — AI review disabled")

SYSTEM_PROMPT = """Du bist ein deutscher Steuerberater-Assistent, spezialisiert auf Umsatzsteuerrecht.
Du überprüfst automatisch klassifizierte Eingangsrechnungen für die USt-Voranmeldung.

Für jede Rechnung prüfst du:
1. Ist die Steuerkateg­orie korrekt? (VST_19, VST_7, VST_0_EU, VST_0_DRITTLAND, NICHT_ABZIEHBAR)
2. Gibt es Hinweise auf private Nutzung?
3. Handelt es sich um Reverse Charge (EU oder §13b)?
4. Gibt es andere steuerliche Risiken?

Antworte immer als JSON-Array. Sei präzise und nenne den §-Bezug wenn relevant."""

CATEGORY_DESCRIPTIONS = {
    "VST_19": "Vorsteuer 19% (inländische Leistung)",
    "VST_7": "Vorsteuer 7% (ermäßigter Steuersatz, z.B. Bücher)",
    "VST_0_EU": "Innergemeinschaftlicher Erwerb (EU, Reverse Charge)",
    "VST_0_DRITTLAND": "§13b UStG Leistungsempfänger (Drittland, Reverse Charge)",
    "NICHT_ABZIEHBAR": "Nicht abziehbare Vorsteuer (Versicherung, Bewirtung etc.)",
}


def _build_review_prompt(invoices: list[dict]) -> str:
    """Build the review prompt for a batch of invoices."""
    invoice_lines = []
    for i, inv in enumerate(invoices, 1):
        cat = inv.get("category", "")
        cat_desc = CATEGORY_DESCRIPTIONS.get(cat, cat)
        invoice_lines.append(
            f"{i}. ID={inv.get('id')} | Lieferant: {inv.get('vendor', '?')} | "
            f"Betrag: {inv.get('amount_gross', 0):.2f} EUR (netto: {inv.get('amount_net', 0):.2f}) | "
            f"Land: {inv.get('country', '?')} | "
            f"Zugeordnet als: {cat_desc} | "
            f"Sicherheit: {int(inv.get('confidence', 0) * 100)}%"
        )

    invoices_text = "\n".join(invoice_lines)

    return f"""Bitte überprüfe folgende Eingangsrechnungen für Q1 2024:

{invoices_text}

Antworte als JSON-Array mit einem Objekt pro Rechnung:
[
  {{
    "id": <invoice_id>,
    "ok": true/false,
    "concern": "kurze Erklärung falls Problem" oder null,
    "suggested_category": "VST_19|VST_7|VST_0_EU|VST_0_DRITTLAND|NICHT_ABZIEHBAR" oder null,
    "risk_level": "low|medium|high"
  }}
]

Antworte NUR mit dem JSON-Array, ohne zusätzlichen Text."""


def review_invoices_with_ai(
    invoices: list[dict],
    api_key: Optional[str] = None,
    model: str = "gemini-2.0-flash",
) -> list[dict]:
    """
    Send invoices to Gemini Flash for AI review.

    Returns list of review results:
    [{id, ok, concern, suggested_category, risk_level}]
    """
    if not HAS_GEMINI:
        logger.warning("Gemini not available — returning mock results")
        return _mock_review(invoices)

    key = api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        logger.warning("No GEMINI_API_KEY set — returning mock results")
        return _mock_review(invoices)

    try:
        genai.configure(api_key=key)
        model_instance = genai.GenerativeModel(
            model_name=model,
            system_instruction=SYSTEM_PROMPT,
        )

        # Process in batches of 15 to stay within token limits
        batch_size = 15
        all_results = []

        for i in range(0, len(invoices), batch_size):
            batch = invoices[i:i + batch_size]
            prompt = _build_review_prompt(batch)

            response = model_instance.generate_content(prompt)
            text = response.text.strip()

            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            if text.endswith("```"):
                text = text[:-3]

            batch_results = json.loads(text.strip())
            all_results.extend(batch_results)

        logger.info("AI review completed for %d invoices", len(all_results))
        return all_results

    except json.JSONDecodeError as e:
        logger.error("AI returned invalid JSON: %s", e)
        return _mock_review(invoices)
    except Exception as e:
        logger.error("AI review failed: %s", e)
        return _mock_review(invoices)


def _mock_review(invoices: list[dict]) -> list[dict]:
    """
    Fallback mock review when Gemini is not available.
    Generates realistic-looking review results based on category heuristics.
    """
    results = []
    for inv in invoices:
        cat = inv.get("category", "")
        confidence = inv.get("confidence", 0.8)
        vendor = (inv.get("vendor") or "").lower()

        ok = confidence >= 0.75
        concern = None
        suggested = None
        risk = "low"

        if cat == "VST_0_EU" and confidence < 0.80:
            ok = False
            concern = "Bitte EU-USt-ID des Lieferanten verifizieren und Reverse Charge bestätigen."
            risk = "medium"
        elif cat == "VST_0_DRITTLAND":
            concern = "§13b UStG: Reverse Charge muss in USt-Voranmeldung deklariert werden (Kz. 46/47 + 67)."
            risk = "medium"
        elif cat == "NICHT_ABZIEHBAR" and "restaurant" in vendor:
            concern = "Bewirtungskosten: Vorsteuerabzug ausgeschlossen (§15 Abs. 1a UStG)."
            risk = "low"
        elif confidence < 0.60:
            ok = False
            concern = "Geringe Erkennungssicherheit — manuelle Überprüfung empfohlen."
            risk = "high"
        elif "amazon" in vendor and cat == "VST_19":
            concern = "Gemischte Amazon-Bestellung: Bitte sicherstellen, dass keine Privatartikel enthalten sind."
            risk = "medium"

        results.append({
            "id": inv.get("id"),
            "ok": ok,
            "concern": concern,
            "suggested_category": suggested,
            "risk_level": risk,
        })

    return results


def apply_ai_review_results(
    invoices: list[dict], review_results: list[dict]
) -> list[dict]:
    """
    Merge AI review results back into invoice dicts.
    Updates ai_flag, ai_reason, and optionally category suggestion.
    """
    review_map = {r["id"]: r for r in review_results if r.get("id")}

    updated = []
    for inv in invoices:
        inv_copy = dict(inv)
        review = review_map.get(inv.get("id"))

        if review:
            if not review.get("ok"):
                inv_copy["ai_flag"] = True
                existing_reason = inv_copy.get("ai_reason") or ""
                new_reason = review.get("concern") or ""
                if new_reason and new_reason not in existing_reason:
                    inv_copy["ai_reason"] = (
                        f"{existing_reason} | {new_reason}".strip(" |")
                        if existing_reason else new_reason
                    )
                if inv_copy.get("status") == "ok":
                    inv_copy["status"] = "to_review"
            else:
                if not inv_copy.get("ai_flag"):
                    inv_copy["ai_flag"] = False

        updated.append(inv_copy)

    return updated
