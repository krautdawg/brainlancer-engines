"""
ELSTER Kennzahlen calculator for German USt-Voranmeldung (quarterly VAT return).

German VAT categories → ELSTER Kennzahlen mapping:

INCOMING INVOICES (Vorsteuer / Input VAT):
  VST_19        → Kz. 66  (Abziehbare Vorsteuerbeträge — VAT amount)
  VST_7         → Kz. 66  (Abziehbare Vorsteuerbeträge — VAT amount)
  VST_0_EU      → Kz. 89  (Bemessungsgrundlage innergemeinschaftlicher Erwerb)
                  Kz. 67  (Vorsteuer §13b = net × 19%)
  VST_0_DRITTLAND → Kz. 46 (Bemessungsgrundlage §13b-Leistungen)
                    Kz. 47 (Steuer aus §13b = net × 19%) ← output tax
                    Kz. 67 (Vorsteuer §13b = net × 19%) ← input tax (cancels)
  NICHT_ABZIEHBAR → nothing

OUTGOING INVOICES (Umsatzsteuer / Output VAT):
  UST_19        → Kz. 81  (Steuerpflichtige Umsätze 19% — net amount)
  UST_7         → Kz. 86  (Steuerpflichtige Umsätze 7% — net amount)
  UST_0_EU_B2B  → Kz. 41  (Steuerfreie innergemeinschaftliche Lieferungen)
  UST_0_EXPORT  → Kz. 43  (Steuerfreie Ausfuhrlieferungen)

RESULT:
  Output tax = (Kz.81 × 19%) + (Kz.86 × 7%) + (Kz.89 × 19%) + Kz.47
  Input tax  = Kz.66 + Kz.67
  Kz. 83     = Output tax − Input tax
    > 0  →  Zahllast (you owe the Finanzamt)
    < 0  →  Überschuss / Erstattung (Finanzamt owes you)
"""

from typing import Optional
import xml.etree.ElementTree as ET
from datetime import datetime


CATEGORY_LABELS = {
    "VST_19": "Vorsteuer 19% (inland)",
    "VST_7": "Vorsteuer 7% (ermäßigt)",
    "VST_0_EU": "Innergemeinschaftlicher Erwerb (EU, §15a)",
    "VST_0_DRITTLAND": "§13b UStG Leistungsempfänger (Drittland)",
    "NICHT_ABZIEHBAR": "Nicht abziehbare Vorsteuer",
    "UST_19": "Steuerpfl. Umsätze 19%",
    "UST_7": "Steuerpfl. Umsätze 7%",
    "UST_0_EU_B2B": "Steuerfreie innergemeinschaftliche Lieferungen",
    "UST_0_EXPORT": "Steuerfreie Ausfuhrlieferungen",
}


