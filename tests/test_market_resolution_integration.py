import pytest
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import User, Market, Prediction, MarketEvent

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
def session(app_context):
    return db.session

@pytest.fixture
def user(session):
    user = User(username="test", email="test@example.com")
    session.add(user)
    session.commit()
    return user

@pytest.fixture
def market(session):
    market = Market(
        title="Test Market",
        description="Test market for integration testing",
        resolution_date=datetime.utcnow() + timedelta(days=1),
        resolution_method="manual",
        prediction_deadline=datetime.utcnow() + timedelta(days=1)
    )
    session.add(market)
    session.commit()
    return market

@pytest.fixture
def prediction(user, market, session):
    prediction = Prediction(
        user_id=user.id,
        market_id=market.id,
        market=market,  # Required for prediction logging
        user=user,     # Required for prediction logging
        outcome=True,
        shares=100.0,
        platform_fee=5.0,
        used_liquidity_buffer=False
    )
    session.add(prediction)
    session.flush()  # Ensure prediction gets an ID before logging event
    prediction.log_prediction_event()
    session.commit()
    return prediction

def test_market_resolve_awards_xp_and_logs_events(user, market, prediction, session):
    # Verify initial state
    assert not market.resolved
    assert market.resolved_outcome is None
    assert not prediction.xp_awarded
    assert user.xp == 0
    assert MarketEvent.query.count() == 1  # Initial prediction event

    # Resolve the market
    market.resolve('YES')

    # Refresh objects from DB
    session.refresh(market)
    session.refresh(prediction)
    session.refresh(user)

    # Verify market resolution
    assert market.resolved
    assert market.resolved_outcome == 'YES'
    assert market.resolved_at is not None

    # Verify prediction XP award
    assert prediction.xp_awarded

    # Verify user XP
    assert user.xp == 15  # 10 base XP + 5 bonus for correct prediction

    # Verify events
    events = MarketEvent.query.all()
    assert len(events) == 3  # Initial prediction + XP award + market resolved

    # Verify prediction event
    pred_event = next(e for e in events if e.event_type == 'prediction')
    assert pred_event.market_id == market.id
    assert pred_event.user_id == user.id
    assert pred_event.event_data['prediction_id'] == prediction.id
    assert pred_event.event_data['shares'] == prediction.shares
    assert pred_event.event_data['outcome'] == prediction.outcome
    assert pred_event.event_data['xp_awarded'] == False  # XP not awarded yet

    # Verify XP awarded event
    xp_event = next(e for e in events if e.event_type == 'xp_awarded')
    assert xp_event.market_id == market.id
    assert xp_event.user_id == user.id
    assert xp_event.event_data['prediction_id'] == prediction.id
    assert xp_event.event_data['success'] is True
    assert xp_event.event_data['xp_awarded'] is True

    # Verify market resolved event
    resolved_event = next(e for e in events if e.event_type == 'market_resolved')
    assert resolved_event.market_id == market.id
    assert resolved_event.event_data['outcome'] == 'YES'
