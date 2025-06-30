import json
import os
from typing import Dict, List

# Configuration
INPUT_PATH = "drafts/draft_contracts.json"
OUTPUT_PATH = "drafts/cleaned_drafts.json"
REQUIRED_KEYS = ["headline", "url", "source", "city", "date"]

# Common key mappings to fix
KEY_MAPPINGS = {
    "title": "headline",
    "web_url": "url",
    "source_name": "source",
    "city_name": "city",
    "publication_date": "date"
}

# Validation functions
def fix_keys(entry: Dict) -> Dict:
    """
    Attempt to fix common key mismatches in the entry.
    """
    for old_key, new_key in KEY_MAPPINGS.items():
        if old_key in entry and new_key not in entry:
            entry[new_key] = entry.pop(old_key)
    return entry

def is_valid(entry: Dict) -> bool:
    """
    Check if entry has all required keys.
    """
    return all(k in entry for k in REQUIRED_KEYS)

def validate_entry(entry: Dict) -> Dict:
    """
    Validate and clean an entry, returning None if invalid.
    """
    try:
        entry = fix_keys(entry)
        if not is_valid(entry):
            print(f"⚠️ Skipping invalid entry: {entry}")
            return None
        
        # Basic type validation
        if not isinstance(entry["headline"], str):
            print(f"⚠️ Invalid headline type: {entry}")
            return None
        
        if not isinstance(entry["url"], str):
            print(f"⚠️ Invalid URL type: {entry}")
            return None
        
        if not isinstance(entry["source"], str):
            print(f"⚠️ Invalid source type: {entry}")
            return None
        
        if not isinstance(entry["city"], str):
            print(f"⚠️ Invalid city type: {entry}")
            return None
        
        if not isinstance(entry["date"], str):
            print(f"⚠️ Invalid date type: {entry}")
            return None
        
        return entry
    except Exception as e:
        print(f"⚠️ Error validating entry: {str(e)}")
        return None

def main() -> None:
    """
    Main function to clean and validate draft contracts.
    """
    if not os.path.exists(INPUT_PATH):
        print(f"❌ File not found: {INPUT_PATH}")
        return

    try:
        with open(INPUT_PATH, "r") as f:
            drafts = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    if not isinstance(drafts, list):
        print(f"❌ Invalid input format: Expected list, got {type(drafts)}")
        return

    cleaned: List[Dict] = []
    for entry in drafts:
        if not isinstance(entry, dict):
            print(f"⚠️ Skipping non-dict entry: {entry}")
            continue
        
        cleaned_entry = validate_entry(entry)
        if cleaned_entry:
            cleaned.append(cleaned_entry)

    # Create output directory if needed
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    with open(OUTPUT_PATH, "w") as f:
        json.dump(cleaned, f, indent=2)

    print(f"✅ Cleaned {len(cleaned)} valid entries saved to {OUTPUT_PATH}")
    print(f"⚠️ Skipped {len(drafts) - len(cleaned)} invalid entries")

if __name__ == "__main__":
    main()
