#!/usr/bin/env python3
"""
Institutional QA Upgrade Test Suite - Memphis Civic Market

Tests the upgraded contract validation system with:
- 30-70% probability band logic
- Deterministic OpenAI calls with caching
- Robust error handling and reporting
- Real Memphis civic contract scenarios
- Production-ready validation API

Version: July_28_2025 - Production Market Viability Standards
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.append('.')

from app.contract_validation_api import ContractValidationAPI, ValidationResult
from app.enhanced_contract_critic_enforcer import EnhancedContractCriticEnforcer
from app.multi_variant_reframing_engine import MultiVariantReframingEngine, safe_success_rate_calculation

def create_test_contracts() -> List[Dict[str, Any]]:
    """Create realistic Memphis civic contracts for testing"""
    
    return [
        # SHOULD PASS - Genuine uncertainty (30-70% range)
        {
            'title': 'Memphis City Council Budget Approval',
            'description': 'Will the Memphis City Council approve the proposed 2025 municipal budget by December 31st?',
            'actor': 'Memphis City Council',
            'timeline': 'December 31, 2025',
            'resolution_criteria': 'Official council vote record and meeting minutes',
            'source': 'Memphis City Council Meeting',
            'expected_result': 'PASS',
            'expected_band': 'viable_30_70'
        },
        {
            'title': 'Shelby County Commission Election',
            'description': 'Will the incumbent candidate win re-election in District 7 in the 2025 Shelby County Commission race?',
            'actor': 'Shelby County Voters',
            'timeline': 'November 2025',
            'resolution_criteria': 'Official election results from Shelby County Election Commission',
            'source': 'Election Commission',
            'expected_result': 'PASS',
            'expected_band': 'viable_30_70'
        },
        {
            'title': 'Memphis Police Reform Initiative',
            'description': 'Will the Memphis Police Department implement the proposed community oversight board by June 2025?',
            'actor': 'Memphis Police Department',
            'timeline': 'June 30, 2025',
            'resolution_criteria': 'Official MPD announcement and oversight board formation',
            'source': 'Memphis Police Department',
            'expected_result': 'PASS',
            'expected_band': 'viable_30_70'
        },
        
        # SHOULD BLOCK - Too certain (>70% probability)
        {
            'title': 'Memphis Weather Certainty',
            'description': 'Will the sun rise in Memphis tomorrow morning?',
            'actor': 'Nature',
            'timeline': 'Tomorrow',
            'resolution_criteria': 'Sunrise observation',
            'source': 'Weather Service',
            'expected_result': 'BLOCK',
            'expected_band': 'too_certain_70_plus'
        },
        {
            'title': 'Obvious Legal Outcome',
            'description': 'Will Memphis continue to be located in Tennessee next year?',
            'actor': 'Geography',
            'timeline': 'December 31, 2025',
            'resolution_criteria': 'Geographic verification',
            'source': 'Geographic Survey',
            'expected_result': 'BLOCK',
            'expected_band': 'too_certain_70_plus'
        },
        
        # SHOULD BLOCK - Missing required fields
        {
            'title': 'Incomplete Contract',
            'description': 'Will something happen?',
            # Missing actor, timeline, resolution_criteria
            'source': 'Unknown',
            'expected_result': 'BLOCK',
            'expected_band': 'invalid_fields'
        },
        
        # SHOULD BLOCK - Unresolvable/ambiguous
        {
            'title': 'Unresolvable Event',
            'description': 'Will Memphis residents be "happier" after the new park opens?',
            'actor': 'Memphis Residents',
            'timeline': 'After park opening',
            'resolution_criteria': 'Subjective happiness measurement',
            'source': 'Parks Department',
            'expected_result': 'BLOCK',
            'expected_band': 'not_marketable'
        },
        
        # EDGE CASES - Test boundary conditions
        {
            'title': 'Memphis Mayoral Debate Schedule',
            'description': 'Will the Memphis mayoral candidates agree to participate in at least 3 public debates before the election?',
            'actor': 'Memphis Mayoral Candidates',
            'timeline': 'Before November 2025 election',
            'resolution_criteria': 'Public debate announcements and candidate confirmations',
            'source': 'Election Commission',
            'expected_result': 'PASS',
            'expected_band': 'viable_30_70'
        },
        {
            'title': 'FedEx Forum Event Decision',
            'description': 'Will FedEx Forum host a major concert event in the first quarter of 2025?',
            'actor': 'FedEx Forum Management',
            'timeline': 'March 31, 2025',
            'resolution_criteria': 'Official FedEx Forum event announcements',
            'source': 'FedEx Forum',
            'expected_result': 'PASS',
            'expected_band': 'viable_30_70'
        },
        {
            'title': 'Memphis Transportation Initiative',
            'description': 'Will MATA (Memphis Area Transit Authority) expand bus routes to include Germantown by end of 2025?',
            'actor': 'MATA',
            'timeline': 'December 31, 2025',
            'resolution_criteria': 'Official MATA route announcements and service maps',
            'source': 'MATA',
            'expected_result': 'PASS',
            'expected_band': 'viable_30_70'
        }
    ]

def run_institutional_qa_test():
    """Run comprehensive test of institutional QA upgrade"""
    
    print("🚀 INSTITUTIONAL QA UPGRADE TEST SUITE")
    print("=" * 60)
    print(f"Test Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize validation API
    print("🔧 Initializing Contract Validation API...")
    
    # Enable caching for faster testing
    os.environ['ENABLE_CRITIC_CACHING'] = 'true'
    
    validator = ContractValidationAPI()
    
    # Get test contracts
    test_contracts = create_test_contracts()
    print(f"📋 Testing {len(test_contracts)} contracts")
    print()
    
    # Test results tracking
    results = []
    passed_count = 0
    blocked_count = 0
    error_count = 0
    
    # Test each contract
    for i, contract in enumerate(test_contracts, 1):
        print(f"🧪 Test {i}/{len(test_contracts)}: {contract.get('title', 'Unknown')}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # Run validation
            result = validator.validate_contract(
                contract=contract,
                include_variants=False,  # Skip variants for speed
                user_id="test_user"
            )
            
            processing_time = time.time() - start_time
            
            # Check against expected results
            expected_result = contract.get('expected_result', 'UNKNOWN')
            expected_band = contract.get('expected_band', 'unknown')
            
            actual_result = "PASS" if result.passed else "BLOCK"
            test_passed = (actual_result == expected_result)
            
            # Track results
            if result.passed:
                passed_count += 1
            elif result.blocked:
                blocked_count += 1
            else:
                error_count += 1
            
            # Display results
            status_icon = "✅" if test_passed else "❌"
            print(f"   {status_icon} Result: {actual_result} (Expected: {expected_result})")
            print(f"   📊 Probability Band: {result.probability_band}")
            print(f"   🎯 Market Viability Score: {result.market_viability_score:.3f}")
            print(f"   ⏱️  Processing Time: {processing_time:.2f}s")
            
            if result.blocking_reason:
                print(f"   🚫 Blocking Reason: {result.blocking_reason}")
            
            if result.required_fields_missing:
                print(f"   📝 Missing Fields: {result.required_fields_missing}")
            
            if result.error_details:
                print(f"   ⚠️  Error Details: {result.error_details}")
            
            # Store detailed results
            results.append({
                'contract_title': contract.get('title', 'Unknown'),
                'expected_result': expected_result,
                'actual_result': actual_result,
                'test_passed': test_passed,
                'probability_band': result.probability_band,
                'market_viability_score': result.market_viability_score,
                'processing_time': processing_time,
                'blocking_reason': result.blocking_reason,
                'admin_review_required': result.admin_review_required
            })
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            error_count += 1
            results.append({
                'contract_title': contract.get('title', 'Unknown'),
                'expected_result': expected_result,
                'actual_result': 'ERROR',
                'test_passed': False,
                'error': str(e)
            })
        
        print()
    
    # Calculate overall results
    total_tests = len(test_contracts)
    test_success_rate = safe_success_rate_calculation(
        [r for r in results if r.get('test_passed', False)], 
        results
    )
    contract_pass_rate = safe_success_rate_calculation(passed_count, total_tests)
    
    # Display summary
    print("📊 INSTITUTIONAL QA TEST RESULTS")
    print("=" * 60)
    print(f"Total Contracts Tested: {total_tests}")
    print(f"Contracts Passed: {passed_count}")
    print(f"Contracts Blocked: {blocked_count}")
    print(f"System Errors: {error_count}")
    print()
    print(f"Contract Pass Rate: {contract_pass_rate:.1f}%")
    print(f"Test Accuracy Rate: {test_success_rate:.1f}%")
    print()
    
    # Probability band analysis
    band_counts = {}
    for result in results:
        band = result.get('probability_band', 'unknown')
        band_counts[band] = band_counts.get(band, 0) + 1
    
    print("📈 Probability Band Distribution:")
    for band, count in band_counts.items():
        percentage = (count / total_tests) * 100
        print(f"   {band}: {count} contracts ({percentage:.1f}%)")
    print()
    
    # Detailed results table
    print("📋 Detailed Test Results:")
    print("-" * 80)
    print(f"{'Contract':<30} {'Expected':<8} {'Actual':<8} {'Band':<20} {'Score':<8}")
    print("-" * 80)
    
    for result in results:
        title = result['contract_title'][:28]
        expected = result['expected_result'][:6]
        actual = result['actual_result'][:6]
        band = result.get('probability_band', 'unknown')[:18]
        score = f"{result.get('market_viability_score', 0):.2f}"
        
        print(f"{title:<30} {expected:<8} {actual:<8} {band:<20} {score:<8}")
    
    print("-" * 80)
    print()
    
    # Assessment and recommendations
    print("🎯 ASSESSMENT:")
    if contract_pass_rate >= 20 and contract_pass_rate <= 40:
        print("✅ OPTIMAL: Contract pass rate is within target range (20-40%)")
        print("   System correctly identifies viable markets while blocking problematic contracts")
    elif contract_pass_rate < 20:
        print("⚠️  CAUTION: Pass rate below 20% - may be over-blocking viable contracts")
        print("   Consider relaxing probability thresholds or improving market viability detection")
    elif contract_pass_rate > 40:
        print("⚠️  CAUTION: Pass rate above 40% - may be under-blocking problematic contracts")
        print("   Consider tightening probability thresholds or improving blocking detection")
    
    if test_success_rate >= 80:
        print("✅ EXCELLENT: Test accuracy >80% - system behavior matches expectations")
    elif test_success_rate >= 60:
        print("⚠️  GOOD: Test accuracy 60-80% - minor tuning may be needed")
    else:
        print("❌ NEEDS WORK: Test accuracy <60% - significant tuning required")
    
    print()
    print("🎉 INSTITUTIONAL QA UPGRADE TEST COMPLETE")
    print("=" * 60)
    
    # Save results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"institutional_qa_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            'test_summary': {
                'total_tests': total_tests,
                'passed_count': passed_count,
                'blocked_count': blocked_count,
                'error_count': error_count,
                'contract_pass_rate': contract_pass_rate,
                'test_accuracy_rate': test_success_rate,
                'timestamp': datetime.now().isoformat()
            },
            'probability_bands': band_counts,
            'detailed_results': results
        }, f, indent=2)
    
    print(f"💾 Results saved to: {results_file}")
    
    return {
        'total_tests': total_tests,
        'passed_count': passed_count,
        'blocked_count': blocked_count,
        'contract_pass_rate': contract_pass_rate,
        'test_accuracy_rate': test_success_rate,
        'results_file': results_file
    }

if __name__ == '__main__':
    # Run the institutional QA test
    test_results = run_institutional_qa_test()
