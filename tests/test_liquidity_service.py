import pytest
from datetime import datetime, timedelta
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
    return MarketEvent()

@pytest.fixture
def mock_db_session():
    """Fixture for a mock SQLAlchemy session."""
    return mock_db_session

def test_deposit_success(test_client, test_db):
    """
    Test successful liquidity deposit:
    - Updates buffer deposit
    - Sets last deposit time
    - Logs event
    """
    amount = 100.0
    user = create_test_user()
    test_db.session.add(user)
    test_db.session.commit()
    
    # Call deposit
    LiquidityService.deposit(user, amount)
    
    # Verify state changes
    updated_user = test_db.session.get(User, user.id)
    assert updated_user.liquidity_buffer_deposit == amount
    assert updated_user.liquidity_last_deposit_at is not None
    
    # Verify logging
    event = test_db.session.query(MarketEvent).filter_by(
        user_id=user.id,
        event_type='liquidity_deposit'
    ).first()
    assert event is not None
    assert event.event_data["amount"] == amount

def test_withdraw_success(test_client, test_db):
    """
    Test successful liquidity withdrawal after lockout period:
    - Updates buffer deposit
    - Logs event
    """
    # Set up user with deposit 91 days ago
    user = create_test_user(liquidity_buffer_deposit=200.0, liquidity_last_deposit_at=datetime(2025, 4, 1))
    test_db.session.add(user)
    test_db.session.commit()
    
    amount = 100.0
    
    # Call withdraw
    LiquidityService.withdraw(user, amount)
    
    # Verify state changes
    updated_user = test_db.session.get(User, user.id)
    assert updated_user.liquidity_buffer_deposit == 100.0
    
    # Verify logging
    event = test_db.session.query(MarketEvent).filter_by(
        user_id=user.id,
        event_type='liquidity_withdraw'
    ).first()
    assert event is not None
    assert event.event_data["amount"] == amount

def test_withdraw_too_soon(test_client, test_db):
    """
    Test withdrawal fails if less than 90 days since deposit
    """
    # Set up user with recent deposit
    user = create_test_user(liquidity_buffer_deposit=200.0, liquidity_last_deposit_at=datetime(2025, 6, 1))
    test_db.session.add(user)
    test_db.session.commit()
    
    with pytest.raises(ValueError, match="Cannot withdraw liquidity within 90 days of last deposit"):
        LiquidityService.withdraw(user, 100.0)

def test_withdraw_insufficient_funds(test_client, test_db):
    """
    Test withdrawal fails if amount exceeds available balance
    """
    # Set up user with insufficient funds
    user = create_test_user(liquidity_buffer_deposit=50.0, liquidity_last_deposit_at=datetime(2025, 4, 1))
    test_db.session.add(user)
    test_db.session.commit()
    
    with pytest.raises(ValueError, match="Insufficient liquidity buffer balance"):
        LiquidityService.withdraw(user, 100.0)

def test_withdraw_no_deposit(test_client, test_db):
    """
    Test withdrawal fails if no deposit has been made
    """
    # Set up user with no deposit
    user = create_test_user()
    test_db.session.add(user)
    test_db.session.commit()
    
    with pytest.raises(ValueError, match="Cannot withdraw liquidity without a deposit"):
        LiquidityService.withdraw(user, 100.0)

def test_deposit_zero_amount(test_client, test_db):
    """
    Test deposit fails with zero amount
    """
    user = create_test_user()
    test_db.session.add(user)
    test_db.session.commit()
    
    with pytest.raises(ValueError, match="Deposit amount must be positive"):
        LiquidityService.deposit(user, 0.0)

def test_deposit_negative_amount(test_client, test_db):
    """
    Test deposit fails with negative amount
    """
    user = create_test_user()
    test_db.session.add(user)
    test_db.session.commit()
    
    with pytest.raises(ValueError, match="Deposit amount must be positive"):
        LiquidityService.deposit(user, -100.0)

def test_deposit_to_lb_success(test_client, test_db):
    """
    Test successful liquidity buffer deposit:
    - User exists
    - Sufficient points
    - Correct balance updates
    - Event logged
    """
    # Create test user
    user = User(username="testuser", email="test@example.com")
    user.points = 100
    user.lb_deposit = 0
    test_db.session.add(user)
    test_db.session.commit()
    
    # Call deposit_to_lb
    result = LiquidityService.deposit_to_lb(user.id, 50)
    
    # Verify result
    assert result is not None
    assert result["user_id"] == user.id
    assert result["new_lb_balance"] == 50
    assert result["remaining_points"] == 50
    
    # Verify database state
    updated_user = test_db.session.get(User, user.id)
    assert updated_user.lb_deposit == 50
    assert updated_user.points == 50
    
    # Verify event was created
    event = test_db.session.query(MarketEvent).filter_by(
        user_id=user.id,
        event_type='liquidity_deposit'
    ).first()
    assert event is not None
    assert event.event_data["amount"] == 50

