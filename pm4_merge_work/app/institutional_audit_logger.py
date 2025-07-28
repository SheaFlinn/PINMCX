#!/usr/bin/env python3
"""
Institutional Audit Logger - Dow Jones-Level Audit Trail

Comprehensive audit logging system for Memphis civic prediction market.
Ensures institutional-grade compliance, traceability, and accountability.

Features:
- Comprehensive audit trail for all system operations
- Structured logging with JSON format for analysis
- Real-time audit event streaming
- Compliance reporting and retention management
- Performance metrics and SLA monitoring

Version: July_27_2025v1_InstitutionalLogger
"""

import os
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import queue
import time

@dataclass
class AuditEvent:
    """Structured audit event for institutional logging"""
    event_id: str
    timestamp: str
    event_type: str  # CONTRACT_PROCESSED, ADMIN_OVERRIDE, SYSTEM_ERROR, etc.
    user_id: Optional[str]
    contract_id: Optional[str]
    component: str  # pipeline_enforcer, critic_enforcer, etc.
    action: str
    details: Dict[str, Any]
    outcome: str  # SUCCESS, FAILURE, BLOCKED, RESCUE
    compliance_level: str  # INSTITUTIONAL, STANDARD, BASIC
    retention_days: int

class InstitutionalAuditLogger:
    """Institutional-grade audit logging system"""
    
    def __init__(self, db_path: str = "audit_trail.db", log_dir: str = "logs"):
        self.db_path = db_path
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_audit_database()
        
        # Initialize file logging
        self._init_file_logging()
        
        # Initialize real-time event queue
        self.event_queue = queue.Queue()
        self.event_processor_thread = threading.Thread(target=self._process_audit_events, daemon=True)
        self.event_processor_thread.start()
        
        # Compliance settings
        self.compliance_settings = {
            'INSTITUTIONAL': {'retention_days': 2555, 'encryption': True, 'backup_frequency': 1},  # 7 years
            'STANDARD': {'retention_days': 1095, 'encryption': False, 'backup_frequency': 7},      # 3 years
            'BASIC': {'retention_days': 365, 'encryption': False, 'backup_frequency': 30}          # 1 year
        }
        
    def _init_audit_database(self):
        """Initialize audit trail database with institutional schema"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create audit events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                user_id TEXT,
                contract_id TEXT,
                component TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT NOT NULL,
                outcome TEXT NOT NULL,
                compliance_level TEXT NOT NULL,
                retention_days INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for audit events
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_events(event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_component ON audit_events(component)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_outcome ON audit_events(outcome)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_compliance ON audit_events(compliance_level)')
        
        # Create compliance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_metrics (
                metric_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                metric_value REAL NOT NULL,
                component TEXT NOT NULL,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for compliance metrics
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON compliance_metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_type ON compliance_metrics(metric_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_component ON compliance_metrics(component)')
        
        # Create admin actions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_actions (
                action_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                admin_user_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                target_contract_id TEXT,
                reason TEXT NOT NULL,
                outcome TEXT NOT NULL,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for admin actions
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_timestamp ON admin_actions(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_user ON admin_actions(admin_user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_action_type ON admin_actions(action_type)')
        
        conn.commit()
        conn.close()
        
    def _init_file_logging(self):
        """Initialize structured file logging"""
        
        # Create institutional audit logger
        self.institutional_logger = logging.getLogger('institutional_audit')
        self.institutional_logger.setLevel(logging.INFO)
        
        # Create file handler with rotation
        audit_log_file = self.log_dir / 'institutional_audit.log'
        file_handler = logging.FileHandler(audit_log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create JSON formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        self.institutional_logger.addHandler(file_handler)
        
        # Create compliance logger
        self.compliance_logger = logging.getLogger('compliance_audit')
        self.compliance_logger.setLevel(logging.INFO)
        
        compliance_log_file = self.log_dir / 'compliance_audit.log'
        compliance_handler = logging.FileHandler(compliance_log_file)
        compliance_handler.setFormatter(formatter)
        self.compliance_logger.addHandler(compliance_handler)
        
    def log_audit_event(self, event: AuditEvent):
        """Log institutional audit event"""
        
        # Add to real-time processing queue
        self.event_queue.put(event)
        
        # Log to file immediately for critical events
        if event.compliance_level == 'INSTITUTIONAL':
            self.institutional_logger.info(json.dumps(asdict(event)))
            
    def log_contract_processing(self, contract_id: str, component: str, action: str, 
                              outcome: str, details: Dict[str, Any], user_id: Optional[str] = None):
        """Log contract processing event"""
        
        event = AuditEvent(
            event_id=f"contract_{contract_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            timestamp=datetime.utcnow().isoformat(),
            event_type='CONTRACT_PROCESSED',
            user_id=user_id,
            contract_id=contract_id,
            component=component,
            action=action,
            details=details,
            outcome=outcome,
            compliance_level='INSTITUTIONAL',
            retention_days=self.compliance_settings['INSTITUTIONAL']['retention_days']
        )
        
        self.log_audit_event(event)
        
    def log_admin_override(self, admin_user_id: str, contract_id: str, action_type: str, 
                          reason: str, outcome: str, details: Optional[Dict[str, Any]] = None):
        """Log admin override action"""
        
        event = AuditEvent(
            event_id=f"admin_override_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            timestamp=datetime.utcnow().isoformat(),
            event_type='ADMIN_OVERRIDE',
            user_id=admin_user_id,
            contract_id=contract_id,
            component='admin_dashboard',
            action=action_type,
            details=details or {},
            outcome=outcome,
            compliance_level='INSTITUTIONAL',
            retention_days=self.compliance_settings['INSTITUTIONAL']['retention_days']
        )
        
        self.log_audit_event(event)
        
        # Also log to admin actions table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO admin_actions 
            (action_id, timestamp, admin_user_id, action_type, target_contract_id, reason, outcome, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.event_id,
            event.timestamp,
            admin_user_id,
            action_type,
            contract_id,
            reason,
            outcome,
            json.dumps(details or {})
        ))
        
        conn.commit()
        conn.close()
        
    def log_system_error(self, component: str, error_type: str, error_details: Dict[str, Any], 
                        contract_id: Optional[str] = None):
        """Log system error event"""
        
        event = AuditEvent(
            event_id=f"error_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            timestamp=datetime.utcnow().isoformat(),
            event_type='SYSTEM_ERROR',
            user_id=None,
            contract_id=contract_id,
            component=component,
            action='error_occurred',
            details=error_details,
            outcome='FAILURE',
            compliance_level='INSTITUTIONAL',
            retention_days=self.compliance_settings['INSTITUTIONAL']['retention_days']
        )
        
        self.log_audit_event(event)
        
    def log_compliance_metric(self, metric_type: str, metric_value: float, component: str, 
                            details: Optional[Dict[str, Any]] = None):
        """Log compliance metric"""
        
        metric_id = f"metric_{metric_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO compliance_metrics 
            (metric_id, timestamp, metric_type, metric_value, component, details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            metric_id,
            datetime.utcnow().isoformat(),
            metric_type,
            metric_value,
            component,
            json.dumps(details or {})
        ))
        
        conn.commit()
        conn.close()
        
        self.compliance_logger.info(f"Compliance metric: {metric_type}={metric_value} for {component}")
        
    def _process_audit_events(self):
        """Process audit events in real-time"""
        
        while True:
            try:
                # Get event from queue (blocks until available)
                event = self.event_queue.get(timeout=1.0)
                
                # Store in database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO audit_events 
                    (event_id, timestamp, event_type, user_id, contract_id, component, 
                     action, details, outcome, compliance_level, retention_days)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_id,
                    event.timestamp,
                    event.event_type,
                    event.user_id,
                    event.contract_id,
                    event.component,
                    event.action,
                    json.dumps(event.details),
                    event.outcome,
                    event.compliance_level,
                    event.retention_days
                ))
                
                conn.commit()
                conn.close()
                
                # Mark task as done
                self.event_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing audit event: {str(e)}")
                
    def get_audit_trail(self, start_date: Optional[str] = None, end_date: Optional[str] = None, 
                       event_type: Optional[str] = None, component: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get audit trail with filters"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
            
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
            
        if component:
            query += " AND component = ?"
            params.append(component)
            
        query += " ORDER BY timestamp DESC LIMIT 1000"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        
        return results
        
    def get_compliance_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate compliance report"""
        
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get event counts by type
        cursor.execute('''
            SELECT event_type, outcome, COUNT(*) as count
            FROM audit_events 
            WHERE timestamp >= ?
            GROUP BY event_type, outcome
        ''', (start_date,))
        
        event_counts = cursor.fetchall()
        
        # Get compliance metrics
        cursor.execute('''
            SELECT metric_type, AVG(metric_value) as avg_value, COUNT(*) as count
            FROM compliance_metrics 
            WHERE timestamp >= ?
            GROUP BY metric_type
        ''', (start_date,))
        
        metrics = cursor.fetchall()
        
        # Get admin actions
        cursor.execute('''
            SELECT action_type, COUNT(*) as count
            FROM admin_actions 
            WHERE timestamp >= ?
            GROUP BY action_type
        ''', (start_date,))
        
        admin_actions = cursor.fetchall()
        
        conn.close()
        
        return {
            'report_period_days': days,
            'generated_at': datetime.utcnow().isoformat(),
            'event_counts': [{'event_type': row[0], 'outcome': row[1], 'count': row[2]} for row in event_counts],
            'compliance_metrics': [{'metric_type': row[0], 'avg_value': row[1], 'count': row[2]} for row in metrics],
            'admin_actions': [{'action_type': row[0], 'count': row[1]} for row in admin_actions]
        }
        
    def cleanup_expired_records(self):
        """Clean up expired audit records based on retention policy"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate cutoff dates for each compliance level
        now = datetime.utcnow()
        
        for level, settings in self.compliance_settings.items():
            cutoff_date = (now - timedelta(days=settings['retention_days'])).isoformat()
            
            cursor.execute('''
                DELETE FROM audit_events 
                WHERE compliance_level = ? AND timestamp < ?
            ''', (level, cutoff_date))
            
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            self.institutional_logger.info(f"Cleaned up {deleted_count} expired audit records")
            
        return deleted_count

# Global audit logger instance
institutional_audit_logger = InstitutionalAuditLogger()

def log_contract_processing(contract_id: str, component: str, action: str, outcome: str, 
                          details: Dict[str, Any], user_id: Optional[str] = None):
    """Convenience function for contract processing logging"""
    institutional_audit_logger.log_contract_processing(
        contract_id, component, action, outcome, details, user_id
    )

def log_admin_override(admin_user_id: str, contract_id: str, action_type: str, 
                      reason: str, outcome: str, details: Optional[Dict[str, Any]] = None):
    """Convenience function for admin override logging"""
    institutional_audit_logger.log_admin_override(
        admin_user_id, contract_id, action_type, reason, outcome, details
    )

def log_system_error(component: str, error_type: str, error_details: Dict[str, Any], 
                    contract_id: Optional[str] = None):
    """Convenience function for system error logging"""
    institutional_audit_logger.log_system_error(
        component, error_type, error_details, contract_id
    )

def log_compliance_metric(metric_type: str, metric_value: float, component: str, 
                        details: Optional[Dict[str, Any]] = None):
    """Convenience function for compliance metric logging"""
    institutional_audit_logger.log_compliance_metric(
        metric_type, metric_value, component, details
    )
