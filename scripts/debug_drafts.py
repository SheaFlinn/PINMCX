import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import NewsHeadline, NewsSource, Market
from flask import current_app

# Create Flask app context
app = create_app()

with app.app_context():
    # Check all active news sources
    print("\n=== Active News Sources ===")
    sources = NewsSource.query.filter_by(active=True).all()
    for source in sources:
        print(f"\nSource: {source.name}")
        print(f"URL: {source.url}")
        print(f"Selector: {source.selector}")
        print(f"Domain Tag: {source.domain_tag}")
        
        # Get recent headlines for this source
        headlines = NewsHeadline.query.filter_by(source_id=source.id).order_by(NewsHeadline.date_added.desc()).limit(5).all()
        print(f"\nRecent Headlines ({len(headlines)} total):")
        for headline in headlines:
            print(f"- Title: {headline.title}")
            print(f"  URL: {headline.url}")
            print(f"  Domain Tag: {headline.domain_tag}")
            print(f"  Date Added: {headline.date_added}")
            print(f"  Date Published: {headline.date_published}")
            print()

    # Check if any headlines are being used in markets
    print("\n=== Markets with Headlines ===")
    markets = Market.query.filter(Market.original_headline.isnot(None)).all()
    print(f"Found {len(markets)} markets with headlines")
    for market in markets:
        print(f"\nMarket: {market.title}")
        print(f"Original Headline: {market.original_headline}")
        print(f"Original Source: {market.original_source}")
        print(f"Domain: {market.domain}")
        print(f"Resolution Date: {market.resolution_date}")
