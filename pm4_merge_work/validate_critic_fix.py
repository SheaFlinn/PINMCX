#!/usr/bin/env python3
"""
Validate Critic Fix - Market Viability Only Blocking
Memphis Civic Market - July 27, 2025v3

This script validates that the critic logic fix works correctly:
- Only blocks contracts on market viability metrics
- Overall score is logged but never blocks
- Contracts with perfect market balance pass regardless of overall score
"""

import os
import sys
import json
from datetime import datetime

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.enhanced_contract_critic_enforcer import EnhancedContractCriticEnforcer

def test_critic_fix_validation():
    """Test that critic fix allows viable contracts to pass"""
    
    print("🔧 VALIDATING CRITIC FIX - MARKET VIABILITY ONLY BLOCKING")
    print("=" * 80)
    
    # Test contracts that should have perfect market balance
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
        },
        {
            'title': 'Downtown Development Project',
            'description': 'Will the downtown development project receive approval?',
            'probability': 0.5,
            'resolution_date': '2025-06-01',
            'category': 'civic'
        }
    ]
    
    critic = EnhancedContractCriticEnforcer()
    
    print(f"📊 Critic Configuration:")
    print(f"   Market Balance Threshold: {critic.market_balance_threshold}")
    print(f"   Min Passing Score: {critic.min_passing_score} (analytics only)")
    print(f"   Blocking Issue Types: {critic.blocking_issue_types}")
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_contracts': len(test_contracts),
        'passed_contracts': 0,
        'blocked_contracts': 0,
        'contract_results': []
    }
    
    print(f"\n🧪 Testing {len(test_contracts)} contracts...")
    
    for i, contract in enumerate(test_contracts):
        print(f"\n📋 Contract {i+1}/{len(test_contracts)}: {contract['title']}")
        
        try:
            # Analyze contract with fixed logic
            analysis = critic.analyze_single_contract(contract)
            
            # Extract detailed metrics
            contract_result = {
                'title': contract['title'],
                'overall_score': analysis.overall_score,
                'market_balance_score': analysis.market_balance_score,
                'passed': analysis.passed,
                'blocked': analysis.blocked,
                'blocking_issues': [issue.get('issue_type', 'unknown') for issue in analysis.blocking_issues],
                'market_viability_metrics': {
                    'market_balance_score': analysis.market_balance_score,
                    'market_balance_threshold': critic.market_balance_threshold,
                    'market_balance_passed': analysis.market_balance_score >= critic.market_balance_threshold
                }
            }
            
            # Log detailed results
            print(f"   📊 Overall Score: {analysis.overall_score:.3f} (analytics only)")
            print(f"   🎯 Market Balance Score: {analysis.market_balance_score:.3f}")
            print(f"   📈 Market Balance Threshold: {critic.market_balance_threshold}")
            print(f"   🔍 Market Balance Passed: {analysis.market_balance_score >= critic.market_balance_threshold}")
            print(f"   🚫 Blocking Issues: {len(analysis.blocking_issues)}")
            
            if analysis.blocking_issues:
                for issue in analysis.blocking_issues:
                    issue_type = issue.get('issue_type', 'unknown')
                    print(f"      - {issue_type}")
            
            print(f"   ✅ Final Result: {'PASSED' if analysis.passed else 'BLOCKED'}")
            
            # Track results
            if analysis.passed:
                results['passed_contracts'] += 1
                print(f"   🎉 SUCCESS: Contract passed with market balance {analysis.market_balance_score:.3f}")
            else:
                results['blocked_contracts'] += 1
                if analysis.market_balance_score >= critic.market_balance_threshold:
                    print(f"   ⚠️  WARNING: High market balance ({analysis.market_balance_score:.3f}) but still blocked")
                else:
                    print(f"   ❌ BLOCKED: Market balance {analysis.market_balance_score:.3f} below threshold {critic.market_balance_threshold}")
            
            results['contract_results'].append(contract_result)
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            results['contract_results'].append({
                'title': contract['title'],
                'error': str(e)
            })
    
    # Calculate metrics
    pass_rate = (results['passed_contracts'] / results['total_contracts']) * 100
    
    print(f"\n" + "=" * 80)
    print(f"📊 VALIDATION RESULTS")
    print(f"=" * 80)
    print(f"   Total Contracts: {results['total_contracts']}")
    print(f"   Passed: {results['passed_contracts']}")
    print(f"   Blocked: {results['blocked_contracts']}")
    print(f"   Pass Rate: {pass_rate:.1f}%")
    
    # Analyze results
    high_market_balance_blocked = 0
    for result in results['contract_results']:
        if (not result.get('error') and 
            result.get('market_balance_score', 0) >= critic.market_balance_threshold and 
            not result.get('passed', False)):
            high_market_balance_blocked += 1
    
    print(f"\n🔍 ANALYSIS:")
    if pass_rate > 0:
        print(f"   ✅ SUCCESS: {pass_rate:.1f}% of contracts now pass")
        if high_market_balance_blocked == 0:
            print(f"   ✅ PERFECT: No contracts with high market balance are blocked")
        else:
            print(f"   ⚠️  WARNING: {high_market_balance_blocked} contracts with high market balance still blocked")
    else:
        print(f"   ❌ FAILURE: All contracts still blocked - need further investigation")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"critic_fix_validation_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    return pass_rate > 0, results

