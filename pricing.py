import json
import sys
import os
from typing import List, Dict
import random

# Price ranges for different contract types
PRICE_RANGES = {
    # Strong weight and no bias: 50/50
    "strong_no_bias": (0.48, 0.52),
    
    # Medium weight: wider spread
    "medium": (0.40, 0.60),
    
    # Margin or swing spread: slight skew
    "margin_swing": (0.47, 0.53)
}

def assign_prices(contract: Dict) -> Dict:
    """Assign realistic debut odds to contract."""
    weight = contract.get("weight", "weak")
    bias = contract.get("bias", True)
    spread_type = contract.get("spread_type", "none")
    
    # Determine price range based on contract characteristics
    if weight == "strong" and not bias:
        price_range = PRICE_RANGES["strong_no_bias"]
    elif weight == "medium":
        price_range = PRICE_RANGES["medium"]
    else:
        price_range = PRICE_RANGES["medium"]  # Default to medium range for other cases
        
    # Slightly skew prices for margin or swing spreads
    if spread_type in ["margin", "swing"]:
        price_range = PRICE_RANGES["margin_swing"]
    
    # Randomly select price within range
    yes_price = random.uniform(*price_range)
    no_price = 1 - yes_price
    
    # Round to 4 decimal places
    yes_price = round(yes_price, 4)
    no_price = round(no_price, 4)
    
    # Add price fields
    contract["yes_price"] = yes_price
    contract["no_price"] = no_price
    
    return contract

def price_contracts(input_path: str, output_path: str):
    """Process contracts and assign prices."""
    try:
        print(f"Reading contracts from {input_path}...")
        with open(input_path, 'r', encoding='utf-8') as f:
            contracts = json.load(f)
            
        print(f"Processing {len(contracts)} contracts...")
        
        # Process each contract
        priced_contracts = []
        
        for contract in contracts:
            priced_contract = assign_prices(contract)
            priced_contracts.append(priced_contract)
            
        # Write output
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(priced_contracts, f, indent=2)
            
        print(f"✅ Processed {len(contracts)} contracts")
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
        print("Usage: python3 pricing.py <input_file.json>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = "live/priced_contracts.json"
    price_contracts(input_path, output_path)
