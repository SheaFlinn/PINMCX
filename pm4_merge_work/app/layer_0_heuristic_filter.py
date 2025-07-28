"""
Layer 0: Heuristic Civic Filter - Free, Fast Pre-screening
Memphis Civic Market - July 28, 2025

This module provides free, instant filtering of headlines/submissions to reject
obviously unfit content before expensive LLM processing.

Filter Criteria:
- Civic agent present (council, commission, mayor, etc.)
- Clear action verb (vote, approve, reject, propose, etc.)
- Definite timeframe (date, deadline, period)
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class HeuristicFilterResult:
    """Result of heuristic filtering"""
    passed: bool
    score: float  # 0.0-1.0 confidence score
    missing_elements: List[str]
    detected_elements: Dict[str, str]
    reason: str
    processing_time_ms: float

class Layer0HeuristicFilter:
    """
    Fast, free heuristic filter for civic content.
    Rejects obviously unfit headlines before expensive LLM processing.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # CIVIC AGENTS - Memphis-specific entities
        self.civic_agents = {
            'council', 'city council', 'memphis city council', 'councilman', 'councilwoman',
            'mayor', 'memphis mayor', 'city hall', 'city of memphis',
            'commission', 'county commission', 'shelby county', 'commissioner',
            'school board', 'memphis school board', 'mscs', 'superintendent',
            'mata', 'mlgw', 'memphis police', 'mpd', 'fire department',
            'planning commission', 'zoning board', 'housing authority',
            'tennessee', 'state legislature', 'governor'
        }
        
        # ACTION VERBS - Civic decision-making actions
        self.action_verbs = {
            'vote', 'votes', 'voting', 'approve', 'approves', 'approved',
            'reject', 'rejects', 'rejected', 'pass', 'passes', 'passed',
            'propose', 'proposes', 'proposed', 'plan', 'plans', 'planning',
            'consider', 'considers', 'review', 'reviews', 'decide', 'decides',
            'implement', 'implements', 'launch', 'launches', 'delay', 'delays',
            'postpone', 'postpones', 'cancel', 'cancels', 'fund', 'funds',
            'budget', 'budgets', 'allocate', 'allocates'
        }
        
        # TIMEFRAME PATTERNS
        self.timeframe_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # Dates
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b',
            r'\b(next|this)\s+(week|month|year|quarter)\b',
            r'\b(by|before|after|until)\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b',
            r'\bfiscal\s+year\s+\d{4}\b',
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(today|tomorrow|yesterday)\b',
            r'\bdeadline\b'
        ]
        
        self.compiled_timeframe_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.timeframe_patterns]
    
    def filter_headline(self, headline: str, source: str = "") -> HeuristicFilterResult:
        """Apply heuristic filter to a headline/submission."""
        start_time = datetime.now()
        
        if not headline or not isinstance(headline, str):
            return HeuristicFilterResult(
                passed=False, score=0.0, missing_elements=['headline'],
                detected_elements={}, reason="Empty or invalid headline",
                processing_time_ms=0.0
            )
        
        headline_lower = headline.lower()
        detected_elements = {}
        missing_elements = []
        score_components = []
        
        # 1. CHECK FOR CIVIC AGENT
        civic_agent_found = None
        for agent in self.civic_agents:
            if agent in headline_lower:
                civic_agent_found = agent
                detected_elements['civic_agent'] = agent
                score_components.append(0.4)  # 40% of score
                break
        
        if not civic_agent_found:
            missing_elements.append('civic_agent')
        
        # 2. CHECK FOR ACTION VERB
        action_verb_found = None
        for verb in self.action_verbs:
            if re.search(r'\b' + re.escape(verb) + r'\b', headline_lower):
                action_verb_found = verb
                detected_elements['action_verb'] = verb
                score_components.append(0.3)  # 30% of score
                break
        
        if not action_verb_found:
            missing_elements.append('action_verb')
        
        # 3. CHECK FOR TIMEFRAME
        timeframe_found = None
        for pattern in self.compiled_timeframe_patterns:
            match = pattern.search(headline)
            if match:
                timeframe_found = match.group()
                detected_elements['timeframe'] = timeframe_found
                score_components.append(0.3)  # 30% of score
                break
        
        if not timeframe_found:
            missing_elements.append('timeframe')
        
        # CALCULATE FINAL SCORE AND DECISION
        total_score = sum(score_components)
        passed = total_score >= 0.6  # Need at least 2 of 3 elements
        
        # Generate reason
        if passed:
            reason = f"Civic headline detected: {', '.join(detected_elements.keys())}"
        else:
            reason = f"Missing required elements: {', '.join(missing_elements)}"
        
        # Calculate processing time
        end_time = datetime.now()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000
        
        return HeuristicFilterResult(
            passed=passed, score=total_score, missing_elements=missing_elements,
            detected_elements=detected_elements, reason=reason,
            processing_time_ms=processing_time_ms
        )
