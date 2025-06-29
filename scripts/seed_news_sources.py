import os
import sys
import logging

# Add the project root to PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Now we can import from the app package
from app import create_app
from app.models import NewsSource, NewsHeadline
from app.extensions import db

# Create Flask app context
app = create_app()

with app.app_context():
    # First check if we have any news sources
    sources = NewsSource.query.all()
    print(f"\n=== Current News Sources ===")
    for source in sources:
        print(f"\nID: {source.id}")
        print(f"Name: {source.name}")
        print(f"URL: {source.url}")
        print(f"Selector: {source.selector}")
        print(f"Active: {source.active}")
    print("\n=== End of Current Sources ===")

    # If no sources found, re-seed them
    if not sources:
        logging.info("No news sources found, re-seeding...")
        
        # Define our news sources
        news_sources = [
            {
                "name": "Daily Memphian",
                "url": "https://dailymemphian.com",
                "selector": "article h2",
                "domain_tag": "local",
                "source_weight": 1.0
            },
            {
                "name": "MLK50",
                "url": "https://mlk50.com",
                "selector": "article h2",
                "domain_tag": "local",
                "source_weight": 1.0
            },
            {
                "name": "WREG",
                "url": "https://www.wreg.com",
                "selector": "h2.entry-title",
                "domain_tag": "local",
                "source_weight": 0.8
            },
            {
                "name": "Commercial Appeal",
                "url": "https://www.commercialappeal.com",
                "selector": "h3.gnt_m_th_a",
                "domain_tag": "local",
                "source_weight": 0.9
            },
            {
                "name": "Tri-State Defender",
                "url": "https://www.tristatedefender.com",
                "selector": "h2.entry-title",
                "domain_tag": "local",
                "source_weight": 0.7
            }
        ]

        # Add sources to database
        for source_data in news_sources:
            source = NewsSource(
                name=source_data["name"],
                url=source_data["url"],
                selector=source_data["selector"],
                domain_tag=source_data["domain_tag"],
                source_weight=source_data["source_weight"],
                active=True
            )
            db.session.add(source)
            logging.info(f"Added news source: {source.name}")
        
        db.session.commit()
        logging.info("News sources re-seeded successfully")

    # Check drafts integration
    print("\n=== Checking Drafts Integration ===")
    headlines = NewsHeadline.query.all()
    print(f"\nFound {len(headlines)} news headlines in database")
    
    # Print sample headlines
    for headline in headlines[:5]:
        print(f"\nHeadline: {headline.title}")
        print(f"Source: {headline.source.name if headline.source else 'None'}")
        print(f"Date Added: {headline.date_added}")
        print(f"Domain Tag: {headline.domain_tag}")
    
    print("\n=== End of Drafts Check ===")
