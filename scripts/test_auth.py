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
from werkzeug.security import generate_password_hash, check_password_hash

# Create Flask app context
app = create_app()

with app.app_context():
    # Get all users
    users = User.query.all()
    
    print("\n=== User Records ===")
    for user in users:
        print(f"\nUser: {user.username}")
        print(f"Email: {user.email}")
        print(f"Password hash: {user.password_hash[:10]}...")
        
        # Test password verification
        test_passwords = [
            "password123",  # Common default password
            "admin",       # Common admin password
            "123456",      # Common weak password
            "test123"     # Common test password
        ]
        
        print("\nTesting common passwords:")
        for pwd in test_passwords:
            result = user.check_password(pwd)
            print(f"Password '{pwd}' -> {result}")
            
        # Test with a known password hash
        test_hash = generate_password_hash("password123", method='pbkdf2:sha256')
        print(f"\nTesting with generated hash for 'password123':")
        print(f"Generated hash: {test_hash[:10]}...")
        print(f"Stored hash: {user.password_hash[:10]}...")
        print(f"Check result: {check_password_hash(user.password_hash, 'password123')}")

    print("\n=== End of User Records ===")
