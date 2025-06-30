import json
import sys
import re
import os
from typing import List, Dict

# Expanded list of biased patterns and loaded terms
BIAS_PATTERNS = [
    r"will certainly",
    r"is guaranteed",
    r"will for sure",
    r"is expected to",
    r"is widely believed",
    r"seen as likely",
    r"after approval",
    r"when it happens",
    r"once passed",
    r"as soon as",
    r"survive",
    r"collapse",
    r"fail",
    r"dramatic",
    r"defy",
    r"refuse to"
]

def detect_bias(text: str) -> bool:
    """Detect biased patterns in text using regex."""
    for pattern in BIAS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def clean_bias(text: str) -> str:
    """Clean text by removing biased patterns using regex."""
    cleaned = text
    # Remove each biased pattern
    for pattern in BIAS_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Normalize spacing and punctuation
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Add question mark if missing
    if not cleaned.endswith("?"):
        cleaned += "?"
    
    return cleaned

def process_contracts(contracts: List[Dict]) -> List[Dict]:
    """Process contracts to detect and clean bias."""
    balanced_contracts = []
    biased_count = 0
    
    for contract in contracts:
        title = contract.get("refined_title", "")
        if not title:
            print("⚠️ Skipping contract with missing refined_title")
            continue
            
        if detect_bias(title):
            contract["bias"] = True
            contract["balanced_title"] = clean_bias(title)
            biased_count += 1
        else:
            contract["bias"] = False
            contract["balanced_title"] = title
            
        balanced_contracts.append(contract)
    
    print(f"✅ Processed {len(contracts)} contracts")
    print(f"✅ {biased_count} contracts had bias")
    return balanced_contracts

def write_output(contracts: List[Dict], output_path: str):
    """Write processed contracts to output file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(contracts, f, indent=2)
    print(f"✅ Output written to {output_path}")

def main():
    """Main entry point for script."""
    if len(sys.argv) != 2:
        print("Usage: python3 balancer_api.py <input_file.json>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = "drafts/balanced_contracts.json"
    
    try:
        print(f"Reading contracts from {input_path}...")
        with open(input_path, 'r', encoding='utf-8') as f:
            contracts = json.load(f)
            
        print(f"Processing {len(contracts)} contracts...")
        balanced_contracts = process_contracts(contracts)
        write_output(balanced_contracts, output_path)
            
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
    main()
