"""
Cascade Pipeline Controller - Multi-Layer Contract Generation
Memphis Civic Market - July 28, 2025

This is the main orchestrator for the "Good Enough" contract yield pipeline.
Maximizes contract output while minimizing LLM costs through layered filtering.

Pipeline Layers:
- Layer 0: Heuristic Civic Filter (Free)
- Layer 1: Fast LLM Classifier (Cheap - GPT-3.5)
- Layer 2: Clustering/Deduplication
- Layer 3: Full Pipeline (Expensive - GPT-4)
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

from .layer_0_heuristic_filter import Layer0HeuristicFilter, HeuristicFilterResult
from .layer_1_fast_classifier import Layer1FastClassifier, FastClassifierResult
from .layer_2_clustering import Layer2Clustering, ClusteringResult
from .enhanced_contract_critic_enforcer import EnhancedContractCriticEnforcer
from .multi_variant_reframing_engine import MultiVariantReframingEngine

@dataclass
class PipelineInput:
    """Input to the cascade pipeline"""
    headline: str
    source: str
    metadata: Dict = None
    user_id: str = None
    submission_type: str = "feed"  # feed, user_submission, admin_override

@dataclass
class PipelineResult:
    """Complete result from cascade pipeline"""
    input_headline: str
    final_status: str  # PASS, BLOCK_LAYER_0, BLOCK_LAYER_1, BLOCK_CLUSTER, BLOCK_LAYER_3
    contracts_generated: List[Dict]
    layer_0_result: HeuristicFilterResult
    layer_1_result: Optional[FastClassifierResult]
    layer_2_result: Optional[ClusteringResult]
    layer_3_results: List[Dict]
    total_cost_usd: float
    total_processing_time_ms: float
    narrative_signals: Dict  # For ostension engine
    admin_review_required: bool
    user_feedback: str

class CascadePipelineController:
    """
    Main controller for the cascade contract generation pipeline.
    Implements cost-efficient, high-yield contract generation.
    """
    
    def __init__(self, openai_api_key: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize pipeline layers
        self.layer_0 = Layer0HeuristicFilter()
        self.layer_1 = Layer1FastClassifier(api_key=openai_api_key)
        self.layer_2 = Layer2Clustering()
        
        # Full pipeline components (expensive)
        self.critic_enforcer = EnhancedContractCriticEnforcer()
        self.variant_engine = MultiVariantReframingEngine()
        
        # Cost tracking
        self.total_cost_today = 0.0
        self.contracts_generated_today = 0
        self.headlines_processed_today = 0
        
        # Pipeline statistics
        self.layer_stats = {
            'layer_0_pass': 0, 'layer_0_fail': 0,
            'layer_1_pass': 0, 'layer_1_fail': 0,
            'layer_2_primary': 0, 'layer_2_duplicate': 0,
            'layer_3_pass': 0, 'layer_3_fail': 0
        }
    
    def process_headline(self, pipeline_input: PipelineInput) -> PipelineResult:
        """
        Process a single headline through the cascade pipeline.
        
        Args:
            pipeline_input: Input containing headline and metadata
            
        Returns:
            PipelineResult with complete processing results
        """
        start_time = datetime.now()
        total_cost = 0.0
        contracts_generated = []
        admin_review_required = False
        
        headline = pipeline_input.headline
        source = pipeline_input.source
        
        self.logger.info(f"Processing headline: {headline[:100]}...")
        
        # LAYER 0: HEURISTIC CIVIC FILTER (FREE)
        layer_0_result = self.layer_0.filter_headline(headline, source)
        
        if not layer_0_result.passed:
            self.layer_stats['layer_0_fail'] += 1
            
            # Generate user feedback
            user_feedback = f"Missing required elements: {', '.join(layer_0_result.missing_elements)}"
            if 'civic_agent' in layer_0_result.missing_elements:
                user_feedback += ". Try including a civic entity like 'Memphis City Council' or 'Mayor'."
            if 'action_verb' in layer_0_result.missing_elements:
                user_feedback += ". Try including an action like 'vote', 'approve', or 'propose'."
            if 'timeframe' in layer_0_result.missing_elements:
                user_feedback += ". Try including a date or deadline."
            
            return self._create_pipeline_result(
                pipeline_input, "BLOCK_LAYER_0", contracts_generated,
                layer_0_result, None, None, [],
                total_cost, (datetime.now() - start_time).total_seconds() * 1000,
                self._create_narrative_signals(headline, source, "layer_0_block"),
                admin_review_required, user_feedback
            )
        
        self.layer_stats['layer_0_pass'] += 1
        
        # LAYER 1: FAST LLM CLASSIFIER (CHEAP)
        layer_1_result = self.layer_1.classify_headline(headline, source)
        total_cost += layer_1_result.cost_usd
        
        if not layer_1_result.passed:
            self.layer_stats['layer_1_fail'] += 1
            
            user_feedback = f"Not suitable for prediction market: {layer_1_result.reason}"
            if layer_1_result.confidence < 0.3:
                user_feedback += " Try making the civic decision or controversy more specific."
            
            return self._create_pipeline_result(
                pipeline_input, "BLOCK_LAYER_1", contracts_generated,
                layer_0_result, layer_1_result, None, [],
                total_cost, (datetime.now() - start_time).total_seconds() * 1000,
                self._create_narrative_signals(headline, source, "layer_1_block", layer_1_result),
                admin_review_required, user_feedback
            )
        
        self.layer_stats['layer_1_pass'] += 1
        
        # LAYER 2: CLUSTERING/DEDUPLICATION
        layer_2_result = self.layer_2.find_or_create_cluster(headline, layer_1_result.entity_tags)
        
        if not layer_2_result.is_primary:
            self.layer_stats['layer_2_duplicate'] += 1
            
            user_feedback = f"Similar contract already processed today: {layer_2_result.reason}"
            
            return self._create_pipeline_result(
                pipeline_input, "BLOCK_CLUSTER", contracts_generated,
                layer_0_result, layer_1_result, layer_2_result, [],
                total_cost, (datetime.now() - start_time).total_seconds() * 1000,
                self._create_narrative_signals(headline, source, "cluster_duplicate", layer_1_result),
                admin_review_required, user_feedback
            )
        
        self.layer_stats['layer_2_primary'] += 1
        
        # LAYER 3: FULL PIPELINE (EXPENSIVE - GPT-4)
        layer_3_results = []
        
        try:
            # Create base contract from headline
            base_contract = self._headline_to_contract(headline, layer_1_result)
            
            # Generate variants using multi-variant engine
            variant_results = self.variant_engine.generate_and_analyze_variants(base_contract)
            layer_3_results.append({"stage": "variant_generation", "result": variant_results})
            
            # Track costs from variant generation (estimate based on GPT-4 usage)
            # MultiVariantReframingEngine uses GPT-4, estimate ~$0.03 per variant generation
            estimated_variant_cost = len(variant_results.variants_generated) * 0.03
            total_cost += estimated_variant_cost
            
            # Use the already-analyzed variants from the engine
            # The MultiVariantReframingEngine already runs critic analysis
            passed_contracts = variant_results.variants_passed
            
            # Log the variant analysis results
            layer_3_results.append({
                "stage": "variant_analysis_summary", 
                "result": {
                    "total_variants": variant_results.total_variants,
                    "passed_variants": variant_results.passed_variants,
                    "blocked_variants": variant_results.blocked_variants,
                    "recommendation": variant_results.recommendation
                }
            })
            
            if passed_contracts:
                self.layer_stats['layer_3_pass'] += 1
                contracts_generated = passed_contracts
                final_status = "PASS"
                user_feedback = f"Generated {len(passed_contracts)} viable contract(s)"
                self.contracts_generated_today += len(passed_contracts)
            else:
                self.layer_stats['layer_3_fail'] += 1
                final_status = "BLOCK_LAYER_3"
                user_feedback = "Contract failed market viability checks. Try rephrasing for more balanced outcomes."
                admin_review_required = True  # Flag for admin review
            
        except Exception as e:
            self.logger.error(f"Layer 3 processing failed: {str(e)}")
            layer_3_results.append({"stage": "error", "result": str(e)})
            final_status = "BLOCK_LAYER_3"
            user_feedback = f"Processing error: {str(e)}"
            admin_review_required = True
        
        # Update tracking
        self.total_cost_today += total_cost
        self.headlines_processed_today += 1
        
        # Calculate total processing time
        total_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return self._create_pipeline_result(
            pipeline_input, final_status, contracts_generated,
            layer_0_result, layer_1_result, layer_2_result, layer_3_results,
            total_cost, total_time_ms,
            self._create_narrative_signals(headline, source, final_status, layer_1_result),
            admin_review_required, user_feedback
        )
    
    def _should_pass_contract(self, critic_result) -> bool:
        """
        Relaxed blocking logic - only block truly problematic contracts.
        Implements "good enough" philosophy.
        """
        if not hasattr(critic_result, 'issues') or not critic_result.issues:
            return True  # No issues = pass
        
        # Only block on critical issues that make contracts truly unbettable
        blocking_issues = []
        for issue in critic_result.issues:
            issue_type = issue.get('issue_type', '')
            severity = issue.get('severity', '')
            
            # BLOCK ONLY these critical cases:
            if severity == 'critical':
                if issue_type == 'unbettable':
                    blocking_issues.append(issue)
                elif issue_type == 'probability_bias':
                    # Only block if truly extreme (>90% or <10%)
                    description = issue.get('description', '').lower()
                    if any(phrase in description for phrase in ['near-certain', 'impossible', '>90%', '<10%', 'foregone conclusion']):
                        blocking_issues.append(issue)
        
        # Pass if no truly blocking issues
        return len(blocking_issues) == 0
    
    def _headline_to_contract(self, headline: str, layer_1_result: FastClassifierResult) -> Dict:
        """Convert headline to base contract format."""
        return {
            'title': headline,
            'description': f"Prediction market for: {headline}",
            'actor': ', '.join(layer_1_result.entity_tags) if layer_1_result.entity_tags else "Memphis civic entity",
            'timeline': "To be determined based on headline context",
            'resolution_criteria': "Official announcement or documented outcome",
            'source': headline,
            'topic': layer_1_result.topic,
            'entity_tags': layer_1_result.entity_tags
        }
    
    def _create_narrative_signals(self, headline: str, source: str, status: str, layer_1_result: FastClassifierResult = None) -> Dict:
        """Create narrative signals for ostension engine."""
        return {
            'headline': headline,
            'source': source,
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'topic': layer_1_result.topic if layer_1_result else "unknown",
            'entities': layer_1_result.entity_tags if layer_1_result else [],
            'narrative_potential': status in ['PASS', 'layer_1_block', 'cluster_duplicate']  # Include in narrative even if not contracted
        }
    
    def _create_pipeline_result(self, pipeline_input: PipelineInput, final_status: str,
                              contracts_generated: List[Dict], layer_0_result: HeuristicFilterResult,
                              layer_1_result: Optional[FastClassifierResult],
                              layer_2_result: Optional[ClusteringResult],
                              layer_3_results: List[Dict], total_cost_usd: float,
                              total_processing_time_ms: float, narrative_signals: Dict,
                              admin_review_required: bool, user_feedback: str) -> PipelineResult:
        """Create a complete pipeline result."""
        return PipelineResult(
            input_headline=pipeline_input.headline,
            final_status=final_status,
            contracts_generated=contracts_generated,
            layer_0_result=layer_0_result,
            layer_1_result=layer_1_result,
            layer_2_result=layer_2_result,
            layer_3_results=layer_3_results,
            total_cost_usd=total_cost_usd,
            total_processing_time_ms=total_processing_time_ms,
            narrative_signals=narrative_signals,
            admin_review_required=admin_review_required,
            user_feedback=user_feedback
        )
    
    def get_daily_stats(self) -> Dict:
        """Get daily pipeline statistics."""
        return {
            'headlines_processed': self.headlines_processed_today,
            'contracts_generated': self.contracts_generated_today,
            'total_cost_usd': self.total_cost_today,
            'cost_per_contract': self.total_cost_today / self.contracts_generated_today if self.contracts_generated_today > 0 else 0,
            'layer_stats': self.layer_stats.copy(),
            'pass_rates': {
                'layer_0': self.layer_stats['layer_0_pass'] / (self.layer_stats['layer_0_pass'] + self.layer_stats['layer_0_fail']) if (self.layer_stats['layer_0_pass'] + self.layer_stats['layer_0_fail']) > 0 else 0,
                'layer_1': self.layer_stats['layer_1_pass'] / (self.layer_stats['layer_1_pass'] + self.layer_stats['layer_1_fail']) if (self.layer_stats['layer_1_pass'] + self.layer_stats['layer_1_fail']) > 0 else 0,
                'layer_2': self.layer_stats['layer_2_primary'] / (self.layer_stats['layer_2_primary'] + self.layer_stats['layer_2_duplicate']) if (self.layer_stats['layer_2_primary'] + self.layer_stats['layer_2_duplicate']) > 0 else 0,
                'layer_3': self.layer_stats['layer_3_pass'] / (self.layer_stats['layer_3_pass'] + self.layer_stats['layer_3_fail']) if (self.layer_stats['layer_3_pass'] + self.layer_stats['layer_3_fail']) > 0 else 0
            }
        }
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at midnight)."""
        self.total_cost_today = 0.0
        self.contracts_generated_today = 0
        self.headlines_processed_today = 0
        self.layer_stats = {k: 0 for k in self.layer_stats.keys()}
