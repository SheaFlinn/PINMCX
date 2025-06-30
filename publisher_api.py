import json
import os
import sys
from typing import Dict, List, Any

def filter_and_publish_contracts(input_path: str) -> None:
    """Filter contracts and publish with initial liquidity."""
    # Load input contracts
    try:
        with open(input_path, 'r') as f:
            contracts = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Input file not found: {input_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in input file: {input_path}")
        sys.exit(1)

    # Filter contracts with detailed logging
    filtered_contracts = []
    total_contracts = len(contracts)
    strong_medium_count = 0
    unbiased_count = 0
    
    for contract in contracts:
        weight = contract.get("weight", "")
        bias = contract.get("bias", True)
        
        # Log filtering criteria
        print(f"🔍 Processing contract: {contract.get('title', 'Untitled')}")
        print(f"  Weight: {weight}")
        print(f"  Bias: {bias}")
        
        if weight in ["strong", "medium"]:
            strong_medium_count += 1
        if not bias:
            unbiased_count += 1
            
        if weight in ["strong", "medium"] and not bias:
            # Add initial liquidity
            contract["total_yes"] = 100
            contract["total_no"] = 100
            filtered_contracts.append(contract)
            print(f"✅ Added contract: {contract.get('title', 'Untitled')}")
        else:
            print(f"❌ Skipped contract: {contract.get('title', 'Untitled')}")
            if weight not in ["strong", "medium"]:
                print("  ✗ Failed weight check")
            if bias:
                print("  ✗ Failed bias check")

    print("\n=== Summary ===")
    print(f"🔍 Total contracts processed: {total_contracts}")
    print(f"🔍 Contracts with strong/medium weight: {strong_medium_count}")
    print(f"🔍 Unbiased contracts: {unbiased_count}")
    print(f"✅ Published contracts: {len(filtered_contracts)}")

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname("live/published_contracts.json"), exist_ok=True)

    # Write filtered contracts
    try:
        with open("live/published_contracts.json", 'w') as f:
            json.dump(filtered_contracts, f, indent=2)
        print("✅ Contracts written to live/published_contracts.json")
    except Exception as e:
        print(f"❌ Error writing output file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❌ Error: Usage: python3 publisher_api.py <input_file>")
        print("Example: python3 publisher_api.py drafts/balanced_contracts.json")
        sys.exit(1)

    input_path = sys.argv[1]
    filter_and_publish_contracts(input_path)
