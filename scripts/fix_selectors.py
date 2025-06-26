from app import create_app
from app.models import NewsSource, db

# Create Flask app context
app = create_app()

# Fix broken selectors
fixes = {
    "Daily Memphian": "h3.card-title",
    "MLK50": "h2.entry-title",
    "Commercial Appeal": "h3.gnt_m_th_a"
}

with app.app_context():
    for name, selector in fixes.items():
        source = NewsSource.query.filter_by(name=name).first()
        if source:
            source.selector = selector
            print(f"Updated selector for {name} to {selector}")
        else:
            print(f"Could not find source named {name}")

    db.session.commit()
    print("All changes committed to database")
