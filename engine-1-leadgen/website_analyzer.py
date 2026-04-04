import httpx
from bs4 import BeautifulSoup
import json
import os
import re

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

MOCK_ICP = {
    "company_name": "KI Katapult Demo GmbH",
    "industry": "KI-gestützte Unternehmensberatung",
    "titles": ["Geschäftsführer", "Head of Digital", "IT-Leiter"],
    "location": "Berlin & Brandenburg, DACH-Region",
    "company_size_min": 10,
    "company_size_max": 250,
    "pain_signals": [
        "Manuelle Prozesse bremsen das Wachstum",
        "Fehlende KI-Strategie im Unternehmen",
        "Vertrieb und Marketing nicht automatisiert",
        "Hohe Kosten durch ineffiziente Abläufe",
    ],
    "description": (
        "Mittelständische Unternehmen in der DACH-Region, die ihre Geschäftsprozesse mit KI "
        "automatisieren und skalieren wollen. Typischerweise 10–250 Mitarbeiter, wachstumsorientiert "
        "und offen für digitale Transformation."
    ),
    "website_url": "",
    "is_demo": True,
}


async def scrape_website_content(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; BrainlancerBot/1.0; +https://ki-katapult.de)"},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        meta_desc = ""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            meta_desc = meta.get("content", "").strip()

        headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])[:10]]
        paragraphs = [
            p.get_text(strip=True)
            for p in soup.find_all("p")[:15]
            if len(p.get_text(strip=True)) > 40
        ]

        content = f"Title: {title}\nMeta Description: {meta_desc}\n\n"
        content += "Headings:\n" + "\n".join(f"- {h}" for h in headings if h)
        content += "\n\nContent:\n" + "\n".join(paragraphs)
        return content[:3500]

    except Exception as e:
        return f"Website konnte nicht geladen werden: {str(e)}"


async def analyze_website(url: str) -> dict:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    content = await scrape_website_content(url)

    if not GOOGLE_API_KEY:
        result = MOCK_ICP.copy()
        result["website_url"] = url
        return result

    try:
        import google.generativeai as genai

        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = f"""Analysiere diesen Website-Inhalt und erstelle ein Ideal Customer Profile (ICP) für die B2B-Leadgenerierung.

Website URL: {url}
Website-Inhalt:
{content}

Antworte NUR mit einem JSON-Objekt mit diesen exakten Feldern:
{{
  "company_name": "Name des Unternehmens von der Website",
  "industry": "Branche / Nische des Unternehmens",
  "titles": ["Ziel-Jobtitel 1", "Ziel-Jobtitel 2", "Ziel-Jobtitel 3"],
  "location": "Hauptmarkt / Region (z.B. Berlin, DACH-Region)",
  "company_size_min": 10,
  "company_size_max": 200,
  "pain_signals": [
    "Schmerzpunkt 1 der Zielkunden",
    "Schmerzpunkt 2 der Zielkunden",
    "Schmerzpunkt 3 der Zielkunden",
    "Schmerzpunkt 4 der Zielkunden"
  ],
  "description": "2-3 Sätze: Wer ist die ideale Zielgruppe dieses Unternehmens und warum?",
  "website_url": "{url}"
}}

Fokus: DACH-Region (Deutschland, Österreich, Schweiz). Jobtitel und Schmerzpunkte auf Deutsch."""

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(temperature=0.2, max_output_tokens=1024),
        )

        text = response.text.strip()
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)

        result = json.loads(text)
        result["website_url"] = url
        result["is_demo"] = False
        return result

    except Exception as e:
        result = MOCK_ICP.copy()
        result["website_url"] = url
        result["_error"] = str(e)
        return result
