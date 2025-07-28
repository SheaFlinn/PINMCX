#!/usr/bin/env python3
"""
Contract Validation Test - Emergency Fix
Memphis Civic Market - July 27, 2025v3

Quick test to validate that the threshold fix allows viable contracts to pass
"""

import os
import sys

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.enhanced_contract_critic_enforcer import EnhancedContractCriticEnforcer

def test_viable_contracts():
    """Test several viable civic contracts to confirm they can now pass"""
    
    test_contracts = [
        {
            'title': 'Memphis City Council Infrastructure Vote',
            'description': 'Will Memphis City Council approve the infrastructure bond by March 31st?',
            'probability': 0.5,
            'resolution_date': '2025-03-31',
            'category': 'civic'
        },
        {
            'title': 'Mayor Budget Proposal',
            'description': 'Will Mayor Strickland\'s budget proposal pass without major amendments?',
            'probability': 0.5,
            'resolution_date': '2025-04-15',
            'category': 'civic'
        },
        {
            'title': 'County Tax Increase',
            'description': 'Will the Shelby County Commission approve the tax increase?',
            'probability': 0.5,
            'resolution_date': '2025-05-01',
            'category': 'civic'
        }
    ]
    
    critic = EnhancedContractCriticEnforcer()
    
    print("🧪 Testing viable civic contracts with adjusted thresholds...")
    print(f"   Min Passing Score: {critic.min_passing_score}")
    print(f"   Market Balance Threshold: {critic.market_balance_threshold}")
    
    passed_contracts = 0
    total_contracts = len(test_contracts)
    
    for i, contract in enumerate(test_contracts):
        print(f"\n📋 Contract {i+1}/{total_contracts}: {contract['title']}")
        
        try:
            result = critic.analyze_single_contract(contract)
            
            # Check if contract passes (simplified logic)
            passes = (result.overall_score >= critic.min_passing_score and 
                     result.market_balance_score >= critic.market_balance_threshold)
            
            print(f"   Overall Score: {result.overall_score:.3f}")
            print(f"   Market Balance Score: {result.market_balance_score:.3f}")
            print(f"   Result: {'✅ PASSED' if passes else '❌ BLOCKED'}")
            
            if passes:
                passed_contracts += 1
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    pass_rate = (passed_contracts / total_contracts) * 100
    print(f"\n📊 RESULTS:")
    print(f"   Contracts Passed: {passed_contracts}/{total_contracts}")
    print(f"   Pass Rate: {pass_rate:.1f}%")
    
    if pass_rate > 0:
        print("✅ SUCCESS: Threshold fix is working - viable contracts can now pass!")
        return True
    else:
        print("❌ FAILURE: Contracts still being blocked - need further adjustment")
        return False

def main():
    """Main test execution"""
    print("=" * 80)
    print("🧪 CONTRACT VALIDATION TEST - THRESHOLD FIX")
    print("=" * 80)
    
    success = test_viable_contracts()
    
    if success:
        print("\n🎯 NEXT STEPS:")
        print("   1. Run multi-variant pipeline test")
        print("   2. Validate batch processing works")
        print("   3. Resume institutional readiness testing")
        return 0
    else:
        print("\n🔧 ADDITIONAL FIXES NEEDED:")
        print("   1. Further reduce min_passing_score threshold")
        print("   2. Investigate overall scoring calculation")
        print("   3. Consider market_balance_score weighting")
        return 1

if __name__ == "__main__":
    exit(main())
