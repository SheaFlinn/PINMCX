import sys
import os
import requests
from bs4 import BeautifulSoup
from app import create_app
from app.models import NewsSource

# Ensure app root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create and activate Flask app context
app = create_app()

with app.app_context():
    source = NewsSource.query.filter_by(name="Daily Memphian").first()
    if not source:
        print("❌ Daily Memphian source not found in database.")
        sys.exit(1)

    print(f"\n🧪 Testing content extraction for: {source.name}")
    print(f"🌐 URL: {source.url}")
    print(f"🔍 Selector: {source.selector}")

    try:
        response = requests.get(source.url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        headlines = soup.select(source.selector)
        print(f"\n✅ Found {len(headlines)} headlines using selector: {source.selector}\n")

        for i, headline in enumerate(headlines[:5]):
            title = headline.get_text(strip=True)

            link = headline.find('a')
            article_url = link['href'] if link and link.has_attr('href') else "No link found"

            section = headline.find_previous('a', class_='ArticlePreview__sectionTag')
            section_text = section.get_text(strip=True) if section else "No section found"

            byline = headline.find_next('address', class_='Byline')
            author = byline.find('a').get_text(strip=True) if byline and byline.find('a') else "No author"
            date = byline.find('span', class_='Byline__updated').get_text(strip=True) if byline else "No date"

            print(f"📰 Headline {i + 1}: {title}")
            print(f"🔗 URL: {article_url}")
            print(f"🏷️ Section: {section_text}")
            print(f"✍️ Author: {author}")
            print(f"📆 Date: {date}\n")

    except Exception as e:
        print(f"❌ Error during content extraction: {e}")
