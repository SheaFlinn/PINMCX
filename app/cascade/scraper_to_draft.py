def transform_headline_to_draft(headline: str, city: str) -> dict:
    """
    Create an initial contract draft from a headline.
    
    Args:
        headline (str): The raw headline text
        city (str): The city associated with the headline
        
    Returns:
        dict: Initial contract draft with basic fields
    """
    return {
        "city": city,
        "title": headline,
        "refined_title": None,
        "actor": None,
        "scope": None,
        "timeline": None,
        "weight": 0.5,
        "bias_score": 0.0,
        "stage_log": [
            {
                "stage": "scraper",
                "input": headline,
                "output": "Initialized contract draft object from headline only.",
                "verdict": "pending"
            }
        ],
        "status": "draft"
    }
