from app import create_app
from app.extensions import db
from app.models import User, MarketEvent
from datetime import datetime
import pytest

@pytest.fixture
def test_app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_log_market_creation(test_app):
    user = User(username="tester", email="tester@example.com")
    db.session.add(user)
    db.session.commit()

    event = MarketEvent.log_market_creation(
        market=type('Market', (object,), {
            'id': 1,
            'title': 'Test Market',
            'description': 'Test description',
            'resolution_date': datetime.utcnow(),
            'resolution_method': 'Admin resolves',
            'domain': 'local',
            'lineage_chain': 'Parent → Test Market'
        }),
        user_id=user.id
    )
    db.session.add(event)
    db.session.commit()

    assert event.event_type == 'market_created'
    assert 'Test Market' in event.description
    assert event.user_id == user.id

def test_log_prediction_event(test_app):
    user = User(username="predictor", email="predictor@example.com")
    db.session.add(user)
    db.session.commit()

    event = MarketEvent.log_prediction(
        market=type('Market', (object,), {
            'id': 2,
            'title': 'Market 2',
            'domain': 'local',
            'lineage_chain': 'Parent → Market 2'
        }),
        user_id=user.id,
        prediction={"outcome": "YES", "points": 100}
    )
    db.session.add(event)
    db.session.commit()

    assert event.event_type == 'prediction'
    assert event.event_data["prediction"]["outcome"] == "YES"
