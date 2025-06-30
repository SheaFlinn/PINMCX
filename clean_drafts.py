import json
import os

INPUT_PATH = "drafts/draft_contracts.json"
OUTPUT_PATH = "drafts/cleaned_drafts.json"

REQUIRED_KEYS = ["headline", "url", "source", "city", "date"]

def fix_keys(entry):
    # Try renaming likely mismatches
    if "title" in entry and "headline" not in entry:
        entry["headline"] = entry.pop("title")
    return entry

def is_valid(entry):
    return all(k in entry for k in REQUIRED_KEYS)

def main():
    if not os.path.exists(INPUT_PATH):
        print(f"❌ File not found: {INPUT_PATH}")
        return

    with open(INPUT_PATH, "r") as f:
        try:
            drafts = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            return

    cleaned = []
    for entry in drafts:
        entry = fix_keys(entry)
        if is_valid(entry):
            cleaned.append(entry)
        else:
            print(f"⚠️ Skipping invalid entry: {entry}")

    with open(OUTPUT_PATH, "w") as f:
        json.dump(cleaned, f, indent=2)

    print(f"✅ Cleaned {len(cleaned)} entries saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