def test_deposit_to_lb_insufficient_points(test_client, test_db):
    """
    Test deposit fails when user has insufficient points
    """
    # Create test user
    user = User(username="testuser", email="test@example.com")
    user.points = 40
    user.lb_deposit = 0
    test_db.session.add(user)
    test_db.session.commit()
    
    # Call deposit_to_lb with amount greater than points
    result = LiquidityService.deposit_to_lb(user.id, 50)
    
    # Verify result is None
    assert result is None
    
    # Verify database state unchanged
    updated_user = test_db.session.get(User, user.id)
    assert updated_user.lb_deposit == 0
    assert updated_user.points == 40

def test_deposit_to_lb_nonexistent_user(test_client, test_db):
    """
    Test deposit fails when user does not exist
    """
    # Call deposit_to_lb with non-existent user
    result = LiquidityService.deposit_to_lb(999999, 50)
    
    # Verify result is None
    assert result is None

def test_deposit_to_lb_zero_amount(test_client, test_db):
    """
    Test deposit fails with zero amount
    """
    # Create test user
    user = User(username="testuser", email="test@example.com")
    user.points = 100
    user.lb_deposit = 0
    test_db.session.add(user)
    test_db.session.commit()
    
    # Call deposit_to_lb with zero amount
    result = LiquidityService.deposit_to_lb(user.id, 0)
    
    # Verify result is None
    assert result is None
    
    # Verify database state unchanged
    updated_user = test_db.session.get(User, user.id)
    assert updated_user.lb_deposit == 0
    assert updated_user.points == 100

def test_deposit_to_lb_negative_amount(test_client, test_db):
    """
    Test deposit fails with negative amount
    """
    # Create test user
    user = User(username="testuser", email="test@example.com")
    user.points = 100
    user.lb_deposit = 0
    test_db.session.add(user)
    test_db.session.commit()
    
    # Call deposit_to_lb with negative amount
    result = LiquidityService.deposit_to_lb(user.id, -50)
    
    # Verify result is None
    assert result is None
    
    # Verify database state unchanged
    updated_user = test_db.session.get(User, user.id)
    assert updated_user.lb_deposit == 0
    assert updated_user.points == 100

def test_withdraw_from_lb_success(test_client, test_db):
    """
    Test successful withdrawal from liquidity buffer:
    - User exists
    - Sufficient liquidity buffer
    - Correct balance updates
    - Event logged
    """
    # Create test user with points and liquidity buffer
    user = User(username="testuser", email="test@example.com")
    user.points = 50
    user.lb_deposit = 100
    test_db.session.add(user)
    test_db.session.commit()
    
    # Call withdraw_from_lb
    result = LiquidityService.withdraw_from_lb(user.id, 50)
    
    # Verify result
    assert result is not None
    assert result["user_id"] == user.id
    assert result["withdrawn"] == 50
    assert result["remaining_lb"] == 50
    assert result["updated_points"] == 100
    
    # Verify database state
    updated_user = test_db.session.get(User, user.id)
    assert updated_user.lb_deposit == 50
    assert updated_user.points == 100
    
    # Verify event was created
    event = test_db.session.query(MarketEvent).filter_by(
        user_id=user.id,
        event_type='liquidity_withdraw'
    ).first()
    assert event is not None
    assert event.event_data["amount"] == 50

def test_withdraw_from_lb_insufficient_balance(test_client, test_db):
    """
    Test withdrawal fails when user has insufficient liquidity buffer
    """
    # Create test user with points and insufficient liquidity buffer
    user = User(username="testuser", email="test@example.com")
    user.points = 50
    user.lb_deposit = 40
    test_db.session.add(user)
    test_db.session.commit()
    
    # Call withdraw_from_lb with amount greater than balance
    result = LiquidityService.withdraw_from_lb(user.id, 50)
    
    # Verify result is None
    assert result is None
    
    # Verify database state unchanged
    updated_user = test_db.session.get(User, user.id)
    assert updated_user.lb_deposit == 40
    assert updated_user.points == 50

def test_withdraw_from_lb_zero_amount(test_client, test_db):
    """
    Test withdrawal fails with zero amount
    """
    # Create test user with points and liquidity buffer
    user = User(username="testuser", email="test@example.com")
    user.points = 50
    user.lb_deposit = 100
    test_db.session.add(user)
    test_db.session.commit()
    
    # Call withdraw_from_lb with zero amount
    result = LiquidityService.withdraw_from_lb(user.id, 0)
    
    # Verify result is None
    assert result is None
    
    # Verify database state unchanged
    updated_user = test_db.session.get(User, user.id)
    assert updated_user.lb_deposit == 100
    assert updated_user.points == 50

def test_withdraw_from_lb_nonexistent_user(test_client, test_db):
    """
    Test withdrawal fails for non-existent user
    """
    # Call withdraw_from_lb with non-existent user ID
    result = LiquidityService.withdraw_from_lb(9999, 50)
    
    # Verify result is None
    assert result is None