def calculate_elster(
    incoming_invoices: list[dict],
    outgoing_invoices: list[dict],
    quarter: int = 1,
    year: int = 2024,
) -> dict:
    """
    Calculate all ELSTER Kennzahlen from invoice lists.

    Only invoices with status 'ok' or 'corrected' (not 'deleted' or 'to_review')
    are included in the calculation.
    """
    # Running totals
    kz41 = 0.0   # Steuerfreie innergemeinschaftliche Lieferungen (Bemessungsgrundlage)
    kz43 = 0.0   # Steuerfreie Ausfuhrlieferungen
    kz46 = 0.0   # §13b Leistungen Bemessungsgrundlage
    kz47 = 0.0   # Steuer aus §13b (Kz.46 × 19%) — output tax
    kz66 = 0.0   # Abziehbare Vorsteuer (from domestic 19%/7% invoices)
    kz67 = 0.0   # Vorsteuer aus §13b-Leistungen (EU + Drittland)
    kz81 = 0.0   # Steuerpflichtige Umsätze 19% (Bemessungsgrundlage)
    kz86 = 0.0   # Steuerpflichtige Umsätze 7% (Bemessungsgrundlage)
    kz89 = 0.0   # Innergemeinschaftliche Erwerbe 19% (Bemessungsgrundlage)

    line_items = {
        "VST_19": [],
        "VST_7": [],
        "VST_0_EU": [],
        "VST_0_DRITTLAND": [],
        "NICHT_ABZIEHBAR": [],
    }
    outgoing_line_items = {
        "UST_19": [],
        "UST_7": [],
        "UST_0_EU_B2B": [],
        "UST_0_EXPORT": [],
    }

    # ---- Process incoming invoices ----
    for inv in incoming_invoices:
        if inv.get("status") in ("deleted", "to_review"):
            continue

        # Use correction category if available, else original
        cat = inv.get("correction_category") or inv.get("category", "")
        net = float(inv.get("amount_net", 0) or 0)
        vat = float(inv.get("amount_vat", 0) or 0)
        gross = float(inv.get("amount_gross", 0) or 0)

        # Apply partial deduction percentage
        pct = float(inv.get("correction_percentage", 100) or 100) / 100.0

        item = {
            "id": inv.get("id"),
            "vendor": inv.get("vendor", ""),
            "date": inv.get("invoice_date", ""),
            "net": net,
            "vat": vat,
            "gross": gross,
            "category": cat,
        }

        if cat == "VST_19":
            kz66 += vat * pct
            item["kz"] = "Kz. 66"
            item["effect"] = f"+{vat * pct:.2f} EUR Vorsteuer"
            line_items["VST_19"].append(item)

        elif cat == "VST_7":
            kz66 += vat * pct
            item["kz"] = "Kz. 66"
            item["effect"] = f"+{vat * pct:.2f} EUR Vorsteuer (7%)"
            line_items["VST_7"].append(item)

        elif cat == "VST_0_EU":
            # Innergemeinschaftlicher Erwerb: report net at Kz.89,
            # owe tax at Kz.89×19%, claim back at Kz.67
            rc_tax = net * 0.19 * pct
            kz89 += net * pct
            kz67 += rc_tax
            item["kz"] = "Kz. 89 + Kz. 67"
            item["effect"] = (
                f"Kz.89 +{net * pct:.2f} EUR | "
                f"Kz.67 +{rc_tax:.2f} EUR (Reverse Charge, Nettoeffekt 0)"
            )
            line_items["VST_0_EU"].append(item)

        elif cat == "VST_0_DRITTLAND":
            # §13b: report at Kz.46 (Bemessungsgrundlage),
            # Kz.47 is output tax, Kz.67 cancels it as input tax
            rc_tax = net * 0.19 * pct
            kz46 += net * pct
            kz47 += rc_tax
            kz67 += rc_tax
            item["kz"] = "Kz. 46 + Kz. 47 + Kz. 67"
            item["effect"] = (
                f"Kz.46 +{net * pct:.2f} EUR | "
                f"Kz.47 +{rc_tax:.2f} EUR (output) | "
                f"Kz.67 +{rc_tax:.2f} EUR (input, Nettoeffekt 0)"
            )
            line_items["VST_0_DRITTLAND"].append(item)

        elif cat == "NICHT_ABZIEHBAR":
            item["kz"] = "—"
            item["effect"] = "Kein Vorsteuerabzug"
            line_items["NICHT_ABZIEHBAR"].append(item)

    # ---- Process outgoing invoices ----
    for inv in outgoing_invoices:
        if inv.get("status") == "deleted":
            continue

        cat = inv.get("category", "")
        net = float(inv.get("amount_net", 0) or 0)

        item = {
            "id": inv.get("id"),
            "vendor": inv.get("vendor", ""),
            "date": inv.get("invoice_date", ""),
            "net": net,
            "vat": float(inv.get("amount_vat", 0) or 0),
            "gross": float(inv.get("amount_gross", 0) or 0),
            "category": cat,
        }

        if cat == "UST_19":
            kz81 += net
            item["kz"] = "Kz. 81"
            item["effect"] = f"+{net:.2f} EUR (Steuer: {net * 0.19:.2f} EUR)"
            outgoing_line_items["UST_19"].append(item)

        elif cat == "UST_7":
            kz86 += net
            item["kz"] = "Kz. 86"
            item["effect"] = f"+{net:.2f} EUR (Steuer: {net * 0.07:.2f} EUR)"
            outgoing_line_items["UST_7"].append(item)

        elif cat == "UST_0_EU_B2B":
            kz41 += net
            item["kz"] = "Kz. 41"
            item["effect"] = f"+{net:.2f} EUR (steuerfrei)"
            outgoing_line_items["UST_0_EU_B2B"].append(item)

        elif cat == "UST_0_EXPORT":
            kz43 += net
            item["kz"] = "Kz. 43"
            item["effect"] = f"+{net:.2f} EUR (steuerfrei, Ausfuhr)"
            outgoing_line_items["UST_0_EXPORT"].append(item)

    # ---- Calculate final amounts ----
    kz66 = round(kz66, 2)
    kz67 = round(kz67, 2)
    kz81 = round(kz81, 2)
    kz86 = round(kz86, 2)
    kz89 = round(kz89, 2)
    kz41 = round(kz41, 2)
    kz43 = round(kz43, 2)
    kz46 = round(kz46, 2)
    kz47 = round(kz47, 2)

    output_tax = round(kz81 * 0.19 + kz86 * 0.07 + kz89 * 0.19 + kz47, 2)
    input_tax = round(kz66 + kz67, 2)
    kz83 = round(output_tax - input_tax, 2)

    # Total invoice stats
    total_income_net = sum(
        float(inv.get("amount_net", 0))
        for inv in outgoing_invoices
        if inv.get("status") != "deleted"
    )
    total_expenses_net = sum(
        float(inv.get("amount_net", 0))
        for inv in incoming_invoices
        if inv.get("status") not in ("deleted", "to_review")
    )
    total_vst_reclaimed = round(kz66 + kz67, 2)

    return {
        "quarter": quarter,
        "year": year,
        "period_label": f"Q{quarter}/{year}",
        "calculated_at": datetime.utcnow().isoformat(),

        # ELSTER Kennzahlen
        "kz41": kz41,
        "kz43": kz43,
        "kz46": kz46,
        "kz47": kz47,
        "kz66": kz66,
        "kz67": kz67,
        "kz81": kz81,
        "kz86": kz86,
        "kz89": kz89,
        "kz83": kz83,

        # Derived
        "output_tax": output_tax,
        "input_tax": input_tax,
        "result_type": "Zahllast" if kz83 > 0 else ("Überschuss" if kz83 < 0 else "Ausgeglichen"),
        "result_label": (
            f"{abs(kz83):.2f} EUR an Finanzamt zahlen" if kz83 > 0
            else f"{abs(kz83):.2f} EUR Erstattung" if kz83 < 0
            else "Keine Zahlung"
        ),

        # Summary stats
        "total_income_net": round(total_income_net, 2),
        "total_expenses_net": round(total_expenses_net, 2),
        "total_vst_reclaimed": total_vst_reclaimed,

        # Invoice counts
        "income_invoice_count": len([i for i in outgoing_invoices if i.get("status") != "deleted"]),
        "expense_invoice_count": len([i for i in incoming_invoices if i.get("status") not in ("deleted", "to_review")]),

        # Detailed line items
        "incoming_by_category": line_items,
        "outgoing_by_category": outgoing_line_items,
    }


