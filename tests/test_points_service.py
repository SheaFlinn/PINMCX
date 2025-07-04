import pytest
from app.models import User
from app.extensions import db
from app.services.points_service import PointsService
from datetime import datetime


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
