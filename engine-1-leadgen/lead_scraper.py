import httpx
from bs4 import BeautifulSoup
import json
import os
import re

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

MOCK_LEADS = [
    {
        "company_name": "Digitale Zukunft GmbH",
        "website": "https://digitale-zukunft-berlin.de",
        "contact_name": "Thomas Becker",
        "role": "Geschäftsführer",
        "email": "t.becker@digitale-zukunft-berlin.de",
        "phone": "+49 30 2345 6789",
        "notes": "Berliner IT-Dienstleister mit 45 Mitarbeitern – aktiv auf Wachstumskurs. Manuelle Reporting-Prozesse kosten wöchentlich mehrere Stunden. Perfekter Kandidat für KI-Automatisierung.",
        "source": "Demo-Daten",
    },
    {
        "company_name": "Brandenburg Consulting AG",
        "website": "https://bb-consulting.de",
        "contact_name": "Dr. Sabine Hoffmann",
        "role": "Vorstandsvorsitzende",
        "email": "s.hoffmann@bb-consulting.de",
        "phone": "+49 331 8765 4321",
        "notes": "Führende Unternehmensberatung in Potsdam mit Schwerpunkt Mittelstand. Bietet klassische Beratung an, jedoch noch ohne KI-gestützte Analysetools. Große Chance für Effizienzsteigerung.",
        "source": "Demo-Daten",
    },
    {
        "company_name": "Havelland Industrie Service GmbH",
        "website": "https://havelland-industrie.de",
        "contact_name": "Klaus-Dieter Schulz",
        "role": "Inhaber & Geschäftsführer",
        "email": "info@havelland-industrie.de",
        "phone": "+49 3386 701 234",
        "notes": "Mittelständischer Industriedienstleister in Rathenow mit 80 Mitarbeitern. Vertriebsteam arbeitet noch mit Excel – enormes Potenzial für CRM-Automatisierung und KI-Leadgenerierung.",
        "source": "Demo-Daten",
    },
    {
        "company_name": "Spree Valley IT Solutions",
        "website": "https://spreevalley-it.de",
        "contact_name": "Markus Zimmermann",
        "role": "CEO & Co-Founder",
        "email": "m.zimmermann@spreevalley-it.de",
        "phone": "+49 3375 2198 44",
        "notes": "Wachstumsstarkes IT-Unternehmen aus Königs Wusterhausen. Entwickelt Software für Logistik-Kunden, kämpft aber mit manuellem Vertrieb. Explizit auf der Suche nach Automatisierungslösungen.",
        "source": "Demo-Daten",
    },
    {
        "company_name": "Berliner Handwerk Digital GmbH",
        "website": "https://berliner-handwerk-digital.de",
        "contact_name": "Andreas Krause",
        "role": "Geschäftsführer",
        "email": "a.krause@berliner-handwerk-digital.de",
        "phone": "+49 30 9876 5432",
        "notes": "Plattform für die Digitalisierung von Handwerksbetrieben in Berlin. 120+ Kunden, aber Kundenakquise noch vollständig manuell. Sehr offen für KI-Lösungen laut LinkedIn-Aktivität.",
        "source": "Demo-Daten",
    },
    {
        "company_name": "Smart Factory Solutions GmbH",
        "website": "https://smart-factory-solutions.de",
        "contact_name": "Petra Neumann",
        "role": "Head of Digital Transformation",
        "email": "p.neumann@smart-factory-solutions.de",
        "phone": "+49 3301 5678 90",
        "notes": "Industrie-4.0-Spezialist aus Oranienburg mit 60 Mitarbeitern. Bekannter Schmerzpunkt: Datenerfassung in der Produktion noch nicht automatisiert. Aktiver Content zu KI auf ihrem Blog.",
        "source": "Demo-Daten",
    },
    {
        "company_name": "Nordost Digital Ventures",
        "website": "https://nordost-digital.de",
        "contact_name": "Stefan Lange",
        "role": "Managing Director",
        "email": "s.lange@nordost-digital.de",
        "phone": "+49 335 2234 567",
        "notes": "Digitalberatung aus Frankfurt (Oder) mit Fokus auf KMU der Region. Arbeitet mit 30+ Mittelstandskunden zusammen, nutzt aber noch klassische Tools für Projektmanagement.",
        "source": "Demo-Daten",
    },
    {
        "company_name": "ProzessketteTech AG",
        "website": "https://prozesskette-tech.de",
        "contact_name": "Julia Wagner",
        "role": "Vorstand Operations",
        "email": "j.wagner@prozesskette-tech.de",
        "phone": "+49 331 4455 6677",
        "notes": "Spezialist für Prozessoptimierung in Potsdam, bedient vor allem Logistik- und Fertigungsunternehmen. Kürzlich auf LinkedIn gepostet: 'KI ist die Zukunft der Prozessoptimierung'.",
        "source": "Demo-Daten",
    },
    {
        "company_name": "BerlinBrand Agency GmbH",
        "website": "https://berlinbrand-agency.de",
        "contact_name": "Robert Fischer",
        "role": "Gründer & CEO",
        "email": "r.fischer@berlinbrand-agency.de",
        "phone": "+49 30 1234 8765",
        "notes": "Performance-Marketing-Agentur in Berlin-Mitte mit 25 Mitarbeitern. Kunden fragen nach KI-gestützten Kampagnen-Analysen – Agentur hat noch keine entsprechende Lösung integriert.",
        "source": "Demo-Daten",
    },
    {
        "company_name": "Mittelstand Digital Hub GmbH",
        "website": "https://mittelstand-digital-hub.de",
        "contact_name": "Claudia Richter",
        "role": "Geschäftsführerin",
        "email": "c.richter@mittelstand-digital-hub.de",
        "phone": "+49 355 7788 9900",
        "notes": "Netzwerk und Accelerator für mittelständische Unternehmen in Cottbus. Begleitet Digitalisierungsprojekte, aber kein eigenes KI-Toolset. Sehr hohe Kaufbereitschaft für bewährte Lösungen.",
        "source": "Demo-Daten",
    },
]


