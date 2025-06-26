import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
import requests

# Setup app import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from app.models import NewsSource

# Create Flask app context
app = create_app()

with app.app_context():
    source = NewsSource.query.filter_by(name="Daily Memphian").first()
    if not source:
        print("❌ Daily Memphian source not found in DB.")
        sys.exit(1)

    print(f"🧪 Testing content extraction for: {source.name}")
    print(f"→ URL: {source.url}")
    print(f"→ Selector: {source.selector}")

    try:
        response = requests.get(source.url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = soup.select(source.selector)

        print(f"✅ Found {len(headlines)} headlines using selector: {source.selector}\n")

        for i, headline in enumerate(headlines[:5]):
            title = headline.get_text().strip()

            link_tag = headline.find('a')
            article_url = link_tag['href'] if link_tag else "No link found"

            section_tag = headline.find_previous('a', class_='ArticlePreview__sectionTag')
            section_text = section_tag.get_text().strip() if section_tag else "No section found"

            byline = headline.find_next('address', class_='Byline')
            author = byline.find('a').get_text().strip() if byline and byline.find('a') else "No author"
            date = byline.find('span', class_='Byline__updated').get_text().strip() if byline else "No date"

            print(f"--- Headline {i+1} ---")
            print(f"Title: {title}")
            print(f"URL: {article_url}")
            print(f"Section: {section_text}")
            print(f"Author: {author}")
            print(f"Date: {date}\n")

    except Exception as e:
        print(f"❌ Error during content extraction: {str(e)}")
