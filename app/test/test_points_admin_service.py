import pytest
from unittest.mock import patch, MagicMock
from app.services.points_admin_service import PointsAdminService
from app.models import User, Market, Badge, UserBadge, Prediction
from app.services.points_ledger import PointsLedger
from app import db
from datetime import datetime, timedelta

def create_test_user():
    return User(
        username="test_user",
        points=1000.0,
        xp=100,
        liquidity_buffer_deposit=500.0
    )

def create_test_market():
    return Market(
        title="Test Market",
        description="Test Description",
        deadline=datetime.utcnow() + timedelta(days=1),
        creator_id=1,
        platform_fee=0.05,
        liquidity_fee=0.01,
        status='open'
    )

def create_test_badge():
    return Badge(
        name="Test Badge",
        description="Test Badge Description"
    )

class TestPointsAdminService:
    @pytest.fixture
    def user(self):
        return create_test_user()

    @pytest.fixture
    def market(self):
        return create_test_market()

    @pytest.fixture
    def badge(self):
        return create_test_badge()

    @patch('app.services.points_ledger.PointsLedger.log_transaction')
    def test_award_manual_xp(self, mock_log_transaction, user):
        """Test manual XP award"""
        amount = 50
        reason = "Test XP award"
        
        PointsAdminService.award_manual_xp(user, amount, reason)
        
        assert user.xp == 150  # 100 + 50
        mock_log_transaction.assert_called_once_with(
            user=user,
            amount=amount,
            transaction_type="admin_manual",
            description="Admin XP award - Test XP award"
        )

    @patch('app.services.points_ledger.PointsLedger.log_transaction')
    def test_adjust_liquidity_buffer_deposit(self, mock_log_transaction, user):
        """Test liquidity buffer deposit"""
        amount = 100.0
        
        PointsAdminService.adjust_liquidity_buffer(user, amount, 'deposit')
        
        assert user.liquidity_buffer_deposit == 600.0  # 500 + 100
        mock_log_transaction.assert_called_once_with(
            user=user,
            amount=amount,
            transaction_type="admin_manual",
            description="Liquidity buffer deposited: 100.0"
        )

    @patch('app.services.points_ledger.PointsLedger.log_transaction')
    def test_adjust_liquidity_buffer_withdraw(self, mock_log_transaction, user):
        """Test liquidity buffer withdrawal"""
        amount = 100.0
        
        PointsAdminService.adjust_liquidity_buffer(user, amount, 'withdraw')
        
        assert user.liquidity_buffer_deposit == 400.0  # 500 - 100
        mock_log_transaction.assert_called_once_with(
            user=user,
            amount=-amount,
            transaction_type="admin_manual",
            description="Liquidity buffer withdrawn: 100.0"
        )

    @patch('app.services.points_ledger.PointsLedger.log_transaction')
    def test_credit_points(self, mock_log_transaction, user):
        """Test point credit"""
        amount = 500.0
        reason = "Test credit"
        
        PointsAdminService.credit_points(user, amount, reason)
        
        assert user.points == 1500.0  # 1000 + 500
        mock_log_transaction.assert_called_once_with(
            user=user,
            amount=amount,
            transaction_type="admin_manual",
            description="Admin credit: 500.0 - Test credit"
        )

    @patch('app.services.points_ledger.PointsLedger.log_transaction')
    def test_debit_points(self, mock_log_transaction, user):
        """Test point debit"""
        amount = 300.0
        reason = "Test debit"
        
        PointsAdminService.debit_points(user, amount, reason)
        
        assert user.points == 700.0  # 1000 - 300
        mock_log_transaction.assert_called_once_with(
            user=user,
            amount=-amount,
            transaction_type="admin_manual",
            description="Admin debit: 300.0 - Test debit"
        )

    @patch('app.services.points_ledger.PointsLedger.log_transaction')
    def test_award_badge(self, mock_log_transaction, user, badge):
        """Test badge awarding"""
        PointsAdminService.award_badge(user, badge)
        
        user_badge = UserBadge.query.filter_by(
            user_id=user.id,
            badge_id=badge.id
        ).first()
        
        assert user_badge is not None
        mock_log_transaction.assert_called_once_with(
            user=user,
            amount=0,
            transaction_type="badge_awarded",
            description=f"Badge awarded: {badge.name}"
        )

    @patch('app.services.points_ledger.PointsLedger.log_transaction')
    def test_award_points_for_market_resolution(self, mock_log_transaction, user, market):
        """Test points awarding for market resolution"""
        # Create test prediction
        prediction = Prediction(
            user_id=user.id,
            market_id=market.id,
            outcome='YES',
            stake=100.0,
            confidence=1.0,
            timestamp=datetime.utcnow()
        )
        db.session.add(prediction)
        db.session.commit()

        # Resolve market
        market.resolve('YES')
        
        # Award points
        PointsAdminService.award_points_for_market_resolution(market)
        
        # Verify points were awarded
        assert user.points > 1000.0  # Should have more than initial 1000 points
        mock_log_transaction.assert_called_with(
            user=user,
            amount=100.0,  # Should be equal to prediction stake
            transaction_type="market_resolution",
            description=f"Points awarded for correct prediction on market {market.id}"
        )
