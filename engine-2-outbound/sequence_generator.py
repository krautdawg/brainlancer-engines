import os
import json
import re
import google.generativeai as genai
from typing import List, Dict

TONE_DESCRIPTIONS = {
    "formal": "professional, respectful, businesslike German B2B tone",
    "casual": "friendly, conversational, approachable but still professional",
    "provocative": "bold, direct, challenges assumptions, thought-provoking",
}

GOAL_DESCRIPTIONS = {
    "meeting": "book an introductory meeting",
    "demo": "schedule a product demo",
    "call": "arrange a brief discovery call",
    "reply": "get a reply and start a conversation",
}

EMAIL_ANGLES = [
    "initial outreach with core value proposition",
    "social proof with customer success story",
    "specific pain-point / challenge angle",
    "urgency / limited window angle",
    "breakup email — final respectful attempt",
]


def _get_model():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")


def generate_sequence(lead: Dict, campaign: Dict) -> List[Dict]:
    """Call Gemini Flash to generate a personalized email sequence for one lead."""
    model = _get_model()

    cadence_days = [int(d.strip()) for d in campaign["cadence"].split(",")]
    num_tp = int(campaign["num_touchpoints"])
    tone_desc = TONE_DESCRIPTIONS.get(campaign["tone"], TONE_DESCRIPTIONS["formal"])
    goal_desc = GOAL_DESCRIPTIONS.get(campaign["goal"], GOAL_DESCRIPTIONS["meeting"])
    angles = EMAIL_ANGLES[:num_tp]

    company = lead.get("company") or "Unknown Company"
    contact = lead.get("contact") or "Entscheidungsträger"
    website = lead.get("website") or ""
    notes = lead.get("notes") or ""

    angles_text = "\n".join(
        f"  Email {i+1} (Day {cadence_days[i] if i < len(cadence_days) else (i+1)*3}): {angles[i]}"
        for i in range(num_tp)
    )

    prompt = f"""You are an expert B2B sales copywriter specializing in German-language outbound campaigns.

Generate a {num_tp}-email outbound sequence for this prospect.

PROSPECT:
- Company: {company}
- Contact: {contact}
- Website: {website if website else "not provided"}
- Notes: {notes if notes else "none"}

CAMPAIGN SETTINGS:
- Sender: {campaign["sender_name"]} ({campaign["sender_email"]})
- Tone: {tone_desc}
- Goal: {goal_desc}

EMAIL PLAN (use different angle per email):
{angles_text}

INSTRUCTIONS:
- Write entirely in fluent, natural German (Hochdeutsch)
- Each email: 150–250 words
- Personalize using company/contact details
- One clear CTA per email
- Subject lines: intriguing, not spammy, max 60 chars
- No markdown formatting in body — plain text only

Return ONLY a valid JSON array, no explanation:
[
  {{
    "touchpoint_num": 1,
    "scheduled_day": {cadence_days[0] if cadence_days else 1},
    "subject": "...",
    "body": "..."
  }}
]"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    sequences = json.loads(raw)

    # Enforce scheduled_days from campaign cadence
    for i, seq in enumerate(sequences):
        if i < len(cadence_days):
            seq["scheduled_day"] = cadence_days[i]
        seq["touchpoint_num"] = i + 1

    return sequences[:num_tp]
