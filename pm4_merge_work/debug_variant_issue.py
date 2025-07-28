#!/usr/bin/env python3
"""
Debug Variant Issue - Why Original Passes But Variants Fail
Memphis Civic Market - July 27, 2025v3

Compare the original working contract with its generated variants
to understand why reframing is making contracts worse.
"""

import os
import sys
import json
from datetime import datetime

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.enhanced_contract_critic_enforcer import EnhancedContractCriticEnforcer

def compare_original_vs_variant():
    """Compare original working contract with a problematic variant"""
    
    print("🔍 DEBUG: ORIGINAL VS VARIANT COMPARISON")
    print("=" * 60)
    
    # Original working contract
    original_contract = {
        'title': 'Memphis City Council Infrastructure Bond Vote',
        'description': 'Will Memphis City Council approve the $50M infrastructure bond by March 31, 2025?',
        'probability': 0.5,
        'resolution_date': '2025-03-31',
        'category': 'civic',
        'resolution_criteria': 'Resolved YES if Memphis City Council votes to approve the infrastructure bond by March 31, 2025. Resolved NO otherwise.'
    }
    
    # Problematic variant (from the multi-variant output)
    variant_contract = {
        'title': 'Memphis City Council Infrastructure Bond Vote within Fiscal Year',
        'description': 'Will Memphis City Council approve the $50M infrastructure bond by the end of the fiscal year on June 30, 2025?',
        'probability': 0.5,
        'resolution_date': '2025-03-31',
        'category': 'civic',
        'resolution_criteria': 'Resolved YES if Memphis City Council votes to approve the infrastructure bond by March 31, 2025. Resolved NO otherwise.',
        'timeline': 'By end of fiscal year on June 30, 2025'
    }
    
    critic = EnhancedContractCriticEnforcer()
    
    print("📋 ORIGINAL CONTRACT:")
    print(f"   Title: {original_contract['title']}")
    print(f"   Description: {original_contract['description']}")
    
    try:
        original_analysis = critic.analyze_single_contract(original_contract)
        print(f"\n📊 ORIGINAL RESULTS:")
        print(f"   Overall Score: {original_analysis.overall_score:.3f}")
        print(f"   Market Balance Score: {original_analysis.market_balance_score:.3f}")
        print(f"   Passed: {original_analysis.passed}")
        print(f"   Blocked: {original_analysis.blocked}")
        print(f"   Blocking Issues: {len(original_analysis.blocking_issues)}")
        
    except Exception as e:
        print(f"   ❌ ERROR analyzing original: {str(e)}")
        return False
    
    print(f"\n📋 VARIANT CONTRACT:")
    print(f"   Title: {variant_contract['title']}")
    print(f"   Description: {variant_contract['description']}")
    print(f"   Key Difference: Added fiscal year timeline")
    
    try:
        variant_analysis = critic.analyze_single_contract(variant_contract)
        print(f"\n📊 VARIANT RESULTS:")
        print(f"   Overall Score: {variant_analysis.overall_score:.3f}")
        print(f"   Market Balance Score: {variant_analysis.market_balance_score:.3f}")
        print(f"   Passed: {variant_analysis.passed}")
        print(f"   Blocked: {variant_analysis.blocked}")
        print(f"   Blocking Issues: {len(variant_analysis.blocking_issues)}")
        
        if variant_analysis.blocking_issues:
            print(f"\n🚫 VARIANT BLOCKING ISSUES:")
            for issue in variant_analysis.blocking_issues:
                issue_type = issue.get('issue_type', 'unknown')
                description = issue.get('description', 'No description')
                print(f"   - {issue_type}: {description}")
        
    except Exception as e:
        print(f"   ❌ ERROR analyzing variant: {str(e)}")
        return False
    
    # Compare results
    print(f"\n🔍 COMPARISON ANALYSIS:")
    print(f"   Original Market Balance: {original_analysis.market_balance_score:.3f}")
    print(f"   Variant Market Balance: {variant_analysis.market_balance_score:.3f}")
    print(f"   Market Balance Change: {variant_analysis.market_balance_score - original_analysis.market_balance_score:+.3f}")
    
    print(f"\n   Original Passed: {original_analysis.passed}")
    print(f"   Variant Passed: {variant_analysis.passed}")
    
    if original_analysis.passed and not variant_analysis.passed:
        print(f"\n❌ PROBLEM IDENTIFIED:")
        print(f"   - Original contract passes critic")
        print(f"   - Variant fails critic due to reframing")
        print(f"   - Reframing strategy is making contracts WORSE")
        
        print(f"\n🔧 ROOT CAUSE:")
        print(f"   - Variant market balance dropped from {original_analysis.market_balance_score:.3f} to {variant_analysis.market_balance_score:.3f}")
        print(f"   - Adding fiscal year timeline created new blocking issues")
        print(f"   - Reframing strategies need calibration")
        
        return False
    else:
        print(f"\n✅ Both contracts have similar results")
        return True

def main():
    """Main debug execution"""
    
    print("🔍 VARIANT DEBUGGING - ROOT CAUSE ANALYSIS")
    print("Focus: Why do variants fail when original passes?")
    print("=" * 60)
    
    success = compare_original_vs_variant()
    
    print(f"\n" + "=" * 60)
    print(f"🎯 DIAGNOSIS: {'REFRAMING WORKING' if success else 'REFRAMING BROKEN'}")
    
    if not success:
        print(f"\n🔧 IMMEDIATE FIXES NEEDED:")
        print(f"   1. Reframing strategies are making contracts worse")
        print(f"   2. Need to calibrate reframing to preserve market balance")
        print(f"   3. Test original contract through pipeline WITHOUT variants first")
        print(f"   4. Fix reframing before enabling multi-variant processing")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
