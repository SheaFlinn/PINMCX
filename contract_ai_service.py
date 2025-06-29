import openai
import json
import logging
from typing import Optional, Dict

DEFAULT_GPT_MODEL = "gpt-4o"

class ContractAIService:
    def __init__(self, model: str = DEFAULT_GPT_MODEL):
        self.model = model
        self.last_headline: Optional[str] = None

    def generate_contract(self, headline: str) -> Optional[Dict]:
        """Use GPT model to generate contract draft from headline"""
        self.last_headline = headline
        try:
            prompt = self._build_prompt(headline)
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            content = response.choices[0].message['content']
            return self._parse_contract_response(content)
        except Exception as e:
            logging.error(f"ContractAI error for headline '{headline}': {str(e)}")
            return None

    def _build_prompt(self, headline: str) -> str:
        return f"""
        Given the following headline: "{headline}",
        generate a civic prediction market contract in JSON format with these fields:
        - title
        - resolution_criteria
        - deadline (ISO 8601)
        - domain
        - confidence_boost
        - clarity_score
        Output only the JSON object.
        """

    def _parse_contract_response(self, raw: str) -> Optional[Dict]:
        """Safely parse the GPT output into a contract dict"""
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logging.warning("AI returned invalid JSON, attempting fix...")
            try:
                json_start = raw.find("{")
                json_end = raw.rfind("}") + 1
                return json.loads(raw[json_start:json_end])
            except Exception as e:
                logging.error(f"Failed to fix/parse JSON: {str(e)}")
                return None
