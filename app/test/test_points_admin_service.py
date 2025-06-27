import pytest
from unittest.mock import patch, MagicMock
from app.services.points_admin_service import PointsAdminService
from app.models import User, Market, Badge, UserBadge
from app.services.points_ledger import PointsLedger

def create_test_user():
    return User(
        username="test_user",
        points=1000.0,
        xp=100,
        lb_deposit=500.0
    )

def create_test_market():
    return Market(
        title="Test Market",
        description="Test Description",
        yes_pool=1000.0,
        no_pool=1000.0,
        liquidity_pool=1000.0,
        liquidity_provider_shares=1000.0,
        liquidity_fee=0.01
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
        
        assert user.lb_deposit == 600.0  # 500 + 100
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
        
        assert user.lb_deposit == 400.0  # 500 - 100
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
            description="Admin point credit - Test credit"
        )

    @patch('app.services.points_ledger.PointsLedger.log_transaction')
    def test_debit_points(self, mock_log_transaction, user):
        """Test point debit"""
        amount = 500.0
        reason = "Test debit"
        
        PointsAdminService.debit_points(user, amount, reason)
        
        assert user.points == 500.0  # 1000 - 500
        mock_log_transaction.assert_called_once_with(
            user=user,
            amount=-amount,
            transaction_type="admin_manual",
            description="Admin point debit - Test debit"
        )

    @patch('app.services.points_ledger.PointsLedger.log_transaction')
    def test_force_resolve_market(self, mock_log_transaction, market):
        """Test market forced resolution"""
        outcome = "YES"
        admin_user_id = 1
        
        PointsAdminService.force_resolve_market(market, outcome, admin_user_id)
        
        assert market.resolved
        assert market.resolved_outcome == outcome
        mock_log_transaction.assert_called_once_with(
            user_id=admin_user_id,
            amount=0,
            transaction_type="admin_manual",
            description=f"Admin forced market {market.id} resolution to {outcome}"
        )

    @patch('app.services.points_ledger.PointsLedger.log_transaction')
    def test_grant_badge(self, mock_log_transaction):
        """Test badge granting"""
        from app import create_app, db
        from app.models import User, Badge, UserBadge
        from app.services.points_admin_service import PointsAdminService

        app = create_app("testing")
        with app.app_context():
            # Create and persist user and badge
            user = User(username="test_user", email="test@example.com")
            user.set_password("password")
            badge = Badge(type="test_badge", name="Test Badge", description="Test", icon="fa-test")
            db.session.add_all([user, badge])
            db.session.commit()

            # Grant badge
            PointsAdminService.grant_badge(user, badge, "Test badge grant")

            # Validate result
            user_badge = UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first()
            assert user_badge is not None
            
            mock_log_transaction.assert_called_once_with(
                user_id=user.id,
                amount=0,
                transaction_type="badge_awarded",
                description="Badge 'Test Badge' granted. Reason: Test badge grant"
            )
