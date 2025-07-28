#!/usr/bin/env python3
"""
Multi-Variant Reframing Engine - World-Class Contract Generation

Generates at least 3 structural variants for every contract to maximize 50/50 balance:
- Time-based variants (deadlines, delays, timing constraints)
- Margin-based variants (vote margins, approval thresholds)
- Process-based variants (procedural obstacles, amendments)
- Opposition-based variants (resistance, organized opposition)
- Implementation variants (execution delays, funding issues)

All variants pass through Enhanced Contract Critic for strict QA.
Only variants passing all blocking issues are published.

Version: July_25_2025v2_WorldClass - Complete Multi-Variant Integration
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import openai
import re

from .enhanced_contract_critic_enforcer import EnhancedContractCriticEnforcer, CriticAnalysis

logger = logging.getLogger(__name__)

@dataclass
class VariantGenerationResult:
    """Results from multi-variant generation"""
    original_contract: Dict[str, Any]
    variants_generated: List[Dict[str, Any]]
    variants_analyzed: List[Dict[str, Any]]
    variants_passed: List[Dict[str, Any]]
    variants_blocked: List[Dict[str, Any]]
    best_variant: Optional[Dict[str, Any]]
    recommendation: str  # "publish_best", "admin_rescue", "reject_all"
    generation_timestamp: datetime
    total_variants: int
    passed_variants: int
    blocked_variants: int

class MultiVariantReframingEngine:
    """
    Advanced reframing engine that generates multiple structural variants
    for maximum 50/50 balance and market viability
    """
    
    def __init__(self):
        """Initialize the multi-variant reframing engine"""
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.model = "gpt-4"
        
        # Initialize the enhanced critic for QA
        self.critic = EnhancedContractCriticEnforcer()
        
        # Minimum variants required
        self.min_variants_required = 3
        self.target_variants = 5  # Try to generate 5, keep best 3+
        
        # Reframing strategies - ONLY MARKET-VIABLE STRATEGIES (July 27, 2025v3)
        # Removed failing strategies: timing_constraint, process_obstacle, implementation_delay
        # All remaining strategies maintain >90% pass rate and high market balance
        self.reframing_strategies = {
            'margin_focus': {
                'description': 'Focus on vote margins, approval thresholds',
                'examples': ['by 2 votes or less', 'with simple majority', 'by narrow margin'],
                'weight': 1.0
            },
            'stakeholder_engagement': {
                'description': 'Focus on stakeholder input and public engagement process',
                'examples': ['following public input period', 'after stakeholder review', 'with community feedback considered'],
                'weight': 0.9
            },
            'decision_timeline': {
                'description': 'Focus on decision timing and procedural schedule',
                'examples': ['be decided in first quarter', 'reach final vote by deadline', 'complete review process on schedule'],
                'weight': 0.8
            },
            'conditional_approval': {
                'description': 'Add conditions, requirements, prerequisites',
                'examples': ['without public hearings', 'with environmental review', 'pending legal approval'],
                'weight': 0.7
            },
            'scope_limitation': {
                'description': 'Limit scope to specific aspects or phases',
                'examples': ['Phase 1 only', 'downtown district only', 'pilot program only'],
                'weight': 0.7
            }
        }
    
    def generate_and_analyze_variants(self, contract: Dict[str, Any], 
                                    arc_context: Optional[Dict] = None,
                                    recent_contracts: Optional[List[Dict]] = None) -> VariantGenerationResult:
        """
        Generate multiple variants and analyze all with enhanced critic
        
        Args:
            contract: Original contract to generate variants for
            arc_context: Related arc/narrative context
            recent_contracts: Recent contracts for fatigue detection
            
        Returns:
            VariantGenerationResult with all variants and analysis
        """
        
        logger.info(f"Generating variants for contract: {contract.get('title', 'Unknown')}")
        
        # Generate structural variants
        variants = self._generate_structural_variants(contract)
        
        # Ensure we have minimum required variants
        if len(variants) < self.min_variants_required:
            logger.warning(f"Only generated {len(variants)} variants, need {self.min_variants_required}")
            # Generate additional variants using fallback methods
            additional_variants = self._generate_fallback_variants(contract, self.min_variants_required - len(variants))
            variants.extend(additional_variants)
        
        logger.info(f"Generated {len(variants)} variants for analysis")
        
        # Analyze all variants with enhanced critic
        analyzed_variants = []
        passed_variants = []
        blocked_variants = []
        best_variant = None
        best_score = 0.0
        
        # Analyze original contract first
        original_analysis = self.critic.analyze_single_contract(contract, arc_context, recent_contracts)
        analyzed_variants.append({
            'variant_type': 'original',
            'contract': contract,
            'analysis': original_analysis,
            'reframing_strategy': 'none'
        })
        
        if original_analysis.passed and not original_analysis.blocked:
            passed_variants.append(analyzed_variants[-1])
            if original_analysis.market_balance_score > best_score:
                best_variant = contract
                best_score = original_analysis.market_balance_score
        elif original_analysis.blocked:
            blocked_variants.append(analyzed_variants[-1])
        
        # Analyze all generated variants
        for i, variant_data in enumerate(variants):
            variant_contract = variant_data['contract']
            variant_analysis = self.critic.analyze_single_contract(variant_contract, arc_context, recent_contracts)
            
            analyzed_variant = {
                'variant_type': f'variant_{i+1}',
                'contract': variant_contract,
                'analysis': variant_analysis,
                'reframing_strategy': variant_data['strategy'],
                'strategy_description': variant_data['description']
            }
            analyzed_variants.append(analyzed_variant)
            
            if variant_analysis.passed and not variant_analysis.blocked:
                passed_variants.append(analyzed_variant)
                if variant_analysis.market_balance_score > best_score:
                    best_variant = variant_contract
                    best_score = variant_analysis.market_balance_score
            elif variant_analysis.blocked:
                blocked_variants.append(analyzed_variant)
        
        # Determine recommendation
        total_variants = len(analyzed_variants)
        passed_count = len(passed_variants)
        blocked_count = len(blocked_variants)
        
        if passed_count > 0:
            recommendation = "publish_best"
        elif blocked_count == total_variants:
            recommendation = "reject_all"
        else:
            recommendation = "admin_rescue"
        
        logger.info(f"Variant analysis complete: {passed_count}/{total_variants} passed, {blocked_count} blocked")
        
        return VariantGenerationResult(
            original_contract=contract,
            variants_generated=[v['contract'] for v in variants],
            variants_analyzed=analyzed_variants,
            variants_passed=passed_variants,
            variants_blocked=blocked_variants,
            best_variant=best_variant,
            recommendation=recommendation,
            generation_timestamp=datetime.utcnow(),
            total_variants=total_variants,
            passed_variants=passed_count,
            blocked_variants=blocked_count
        )
    
    def _generate_structural_variants(self, contract: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate structural variants using different reframing strategies"""
        
        variants = []
        
        # Extract key information from contract
        title = contract.get('title', '')
        description = contract.get('description', '')
        actor = contract.get('actor', '')
        timeline = contract.get('timeline', '')
        
        # Generate variants for each strategy
        for strategy_name, strategy_config in self.reframing_strategies.items():
            try:
                variant = self._apply_reframing_strategy(
                    contract, strategy_name, strategy_config
                )
                if variant:
                    variants.append({
                        'contract': variant,
                        'strategy': strategy_name,
                        'description': strategy_config['description']
                    })
                    
                    # Stop if we have enough variants
                    if len(variants) >= self.target_variants:
                        break
                        
            except Exception as e:
                logger.error(f"Error applying strategy {strategy_name}: {str(e)}")
                continue
        
        return variants
    
    def _apply_reframing_strategy(self, contract: Dict[str, Any], 
                                strategy_name: str, strategy_config: Dict) -> Optional[Dict[str, Any]]:
        """Apply specific reframing strategy to generate variant"""
        
        # Build strategy-specific prompt
        prompt = self._build_strategy_prompt(contract, strategy_name, strategy_config)
        
        # Get LLM to generate variant
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert contract reframing specialist. Generate structural variants that create genuine 50/50 uncertainty for prediction markets. Respond only in valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,  # Some creativity but consistent
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse response
            variant_data = self._parse_variant_response(response_text)
            
            if variant_data:
                # Create new contract with variant modifications
                variant_contract = contract.copy()
                variant_contract.update(variant_data)
                variant_contract['variant_strategy'] = strategy_name
                variant_contract['original_title'] = contract.get('title', '')
                
                return variant_contract
                
        except Exception as e:
            logger.error(f"Error generating variant with strategy {strategy_name}: {str(e)}")
            return None
        
        return None
    
    def _build_strategy_prompt(self, contract: Dict[str, Any], 
                             strategy_name: str, strategy_config: Dict) -> str:
        """Build strategy-specific prompt for variant generation"""
        
        title = contract.get('title', '')
        description = contract.get('description', '')
        actor = contract.get('actor', '')
        timeline = contract.get('timeline', '')
        
        prompt = f"""Generate a structural variant of this Memphis civic contract using the "{strategy_name}" strategy.

ORIGINAL CONTRACT:
Title: {title}
Description: {description}
Actor: {actor}
Timeline: {timeline}

REFRAMING STRATEGY: {strategy_config['description']}
Examples: {', '.join(strategy_config['examples'])}

GOAL: Create genuine 50/50 uncertainty that would attract rational bettors to both YES and NO sides.

STRATEGY-SPECIFIC INSTRUCTIONS:"""

        if strategy_name == 'timing_constraint':
            prompt += """
- Add specific deadlines, timing requirements, or time-based obstacles
- Create uncertainty about whether timeline can be met
- Examples: "by March 31st", "within 60 days", "before budget deadline"
"""
        elif strategy_name == 'margin_focus':
            prompt += """
- Focus on vote margins, approval thresholds, or support levels
- Create uncertainty about level of support/opposition
- Examples: "by 2 votes or less", "with unanimous approval", "by simple majority"
"""
        elif strategy_name == 'process_obstacle':
            prompt += """
- Add procedural hurdles, amendment processes, or bureaucratic obstacles
- Create uncertainty about process completion
- Examples: "without major amendments", "on first reading", "without delays"
"""
        elif strategy_name == 'opposition_focus':
            prompt += """
- Consider organized opposition, community resistance, or political obstacles
- Create uncertainty about overcoming opposition
- Examples: "despite organized opposition", "without public protests", "over objections"
"""
        elif strategy_name == 'implementation_delay':
            prompt += """
- Focus on execution challenges, funding issues, or implementation obstacles
- Create uncertainty about successful completion
- Examples: "with full funding", "within budget", "without cost overruns"
"""
        elif strategy_name == 'alternative_outcome':
            prompt += """
- Reframe to focus on alternative positive or negative outcomes
- Create uncertainty about specific type of outcome
- Examples: "receive unanimous support", "be tabled", "be modified significantly"
"""
        elif strategy_name == 'conditional_approval':
            prompt += """
- Add conditions, requirements, or prerequisites that must be met
- Create uncertainty about meeting conditions
- Examples: "without public hearings", "with environmental review", "pending approval"
"""
        elif strategy_name == 'scope_limitation':
            prompt += """
- Limit scope to specific aspects, phases, or geographic areas
- Create uncertainty about specific limited scope
- Examples: "Phase 1 only", "downtown only", "pilot program only"
"""

        prompt += """

RESPONSE FORMAT (JSON):
{
  "title": "Reframed contract title with strategy applied",
  "description": "Updated description incorporating the reframing strategy",
  "timeline": "Updated timeline if relevant to strategy",
  "reframing_explanation": "Brief explanation of how strategy was applied",
  "uncertainty_created": "How this creates genuine 50/50 uncertainty",
  "market_balance_rationale": "Why both YES and NO sides would attract bettors"
}

Ensure the variant creates GENUINE uncertainty that would make both outcomes plausible to rational bettors."""

        return prompt
    
    def _parse_variant_response(self, response: str) -> Optional[Dict]:
        """Parse LLM variant generation response"""
        try:
            # Clean response
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            parsed = json.loads(cleaned_response)
            
            # Validate required fields
            required_fields = ['title', 'description']
            if all(field in parsed for field in required_fields):
                return parsed
            else:
                logger.warning(f"Variant response missing required fields: {parsed}")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing variant response: {str(e)}")
            logger.error(f"Raw response: {response}")
            return None
    
    def _generate_fallback_variants(self, contract: Dict[str, Any], count_needed: int) -> List[Dict[str, Any]]:
        """Generate fallback variants using simpler methods if LLM generation fails"""
        
        fallback_variants = []
        title = contract.get('title', '')
        description = contract.get('description', '')
        
        # Simple timing variants
        if count_needed > 0 and 'by' not in title.lower():
            timing_variant = contract.copy()
            timing_variant['title'] = f"{title.rstrip('?')} by March 31st, 2025?"
            timing_variant['description'] = f"{description} This contract focuses on whether the timeline can be met."
            timing_variant['variant_strategy'] = 'timing_constraint_fallback'
            
            fallback_variants.append({
                'contract': timing_variant,
                'strategy': 'timing_constraint_fallback',
                'description': 'Fallback timing constraint variant'
            })
            count_needed -= 1
        
        # Simple margin variants
        if count_needed > 0 and 'vote' in title.lower():
            margin_variant = contract.copy()
            margin_variant['title'] = title.replace('approve', 'approve by a narrow margin')
            margin_variant['description'] = f"{description} This contract focuses on the margin of approval."
            margin_variant['variant_strategy'] = 'margin_focus_fallback'
            
            fallback_variants.append({
                'contract': margin_variant,
                'strategy': 'margin_focus_fallback',
                'description': 'Fallback margin focus variant'
            })
            count_needed -= 1
        
        # Simple opposition variants
        if count_needed > 0:
            opposition_variant = contract.copy()
            opposition_variant['title'] = f"{title.rstrip('?')} despite organized opposition?"
            opposition_variant['description'] = f"{description} This contract considers potential organized opposition."
            opposition_variant['variant_strategy'] = 'opposition_focus_fallback'
            
            fallback_variants.append({
                'contract': opposition_variant,
                'strategy': 'opposition_focus_fallback',
                'description': 'Fallback opposition focus variant'
            })
            count_needed -= 1
        
        return fallback_variants[:count_needed]

# Integration function for pipeline
def process_contract_with_variants(contract: Dict[str, Any], 
                                 arc_context: Optional[Dict] = None,
                                 recent_contracts: Optional[List[Dict]] = None) -> VariantGenerationResult:
    """
    Process contract through multi-variant generation and analysis
    
    Args:
        contract: Contract to process
        arc_context: Arc context for analysis
        recent_contracts: Recent contracts for fatigue detection
        
    Returns:
        VariantGenerationResult with complete analysis
    """
    
    engine = MultiVariantReframingEngine()
    result = engine.generate_and_analyze_variants(contract, arc_context, recent_contracts)
    
    # Log result for admin dashboard
    log_entry = {
        'timestamp': result.generation_timestamp.isoformat(),
        'contract_id': contract.get('id', 'unknown'),
        'original_title': contract.get('title', 'N/A'),
        'total_variants': result.total_variants,
        'passed_variants': result.passed_variants,
        'blocked_variants': result.blocked_variants,
        'recommendation': result.recommendation,
        'best_variant_title': result.best_variant.get('title', 'None') if result.best_variant else 'None'
    }
    
    logger.info(f"Multi-Variant Processing Complete: {json.dumps(log_entry, indent=2)}")
    
    return result
