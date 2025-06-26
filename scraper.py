import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import dateutil.parser
from app import create_app, db
from app.models import Market, NewsSource
import json
import os
import contextlib
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create application context
@contextlib.contextmanager
def create_app_context():
    app = create_app()
    with app.app_context():
        yield app

# Use context manager to ensure app context is active
def get_active_sources():
    with create_app_context() as app:
        sources = []
        logging.info("Fetching active news sources from the database...")
        db_sources = NewsSource.query.filter_by(active=True).all()
        logging.info(f"Found {len(db_sources)} active source(s).")
        for source in db_sources:
            logging.info(f"  -> Processing source: {source.name} (URL: {source.url})")
            sources.append({
                'name': source.name,
                'url': source.url,
                'selector': source.selector,
                'date_selector': source.date_selector
            })
        return sources

class NewsScraper:
    def __init__(self):
        # Get active sources from the database
        logging.info("Initializing NewsScraper...")
        self.sources = self.get_active_sources()
        logging.info(f"NewsScraper initialized with {len(self.sources)} source(s).")
        
        # Initialize filtering rules
        self.MIN_HEADLINE_LENGTH = 7
        self.NON_ACTIONABLE_PHRASES = [
            "His name was", "Her name was", "Their name was",
            "Books to help", "Why [org] is volunteering",
            "In memory of", "Remembering", "Obituary",
            "Historical", "Past event", "Recap",
            "Review of", "Summary of"
        ]
        
        # Initialize language processing tools
        self.neutral_phrases = [
            "Will there be a significant change in",
            "Is it likely that",
            "Will there be a notable impact on",
            "Will we see a meaningful shift in",
            "Is it probable that"
        ]
        self.balance_factors = {
            'default': {
                'bias_threshold': 0.5,
                'phrase_weight': 0.7,
                'context_weight': 0.3
            }
        }
        
        # Initialize relevance keywords and weights
        self.relevance_keywords = {
            'civic': ['zoning', 'permit', 'development', 'real estate', 'infrastructure', 
                     'housing', 'tax', 'budget', 'bond', 'city council', 'mayor', 'business',
                     'city', 'municipal', 'local government', 'ordinance', 'public works',
                     'transportation', 'utilities', 'planning', 'commission', 'board',
                     'election', 'campaign', 'voter', 'referendum', 'proposal'],
            
            'infrastructure': ['road', 'bridge', 'transit', 'water', 'sewer', 'electricity',
                             'utilities', 'public works', 'construction', 'maintenance',
                             'repair', 'improvement', 'expansion'],
            
            'finance': ['budget', 'tax', 'bond', 'funding', 'appropriation', 'spending',
                      'revenue', 'expense', 'audit', 'finance', 'economic', 'development'],
            
            'housing': ['affordable', 'homelessness', 'rent', 'eviction', 'housing',
                      'development', 'zoning', 'permit', 'construction', 'building'],
            
            'governance': ['city council', 'mayor', 'commissioner', 'board', 'election',
                         'campaign', 'referendum', 'ordinance', 'policy', 'regulation']
        }
        
        self.relevance_weights = {
            'civic': 1.0,
            'infrastructure': 0.8,
            'finance': 0.8,
            'housing': 0.7,
            'governance': 0.9
        }
        
        # Initialize draft contracts list
        self.draft_contracts = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        })

    def calculate_balance_score(self, question):
        """Calculate how balanced a question is (0-1, where 0.5 is perfectly balanced)"""
        # Simple heuristic: count positive vs negative words
        positive_words = ['will', 'likely', 'expected', 'planned']
        negative_words = ['might', 'may', 'could', 'potential']
        
        words = question.lower().split()
        pos_count = sum(1 for word in words if word in positive_words)
        neg_count = sum(1 for word in words if word in negative_words)
        
        if pos_count + neg_count == 0:
            return 0.5  # Perfectly balanced if no bias words
            
        return abs(pos_count - neg_count) / (pos_count + neg_count)

    def extract_market_title(self, headline, source_config=None):
        """Convert news headline into a market prediction format with balanced odds"""
        # Clean and format the headline
        headline = headline.strip()
        
        # Apply source-specific configuration if available
        config = source_config if source_config else self.balance_factors['default']
        
        # Remove common phrases and bias-inducing words
        bias_words = ['will', 'could', 'may', 'might']
        for word in bias_words:
            headline = headline.replace(word + ' ', '')
        
        # Try different neutral phrase patterns
        best_question = None
        best_balance = 0.5  # Start with perfectly balanced
        
        for phrase in self.neutral_phrases:
            if phrase in headline:
                question = headline
            else:
                # Try to construct a balanced question
                question = f"{phrase} {headline}?"
            
            # Calculate balance score
            balance = self.calculate_balance_score(question)
            
            # Keep if it's more balanced than previous attempts
            if abs(balance - 0.5) < abs(best_balance - 0.5):
                best_question = question
                best_balance = balance
        
        # If no good balanced question found, use a default pattern
        if not best_question:
            best_question = f"Is it likely that {headline} will occur?"
            
        # Add additional balancing if needed
        if abs(best_balance - 0.5) > config['bias_threshold']:
            # Add neutralizing phrases
            if best_balance > 0.5:  # Too positive
                best_question = f"{best_question} despite potential challenges?"
            else:  # Too negative
                best_question = f"{best_question} given favorable conditions?"
        
        return best_question

    def create_draft_contract(self, headline, source, article_date):
        """Create a draft contract from a news headline and add it to the list"""
        # Create a market title from the headline
        market_title = self.extract_market_title(headline, source.get('config'))
        
        # Create draft contract dictionary
        draft = {
            'title': market_title,
            'description': f"Created from {source['name']} news article",
            'resolution_date': (article_date + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S'),  # Convert to string
            'source_name': source['name'],
            'source_url': source['url'],
            'original_headline': headline,
            'refined_title': market_title,  # Start with original as refined version
            'refined_description': f"Created from {source['name']} news article",
            'source_date': article_date.strftime('%Y-%m-%dT%H:%M:%S'),  # Convert to string
            'created_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),  # Convert to string
            'original_source': source['name'],
            'original_date': article_date.strftime('%Y-%m-%d %H:%M:%S'),  # Already in string format
            'domain_tags': self.get_domain_tags(headline),  # Add domain tagging
            'relevance_score': self.calculate_relevance(headline),
            'scraped_at': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),  # Convert to string
            'source_url': source['url']  # Store source URL for provenance
        }
        
        self.draft_contracts.append(draft)
        return draft

    def get_active_sources(self):
        """Get active sources with their configurations"""
        with create_app_context() as app:
            sources = []
            logging.info("Fetching active news sources from the database...")
            db_sources = NewsSource.query.filter_by(active=True).all()
            logging.info(f"Found {len(db_sources)} active source(s).")
            for source in db_sources:
                logging.info(f"  -> Processing source: {source.name} (URL: {source.url})")
                # Add source-specific configurations
                source_config = {
                    'config': {
                        'bias_threshold': getattr(source, 'bias_threshold', 0.5),
                        'phrase_weight': getattr(source, 'phrase_weight', 0.7),
                        'context_weight': getattr(source, 'context_weight', 0.3)
                    }
                }
                sources.append({
                    'name': source.name,
                    'url': source.url,
                    'selector': source.selector,
                    'date_selector': source.date_selector,
                    **source_config
                })
            return sources

    def is_relevant(self, headline_text):
        """Check if a headline is relevant for civic contract generation"""
        headline_text = headline_text.lower()
        relevance_score = 0
        
        # Check for relevance keywords and calculate score
        for category, keywords in self.relevance_keywords.items():
            weight = self.relevance_weights[category]
            for keyword in keywords:
                if keyword in headline_text:
                    relevance_score += weight
                    break  # Only count one keyword per category
        
        # Normalize score (0-1)
        max_possible_score = sum(self.relevance_weights.values())
        normalized_score = relevance_score / max_possible_score if max_possible_score > 0 else 0
        
        logging.debug(f"Relevance score for '{headline_text}': {normalized_score:.2f}")
        
        # Return True if score meets threshold
        return normalized_score >= 0.3  # Adjust threshold as needed

    def get_domain_tags(self, headline):
        """Extract domain tags from headline using keywords"""
        domain_keywords = {
            'infrastructure': ['road', 'bridge', 'construction', 'public works'],
            'crime': ['crime', 'police', 'arrest', 'theft', 'robbery'],
            'housing': ['housing', 'rent', 'home', 'property', 'eviction'],
            'governance': ['city council', 'mayor', 'election', 'policy', 'ordinance'],
            'finance': ['budget', 'tax', 'funding', 'spending', 'revenue']
        }
        
        tags = []
        for domain, keywords in domain_keywords.items():
            if any(keyword.lower() in headline.lower() for keyword in keywords):
                tags.append(domain)
        
        return tags

    def calculate_relevance(self, headline):
        """Calculate relevance score for a headline"""
        headline = headline.lower()
        relevance_score = 0
        
        # Check for relevance keywords and calculate score
        for category, keywords in self.relevance_keywords.items():
            weight = self.relevance_weights[category]
            for keyword in keywords:
                if keyword in headline:
                    relevance_score += weight
                    break  # Only count one keyword per category
        
        # Normalize score (0-1)
        max_possible_score = sum(self.relevance_weights.values())
        normalized_score = relevance_score / max_possible_score if max_possible_score > 0 else 0
        
        return normalized_score

    def is_valid_headline(self, headline):
        """
        Validate if a headline is suitable for contract generation.
        Returns True if valid, False otherwise.
        """
        # Check minimum length
        if len(headline.split()) < self.MIN_HEADLINE_LENGTH:
            logging.info(f"Excluded headline (too short): {headline}")
            return False

        # Check for non-actionable phrases
        for phrase in self.NON_ACTIONABLE_PHRASES:
            if phrase.lower() in headline.lower():
                logging.info(f"Excluded headline (non-actionable phrase): {headline}")
                return False

        # Check for future action
        if not self.has_future_action(headline):
            logging.info(f"Excluded headline (no future action): {headline}")
            return False

        return True

    def has_future_action(self, headline):
        """
        Check if headline contains a clear future action verb.
        Returns True if it does, False otherwise.
        """
        # List of future action indicators
        future_indicators = [
            "will", "plans to", "aims to", "set to", "scheduled to",
            "expected to", "likely to", "may", "might", "could"
        ]

        # Check if headline contains any future action indicators
        words = headline.lower().split()
        for indicator in future_indicators:
            if indicator in words:
                return True

        # Check for future tense verbs
        future_tense_verbs = [
            "will", "shall", "going to", "about to"
        ]
        for verb in future_tense_verbs:
            if verb in words:
                return True

        return False

    def process_headline(self, headline, source):
        """
        Process a headline from a news source.
        Returns None if headline is invalid, otherwise returns processed headline.
        """
        try:
            if not self.is_valid_headline(headline):
                return None

            # Clean and normalize headline
            cleaned_headline = headline.strip()
            cleaned_headline = cleaned_headline.replace('\n', ' ').replace('\t', ' ')
            cleaned_headline = ' '.join(cleaned_headline.split())

            return {
                'original_headline': cleaned_headline,
                'source': source,
                'exclusion_reason': None  # Only set if excluded
            }
        except Exception as e:
            logging.error(f"Error processing headline: {e}")
            return None

    def scrape_source(self, source):
        """
        Scrape headlines from a single news source.
        """
        try:
            response = self.session.get(source['url'])
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find headlines using configured selector
            headlines = soup.select(source['selector'])
            logging.info(f"Found {len(headlines)} headlines from {source['name']}")
            
            processed_headlines = []
            for headline in headlines:
                text = headline.get_text().strip()
                if processed := self.process_headline(text, source['name']):
                    processed_headlines.append(processed)
            
            return processed_headlines
            
        except Exception as e:
            logging.error(f"Error scraping {source['name']}: {e}")
            return []

    def scrape_sources(self):
        """Scrape all active news sources and generate draft contracts"""
        for source in self.sources:
            try:
                # Fetch the page
                response = self.session.get(source['url'], timeout=15)
                response.raise_for_status()

                # Check if the source is an RSS feed
                if source['selector'] and source['selector'].upper() == 'RSS':
                    # --- RSS Parsing Logic ---
                    soup = BeautifulSoup(response.content, 'xml')
                    items = soup.find_all('item')
                    if not items:
                        logging.warning(f"    -> No items found in RSS feed for {source['name']}.")
                        continue
                    
                    logging.info(f"  -> Found {len(items)} items in RSS feed for {source['name']}.")
                    relevant_items = 0
                    
                    for item in items:
                        title_tag = item.find('title')
                        pub_date_tag = item.find('pubDate')

                        if not title_tag:
                            continue
                            
                        headline = title_tag.text
                        
                        # Skip if not relevant
                        if not self.is_relevant(headline):
                            logging.debug(f"    -> Skipping non-relevant headline: {headline}")
                            continue
                            
                        relevant_items += 1
                        
                        # Parse date
                        pub_date = self.parse_date(pub_date_tag.text if pub_date_tag else datetime.now())
                        
                        # Create draft contract
                        self.create_draft_contract(headline, source, pub_date)
                    
                    logging.info(f"  -> Processed {relevant_items} relevant items out of {len(items)} for {source['name']}")
                
                else:
                    # --- Original HTML Parsing Logic ---
                    soup = BeautifulSoup(response.content, 'html.parser')
                    headline_elements = soup.select(source['selector'])

                    if not headline_elements:
                        logging.warning(f"    -> No headlines found for {source['name']}. The CSS selector \"{source['selector']}\" may be incorrect or the page structure has changed.")
                        continue
                    
                    logging.info(f"  -> Found {len(headline_elements)} headlines from {source['name']}.")

                    # Get a single article date for all headlines from this source
                    date_elem = soup.select_one(source['date_selector']) if source['date_selector'] else None
                    article_date = self.parse_date(date_elem.get_text(strip=True)) if date_elem else datetime.now()
                    if not date_elem and source['date_selector']:
                        logging.warning(f"    -> No date found for {source['name']} using selector \"{source['date_selector']}\". Using current time.")

                    relevant_headlines = 0
                    
                    for el in headline_elements:
                        headline_text = el.get_text(strip=True)
                        if not headline_text:
                            continue
                            
                        # Skip if not relevant
                        if not self.is_relevant(headline_text):
                            logging.debug(f"    -> Skipping non-relevant headline: {headline_text}")
                            continue
                            
                        relevant_headlines += 1
                        
                        # Create draft contract
                        self.create_draft_contract(headline_text, source, article_date)
                    
                    logging.info(f"  -> Processed {relevant_headlines} relevant headlines out of {len(headline_elements)} for {source['name']}")

            except requests.exceptions.HTTPError as e:
                logging.error(f"HTTP error scraping {source['name']}: {e}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Error scraping {source['name']}: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred for {source['name']}: {e}")

    def parse_date(self, date_str):
        """Parse date string from news article"""
        try:
            return dateutil.parser.parse(date_str)
        except:
            return datetime.now()

    def save_drafts(self):
        """Save draft contracts to JSON file"""
        try:
            # Sort drafts by relevance score (highest first)
            self.draft_contracts.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Save to JSON file
            os.makedirs('drafts', exist_ok=True)
            with open('drafts/draft_contracts.json', 'w', encoding='utf-8') as f:
                json.dump(self.draft_contracts, f, indent=4, cls=DateTimeEncoder)
            
            logging.info(f"Saved {len(self.draft_contracts)} draft contracts to drafts/draft_contracts.json")
            
        except Exception as e:
            logging.error(f"Error saving draft contracts: {str(e)}")
            raise

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Example usage
if __name__ == '__main__':
    scraper = NewsScraper()
    scraper.scrape_sources()
    scraper.save_drafts()
