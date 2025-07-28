#!/usr/bin/env python3
"""
Comprehensive Multi-Variant Reframing Engine Debug
Memphis Civic Market - July 27, 2025v3

Debug and improve multi-variant reframing engine by logging all variants,
analyzing failures, and identifying which strategies degrade market viability.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.multi_variant_reframing_engine import MultiVariantReframingEngine
from app.enhanced_contract_critic_enforcer import EnhancedContractCriticEnforcer

class VariantAnalyzer:
    """Comprehensive analyzer for multi-variant reframing issues"""
    
    def __init__(self):
        self.variant_engine = MultiVariantReframingEngine()
        self.critic = EnhancedContractCriticEnforcer()
        self.analysis_results = []
        
    def analyze_contract_variants(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze original contract and all generated variants"""
        
        print(f"🔍 ANALYZING CONTRACT: {contract['title']}")
        print(f"   Description: {contract['description']}")
        
        analysis = {
            'original_contract': contract,
            'original_analysis': None,
            'variants': [],
            'strategy_performance': {},
            'summary': {}
        }
        
        # Step 1: Analyze original contract
        print(f"\n📋 ORIGINAL CONTRACT ANALYSIS:")
        try:
            original_analysis = self.critic.analyze_single_contract(contract)
            analysis['original_analysis'] = {
                'overall_score': original_analysis.overall_score,
                'market_balance_score': original_analysis.market_balance_score,
                'passed': original_analysis.passed,
                'blocked': original_analysis.blocked,
                'blocking_issues': [
                    {
                        'issue_type': issue.get('issue_type'),
                        'description': issue.get('description'),
                        'severity': issue.get('severity')
                    } for issue in original_analysis.blocking_issues
                ],
                'all_issues': [
                    {
                        'issue_type': issue.get('issue_type'),
                        'description': issue.get('description'),
                        'severity': issue.get('severity')
                    } for issue in original_analysis.issues_found
                ]
            }
            
            print(f"   Market Balance Score: {original_analysis.market_balance_score:.3f}")
            print(f"   Passed: {original_analysis.passed}")
            print(f"   Blocked: {original_analysis.blocked}")
            print(f"   Blocking Issues: {len(original_analysis.blocking_issues)}")
            
        except Exception as e:
            print(f"   ❌ ERROR analyzing original: {str(e)}")
            analysis['original_analysis'] = {'error': str(e)}
        
        # Step 2: Generate and analyze all variants
        print(f"\n🔄 GENERATING VARIANTS:")
        try:
            # Get all reframing strategies from the engine
            strategies = self.variant_engine.reframing_strategies
            print(f"   Available strategies: {len(strategies)}")
            
            for strategy_name, strategy_config in strategies.items():
                print(f"\n   🎯 Testing Strategy: {strategy_name}")
                print(f"      Description: {strategy_config.get('description', 'No description')}")
                
                try:
                    # Generate variant using this strategy
                    variant = self.variant_engine._apply_reframing_strategy(
                        contract, strategy_name, strategy_config
                    )
                    
                    if variant:
                        print(f"      ✅ Variant generated")
                        print(f"         Title: {variant.get('title', 'No title')}")
                        print(f"         Description: {variant.get('description', 'No description')[:100]}...")
                        
                        # Analyze variant with critic
                        variant_analysis = self.critic.analyze_single_contract(variant)
                        
                        variant_result = {
                            'strategy': strategy_name,
                            'strategy_description': strategy_config.get('description'),
                            'variant': variant,
                            'analysis': {
                                'overall_score': variant_analysis.overall_score,
                                'market_balance_score': variant_analysis.market_balance_score,
                                'passed': variant_analysis.passed,
                                'blocked': variant_analysis.blocked,
                                'blocking_issues': [
                                    {
                                        'issue_type': issue.get('issue_type'),
                                        'description': issue.get('description'),
                                        'severity': issue.get('severity')
                                    } for issue in variant_analysis.blocking_issues
                                ],
                                'all_issues': [
                                    {
                                        'issue_type': issue.get('issue_type'),
                                        'description': issue.get('description'),
                                        'severity': issue.get('severity')
                                    } for issue in variant_analysis.issues_found
                                ]
                            }
                        }
                        
                        analysis['variants'].append(variant_result)
                        
                        print(f"         Market Balance: {variant_analysis.market_balance_score:.3f}")
                        print(f"         Passed: {variant_analysis.passed}")
                        print(f"         Blocked: {variant_analysis.blocked}")
                        if variant_analysis.blocking_issues:
                            print(f"         Blocking Issues: {[issue.get('issue_type') for issue in variant_analysis.blocking_issues]}")
                        
                        # Track strategy performance
                        if strategy_name not in analysis['strategy_performance']:
                            analysis['strategy_performance'][strategy_name] = {
                                'total': 0,
                                'passed': 0,
                                'blocked': 0,
                                'avg_market_balance': 0,
                                'blocking_reasons': []
                            }
                        
                        perf = analysis['strategy_performance'][strategy_name]
                        perf['total'] += 1
                        if variant_analysis.passed:
                            perf['passed'] += 1
                        if variant_analysis.blocked:
                            perf['blocked'] += 1
                            perf['blocking_reasons'].extend([
                                issue.get('issue_type') for issue in variant_analysis.blocking_issues
                            ])
                        perf['avg_market_balance'] = (
                            (perf['avg_market_balance'] * (perf['total'] - 1) + variant_analysis.market_balance_score) 
                            / perf['total']
                        )
                        
                    else:
                        print(f"      ❌ No variant generated")
                        
                except Exception as e:
                    print(f"      ❌ ERROR with strategy {strategy_name}: {str(e)}")
                    
        except Exception as e:
            print(f"   ❌ ERROR generating variants: {str(e)}")
        
        # Step 3: Generate summary
        total_variants = len(analysis['variants'])
        passed_variants = sum(1 for v in analysis['variants'] if v['analysis']['passed'])
        blocked_variants = sum(1 for v in analysis['variants'] if v['analysis']['blocked'])
        
        analysis['summary'] = {
            'total_variants': total_variants,
            'passed_variants': passed_variants,
            'blocked_variants': blocked_variants,
            'pass_rate': (passed_variants / total_variants * 100) if total_variants > 0 else 0,
            'original_passed': analysis['original_analysis'].get('passed', False) if analysis['original_analysis'] else False
        }
        
        return analysis
    
    def identify_failing_strategies(self, analysis: Dict[str, Any]) -> List[str]:
        """Identify strategies that consistently fail or degrade contracts"""
        
        failing_strategies = []
        
        for strategy, perf in analysis['strategy_performance'].items():
            # Strategy fails if:
            # 1. 100% blocked rate
            # 2. Average market balance < 0.5
            # 3. Consistently produces ambiguity issues
            
            block_rate = (perf['blocked'] / perf['total']) * 100 if perf['total'] > 0 else 0
            
            if block_rate >= 100:
                failing_strategies.append(f"{strategy} (100% blocked)")
            elif perf['avg_market_balance'] < 0.5:
                failing_strategies.append(f"{strategy} (low market balance: {perf['avg_market_balance']:.3f})")
            elif perf['blocking_reasons'].count('ambiguity') >= perf['total']:
                failing_strategies.append(f"{strategy} (consistent ambiguity)")
        
        return failing_strategies
    
    def generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations for fixing the reframing engine"""
        
        recommendations = []
        
        # Check if original passes but variants fail
        original_passed = analysis['summary']['original_passed']
        variant_pass_rate = analysis['summary']['pass_rate']
        
        if original_passed and variant_pass_rate < 50:
            recommendations.append("CRITICAL: Original contract passes but variants fail - reframing is degrading quality")
            recommendations.append("FIX: Always include original contract as a variant if it passes")
        
        # Identify problematic strategies
        failing_strategies = self.identify_failing_strategies(analysis)
        if failing_strategies:
            recommendations.append(f"REMOVE/FIX failing strategies: {', '.join(failing_strategies)}")
        
        # Check for common issues
        all_blocking_issues = []
        for variant in analysis['variants']:
            all_blocking_issues.extend([
                issue['issue_type'] for issue in variant['analysis']['blocking_issues']
            ])
        
        if all_blocking_issues.count('ambiguity') > len(analysis['variants']) * 0.5:
            recommendations.append("FIX: Reframing strategies are creating ambiguity - preserve actor, timeline, resolution")
        
        if all_blocking_issues.count('market_viability') > len(analysis['variants']) * 0.3:
            recommendations.append("FIX: Reframing strategies are degrading market viability - calibrate reframing logic")
        
        return recommendations

def main():
    """Main execution - comprehensive multi-variant analysis"""
    
    print("🔍 COMPREHENSIVE MULTI-VARIANT REFRAMING DEBUG")
    print("Focus: Identify and fix strategies that degrade market viability")
    print("=" * 80)
    
    # Test contract that we know passes critic analysis
    test_contract = {
        'title': 'Memphis City Council Infrastructure Bond Vote',
        'description': 'Will Memphis City Council approve the $50M infrastructure bond by March 31, 2025?',
        'probability': 0.5,
        'resolution_date': '2025-03-31',
        'category': 'civic',
        'resolution_criteria': 'Resolved YES if Memphis City Council votes to approve the infrastructure bond by March 31, 2025. Resolved NO otherwise.'
    }
    
    analyzer = VariantAnalyzer()
    analysis = analyzer.analyze_contract_variants(test_contract)
    
    # Output comprehensive results
    print(f"\n" + "=" * 80)
    print(f"📊 COMPREHENSIVE ANALYSIS RESULTS")
    print(f"=" * 80)
    
    print(f"\n📋 SUMMARY:")
    print(f"   Original Contract Passed: {analysis['summary']['original_passed']}")
    print(f"   Total Variants Generated: {analysis['summary']['total_variants']}")
    print(f"   Variants Passed: {analysis['summary']['passed_variants']}")
    print(f"   Variants Blocked: {analysis['summary']['blocked_variants']}")
    print(f"   Variant Pass Rate: {analysis['summary']['pass_rate']:.1f}%")
    
    print(f"\n🎯 STRATEGY PERFORMANCE:")
    for strategy, perf in analysis['strategy_performance'].items():
        block_rate = (perf['blocked'] / perf['total']) * 100 if perf['total'] > 0 else 0
        pass_rate = (perf['passed'] / perf['total']) * 100 if perf['total'] > 0 else 0
        print(f"   {strategy}:")
        print(f"      Pass Rate: {pass_rate:.1f}% ({perf['passed']}/{perf['total']})")
        print(f"      Block Rate: {block_rate:.1f}%")
        print(f"      Avg Market Balance: {perf['avg_market_balance']:.3f}")
        if perf['blocking_reasons']:
            print(f"      Common Blocks: {list(set(perf['blocking_reasons']))}")
    
    # Generate recommendations
    recommendations = analyzer.generate_recommendations(analysis)
    
    print(f"\n🔧 RECOMMENDATIONS:")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    
    # Determine success/failure
    original_passed = analysis['summary']['original_passed']
    variant_pass_rate = analysis['summary']['pass_rate']
    
    if original_passed and variant_pass_rate >= 50:
        print(f"\n✅ SUCCESS: Original passes and variants maintain quality")
        return 0
    elif original_passed and variant_pass_rate < 50:
        print(f"\n⚠️  DEGRADATION: Original passes but reframing degrades quality")
        print(f"   IMMEDIATE ACTION: Fix reframing strategies")
        return 1
    else:
        print(f"\n❌ FAILURE: Original contract fails - fix base contract first")
        return 1

if __name__ == "__main__":
    exit(main())
