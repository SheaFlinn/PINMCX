import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Market, Prediction, LiquidityPool
from app.services.points_prediction_engine import PointsPredictionEngine

def create_test_app():
    """Create and configure a test Flask app."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app

@pytest.fixture(scope='module')
def test_app():
    """Test app fixture."""
    app = create_test_app()
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_user(test_app):
    """Test user fixture."""
    with test_app.app_context():
        user = User(username='testuser', points=1000)
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def test_market(test_app):
    """Test market fixture."""
    with test_app.app_context():
        market = Market(
            title="Test Market",
            description="Test market for AMM integration",
            deadline=datetime.utcnow() + timedelta(days=1),
            status="active",
            outcome=None
        )
        db.session.add(market)
        db.session.commit()
        return market

def test_prediction_place_updates_amm_liquidity_and_odds(test_app, test_user, test_market):
    """
    Test that placing a prediction updates AMM liquidity and odds correctly.
    
    Steps:
    1. Create a market with equal YES and NO liquidity
    2. Place a YES prediction with a stake of 100.0
    3. Verify:
       - YES liquidity increased
       - NO liquidity decreased
       - Odds updated correctly
       - Prediction is persisted and linked correctly
    """
    with test_app.app_context():
        # Create liquidity pool with equal liquidity
        pool = LiquidityPool(
            market_id=test_market.id,
            yes_liquidity=1000.0,
            no_liquidity=1000.0
        )
        db.session.add(pool)
        db.session.commit()

        # Place prediction
        outcome = True  # YES prediction
        stake = 100.0
        prediction = PointsPredictionEngine.place_prediction(
            user=test_user,
            market=test_market,
            shares=stake,
            outcome=outcome,
            use_liquidity_buffer=False
        )

        # Verify prediction is persisted
        assert prediction is not None
        assert prediction.user_id == test_user.id
        assert prediction.market_id == test_market.id
        assert prediction.outcome == "YES"
        assert prediction.stake == stake

        # Verify pool liquidity updated
        updated_pool = LiquidityPool.query.filter_by(market_id=test_market.id).first()
        assert updated_pool is not None
        
        # Calculate expected values using AMM formula
        initial_k = 1000.0 * 1000.0  # Initial constant product
        net_stake = stake * 0.95  # After 5% platform fee
        
        # For YES prediction:
        # new_yes_liquidity = initial_yes + net_stake
        # new_no_liquidity = initial_k / new_yes_liquidity
        expected_yes = 1000.0 + net_stake
        expected_no = initial_k / expected_yes
        
        assert updated_pool.yes_liquidity == pytest.approx(expected_yes)
        assert updated_pool.no_liquidity == pytest.approx(expected_no)

        # Verify odds updated correctly
        total = updated_pool.yes_liquidity + updated_pool.no_liquidity
        odds_yes = updated_pool.no_liquidity / total
        odds_no = updated_pool.yes_liquidity / total
        assert odds_yes + odds_no == pytest.approx(1.0)  # Odds should sum to 1
        assert odds_yes < 0.5  # Should be less than initial 0.5 odds
        assert odds_no > 0.5   # Should be greater than initial 0.5 odds

        # Verify prediction confidence matches shares purchased
        assert prediction.confidence > 0
        assert prediction.confidence < stake  # Should be less than full stake due to AMM price impact
