#!/usr/bin/env python3
"""
Single Contract End-to-End Test
Memphis Civic Market - July 27, 2025v3

Focus on getting ONE contract to work correctly through the entire chain
before attempting batch processing or multiple contracts.
"""

import os
import sys
import json
from datetime import datetime

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.enhanced_contract_critic_enforcer import EnhancedContractCriticEnforcer

def test_single_contract_deep_analysis():
    """Deep analysis of a single contract to understand exactly what's happening"""
    
    print("🔍 SINGLE CONTRACT DEEP ANALYSIS")
    print("=" * 60)
    
    # One simple, clearly viable civic contract - made more specific to address ambiguity
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
    
    critic = EnhancedContractCriticEnforcer()
    
    try:
        # Analyze the contract
        analysis = critic.analyze_single_contract(test_contract)
        
        print(f"\n📊 ANALYSIS RESULTS:")
        print(f"   Overall Score: {analysis.overall_score:.3f}")
        print(f"   Market Balance Score: {analysis.market_balance_score:.3f}")
        print(f"   Passed: {analysis.passed}")
        print(f"   Blocked: {analysis.blocked}")
        
        print(f"\n🔍 DETAILED BREAKDOWN:")
        print(f"   Market Balance Threshold: {critic.market_balance_threshold}")
        print(f"   Market Balance Passed: {analysis.market_balance_score >= critic.market_balance_threshold}")
        print(f"   Blocking Issue Types: {critic.blocking_issue_types}")
        
        # Analyze all issues found
        print(f"\n📝 ALL ISSUES FOUND ({len(analysis.issues_found)}):")
        for i, issue in enumerate(analysis.issues_found):
            issue_type = issue.get('issue_type', 'unknown')
            severity = issue.get('severity', 'unknown')
            description = issue.get('description', 'No description')
            weight = critic.issue_weights.get(issue_type, 0.0)
            is_blocking = issue_type in critic.blocking_issue_types
            
            print(f"   {i+1}. {issue_type} (weight: {weight}, blocking: {is_blocking})")
            print(f"      Severity: {severity}")
            print(f"      Description: {description}")
        
        # Analyze blocking issues specifically
        print(f"\n🚫 BLOCKING ISSUES ({len(analysis.blocking_issues)}):")
        if analysis.blocking_issues:
            for i, issue in enumerate(analysis.blocking_issues):
                issue_type = issue.get('issue_type', 'unknown')
                description = issue.get('description', 'No description')
                print(f"   {i+1}. {issue_type}: {description}")
        else:
            print("   None")
        
        # Final determination
        print(f"\n🎯 PASS/FAIL LOGIC:")
        market_viability_passed = analysis.market_balance_score >= critic.market_balance_threshold
        has_blocking_issues = len(analysis.blocking_issues) > 0
        
        print(f"   Market Viability Passed: {market_viability_passed}")
        print(f"   Has Blocking Issues: {has_blocking_issues}")
        print(f"   Should Pass: {market_viability_passed and not has_blocking_issues}")
        print(f"   Actually Passed: {analysis.passed}")
        
        if analysis.passed:
            print(f"\n✅ SUCCESS: Contract passes all checks!")
            return True, "Contract passed successfully"
        else:
            if not market_viability_passed:
                reason = f"Market balance score {analysis.market_balance_score:.3f} below threshold {critic.market_balance_threshold}"
            elif has_blocking_issues:
                blocking_types = [issue.get('issue_type', 'unknown') for issue in analysis.blocking_issues]
                reason = f"Blocking issues: {', '.join(blocking_types)}"
            else:
                reason = "Unknown reason - logic error"
            
            print(f"\n❌ FAILED: {reason}")
            return False, reason
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False, f"Analysis error: {str(e)}"

def main():
    """Main execution - focus on one contract"""
    
    print("🎯 SINGLE CONTRACT FOCUSED TEST")
    print("Focus: Get ONE contract working correctly before scaling")
    print("=" * 60)
    
    success, reason = test_single_contract_deep_analysis()
    
    print(f"\n" + "=" * 60)
    print(f"🎯 RESULT: {'SUCCESS' if success else 'FAILURE'}")
    print(f"Reason: {reason}")
    
    if success:
        print(f"\n✅ NEXT STEPS:")
        print(f"   1. Test this same contract through multi-variant engine")
        print(f"   2. Test through full pipeline enforcer")
        print(f"   3. Only then scale to multiple contracts")
    else:
        print(f"\n🔧 FIX NEEDED:")
        print(f"   1. Address the specific issue: {reason}")
        print(f"   2. Retest this same contract")
        print(f"   3. Do NOT proceed to batch testing until this works")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
