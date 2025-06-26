import sys
import os
# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import NewsSource, NewsHeadline
from app.extensions import db
from bs4 import BeautifulSoup
import requests
from datetime import datetime

def scrape_and_save_headlines():
    app = create_app()
    with app.app_context():
        # Get all active news sources
        sources = NewsSource.query.filter_by(active=True).all()
        
        print("\nTesting scraper integration with database:")
        for source in sources:
            print(f"\nScraping {source.name}")
            print(f"URL: {source.url}")
            print(f"Selector: {source.selector}")
            
            try:
                # Fetch the page
                response = requests.get(source.url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find headlines
                headlines = soup.select(source.selector)
                print(f"Found {len(headlines)} headlines")
                
                # Try to save 5 headlines to database
                print("\nSaving headlines to database:")
                for i, headline in enumerate(headlines[:5]):
                    title = headline.get_text(strip=True)
                    
                    # Get article URL
                    link = headline.find('a')
                    if link:
                        article_url = link['href']
                    else:
                        article_url = None
                    
                    # Create new headline
                    new_headline = NewsHeadline(
                        title=title,
                        url=article_url,
                        source_id=source.id,
                        date_added=datetime.now()
                    )
                    
                    try:
                        # Add to session
                        db.session.add(new_headline)
                        db.session.commit()
                        print(f"Successfully saved headline: {title}")
                    except Exception as e:
                        db.session.rollback()
                        print(f"Error saving headline: {e}")
                
                # Verify headlines were saved
                db_headlines = NewsHeadline.query.filter_by(source_id=source.id).all()
                print(f"\nTotal headlines in database for {source.name}: {len(db_headlines)}")
                
            except Exception as e:
                print(f"Error scraping {source.name}: {e}")

if __name__ == "__main__":
    scrape_and_save_headlines()
