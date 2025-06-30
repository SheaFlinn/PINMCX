import json
import sys
import os
from typing import List, Dict

def is_publishable(contract: Dict) -> bool:
    """Check if contract meets publishing criteria."""
    weight = contract.get("weight", "")
    bias = contract.get("bias", False)
    return weight in ["strong", "medium"] and not bias

def publish_contract(contract: Dict) -> Dict:
    """Add status field to contract."""
    contract["status"] = "live"
    return contract

def publish_contracts(input_path: str, output_path: str):
    """Process contracts and publish only those that meet criteria."""
    try:
        print(f"Reading contracts from {input_path}...")
        with open(input_path, 'r', encoding='utf-8') as f:
            contracts = json.load(f)
            
        print(f"Processing {len(contracts)} contracts...")
        
        # Process contracts
        published_contracts = []
        skipped_count = 0
        
        for contract in contracts:
            if is_publishable(contract):
                published_contract = publish_contract(contract)
                published_contracts.append(published_contract)
            else:
                skipped_count += 1
                
        # Write output
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(published_contracts, f, indent=2)
            
        print(f"✅ Processed {len(contracts)} contracts")
        print(f"✅ Published {len(published_contracts)} contracts")
        print(f"✅ Skipped {skipped_count} contracts")
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
        print("Usage: python3 publisher_api.py <input_file.json>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = "live/published_contracts.json"
    publish_contracts(input_path, output_path)
