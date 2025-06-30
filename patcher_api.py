import json
import openai
import os
from typing import Dict, List
from datetime import datetime

# -------------- CONFIG -----------------
INPUT_PATH = "drafts/reframed_contracts.json"
OUTPUT_PATH = "drafts/patched_contracts.json"
OPENAI_MODEL = "gpt-4"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set API key
openai.api_key = OPENAI_API_KEY

# --------------------------------------

PROMPT_TEMPLATE = """
You are a prediction market question formatter.

Your job is to convert the following civic issue into a prediction market question with a binary 50/50 framing suitable for betting odds. Make it objective, testable, and future-dated.

### EXAMPLE INPUT
{refined_title}

### EXAMPLE OUTPUT
Will the civic issue be resolved by [future date]?

### END INSTRUCTIONS
Now reframe this input:
{refined_title}
"""

def patch_entry(entry: Dict) -> Dict:
    """
    Use OpenAI to convert a civic question into a 50/50 prediction market question.
    Accepts either 'title' or 'refined_title' as input.
    """
    # Try to get the title from either field
    title_key = "refined_title" if "refined_title" in entry else "title"
    if title_key not in entry:
        print(f"Error: Entry missing title: {entry}")
        return None

    prompt = PROMPT_TEMPLATE.format(
        refined_title=entry[title_key]
    )

    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        patched_title = response.choices[0].message.content.strip()
        
        # Create new entry with patched title
        patched_entry = entry.copy()
        patched_entry["patched_title"] = patched_title
        
        return patched_entry
    except Exception as e:
        print(f"Error patching entry: {str(e)}")
        return None

def main() -> None:
    """
    Main function to process all contracts and generate patched versions.
    """
    if not os.path.exists(INPUT_PATH):
        print(f"❌ Input file not found: {INPUT_PATH}")
        return

    try:
        with open(INPUT_PATH, "r") as f:
            contracts = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    if not isinstance(contracts, list):
        print(f"❌ Invalid input format: Expected list, got {type(contracts)}")
        return

    patched_contracts = []
    skipped_count = 0

    for contract in contracts:
        if not isinstance(contract, dict):
            print(f"⚠️ Skipping non-dict entry: {contract}")
            skipped_count += 1
            continue

        patched = patch_entry(contract)
        if patched:
            patched_contracts.append(patched)
        else:
            skipped_count += 1

    # Create output directory if needed
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    with open(OUTPUT_PATH, "w") as f:
        json.dump(patched_contracts, f, indent=2)

    print(f"✅ Processed {len(contracts)} contracts")
    print(f"✅ {len(patched_contracts)} patched contracts written to {OUTPUT_PATH}")
    print(f"⚠️ {skipped_count} contracts skipped")

if __name__ == "__main__":
    main()
