import os
import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_scraper_config(city_name):
    """
    Load a city-specific scraper configuration from JSON file.
    
    Args:
        city_name (str): Name of the city (case-insensitive)
        
    Returns:
        dict: Parsed JSON configuration
        
    Raises:
        ValueError: If the config file does not exist or contains invalid JSON
    """
    # Convert to lowercase and build path
    config_dir = Path("scraper_configs")
    config_file = config_dir / f"{city_name.lower()}.json"
    
    # Create directory if it doesn't exist
    config_dir.mkdir(exist_ok=True)
    
    # Check if file exists
    if not config_file.exists():
        raise ValueError(f"No config found for city: {city_name}")
    
    # Load and return config
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
            logger.info(f"Successfully loaded config for {city_name}")
            return config
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON for {city_name}: {e}")
        raise ValueError(f"Invalid JSON in config file for {city_name}")
    except Exception as e:
        logger.error(f"Unexpected error loading config for {city_name}: {e}")
        raise
