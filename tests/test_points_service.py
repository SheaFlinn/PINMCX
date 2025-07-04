import pytest
from app.models import User
from app.extensions import db
from app.services.points_service import PointsService


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
