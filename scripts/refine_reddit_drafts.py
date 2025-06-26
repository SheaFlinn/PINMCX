import json
import os
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RedditDraftRefiner:
    def __init__(self):
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

    def load_reddit_drafts(self):
        """Load Reddit drafts from JSON file"""
        drafts_dir = Path(__file__).parent.parent / 'drafts'
        drafts_path = drafts_dir / 'reddit_drafts.json'
        
        try:
            with open(drafts_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Drafts file not found: {drafts_path}")
            return []

    def save_refined_drafts(self, refined_drafts):
        """Save refined drafts to JSON file"""
        drafts_dir = Path(__file__).parent.parent / 'drafts'
        output_path = drafts_dir / 'refined_reddit_drafts.json'
        
        try:
            with open(output_path, 'w') as f:
                json.dump(refined_drafts, f, indent=2)
            logging.info(f"Saved {len(refined_drafts)} refined Reddit drafts to {output_path}")
        except Exception as e:
            logging.error(f"Error saving refined drafts: {e}")
            raise

    def is_valid_headline(self, headline):
        """Check if headline meets filtering criteria"""
        # Check minimum length
        if len(headline.split()) < self.MIN_HEADLINE_LENGTH:
            return False, "Headline too short"
            
        # Check for non-actionable phrases
        for phrase in self.NON_ACTIONABLE_PHRASES:
            if headline.lower().startswith(phrase.lower()):
                return False, f"Non-actionable phrase: {phrase}"
                
        return True, None

    def refine_headline(self, headline):
        """Refine headline into a prediction question format"""
        # Try to find a relevant neutral phrase
        for phrase in self.neutral_phrases:
            if any(keyword in headline.lower() for category in self.relevance_keywords.values() 
                  for keyword in category):
                return f"{phrase} {headline}?"
        
        # If no neutral phrase matches, use default
        return f"Is it likely that {headline}?"

    def calculate_relevance_score(self, headline):
        """Calculate relevance score based on keywords"""
        score = 0
        total_weight = 0
        
        # Check each category
        for category, keywords in self.relevance_keywords.items():
            weight = self.relevance_weights[category]
            
            for keyword in keywords:
                if keyword.lower() in headline.lower():
                    score += weight
                    total_weight += weight
                    break
                    
        return score / total_weight if total_weight > 0 else 0

    def refine_reddit_drafts(self):
        """Process and refine Reddit drafts"""
        drafts = self.load_reddit_drafts()
        refined_drafts = []
        
        for draft in drafts:
            headline = draft['headline']
            
            # Check validity
            is_valid, reason = self.is_valid_headline(headline)
            if not is_valid:
                draft['exclusion_reason'] = reason
                continue
                
            # Refine headline
            refined_title = self.refine_headline(headline)
            
            # Calculate relevance score
            relevance_score = self.calculate_relevance_score(headline)
            
            # Create refined draft
            refined_draft = {
                'original_headline': headline,
                'source': draft['source'],
                'link': draft['link'],
                'created_at': draft['created_at'],
                'refined_title': refined_title,
                'relevance_score': relevance_score,
                'domain': self.determine_domain(headline)  # Add domain detection
            }
            
            refined_drafts.append(refined_draft)
            
        # Sort by relevance score
        refined_drafts.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        self.save_refined_drafts(refined_drafts)
        return refined_drafts

    def determine_domain(self, headline):
        """Determine the most relevant domain for the headline"""
        max_score = 0
        best_domain = None
        
        for domain, keywords in self.relevance_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in headline.lower())
            if score > max_score:
                max_score = score
                best_domain = domain
                
        return best_domain or 'other'

if __name__ == '__main__':
    refiner = RedditDraftRefiner()
    refined_drafts = refiner.refine_reddit_drafts()
    logging.info(f"Successfully processed {len(refined_drafts)} Reddit drafts")
