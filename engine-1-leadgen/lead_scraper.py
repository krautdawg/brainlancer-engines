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
        "role": "Managing Director",
        "email": "t.becker@digitale-zukunft-berlin.de",
        "phone": "+49 30 2345 6789",
        "notes": "Berlin-based IT services company with 45 employees and clear growth momentum. Manual reporting still consumes several hours each week. Strong fit for AI automation.",
        "source": "Demo Data",
    },
    {
        "company_name": "Brandenburg Consulting AG",
        "website": "https://bb-consulting.de",
        "contact_name": "Dr. Sabine Hoffmann",
        "role": "Chief Executive Officer",
        "email": "s.hoffmann@bb-consulting.de",
        "phone": "+49 331 8765 4321",
        "notes": "Established consulting firm in Potsdam focused on mid-market clients. Still delivers mostly traditional consulting services without AI-driven analytics. Clear upside in efficiency and differentiation.",
        "source": "Demo Data",
    },
    {
        "company_name": "Havelland Industrie Service GmbH",
        "website": "https://havelland-industrie.de",
        "contact_name": "Klaus-Dieter Schulz",
        "role": "Owner & Managing Director",
        "email": "info@havelland-industrie.de",
        "phone": "+49 3386 701 234",
        "notes": "Mid-sized industrial services provider in Rathenow with 80 employees. The sales team still relies heavily on Excel, creating strong potential for CRM automation and AI-supported lead generation.",
        "source": "Demo Data",
    },
    {
        "company_name": "Spree Valley IT Solutions",
        "website": "https://spreevalley-it.de",
        "contact_name": "Markus Zimmermann",
        "role": "CEO & Co-Founder",
        "email": "m.zimmermann@spreevalley-it.de",
        "phone": "+49 3375 2198 44",
        "notes": "Fast-growing IT company from Koenigs Wusterhausen building software for logistics clients. Sales is still largely manual, and the company is actively looking for automation opportunities.",
        "source": "Demo Data",
    },
    {
        "company_name": "Berliner Handwerk Digital GmbH",
        "website": "https://berliner-handwerk-digital.de",
        "contact_name": "Andreas Krause",
        "role": "Managing Director",
        "email": "a.krause@berliner-handwerk-digital.de",
        "phone": "+49 30 9876 5432",
        "notes": "Platform helping trade businesses digitize operations across Berlin. It serves more than 120 customers, but customer acquisition is still fully manual. Public activity suggests high openness to AI solutions.",
        "source": "Demo Data",
    },
    {
        "company_name": "Smart Factory Solutions GmbH",
        "website": "https://smart-factory-solutions.de",
        "contact_name": "Petra Neumann",
        "role": "Head of Digital Transformation",
        "email": "p.neumann@smart-factory-solutions.de",
        "phone": "+49 3301 5678 90",
        "notes": "Industry 4.0 specialist in Oranienburg with 60 employees. A known pain point is that shop-floor data capture is still not automated. Their blog shows active interest in AI topics.",
        "source": "Demo Data",
    },
    {
        "company_name": "Nordost Digital Ventures",
        "website": "https://nordost-digital.de",
        "contact_name": "Stefan Lange",
        "role": "Managing Director",
        "email": "s.lange@nordost-digital.de",
        "phone": "+49 335 2234 567",
        "notes": "Digital advisory firm in Frankfurt (Oder) focused on regional SMEs. It already works with more than 30 mid-market clients but still depends on conventional project management tooling.",
        "source": "Demo Data",
    },
    {
        "company_name": "ProzessketteTech AG",
        "website": "https://prozesskette-tech.de",
        "contact_name": "Julia Wagner",
        "role": "Chief Operating Officer",
        "email": "j.wagner@prozesskette-tech.de",
        "phone": "+49 331 4455 6677",
        "notes": "Process optimization specialist in Potsdam serving logistics and manufacturing clients. The team recently posted publicly that AI is the future of process optimization, which signals strong strategic fit.",
        "source": "Demo Data",
    },
    {
        "company_name": "BerlinBrand Agency GmbH",
        "website": "https://berlinbrand-agency.de",
        "contact_name": "Robert Fischer",
        "role": "Founder & CEO",
        "email": "r.fischer@berlinbrand-agency.de",
        "phone": "+49 30 1234 8765",
        "notes": "Performance marketing agency in central Berlin with 25 employees. Clients are already asking for AI-assisted campaign analytics, but the agency has not yet integrated a suitable solution.",
        "source": "Demo Data",
    },
    {
        "company_name": "Mittelstand Digital Hub GmbH",
        "website": "https://mittelstand-digital-hub.de",
        "contact_name": "Claudia Richter",
        "role": "Managing Director",
        "email": "c.richter@mittelstand-digital-hub.de",
        "phone": "+49 355 7788 9900",
        "notes": "Network and accelerator for mid-sized companies in Cottbus. It supports digitization projects but does not yet offer its own AI toolkit. Purchase intent for proven solutions is likely high.",
        "source": "Demo Data",
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

    prompt = f"""Find 10 real German B2B companies that match this Ideal Customer Profile.

ICP:
- Industry: {icp_data.get("industry")}
- Target job titles: {", ".join(icp_data.get("titles", []))}
- Region: {icp_data.get("location", "DACH region")}
- Company size: {icp_data.get("company_size_min", 10)}-{icp_data.get("company_size_max", 200)} employees
- Pain signals: {", ".join(icp_data.get("pain_signals", []))}
- Customer description: {icp_data.get("description", "")}

Respond ONLY with a JSON array containing 10 companies:
[
  {{
    "company_name": "Real company name GmbH",
    "website": "https://example.de",
    "contact_name": "Name or 'Management'",
    "role": "Managing Director",
    "email": "N/A",
    "phone": "N/A",
    "notes": "Why this company is a strong fit - concrete justification",
    "source": "Gemini Research"
  }}
]

Only include real, verifiable German companies. Focus on the DACH region.
No B2C companies. No large enterprises. Prefer mid-market businesses."""

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
                    not lead.get("contact_name") or lead["contact_name"] == "Management"
                ):
                    lead["contact_name"] = impressum["contact_name"]

        return leads

    except Exception:
        return MOCK_LEADS
