import praw
import json
import os
import logging
from datetime import datetime, timedelta
import contextlib
from dotenv import load_dotenv
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Reddit API configuration
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USERNAME = os.getenv('REDDIT_USERNAME', 'PINMCX')
REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD', 'upgradecivics')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'MCX Reddit Scraper by u/PINMCX')

# Configuration
SUBREDDITS = ['memphis', 'tennessee', 'memphispolitics']
MIN_SCORE = 10  # Minimum score for a post to be considered
POST_LIMIT = 10  # Number of posts to fetch per subreddit

@contextlib.contextmanager
def reddit_context():
    """Create a context manager for Reddit API connection"""
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD,
            user_agent=REDDIT_USER_AGENT
        )
        yield reddit
    except Exception as e:
        logging.error(f"Failed to create Reddit API connection: {e}")
        raise

class RedditScraper:
    def __init__(self):
        self.draft_contracts = []
        self.reddit = None

    def is_valid_post(self, post):
        """Check if a post meets our criteria"""
        # Check score threshold
        if post.score < MIN_SCORE:
            return False
            
        # Check for media content
        if post.is_gallery or post.is_video:
            return False
            
        # Check URL for image extensions
        if post.url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            return False
            
        # Check title length
        if len(post.title.split()) < 7:
            return False
            
        return True

    def create_reddit_draft(self, post):
        """Create a draft contract from a Reddit post"""
        draft = {
            'headline': post.title,
            'source': f"r/{post.subreddit.display_name}",
            'link': f"https://reddit.com{post.permalink}",
            'created_at': datetime.fromtimestamp(post.created_utc).isoformat(),
        }
        self.draft_contracts.append(draft)
        return draft

    def scrape_subreddit(self, subreddit_name):
        """Scrape posts from a specific subreddit"""
        try:
            with reddit_context() as reddit:
                subreddit = reddit.subreddit(subreddit_name)
                # Use .top() instead of .hot() for better quality posts
                posts = subreddit.top(time_filter='day', limit=POST_LIMIT)
                
                relevant_posts = 0
                for post in posts:
                    if self.is_valid_post(post):
                        draft = self.create_reddit_draft(post)
                        relevant_posts += 1
                        logging.info(f"Added post '{post.title}' from r/{subreddit_name} with score {post.score}")
                
                logging.info(f"Processed {relevant_posts} relevant posts out of {POST_LIMIT} from r/{subreddit_name}")
                
        except Exception as e:
            logging.error(f"Error scraping r/{subreddit_name}: {e}")
            raise

    def save_drafts(self):
        """Save Reddit drafts to JSON file"""
        try:
            # Create drafts directory if it doesn't exist
            drafts_dir = Path(__file__).parent / 'drafts'
            drafts_dir.mkdir(exist_ok=True)
            
            # Save drafts to JSON file
            json_path = drafts_dir / 'reddit_drafts.json'
            with open(json_path, 'w') as f:
                json.dump(self.draft_contracts, f, indent=2)
            
            logging.info(f"Successfully saved {len(self.draft_contracts)} Reddit draft contracts to {json_path}")
            
            # Print summary if running directly
            if __name__ == '__main__':
                print(f"\nSaved {len(self.draft_contracts)} drafts:")
                for draft in self.draft_contracts:
                    print(f"- {draft['headline']}")
            
        except Exception as e:
            logging.error(f"Error saving Reddit drafts: {e}")
            raise

    def run_scraper(self):
        """Run the complete scraping process"""
        logging.info("Starting Reddit scraper...")
        
        for subreddit in SUBREDDITS:
            logging.info(f"Scraping r/{subreddit}...")
            self.scrape_subreddit(subreddit)
            
        self.save_drafts()
        logging.info("Reddit scraping completed")

if __name__ == '__main__':
    scraper = RedditScraper()
    scraper.run_scraper()
