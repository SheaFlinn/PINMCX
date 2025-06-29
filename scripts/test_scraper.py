import sys
import os
# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import NewsSource
from bs4 import BeautifulSoup
import requests

# Create Flask app context
app = create_app()

# Test a single source
SOURCE_NAME = "MLK50"

# Custom selectors for MLK50
SPECIFIC_SELECTORS = [
    "article h2",  # Main article headlines
    "article h3",  # Secondary headlines
    "h2.entry-title",  # Entry title class
    "h3.entry-title",  # Entry title class
    "a[href^='https://mlk50.com/']",  # Links to articles
    "div.post-content h2",  # Post content headings
    "div.post-content h3",  # Post content headings
    "div.post-content h4",  # Post content headings
]

def test_scraper():
    with app.app_context():
        source = NewsSource.query.filter_by(name=SOURCE_NAME).first()
        if not source:
            print(f"Source '{SOURCE_NAME}' not found in database")
            return

        print(f"\nTesting scraper for {SOURCE_NAME}")
        print(f"URL: {source.url}")
        print(f"Current selector: {source.selector}")
        print(f"Domain tag: {source.domain_tag}")

        try:
            response = requests.get(source.url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Test specific MLK50 selectors
            print("\nTesting MLK50 specific selectors:")
            for selector in SPECIFIC_SELECTORS:
                elements = soup.select(selector)
                if elements:
                    print(f"\nFound {len(elements)} elements with selector: {selector}")
                    print("First 5 headlines:")
                    for i, elem in enumerate(elements[:5]):
                        print(f"{i+1}. {elem.get_text(strip=True)}")
                else:
                    print(f"No elements found with selector: {selector}")

            # Print HTML structure around headlines
            print("\nHTML structure around headlines:")
            for selector in SPECIFIC_SELECTORS:
                if elements := soup.select(selector):
                    print(f"\nStructure for selector: {selector}")
                    for elem in elements[:2]:  # Show structure for first 2 elements
                        print("\nElement HTML:")
                        print(elem.prettify())
                        print("\nParent structure:")
                        print(elem.parent.prettify())

        except Exception as e:
            print(f"Error scraping {SOURCE_NAME}: {e}")

if __name__ == "__main__":
    test_scraper()
