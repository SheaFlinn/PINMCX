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
from app.models import NewsSource
from app.extensions import db

# Create Flask app context
app = create_app()

with app.app_context():
    # Check if Reddit source exists
    reddit_source = NewsSource.query.filter_by(name="Reddit").first()
    print(f"\n=== Checking Reddit News Source ===")
    
    if reddit_source:
        print(f"\nReddit source already exists:")
        print(f"ID: {reddit_source.id}")
        print(f"Name: {reddit_source.name}")
        print(f"URL: {reddit_source.url}")
        print(f"Selector: {reddit_source.selector}")
        print(f"Domain Tag: {reddit_source.domain_tag}")
        print(f"Active: {reddit_source.active}")
    else:
        print("\nReddit source not found, creating...")
        reddit_source = NewsSource(
            name="Reddit",
            url="https://reddit.com",
            selector="h3",
            domain_tag="community",
            source_weight=0.6,
            active=True
        )
        db.session.add(reddit_source)
        db.session.commit()
        print("\nReddit source created successfully!")
        print(f"ID: {reddit_source.id}")
        print(f"Name: {reddit_source.name}")
        print(f"URL: {reddit_source.url}")
        print(f"Selector: {reddit_source.selector}")
        print(f"Domain Tag: {reddit_source.domain_tag}")
        print(f"Active: {reddit_source.active}")
    
    print("\n=== End of Reddit Source Check ===")
