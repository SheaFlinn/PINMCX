from app import db
from app.models import Badge

# Create an application context
from app import create_app
app = create_app()
app.app_context().push()

# Check if tables exist
tables = db.engine.table_names()
print("\nExisting tables:")
for table in tables:
    print(f"- {table}")

# Try to create all tables
print("\nAttempting to create all tables...")
db.create_all()

# Check tables again after creation attempt
print("\nTables after creation attempt:")
tables = db.engine.table_names()
for table in tables:
    print(f"- {table}")

# Check if Badge table exists
badge_table_exists = 'badge' in tables
print(f"\nBadge table exists: {badge_table_exists}")

# Try to create a test badge
try:
    test_badge = Badge(name="Test Badge")
    db.session.add(test_badge)
    db.session.commit()
    print("\nSuccessfully created test badge")
except Exception as e:
    print(f"\nError creating test badge: {e}")
