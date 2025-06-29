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
from app.models import User
from app.extensions import db

# Create Flask app context
app = create_app()

with app.app_context():
    # User credentials to reset
    users_to_reset = {
        "admin": {"password": "admin", "is_admin": True},
        "test_admin": {"password": "test123", "is_admin": False}
    }

    # Process each user
    for username, user_data in users_to_reset.items():
        user = User.query.filter_by(username=username).first()
        if user:
            logging.info(f"Resetting password for user {username}")
            user.set_password(user_data["password"])
            user.is_admin = user_data["is_admin"]
            db.session.commit()
            logging.info(f"Password reset and admin status updated for user {username}")
        else:
            logging.warning(f"User {username} not found in database")

    print("\n=== Password Reset Summary ===")
    for username, user_data in users_to_reset.items():
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"\nUser: {username}")
            print(f"Email: {user.email}")
            print(f"Password hash: {user.password_hash[:10]}...")
            print(f"Is admin: {user.is_admin}")
            print(f"Password verification: {user.check_password(user_data['password'])}")
    print("\n=== End of Summary ===")
