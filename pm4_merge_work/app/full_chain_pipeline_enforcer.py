#!/usr/bin/env python3
"""
Full-Chain Pipeline Enforcer - World-Class 50/50 Contract Flow

Complete end-to-end pipeline with strict enforcement:
1. Memphis headline ingestion
2. Multi-variant reframing (minimum 3 variants)
3. Enhanced critic analysis with blocking enforcement
4. Admin rescue workflow for flagged contracts
5. Publication only for contracts passing all QA

Targets >80% pipeline reliability with strict 50/50 enforcement.
No drift, no weak spots - only genuinely bettable contracts published.

Version: July_25_2025v2_WorldClass - Complete Pipeline Integration
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
import traceback

from .multi_variant_reframing_engine import MultiVariantReframingEngine, VariantGenerationResult
from .enhanced_contract_critic_enforcer import EnhancedContractCriticEnforcer, CriticAnalysis, log_critic_analysis

logger = logging.getLogger(__name__)

@dataclass
class PipelineStageResult:
    """Result of a single pipeline stage"""
    stage_name: str
    status: str  # "SUCCESS", "FAILED", "BLOCKED", "ADMIN_RESCUE"
    input_count: int
    output_count: int
    blocked_count: int
    execution_time: float
    error_message: Optional[str] = None
    stage_details: Optional[Dict] = None

@dataclass
class ContractPipelineResult:
    """Complete pipeline processing result for a single contract"""
    contract_id: str
    original_title: str
    pipeline_status: str  # "PUBLISHED", "BLOCKED", "ADMIN_RESCUE", "FAILED"
    stages_completed: List[PipelineStageResult]
    final_contract: Optional[Dict] = None
    variants_generated: int = 0
    variants_passed: int = 0
    variants_blocked: int = 0
    blocking_issues: List[str] = None
    admin_rescue_reason: Optional[str] = None
    processing_time: float = 0.0
    timestamp: datetime = None

@dataclass
class BatchPipelineResult:
    """Results from processing a batch of contracts"""
    batch_id: str
    total_contracts: int
    published_contracts: int
    blocked_contracts: int
    admin_rescue_contracts: int
    failed_contracts: int
    pipeline_reliability: float  # % of contracts successfully processed
    enforcement_rate: float  # % of contracts blocked by critic
    processing_time: float
    timestamp: datetime
    contract_results: List[ContractPipelineResult]
    stage_summary: Dict[str, PipelineStageResult]

class FullChainPipelineEnforcer:
    """
    Complete pipeline enforcer with world-class 50/50 contract flow enforcement
    """
    
    def __init__(self):
        """Initialize the full-chain pipeline enforcer"""
        
        # Initialize core components
        self.variant_engine = MultiVariantReframingEngine()
        self.critic_enforcer = EnhancedContractCriticEnforcer()
        
        # Pipeline configuration
        self.target_reliability = 0.8  # >80% pipeline reliability target
        self.min_variants_required = 3
        self.max_processing_time = 300  # 5 minutes max per contract
        
        # Enforcement thresholds
        self.market_balance_threshold = 0.8
        self.quality_threshold = 0.8
        
        # Admin rescue criteria
        self.admin_rescue_triggers = {
            'high_drama_score',  # High civic drama but blocked
            'critical_civic_event',  # Important civic event but problematic
            'close_market_balance',  # Close to passing but blocked
            'variant_potential'  # Some variants passed, others blocked
        }
    
    def process_batch_contracts(self, contracts: List[Dict[str, Any]], 
                              batch_id: str = None,
                              arc_context: Optional[Dict] = None) -> BatchPipelineResult:
        """
        Process a batch of contracts through the complete pipeline
        
        Args:
            contracts: List of contracts to process
            batch_id: Identifier for this batch
            arc_context: Arc context for analysis
            
        Returns:
            BatchPipelineResult with complete batch analysis
        """
        
        if not batch_id:
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting batch processing: {batch_id} with {len(contracts)} contracts")
        
        start_time = datetime.utcnow()
        contract_results = []
        
        # Counters
        published_count = 0
        blocked_count = 0
        admin_rescue_count = 0
        failed_count = 0
        
        # Stage summaries
        stage_summaries = {
            'variant_generation': PipelineStageResult('variant_generation', 'SUCCESS', 0, 0, 0, 0.0),
            'critic_analysis': PipelineStageResult('critic_analysis', 'SUCCESS', 0, 0, 0, 0.0),
            'admin_rescue': PipelineStageResult('admin_rescue', 'SUCCESS', 0, 0, 0, 0.0),
            'publication': PipelineStageResult('publication', 'SUCCESS', 0, 0, 0, 0.0)
        }
        
        # Process each contract
        for i, contract in enumerate(contracts):
            try:
                logger.info(f"Processing contract {i+1}/{len(contracts)}: {contract.get('title', 'Unknown')}")
                
                # Process single contract through full pipeline
                result = self.process_single_contract(contract, arc_context)
                contract_results.append(result)
                
                # Update counters
                if result.pipeline_status == 'PUBLISHED':
                    published_count += 1
                elif result.pipeline_status == 'BLOCKED':
                    blocked_count += 1
                elif result.pipeline_status == 'ADMIN_RESCUE':
                    admin_rescue_count += 1
                else:
                    failed_count += 1
                
                # Update stage summaries
                for stage_result in result.stages_completed:
                    stage_name = stage_result.stage_name
                    if stage_name in stage_summaries:
                        summary = stage_summaries[stage_name]
                        summary.input_count += stage_result.input_count
                        summary.output_count += stage_result.output_count
                        summary.blocked_count += stage_result.blocked_count
                        summary.execution_time += stage_result.execution_time
                
            except Exception as e:
                logger.error(f"Error processing contract {i+1}: {str(e)}")
                logger.error(traceback.format_exc())
                
                # Create failed result
                failed_result = ContractPipelineResult(
                    contract_id=contract.get('id', f'unknown_{i}'),
                    original_title=contract.get('title', 'Unknown'),
                    pipeline_status='FAILED',
                    stages_completed=[],
                    processing_time=0.0,
                    timestamp=datetime.utcnow()
                )
                contract_results.append(failed_result)
                failed_count += 1
        
        # Calculate metrics
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        total_contracts = len(contracts)
        successfully_processed = published_count + blocked_count + admin_rescue_count
        pipeline_reliability = successfully_processed / total_contracts if total_contracts > 0 else 0.0
        enforcement_rate = blocked_count / total_contracts if total_contracts > 0 else 0.0
        
        # Create batch result
        batch_result = BatchPipelineResult(
            batch_id=batch_id,
            total_contracts=total_contracts,
            published_contracts=published_count,
            blocked_contracts=blocked_count,
            admin_rescue_contracts=admin_rescue_count,
            failed_contracts=failed_count,
            pipeline_reliability=pipeline_reliability,
            enforcement_rate=enforcement_rate,
            processing_time=processing_time,
            timestamp=end_time,
            contract_results=contract_results,
            stage_summary=stage_summaries
        )
        
        # Log batch results
        self._log_batch_results(batch_result)
        
        logger.info(f"Batch processing complete: {batch_id}")
        logger.info(f"Results: {published_count} published, {blocked_count} blocked, {admin_rescue_count} admin rescue, {failed_count} failed")
        logger.info(f"Pipeline reliability: {pipeline_reliability:.1%}, Enforcement rate: {enforcement_rate:.1%}")
        
        return batch_result
    
    def process_single_contract(self, contract: Dict[str, Any], 
                              arc_context: Optional[Dict] = None) -> ContractPipelineResult:
        """
        Process a single contract through the complete pipeline
        
        Args:
            contract: Contract to process
            arc_context: Arc context for analysis
            
        Returns:
            ContractPipelineResult with complete processing details
        """
        
        contract_id = contract.get('id', f"contract_{datetime.now().strftime('%H%M%S')}")
        original_title = contract.get('title', 'Unknown')
        start_time = datetime.utcnow()
        
        stages_completed = []
        pipeline_status = 'FAILED'
        final_contract = None
        blocking_issues = []
        admin_rescue_reason = None
        
        try:
            # Stage 1: Multi-Variant Generation
            logger.debug(f"Stage 1: Generating variants for {contract_id}")
            variant_start = datetime.utcnow()
            
            variant_result = self.variant_engine.generate_and_analyze_variants(
                contract, arc_context
            )
            
            variant_time = (datetime.utcnow() - variant_start).total_seconds()
            
            # Record variant generation stage
            variant_stage = PipelineStageResult(
                stage_name='variant_generation',
                status='SUCCESS',
                input_count=1,
                output_count=variant_result.total_variants,
                blocked_count=variant_result.blocked_variants,
                execution_time=variant_time,
                stage_details={
                    'variants_generated': variant_result.total_variants,
                    'variants_passed': variant_result.passed_variants,
                    'variants_blocked': variant_result.blocked_variants,
                    'recommendation': variant_result.recommendation
                }
            )
            stages_completed.append(variant_stage)
            
            # Stage 2: Critic Analysis & Enforcement
            logger.debug(f"Stage 2: Critic analysis for {contract_id}")
            critic_start = datetime.utcnow()
            
            # Get the best analysis result
            if variant_result.best_variant:
                best_analysis = None
                for analyzed_variant in variant_result.variants_analyzed:
                    if analyzed_variant['contract'] == variant_result.best_variant:
                        best_analysis = analyzed_variant['analysis']
                        break
                
                if not best_analysis:
                    # Fallback to original analysis
                    best_analysis = variant_result.variants_analyzed[0]['analysis']
            else:
                # No variants passed, use original analysis
                best_analysis = variant_result.variants_analyzed[0]['analysis']
            
            critic_time = (datetime.utcnow() - critic_start).total_seconds()
            
            # Extract blocking issues
            if best_analysis.blocking_issues:
                blocking_issues = [issue['issue_type'] for issue in best_analysis.blocking_issues]
            
            # Record critic analysis stage
            critic_stage = PipelineStageResult(
                stage_name='critic_analysis',
                status='SUCCESS' if best_analysis.passed else 'BLOCKED',
                input_count=variant_result.total_variants,
                output_count=1 if best_analysis.passed else 0,
                blocked_count=1 if best_analysis.blocked else 0,
                execution_time=critic_time,
                stage_details={
                    'overall_score': best_analysis.overall_score,
                    'market_balance_score': best_analysis.market_balance_score,
                    'blocked': best_analysis.blocked,
                    'blocking_issues': blocking_issues,
                    'admin_override_required': best_analysis.admin_override_required
                }
            )
            stages_completed.append(critic_stage)
            
            # Stage 3: Admin Rescue Decision
            logger.debug(f"Stage 3: Admin rescue evaluation for {contract_id}")
            rescue_start = datetime.utcnow()
            
            requires_admin_rescue = self._evaluate_admin_rescue(variant_result, best_analysis, contract)
            
            rescue_time = (datetime.utcnow() - rescue_start).total_seconds()
            
            # Record admin rescue stage
            rescue_stage = PipelineStageResult(
                stage_name='admin_rescue',
                status='ADMIN_RESCUE' if requires_admin_rescue else 'SUCCESS',
                input_count=1,
                output_count=0 if requires_admin_rescue else 1,
                blocked_count=0,
                execution_time=rescue_time,
                stage_details={
                    'requires_rescue': requires_admin_rescue,
                    'rescue_reason': admin_rescue_reason
                }
            )
            stages_completed.append(rescue_stage)
            
            # Stage 4: Publication Decision
            logger.debug(f"Stage 4: Publication decision for {contract_id}")
            pub_start = datetime.utcnow()
            
            if requires_admin_rescue:
                pipeline_status = 'ADMIN_RESCUE'
                admin_rescue_reason = self._generate_admin_rescue_reason(variant_result, best_analysis)
            elif best_analysis.passed and not best_analysis.blocked and variant_result.best_variant:
                pipeline_status = 'PUBLISHED'
                final_contract = variant_result.best_variant
            elif best_analysis.blocked or blocking_issues:
                pipeline_status = 'BLOCKED'
            else:
                pipeline_status = 'FAILED'
            
            pub_time = (datetime.utcnow() - pub_start).total_seconds()
            
            # Record publication stage
            pub_stage = PipelineStageResult(
                stage_name='publication',
                status=pipeline_status,
                input_count=1,
                output_count=1 if pipeline_status == 'PUBLISHED' else 0,
                blocked_count=1 if pipeline_status == 'BLOCKED' else 0,
                execution_time=pub_time,
                stage_details={
                    'final_status': pipeline_status,
                    'published': pipeline_status == 'PUBLISHED'
                }
            )
            stages_completed.append(pub_stage)
            
        except Exception as e:
            logger.error(f"Error in pipeline processing for {contract_id}: {str(e)}")
            pipeline_status = 'FAILED'
            
            # Add error stage
            error_stage = PipelineStageResult(
                stage_name='error',
                status='FAILED',
                input_count=1,
                output_count=0,
                blocked_count=0,
                execution_time=0.0,
                error_message=str(e)
            )
            stages_completed.append(error_stage)
        
        # Calculate total processing time
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Create result
        result = ContractPipelineResult(
            contract_id=contract_id,
            original_title=original_title,
            pipeline_status=pipeline_status,
            stages_completed=stages_completed,
            final_contract=final_contract,
            variants_generated=variant_result.total_variants if 'variant_result' in locals() else 0,
            variants_passed=variant_result.passed_variants if 'variant_result' in locals() else 0,
            variants_blocked=variant_result.blocked_variants if 'variant_result' in locals() else 0,
            blocking_issues=blocking_issues,
            admin_rescue_reason=admin_rescue_reason,
            processing_time=processing_time,
            timestamp=end_time
        )
        
        # Log individual contract result
        self._log_contract_result(result)
        
        return result
    
    def _evaluate_admin_rescue(self, variant_result: VariantGenerationResult, 
                             best_analysis: CriticAnalysis, 
                             original_contract: Dict) -> bool:
        """Evaluate if contract should be flagged for admin rescue"""
        
        # Check admin rescue triggers
        drama_score = original_contract.get('drama_score', 0)
        
        # High drama but blocked
        if drama_score > 0.8 and best_analysis.blocked:
            return True
        
        # Some variants passed, others blocked (mixed results)
        if variant_result.passed_variants > 0 and variant_result.blocked_variants > 0:
            return True
        
        # Close to passing market balance but blocked
        if (best_analysis.market_balance_score > 0.7 and 
            best_analysis.blocked and 
            len(best_analysis.blocking_issues) == 1):
            return True
        
        # Critical civic event (based on actor or topic)
        actor = original_contract.get('actor', '').lower()
        title = original_contract.get('title', '').lower()
        
        critical_actors = ['city council', 'mayor', 'county commission']
        critical_topics = ['budget', 'tax', 'bond', 'election']
        
        is_critical = (any(ca in actor for ca in critical_actors) or 
                      any(ct in title for ct in critical_topics))
        
        if is_critical and best_analysis.blocked:
            return True
        
        return False
    
    def _generate_admin_rescue_reason(self, variant_result: VariantGenerationResult, 
                                    best_analysis: CriticAnalysis) -> str:
        """Generate reason for admin rescue"""
        
        reasons = []
        
        if variant_result.passed_variants > 0 and variant_result.blocked_variants > 0:
            reasons.append(f"Mixed variant results: {variant_result.passed_variants} passed, {variant_result.blocked_variants} blocked")
        
        if best_analysis.market_balance_score > 0.7 and best_analysis.blocked:
            reasons.append(f"Close to market balance threshold ({best_analysis.market_balance_score:.2f}) but blocked")
        
        if best_analysis.blocking_issues:
            issue_types = [issue['issue_type'] for issue in best_analysis.blocking_issues]
            reasons.append(f"Blocking issues: {', '.join(issue_types)}")
        
        return "; ".join(reasons) if reasons else "Manual review recommended"
    
    def _log_batch_results(self, batch_result: BatchPipelineResult):
        """Log batch processing results for admin dashboard"""
        
        log_entry = {
            'type': 'batch_pipeline_result',
            'batch_id': batch_result.batch_id,
            'timestamp': batch_result.timestamp.isoformat(),
            'total_contracts': batch_result.total_contracts,
            'published_contracts': batch_result.published_contracts,
            'blocked_contracts': batch_result.blocked_contracts,
            'admin_rescue_contracts': batch_result.admin_rescue_contracts,
            'failed_contracts': batch_result.failed_contracts,
            'pipeline_reliability': batch_result.pipeline_reliability,
            'enforcement_rate': batch_result.enforcement_rate,
            'processing_time': batch_result.processing_time,
            'meets_reliability_target': batch_result.pipeline_reliability >= self.target_reliability
        }
        
        logger.info(f"Batch Pipeline Result: {json.dumps(log_entry, indent=2)}")
        
        # Save to file for admin dashboard
        log_file = f"logs/batch_pipeline_{batch_result.batch_id}.json"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        with open(log_file, 'w') as f:
            json.dump(asdict(batch_result), f, indent=2, default=str)
    
    def _log_contract_result(self, contract_result: ContractPipelineResult):
        """Log individual contract processing result"""
        
        log_entry = {
            'type': 'contract_pipeline_result',
            'contract_id': contract_result.contract_id,
            'original_title': contract_result.original_title,
            'pipeline_status': contract_result.pipeline_status,
            'variants_generated': contract_result.variants_generated,
            'variants_passed': contract_result.variants_passed,
            'variants_blocked': contract_result.variants_blocked,
            'blocking_issues': contract_result.blocking_issues,
            'processing_time': contract_result.processing_time,
            'timestamp': contract_result.timestamp.isoformat()
        }
        
        logger.debug(f"Contract Pipeline Result: {json.dumps(log_entry, indent=2)}")

# CLI function for testing
def test_pipeline_with_memphis_headlines(headlines_file: str = None, count: int = 100) -> BatchPipelineResult:
    """
    Test the full pipeline with real Memphis headlines
    
    Args:
        headlines_file: Path to file with Memphis headlines (JSON format)
        count: Number of headlines to process
        
    Returns:
        BatchPipelineResult with complete test results
    """
    
    # Initialize pipeline
    pipeline = FullChainPipelineEnforcer()
    
    # Load test headlines
    if headlines_file and os.path.exists(headlines_file):
        with open(headlines_file, 'r') as f:
            headlines_data = json.load(f)
        
        # Convert headlines to contracts
        test_contracts = []
        for i, headline_data in enumerate(headlines_data[:count]):
            contract = {
                'id': f'test_{i+1}',
                'title': headline_data.get('headline', f'Test Contract {i+1}'),
                'description': headline_data.get('description', 'Test contract description'),
                'actor': headline_data.get('actor', 'Memphis City Council'),
                'timeline': headline_data.get('timeline', '2025-03-31'),
                'drama_score': headline_data.get('drama_score', 0.5),
                'source_url': headline_data.get('url', 'https://example.com')
            }
            test_contracts.append(contract)
    else:
        # Generate sample Memphis contracts for testing
        test_contracts = []
        sample_titles = [
            "Will Memphis City Council approve the $50M infrastructure bond by March 31st?",
            "Will the new downtown development project receive unanimous approval?",
            "Will Mayor Strickland's budget proposal pass without major amendments?",
            "Will the Shelby County Commission approve the tax increase by year-end?",
            "Will the Memphis Light Gas & Water rate hike be delayed beyond 2025?",
            "Will the FedExForum renovation project stay within budget?",
            "Will the Memphis Police Department budget increase be approved?",
            "Will the new affordable housing initiative receive full funding?",
            "Will the Beale Street renovation be completed on schedule?",
            "Will the Memphis Airport expansion project face organized opposition?"
        ]
        
        for i in range(min(count, len(sample_titles))):
            contract = {
                'id': f'test_{i+1}',
                'title': sample_titles[i],
                'description': f'Test contract for Memphis civic prediction market: {sample_titles[i]}',
                'actor': 'Memphis City Council',
                'timeline': '2025-03-31',
                'drama_score': 0.6 + (i * 0.05),  # Varying drama scores
                'source_url': f'https://example.com/story_{i+1}'
            }
            test_contracts.append(contract)
    
    # Process batch
    batch_id = f"test_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    result = pipeline.process_batch_contracts(test_contracts, batch_id)
    
    print(f"\n=== PIPELINE TEST RESULTS ===")
    print(f"Batch ID: {result.batch_id}")
    print(f"Total Contracts: {result.total_contracts}")
    print(f"Published: {result.published_contracts}")
    print(f"Blocked: {result.blocked_contracts}")
    print(f"Admin Rescue: {result.admin_rescue_contracts}")
    print(f"Failed: {result.failed_contracts}")
    print(f"Pipeline Reliability: {result.pipeline_reliability:.1%}")
    print(f"Enforcement Rate: {result.enforcement_rate:.1%}")
    print(f"Processing Time: {result.processing_time:.1f}s")
    
    target_met = result.pipeline_reliability >= 0.8
    print(f"Target >80% Reliability: {'✅ MET' if target_met else '❌ NOT MET'}")
    
    return result

if __name__ == "__main__":
    # Run test with sample Memphis contracts
    test_result = test_pipeline_with_memphis_headlines(count=20)
