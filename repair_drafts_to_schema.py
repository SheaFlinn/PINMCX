import json
import os
from datetime import datetime

INPUT_PATH = "drafts/draft_contracts.json"
OUTPUT_PATH = "drafts/draft_contracts.json"

def convert(entry):
    return {
        "headline": entry.get("refined_title") or entry.get("title"),
        "url": entry.get("source_url"),
        "source": entry.get("source_name"),
        "city": "Memphis",
        "date": entry.get("source_date")[:10] if entry.get("source_date") else None
    }

def is_valid(entry):
    return all(entry.get(k) for k in ["headline", "url", "source", "city", "date"])

def main():
    with open(INPUT_PATH, "r") as f:
        raw = json.load(f)

    cleaned = [convert(e) for e in raw if is_valid(convert(e))]

    with open(OUTPUT_PATH, "w") as f:
        json.dump(cleaned, f, indent=2)

    print(f"✅ Overwrote {OUTPUT_PATH} with {len(cleaned)} cleaned entries.")

if __name__ == "__main__":
    main()

