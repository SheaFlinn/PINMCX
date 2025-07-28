#!/usr/bin/env python3
"""
Full-Chain Admin Dashboard - World-Class Market Viability Monitoring

Complete admin interface for monitoring and managing the full-chain pipeline:
- Real-time pipeline performance metrics
- Failed/flagged contract queue with full audit trail
- Admin rescue workflow with reason logging
- Blocking issue analysis and override management
- Multi-variant analysis and approval workflow

Version: July_25_2025v2_WorldClass - Complete Admin Integration
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
import glob

from ..full_chain_pipeline_enforcer import FullChainPipelineEnforcer, BatchPipelineResult, ContractPipelineResult
from ..enhanced_contract_critic_enforcer import EnhancedContractCriticEnforcer, log_critic_analysis
from ..multi_variant_reframing_engine import MultiVariantReframingEngine

logger = logging.getLogger(__name__)

# Create Flask blueprint
full_chain_admin_bp = Blueprint('full_chain_admin', __name__, url_prefix='/admin/full-chain')

class FullChainAdminDashboard:
    """Admin dashboard for full-chain pipeline monitoring and management"""
    
    def __init__(self):
        self.pipeline_enforcer = FullChainPipelineEnforcer()
        self.critic_enforcer = EnhancedContractCriticEnforcer()
        self.variant_engine = MultiVariantReframingEngine()
    
    def get_dashboard_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics for the specified period"""
        
        # Load recent batch results
        batch_results = self._load_recent_batch_results(days)
        
        # Calculate aggregate metrics
        total_contracts = sum(batch.total_contracts for batch in batch_results)
        published_contracts = sum(batch.published_contracts for batch in batch_results)
        blocked_contracts = sum(batch.blocked_contracts for batch in batch_results)
        admin_rescue_contracts = sum(batch.admin_rescue_contracts for batch in batch_results)
        failed_contracts = sum(batch.failed_contracts for batch in batch_results)
        
        # Calculate rates
        pipeline_reliability = (published_contracts + blocked_contracts + admin_rescue_contracts) / total_contracts if total_contracts > 0 else 0
        enforcement_rate = blocked_contracts / total_contracts if total_contracts > 0 else 0
        rescue_rate = admin_rescue_contracts / total_contracts if total_contracts > 0 else 0
        
        # Get recent contract results for detailed analysis
        contract_results = []
        for batch in batch_results:
            contract_results.extend(batch.contract_results)
        
        # Analyze blocking issues
        blocking_issue_analysis = self._analyze_blocking_issues(contract_results)
        
        # Get admin rescue queue
        rescue_queue = self._get_admin_rescue_queue(contract_results)
        
        # Performance trends
        daily_metrics = self._calculate_daily_metrics(batch_results)
        
        return {
            'period_days': days,
            'total_contracts': total_contracts,
            'published_contracts': published_contracts,
            'blocked_contracts': blocked_contracts,
            'admin_rescue_contracts': admin_rescue_contracts,
            'failed_contracts': failed_contracts,
            'pipeline_reliability': pipeline_reliability,
            'enforcement_rate': enforcement_rate,
            'rescue_rate': rescue_rate,
            'reliability_target_met': pipeline_reliability >= 0.8,
            'blocking_issue_analysis': blocking_issue_analysis,
            'admin_rescue_queue': rescue_queue,
            'daily_metrics': daily_metrics,
            'recent_batches': [self._batch_summary(batch) for batch in batch_results[-10:]]
        }
    
    def get_contract_details(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific contract"""
        
        # Search through recent batch results
        batch_results = self._load_recent_batch_results(30)  # Search last 30 days
        
        for batch in batch_results:
            for contract_result in batch.contract_results:
                if contract_result.contract_id == contract_id:
                    return {
                        'contract_result': contract_result,
                        'batch_info': {
                            'batch_id': batch.batch_id,
                            'timestamp': batch.timestamp,
                            'pipeline_reliability': batch.pipeline_reliability
                        },
                        'stage_details': self._get_stage_details(contract_result),
                        'variant_analysis': self._get_variant_analysis(contract_result),
                        'blocking_analysis': self._get_blocking_analysis(contract_result),
                        'admin_actions': self._get_admin_actions(contract_id)
                    }
        
        return None
    
    def process_admin_override(self, contract_id: str, admin_user: str, 
                             override_reason: str, action: str) -> Dict[str, Any]:
        """Process admin override for blocked or rescued contract"""
        
        try:
            # Get contract details
            contract_details = self.get_contract_details(contract_id)
            if not contract_details:
                return {'success': False, 'error': 'Contract not found'}
            
            contract_result = contract_details['contract_result']
            
            # Validate override reason
            if not override_reason or len(override_reason.strip()) < 10:
                return {'success': False, 'error': 'Override reason must be at least 10 characters'}
            
            # Log admin override
            override_log = {
                'timestamp': datetime.utcnow().isoformat(),
                'contract_id': contract_id,
                'admin_user': admin_user,
                'original_status': contract_result.pipeline_status,
                'override_action': action,
                'override_reason': override_reason.strip(),
                'blocking_issues': contract_result.blocking_issues,
                'variants_analyzed': contract_result.variants_generated,
                'variants_passed': contract_result.variants_passed
            }
            
            # Save override log
            self._save_admin_override_log(override_log)
            
            # Update contract status based on action
            if action == 'approve_publish':
                # Mark contract for publication despite blocking issues
                result_message = f"Contract approved for publication by {admin_user}"
                
            elif action == 'request_rewrite':
                # Request contract rewrite with specific guidance
                result_message = f"Contract flagged for rewrite by {admin_user}"
                
            elif action == 'reject_permanently':
                # Permanently reject contract
                result_message = f"Contract permanently rejected by {admin_user}"
                
            else:
                return {'success': False, 'error': 'Invalid override action'}
            
            logger.info(f"Admin override processed: {contract_id} by {admin_user} - {action}")
            
            return {
                'success': True,
                'message': result_message,
                'override_id': f"override_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'contract_id': contract_id
            }
            
        except Exception as e:
            logger.error(f"Error processing admin override: {str(e)}")
            return {'success': False, 'error': f'Processing error: {str(e)}'}
    
    def _load_recent_batch_results(self, days: int) -> List[BatchPipelineResult]:
        """Load recent batch results from log files"""
        
        batch_results = []
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Search for batch log files
        log_pattern = "logs/batch_pipeline_*.json"
        log_files = glob.glob(log_pattern)
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    batch_data = json.load(f)
                
                # Parse timestamp
                timestamp = datetime.fromisoformat(batch_data['timestamp'].replace('Z', '+00:00'))
                
                # Filter by date
                if timestamp >= cutoff_date:
                    # Convert to BatchPipelineResult object
                    batch_result = self._dict_to_batch_result(batch_data)
                    batch_results.append(batch_result)
                    
            except Exception as e:
                logger.warning(f"Error loading batch file {log_file}: {str(e)}")
                continue
        
        # Sort by timestamp (newest first)
        batch_results.sort(key=lambda x: x.timestamp, reverse=True)
        
        return batch_results
    
    def _analyze_blocking_issues(self, contract_results: List[ContractPipelineResult]) -> Dict[str, Any]:
        """Analyze blocking issues across all contracts"""
        
        issue_counts = {}
        total_blocked = 0
        
        for contract_result in contract_results:
            if contract_result.pipeline_status == 'BLOCKED' and contract_result.blocking_issues:
                total_blocked += 1
                for issue in contract_result.blocking_issues:
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Sort by frequency
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_blocked_contracts': total_blocked,
            'issue_frequency': sorted_issues,
            'most_common_issue': sorted_issues[0][0] if sorted_issues else None,
            'issue_distribution': {issue: count/total_blocked for issue, count in sorted_issues} if total_blocked > 0 else {}
        }
    
    def _get_admin_rescue_queue(self, contract_results: List[ContractPipelineResult]) -> List[Dict[str, Any]]:
        """Get contracts requiring admin rescue"""
        
        rescue_queue = []
        
        for contract_result in contract_results:
            if contract_result.pipeline_status == 'ADMIN_RESCUE':
                rescue_item = {
                    'contract_id': contract_result.contract_id,
                    'original_title': contract_result.original_title,
                    'rescue_reason': contract_result.admin_rescue_reason,
                    'variants_generated': contract_result.variants_generated,
                    'variants_passed': contract_result.variants_passed,
                    'variants_blocked': contract_result.variants_blocked,
                    'blocking_issues': contract_result.blocking_issues,
                    'timestamp': contract_result.timestamp,
                    'priority': self._calculate_rescue_priority(contract_result)
                }
                rescue_queue.append(rescue_item)
        
        # Sort by priority (highest first)
        rescue_queue.sort(key=lambda x: x['priority'], reverse=True)
        
        return rescue_queue
    
    def _calculate_rescue_priority(self, contract_result: ContractPipelineResult) -> float:
        """Calculate priority score for admin rescue (0.0 to 1.0)"""
        
        priority = 0.0
        
        # Higher priority for contracts with some passing variants
        if contract_result.variants_passed > 0:
            priority += 0.4
        
        # Higher priority for fewer blocking issues
        if contract_result.blocking_issues:
            priority += max(0, 0.3 - (len(contract_result.blocking_issues) * 0.1))
        
        # Higher priority for recent contracts
        hours_old = (datetime.utcnow() - contract_result.timestamp).total_seconds() / 3600
        if hours_old < 24:
            priority += 0.3 * (1 - hours_old / 24)
        
        return min(1.0, priority)
    
    def _calculate_daily_metrics(self, batch_results: List[BatchPipelineResult]) -> List[Dict[str, Any]]:
        """Calculate daily performance metrics"""
        
        daily_data = {}
        
        for batch in batch_results:
            date_key = batch.timestamp.date().isoformat()
            
            if date_key not in daily_data:
                daily_data[date_key] = {
                    'date': date_key,
                    'total_contracts': 0,
                    'published_contracts': 0,
                    'blocked_contracts': 0,
                    'admin_rescue_contracts': 0,
                    'batches_processed': 0
                }
            
            daily_data[date_key]['total_contracts'] += batch.total_contracts
            daily_data[date_key]['published_contracts'] += batch.published_contracts
            daily_data[date_key]['blocked_contracts'] += batch.blocked_contracts
            daily_data[date_key]['admin_rescue_contracts'] += batch.admin_rescue_contracts
            daily_data[date_key]['batches_processed'] += 1
        
        # Calculate rates for each day
        for day_data in daily_data.values():
            total = day_data['total_contracts']
            if total > 0:
                day_data['pipeline_reliability'] = (day_data['published_contracts'] + day_data['blocked_contracts'] + day_data['admin_rescue_contracts']) / total
                day_data['enforcement_rate'] = day_data['blocked_contracts'] / total
                day_data['rescue_rate'] = day_data['admin_rescue_contracts'] / total
            else:
                day_data['pipeline_reliability'] = 0
                day_data['enforcement_rate'] = 0
                day_data['rescue_rate'] = 0
        
        # Sort by date
        return sorted(daily_data.values(), key=lambda x: x['date'])
    
    def _save_admin_override_log(self, override_log: Dict[str, Any]):
        """Save admin override log for audit trail"""
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs/admin_overrides', exist_ok=True)
        
        # Save individual override log
        filename = f"logs/admin_overrides/override_{override_log['timestamp'].replace(':', '-')}.json"
        with open(filename, 'w') as f:
            json.dump(override_log, f, indent=2)
        
        # Append to master override log
        master_log = 'logs/admin_overrides/master_override_log.jsonl'
        with open(master_log, 'a') as f:
            f.write(json.dumps(override_log) + '\n')
        
        logger.info(f"Admin override logged: {override_log['contract_id']} by {override_log['admin_user']}")
    
    def _dict_to_batch_result(self, batch_data: Dict) -> BatchPipelineResult:
        """Convert dictionary to BatchPipelineResult object"""
        
        # Convert contract results
        contract_results = []
        for contract_data in batch_data.get('contract_results', []):
            contract_result = ContractPipelineResult(
                contract_id=contract_data['contract_id'],
                original_title=contract_data['original_title'],
                pipeline_status=contract_data['pipeline_status'],
                stages_completed=contract_data.get('stages_completed', []),
                final_contract=contract_data.get('final_contract'),
                variants_generated=contract_data.get('variants_generated', 0),
                variants_passed=contract_data.get('variants_passed', 0),
                variants_blocked=contract_data.get('variants_blocked', 0),
                blocking_issues=contract_data.get('blocking_issues', []),
                admin_rescue_reason=contract_data.get('admin_rescue_reason'),
                processing_time=contract_data.get('processing_time', 0.0),
                timestamp=datetime.fromisoformat(contract_data['timestamp'].replace('Z', '+00:00'))
            )
            contract_results.append(contract_result)
        
        # Create BatchPipelineResult
        return BatchPipelineResult(
            batch_id=batch_data['batch_id'],
            total_contracts=batch_data['total_contracts'],
            published_contracts=batch_data['published_contracts'],
            blocked_contracts=batch_data['blocked_contracts'],
            admin_rescue_contracts=batch_data['admin_rescue_contracts'],
            failed_contracts=batch_data['failed_contracts'],
            pipeline_reliability=batch_data['pipeline_reliability'],
            enforcement_rate=batch_data['enforcement_rate'],
            processing_time=batch_data['processing_time'],
            timestamp=datetime.fromisoformat(batch_data['timestamp'].replace('Z', '+00:00')),
            contract_results=contract_results,
            stage_summary=batch_data.get('stage_summary', {})
        )
    
    def _batch_summary(self, batch: BatchPipelineResult) -> Dict[str, Any]:
        """Create summary of batch result"""
        return {
            'batch_id': batch.batch_id,
            'timestamp': batch.timestamp.isoformat(),
            'total_contracts': batch.total_contracts,
            'published_contracts': batch.published_contracts,
            'blocked_contracts': batch.blocked_contracts,
            'admin_rescue_contracts': batch.admin_rescue_contracts,
            'pipeline_reliability': batch.pipeline_reliability,
            'enforcement_rate': batch.enforcement_rate
        }
    
    def _get_stage_details(self, contract_result: ContractPipelineResult) -> List[Dict[str, Any]]:
        """Get detailed stage information for contract"""
        return [
            {
                'stage_name': stage.stage_name,
                'status': stage.status,
                'input_count': stage.input_count,
                'output_count': stage.output_count,
                'blocked_count': stage.blocked_count,
                'execution_time': stage.execution_time,
                'error_message': stage.error_message,
                'stage_details': stage.stage_details
            }
            for stage in contract_result.stages_completed
        ]
    
    def _get_variant_analysis(self, contract_result: ContractPipelineResult) -> Dict[str, Any]:
        """Get variant analysis for contract"""
        return {
            'variants_generated': contract_result.variants_generated,
            'variants_passed': contract_result.variants_passed,
            'variants_blocked': contract_result.variants_blocked,
            'pass_rate': contract_result.variants_passed / contract_result.variants_generated if contract_result.variants_generated > 0 else 0
        }
    
    def _get_blocking_analysis(self, contract_result: ContractPipelineResult) -> Dict[str, Any]:
        """Get blocking issue analysis for contract"""
        return {
            'blocking_issues': contract_result.blocking_issues,
            'issue_count': len(contract_result.blocking_issues) if contract_result.blocking_issues else 0,
            'is_blocked': contract_result.pipeline_status == 'BLOCKED'
        }
    
    def _get_admin_actions(self, contract_id: str) -> List[Dict[str, Any]]:
        """Get admin actions taken on contract"""
        
        actions = []
        
        # Load admin override logs
        try:
            master_log = 'logs/admin_overrides/master_override_log.jsonl'
            if os.path.exists(master_log):
                with open(master_log, 'r') as f:
                    for line in f:
                        try:
                            override_data = json.loads(line.strip())
                            if override_data.get('contract_id') == contract_id:
                                actions.append(override_data)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.warning(f"Error loading admin actions for {contract_id}: {str(e)}")
        
        return sorted(actions, key=lambda x: x['timestamp'], reverse=True)

# Initialize dashboard instance
dashboard = FullChainAdminDashboard()

# Flask routes
@full_chain_admin_bp.route('/dashboard')
def dashboard_view():
    """Main dashboard view"""
    try:
        days = request.args.get('days', 7, type=int)
        metrics = dashboard.get_dashboard_metrics(days)
        return render_template('admin/full_chain_dashboard.html', metrics=metrics)
    except Exception as e:
        logger.error(f"Error in dashboard view: {str(e)}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('admin/error.html')

@full_chain_admin_bp.route('/contract/<contract_id>')
def contract_details(contract_id: str):
    """Contract details view"""
    try:
        details = dashboard.get_contract_details(contract_id)
        if not details:
            flash(f'Contract {contract_id} not found', 'error')
            return redirect(url_for('full_chain_admin.dashboard_view'))
        
        return render_template('admin/contract_details.html', details=details)
    except Exception as e:
        logger.error(f"Error in contract details view: {str(e)}")
        flash(f'Error loading contract details: {str(e)}', 'error')
        return redirect(url_for('full_chain_admin.dashboard_view'))

@full_chain_admin_bp.route('/rescue-queue')
def rescue_queue():
    """Admin rescue queue view"""
    try:
        metrics = dashboard.get_dashboard_metrics(30)  # Last 30 days
        rescue_queue = metrics['admin_rescue_queue']
        return render_template('admin/rescue_queue.html', rescue_queue=rescue_queue)
    except Exception as e:
        logger.error(f"Error in rescue queue view: {str(e)}")
        flash(f'Error loading rescue queue: {str(e)}', 'error')
        return render_template('admin/error.html')

@full_chain_admin_bp.route('/override', methods=['POST'])
def process_override():
    """Process admin override"""
    try:
        data = request.get_json()
        
        contract_id = data.get('contract_id')
        admin_user = session.get('user_email', 'unknown')
        override_reason = data.get('override_reason', '')
        action = data.get('action')
        
        if not all([contract_id, override_reason, action]):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        result = dashboard.process_admin_override(contract_id, admin_user, override_reason, action)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing override: {str(e)}")
        return jsonify({'success': False, 'error': f'Processing error: {str(e)}'})

@full_chain_admin_bp.route('/api/metrics')
def api_metrics():
    """API endpoint for dashboard metrics"""
    try:
        days = request.args.get('days', 7, type=int)
        metrics = dashboard.get_dashboard_metrics(days)
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error in API metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@full_chain_admin_bp.route('/api/test-pipeline', methods=['POST'])
def test_pipeline():
    """API endpoint to test pipeline with sample contracts"""
    try:
        data = request.get_json()
        count = data.get('count', 10)
        
        # Import and run pipeline test
        from ..full_chain_pipeline_enforcer import test_pipeline_with_memphis_headlines
        
        result = test_pipeline_with_memphis_headlines(count=count)
        
        return jsonify({
            'success': True,
            'batch_id': result.batch_id,
            'total_contracts': result.total_contracts,
            'published_contracts': result.published_contracts,
            'blocked_contracts': result.blocked_contracts,
            'admin_rescue_contracts': result.admin_rescue_contracts,
            'pipeline_reliability': result.pipeline_reliability,
            'enforcement_rate': result.enforcement_rate,
            'target_met': result.pipeline_reliability >= 0.8
        })
        
    except Exception as e:
        logger.error(f"Error in pipeline test: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
