import sys
import os
import json
import requests
from flask import Flask, Response
from flask.testing import FlaskClient
from flask_login import login_user
from flask_wtf.csrf import generate_csrf
from datetime import datetime

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import User, db, NewsSource

# Test data
TEST_DRAFTS = [
    {
        "title": "Test Draft 1",
        "source_id": "reddit1",
        "relevance_score": 0.8
    },
    {
        "title": "Test Draft 2",
        "relevance_score": 0.5
    },
    {
        "title": "Test Draft 3",
        "source_id": "reddit3"
    },
    {
        "source_id": "reddit4"  # Missing title
    }
]

def setup_test_environment():
    """Set up test environment with test data"""
    # Create Flask app context
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    # Create test user with admin privileges
    with app.app_context():
        # Clear existing users and sources
        User.query.delete()
        NewsSource.query.delete()
        db.session.commit()
        
        test_user = User(username="test_admin", email="test@example.com")
        test_user.set_password("test_password")
        test_user.is_admin = True
        db.session.add(test_user)
        
        # Create Reddit NewsSource
        reddit_source = NewsSource(
            name="Reddit",
            url="https://reddit.com",
            selector="h1",
            domain_tag="community",
            source_weight=0.7,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(reddit_source)
        db.session.commit()
        
        # Write test drafts to file
        os.makedirs('drafts', exist_ok=True)
        with open('drafts/refined_reddit_drafts.json', 'w') as f:
            json.dump(TEST_DRAFTS, f)
            
        return app, test_user

def test_debug_route():
    """Test the debug route functionality"""
    app, test_user = setup_test_environment()
    
    with app.test_client() as client:
        # Log in as admin
        response = client.post('/login', data={
            'username': 'test_admin',
            'password': 'test_password'
        })
        assert response.status_code == 302  # Should redirect after login
        
        # Test debug route
        response = client.get('/admin/debug_reddit_drafts')
        assert response.status_code == 200
        
        # Verify HTML response contains expected data
        response_data = response.get_data(as_text=True)
        assert "Test Draft 1" in response_data
        assert "Test Draft 2" in response_data
        assert "Test Draft 3" in response_data
        assert "Untitled" in response_data  # For draft with missing title
        
        # Verify source and relevance score display
        assert "reddit1" in response_data
        assert "0.8" in response_data
        assert "0.5" in response_data
        
        print("\nDebug route test passed!")
        print("Verifying error handling...")
        
        # Test error handling by removing the file
        os.remove('drafts/refined_reddit_drafts.json')
        response = client.get('/admin/debug_reddit_drafts')
        assert response.status_code == 200
        assert "Drafts file not found" in response.get_data(as_text=True)
        
        print("Error handling verified!")

def test_admin_drafts_route():
    """Test the main admin drafts route"""
    app, test_user = setup_test_environment()
    
    with app.test_client() as client:
        # Log in as admin
        response = client.post('/login', data={
            'username': 'test_admin',
            'password': 'test_password'
        })
        assert response.status_code == 302
        
        # Test admin drafts route
        response = client.get('/admin/drafts')
        assert response.status_code == 200
        
        # Verify HTML response contains expected data
        response_data = response.get_data(as_text=True)
        assert "Test Draft 1" in response_data
        assert "Test Draft 2" in response_data
        assert "Test Draft 3" in response_data
        assert "Untitled" in response_data
        
        # Verify Reddit badge appears
        assert "badge bg-danger text-white" in response_data
        assert "Reddit" in response_data
        
        print("\nAdmin drafts route test passed!")
        print("Verifying Reddit badge display...")
        
        # Test with no Reddit NewsSource
        with app.app_context():
            NewsSource.query.filter_by(name="Reddit").delete()
            db.session.commit()
            
        response = client.get('/admin/drafts')
        assert response.status_code == 200
        response_data = response.get_data(as_text=True)
        assert "Test Draft 1" not in response_data  # Verify Reddit drafts are not shown
        assert "Reddit" not in response_data  # Verify Reddit badge is not shown
        
        print("Reddit NewsSource handling verified!")

if __name__ == "__main__":
    test_debug_route()
    test_admin_drafts_route()
