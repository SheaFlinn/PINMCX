#!/usr/bin/env python3
"""
System Hardening Sprint - Institutional Readiness Completion

Final hardening script to achieve Dow Jones-level institutional readiness.
Integrates all new components and validates complete system compliance.

Components Integrated:
- Institutional Audit Logger
- Institutional Backup System  
- Gamification System
- Enhanced Pipeline Integration
- Compliance Validation

Version: July_27_2025v1_SystemHardening
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import all institutional components
try:
    from app.institutional_audit_logger import institutional_audit_logger, log_contract_processing
    from app.institutional_backup_system import institutional_backup_system, create_backup, get_backup_status
    from app.gamification import institutional_gamification_system, award_xp, get_user_metrics
    from app.full_chain_pipeline_enforcer import FullChainPipelineEnforcer
    from app.enhanced_contract_critic_enforcer import EnhancedContractCriticEnforcer
    from app.multi_variant_reframing_engine import MultiVariantReframingEngine
    from institutional_readiness_audit import InstitutionalReadinessAuditor
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemHardeningManager:
    """Manages complete system hardening for institutional readiness"""
    
    def __init__(self):
        self.hardening_id = f"hardening_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.timestamp = datetime.utcnow().isoformat()
        
        # Initialize all components
        try:
            self.audit_logger = institutional_audit_logger
            self.backup_system = institutional_backup_system
            self.gamification = institutional_gamification_system
            self.pipeline_enforcer = FullChainPipelineEnforcer()
            self.critic_enforcer = EnhancedContractCriticEnforcer()
            self.variant_engine = MultiVariantReframingEngine()
            self.auditor = InstitutionalReadinessAuditor()
        except Exception as e:
            logger.error(f"Failed to initialize components: {str(e)}")
            raise
        
    def execute_system_hardening(self) -> Dict[str, Any]:
        """Execute complete system hardening sprint"""
        
        print("\n" + "="*100)
        print("🔧 SYSTEM HARDENING SPRINT - INSTITUTIONAL READINESS COMPLETION")
        print("Memphis Civic Prediction Market - Dow Jones-Level Standards")
        print("="*100)
        
        hardening_results = {
            'hardening_id': self.hardening_id,
            'timestamp': self.timestamp,
            'phases_completed': [],
            'overall_success': False,
            'institutional_readiness': False
        }
        
        try:
            # Phase 1: Initialize Institutional Infrastructure
            print("\n🏗️  Phase 1: Initialize Institutional Infrastructure")
            phase1_result = self._initialize_institutional_infrastructure()
            hardening_results['phases_completed'].append(phase1_result)
            
            # Phase 2: Integrate Audit Logging
            print("\n📝 Phase 2: Integrate Institutional Audit Logging")
            phase2_result = self._integrate_audit_logging()
            hardening_results['phases_completed'].append(phase2_result)
            
            # Phase 3: Deploy Backup System
            print("\n💾 Phase 3: Deploy Institutional Backup System")
            phase3_result = self._deploy_backup_system()
            hardening_results['phases_completed'].append(phase3_result)
            
            # Phase 4: Activate Gamification
            print("\n🎮 Phase 4: Activate Gamification System")
            phase4_result = self._activate_gamification()
            hardening_results['phases_completed'].append(phase4_result)
            
            # Phase 5: Validate Pipeline Integration
            print("\n🔗 Phase 5: Validate Pipeline Integration")
            phase5_result = self._validate_pipeline_integration()
            hardening_results['phases_completed'].append(phase5_result)
            
            # Phase 6: Final Institutional Audit
            print("\n🏛️  Phase 6: Final Institutional Readiness Audit")
            phase6_result = self._final_institutional_audit()
            hardening_results['phases_completed'].append(phase6_result)
            
            # Calculate overall success
            successful_phases = sum(1 for phase in hardening_results['phases_completed'] if phase['success'])
            total_phases = len(hardening_results['phases_completed'])
            
            hardening_results['overall_success'] = successful_phases == total_phases
            hardening_results['success_rate'] = successful_phases / total_phases
            
            # Determine institutional readiness
            hardening_results['institutional_readiness'] = (
                hardening_results['overall_success'] and 
                phase6_result.get('institutional_grade') == 'GREEN'
            )
            
            # Display final results
            self._display_hardening_results(hardening_results)
            
            return hardening_results
            
        except Exception as e:
            logger.error(f"Critical error in system hardening: {str(e)}")
            hardening_results['error'] = str(e)
            hardening_results['overall_success'] = False
            return hardening_results
    
    def _initialize_institutional_infrastructure(self) -> Dict[str, Any]:
        """Phase 1: Initialize institutional infrastructure"""
        
        print("  🔍 Initializing institutional infrastructure...")
        
        phase_result = {
            'phase': 'institutional_infrastructure',
            'success': False,
            'components_initialized': [],
            'issues': []
        }
        
        try:
            # Create necessary directories
            directories = ['logs', 'backups', 'audit_trail', 'compliance_reports']
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                phase_result['components_initialized'].append(f"directory_{directory}")
            
            # Initialize database tables
            try:
                # Test audit logger
                self.audit_logger.log_system_error(
                    component='system_hardening',
                    error_type='initialization_test',
                    error_details={'test': 'infrastructure_initialization'}
                )
                phase_result['components_initialized'].append('audit_logger')
            except Exception as e:
                phase_result['issues'].append(f"Audit logger initialization failed: {str(e)}")
            
            # Test backup system
            try:
                backup_status = self.backup_system.get_backup_status()
                phase_result['components_initialized'].append('backup_system')
            except Exception as e:
                phase_result['issues'].append(f"Backup system initialization failed: {str(e)}")
            
            # Test gamification system
            try:
                system_stats = self.gamification.get_system_stats()
                phase_result['components_initialized'].append('gamification_system')
            except Exception as e:
                phase_result['issues'].append(f"Gamification system initialization failed: {str(e)}")
            
            phase_result['success'] = len(phase_result['issues']) == 0
            
            if phase_result['success']:
                print(f"    ✅ Infrastructure initialized: {len(phase_result['components_initialized'])} components")
            else:
                print(f"    ❌ Infrastructure issues: {len(phase_result['issues'])} problems")
            
        except Exception as e:
            phase_result['issues'].append(f"Infrastructure initialization failed: {str(e)}")
            phase_result['success'] = False
        
        return phase_result
    
    def _integrate_audit_logging(self) -> Dict[str, Any]:
        """Phase 2: Integrate institutional audit logging"""
        
        print("  🔍 Integrating institutional audit logging...")
        
        phase_result = {
            'phase': 'audit_logging',
            'success': False,
            'audit_events_logged': 0,
            'compliance_metrics_logged': 0,
            'issues': []
        }
        
        try:
            # Test audit event logging
            test_events = [
                ('contract_processing', 'test_contract_1', 'reframing', 'SUCCESS'),
                ('contract_processing', 'test_contract_2', 'critic_analysis', 'BLOCKED'),
                ('admin_override', 'test_contract_3', 'approve_publish', 'SUCCESS')
            ]
            
            for event_type, contract_id, action, outcome in test_events:
                try:
                    if event_type == 'contract_processing':
                        log_contract_processing(
                            contract_id=contract_id,
                            component='system_hardening_test',
                            action=action,
                            outcome=outcome,
                            details={'test': 'audit_integration'}
                        )
                    elif event_type == 'admin_override':
                        self.audit_logger.log_admin_override(
                            admin_user_id='system_test',
                            contract_id=contract_id,
                            action_type=action,
                            reason='System hardening test',
                            outcome=outcome
                        )
                    
                    phase_result['audit_events_logged'] += 1
                    
                except Exception as e:
                    phase_result['issues'].append(f"Failed to log {event_type}: {str(e)}")
            
            # Test compliance metrics logging
            test_metrics = [
                ('pipeline_reliability', 0.95, 'pipeline_enforcer'),
                ('enforcement_rate', 0.80, 'critic_enforcer'),
                ('backup_success_rate', 1.0, 'backup_system')
            ]
            
            for metric_type, value, component in test_metrics:
                try:
                    self.audit_logger.log_compliance_metric(
                        metric_type=metric_type,
                        metric_value=value,
                        component=component
                    )
                    phase_result['compliance_metrics_logged'] += 1
                    
                except Exception as e:
                    phase_result['issues'].append(f"Failed to log metric {metric_type}: {str(e)}")
            
            phase_result['success'] = len(phase_result['issues']) == 0
            
            if phase_result['success']:
                print(f"    ✅ Audit logging integrated: {phase_result['audit_events_logged']} events, {phase_result['compliance_metrics_logged']} metrics")
            else:
                print(f"    ❌ Audit logging issues: {len(phase_result['issues'])} problems")
            
        except Exception as e:
            phase_result['issues'].append(f"Audit logging integration failed: {str(e)}")
            phase_result['success'] = False
        
        return phase_result
    
    def _deploy_backup_system(self) -> Dict[str, Any]:
        """Phase 3: Deploy institutional backup system"""
        
        print("  🔍 Deploying institutional backup system...")
        
        phase_result = {
            'phase': 'backup_system',
            'success': False,
            'backups_created': 0,
            'backup_jobs_active': 0,
            'issues': []
        }
        
        try:
            # Test backup creation
            backup_jobs = ['db_daily_backup', 'logs_daily_backup']
            
            for job_id in backup_jobs:
                try:
                    backup_result = create_backup(job_id)
                    
                    if backup_result.status == 'SUCCESS':
                        phase_result['backups_created'] += 1
                    else:
                        phase_result['issues'].append(f"Backup {job_id} failed: {backup_result.error_message}")
                        
                except Exception as e:
                    phase_result['issues'].append(f"Backup job {job_id} failed: {str(e)}")
            
            # Get backup system status
            try:
                backup_status = get_backup_status()
                phase_result['backup_jobs_active'] = backup_status.get('active_jobs', 0)
                
                # Check compliance
                compliance_status = backup_status.get('compliance_status', {})
                non_compliant = [k for k, v in compliance_status.items() if v != 'COMPLIANT']
                
                if non_compliant:
                    phase_result['issues'].extend([f"Non-compliant: {item}" for item in non_compliant])
                    
            except Exception as e:
                phase_result['issues'].append(f"Backup status check failed: {str(e)}")
            
            phase_result['success'] = len(phase_result['issues']) == 0 and phase_result['backups_created'] > 0
            
            if phase_result['success']:
                print(f"    ✅ Backup system deployed: {phase_result['backups_created']} backups created, {phase_result['backup_jobs_active']} jobs active")
            else:
                print(f"    ❌ Backup system issues: {len(phase_result['issues'])} problems")
            
        except Exception as e:
            phase_result['issues'].append(f"Backup system deployment failed: {str(e)}")
            phase_result['success'] = False
        
        return phase_result
    
    def _activate_gamification(self) -> Dict[str, Any]:
        """Phase 4: Activate gamification system"""
        
        print("  🔍 Activating gamification system...")
        
        phase_result = {
            'phase': 'gamification',
            'success': False,
            'test_users_created': 0,
            'xp_awarded': 0,
            'achievements_available': 0,
            'issues': []
        }
        
        try:
            # Test user creation and XP awarding
            test_users = ['test_user_1', 'test_user_2', 'test_user_3']
            
            for user_id in test_users:
                try:
                    # Award test XP
                    xp_awarded = award_xp(user_id, 'prediction_made')
                    phase_result['xp_awarded'] += xp_awarded
                    
                    # Get user metrics to verify
                    metrics = get_user_metrics(user_id)
                    if metrics.total_xp > 0:
                        phase_result['test_users_created'] += 1
                    
                except Exception as e:
                    phase_result['issues'].append(f"Gamification test for {user_id} failed: {str(e)}")
            
            # Get system stats
            try:
                system_stats = self.gamification.get_system_stats()
                phase_result['achievements_available'] = system_stats.get('available_achievements', 0)
                
            except Exception as e:
                phase_result['issues'].append(f"Gamification stats failed: {str(e)}")
            
            phase_result['success'] = (
                len(phase_result['issues']) == 0 and 
                phase_result['test_users_created'] > 0 and
                phase_result['achievements_available'] > 0
            )
            
            if phase_result['success']:
                print(f"    ✅ Gamification activated: {phase_result['test_users_created']} users, {phase_result['xp_awarded']} XP, {phase_result['achievements_available']} achievements")
            else:
                print(f"    ❌ Gamification issues: {len(phase_result['issues'])} problems")
            
        except Exception as e:
            phase_result['issues'].append(f"Gamification activation failed: {str(e)}")
            phase_result['success'] = False
        
        return phase_result
    
    def _validate_pipeline_integration(self) -> Dict[str, Any]:
        """Phase 5: Validate pipeline integration"""
        
        print("  🔍 Validating pipeline integration...")
        
        phase_result = {
            'phase': 'pipeline_integration',
            'success': False,
            'contracts_processed': 0,
            'pipeline_reliability': 0.0,
            'enforcement_rate': 0.0,
            'issues': []
        }
        
        try:
            # Test pipeline with sample contracts
            test_contracts = [
                {
                    'id': 'integration_test_1',
                    'title': 'Will Memphis City Council approve the test measure by March 31st?',
                    'description': 'Test contract for pipeline integration validation.',
                    'actor': 'Memphis City Council',
                    'timeline': '2025-03-31'
                },
                {
                    'id': 'integration_test_2',
                    'title': 'Will the obviously biased test proposal definitely pass?',
                    'description': 'This test proposal is clearly biased and should be blocked.',
                    'actor': 'Memphis City Council',
                    'timeline': '2025-03-31'
                }
            ]
            
            try:
                batch_result = self.pipeline_enforcer.process_batch_contracts(test_contracts)
                
                phase_result['contracts_processed'] = batch_result.total_contracts
                phase_result['pipeline_reliability'] = batch_result.pipeline_reliability
                phase_result['enforcement_rate'] = batch_result.enforcement_rate
                
                # Validate institutional standards
                if batch_result.pipeline_reliability < 0.95:
                    phase_result['issues'].append(f"Pipeline reliability {batch_result.pipeline_reliability:.1%} below institutional standard (95%)")
                
                if batch_result.enforcement_rate < 0.50:  # At least some enforcement expected
                    phase_result['issues'].append(f"Enforcement rate {batch_result.enforcement_rate:.1%} unexpectedly low")
                
            except Exception as e:
                phase_result['issues'].append(f"Pipeline processing failed: {str(e)}")
            
            phase_result['success'] = len(phase_result['issues']) == 0 and phase_result['contracts_processed'] > 0
            
            if phase_result['success']:
                print(f"    ✅ Pipeline integration validated: {phase_result['contracts_processed']} contracts, {phase_result['pipeline_reliability']:.1%} reliability")
            else:
                print(f"    ❌ Pipeline integration issues: {len(phase_result['issues'])} problems")
            
        except Exception as e:
            phase_result['issues'].append(f"Pipeline integration validation failed: {str(e)}")
            phase_result['success'] = False
        
        return phase_result
    
    def _final_institutional_audit(self) -> Dict[str, Any]:
        """Phase 6: Final institutional readiness audit"""
        
        print("  🔍 Running final institutional readiness audit...")
        
        phase_result = {
            'phase': 'final_audit',
            'success': False,
            'institutional_grade': 'RED',
            'overall_score': 0.0,
            'issues': []
        }
        
        try:
            # Run comprehensive audit
            audit_report = self.auditor.run_institutional_audit()
            
            phase_result['institutional_grade'] = audit_report.overall_status
            phase_result['overall_score'] = audit_report.overall_score
            
            # Check if institutional readiness achieved
            if audit_report.overall_status == 'GREEN' and audit_report.overall_score >= 0.95:
                phase_result['success'] = True
            else:
                # Collect issues from audit
                for category, results in audit_report.category_results.items():
                    for result in results:
                        if result.status in ['YELLOW', 'RED']:
                            phase_result['issues'].extend(result.issues)
            
            if phase_result['success']:
                print(f"    ✅ Institutional audit passed: {phase_result['institutional_grade']} grade, {phase_result['overall_score']:.1%} score")
            else:
                print(f"    ❌ Institutional audit issues: {phase_result['institutional_grade']} grade, {len(phase_result['issues'])} problems")
            
        except Exception as e:
            phase_result['issues'].append(f"Final audit failed: {str(e)}")
            phase_result['success'] = False
        
        return phase_result
    
    def _display_hardening_results(self, results: Dict[str, Any]):
        """Display comprehensive hardening results"""
        
        print("\n" + "="*100)
        print("📊 SYSTEM HARDENING SPRINT RESULTS")
        print("="*100)
        
        # Overall status
        if results['institutional_readiness']:
            print("🎉 INSTITUTIONAL READINESS: ✅ ACHIEVED")
            print("🏆 Dow Jones-Level Standards: OPERATIONAL")
        elif results['overall_success']:
            print("✅ SYSTEM HARDENING: COMPLETED")
            print("⚠️  Institutional Readiness: NEEDS MINOR ADJUSTMENTS")
        else:
            print("❌ SYSTEM HARDENING: INCOMPLETE")
            print("🔧 Requires Additional Work")
        
        # Phase results
        print(f"\n📋 Phase Results:")
        for phase in results['phases_completed']:
            status = "✅ SUCCESS" if phase['success'] else "❌ FAILURE"
            print(f"   {phase['phase'].replace('_', ' ').title()}: {status}")
            
            if not phase['success'] and 'issues' in phase:
                for issue in phase['issues'][:3]:  # Show first 3 issues
                    print(f"      - {issue}")
        
        # Success metrics
        print(f"\n📈 Success Metrics:")
        print(f"   Phases Completed: {sum(1 for p in results['phases_completed'] if p['success'])}/{len(results['phases_completed'])}")
        print(f"   Success Rate: {results.get('success_rate', 0):.1%}")
        
        if 'phases_completed' in results and len(results['phases_completed']) > 0:
            final_audit = next((p for p in results['phases_completed'] if p['phase'] == 'final_audit'), None)
            if final_audit:
                print(f"   Institutional Grade: {final_audit.get('institutional_grade', 'UNKNOWN')}")
                print(f"   Overall Score: {final_audit.get('overall_score', 0):.1%}")
        
        print("="*100)

def main():
    """Execute system hardening sprint"""
    
    # Create hardening manager
    hardening_manager = SystemHardeningManager()
    
    # Execute hardening sprint
    results = hardening_manager.execute_system_hardening()
    
    # Save results
    results_file = f"system_hardening_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 System hardening results saved to: {results_file}")
    
    # Return exit code based on institutional readiness
    return 0 if results.get('institutional_readiness', False) else 1

if __name__ == "__main__":
    exit_code = main()
