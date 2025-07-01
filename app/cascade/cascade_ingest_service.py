from typing import Dict, List, Optional
from datetime import datetime
import logging
from pathlib import Path
import json

from app.models import ContractDraft, PublishedContract
from app.cascade.contract_ai_service import ContractAIService
from app.cascade.scraper_to_draft import transform_headline_to_draft
from app.cascade.reframer_api import reframe_title_as_question
from app.cascade.refiner_api import refine_question_with_scope
from app.cascade.patcher_api import patch_bias_and_vagueness
from app.cascade.filter_api import filter_contract_quality
from app.cascade.weigher_api import weigh_contract_predictive_value
from app.cascade.balancer_api import balance_for_odds_and_xp
from app.cascade.publisher_api import publish_contract
from app.cascade.scraper_config_loader import load_scraper_config
from app.cascade.scrapers import fetch_city_headlines

logger = logging.getLogger(__name__)

class CascadeIngestService:
    """
    Service for automated ingestion of civic headlines into the contract generation cascade.
    """

    def __init__(self):
        self.config_dir = Path("scraper_configs")
        self.config_dir.mkdir(exist_ok=True)

    def load_city_config(self, city_name: str) -> Dict:
        """
        Load and validate city-specific scraper configuration.
        """
        try:
            config = load_scraper_config(city_name)
            logger.info(f"Loaded config for city: {city_name}")
            return config
        except FileNotFoundError as e:
            logger.error(f"Config not found for city: {city_name}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config for city: {city_name}")
            raise

    def fetch_headlines(self, city_name: str) -> List[Dict]:
        """
        Fetch headlines from all sources for a city.
        """
        try:
            config = self.load_city_config(city_name)
            headlines = fetch_city_headlines(city_name)
            logger.info(f"Fetched {len(headlines)} headlines for {city_name}")
            return headlines
        except Exception as e:
            logger.error(f"Error fetching headlines for {city_name}: {str(e)}")
            raise

    def process_headline(self, headline: Dict) -> Optional[Dict]:
        """
        Process a single headline through the full cascade pipeline.
        """
        try:
            draft = transform_headline_to_draft(headline["headline"], headline["city"])
            draft = reframe_title_as_question(draft)
            draft = refine_question_with_scope(draft)
            draft = patch_bias_and_vagueness(draft)
            draft = filter_contract_quality(draft)

            if draft.get("status") == "rejected":
                logger.info(f"Headline rejected: {headline['headline']}")
                return None

            draft = weigh_contract_predictive_value(draft)
            draft = balance_for_odds_and_xp(draft)
            draft = publish_contract(draft)

            logger.info(f"Successfully processed headline: {headline['headline']}")
            return draft

        except Exception as e:
            logger.error(f"Error processing headline {headline['headline']}: {str(e)}")
            return None

    def ingest_headlines(self, city_name: str) -> int:
        """
        Main method to fetch and process headlines for a city.
        Returns number of successfully processed headlines.
        """
        try:
            headlines = self.fetch_headlines(city_name)
            processed_count = 0

            for headline in headlines:
                result = self.process_headline(headline)
                if result:
                    processed_count += 1

            logger.info(f"Processed {processed_count} of {len(headlines)} headlines for {city_name}")
            return processed_count

        except Exception as e:
            logger.error(f"Error in headline ingestion for {city_name}: {str(e)}")
            raise

    def run_scheduled_ingest(self):
        """
        Run scheduled ingestion for all configured cities.
        """
        # Find all city config files
        config_files = list(self.config_dir.glob("*.json"))
        cities = [f.stem.replace("_config", "") for f in config_files]

        total_processed = 0
        for city in cities:
            processed = self.ingest_headlines(city)
            total_processed += processed

        logger.info(f"Total processed headlines across all cities: {total_processed}")
        return total_processed
