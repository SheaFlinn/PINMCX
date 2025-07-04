import pytest
from app.models import User, Market
from app.extensions import db
from app.services.points_service import PointsService
from datetime import datetime, timedelta


def test_award_xp(app):
    """Test XP awarding functionality"""
    with app.app_context():
        # Create a test user
        user = User(username="xpuser", email="xp@example.com")
        db.session.add(user)
        db.session.commit()

        ps = PointsService()

        # Award 25 XP
        result = ps.award_xp(user.id, 25)
        assert result == 25
        assert ps.get_user_xp(user.id) == 25

        # Award 10 more XP
        result = ps.award_xp(user.id, 10)
        assert result == 35

        # Verify the user's XP is persisted
        db.session.refresh(user)
        assert user.xp == 35


def test_get_user_streak(app):
    """Test user streak information retrieval"""
    with app.app_context():
        # Create a test user with streak data
        user = User(username="streakuser", email="streak@example.com")
        user.current_streak = 5
        user.longest_streak = 10
        user.last_check_in_date = datetime.utcnow()
        db.session.add(user)
        db.session.commit()

        ps = PointsService()
        
        # Test getting streak info
        streak_info = ps.get_user_streak(user.id)
        assert streak_info is not None
        assert streak_info["current_streak"] == 5
        assert streak_info["longest_streak"] == 10
        assert isinstance(streak_info["last_check_in"], datetime)

        # Test with non-existent user
        assert ps.get_user_streak(999999) is None


def test_predict(app):
    """Test prediction creation functionality"""
    with app.app_context():
        # Create test user with points
        user = User(username="predictor", email="predictor@example.com")
        user.points = 100
        db.session.add(user)
        db.session.commit()

        # Create test market
        market = Market(
            title="Test Market",
            description="Test description",
            resolution_date=datetime.utcnow() + timedelta(days=7),
            resolution_method="manual",
            source_url="http://test.com",
            domain="test",
            original_source="test",
            original_headline="Test Headline",
            original_date=datetime.utcnow()
        )
        db.session.add(market)
        db.session.commit()

        ps = PointsService()

        # Test successful prediction
        result = ps.predict(user.id, market.id, 'YES', 50)
        assert result["success"]
        assert result["prediction_id"] > 0
        assert result["remaining_points"] == 50
        assert "Prediction created successfully" in result["message"]

        # Test invalid choice
        result = ps.predict(user.id, market.id, 'MAYBE', 50)
        assert not result["success"]
        assert "Invalid choice" in result["message"]

        # Test insufficient points
        result = ps.predict(user.id, market.id, 'YES', 1000)
        assert not result["success"]
        assert "Insufficient points" in result["message"]
        assert result["required_points"] == 1000
        assert result["available_points"] == 50

        # Test non-existent market
        result = ps.predict(user.id, 999999, 'YES', 50)
        assert not result["success"]
        assert "Market not found" in result["message"]

        # Test non-existent user
        result = ps.predict(999999, market.id, 'YES', 50)
        assert not result["success"]
        assert "User not found" in result["message"]
