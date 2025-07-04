import pytest
from app.extensions import db
from app.models import User
from app import create_app
from app.services.xp_service import XPService
from datetime import datetime, timedelta

@pytest.fixture(scope="function")
def test_app():
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    return app

@pytest.fixture
def app_context(test_app):
    with test_app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()

@pytest.fixture
def session(test_app):
    """Provide a clean database session for each test."""
    with test_app.app_context():
        db.create_all()
        try:
            yield db.session
        finally:
            db.session.remove()
            db.drop_all()

@pytest.fixture
def user(session) -> User:
    """Create a test user."""
    user = User(username="test", email="test@example.com")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture
def user_with_xp(session) -> User:
    """Create a test user with XP and predictions."""
    user = User(username="test", email="test@example.com")
    user.xp = 50
    user.predictions_count = 2
    user.successful_predictions = 1
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def test_award_prediction_xp_success(user, session):
    XPService.award_prediction_xp(user, success=True)
    session.commit()
    session.refresh(user)
    assert user.xp == 15
    assert user.predictions_count == 1
    assert user.successful_predictions == 1
    assert user.reliability_index == 100.0

def test_award_prediction_xp_failure(user_with_xp, session):
    XPService.award_prediction_xp(user_with_xp, success=False)
    session.commit()
    session.refresh(user_with_xp)
    assert user_with_xp.xp == 60
    assert user_with_xp.predictions_count == 3
    assert user_with_xp.successful_predictions == 1
    assert round(user_with_xp.reliability_index, 2) == 33.33

def test_check_in_streak_reset(user, session):
    user.current_streak = 3
    user.longest_streak = 3
    user.last_check_in_date = datetime.utcnow() - timedelta(days=2)
    user.xp = 0
    session.commit()
    
    XPService.check_in(user)
    session.commit()
    session.refresh(user)
    assert user.current_streak == 1
    assert user.longest_streak == 3
    assert user.xp == 7

def test_check_in_streak_continue(user, session):
    user.current_streak = 2
    user.longest_streak = 2
    user.last_check_in_date = datetime.utcnow() - timedelta(days=1)
    user.xp = 10
    session.commit()
    
    XPService.check_in(user)
    session.commit()
    session.refresh(user)
    assert user.current_streak == 3
    assert user.longest_streak == 3
    assert user.xp == 21

def test_check_in_same_day_no_change(user, session):
    user.current_streak = 2
    user.longest_streak = 2
    user.last_check_in_date = datetime.utcnow()
    user.xp = 10
    session.commit()
    
    XPService.check_in(user)
    session.commit()
    session.refresh(user)
    assert user.current_streak == 2
    assert user.longest_streak == 2
    assert user.xp == 10
