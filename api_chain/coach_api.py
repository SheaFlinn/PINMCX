from typing import Dict, Any
import logging
from api_chain import scraper_api, reframer_api, patcher_api, weigher_api, balancer_api, retester_api, publisher_api, notifier_api

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_stage_output(stage_name: str, output: Dict, required_keys: list) -> bool:
    """Validate that a stage's output contains all required keys."""
    missing_keys = [key for key in required_keys if key not in output]
    if missing_keys:
        raise ValueError(f"Missing required keys in {stage_name} output: {missing_keys}")
    return True

def run_contract_pipeline(city: str, headline: str) -> Dict:
    """
    Main pipeline function that coordinates all 8 API stages.
    
    Args:
        city (str): Name of the city
        headline (str): Civic headline to process
        
    Returns:
        dict: Either error object or success object with final contract
    """
    try:
        # Stage 1: Scraper API
        print(f"[Coach] Starting scraper stage...")
        scraper_output = scraper_api.run_scraper(city)
        validate_stage_output("scraper", scraper_output, ["city", "source", "headlines"])
        
        # Stage 2: Reframer API
        print(f"[Coach] Starting reframer stage...")
        reframer_output = reframer_api.run_reframer(scraper_output)
        validate_stage_output("reframer", reframer_output, ["title", "city", "question", "yes_option", "no_option"])
        
        # Stage 3: Patcher API
        print(f"[Coach] Starting patcher stage...")
        patcher_output = patcher_api.run_patcher(reframer_output)
        validate_stage_output("patcher", patcher_output, ["title", "city", "question", "yes_option", "no_option"])
        
        # Stage 4: Weigher API
        print(f"[Coach] Starting weigher stage...")
        weigher_output = weigher_api.run_weigher(patcher_output)
        validate_stage_output("weigher", weigher_output, ["title", "city", "question", "weight", "bias_score"])
        
        # Stage 5: Balancer API
        print(f"[Coach] Starting balancer stage...")
        balancer_output = balancer_api.run_balancer(weigher_output)
        validate_stage_output("balancer", balancer_output, ["title", "city", "question", "odds", "xp_threshold"])
        
        # Stage 6: Retester API
        print(f"[Coach] Starting retester stage...")
        retester_output = retester_api.run_retester(balancer_output)
        validate_stage_output("retester", retester_output, ["title", "city", "question", "status"])
        
        # Stage 7: Publisher API
        print(f"[Coach] Starting publisher stage...")
        publisher_output = publisher_api.run_publisher(retester_output)
        validate_stage_output("publisher", publisher_output, ["title", "city", "question", "contract_id"])
        
        # Stage 8: Notifier API
        print(f"[Coach] Starting notifier stage...")
        notifier_output = notifier_api.run_notifier(publisher_output)
        validate_stage_output("notifier", notifier_output, ["title", "city", "question", "notification_id"])
        
        # Return success object
        return {
            "status": "success",
            "contract": notifier_output
        }
        
    except Exception as e:
        logger.error(f"Error in pipeline: {str(e)}")
        return {
            "status": "error",
            "stage": e.__class__.__name__,
            "error": str(e)
        }

if __name__ == "__main__":
    # Example usage
    result = run_contract_pipeline("memphis", "City Council debates police budget")
    print(f"\nPipeline result: {result['status']}")
    if result['status'] == 'success':
        print(f"\nFinal contract: {result['contract']}")
    else:
        print(f"\nError occurred in stage: {result['stage']}")
        print(f"Error message: {result['error']}")
