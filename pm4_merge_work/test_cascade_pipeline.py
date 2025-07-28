"""
Cascade Pipeline Test Suite - "Good Enough" Contract Yield
Memphis Civic Market - July 28, 2025

Test the multi-layer pipeline for cost efficiency and contract yield.
Validates the "maximize contracts per dollar" philosophy.
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, try to load manually
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

# Add app directory to path
sys.path.append('.')
sys.path.append('./app')

from app.cascade_pipeline_controller import CascadePipelineController, PipelineInput

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_cascade_pipeline():
    """Test the complete cascade pipeline with realistic Memphis headlines."""
    
    print("🚀 CASCADE PIPELINE TEST SUITE")
    print("=" * 60)
    print("Testing multi-layer 'good enough' contract generation")
    print("Goal: Maximize contracts per dollar, minimize over-blocking")
    print()
    
    # Test headlines covering various scenarios
    test_headlines = [
        # SHOULD PASS - Good civic contracts (Layer 0 + 1 + 2 + 3 pass)
        {
            "headline": "Memphis City Council to vote on 2025 budget proposal next Tuesday",
            "source": "Memphis Commercial Appeal",
            "expected_layer_0": True,
            "expected_layer_1": True,
            "expected_final": "PASS",
            "category": "Budget Vote"
        },
        {
            "headline": "Shelby County Commission considers new zoning ordinance for Midtown development",
            "source": "Memphis Business Journal", 
            "expected_layer_0": True,
            "expected_layer_1": True,
            "expected_final": "PASS",
            "category": "Zoning Decision"
        },
        {
            "headline": "Memphis Mayor announces decision on police reform initiative by December 15th",
            "source": "Action News 5",
            "expected_layer_0": True,
            "expected_layer_1": True,
            "expected_final": "PASS",
            "category": "Policy Decision"
        },
        
        # SHOULD BLOCK LAYER 0 - Missing civic elements
        {
            "headline": "Local restaurant opens new location downtown",
            "source": "Memphis Flyer",
            "expected_layer_0": False,
            "expected_final": "BLOCK_LAYER_0",
            "category": "Non-civic"
        },
        {
            "headline": "Weather forecast calls for rain this weekend",
            "source": "Weather Channel",
            "expected_layer_0": False,
            "expected_final": "BLOCK_LAYER_0", 
            "category": "Weather"
        },
        
        # SHOULD BLOCK LAYER 1 - Not bettable civic events
        {
            "headline": "Memphis City Council meeting scheduled for Monday",
            "source": "City of Memphis",
            "expected_layer_0": True,
            "expected_layer_1": False,
            "expected_final": "BLOCK_LAYER_1",
            "category": "Informational"
        },
        {
            "headline": "Mayor gives speech about Memphis history",
            "source": "Memphis Daily News",
            "expected_layer_0": True,
            "expected_layer_1": False,
            "expected_final": "BLOCK_LAYER_1",
            "category": "Ceremonial"
        },
        
        # CLUSTERING TEST - Similar headlines (second should be duplicate)
        {
            "headline": "MATA board to decide on bus route changes in January 2025",
            "source": "Memphis Bus Riders",
            "expected_layer_0": True,
            "expected_layer_1": True,
            "expected_final": "PASS",
            "category": "Transportation"
        },
        {
            "headline": "Memphis transit authority considers route modifications for new year",
            "source": "Transport Weekly",
            "expected_layer_0": True,
            "expected_layer_1": True,
            "expected_final": "BLOCK_CLUSTER",  # Should be clustered as duplicate
            "category": "Transportation Duplicate"
        },
        
        # EDGE CASES - Test relaxed blocking logic
        {
            "headline": "Memphis School Board reviews superintendent contract renewal",
            "source": "Education Weekly",
            "expected_layer_0": True,
            "expected_layer_1": True,
            "expected_final": "PASS",  # Should pass with relaxed logic
            "category": "Education"
        }
    ]
    
    # Initialize pipeline controller
    controller = CascadePipelineController()
    
    # Process each test headline
    results = []
    total_cost = 0.0
    contracts_generated = 0
    
    print("📊 PROCESSING TEST HEADLINES")
    print("-" * 60)
    
    for i, test_case in enumerate(test_headlines, 1):
        headline = test_case["headline"]
        source = test_case["source"]
        category = test_case["category"]
        
        print(f"\n🧪 Test {i}/{len(test_headlines)}: {category}")
        print(f"   Headline: {headline}")
        print(f"   Source: {source}")
        
        # Create pipeline input
        pipeline_input = PipelineInput(
            headline=headline,
            source=source,
            metadata={"test_category": category}
        )
        
        # Process through pipeline
        try:
            result = controller.process_headline(pipeline_input)
            results.append(result)
            
            # Track costs and contracts
            total_cost += result.total_cost_usd
            contracts_generated += len(result.contracts_generated)
            
            # Validate results
            layer_0_actual = result.layer_0_result.passed
            layer_1_actual = result.layer_1_result.passed if result.layer_1_result else False
            final_actual = result.final_status
            
            # Check expectations
            layer_0_match = layer_0_actual == test_case["expected_layer_0"]
            final_match = final_actual == test_case["expected_final"]
            
            print(f"   ✅ Layer 0: {'PASS' if layer_0_actual else 'FAIL'} (Expected: {'PASS' if test_case['expected_layer_0'] else 'FAIL'}) {'✓' if layer_0_match else '✗'}")
            
            if result.layer_1_result:
                layer_1_match = layer_1_actual == test_case.get("expected_layer_1", True)
                print(f"   ✅ Layer 1: {'PASS' if layer_1_actual else 'FAIL'} (Expected: {'PASS' if test_case.get('expected_layer_1', True) else 'FAIL'}) {'✓' if layer_1_match else '✗'}")
            
            print(f"   🎯 Final: {final_actual} (Expected: {test_case['expected_final']}) {'✓' if final_match else '✗'}")
            print(f"   💰 Cost: ${result.total_cost_usd:.4f}")
            print(f"   ⏱️  Time: {result.total_processing_time_ms:.1f}ms")
            print(f"   📝 Contracts: {len(result.contracts_generated)}")
            
            if result.user_feedback:
                print(f"   💬 Feedback: {result.user_feedback}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            results.append(None)
    
    # Generate summary statistics
    print("\n" + "=" * 60)
    print("📈 PIPELINE PERFORMANCE SUMMARY")
    print("=" * 60)
    
    # Calculate success rates
    successful_results = [r for r in results if r is not None]
    layer_0_passes = sum(1 for r in successful_results if r.layer_0_result.passed)
    layer_1_passes = sum(1 for r in successful_results if r.layer_1_result and r.layer_1_result.passed)
    final_passes = sum(1 for r in successful_results if r.final_status == "PASS")
    
    print(f"Headlines Processed: {len(test_headlines)}")
    print(f"Successful Runs: {len(successful_results)}")
    print(f"Layer 0 Pass Rate: {layer_0_passes}/{len(successful_results)} ({(layer_0_passes/len(successful_results)*100):.1f}%)")
    print(f"Layer 1 Pass Rate: {layer_1_passes}/{layer_0_passes} ({(layer_1_passes/layer_0_passes*100) if layer_0_passes > 0 else 0:.1f}%)")
    print(f"Final Pass Rate: {final_passes}/{len(successful_results)} ({(final_passes/len(successful_results)*100):.1f}%)")
    print(f"Contracts Generated: {contracts_generated}")
    print(f"Total Cost: ${total_cost:.4f}")
    print(f"Cost per Contract: ${(total_cost/contracts_generated):.4f}" if contracts_generated > 0 else "N/A")
    
    # Get detailed pipeline stats
    daily_stats = controller.get_daily_stats()
    print(f"\n📊 DETAILED LAYER STATISTICS:")
    print(f"Layer 0 - Pass: {daily_stats['layer_stats']['layer_0_pass']}, Fail: {daily_stats['layer_stats']['layer_0_fail']}")
    print(f"Layer 1 - Pass: {daily_stats['layer_stats']['layer_1_pass']}, Fail: {daily_stats['layer_stats']['layer_1_fail']}")
    print(f"Layer 2 - Primary: {daily_stats['layer_stats']['layer_2_primary']}, Duplicate: {daily_stats['layer_stats']['layer_2_duplicate']}")
    print(f"Layer 3 - Pass: {daily_stats['layer_stats']['layer_3_pass']}, Fail: {daily_stats['layer_stats']['layer_3_fail']}")
    
    # Assess "good enough" philosophy
    print(f"\n🎯 'GOOD ENOUGH' ASSESSMENT:")
    contract_yield = (contracts_generated / len(test_headlines)) * 100
    print(f"Contract Yield: {contract_yield:.1f}% (Target: >20%)")
    
    if contract_yield >= 20:
        print("✅ EXCELLENT: High contract yield achieved")
    elif contract_yield >= 10:
        print("⚠️  GOOD: Moderate contract yield")
    else:
        print("❌ NEEDS WORK: Low contract yield")
    
    cost_efficiency = total_cost / contracts_generated if contracts_generated > 0 else float('inf')
    print(f"Cost Efficiency: ${cost_efficiency:.4f} per contract (Target: <$0.50)")
    
    if cost_efficiency <= 0.50:
        print("✅ EXCELLENT: Cost-efficient generation")
    elif cost_efficiency <= 1.00:
        print("⚠️  GOOD: Reasonable cost efficiency")
    else:
        print("❌ EXPENSIVE: High cost per contract")
    
    # Narrative preservation check
    narrative_signals = sum(1 for r in successful_results if r.narrative_signals.get('narrative_potential', False))
    narrative_preservation = (narrative_signals / len(successful_results)) * 100 if successful_results else 0
    print(f"Narrative Preservation: {narrative_preservation:.1f}% (Target: >80%)")
    
    if narrative_preservation >= 80:
        print("✅ EXCELLENT: Strong narrative signal preservation")
    elif narrative_preservation >= 60:
        print("⚠️  GOOD: Moderate narrative preservation")
    else:
        print("❌ POOR: Low narrative signal preservation")
    
    print(f"\n🎉 CASCADE PIPELINE TEST COMPLETE")
    print("=" * 60)
    
    return {
        'total_headlines': len(test_headlines),
        'contracts_generated': contracts_generated,
        'total_cost': total_cost,
        'cost_per_contract': cost_efficiency,
        'contract_yield_percent': contract_yield,
        'narrative_preservation_percent': narrative_preservation,
        'daily_stats': daily_stats
    }

if __name__ == "__main__":
    # Ensure OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key before running the test")
        sys.exit(1)
    
    # Run the test
    test_results = test_cascade_pipeline()
    
    # Save results for analysis
    import json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"cascade_pipeline_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    print(f"💾 Test results saved to: {results_file}")
