#!/usr/bin/env python3
"""
Diagnostic Script: Analyze Why All Contract Variants Are Being Blocked
Memphis Civic Market - July 27, 2025v3

This script diagnoses the over-blocking issue in the multi-variant chain execution
by analyzing recent logs, testing known-good contracts, and identifying root causes.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.multi_variant_reframing_engine import MultiVariantReframingEngine
from app.enhanced_contract_critic_enforcer import EnhancedContractCriticEnforcer

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BlockingDiagnostic:
    """Comprehensive diagnostic tool for analyzing contract blocking issues"""
    
    def __init__(self):
        """Initialize diagnostic components"""
        self.variant_engine = MultiVariantReframingEngine()
        self.critic_enforcer = EnhancedContractCriticEnforcer()
        self.diagnostic_results = {
            'timestamp': datetime.now().isoformat(),
            'blocked_variants': [],
            'root_causes': [],
            'recommendations': []
        }
        
    def analyze_recent_blocking_patterns(self) -> Dict[str, Any]:
        """Analyze recent blocking patterns from logs and test runs"""
        logger.info("🔍 Analyzing recent blocking patterns...")
        
        # Test contracts that should be viable civic predictions
        test_contracts = [
            {
                'title': 'Memphis City Council Infrastructure Vote',
                'description': 'Will Memphis City Council approve the $50M infrastructure bond by March 31st?',
                'expected_viability': 'HIGH'
            },
            {
                'title': 'Mayor Budget Proposal',
                'description': 'Will Mayor Strickland\'s budget proposal pass without major amendments?',
                'expected_viability': 'HIGH'
            },
            {
                'title': 'County Tax Increase',
                'description': 'Will the Shelby County Commission approve the tax increase?',
                'expected_viability': 'HIGH'
            },
            {
                'title': 'Police Budget Increase',
                'description': 'Will the Memphis Police Department budget increase be approved?',
                'expected_viability': 'HIGH'
            },
            {
                'title': 'Downtown Development Project',
                'description': 'Will the downtown development project receive unanimous approval?',
                'expected_viability': 'MEDIUM'  # Unanimous might be too specific
            }
        ]
        
        blocking_analysis = {
            'total_contracts_tested': len(test_contracts),
            'contracts_analyzed': [],
            'common_failure_patterns': {},
            'critic_threshold_analysis': {}
        }
        
        for i, contract in enumerate(test_contracts):
            logger.info(f"📋 Testing contract {i+1}/{len(test_contracts)}: {contract['title']}")
            
            contract_analysis = self._analyze_single_contract(contract)
            blocking_analysis['contracts_analyzed'].append(contract_analysis)
            
            # Track common failure patterns
            for variant in contract_analysis['variants']:
                for reason in variant['block_reasons']:
                    if reason not in blocking_analysis['common_failure_patterns']:
                        blocking_analysis['common_failure_patterns'][reason] = 0
                    blocking_analysis['common_failure_patterns'][reason] += 1
        
        return blocking_analysis
    
    def _analyze_single_contract(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single contract and its variants"""
        contract_data = {
            'title': contract['title'],
            'description': contract['description'],
            'expected_viability': contract['expected_viability'],
            'variants': [],
            'summary': {
                'total_variants': 0,
                'passed_variants': 0,
                'blocked_variants': 0,
                'pass_rate': 0.0
            }
        }
        
        try:
            # Generate variants
            logger.info(f"  🔄 Generating variants for: {contract['title']}")
            variant_result = self.variant_engine.generate_and_analyze_variants(contract)
            
            contract_data['summary']['total_variants'] = len(variant_result.get('variants', []))
            
            # Analyze each variant
            for variant in variant_result.get('variants', []):
                variant_analysis = self._analyze_variant(variant)
                contract_data['variants'].append(variant_analysis)
                
                if variant_analysis['blocked']:
                    contract_data['summary']['blocked_variants'] += 1
                else:
                    contract_data['summary']['passed_variants'] += 1
            
            # Calculate pass rate
            if contract_data['summary']['total_variants'] > 0:
                contract_data['summary']['pass_rate'] = (
                    contract_data['summary']['passed_variants'] / 
                    contract_data['summary']['total_variants']
                )
            
        except Exception as e:
            logger.error(f"  ❌ Error analyzing contract {contract['title']}: {str(e)}")
            contract_data['error'] = str(e)
        
        return contract_data
    
    def _analyze_variant(self, variant: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single variant and its critic results"""
        variant_analysis = {
            'title': variant.get('title', 'Unknown'),
            'description': variant.get('description', 'Unknown'),
            'reframing_strategy': variant.get('reframing_strategy', 'Unknown'),
            'blocked': False,
            'block_reasons': [],
            'critic_scores': {},
            'critic_details': {}
        }
        
        try:
            # Run critic analysis
            critic_result = self.critic_enforcer.analyze_contract(variant)
            
            variant_analysis['blocked'] = not critic_result.passes_all_checks
            variant_analysis['critic_scores'] = {
                'overall_score': critic_result.overall_score,
                'market_balance_score': critic_result.market_balance_score
            }
            
            # Extract blocking reasons
            for issue in critic_result.issues:
                if issue.weight >= 1.0:  # Blocking issues
                    variant_analysis['block_reasons'].append(issue.issue_type)
                    variant_analysis['critic_details'][issue.issue_type] = {
                        'reason': issue.reason,
                        'weight': issue.weight,
                        'score': issue.score
                    }
            
        except Exception as e:
            logger.error(f"    ❌ Error analyzing variant: {str(e)}")
            variant_analysis['error'] = str(e)
        
        return variant_analysis
    
    def test_known_good_contracts(self) -> Dict[str, Any]:
        """Test contracts that previously passed to see if they still work"""
        logger.info("🧪 Testing known-good contracts...")
        
        # These are contracts that should definitely be viable civic predictions
        known_good_contracts = [
            {
                'title': 'Simple Council Vote',
                'description': 'Will Memphis City Council approve the proposed ordinance?',
                'expected_result': 'SHOULD_PASS'
            },
            {
                'title': 'Budget Approval',
                'description': 'Will the city budget be approved by the deadline?',
                'expected_result': 'SHOULD_PASS'
            },
            {
                'title': 'Development Project',
                'description': 'Will the riverfront development project be approved?',
                'expected_result': 'SHOULD_PASS'
            }
        ]
        
        results = {
            'total_tested': len(known_good_contracts),
            'passed': 0,
            'failed': 0,
            'contract_results': []
        }
        
        for contract in known_good_contracts:
            logger.info(f"  🧪 Testing: {contract['title']}")
            
            try:
                # Test direct critic analysis (bypass variant generation)
                critic_result = self.critic_enforcer.analyze_contract(contract)
                
                contract_result = {
                    'title': contract['title'],
                    'expected_result': contract['expected_result'],
                    'actual_result': 'PASSED' if critic_result.passes_all_checks else 'BLOCKED',
                    'critic_score': critic_result.overall_score,
                    'market_score': critic_result.market_balance_score,
                    'blocking_issues': [issue.issue_type for issue in critic_result.issues if issue.weight >= 1.0]
                }
                
                if critic_result.passes_all_checks:
                    results['passed'] += 1
                else:
                    results['failed'] += 1
                
                results['contract_results'].append(contract_result)
                
            except Exception as e:
                logger.error(f"    ❌ Error testing {contract['title']}: {str(e)}")
                results['contract_results'].append({
                    'title': contract['title'],
                    'error': str(e)
                })
        
        return results
    
    def identify_root_causes(self, blocking_analysis: Dict[str, Any], known_good_results: Dict[str, Any]) -> List[str]:
        """Identify root causes of the over-blocking issue"""
        logger.info("🔍 Identifying root causes...")
        
        root_causes = []
        
        # Analyze failure patterns
        failure_patterns = blocking_analysis.get('common_failure_patterns', {})
        total_failures = sum(failure_patterns.values())
        
        if total_failures > 0:
            logger.info(f"  📊 Total blocking instances: {total_failures}")
            
            # Check for dominant failure types
            for failure_type, count in sorted(failure_patterns.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_failures) * 100
                logger.info(f"    - {failure_type}: {count} ({percentage:.1f}%)")
                
                if percentage > 50:
                    root_causes.append(f"DOMINANT_FAILURE: {failure_type} accounts for {percentage:.1f}% of blocks")
                elif percentage > 25:
                    root_causes.append(f"MAJOR_FAILURE: {failure_type} accounts for {percentage:.1f}% of blocks")
        
        # Check if known-good contracts are failing
        if known_good_results['failed'] > known_good_results['passed']:
            root_causes.append("CRITIC_TOO_STRICT: Even simple, viable contracts are being blocked")
        
        # Check for 100% blocking rate
        total_contracts = blocking_analysis.get('total_contracts_tested', 0)
        total_blocked = sum(c['summary']['blocked_variants'] for c in blocking_analysis.get('contracts_analyzed', []))
        total_variants = sum(c['summary']['total_variants'] for c in blocking_analysis.get('contracts_analyzed', []))
        
        if total_variants > 0:
            block_rate = (total_blocked / total_variants) * 100
            logger.info(f"  📊 Overall blocking rate: {block_rate:.1f}%")
            
            if block_rate > 95:
                root_causes.append("COMPLETE_BLOCKING: >95% of variants are being blocked")
            elif block_rate > 80:
                root_causes.append("EXCESSIVE_BLOCKING: >80% of variants are being blocked")
        
        return root_causes
    
    def generate_recommendations(self, root_causes: List[str], failure_patterns: Dict[str, int]) -> List[str]:
        """Generate specific recommendations to fix the blocking issues"""
        logger.info("💡 Generating recommendations...")
        
        recommendations = []
        
        # Analyze dominant failure patterns
        if failure_patterns:
            top_failure = max(failure_patterns.items(), key=lambda x: x[1])
            failure_type, count = top_failure
            
            if failure_type == 'probability_bias':
                recommendations.append("ADJUST_PROBABILITY_THRESHOLDS: Relax probability bias detection (currently too sensitive)")
                recommendations.append("REVIEW_PROBABILITY_PROMPTS: Update LLM prompts to better assess genuine 50/50 scenarios")
            
            elif failure_type == 'market_viability':
                recommendations.append("CALIBRATE_MARKET_VIABILITY: Adjust market viability criteria for civic prediction markets")
                recommendations.append("UPDATE_VIABILITY_EXAMPLES: Provide better examples of viable civic contracts in prompts")
            
            elif failure_type == 'trading_balance':
                recommendations.append("REVIEW_TRADING_BALANCE: Recalibrate what constitutes balanced trading interest")
            
            elif failure_type == 'biased_framing':
                recommendations.append("TUNE_BIAS_DETECTION: Reduce false positives in political bias detection")
        
        # General recommendations based on root causes
        for cause in root_causes:
            if "CRITIC_TOO_STRICT" in cause:
                recommendations.append("REDUCE_CRITIC_WEIGHTS: Lower blocking weights from 1.0 to 0.8 for initial testing")
                recommendations.append("IMPLEMENT_GRADUATED_BLOCKING: Use warning levels before hard blocks")
            
            if "COMPLETE_BLOCKING" in cause:
                recommendations.append("EMERGENCY_THRESHOLD_ADJUSTMENT: Temporarily reduce all blocking thresholds by 20%")
                recommendations.append("ENABLE_ADMIN_BYPASS: Allow admin override for testing viable contracts")
        
        return recommendations
    
    def run_comprehensive_diagnosis(self) -> Dict[str, Any]:
        """Run complete diagnostic analysis"""
        logger.info("🚀 Starting comprehensive blocking diagnosis...")
        
        # Step 1: Analyze recent blocking patterns
        blocking_analysis = self.analyze_recent_blocking_patterns()
        
        # Step 2: Test known-good contracts
        known_good_results = self.test_known_good_contracts()
        
        # Step 3: Identify root causes
        root_causes = self.identify_root_causes(blocking_analysis, known_good_results)
        
        # Step 4: Generate recommendations
        failure_patterns = blocking_analysis.get('common_failure_patterns', {})
        recommendations = self.generate_recommendations(root_causes, failure_patterns)
        
        # Compile final results
        final_results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_contracts_tested': blocking_analysis.get('total_contracts_tested', 0),
                'known_good_pass_rate': (known_good_results['passed'] / max(known_good_results['total_tested'], 1)) * 100,
                'dominant_failure_types': list(failure_patterns.keys())[:3] if failure_patterns else [],
                'root_causes_identified': len(root_causes),
                'recommendations_generated': len(recommendations)
            },
            'blocking_analysis': blocking_analysis,
            'known_good_results': known_good_results,
            'root_causes': root_causes,
            'recommendations': recommendations
        }
        
        return final_results

def main():
    """Main diagnostic execution"""
    print("=" * 80)
    print("🔍 MEMPHIS CIVIC MARKET - CONTRACT BLOCKING DIAGNOSTIC")
    print("=" * 80)
    
    try:
        diagnostic = BlockingDiagnostic()
        results = diagnostic.run_comprehensive_diagnosis()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"blocking_diagnostic_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print("\n📊 DIAGNOSTIC SUMMARY:")
        print(f"   Total Contracts Tested: {results['summary']['total_contracts_tested']}")
        print(f"   Known-Good Pass Rate: {results['summary']['known_good_pass_rate']:.1f}%")
        print(f"   Root Causes Identified: {results['summary']['root_causes_identified']}")
        print(f"   Recommendations Generated: {results['summary']['recommendations_generated']}")
        
        print("\n🔍 TOP FAILURE TYPES:")
        for failure_type in results['summary']['dominant_failure_types']:
            count = results['blocking_analysis']['common_failure_patterns'].get(failure_type, 0)
            print(f"   - {failure_type}: {count} instances")
        
        print("\n🎯 ROOT CAUSES:")
        for cause in results['root_causes']:
            print(f"   - {cause}")
        
        print("\n💡 RECOMMENDATIONS:")
        for rec in results['recommendations']:
            print(f"   - {rec}")
        
        print(f"\n💾 Full results saved to: {results_file}")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Diagnostic failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
