import json
import sys
import re
import random
import os
from typing import List, Dict

# Example swing actors or margin phrases to pull from
SWING_ACTORS = [
    "Councilmember Robinson",
    "the District 3 representative",
    "the Memphis mayor",
    "the city finance committee"
]

MARGIN_PHRASES = [
    "by more than 3 votes",
    "by at least 5% over the target",
    "exceeding $1 million in funding",
    "with a 2/3 majority"
]

def needs_refinement(title: str) -> bool:
    """Check if title needs refinement."""
    # Skip if title already has framing elements
    if re.search(r"by \w+ \d{4}|within \d+|more than|less than|before|after", title, re.IGNORECASE):
        return False
    return True

def apply_refinement(title: str) -> (str, str):
    """Apply random refinement type to title."""
    rand = random.random()
    if rand < 0.33:
        # Margin refinement
        margin = random.choice(MARGIN_PHRASES)
        return f"{title.rstrip('?')} {margin}?", "margin"
    elif rand < 0.66:
        # Swing actor refinement
        actor = random.choice(SWING_ACTORS)
        return f"Will {actor} support this: {title.rstrip('?')}?", "swing"
    else:
        # Timing refinement with plausible random offset
        fallback_date = random.choice(["by July 15", "by August 30", "by October 1"])
        return f"{title.rstrip('?')} {fallback_date}?", "timing"

def refine_contracts(input_path: str, output_path: str):
    """Process and refine contracts."""
    try:
        # Read input file
        print(f"Reading contracts from {input_path}...")
        with open(input_path, 'r', encoding='utf-8') as f:
            contracts = json.load(f)
            
        print(f"Processing {len(contracts)} contracts...")
        
        # Process each contract
        refined_contracts = []
        unchanged_count = 0
        refined_count = 0
        
        for contract in contracts:
            patched_title = contract.get("patched_title", "")
            if not patched_title:
                print("⚠️ Skipping contract with missing patched_title")
                continue
                
            if needs_refinement(patched_title):
                refined, spread_type = apply_refinement(patched_title)
                contract["refined_title"] = refined
                contract["spread_type"] = spread_type
                refined_count += 1
            else:
                contract["refined_title"] = patched_title
                contract["spread_type"] = "none"
                unchanged_count += 1
                
            refined_contracts.append(contract)
            
        # Write output
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(refined_contracts, f, indent=2)
            
        print(f"✅ Processed {len(contracts)} contracts")
        print(f"✅ {unchanged_count} contracts left unchanged")
        print(f"✅ {refined_count} contracts refined")
        print(f"✅ Output written to {output_path}")
            
    except FileNotFoundError:
        print(f"❌ Error: Input file not found: {input_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON format in {input_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 spread_refiner.py <input_file.json>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = "drafts/spread_refined_contracts.json"
    refine_contracts(input_path, output_path)
