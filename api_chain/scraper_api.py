import os
import praw
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_reddit_instance() -> Optional[praw.Reddit]:
    """Create Reddit instance with error handling."""
    try:
        return praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent='PIN Contract Generator'
        )
    except Exception as e:
        logger.error(f"Failed to create Reddit instance: {str(e)}")
        return None

def get_city_subreddit(city: str) -> str:
    """Map city names to subreddit names."""
    subreddit_map = {
        'memphis': 'memphis',
        'nashville': 'nashville',
        'knoxville': 'knoxville',
        'chattanooga': 'chattanooga'
    }
    return subreddit_map.get(city.lower(), 'memphis')

def fetch_reddit_headlines(reddit: praw.Reddit, subreddit: str, limit: int = 10) -> List[Dict]:
    """Fetch headlines from Reddit subreddit."""
    try:
        subreddit = reddit.subreddit(subreddit)
        posts = subreddit.new(limit=limit)
        
        return [{
            "title": post.title,
            "url": post.url,
            "created_utc": post.created_utc,
            "author": str(post.author) if post.author else "unknown"
        } for post in posts]
    except Exception as e:
        logger.error(f"Failed to fetch Reddit headlines: {str(e)}")
        return []

def get_mock_headlines(city: str) -> List[Dict]:
    """Return mock data for testing."""
    return [
        {
            "title": f"{city.title()} City Council discusses budget changes",
            "url": f"https://mock-data.com/{city.lower()}/budget",
            "created_utc": datetime.utcnow().timestamp(),
            "author": "mock_author"
        },
        {
            "title": f"New infrastructure project proposed in {city.title()}",
            "url": f"https://mock-data.com/{city.lower()}/infrastructure",
            "created_utc": datetime.utcnow().timestamp(),
            "author": "mock_author"
        }
    ]

def run_scraper(city: str) -> Dict:
    """
    Main API function that retrieves civic headlines for a given city.
    
    Args:
        city (str): Name of the city (case-insensitive)
        
    Returns:
        dict: Structured response with city, source, and headlines
    """
    try:
        # Get Reddit instance
        reddit = get_reddit_instance()
        if not reddit:
            logger.warning("Using mock data - Reddit instance not available")
            return {
                "city": city.lower(),
                "source": "mock",
                "headlines": get_mock_headlines(city)
            }

        # Get subreddit for city
        subreddit = get_city_subreddit(city)
        if not subreddit:
            logger.warning(f"No subreddit mapping found for city: {city}")
            return {
                "city": city.lower(),
                "source": "mock",
                "headlines": get_mock_headlines(city)
            }

        # Fetch headlines
        headlines = fetch_reddit_headlines(reddit, subreddit)
        if not headlines:
            logger.warning(f"No headlines found for subreddit: {subreddit}")
            return {
                "city": city.lower(),
                "source": "mock",
                "headlines": get_mock_headlines(city)
            }

        return {
            "city": city.lower(),
            "source": "reddit",
            "headlines": headlines
        }

    except Exception as e:
        logger.error(f"Error in run_scraper: {str(e)}")
        return {
            "city": city.lower(),
            "source": "error",
            "headlines": [],
            "error": str(e)
        }

if __name__ == "__main__":
    # Example usage
    result = run_scraper("Memphis")
    print(f"\nScraped headlines for {result['city']}:")
    for headline in result['headlines']:
        print(f"- {headline['title']}")
