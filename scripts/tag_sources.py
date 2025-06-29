from app import db, NewsSource

def tag_sources():
    """Update domain tags for news sources based on their content focus"""
    # Get all sources
    sources = NewsSource.query.all()
    
    for source in sources:
        # Determine domain based on URL and content focus
        domain = None
        
        # Check URL patterns and content focus
        url = source.url.lower()
        
        # Infrastructure
        if any(x in url for x in ['dot.gov', 'infrastructure', 'construction']):
            domain = 'infrastructure'
        # Public Safety
        elif any(x in url for x in ['police', 'fire', 'emergency', 'safety']):
            domain = 'public_safety'
        # Housing
        elif any(x in url for x in ['housing', 'real estate', 'apartments']):
            domain = 'housing'
        # Education
        elif any(x in url for x in ['education', 'school', 'university', 'college']):
            domain = 'education'
        # Transportation
        elif any(x in url for x in ['transportation', 'transit', 'railway', 'airline']):
            domain = 'transportation'
        # Environment
        elif any(x in url for x in ['environment', 'climate', 'weather', 'pollution']):
            domain = 'environment'
        # Economy
        elif any(x in url for x in ['economy', 'business', 'finance', 'market']):
            domain = 'economy'
        # Health
        elif any(x in url for x in ['health', 'medical', 'hospital', 'disease']):
            domain = 'health'
        else:
            domain = 'other'
        
        # Update source with domain
        source.domain_tag = domain
        print(f"Updated {source.name} with domain: {domain}")
    
    # Commit changes
    db.session.commit()
    print("\nAll sources have been tagged!")

if __name__ == '__main__':
    tag_sources()
