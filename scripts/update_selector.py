import sys
import os
# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import NewsSource
from app.extensions import db

# Create Flask app context
app = create_app()

with app.app_context():
    # Get the Daily Memphian source
    source = NewsSource.query.filter_by(name="Daily Memphian").first()
    if not source:
        print("Daily Memphian source not found in database")
        exit(1)
    
    # Update the selector
    source.selector = "article h2"
    print(f"Updating Daily Memphian selector from '{source.selector}' to 'article h2'")
    
    # Commit the changes
    db.session.commit()
    print("Selector update successful!")
