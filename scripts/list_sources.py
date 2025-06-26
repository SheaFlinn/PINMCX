from app import db, NewsSource

def list_sources():
    """List all news sources from the database"""
    sources = NewsSource.query.all()
    print("\n=== News Sources ===\n")
    print(f"Total sources: {len(sources)}\n")
    
    for source in sources:
        print(f"ID: {source.id}")
        print(f"Name: {source.name}")
        print(f"URL: {source.url}")
        print(f"Selector: {source.selector}")
        print(f"Date Selector: {source.date_selector}")
        print(f"Active: {source.active}")
        print(f"Domain Tag: {source.domain_tag}")
        print(f"Source Weight: {source.source_weight}")
        print("-" * 50)

if __name__ == '__main__':
    list_sources()
