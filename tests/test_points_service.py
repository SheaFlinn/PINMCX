import pytest
from app.models import User, Market, Prediction, MarketEvent
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
        result = ps.predict(
            user_id=user.id,
            market_id=market.id,
            choice='YES',
            stake_amount=50
        )
        assert result["success"]
        assert result["prediction_id"] > 0
        assert result["remaining_points"] == 50
        assert "Prediction created successfully" in result["message"]

        # Test invalid choice
        result = ps.predict(
            user_id=user.id,
            market_id=market.id,
            choice='MAYBE',
            stake_amount=50
        )
        assert not result["success"]
        assert "Invalid choice" in result["message"]

        # Test insufficient points
        result = ps.predict(
            user_id=user.id,
            market_id=market.id,
            choice='YES',
            stake_amount=1000
        )
        assert not result["success"]
        assert "Insufficient points" in result["message"]
        assert result["required_points"] == 1000
        assert result["available_points"] == 50

        # Test non-existent market
        result = ps.predict(
            user_id=user.id,
            market_id=999999,
            choice='YES',
            stake_amount=50
        )
        assert not result["success"]
        assert "Market not found" in result["message"]

        # Test non-existent user
        result = ps.predict(
            user_id=999999,
            market_id=market.id,
            choice='YES',
            stake_amount=50
        )
        assert not result["success"]
        assert "User not found" in result["message"]


def test_resolve_market(test_client, test_db):
    """Test resolving a market and awarding points to winners"""
    # Create test user
    user = User(username="resolver", email="resolver@example.com")
    test_db.session.add(user)
    test_db.session.commit()  # Commit to get user ID
    user.points = 100  # Set points after commit
    test_db.session.commit()  # Commit points update

    # Create test market with all required fields
    market = Market(
        title="Test Market",
        description="Test description",
        resolution_date=datetime.utcnow() + timedelta(days=1),
        resolution_method="manual",
        domain="test",
        source_url="http://example.com",
        resolution_deadline=datetime.utcnow() + timedelta(days=2),
        prediction_deadline=datetime.utcnow() + timedelta(days=1),
        yes_pool=1000.0,
        no_pool=1000.0,
        liquidity_pool=2000.0,
        liquidity_provider_shares=1.0,
        liquidity_fee=0.003
    )
    test_db.session.add(market)
    test_db.session.commit()

    # Place winning prediction
    prediction = Prediction(
        user_id=user.id,
        market_id=market.id,
        outcome=True,  # YES prediction
        shares=50,
        shares_purchased=50,
        stake=50,
        price=1.0,  # Simplified price
        created_at=datetime.utcnow()
    )
    test_db.session.add(prediction)
    test_db.session.commit()

    ps = PointsService()
    result = ps.resolve_market(market.id, "YES")

    # Check result structure
    assert result["market_id"] == market.id
    assert result["winning_choice"] == "YES"
    assert user.id in result["winners"]

    # Check user's points (50 staked, 100 total before, +100 rewarded)
    updated_user = db.session.get(User, user.id)
    assert updated_user.points == 150

    # Check market resolved
    updated_market = db.session.get(Market, market.id)
    assert updated_market.resolved is True
    assert updated_market.resolved_outcome == "YES"


def test_resolve_market(test_client, test_db):
    """Test resolving a market and awarding points to winners"""
    # Create test user
    user = User(username="test", email="test@example.com")
    user.points = 100
    test_db.session.add(user)
    test_db.session.commit()

    # Create test market
    market = Market(
        title="Test Market",
        description="Test description",
        resolution_date=datetime.utcnow() + timedelta(days=1),
        resolution_method="manual",
        domain="test"
    )
    test_db.session.add(market)
    test_db.session.commit()

    # Create predictions
    prediction1 = Prediction(
        user_id=user.id,
        market_id=market.id,
        outcome=True,  # YES prediction
        shares=10,
        shares_purchased=10,
        stake=10,
        price=10,
        created_at=datetime.utcnow()
    )
    prediction2 = Prediction(
        user_id=user.id,
        market_id=market.id,
        outcome=False,  # NO prediction
        shares=10,
        shares_purchased=10,
        stake=10,
        price=-10,
        created_at=datetime.utcnow()
    )
    test_db.session.add_all([prediction1, prediction2])
    test_db.session.commit()

    # Resolve market with YES outcome
    result = PointsService.resolve_market(market.id, "YES")
    assert result is not None
    assert result["market_id"] == market.id
    assert result["winning_choice"] == "YES"
    assert user.id in result["winners"]

    # Verify points were awarded to YES predictor
    updated_user = db.session.get(User, user.id)
    assert updated_user.points == 100 + (10 * 2)  # Original points + reward

    # Verify market is resolved
    updated_market = db.session.get(Market, market.id)
    assert updated_market.resolved
    assert updated_market.resolved_outcome == "YES"
    assert updated_market.resolved_at is not None

    # Verify prediction event was created
    event = db.session.query(MarketEvent).filter_by(
        market_id=market.id,
        user_id=user.id,
        event_type='prediction_resolved'
    ).first()
    assert event is not None
    assert event.event_data["points_awarded"] == 20
    assert event.event_data["outcome"] == "YES"


def test_award_points(app):
    """
    Test awarding points to a user:
    - User exists
    - Valid amount
    - Points are updated
    - Event is logged
    """
    with app.app_context():
        # Create test user
        user = User(username="pointsuser", email="points@example.com")
        db.session.add(user)
        db.session.commit()
        
        ps = PointsService()
        
        # Test awarding points to user with no initial points
        result = ps.award_points(user.id, 50)
        assert result == 50
        
        # Verify database state
        updated_user = db.session.get(User, user.id)
        assert updated_user.points == 50
        
        # Verify event was created
        event = db.session.query(MarketEvent).filter_by(
            user_id=user.id,
            event_type='liquidity_deposit'
        ).first()
        assert event is not None
        assert event.event_data["amount"] == 50
        
        # Test awarding more points
        result = ps.award_points(user.id, 25)
        assert result == 75
        
        # Verify database state
        updated_user = db.session.get(User, user.id)
        assert updated_user.points == 75
        
        # Test invalid amount (zero)
        result = ps.award_points(user.id, 0)
        assert result is None
        
        # Test invalid amount (negative)
        result = ps.award_points(user.id, -10)
        assert result is None
        
        # Test non-existent user
        result = ps.award_points(999999, 50)
        assert result is None
