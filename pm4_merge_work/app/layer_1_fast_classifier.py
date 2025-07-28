"""
Layer 1: Fast LLM Classifier - Cheap Civic Relevance Detection
Memphis Civic Market - July 28, 2025

This module uses GPT-3.5 (cheap) to quickly classify headlines that passed
Layer 0 heuristic filtering for civic relevance and bettability.
"""

import openai
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class FastClassifierResult:
    """Result of fast LLM classification"""
    passed: bool
    confidence: float  # 0.0-1.0
    topic: str
    entity_tags: List[str]
    reason: str
    processing_time_ms: float
    tokens_used: int
    cost_usd: float

class Layer1FastClassifier:
    """
    Fast, cheap LLM classifier for civic relevance.
    Uses GPT-3.5 to determine if headlines are locally bettable civic events.
    """
    
    def __init__(self, api_key: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = openai.OpenAI()  # Uses OPENAI_API_KEY env var
        
        # Cost tracking (GPT-3.5-turbo pricing)
        self.cost_per_1k_tokens = 0.0015  # $0.0015 per 1K tokens for GPT-3.5-turbo
        
        # Classification prompt template
        self.classification_prompt = """You are a civic prediction market classifier for Memphis, Tennessee.

Analyze this headline and determine if it represents a locally bettable civic decision or controversy.

CRITERIA FOR "YES" (bettable civic event):
- Clear civic agent (council, commission, mayor, school board, etc.)
- Specific action or decision with uncertain outcome
- Definite timeframe or deadline
- Outcome can be objectively verified
- Local Memphis/Shelby County relevance
- Genuine uncertainty (not foregone conclusion)

CRITERIA FOR "NO" (not bettable):
- No clear civic agent or decision
- Purely informational/historical content
- Vague or hypothetical scenarios
- No clear resolution criteria
- Foregone conclusions or obvious outcomes

HEADLINE: "{headline}"

Respond in JSON format:
{{
    "decision": "YES" or "NO",
    "confidence": 0.0-1.0,
    "topic": "brief topic description",
    "entity_tags": ["list", "of", "relevant", "entities"],
    "reason": "brief explanation of decision"
}}"""

    def classify_headline(self, headline: str, source: str = "") -> FastClassifierResult:
        """
        Classify a headline using fast LLM for civic relevance.
        
        Args:
            headline: The headline to classify
            source: Source of the headline (for logging)
            
        Returns:
            FastClassifierResult with classification decision and metadata
        """
        start_time = datetime.now()
        
        try:
            # Prepare prompt
            prompt = self.classification_prompt.format(headline=headline)
            
            # Call GPT-3.5-turbo (cheap and fast)
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a civic prediction market classifier."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=200,   # Keep responses short
                response_format={"type": "json_object"}
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            result_data = json.loads(response_text)
            
            # Extract classification data
            decision = result_data.get("decision", "NO").upper()
            confidence = float(result_data.get("confidence", 0.0))
            topic = result_data.get("topic", "Unknown")
            entity_tags = result_data.get("entity_tags", [])
            reason = result_data.get("reason", "No reason provided")
            
            # Calculate costs
            tokens_used = response.usage.total_tokens
            cost_usd = (tokens_used / 1000) * self.cost_per_1k_tokens
            
            # Determine pass/fail
            passed = decision == "YES" and confidence >= 0.6
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Log result
            status = 'PASS' if passed else 'FAIL'
            self.logger.info(f"Layer 1 Classifier: {status} - {headline[:100]}... - Confidence: {confidence:.2f}")
            
            return FastClassifierResult(
                passed=passed,
                confidence=confidence,
                topic=topic,
                entity_tags=entity_tags,
                reason=reason,
                processing_time_ms=processing_time_ms,
                tokens_used=tokens_used,
                cost_usd=cost_usd
            )
            
        except Exception as e:
            self.logger.error(f"Layer 1 classification failed: {str(e)}")
            
            # Return failure result
            end_time = datetime.now()
            processing_time_ms = (end_time - start_time).total_seconds() * 1000
            
            return FastClassifierResult(
                passed=False,
                confidence=0.0,
                topic="Error",
                entity_tags=[],
                reason=f"Classification error: {str(e)}",
                processing_time_ms=processing_time_ms,
                tokens_used=0,
                cost_usd=0.0
            )
    
    def batch_classify(self, headlines: List[str], sources: List[str] = None) -> List[FastClassifierResult]:
        """
        Classify a batch of headlines.
        
        Args:
            headlines: List of headlines to classify
            sources: Optional list of sources (same length as headlines)
            
        Returns:
            List of FastClassifierResult objects
        """
        if sources is None:
            sources = ["unknown"] * len(headlines)
        
        results = []
        total_cost = 0.0
        
        for i, headline in enumerate(headlines):
            source = sources[i] if i < len(sources) else "unknown"
            result = self.classify_headline(headline, source)
            results.append(result)
            total_cost += result.cost_usd
        
        # Log batch statistics
        passed_count = sum(1 for r in results if r.passed)
        pass_rate = (passed_count / len(results)) * 100 if results else 0
        
        self.logger.info(f"Layer 1 Batch: {passed_count}/{len(results)} passed ({pass_rate:.1f}%) - Total cost: ${total_cost:.4f}")
        
        return results
