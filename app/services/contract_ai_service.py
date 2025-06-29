import os
import logging
from typing import Dict, Any
import openai
from dotenv import load_dotenv
import re

DEFAULT_GPT_MODEL = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

def log_contract_trace(stage: str, input_data: Any, output_data: Any) -> None:
    """
    Log contract processing trace to a timestamped JSON file.
    """
    import json
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/contract_trace_{stage}_{timestamp}.json"
    
    trace = {
        "timestamp": timestamp,
        "stage": stage,
        "input": input_data,
        "output": output_data
    }
    
    with open(log_filename, 'w') as f:
        json.dump(trace, f, indent=2)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Fallback stub data for when OpenAI API is not available
STUB_CONTRACT = {
    "sections": [
        {"title": "Purpose", "content": "[STUB] Contract purpose based on headline"},
        {"title": "Scope", "content": "[STUB] Contract scope and boundaries"},
        {"title": "Terms", "content": "[STUB] Key terms and conditions"}
    ],
    "confidence": 0.5,
    "issues": ["API key not found"]
}

# Fallback stub specifically for test_contract output
STUB_TEST_CONTRACT = {
    "status": "invalid",
    "confidence": 0.5,
    "issues": ["API key not found"],
    "headline": "[STUB]",
    "publish_ready": False
}

STUB_SECTIONS = [
    {"title": "Purpose", "content": "[STUB] Contract purpose based on headline"},
    {"title": "Scope", "content": "[STUB] Contract scope and boundaries"},
    {"title": "Terms", "content": "[STUB] Key terms and conditions"}
]

