import json
import sys
import re
import os
from typing import List, Dict

def score_title(title: str) -> str:
    """Score a contract title based on clarity and ambiguity."""
    # Check for missing or broken title
    if not title or not title.strip():
        return "weak"
    
    # Check for question mark at end (required for strong)
    ends_with_question = title.strip().endswith('?')
    
    # Check for vague words
    vague_words = [
        "might",
        "could",
        "possibly",
        "maybe",
        "perhaps",
        "some",
        "several",
        "many"
    ]
    contains_vague = any(word in title.lower() for word in vague_words)
    
    # Determine score based on criteria
    if ends_with_question and not contains_vague:
        return "strong"
    elif not contains_vague:
        return "medium"
    else:
        return "weak"

def weigh_contracts(input_path: str, output_path: str):
    """Process and score contracts."""
    try:
        # Read input file
        print(f"Reading contracts from {input_path}...")
        with open(input_path, 'r', encoding='utf-8') as f:
            contracts = json.load(f)
            
        print(f"Processing {len(contracts)} contracts...")
        
        # Process each contract
        weighted_contracts = []
        scores = {"strong": 0, "medium": 0, "weak": 0}
        
        for contract in contracts:
            refined_title = contract.get("refined_title", "")
            if not refined_title:
                print("⚠️ Skipping contract with missing refined_title")
                continue
                
            # Score the title
            weight = score_title(refined_title)
            contract["weight"] = weight
            scores[weight] += 1
            
            weighted_contracts.append(contract)
            
        # Write output
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(weighted_contracts, f, indent=2)
            
        print(f"✅ Processed {len(contracts)} contracts")
        print(f"✅ Strong: {scores['strong']} contracts")
        print(f"✅ Medium: {scores['medium']} contracts")
        print(f"✅ Weak: {scores['weak']} contracts")
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
        print("Usage: python3 weigher_api.py <input_file.json>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = "drafts/weighted_contracts.json"
    weigh_contracts(input_path, output_path)
