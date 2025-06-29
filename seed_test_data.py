from app import db, create_app
from app.models import User, Badge, UserBadge

# Create an app context
app = create_app()

with app.app_context():
    # Clear existing data
    db.session.query(UserBadge).delete()
    db.session.query(User).delete()
    db.session.query(Badge).delete()
    db.session.commit()

    # Create test user
    test_user = User(
        username='test_user',
        email='test@example.com',
        is_admin=False
    )
    test_user.set_password('password123')
    db.session.add(test_user)
    db.session.commit()

    # Create test badge
    test_badge = Badge(
        type='test_badge',
        name='Test Badge',
        description='A test badge for debugging',
        icon='fa-solid fa-bug'
    )
    db.session.add(test_badge)
    db.session.commit()

    # Verify data exists
    user = User.query.first()
    badge = Badge.query.first()
    print(f"Created user: {user.username}")
    print(f"Created badge: {badge.name}")

    # Test badge assignment
    user.assign_badge(badge)
    
    # Verify assignment
    assigned_badge = user.badges[0]
    print(f"Assigned badge: {assigned_badge.name}")
    print("Badge assignment test completed successfully!")