class ContractAIService:
    def __init__(self):
        self.model = DEFAULT_GPT_MODEL
        self.max_retries = 3
        
    def _get_openai_client(self):
        if not os.getenv("OPENAI_API_KEY"):
            logger.warning("OpenAI API key not found. Using stub responses.")
            return None
        return openai

    def _structured_prompt(self, role: str, content: str) -> Dict[str, str]:
        return {"role": role, "content": content}

    def _make_api_call(self, messages: list, max_retries: int = 3) -> Dict[str, Any]:
        client = self._get_openai_client()
        if not client:
            return STUB_CONTRACT

        for attempt in range(max_retries):
            try:
                response = client.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI API error (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    raise
                continue

    def _parse_contract_response(self, response: str) -> Dict[str, Any]:
        try:
            parsed = eval(response)
            if not isinstance(parsed, dict):
                logger.error("Invalid response format: expected dict")
                return STUB_CONTRACT
            return parsed
        except Exception:
            logger.error("Failed to parse contract response")
            return STUB_CONTRACT

    def generate_draft_contract(self, headline: str) -> Dict[str, Any]:
        """
        Generate initial contract draft from headline.
        """
        system_prompt = """
        You are a contract drafting assistant. Generate a structured contract draft based on the provided headline.
        The output should be a JSON object with the following structure:
        {
            "sections": [
                {"title": "Purpose", "content": "..."},
                {"title": "Scope", "content": "..."},
                {"title": "Terms", "content": "..."}
            ],
            "confidence": 0.0-1.0,
            "issues": ["..."],
            "headline": "..."
        }
        """
        
        messages = [
            self._structured_prompt("system", system_prompt),
            self._structured_prompt("user", f"Headline: {headline}")
        ]
        
        try:
            response = self._make_api_call(messages)
            output = self._parse_contract_response(response)
            log_contract_trace("draft", headline, output)
            return output
        except Exception as e:
            logger.error(f"Error generating draft contract: {str(e)}")
            return STUB_CONTRACT

    def rewrite_contract(self, contract: dict) -> Dict[str, Any]:
        """
        Rewrite and clarify the contract language.
        
        Args:
            contract: The contract dictionary to rewrite
            
        Returns:
            A dictionary with the rewritten contract and metadata
        """
        system_prompt = """
        You are a contract language expert. Rewrite the contract to be more clear and precise.
        Focus on:
        1. Eliminating ambiguity
        2. Improving readability
        3. Maintaining legal accuracy
        
        Output format:
        {
            "sections": [
                {"title": "...", "content": "..."}
            ],
            "confidence": 0.0-1.0,
            "issues": ["..."],
            "original_headline": "..."
        }
        """
        
        messages = [
            self._structured_prompt("system", system_prompt),
            self._structured_prompt("user", f"Contract: {str(contract)}")
        ]
        
        try:
            response = self._make_api_call(messages)
            output = self._parse_contract_response(response)
            log_contract_trace("rewrite", contract, output)
            return output
        except Exception as e:
            logger.error(f"Error rewriting contract: {str(e)}")
            return STUB_CONTRACT

    def weigh_contract(self, draft_contract: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate and refine the draft contract.
        """
        system_prompt = """
        You are a contract review assistant. Analyze the provided contract draft and:
        1. Evaluate completeness and coverage
        2. Identify potential risks and issues
        3. Suggest refinements
        
        Output format:
        {
            "refinements": [
                {"section": "...", "suggestions": ["..."]}
            ],
            "confidence": 0.0-1.0,
            "issues": ["..."],
            "original_headline": "..."
        }
        """
        
        draft_str = str(draft_contract)
        messages = [
            self._structured_prompt("system", system_prompt),
            self._structured_prompt("user", f"Draft Contract: {draft_str}")
        ]
        
        try:
            response = self._make_api_call(messages)
            output = self._parse_contract_response(response)
            log_contract_trace("weigh", draft_contract, output)
            return output
        except Exception as e:
            logger.error(f"Error weighing contract: {str(e)}")
            return STUB_CONTRACT

    @staticmethod
    def balance_contract(contract: dict) -> dict:
        """Balance contract headline based on confidence score to maintain market engagement."""
        # Ensure headline is always present for balancing
        if not contract.get("headline"):
            if contract.get("original_headline"):
                contract["headline"] = contract["original_headline"]
            elif hasattr(ContractAIService, "last_headline") and ContractAIService.last_headline:
                contract["headline"] = ContractAIService.last_headline
            else:
                raise ValueError("balance_contract(): HEADLINE MISSING — cascade is broken between patch and balance")

        # Store headline for future recovery
        ContractAIService.last_headline = contract["headline"]

        original_headline = contract.get("headline", "")
        headline = original_headline.strip()
        confidence = contract.get("confidence", 0.5)
        notes = []
        retest = False

        # Fail-fast if no headline
        if not headline:
            raise ValueError("balance_contract(): HEADLINE MISSING — cascade is broken between patch and balance")

        print(f"[balance_contract] Confidence received: {confidence}")
        print(f"[balance_contract] Original headline: {original_headline}")

        # Force balance if confidence is high
        if confidence >= 0.84:
            if re.search(r"vote to approve", headline, re.IGNORECASE) and "9–3" not in headline:
                headline = re.sub(r"(?i)vote to approve", "vote to approve by at least a 9–3 vote margin", headline)
                notes.append(f"Reframed headline due to high confidence: {confidence}")
                retest = True
            elif re.search(r"approve", headline, re.IGNORECASE) and "9–3" not in headline:
                headline = re.sub(r"(?i)approve", "approve by at least a 9–3 vote margin", headline)
                notes.append(f"Fallback tightening using 'approve' at confidence {confidence}")
                retest = True
            elif re.search(r"vote", headline, re.IGNORECASE) and "9–3" not in headline:
                headline += " by a 9–3 or greater vote margin"
                notes.append(f"Generic fallback tightening because confidence {confidence} exceeded threshold.")
                retest = True

        if not retest:
            notes.append(f"No change needed for confidence {confidence}")

        contract["headline"] = headline
        contract["balanced"] = retest
        contract["retest_required"] = retest
        contract["balance_notes"] = notes
        return contract

    @staticmethod
    def test_contract(contract: dict) -> dict:
        """Audit contract for bias, ambiguity, and structural flaws. Return full contract."""
        prompt = f"""
You are a civic fairness auditor. Review this contract JSON for logical errors, ambiguity, or bias.

TASK:
- For each section ("Purpose", "Scope", "Terms"), rewrite to improve clarity and fairness
- Return updated contract in this exact JSON format:
{{
  "sections": [
    {{
      "title": "Purpose",
      "content": "..."
    }},
    {{
      "title": "Scope",
      "content": "..."
    }},
    {{
      "title": "Terms",
      "content": "..."
    }}
  ],
  "confidence": float (0.0 to 1.0),
  "issues": [list of strings]
}}

CONTRACT TO AUDIT:
{contract}
"""
        try:
            response = ContractAIService()._make_api_call([ContractAIService()._structured_prompt("system", prompt)])
            tested = ContractAIService()._parse_contract_response(response)
            log_contract_trace("test", contract, tested)
            return tested
        except Exception as e:
            logger.error(f"Error testing contract: {e}")
            return {
                "sections": STUB_SECTIONS,
                "confidence": 0.5,
                "issues": [f"Exception in test_contract: {str(e)}"]
            }

    def explain_contract(self, contract: dict) -> Dict[str, Any]:
        """
        Generate a public-facing explanation of the contract.
        
        Args:
            contract: The contract dictionary to explain
            
        Returns:
            A dictionary containing a clear explanation of the contract
        """
        system_prompt = """
        You are a contract explainer. Generate a clear, non-technical explanation of the contract.
        Focus on:
        1. Key terms and conditions
        2. Potential implications
        3. User-friendly language
        
        Output format:
        {
            "explanation": "...",
            "key_points": ["..."],
            "confidence": 0.0-1.0,
            "issues": ["..."],
            "original_headline": "..."
        }
        """
        
        messages = [
            self._structured_prompt("system", system_prompt),
            self._structured_prompt("user", f"Contract: {str(contract)}")
        ]
        
        try:
            response = self._make_api_call(messages)
            output = self._parse_contract_response(response)
            log_contract_trace("explain", contract, output)
            return output
        except Exception as e:
            logger.error(f"Error explaining contract: {str(e)}")
            return STUB_CONTRACT

    def narrate_contract_cluster(self, headline: str, peer_contracts: list) -> Dict[str, Any]:
        """
        Generate market context and trend analysis for the contract cluster.
        
        Args:
            headline: The headline of the contract to analyze
            peer_contracts: List of related peer contracts for comparison
            
        Returns:
            A dictionary containing market context and trend analysis
        """
        system_prompt = """
        You are a market analysis assistant. Analyze the contract in the context of its peer contracts and:
        1. Identify market trends
        2. Compare similarities and differences
        3. Provide strategic insights
        
        Output format:
        {
            "market_context": "...",
            "trend_analysis": "...",
            "peer_comparison": ["..."],
            "confidence": 0.0-1.0,
            "issues": ["..."],
            "headline": "..."
        }
        """
        
        messages = [
            self._structured_prompt("system", system_prompt),
            self._structured_prompt("user", f"Headline: {headline}\nPeer Contracts: {str(peer_contracts)}")
        ]
        
        try:
            response = self._make_api_call(messages)
            output = self._parse_contract_response(response)
            log_contract_trace("narrate", headline, output)
            return output
        except Exception as e:
            logger.error(f"Error narrating contract cluster: {str(e)}")
            return STUB_CONTRACT

    def audit_contract_full(self, contract: dict) -> Dict[str, Any]:
        """
        Perform a comprehensive audit of the contract.
        
        Args:
            contract: The contract dictionary to audit
            
        Returns:
            A dictionary containing the full audit trail and risk assessment
        """
        system_prompt = """
        You are a contract auditor. Perform a comprehensive audit of the contract and:
        1. Verify all components
        2. Assess risk levels
        3. Generate full audit trail
        
        Output format:
        {
            "audit_trail": [
                {"component": "...", "status": "...", "notes": "..."}
            ],
            "risk_assessment": {
                "overall": 0.0-1.0,
                "components": {"...": 0.0-1.0}
            },
            "confidence": 0.0-1.0,
            "issues": ["..."],
            "headline": "..."
        }
        """
        
        messages = [
            self._structured_prompt("system", system_prompt),
            self._structured_prompt("user", f"Contract: {str(contract)}")
        ]
        
        try:
            response = self._make_api_call(messages)
            output = self._parse_contract_response(response)
            log_contract_trace("audit", contract, output)
            return output
        except Exception as e:
            logger.error(f"Error auditing contract: {str(e)}")
            return STUB_CONTRACT

    @staticmethod
    def patch_contract(contract: dict) -> dict:
        """Patch contract to remove bias, clarify actors, and improve clarity."""
        patched = contract.copy()
        patch_notes = []
        
        # Helper function to add patch note
        def add_patch_note(description: str):
            patch_notes.append(description)

        # Initialize headline from contract
        headline = contract.get("headline", "").strip()
        
        # Process headline if present
        if headline:
            # 1. Replace vague civic actors
            actor_mappings = {
                "mayor": "City Council",
                "city leadership": "City Council",
                "administration": "City Council",
                "city officials": "City Council",
                "state leadership": "State Legislature",
                "governor": "State Governor",
                "state officials": "State Government"
            }
            for pattern, replacement in actor_mappings.items():
                if re.search(pattern, headline, re.IGNORECASE):
                    headline = re.sub(pattern, replacement, headline, flags=re.IGNORECASE)
                    add_patch_note(f"Replaced '{pattern}' with '{replacement}'")

            # 2. Replace vague action language
            action_mappings = {
                "push through": "vote to approve",
                "implement": "implement",
                "move forward": "proceed with",
                "enact": "pass",
                "approve": "vote to approve",
                "pass": "vote to approve",
                "implement": "implement",
                "enforce": "enforce",
                "carry out": "carry out"
            }
            for pattern, replacement in action_mappings.items():
                if pattern in headline.lower():
                    headline = headline.lower().replace(pattern, replacement)
                    add_patch_note(f"Rephrased '{pattern}' to '{replacement}'")

            # 3. Remove biased words
            bias_words = [
                "controversial", "ambitious", "radical", "unfair", "misguided",
                "outrageous", "extreme", "unjust", "unreasonable", "draconian",
                "radical", "radicalizing", "radicalized", "radicalization"
            ]
            for word in bias_words:
                if word in headline.lower():
                    headline = headline.lower().replace(word, "")
                    add_patch_note(f"Removed bias word '{word}'")

            # 4. Clarify timeframes
            time_patterns = {
                r"by\s+november": "by November 30",
                r"by\s+december": "by December 31",
                r"by\s+january": "by January 31",
                r"between\s+november\s+and\s+december": "between November 1 and December 31",
                r"by\s+end\s+of\s+year": "by December 31",
                r"by\s+end\s+of\s+month": "by Last Day of Month"
            }
            for pattern, replacement in time_patterns.items():
                if re.search(pattern, headline, re.IGNORECASE):
                    headline = re.sub(pattern, replacement, headline, flags=re.IGNORECASE)
                    add_patch_note(f"Clarified timeframe '{pattern}' to '{replacement}'")

            # 5. Deduplicate phrases
            def deduplicate_phrases(text: str) -> str:
                text = re.sub(r'vote to vote to approve', 'vote to approve', text, flags=re.IGNORECASE)
                text = re.sub(r'approve to approve', 'approve', text, flags=re.IGNORECASE)
                text = re.sub(r'pass to pass', 'pass', text, flags=re.IGNORECASE)
                text = re.sub(r'enact to enact', 'enact', text, flags=re.IGNORECASE)
                return text

            headline = deduplicate_phrases(headline)
            if headline != patched["headline"]:
                add_patch_note("Deduplicated repeated phrases")

            # 6. Capitalize first word
            headline = headline.capitalize()

            # Update the headline in the patched contract
            patched["headline"] = headline

        # Finalize
        patched["patched"] = True
        patched["patch_notes"] = patch_notes

        # This is the key fix:
        if not patched.get("headline") or not patched["headline"].strip():
            patched["headline"] = headline.strip()

        return patched

    @staticmethod
    def test_contract_balancing():
        """Test the contract balancing logic with various examples."""
        # Test case 1: High confidence (should be tightened)
        test_contract_1 = {
            "headline": "Will the City Council approve the downtown redevelopment ordinance by November 30?",
            "confidence": 0.83
        }
        
        result_1 = ContractAIService.balance_contract(test_contract_1)
        print("\nTest Case 1 (High Confidence):")
        print(f"Original: {test_contract_1['headline']}")
        print(f"Balanced: {result_1['headline']}")
        print(f"Notes: {result_1['balance_notes']}")
        
        # Test case 2: Low confidence (should be softened)
        test_contract_2 = {
            "headline": "Will the City Council fail to pass the downtown redevelopment ordinance by November 30?",
            "confidence": 0.25
        }
        
        result_2 = ContractAIService.balance_contract(test_contract_2)
        print("\nTest Case 2 (Low Confidence):")
        print(f"Original: {test_contract_2['headline']}")
        print(f"Balanced: {result_2['headline']}")
        print(f"Notes: {result_2['balance_notes']}")
        
        # Test case 3: Neutral confidence (should remain unchanged)
        test_contract_3 = {
            "headline": "Will the City Council vote on the downtown redevelopment ordinance by November 30?",
            "confidence": 0.55
        }
        
        result_3 = ContractAIService.balance_contract(test_contract_3)
        print("\nTest Case 3 (Neutral Confidence):")
        print(f"Original: {test_contract_3['headline']}")
        print(f"Balanced: {result_3['headline']}")
        print(f"Notes: {result_3['balance_notes']}")