def test_multi_variant_pipeline():
    """Test that multi-variant pipeline works with fixed critic"""
    
    print(f"\n🔄 TESTING MULTI-VARIANT PIPELINE WITH FIXED CRITIC")
    print("=" * 80)
    
    # Import multi-variant engine
    from app.multi_variant_reframing_engine import MultiVariantReframingEngine
    
    variant_engine = MultiVariantReframingEngine()
    
    # Test single contract through full variant pipeline
    test_contract = {
        'title': 'Memphis City Council Infrastructure Vote',
        'description': 'Will Memphis City Council approve the infrastructure bond by March 31st?',
        'probability': 0.5,
        'resolution_date': '2025-03-31',
        'category': 'civic'
    }
    
    print(f"📋 Testing: {test_contract['title']}")
    
    try:
        # Generate and analyze variants
        variant_result = variant_engine.generate_and_analyze_variants(test_contract)
        
        # Extract results
        total_variants = len(variant_result.variants) if hasattr(variant_result, 'variants') else 0
        passed_variants = variant_result.variants_passed if hasattr(variant_result, 'variants_passed') else 0
        blocked_variants = variant_result.variants_blocked if hasattr(variant_result, 'variants_blocked') else 0
        
        print(f"   📊 Total Variants: {total_variants}")
        print(f"   ✅ Passed Variants: {passed_variants}")
        print(f"   ❌ Blocked Variants: {blocked_variants}")
        
        if total_variants > 0:
            variant_pass_rate = (passed_variants / total_variants) * 100
            print(f"   📈 Variant Pass Rate: {variant_pass_rate:.1f}%")
            
            if variant_pass_rate > 0:
                print(f"   🎉 SUCCESS: Multi-variant pipeline is working!")
                return True
            else:
                print(f"   ❌ ISSUE: All variants still blocked")
                return False
        else:
            print(f"   ❌ ERROR: No variants generated")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

def main():
    """Main validation execution"""
    
    # Step 1: Test critic fix
    critic_success, results = test_critic_fix_validation()
    
    # Step 2: Test multi-variant pipeline if critic is working
    pipeline_success = False
    if critic_success:
        pipeline_success = test_multi_variant_pipeline()
    
    # Final summary
    print(f"\n" + "=" * 80)
    print(f"🎯 FINAL VALIDATION SUMMARY")
    print(f"=" * 80)
    
    if critic_success:
        print(f"   ✅ Critic Fix: WORKING - Viable contracts can now pass")
    else:
        print(f"   ❌ Critic Fix: FAILED - Contracts still blocked")
    
    if pipeline_success:
        print(f"   ✅ Multi-Variant Pipeline: WORKING - Variants passing critic")
    else:
        print(f"   ❌ Multi-Variant Pipeline: NEEDS WORK - Variants still blocked")
    
    if critic_success and pipeline_success:
        print(f"\n🎉 OVERALL STATUS: SUCCESS - Ready for batch processing!")
        print(f"   Next Steps:")
        print(f"   1. Run full institutional readiness test")
        print(f"   2. Process batch of 100+ Memphis events")
        print(f"   3. Validate end-to-end pipeline reliability")
        return 0
    else:
        print(f"\n⚠️  OVERALL STATUS: NEEDS MORE WORK")
        print(f"   Next Steps:")
        print(f"   1. Investigate remaining blocking issues")
        print(f"   2. Further adjust market viability thresholds")
        print(f"   3. Test individual blocking issue types")
        return 1

if __name__ == "__main__":
    exit(main())
