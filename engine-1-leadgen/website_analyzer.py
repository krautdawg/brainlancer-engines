import httpx
from bs4 import BeautifulSoup
import json
import os
import re

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

MOCK_ICP = {
    "company_name": "KI Katapult Demo Ltd.",
    "industry": "AI-powered business consulting",
    "titles": ["Managing Director", "Head of Digital", "IT Director"],
    "location": "Berlin & Brandenburg, DACH region",
    "company_size_min": 10,
    "company_size_max": 250,
    "pain_signals": [
        "Manual processes are slowing growth",
        "No clear AI strategy across the business",
        "Sales and marketing workflows are not automated",
        "High operating costs caused by inefficient processes",
    ],
    "description": (
        "Mid-market companies in the DACH region that want to automate and scale their business "
        "processes with AI. Typically 10-250 employees, growth-oriented, and open to digital "
        "transformation."
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
        return f"Could not load website: {str(e)}"


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

        prompt = f"""Analyze this website content and create an Ideal Customer Profile (ICP) for B2B lead generation.

Website URL: {url}
Website content:
{content}

Respond ONLY with a JSON object using these exact fields:
{{
  "company_name": "Company name from the website",
  "industry": "Industry / niche of the company",
  "titles": ["Target job title 1", "Target job title 2", "Target job title 3"],
  "location": "Primary market / region (e.g. Berlin, DACH region)",
  "company_size_min": 10,
  "company_size_max": 200,
  "pain_signals": [
    "Pain point 1 of the target customers",
    "Pain point 2 of the target customers",
    "Pain point 3 of the target customers",
    "Pain point 4 of the target customers"
  ],
  "description": "2-3 sentences: Who is this company's ideal target audience and why?",
  "website_url": "{url}"
}}

Focus on the DACH region (Germany, Austria, Switzerland). Return job titles and pain points in English."""

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
