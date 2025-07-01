from app import create_app
app = create_app()
app.app_context().push()

import json

from app.cascade.scraper_to_draft import transform_headline_to_draft
from app.cascade.reframer_api import reframe_title_as_question
from app.cascade.refiner_api import refine_question_with_scope
from app.cascade.patcher_api import patch_bias_and_vagueness
from app.cascade.filter_api import filter_contract_quality
from app.cascade.weigher_api import weigh_contract_predictive_value
from app.cascade.balancer_api import balance_for_odds_and_xp
from app.cascade.publisher_api import publish_contract

def run_cascade_on_headline(headline: str, city: str = "Memphis") -> dict:
    """
    Run the full 8-stage cascade pipeline on a headline to generate a contract.
    
    Args:
        headline (str): The raw headline text
        city (str): The city associated with the headline
        
    Returns:
        dict: The final contract draft dictionary with all processing stages
    """
    draft = transform_headline_to_draft(headline, city)
    draft = reframe_title_as_question(draft)
    draft = refine_question_with_scope(draft)
    draft = patch_bias_and_vagueness(draft)
    draft = filter_contract_quality(draft)
    
    if draft.get("status") != "rejected":
        draft = weigh_contract_predictive_value(draft)
        draft = balance_for_odds_and_xp(draft)
        draft = publish_contract(draft)
    
    return draft

if __name__ == "__main__":
    # Example usage
    example_headline = """City Council to vote on stadium funding"""
    result = run_cascade_on_headline(example_headline)
    print(json.dumps(result, indent=2))