def format_elster_summary(result: dict) -> str:
    """Generate human-readable ELSTER summary for Mein ELSTER manual entry."""
    lines = [
        f"=== USt-Voranmeldung {result['period_label']} ===",
        f"Erstellt: {result['calculated_at'][:10]}",
        "",
        "--- UMSÄTZE (Ausgangsrechnungen) ---",
        f"Kz. 81 — Steuerpflichtige Umsätze 19%:          {result['kz81']:>12.2f} EUR",
    ]
    if result["kz86"] > 0:
        lines.append(f"Kz. 86 — Steuerpflichtige Umsätze 7%:           {result['kz86']:>12.2f} EUR")
    if result["kz41"] > 0:
        lines.append(f"Kz. 41 — Steuerfreie EU-Lieferungen:             {result['kz41']:>12.2f} EUR")
    if result["kz43"] > 0:
        lines.append(f"Kz. 43 — Steuerfreie Ausfuhrlieferungen:         {result['kz43']:>12.2f} EUR")
    if result["kz89"] > 0:
        lines.append(f"Kz. 89 — Innergemeinschaftl. Erwerbe 19%:        {result['kz89']:>12.2f} EUR")
    if result["kz46"] > 0:
        lines.append(f"Kz. 46 — §13b Leistungen (Bemessungsgrdl.):      {result['kz46']:>12.2f} EUR")
    if result["kz47"] > 0:
        lines.append(f"Kz. 47 — Steuer §13b (Kz.46 × 19%):             {result['kz47']:>12.2f} EUR")

    lines += [
        "",
        "--- VORSTEUER (Eingangsrechnungen) ---",
        f"Kz. 66 — Abziehbare Vorsteuer (inl. 19%/7%):    {result['kz66']:>12.2f} EUR",
    ]
    if result["kz67"] > 0:
        lines.append(f"Kz. 67 — Vorsteuer §13b (EU + Drittland):        {result['kz67']:>12.2f} EUR")

    ust_output = result["kz81"] * 0.19 + result["kz86"] * 0.07
    lines += [
        "",
        "--- BERECHNUNG ---",
        f"Umsatzsteuer (Kz.81×19% + Kz.86×7%):            {ust_output:>12.2f} EUR",
        f"+ EU-Erwerbsteuer (Kz.89×19%):                   {result['kz89'] * 0.19:>12.2f} EUR",
        f"+ §13b-Steuer (Kz.47):                           {result['kz47']:>12.2f} EUR",
        f"= Gesamte Umsatzsteuer:                          {result['output_tax']:>12.2f} EUR",
        f"- Abziehbare Vorsteuer (Kz.66+67):               {result['input_tax']:>12.2f} EUR",
        "                                                  ─────────────",
        f"Kz. 83 — {result['result_type']:30s}   {result['kz83']:>12.2f} EUR",
        "",
        f">>> {result['result_label'].upper()} <<<",
    ]
    return "\n".join(lines)