async def scrape_impressum(website: str, client: httpx.AsyncClient) -> dict:
    result = {"email": None, "phone": None, "contact_name": None}
    paths = ["/impressum", "/kontakt", "/contact", "/about", "/ueber-uns", "/team"]

    for path in paths:
        try:
            url = website.rstrip("/") + path
            resp = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; BrainlancerBot/1.0)"},
                timeout=8,
            )
            if resp.status_code != 200:
                continue

            text = resp.text

            if not result["email"]:
                emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
                ignore = {"noreply", "no-reply", "mailer", "postmaster", "webmaster", "support", "info@example"}
                for e in emails:
                    if not any(ign in e.lower() for ign in ignore):
                        result["email"] = e
                        break

            if not result["phone"]:
                phones = re.findall(
                    r"(?:\+49|0049|0)\s*[\d\s\-/()]{7,20}",
                    text,
                )
                if phones:
                    result["phone"] = re.sub(r"\s+", " ", phones[0]).strip()

            if not result["contact_name"]:
                patterns = [
                    r"Geschäftsführer(?:in)?[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
                    r"Inhaber(?:in)?[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
                    r"CEO[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
                    r"Gründer(?:in)?[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
                ]
                for pat in patterns:
                    m = re.search(pat, text)
                    if m:
                        result["contact_name"] = m.group(1).strip()
                        break

            if result["email"] and result["phone"]:
                break

        except Exception:
            continue

    return result


async def gemini_find_leads(icp_data: dict) -> list:
    import google.generativeai as genai

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""Finde 10 reale deutsche B2B-Unternehmen, die zu diesem Ideal Customer Profile passen.

ICP:
- Branche: {icp_data.get("industry")}
- Ziel-Jobtitel: {", ".join(icp_data.get("titles", []))}
- Region: {icp_data.get("location", "DACH-Region")}
- Unternehmensgröße: {icp_data.get("company_size_min", 10)}–{icp_data.get("company_size_max", 200)} Mitarbeiter
- Schmerzpunkte: {", ".join(icp_data.get("pain_signals", []))}
- Kundenbeschreibung: {icp_data.get("description", "")}

Antworte NUR mit einem JSON-Array mit 10 Unternehmen:
[
  {{
    "company_name": "Echter Unternehmensname GmbH",
    "website": "https://example.de",
    "contact_name": "Name oder 'Geschäftsführung'",
    "role": "Geschäftsführer",
    "email": "N/A",
    "phone": "N/A",
    "notes": "Warum dieses Unternehmen ein perfekter Fit ist – konkrete Begründung",
    "source": "Gemini Research"
  }}
]

Nur reale, verifizierbare deutsche Unternehmen. Fokus auf DACH-Region.
Keine B2C-Unternehmen. Keine Konzerne. Mittelstand bevorzugt."""

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(temperature=0.1, max_output_tokens=2048),
    )

    text = response.text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return json.loads(text)


async def find_leads(icp_data: dict) -> list:
    if not GOOGLE_API_KEY:
        return MOCK_LEADS

    try:
        leads = await gemini_find_leads(icp_data)
        leads = leads[:10]

        # Enrich with Impressum data
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for lead in leads:
                if not lead.get("website") or lead["website"] == "N/A":
                    continue
                impressum = await scrape_impressum(lead["website"], client)
                if impressum["email"] and (not lead.get("email") or lead["email"] == "N/A"):
                    lead["email"] = impressum["email"]
                if impressum["phone"] and (not lead.get("phone") or lead["phone"] == "N/A"):
                    lead["phone"] = impressum["phone"]
                if impressum["contact_name"] and (
                    not lead.get("contact_name") or lead["contact_name"] == "Geschäftsführung"
                ):
                    lead["contact_name"] = impressum["contact_name"]

        return leads

    except Exception:
        return MOCK_LEADS
