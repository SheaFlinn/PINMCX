import json
import os
from datetime import datetime
from typing import Dict, List

# Configuration
INPUT_PATH = OUTPUT_PATH = "drafts/draft_contracts.json"
REQUIRED_KEYS = ["headline", "url", "source", "city", "date"]
DEFAULT_CITY = "Memphis"

# Key mappings from various formats to our required schema
KEY_MAPPINGS = {
    "refined_title": "headline",
    "original_headline": "headline",
    "source_url": "url",
    "source_name": "source",
    "source_date": "date",
    "publication_date": "date",
    "resolution_date": "date"
}

def convert_date(date_str: str) -> str:
    """
    Convert various date formats to YYYY-MM-DD format.
    Returns None if date cannot be parsed.
    """
    try:
        # Try parsing as ISO format
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        try:
            # Try parsing as timestamp
            dt = datetime.fromtimestamp(float(date_str))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None

def enforce_schema(entry: Dict) -> Dict:
    """
    Enforce strict schema compliance on a single entry.
    Returns None if entry cannot be converted to valid schema.
    """
    try:
        # Create a new clean entry with only required keys
        clean_entry: Dict[str, str] = {}
        
        # Map keys from various formats
        for src_key, dst_key in KEY_MAPPINGS.items():
            if src_key in entry:
                value = entry[src_key]
                if dst_key == "date":
                    date = convert_date(value)
                    if date:
                        clean_entry[dst_key] = date
                elif isinstance(value, str):
                    clean_entry[dst_key] = value
                    
        # Add default city if not present
        if "city" not in clean_entry:
            clean_entry["city"] = DEFAULT_CITY
            
        # Validate that we have all required keys
        if not all(key in clean_entry for key in REQUIRED_KEYS):
            return None
            
        # Ensure all values are strings
        for key in REQUIRED_KEYS:
            if not isinstance(clean_entry[key], str):
                return None
                
        return clean_entry
    except Exception as e:
        print(f"Error enforcing schema on entry: {str(e)}")
        return None

def main() -> None:
    """
    Main function to enforce schema on draft contracts file.
    """
    if not os.path.exists(INPUT_PATH):
        print(f"❌ Input file not found: {INPUT_PATH}")
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

    valid_entries: List[Dict] = []
    invalid_count = 0

    for entry in drafts:
        if not isinstance(entry, dict):
            print(f"⚠️ Skipping non-dict entry: {entry}")
            invalid_count += 1
            continue
            
        clean_entry = enforce_schema(entry)
        if clean_entry:
            valid_entries.append(clean_entry)
        else:
            invalid_count += 1

    # Create output directory if needed
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    with open(OUTPUT_PATH, "w") as f:
        json.dump(valid_entries, f, indent=2)

    print(f"✅ Processed {len(drafts)} entries")
    print(f"✅ {len(valid_entries)} valid entries written to {OUTPUT_PATH}")
    print(f"⚠️ {invalid_count} invalid entries skipped")

if __name__ == "__main__":
    main()