def generate_elster_xml(result: dict, business_info: dict = None) -> str:
    """
    Generate simplified ELSTER-compatible XML for USt-Voranmeldung.
    This is a representative structure — the actual Mein ELSTER XML schema
    varies by year; use this as a human-readable reference.
    """
    if business_info is None:
        business_info = {
            "name": "Muster GmbH",
            "tax_number": "12/345/67890",
            "vat_id": "DE123456789",
        }

    root = ET.Element("UStVA")
    root.set("version", "2024")
    root.set("generated", result.get("calculated_at", ""))

    # Header
    header = ET.SubElement(root, "Header")
    ET.SubElement(header, "Steuerpflichtiger").text = business_info.get("name", "")
    ET.SubElement(header, "Steuernummer").text = business_info.get("tax_number", "")
    ET.SubElement(header, "UStIdNr").text = business_info.get("vat_id", "")
    ET.SubElement(header, "Zeitraum").text = result.get("period_label", "")
    ET.SubElement(header, "Jahr").text = str(result.get("year", 2024))
    ET.SubElement(header, "Quartal").text = str(result.get("quarter", 1))

    # Umsätze
    umsaetze = ET.SubElement(root, "Umsaetze")
    kz = ET.SubElement(umsaetze, "Kz81")
    kz.set("beschreibung", "Steuerpflichtige Umsätze 19%")
    kz.text = f"{result['kz81']:.2f}"

    if result["kz86"] > 0:
        kz = ET.SubElement(umsaetze, "Kz86")
        kz.set("beschreibung", "Steuerpflichtige Umsätze 7%")
        kz.text = f"{result['kz86']:.2f}"

    if result["kz41"] > 0:
        kz = ET.SubElement(umsaetze, "Kz41")
        kz.set("beschreibung", "Steuerfreie innergemeinschaftliche Lieferungen")
        kz.text = f"{result['kz41']:.2f}"

    if result["kz43"] > 0:
        kz = ET.SubElement(umsaetze, "Kz43")
        kz.set("beschreibung", "Steuerfreie Ausfuhrlieferungen")
        kz.text = f"{result['kz43']:.2f}"

    if result["kz89"] > 0:
        kz = ET.SubElement(umsaetze, "Kz89")
        kz.set("beschreibung", "Innergemeinschaftliche Erwerbe 19%")
        kz.text = f"{result['kz89']:.2f}"

    if result["kz46"] > 0:
        kz = ET.SubElement(umsaetze, "Kz46")
        kz.set("beschreibung", "§13b Leistungen Bemessungsgrundlage")
        kz.text = f"{result['kz46']:.2f}"

    if result["kz47"] > 0:
        kz = ET.SubElement(umsaetze, "Kz47")
        kz.set("beschreibung", "Steuer aus §13b-Leistungen")
        kz.text = f"{result['kz47']:.2f}"

    # Vorsteuer
    vorsteuer = ET.SubElement(root, "Vorsteuer")
    kz = ET.SubElement(vorsteuer, "Kz66")
    kz.set("beschreibung", "Abziehbare Vorsteuerbeträge")
    kz.text = f"{result['kz66']:.2f}"

    if result["kz67"] > 0:
        kz = ET.SubElement(vorsteuer, "Kz67")
        kz.set("beschreibung", "Vorsteuer aus §13b-Leistungen")
        kz.text = f"{result['kz67']:.2f}"

    # Ergebnis
    ergebnis = ET.SubElement(root, "Ergebnis")
    kz83 = ET.SubElement(ergebnis, "Kz83")
    kz83.set("beschreibung", result.get("result_type", ""))
    kz83.text = f"{result['kz83']:.2f}"

    ET.SubElement(ergebnis, "Umsatzsteuer").text = f"{result['output_tax']:.2f}"
    ET.SubElement(ergebnis, "Vorsteuer").text = f"{result['input_tax']:.2f}"

    return ET.tostring(root, encoding="unicode", xml_declaration=False)
