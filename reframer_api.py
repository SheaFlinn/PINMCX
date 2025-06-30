# reframer_api.py

import json
import openai
import os
from datetime import datetime
from time import sleep

# -------------- CONFIG -----------------
INPUT_PATH = "drafts/draft_contracts.json"
OUTPUT_PATH = "drafts/reframed_contracts.json"
OPENAI_MODEL = "gpt-4"
openai.api_key = os.getenv("OPENAI_API_KEY")
# --------------------------------------

PROMPT_TEMPLATE = """
You are a civic contract generator for a municipal prediction market.

Your job is to convert raw local news headlines into formal, binary civic prediction contracts. Use only forecastable, verifiable, time-bounded outcomes. Avoid vague or subjective language. Structure the output using the five fields below:

1. **title**: Short phrasing of the civic prediction
2. **purpose**: Why this question matters for the city
3. **scope**: What the contract includes and excludes
4. **terms**: Clear YES/NO resolution rules
5. **source_url**: Original news article URL

Always structure the contract to make the outcome realistically uncertain—ideally around 50/50.

### EXAMPLE INPUT
City: Memphis  
Headline: "City Council approves $8M bond for drainage improvements"  
Source: Daily Memphian  
Date: 2025-06-28  
URL: https://example.com/story

### EXAMPLE OUTPUT
{{
  "title": "Will the Memphis City Council approve the $8M drainage bond by August 1?",
  "purpose": "This contract forecasts whether the City Council will formally approve an $8M bond package intended to fund drainage and flood infrastructure upgrades in identified neighborhoods...",
  "scope": "This contract only applies to the formal vote of approval for the bond in its current form, not subsequent amendments or implementation delays...",
  "terms": {{
    "YES": "If the City Council votes to approve the full bond package by August 1, 2025.",
    "NO": "If the Council does not vote, or rejects the proposal, by August 1.",
    "resolution_source": "https://example.com/story"
  }},
  "source_url": "https://example.com/story"
}}

### END INSTRUCTIONS
Now reframe this input:

City: {city}  
Headline: "{headline}"  
Source: {source}  
Date: {date}  
URL: {url}
"""

def reframe_entry(entry):
    prompt = PROMPT_TEMPLATE.format(
        city=entry["city"],
        headline=entry["headline"],
        source=entry["source"],
        date=entry["date"],
        url=entry["url"]
    )

    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        output_text = response.choices[0].message.content.strip()
        # Assume model returns valid JSON
        return json.loads(output_text)
    except Exception as e:
        print(f"Error reframing headline: {entry['headline']}")
        print(str(e))
        return None

def main():
    with open(INPUT_PATH, "r") as f:
        drafts = json.load(f)

    reframed = []

    for entry in drafts:
        print(f"Reframing: {entry['headline']}")
        contract = reframe_entry(entry)
        if contract:
            contract["city"] = entry["city"]
            contract["status"] = "draft"
            reframed.append(contract)
            sleep(1.2)  # avoid rate limits

    with open(OUTPUT_PATH, "w") as f:
        json.dump(reframed, f, indent=2)

    print(f"✅ Reframed {len(reframed)} contracts saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
