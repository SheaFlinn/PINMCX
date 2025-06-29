import sys
import os
import pytest
# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import NewsSource
from bs4 import BeautifulSoup
import requests

# Create Flask app context
app = create_app()

with app.app_context():
    # Get the Daily Memphian source
    source = NewsSource.query.filter_by(name="Daily Memphian").first()
    if not source:
        pytest.skip("Daily Memphian source not found in database", allow_module_level=True)
    
    print(f"\nTesting content extraction for Daily Memphian")
    print(f"URL: {source.url}")
    print(f"Selector: {source.selector}")
    
    try:
        # Fetch the page
        response = requests.get(source.url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find headlines
        headlines = soup.select(source.selector)
        print(f"\nFound {len(headlines)} headlines with selector: {source.selector}")
        
        # Test content extraction for first 5 headlines
        print("\nTesting content extraction for first 5 headlines:")
        for i, headline in enumerate(headlines[:5]):
            # Get headline text
            title = headline.get_text().strip()
            
            # Get article link
            link = headline.find('a')
            if link:
                article_url = link['href']
            else:
                article_url = "No link found"
            
            # Get section tag
            section = headline.find_previous('a', class_='ArticlePreview__sectionTag')
            section_text = section.get_text().strip() if section else "No section found"
            
            # Get author and date
            byline = headline.find_next('address', class_='Byline')
            author = byline.find('a').get_text().strip() if byline and byline.find('a') else "No author"
            date = byline.find('span', class_='Byline__updated').get_text().strip() if byline else "No date"
            
            print(f"\nHeadline {i+1}:")
            print(f"Title: {title}")
            print(f"URL: {article_url}")
            print(f"Section: {section_text}")
            print(f"Author: {author}")
            print(f"Date: {date}")
            
    except Exception as e:
        print(f"Error testing content extraction: {e}")
