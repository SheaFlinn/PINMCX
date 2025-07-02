import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.services.liquidity_service import LiquidityService
from app.models import User, MarketEvent

def create_test_user(liquidity_buffer_deposit: float = 0.0, liquidity_last_deposit_at: datetime = None) -> User:
    """Create a mock user for testing."""
    user = User(username="testuser", email="test@example.com")
    user.liquidity_buffer_deposit = liquidity_buffer_deposit
    user.liquidity_last_deposit_at = liquidity_last_deposit_at
    return user

@pytest.fixture
def mock_user():
    """Fixture for a mock user."""
    return create_test_user()

@pytest.fixture
def mock_market_event():
    """Fixture for a mock MarketEvent."""
    return MagicMock(spec=MarketEvent)

@pytest.fixture
def mock_db_session():
    """Fixture for a mock SQLAlchemy session."""
    return MagicMock()

@patch('app.services.liquidity_service.datetime')
@patch('app.services.liquidity_service.MarketEvent')
@patch('app.services.liquidity_service.db')
def test_deposit_success(mock_db, mock_market_event, mock_datetime, mock_user):
    """
    Test successful liquidity deposit:
    - Updates buffer deposit
    - Sets last deposit time
    - Logs event
    """
    amount = 100.0
    mock_datetime.utcnow.return_value = datetime(2025, 7, 1)
    
    # Mock MarketEvent
    mock_market_event.log_liquidity_deposit.return_value = None
    
    # Call deposit
    LiquidityService.deposit(mock_user, amount)
    
    # Verify state changes
    assert mock_user.liquidity_buffer_deposit == amount
    assert mock_user.liquidity_last_deposit_at == datetime(2025, 7, 1)
    
    # Verify logging
    mock_market_event.log_liquidity_deposit.assert_called_once_with(
        user_id=mock_user.id,
        amount=amount
    )
    mock_db.session.add.assert_called_once()
    mock_db.session.commit.assert_called_once()

@patch('app.services.liquidity_service.datetime')
@patch('app.services.liquidity_service.MarketEvent')
@patch('app.services.liquidity_service.db')
def test_withdraw_success(mock_db, mock_market_event, mock_datetime, mock_user):
    """
    Test successful liquidity withdrawal after lockout period:
    - Updates buffer deposit
    - Logs event
    """
    # Set up user with deposit 91 days ago
    mock_user.liquidity_buffer_deposit = 200.0
    mock_user.liquidity_last_deposit_at = datetime(2025, 4, 1)
    
    amount = 100.0
    mock_datetime.utcnow.return_value = datetime(2025, 7, 1)
    
    # Mock MarketEvent
    mock_market_event.log_liquidity_withdraw.return_value = None
    
    # Call withdraw
    LiquidityService.withdraw(mock_user, amount)
    
    # Verify state changes
    assert mock_user.liquidity_buffer_deposit == 100.0
    
    # Verify logging
    mock_market_event.log_liquidity_withdraw.assert_called_once_with(
        user_id=mock_user.id,
        amount=amount
    )
    mock_db.session.add.assert_called_once()
    mock_db.session.commit.assert_called_once()

@patch('app.services.liquidity_service.datetime')
def test_withdraw_too_soon(mock_datetime, mock_user):
    """
    Test withdrawal fails if less than 90 days since deposit
    """
    # Set up user with recent deposit
    mock_user.liquidity_buffer_deposit = 200.0
    mock_user.liquidity_last_deposit_at = datetime(2025, 6, 1)
    
    mock_datetime.utcnow.return_value = datetime(2025, 7, 1)
    
    with pytest.raises(ValueError, match="Cannot withdraw liquidity within 90 days of last deposit"):
        LiquidityService.withdraw(mock_user, 100.0)

@patch('app.services.liquidity_service.datetime')
def test_withdraw_insufficient_funds(mock_datetime, mock_user):
    """
    Test withdrawal fails if amount exceeds available balance
    """
    # Set up user with insufficient funds
    mock_user.liquidity_buffer_deposit = 50.0
    mock_user.liquidity_last_deposit_at = datetime(2025, 4, 1)
    
    mock_datetime.utcnow.return_value = datetime(2025, 7, 1)
    
    with pytest.raises(ValueError, match="Insufficient liquidity buffer balance"):
        LiquidityService.withdraw(mock_user, 100.0)

@patch('app.services.liquidity_service.datetime')
def test_withdraw_no_deposit(mock_datetime, mock_user):
    """
    Test withdrawal fails if no deposit has been made
    """
    # Set up user with no deposit
    mock_user.liquidity_buffer_deposit = 0.0
    mock_user.liquidity_last_deposit_at = None
    
    mock_datetime.utcnow.return_value = datetime(2025, 7, 1)
    
    with pytest.raises(ValueError, match="Cannot withdraw liquidity without a deposit"):
        LiquidityService.withdraw(mock_user, 100.0)

@patch('app.services.liquidity_service.datetime')
def test_deposit_zero_amount(mock_datetime, mock_user):
    """
    Test deposit fails with zero amount
    """
    mock_datetime.utcnow.return_value = datetime(2025, 7, 1)
    
    with pytest.raises(ValueError, match="Deposit amount must be positive"):
        LiquidityService.deposit(mock_user, 0.0)

@patch('app.services.liquidity_service.datetime')
def test_deposit_negative_amount(mock_datetime, mock_user):
    """
    Test deposit fails with negative amount
    """
    mock_datetime.utcnow.return_value = datetime(2025, 7, 1)
    
    with pytest.raises(ValueError, match="Deposit amount must be positive"):
        LiquidityService.deposit(mock_user, -100.0)
