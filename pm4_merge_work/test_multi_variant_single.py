#!/usr/bin/env python3
"""
Test Multi-Variant Engine with Single Working Contract
Memphis Civic Market - July 27, 2025v3

Test the same contract that passed critic analysis through the multi-variant engine
to ensure end-to-end pipeline functionality before scaling.
"""

import os
import sys
import json
from datetime import datetime

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.multi_variant_reframing_engine import MultiVariantReframingEngine

def test_single_contract_multi_variant():
    """Test the working contract through multi-variant engine"""
    
    print("🔄 MULTI-VARIANT ENGINE TEST - SINGLE CONTRACT")
    print("=" * 60)
    
    # Same contract that passed critic analysis
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
    
    variant_engine = MultiVariantReframingEngine()
    
    try:
        print(f"\n🔄 Generating and analyzing variants...")
        
        # Generate and analyze variants
        result = variant_engine.generate_and_analyze_variants(test_contract)
        
        # Extract results
        print(f"\n📊 MULTI-VARIANT RESULTS:")
        print(f"   Total Variants Generated: {len(result.variants) if hasattr(result, 'variants') else 'Unknown'}")
        print(f"   Variants Passed: {result.variants_passed if hasattr(result, 'variants_passed') else 'Unknown'}")
        print(f"   Variants Blocked: {result.variants_blocked if hasattr(result, 'variants_blocked') else 'Unknown'}")
        
        if hasattr(result, 'variants') and result.variants:
            print(f"\n📝 VARIANT DETAILS:")
            for i, variant in enumerate(result.variants[:3]):  # Show first 3 variants
                print(f"   Variant {i+1}:")
                print(f"      Title: {variant.get('title', 'Unknown')}")
                print(f"      Strategy: {variant.get('reframing_strategy', 'Unknown')}")
                print(f"      Passed: {variant.get('passed', 'Unknown')}")
                print(f"      Blocked: {variant.get('blocked', 'Unknown')}")
        
        # Calculate success metrics
        total_variants = len(result.variants) if hasattr(result, 'variants') else 0
        passed_variants = result.variants_passed if hasattr(result, 'variants_passed') else 0
        
        if total_variants > 0:
            pass_rate = (passed_variants / total_variants) * 100
            print(f"\n📈 PERFORMANCE METRICS:")
            print(f"   Pass Rate: {pass_rate:.1f}%")
            print(f"   Minimum Required: ≥1 variant passing")
            
            if passed_variants > 0:
                print(f"   ✅ SUCCESS: {passed_variants} variant(s) passed critic analysis")
                return True, f"{passed_variants}/{total_variants} variants passed"
            else:
                print(f"   ❌ FAILURE: No variants passed critic analysis")
                return False, f"0/{total_variants} variants passed - all blocked"
        else:
            print(f"   ❌ ERROR: No variants generated")
            return False, "No variants generated"
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False, f"Multi-variant error: {str(e)}"

def main():
    """Main execution - test multi-variant with single working contract"""
    
    print("🎯 MULTI-VARIANT SINGLE CONTRACT TEST")
    print("Focus: Ensure working contract generates viable variants")
    print("=" * 60)
    
    success, reason = test_single_contract_multi_variant()
    
    print(f"\n" + "=" * 60)
    print(f"🎯 RESULT: {'SUCCESS' if success else 'FAILURE'}")
    print(f"Reason: {reason}")
    
    if success:
        print(f"\n✅ NEXT STEPS:")
        print(f"   1. Test same contract through full pipeline enforcer")
        print(f"   2. Validate end-to-end processing works")
        print(f"   3. Only then scale to batch processing")
    else:
        print(f"\n🔧 FIX NEEDED:")
        print(f"   1. Address multi-variant issue: {reason}")
        print(f"   2. Ensure variants inherit working contract properties")
        print(f"   3. Retest before proceeding to pipeline")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
