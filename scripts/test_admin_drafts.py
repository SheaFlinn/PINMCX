import sys
import os
# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import NewsSource, NewsHeadline
from bs4 import BeautifulSoup
import requests

# Create Flask app context
app = create_app()

def test_headline_extraction():
    with app.app_context():
        # Get all active news sources
        sources = NewsSource.query.filter_by(active=True).all()
        
        print("\nTesting headline extraction for all active sources:")
        for source in sources:
            print(f"\nTesting {source.name}")
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
                
                # Print first 5 headlines
                print("First 5 headlines:")
                for i, headline in enumerate(headlines[:5]):
                    title = headline.get_text(strip=True)
                    print(f"{i+1}. {title}")
                    
                    # Check if we can find the article URL
                    link = headline.find('a')
                    if link:
                        article_url = link['href']
                        print(f"   URL: {article_url}")
                    
                # Check if these headlines exist in the database
                db_headlines = NewsHeadline.query.filter_by(source_id=source.id).all()
                print(f"\nNumber of headlines in database: {len(db_headlines)}")
                
            except Exception as e:
                print(f"Error testing {source.name}: {e}")

if __name__ == "__main__":
    test_headline_extraction()
