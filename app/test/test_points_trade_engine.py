import pytest
from unittest.mock import patch, MagicMock
from app.services.points_trade_engine import PointsTradeEngine
from app.models import Market, User, Prediction
from app.services.points_ledger import PointsLedger
from datetime import datetime, timedelta

def create_test_market():
    market = Market(
        title="Test Market",
        description="Test Description",
        deadline=datetime.utcnow() + timedelta(days=1),
        creator_id=1,
        platform_fee=0.05,
        liquidity_fee=0.01,
        status='open'
    )
    return market

def create_test_user():
    return User(points=1000.0, xp=0)

class TestPointsTradeEngine:
    @pytest.fixture
    def market(self):
        return create_test_market()

    @pytest.fixture
    def user(self):
        return create_test_user()

    def test_execute_trade_yes(self, market, user):
        """Test YES trade execution"""
        amount = 100.0
        outcome = True
        
        result = PointsTradeEngine.execute_trade(user, market, amount, outcome)
        
        assert result['stake'] > 0
        assert result['price'] > 0
        assert result['outcome'] == 'YES'
        assert user.points == 900.0  # 1000 - 100
        assert market.status == 'open'

    def test_execute_trade_no(self, market, user):
        """Test NO trade execution"""
        amount = 100.0
        outcome = False
        
        result = PointsTradeEngine.execute_trade(user, market, amount, outcome)
        
        assert result['stake'] > 0
        assert result['price'] > 0
        assert result['outcome'] == 'NO'
        assert user.points == 900.0  # 1000 - 100
        assert market.status == 'open'

    def test_trade_amount_validation(self, market, user):
        """Test trade amount validation"""
        # Test with valid trade amount
        result = PointsTradeEngine.execute_trade(user, market, 100.0, True)
        assert result['stake'] > 0
        
        # Test with negative amount
        with pytest.raises(ValueError):
            PointsTradeEngine.execute_trade(user, market, -100.0, True)
        
        # Test with zero amount
        with pytest.raises(ValueError):
            PointsTradeEngine.execute_trade(user, market, 0.0, True)
        with pytest.raises(ValueError):
            PointsTradeEngine.execute_trade(user, market, 0.5, True)  # Below min
        with pytest.raises(ValueError):
            PointsTradeEngine.execute_trade(user, market, 2000.0, True)  # Above max

    @patch('app.services.points_ledger.PointsLedger.log_transaction')
    def test_ledger_logging(self, mock_log_transaction, market, user):
        """Test that trades are logged to ledger"""
        amount = 100.0
        outcome = True
        
        PointsTradeEngine.execute_trade(user, market, amount, outcome)
        
        mock_log_transaction.assert_called_once()
        args = mock_log_transaction.call_args[1]
        assert args['transaction_type'] == 'trade'
        assert args['amount'] == -amount
        assert 'YES' in args['description']

    def test_trade_result_structure(self, market, user):
        """Test that trade result contains correct structure"""
        result = PointsTradeEngine.execute_trade(user, market, 100.0, True)
        assert 'price' in result
        assert 'stake' in result
        assert 'outcome' in result
        assert isinstance(result['price'], float)
        assert isinstance(result['stake'], float)
        assert isinstance(result['outcome'], str)

    def test_prediction_creation(self, market, user):
        """Test that trade creates prediction correctly"""
        amount = 100.0
        outcome = True
        
        result = PointsTradeEngine.execute_trade(user, market, amount, outcome)
        
        prediction = Prediction.query.filter_by(
            user_id=user.id,
            market_id=market.id,
            outcome='YES'
        ).first()
        
        assert prediction is not None
        assert prediction.stake == amount
        assert prediction.confidence == 1.0
        assert prediction.timestamp is not None

    def test_market_status_validation(self, market, user):
        """Test that trades cannot be made on resolved markets"""
        market.status = 'resolved'
        market.outcome = 'YES'
        
        with pytest.raises(ValueError):
            PointsTradeEngine.execute_trade(user, market, 100.0, True)

    def test_insufficient_points(self, market, user):
        """Test trade with insufficient points"""
        user.points = 50.0  # Less than trade amount
        
        with pytest.raises(ValueError):
            PointsTradeEngine.execute_trade(user, market, 100.0, True)
