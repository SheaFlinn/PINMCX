import logging
from datetime import datetime
from city_scraper import scrape_city_headlines
import json
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_scraper():
    """Test the scraper functionality and validate output."""
    cities = ['memphis', 'nashville', 'dallas']
    
    # Test each city
    for city in cities:
        logger.info(f"Testing scraper for {city}")
        try:
            # Run scraper
            headlines = scrape_city_headlines(city)
            
            # Validate output structure
            if not isinstance(headlines, list):
                raise ValueError(f"Expected list of headlines, got {type(headlines)}")
                
            # Save to file with timestamp
            timestamp = datetime.now().strftime('%Y-%m-%dT%H')
            filename = f'scraper_output/{city}_{timestamp}.json'
            
            # Create output directory if it doesn't exist
            os.makedirs('scraper_output', exist_ok=True)
            
            # Save with proper structure
            output = {
                'city': city,
                'scrape_time': datetime.now().isoformat(),
                'headlines': headlines
            }
            
            with open(filename, 'w') as f:
                json.dump(output, f, indent=2)
                logger.info(f"Saved {len(headlines)} headlines for {city} to {filename}")
                
            # Validate file contents
            with open(filename, 'r') as f:
                data = json.load(f)
                assert 'city' in data, "Missing 'city' field in output"
                assert 'scrape_time' in data, "Missing 'scrape_time' field in output"
                assert isinstance(data['headlines'], list), "headlines should be a list"
                
                # Check at least one headline has required fields
                if data['headlines']:
                    sample_headline = data['headlines'][0]
                    assert 'title' in sample_headline or 'headline' in sample_headline, "Headline missing title/headline field"
                    assert 'link' in sample_headline or 'url' in sample_headline, "Headline missing link/url field"
                    
            logger.info(f"Successfully validated output structure for {city}")
            
        except Exception as e:
            logger.error(f"Error testing {city}: {str(e)}")
            raise

if __name__ == "__main__":
    test_scraper()
