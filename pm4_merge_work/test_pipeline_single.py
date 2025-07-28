#!/usr/bin/env python3
"""
Test Full Pipeline with Single Working Contract
Memphis Civic Market - July 27, 2025v3

Skip multi-variant reframing and test the working contract directly through
the full pipeline enforcer to validate end-to-end processing.
"""

import os
import sys
import json
from datetime import datetime

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.full_chain_pipeline_enforcer import FullChainPipelineEnforcer

def test_single_contract_pipeline():
    """Test the working contract through full pipeline without variants"""
    
    print("🔄 FULL PIPELINE TEST - SINGLE CONTRACT")
    print("=" * 60)
    
    # Same contract that passes critic analysis
    test_contract = {
        'title': 'Memphis City Council Infrastructure Bond Vote',
        'description': 'Will Memphis City Council approve the $50M infrastructure bond by March 31, 2025?',
        'probability': 0.5,
        'resolution_date': '2025-03-31',
        'category': 'civic',
        'resolution_criteria': 'Resolved YES if Memphis City Council votes to approve the infrastructure bond by March 31, 2025. Resolved NO otherwise.'
    }
    
    print(f"📋 Testing Contract: {test_contract['title']}")
    print(f"   Description: {test_contract['description']}")
    
    pipeline = FullChainPipelineEnforcer()
    
    try:
        print(f"\n🔄 Processing through full pipeline...")
        
        # Process single contract through pipeline
        result = pipeline.process_single_contract(test_contract)
        
        # Extract results
        print(f"\n📊 PIPELINE RESULTS:")
        print(f"   Processing Status: {result.get('status', 'Unknown')}")
        print(f"   Final Outcome: {result.get('final_outcome', 'Unknown')}")
        print(f"   Pipeline Stage: {result.get('pipeline_stage', 'Unknown')}")
        
        if 'contract_analysis' in result:
            analysis = result['contract_analysis']
            print(f"   Contract Passed: {analysis.get('passed', 'Unknown')}")
            print(f"   Contract Blocked: {analysis.get('blocked', 'Unknown')}")
            print(f"   Market Balance Score: {analysis.get('market_balance_score', 'Unknown')}")
        
        if 'admin_override_required' in result:
            print(f"   Admin Override Required: {result['admin_override_required']}")
        
        # Check success criteria
        status = result.get('status', '')
        final_outcome = result.get('final_outcome', '')
        
        if status == 'success' and final_outcome == 'published':
            print(f"\n✅ SUCCESS: Contract processed and published")
            return True, "Contract successfully processed through pipeline"
        elif status == 'blocked' or final_outcome == 'blocked':
            print(f"\n❌ BLOCKED: Contract blocked in pipeline")
            blocking_reason = result.get('blocking_reason', 'Unknown reason')
            return False, f"Contract blocked: {blocking_reason}"
        elif final_outcome == 'admin_rescue':
            print(f"\n⚠️  ADMIN RESCUE: Contract requires admin intervention")
            return True, "Contract sent to admin rescue (acceptable outcome)"
        else:
            print(f"\n❓ UNKNOWN: Unexpected pipeline result")
            return False, f"Unknown pipeline result: {status}/{final_outcome}"
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False, f"Pipeline error: {str(e)}"

def main():
    """Main execution - test pipeline with single working contract"""
    
    print("🎯 FULL PIPELINE SINGLE CONTRACT TEST")
    print("Focus: Validate end-to-end processing without multi-variant complexity")
    print("=" * 60)
    
    success, reason = test_single_contract_pipeline()
    
    print(f"\n" + "=" * 60)
    print(f"🎯 RESULT: {'SUCCESS' if success else 'FAILURE'}")
    print(f"Reason: {reason}")
    
    if success:
        print(f"\n✅ NEXT STEPS:")
        print(f"   1. End-to-end pipeline works with single contract")
        print(f"   2. Can now debug multi-variant reframing separately")
        print(f"   3. Focus on fixing reframing strategies")
        print(f"   4. Then integrate multi-variant back into pipeline")
    else:
        print(f"\n🔧 FIX NEEDED:")
        print(f"   1. Address pipeline issue: {reason}")
        print(f"   2. Ensure single contract can flow through pipeline")
        print(f"   3. Fix pipeline before addressing multi-variant")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
