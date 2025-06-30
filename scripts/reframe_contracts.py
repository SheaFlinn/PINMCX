import json
import os
from datetime import datetime
from app.services.contract_ai_service import ContractAIService
from app import create_app

# -------------- CONFIG -----------------
INPUT_PATH = "drafts/draft_contracts.json"
OUTPUT_PATH = "drafts/reframed_contracts.json"
# --------------------------------------

def reframe_civic_headline(headline_data):
    """
    Convert civic headline data into a contract draft using ContractAIService.
    
    Args:
        headline_data: Dict containing city, headline, source, date, and url
        
    Returns:
        Dict: Contract draft in the required format
    """
    app = create_app()
    with app.app_context():
        service = ContractAIService()
        
        # Create a custom prompt for civic headlines
        prompt = f"""
        You are a civic contract generator for a municipal prediction market.
        
        Convert this civic headline into a binary prediction contract:
        
        City: {headline_data['city']}
        Headline: {headline_data['headline']}
        Source: {headline_data['source']}
        Date: {headline_data['date']}
        URL: {headline_data['url']}
        
        Output should be a JSON object with these fields:
        1. title: Short phrasing of the civic prediction
        2. purpose: Why this question matters for the city
        3. scope: What the contract includes and excludes
        4. terms: Clear YES/NO resolution rules
        5. source_url: Original news article URL
        """
        
        try:
            # Use the service to generate the draft
            draft = service.generate_draft_contract(prompt)
            
            # Transform the output to match the required format
            contract = {
                "title": draft.get("sections", [{}])[0].get("content", ""),
                "purpose": draft.get("sections", [{}])[1].get("content", ""),
                "scope": draft.get("sections", [{}])[2].get("content", ""),
                "terms": {
                    "YES": "",
                    "NO": "",
                    "resolution_source": headline_data["url"]
                },
                "source_url": headline_data["url"],
                "city": headline_data["city"],
                "status": "draft"
            }
            
            return contract
            
        except Exception as e:
            print(f"Error reframing headline: {headline_data['headline']}")
            print(str(e))
            return None

def main():
    if not os.path.exists(INPUT_PATH):
        print(f"Error: Input file {INPUT_PATH} not found")
        return
    
    with open(INPUT_PATH, "r") as f:
        drafts = json.load(f)

    reframed = []
    for entry in drafts:
        print(f"Reframing: {entry['headline']}")
        contract = reframe_civic_headline(entry)
        if contract:
            reframed.append(contract)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(reframed, f, indent=2)

    print(f"✅ Reframed {len(reframed)} contracts saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
