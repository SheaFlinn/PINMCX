import argparse
import json
import sys
import os
from typing import Dict, Any

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.contract_ai_service import ContractAIService

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_contract_stage(stage_name: str, contract_data: Dict[str, Any]):
    """Print a formatted version of the contract stage."""
    print(f"\n=== {stage_name.upper()} ===")
    print(json.dumps(contract_data, indent=2))
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="Test the AI contract cascade")
    parser.add_argument("headline", type=str, help="The headline to generate a contract from")
    args = parser.parse_args()
    
    service = ContractAIService()
    
    try:
        # Generate draft contract
        draft = service.generate_draft_contract(args.headline)
        print_contract_stage("Draft Contract", draft)
        
        # Patch contract if needed
        if not draft.get("patched"):
            print("[Stage 4] Running patch_contract()")
            draft = service.patch_contract(draft)
            print_contract_stage("Patched Contract", draft)
        else:
            print("[Stage 4] Skipped - already patched.")
        
        # Weigh contract
        weighed = service.weigh_contract(draft)
        print_contract_stage("Weighed Contract", weighed)
        
        # Test contract
        tested = service.test_contract(weighed)
        print_contract_stage("Tested Contract", tested)
        
        # Safety: copy headline back in if it got lost
        if not tested.get("headline") and draft.get("headline"):
            tested["headline"] = draft["headline"]
            tested["original_headline"] = draft["headline"]
        
        # Balance contract if confidence is extreme
        if "confidence" in tested and (tested["confidence"] > 0.7 or tested["confidence"] < 0.3):
            print("[Stage 5] Running balance_contract()")
            tested = service.balance_contract(tested)
            print_contract_stage("Balanced Contract", tested)

            if tested.get("retest_required"):
                print("[Stage 6] Re-running test_contract() after balance")
                tested = service.test_contract(tested)
                print_contract_stage("Re-tested Contract", tested)
        
        if tested.get("publish_ready", False):
            logger.info("Contract is ready for publishing!")
        else:
            logger.warning("Contract needs further review before publishing.")
            
    except Exception as e:
        logger.error(f"Error running contract cascade: {str(e)}")
        raise

if __name__ == "__main__":
    main()
