#!/usr/bin/env python3
"""
Production Contract Validation API - Memphis Civic Market

Provides reliable contract validation with institutional-grade QA:
- 30-70% probability range for market viability
- Required field validation
- Clear blocking reasons for admin review
- Rate limiting and error logging
- Robust error handling with no silent failures

Version: July_28_2025 - Production Market Viability Standards
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from functools import wraps
import hashlib

from .enhanced_contract_critic_enforcer import EnhancedContractCriticEnforcer
from .multi_variant_reframing_engine import MultiVariantReframingEngine, safe_success_rate_calculation

logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis or database)
rate_limit_storage = {}

@dataclass
class ValidationResult:
    """Results from contract validation"""
    contract_id: str
    passed: bool
    blocked: bool
    blocking_reason: Optional[str]
    probability_band: str  # "viable_30_70", "too_certain_70_plus", "too_uncertain_30_minus", "unresolvable"
    market_viability_score: float
    required_fields_missing: List[str]
    validation_timestamp: datetime
    processing_time_ms: int
    critic_analysis: Optional[Dict]
    variant_analysis: Optional[Dict]
    admin_review_required: bool
    error_details: Optional[str]

class ContractValidationAPI:
    """Production-ready contract validation API with institutional standards"""
    
    def __init__(self):
        """Initialize the validation API"""
        self.critic = EnhancedContractCriticEnforcer()
        self.reframer = MultiVariantReframingEngine()
        
        # Required contract fields for production
        self.required_fields = ['title', 'description', 'actor', 'timeline', 'resolution_criteria']
        
        # Rate limiting settings
        self.rate_limit_requests = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))  # per hour
        self.rate_limit_window = int(os.getenv('RATE_LIMIT_WINDOW', '3600'))  # seconds
        
        # Probability band thresholds
        self.min_viable_prob = 0.30
        self.max_viable_prob = 0.70
        
    def validate_contract(self, contract: Dict[str, Any], 
                         include_variants: bool = False,
                         user_id: Optional[str] = None) -> ValidationResult:
        """
        Validate contract with comprehensive QA and clear blocking reasons
        
        Args:
            contract: Contract to validate
            include_variants: Whether to generate and analyze variants
            user_id: User ID for rate limiting
            
        Returns:
            ValidationResult with detailed findings and clear blocking reasons
        """
        start_time = time.time()
        contract_id = self._generate_contract_id(contract)
        
        try:
            # Rate limiting check
            if user_id and not self._check_rate_limit(user_id):
                return ValidationResult(
                    contract_id=contract_id,
                    passed=False,
                    blocked=True,
                    blocking_reason="Rate limit exceeded. Please try again later.",
                    probability_band="rate_limited",
                    market_viability_score=0.0,
                    required_fields_missing=[],
                    validation_timestamp=datetime.utcnow(),
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    critic_analysis=None,
                    variant_analysis=None,
                    admin_review_required=False,
                    error_details="Rate limit exceeded"
                )
            
            # Required field validation
            missing_fields = self._validate_required_fields(contract)
            if missing_fields:
                return ValidationResult(
                    contract_id=contract_id,
                    passed=False,
                    blocked=True,
                    blocking_reason=f"Missing required fields: {', '.join(missing_fields)}. All contracts must include title, description, actor, timeline, and resolution_criteria.",
                    probability_band="invalid_fields",
                    market_viability_score=0.0,
                    required_fields_missing=missing_fields,
                    validation_timestamp=datetime.utcnow(),
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    critic_analysis=None,
                    variant_analysis=None,
                    admin_review_required=True,
                    error_details=f"Missing fields: {missing_fields}"
                )
            
            # Contract critic analysis
            logger.info(f"Starting critic analysis for contract: {contract.get('title', 'Unknown')}")
            critic_result = self.critic.analyze_single_contract(contract)
            
            # Determine probability band and blocking reason
            probability_band, blocking_reason = self._analyze_probability_band(critic_result, contract)
            
            # Variant analysis if requested
            variant_analysis = None
            if include_variants and not critic_result.blocked:
                try:
                    logger.info(f"Starting variant generation for contract: {contract.get('title', 'Unknown')}")
                    variant_result = self.reframer.generate_and_analyze_variants(contract)
                    variant_analysis = {
                        'total_variants': variant_result.total_variants,
                        'variants_passed': variant_result.passed_variants,
                        'variants_blocked': variant_result.blocked_variants,
                        'success_rate': safe_success_rate_calculation(variant_result.passed_variants, variant_result.total_variants),
                        'best_variant_title': variant_result.best_variant.get('title') if variant_result.best_variant else None,
                        'recommendation': variant_result.recommendation
                    }
                except Exception as e:
                    logger.error(f"Variant analysis failed: {str(e)}")
                    variant_analysis = {'error': str(e)}
            
            # Final validation result
            processing_time = int((time.time() - start_time) * 1000)
            
            return ValidationResult(
                contract_id=contract_id,
                passed=critic_result.passed and not critic_result.blocked,
                blocked=critic_result.blocked,
                blocking_reason=blocking_reason,
                probability_band=probability_band,
                market_viability_score=critic_result.market_balance_score,
                required_fields_missing=[],
                validation_timestamp=datetime.utcnow(),
                processing_time_ms=processing_time,
                critic_analysis={
                    'overall_score': critic_result.overall_score,
                    'market_balance_score': critic_result.market_balance_score,
                    'total_issues': len(critic_result.issues_found),
                    'blocking_issues': len(critic_result.blocking_issues),
                    'admin_override_required': critic_result.admin_override_required
                },
                variant_analysis=variant_analysis,
                admin_review_required=critic_result.admin_override_required,
                error_details=None
            )
            
        except Exception as e:
            # Robust error handling - no silent failures
            error_msg = f"Contract validation failed: {str(e)}"
            logger.error(error_msg)
            
            return ValidationResult(
                contract_id=contract_id,
                passed=False,
                blocked=True,
                blocking_reason=f"Validation system error: {str(e)}. Please contact admin for review.",
                probability_band="system_error",
                market_viability_score=0.0,
                required_fields_missing=[],
                validation_timestamp=datetime.utcnow(),
                processing_time_ms=int((time.time() - start_time) * 1000),
                critic_analysis=None,
                variant_analysis=None,
                admin_review_required=True,
                error_details=error_msg
            )
    
    def _generate_contract_id(self, contract: Dict[str, Any]) -> str:
        """Generate unique contract ID for tracking"""
        contract_str = json.dumps(contract, sort_keys=True)
        return hashlib.md5(contract_str.encode()).hexdigest()[:12]
    
    def _validate_required_fields(self, contract: Dict[str, Any]) -> List[str]:
        """Validate that all required fields are present and non-empty"""
        missing_fields = []
        for field in self.required_fields:
            if not contract.get(field) or str(contract.get(field)).strip() == '':
                missing_fields.append(field)
        return missing_fields
    
    def _analyze_probability_band(self, critic_result, contract: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Analyze probability band and generate clear blocking reason"""
        
        # Check for specific blocking issues
        blocking_issues = critic_result.blocking_issues
        if not blocking_issues:
            return "viable_30_70", None
        
        # Analyze blocking reasons
        probability_bias_issues = [issue for issue in blocking_issues if issue.get('issue_type') == 'probability_bias']
        market_viability_issues = [issue for issue in blocking_issues if issue.get('issue_type') == 'market_viability']
        biased_framing_issues = [issue for issue in blocking_issues if issue.get('issue_type') == 'biased_framing']
        trading_balance_issues = [issue for issue in blocking_issues if issue.get('issue_type') == 'trading_balance']
        
        # Generate clear blocking reason
        if probability_bias_issues:
            issue = probability_bias_issues[0]
            description = issue.get('description', '')
            if 'near-certain' in description.lower() or 'obvious' in description.lower():
                return "too_certain_70_plus", f"Contract outcome is too certain (>70% probability). {description}"
            elif 'unlikely' in description.lower() or 'remote' in description.lower():
                return "too_uncertain_30_minus", f"Contract outcome is too uncertain (<30% probability). {description}"
            else:
                return "probability_unclear", f"Probability assessment unclear. {description}"
        
        if market_viability_issues:
            issue = market_viability_issues[0]
            return "not_marketable", f"Not suitable for prediction market. {issue.get('description', 'Market viability concerns.')}"
        
        if biased_framing_issues:
            issue = biased_framing_issues[0]
            return "biased_framing", f"Contract contains bias or loaded language. {issue.get('description', 'Neutral framing required.')}"
        
        if trading_balance_issues:
            issue = trading_balance_issues[0]
            return "trading_imbalance", f"Would not attract balanced trading. {issue.get('description', 'Both sides must be attractive to bettors.')}"
        
        # Generic blocking reason
        if blocking_issues:
            return "blocked_other", f"Contract blocked: {blocking_issues[0].get('description', 'See admin for details.')}"
        
        return "viable_30_70", None
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        current_time = time.time()
        user_key = f"rate_limit_{user_id}"
        
        # Clean old entries
        if user_key in rate_limit_storage:
            rate_limit_storage[user_key] = [
                timestamp for timestamp in rate_limit_storage[user_key]
                if current_time - timestamp < self.rate_limit_window
            ]
        else:
            rate_limit_storage[user_key] = []
        
        # Check rate limit
        if len(rate_limit_storage[user_key]) >= self.rate_limit_requests:
            return False
        
        # Add current request
        rate_limit_storage[user_key].append(current_time)
        return True

# Flask API endpoints
app = Flask(__name__)
validator = ContractValidationAPI()

@app.route('/api/validate-contract', methods=['POST'])
def validate_contract_endpoint():
    """Validate a single contract"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        contract = data.get('contract', {})
        include_variants = data.get('include_variants', False)
        user_id = data.get('user_id', request.remote_addr)
        
        result = validator.validate_contract(contract, include_variants, user_id)
        
        return jsonify(asdict(result))
        
    except Exception as e:
        logger.error(f"API endpoint error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': 'July_28_2025_Production'
    })

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run development server
    app.run(debug=False, host='0.0.0.0', port=5000)
