import requests
import logging
import json
from bs4 import BeautifulSoup
import yaml
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("city_scraper")

def scrape_city_headlines(city: str):
    """
    Scrape headlines from city-specific news sources using YAML configuration.
    
    Args:
        city (str): Name of the city to scrape headlines for
        
    Returns:
        list: List of dictionaries containing headline titles and links
        
    Raises:
        FileNotFoundError: If city configuration file is not found
        ValueError: If selectors return no elements
    """
    try:
        # Load city-specific configuration
        # Try JSON first, then YAML
        config_path_json = Path(f"scraper_configs/{city.lower()}_config.json")
        config_path_yaml = Path(f"scraper_configs/{city.lower()}.yaml")
        
        if config_path_json.exists():
            config_path = config_path_json
            with open(config_path, "r") as f:
                config = json.load(f)
        elif config_path_yaml.exists():
            config_path = config_path_yaml
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"Missing config file for city: {city}. Tried {config_path_json} and {config_path_yaml}")

        sources = config.get("sources", [])
        headlines = []

        for source in sources:
            try:
                logger.info(f"Scraping source: {source['name']}")
                url = source["url"]
                
                # Handle both selector formats
                selectors = source.get("selectors", {})
                headline_selector = selectors.get("headline", source.get("headline", ""))
                link_selector = selectors.get("link", source.get("link", ""))
                
                # Set up headers with user-agent
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15"
                }
                
                logger.debug(f"Fetching URL: {url}")
                response = requests.get(url, headers=headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                headline_elems = soup.select(headline_selector)
                link_elems = soup.select(link_selector)

                # Log selector failures
                if not headline_elems:
                    logger.error(f"Error extracting headlines from {source['name']}: No headline elements found")
                    continue
                
                if not link_elems:
                    logger.error(f"Error extracting headlines from {source['name']}: No link elements found")
                    continue

                logger.info(f"Found {len(headline_elems)} headlines from {source['name']}")

                # Process headlines and links
                for h, l in zip(headline_elems, link_elems):
                    headline = {
                        "title": h.get_text(strip=True),
                        "link": l["href"]
                    }
                    headlines.append(headline)

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching URL {url}: {e}")
                continue
            except KeyError as e:
                logger.error(f"Missing required key in source config: {e} in source: {source['name']}")
                continue
            except Exception as e:
                logger.error(f"Error extracting headlines from {source['name']}: {e}")
                continue

        return headlines

    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML config: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in scrape_city_headlines: {e}")
        raise
