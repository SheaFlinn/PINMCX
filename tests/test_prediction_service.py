import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from app import create_app, db
from app.services.prediction_service import PredictionService
from app.models import User, Market, Prediction, MarketEvent, LiquidityPool, LiquidityProvider

@pytest.fixture(scope="function")
def test_app():
    """Create and configure a new app instance for each test."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'connect_args': {'timeout': 15}
        }
    })
    
    with app.app_context():
        db.create_all()
        
        # Register models
        from app.models import user, market, prediction, market_event, platform_wallet, news, liquidity_pool, liquidity_provider, user_ledger, amm_market
        models = [
            user.User,
            market.Market,
            prediction.Prediction,
            market_event.MarketEvent,
            platform_wallet.PlatformWallet,
            news.NewsSource,
            news.NewsHeadline,
            liquidity_pool.LiquidityPool,
            liquidity_provider.LiquidityProvider,
            user_ledger.UserLedger,
            amm_market.AMMMarket
        ]
        print(f"Registered tables after init_app: {dict([(model.__tablename__, model.__tablename__) for model in models])}")
        
    yield app
    
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_user(test_app):
    """Fixture for a test user with points and liquidity buffer."""
    with test_app.app_context():
        # Create user with required attributes
        user = User(
            username="testuser",
            email="testuser@example.com"
        )
        user.liquidity_buffer_deposit = 1000.0
        db.session.add(user)
        db.session.commit()
        
        yield user
        
        # Clean up
        db.session.delete(user)
        db.session.commit()

@pytest.fixture
def test_session(test_app):
    with test_app.app_context():
        yield db.session

@pytest.fixture
def test_market(test_user, test_session):
    """Fixture for a test market with valid attributes."""
    # Create market with required attributes
    market = Market(
        title="Test Market",
        description="Is this a test market?",
        resolution_date=datetime.utcnow() + timedelta(days=30),
        resolution_method="manual",
        yes_pool=1000.0,
        no_pool=1000.0,
        liquidity_pool=2000.0
    )
    
    # Add market to session and commit to get an ID
    test_session.add(market)
    test_session.commit()
    
    # Create liquidity pool
    liquidity_pool = LiquidityPool(
        contract_id=market.id,
        max_liquidity=2000.0,
        current_liquidity=2000.0
    )
    
    # Add both to session
    test_session.add(liquidity_pool)
    test_session.commit()
    
    yield market
    
    # Cleanup
    test_session.delete(liquidity_pool)
    test_session.delete(market)
    test_session.commit()

@pytest.fixture
@patch('app.services.prediction_service.XPService', autospec=True)
def test_prediction(test_app, test_user, test_market, mock_xp_service):
    """Fixture for a test prediction."""
    with test_app.app_context():
        # Mock XP service response
        mock_xp_service.award_prediction_xp.return_value = None

        # Create prediction
        prediction = Prediction(
            user_id=test_user.id,
            market_id=test_market.id,
            stake=100,
            outcome=True,
            shares=0.5,
            shares_purchased=0.5,
            price=1.0,
            used_liquidity_buffer=False
        )
        
        # Add to session and commit
        db.session.add(prediction)
        db.session.commit()
        
        yield prediction
        
        # Clean up
        db.session.delete(prediction)
        db.session.commit()

class TestPredictionService:
    @patch('app.services.prediction_service.AMMService', autospec=True)
    @patch('app.services.prediction_service.XPService', autospec=True)
    def test_place_prediction_points(self, mock_xp_service, mock_amm_service, test_app, test_session):
        """
        Test placing a prediction using points:
        - Deducts points
        - Updates market liquidity
        - Creates prediction record
        """
        with test_app.app_context():
            # Create user
            user = User(username="test_user", email="test@example.com")
            user.points = 100
            user.liquidity_buffer_deposit = 100.0
            test_session.add(user)
            test_session.commit()
            
            # Create market
            market = Market(
                title="Test Market",
                description="Is this a test market?",
                resolution_date=datetime.utcnow() + timedelta(days=30),
                resolution_method="manual",
                yes_pool=1000.0,
                no_pool=1000.0,
                liquidity_pool=2000.0
            )
            test_session.add(market)
            test_session.commit()
            
            # Mock AMM service response
            mock_amm_service.calculate_share_allocation.return_value = {
                'shares': 0.5,
                'yes_liquidity': 1050.0,
                'no_liquidity': 950.0,
                'price': 0.525
            }
            
            # Place prediction
            with test_session.no_autoflush:
                prediction = PredictionService.place_prediction(
                    user=user,
                    market=market,
                    stake=100,
                    outcome=True
                )
                
                # Verify points were deducted
                assert user.points == 0
                
                # Verify prediction was created
                assert prediction is not None
                assert prediction.outcome is True
                assert prediction.shares == 0.5
                assert prediction.stake == 100
                
                # Verify market pools were updated
                assert market.yes_pool == 1050.0
                assert market.no_pool == 950.0

            # Verify points deducted
            assert user.points == 0

            # Verify market liquidity updated
            assert market.yes_pool == 1050.0
            assert market.no_pool == 950.0

            # Verify prediction created
            assert prediction.user_id == user.id
            assert prediction.market_id == market.id
            assert prediction.stake == 100
            assert prediction.outcome is True
            assert prediction.shares == 0.5
            assert prediction.price == 0.525
            assert prediction.used_liquidity_buffer is False

    @patch('app.services.prediction_service.AMMService', autospec=True)
    @patch('app.services.prediction_service.XPService', autospec=True)
    def test_place_prediction_buffer(self, mock_xp_service, mock_amm_service, test_app, test_session):
        """
        Test placing a prediction using liquidity buffer:
        - Deducts buffer
        - Updates market liquidity
        - Creates prediction record
        """
        with test_app.app_context():
            # Create user with buffer
            user = User(username="test_user", email="test@example.com")
            user.liquidity_buffer_deposit = 100.0
            test_session.add(user)
            test_session.commit()
            
            # Create market
            market = Market(
                title="Test Market",
                description="Is this a test market?",
                resolution_date=datetime.utcnow() + timedelta(days=30),
                resolution_method="manual",
                yes_pool=1000.0,
                no_pool=1000.0,
                liquidity_pool=2000.0
            )
            test_session.add(market)
            test_session.commit()
            
            # Create liquidity pool
            liquidity_pool = LiquidityPool(
                contract_id=market.id,
                max_liquidity=2000.0,
                current_liquidity=2000.0
            )
            test_session.add(liquidity_pool)
            test_session.commit()
            
            # Set market relationship
            market.market_liquidity_pool = liquidity_pool
            test_session.commit()
            
            # Mock AMM service response
            mock_amm_service.calculate_share_allocation.return_value = {
                'shares': 0.5,
                'yes_liquidity': 1100.0,
                'no_liquidity': 900.0,
                'price': 1.0,
                'slippage': 0.01
            }

            # Mock XP service response
            mock_xp_service.award_prediction_xp.return_value = None

            # Mock market event logging
            # mock_log_prediction.return_value = None

            # Place prediction with buffer
            with db.session.no_autoflush:
                prediction = PredictionService.place_prediction(
                    user=user,
                    market=market,
                    stake=100,
                    outcome=True,
                    use_liquidity_buffer=True
                )

            # Verify buffer deducted
            assert user.liquidity_buffer_deposit == 900

            # Verify market liquidity updated
            assert market.yes_pool == 1100.0
            assert market.no_pool == 900.0
            assert market.liquidity_pool == 2000.0

            # Verify prediction created
            assert prediction.user_id == user.id
            assert prediction.market_id == market.id
            assert prediction.stake == 100
            assert prediction.outcome is True
            assert prediction.shares == 0.5
            assert prediction.price == 1.0
            assert prediction.used_liquidity_buffer is True

    @patch('app.services.prediction_service.XPService', autospec=True)
    def test_resolve_prediction_correct(self, mock_xp_service, test_app, test_session):
        """
        Test resolving prediction with correct outcome.
        """
        with test_app.app_context():
            # Create user first
            user = User(username="test_user", email="test@example.com")
            test_session.add(user)
            test_session.commit()

            # Update user points and buffer
            user.points = 1000
            user.liquidity_buffer_deposit = 1000
            user.xp = 0
            test_session.commit()

            # Create prediction
            prediction = Prediction(
                user_id=1,
                market_id=1,
                stake=100,
                outcome=True,
                shares=0.5,
                shares_purchased=0.5,
                price=1.0
            )
            test_session.add(prediction)
            test_session.commit()
    
            # Resolve market
            market = Market(
                title="Test Market",
                description="Is this a test market?",
                resolution_date=datetime.utcnow() + timedelta(days=30),
                resolution_method="manual",
                yes_pool=1000.0,
                no_pool=1000.0,
                liquidity_pool=2000.0,
                resolved=True,
                resolved_outcome="YES",
                resolved_at=datetime.utcnow()
            )
            test_session.add(market)
            test_session.commit()
    
            # Mock XP service response
            mock_xp_service.award_prediction_xp.return_value = 100
            
            # Resolve prediction
            PredictionService.resolve_prediction(prediction, market)
            
            # Verify points and XP were awarded
            user = test_session.get(User, 1)
            assert user.points > 1000
            assert prediction.awarded_points > 0
            assert prediction.awarded_xp == 100
            assert user.xp == 100

    @patch('app.services.prediction_service.XPService', autospec=True)
    def test_resolve_prediction_incorrect(self, mock_xp_service, test_app, test_session):
        """
        Test resolving prediction with incorrect outcome.
        """
        with test_app.app_context():
            # Create user first
            user = User(username="test_user", email="test@example.com")
            test_session.add(user)
            test_session.commit()

            # Update user points and buffer
            user.points = 1000
            user.liquidity_buffer_deposit = 1000
            user.xp = 0
            test_session.commit()

            # Create prediction
            prediction = Prediction(
                user_id=1,
                market_id=1,
                stake=100,
                outcome=True,
                shares=0.5,
                shares_purchased=0.5,
                price=1.0
            )
            test_session.add(prediction)
            test_session.commit()
    
            # Resolve market with incorrect outcome
            market = Market(
                title="Test Market",
                description="Is this a test market?",
                resolution_date=datetime.utcnow() + timedelta(days=30),
                resolution_method="manual",
                yes_pool=1000.0,
                no_pool=1000.0,
                liquidity_pool=2000.0,
                resolved=True,
                resolved_outcome="NO",
                resolved_at=datetime.utcnow()
            )
            test_session.add(market)
            test_session.commit()
    
            # Resolve prediction
            PredictionService.resolve_prediction(prediction, market)
            
            # Verify no points or XP were awarded
            user = test_session.get(User, 1)
            assert user.points == 1000
            assert prediction.awarded_points == 0
            assert prediction.awarded_xp == 0
            assert user.xp == 0

    @patch('app.services.prediction_service.AMMService', autospec=True)
    @patch('app.services.prediction_service.XPService', autospec=True)
    def test_place_prediction_insufficient_points(self, mock_xp_service, mock_amm_service, test_app, test_user, test_market):
        """
        Test placing prediction with insufficient points.
        """
        with test_app.app_context():
            # Set insufficient points
            test_user.points = 50
            db.session.commit()

            # Mock AMM service response
            mock_amm_service.calculate_share_allocation.return_value = {
                'shares': 0.5,
                'yes_liquidity': 1050.0,
                'no_liquidity': 950.0,
                'price': 0.525
            }

            # Mock XP service response
            mock_xp_service.award_prediction_xp.return_value = None

            # Mock market event logging
            # mock_log_prediction.return_value = None

            # Test prediction with insufficient points
            with pytest.raises(ValueError) as exc_info:
                with db.session.no_autoflush:
                    PredictionService.place_prediction(
                        user=test_user,
                        market=test_market,
                        stake=100,
                        outcome=True
                    )

            assert str(exc_info.value) == "Insufficient points"

            # Test prediction with insufficient buffer
            with pytest.raises(ValueError) as exc_info:
                with db.session.no_autoflush:
                    PredictionService.place_prediction(
                        user=test_user,
                        market=test_market,
                        stake=100,
                        outcome=True,
                        use_liquidity_buffer=True
                    )

            assert str(exc_info.value) == "Insufficient liquidity buffer balance"

    @patch('app.services.prediction_service.AMMService', autospec=True)
    @patch('app.services.prediction_service.XPService', autospec=True)
    def test_place_prediction_insufficient_buffer(self, mock_xp_service, mock_amm_service, test_app, test_user, test_market):
        """
        Test placing prediction with insufficient buffer.
        """
        with test_app.app_context():
            # Set insufficient buffer
            test_user.liquidity_buffer_deposit = 50.0
            db.session.commit()

            # Mock AMM service response
            mock_amm_service.calculate_share_allocation.return_value = {
                'shares': 0.5,
                'yes_liquidity': 1100.0,
                'no_liquidity': 900.0,
                'price': 1.0,
                'slippage': 0.01
            }

            # Mock XP service response
            mock_xp_service.award_prediction_xp.return_value = None

            # Mock market event logging
            # mock_log_prediction.return_value = None

            # Test prediction with insufficient buffer
            with pytest.raises(ValueError) as exc_info:
                with db.session.no_autoflush:
                    PredictionService.place_prediction(
                        user=test_user,
                        market=test_market,
                        stake=100,
                        outcome=True,
                        use_liquidity_buffer=True
                    )

            assert str(exc_info.value) == "Insufficient liquidity buffer balance"

    @patch('app.services.prediction_service.AMMService', autospec=True)
    @patch('app.services.prediction_service.XPService', autospec=True)
    def test_place_prediction_insufficient_balance(self, mock_xp_service, mock_amm_service, test_app, test_user, test_market):
        """
        Test placing prediction with insufficient balance.
        """
        with test_app.app_context():
            # Set insufficient balance
            test_user.liquidity_buffer_deposit = 0.0
            db.session.commit()

            # Mock AMM service response
            mock_amm_service.calculate_share_allocation.return_value = {
                'shares': 0.5,
                'yes_liquidity': 1100.0,
                'no_liquidity': 900.0,
                'price': 1.0,
                'slippage': 0.01
            }

            # Mock XP service response
            mock_xp_service.award_prediction_xp.return_value = None

            # Mock market event logging
            # mock_log_prediction.return_value = None

            # Test prediction with insufficient buffer
            with pytest.raises(ValueError) as exc_info:
                with db.session.no_autoflush:
                    PredictionService.place_prediction(
                        user=test_user,
                        market=test_market,
                        stake=100,
                        outcome=True,
                        use_liquidity_buffer=True
                    )

            assert str(exc_info.value) == "Insufficient liquidity buffer balance"

    @patch('app.services.prediction_service.AMMService', autospec=True)
    @patch('app.services.prediction_service.XPService', autospec=True)
    def test_resolve_prediction_unresolved_market(self, mock_xp_service, mock_amm_service, test_app, test_session):
        """
        Test resolving prediction on unresolved market.
        """
        with test_app.app_context():
            # Create prediction
            prediction = Prediction(
                user_id=1,
                market_id=1,
                stake=100,
                outcome=True,
                shares=0.5,
                shares_purchased=0.5,
                price=1.0
            )
            test_session.add(prediction)
            test_session.commit()
            
            # Create market
            market = Market(
                title="Test Market",
                description="Is this a test market?",
                resolution_date=datetime.utcnow() + timedelta(days=30),
                resolution_method="manual",
                yes_pool=1000.0,
                no_pool=1000.0,
                liquidity_pool=2000.0
            )
            test_session.add(market)
            test_session.commit()
            
            # Resolve prediction should fail
            with pytest.raises(ValueError):
                PredictionService.resolve_prediction(prediction, market)

            # Verify prediction not resolved
            assert prediction.resolved_at is None
            assert prediction.awarded_points is None

    @patch('app.models.MarketEvent.log_prediction')
    def test_place_prediction_zero_stake(self, mock_log_prediction, test_app, test_user, test_market):
        """
        Test placing prediction with zero stake.
        """
        with test_app.app_context():
            with pytest.raises(ValueError) as exc_info:
                with db.session.no_autoflush:
                    PredictionService.place_prediction(
                        user=test_user,
                        market=test_market,
                        stake=0,
                        outcome=True
                    )

            assert str(exc_info.value) == "Stake must be positive"

    @patch('app.models.MarketEvent.log_prediction')
    def test_place_prediction_negative_stake(self, mock_log_prediction, test_app, test_user, test_market):
        """
        Test placing prediction with negative stake.
        """
        with test_app.app_context():
            with pytest.raises(ValueError) as exc_info:
                with db.session.no_autoflush:
                    PredictionService.place_prediction(
                        user=test_user,
                        market=test_market,
                        stake=-100,
                        outcome=True
                    )

            assert str(exc_info.value) == "Stake must be positive"

    @patch('app.models.MarketEvent.log_prediction')
    def test_place_prediction_invalid_outcome(self, mock_log_prediction, test_app, test_user, test_market):
        """
        Test placing prediction with invalid outcome.
        """
        with test_app.app_context():
            with pytest.raises(ValueError) as exc_info:
                with db.session.no_autoflush:
                    PredictionService.place_prediction(
                        user=test_user,
                        market=test_market,
                        stake=100,
                        outcome="INVALID"
                    )

            assert str(exc_info.value) == "Outcome must be True or False"

    @patch('app.services.prediction_service.AMMService', autospec=True)
    @patch('app.services.prediction_service.XPService', autospec=True)
    def test_place_prediction_buffer(self, mock_xp_service, mock_amm_service, test_app, test_session):
        """
        Test placing a prediction using liquidity buffer:
        - Deducts buffer
        - Updates market liquidity
        - Creates prediction record
        """
        with test_app.app_context():
            # Create user with buffer
            user = User(username="test_user", email="test@example.com")
            user.liquidity_buffer_deposit = 100.0
            test_session.add(user)
            test_session.commit()
            
            # Create market
            market = Market(
                title="Test Market",
                description="Is this a test market?",
                resolution_date=datetime.utcnow() + timedelta(days=30),
                resolution_method="manual",
                yes_pool=1000.0,
                no_pool=1000.0,
                liquidity_pool=2000.0
            )
            test_session.add(market)
            test_session.commit()
            
            # Create liquidity pool
            liquidity_pool = LiquidityPool(
                contract_id=market.id,
                max_liquidity=2000.0,
                current_liquidity=2000.0
            )
            test_session.add(liquidity_pool)
            test_session.commit()
            
            # Set market relationship
            market.market_liquidity_pool = liquidity_pool
            test_session.commit()
            
            # Mock AMM service response
            mock_amm_service.calculate_share_allocation.return_value = {
                'shares': 0.5,
                'yes_liquidity': 1050.0,
                'no_liquidity': 950.0,
                'price': 0.525
            }
            
            # Place prediction
            with test_session.no_autoflush:
                prediction = PredictionService.place_prediction(
                    user=user,
                    market=market,
                    stake=100,
                    outcome=True,
                    use_liquidity_buffer=True
                )
                
                # Verify buffer was deducted
                assert user.liquidity_buffer_deposit == 0
                
                # Verify prediction was created
                assert prediction is not None
                assert prediction.outcome is True

    def test_place_prediction_insufficient_points(self, test_app, test_session):
        """
        Test placing prediction with insufficient points.
        """
        with test_app.app_context():
            # Create user with insufficient points
            user = User(username="test_user", email="test@example.com")
            user.points = 50
            user.liquidity_buffer_deposit = 100.0
            test_session.add(user)
            test_session.commit()
            
            # Create market
            market = Market(
                title="Test Market",
                description="Is this a test market?",
                resolution_date=datetime.utcnow() + timedelta(days=30),
                resolution_method="manual",
                yes_pool=1000.0,
                no_pool=1000.0,
                liquidity_pool=2000.0
            )
            test_session.add(market)
            test_session.commit()
            
            # Place prediction with insufficient points
            with pytest.raises(ValueError):
                PredictionService.place_prediction(
                    user=user,
                    market=market,
                    stake=100,
                    outcome=True
                )

    def test_place_prediction_insufficient_buffer(self, test_app, test_session):
        """
        Test placing prediction with insufficient buffer.
        """
        with test_app.app_context():
            # Create user with insufficient buffer
            user = User(username="test_user", email="test@example.com")
            user.points = 100
            user.liquidity_buffer_deposit = 50.0
            test_session.add(user)
            test_session.commit()
            
            # Create market
            market = Market(
                title="Test Market",
                description="Is this a test market?",
                resolution_date=datetime.utcnow() + timedelta(days=30),
                resolution_method="manual",
                yes_pool=1000.0,
                no_pool=1000.0,
                liquidity_pool=2000.0
            )
            test_session.add(market)
            test_session.commit()
            
            # Place prediction with insufficient buffer
            with pytest.raises(ValueError):
                PredictionService.place_prediction(
                    user=user,
                    market=market,
                    stake=100,
                    outcome=True,
                    use_liquidity_buffer=True
                )

    def test_place_prediction_insufficient_balance(self, test_app, test_session):
        """
        Test placing prediction with insufficient balance.
        """
        with test_app.app_context():
            # Create user with insufficient balance
            user = User(username="test_user", email="test@example.com")
            user.points = 0
            user.liquidity_buffer_deposit = 0.0
            test_session.add(user)
            test_session.commit()
            
            # Create market
            market = Market(
                title="Test Market",
                description="Is this a test market?",
                resolution_date=datetime.utcnow() + timedelta(days=30),
                resolution_method="manual",
                yes_pool=1000.0,
                no_pool=1000.0,
                liquidity_pool=2000.0
            )
            test_session.add(market)
            test_session.commit()
            
            # Place prediction with insufficient balance
            with pytest.raises(ValueError):
                PredictionService.place_prediction(
                    user=user,
                    market=market,
                    stake=100,
                    outcome=True
                )

    @patch('app.services.prediction_service.XPService', autospec=True)
    def test_resolve_prediction_correct(self, mock_xp_service, test_app, test_session):
        """
        Test resolving prediction with correct outcome.
        """
        with test_app.app_context():
            # Create user first
            user = User(username="test_user", email="test@example.com")
            test_session.add(user)
            test_session.commit()

            # Update user points and buffer
            user.points = 1000
            user.liquidity_buffer_deposit = 1000
            user.xp = 0
            test_session.commit()

            # Create prediction
            prediction = Prediction(
                user_id=1,
                market_id=1,
                stake=100,
                outcome=True,
                shares=0.5,
                shares_purchased=0.5,
                price=1.0
            )
            test_session.add(prediction)
            test_session.commit()
            
            # Resolve market
            market = Market(
                title="Test Market",
                description="Is this a test market?",
                resolution_date=datetime.utcnow() + timedelta(days=30),
                resolution_method="manual",
                yes_pool=1000.0,
                no_pool=1000.0,
                liquidity_pool=2000.0,
                resolved=True,
                resolved_outcome="YES",
                resolved_at=datetime.utcnow()
            )
            test_session.add(market)
            test_session.commit()
            
            # Mock XP service response
            mock_xp_service.award_prediction_xp.return_value = 100
            
            # Resolve prediction
            PredictionService.resolve_prediction(prediction, market)
            
            # Verify points awarded
            user = test_session.get(User, 1)
            assert user.points > 1000
            assert prediction.awarded_points > 0
            assert prediction.awarded_xp > 0

    @patch('app.services.prediction_service.XPService', autospec=True)
    def test_resolve_prediction_incorrect(self, mock_xp_service, test_app, test_session):
        """
        Test resolving prediction with incorrect outcome.
        """
        with test_app.app_context():
            # Create user first
            user = User(username="test_user", email="test@example.com")
            test_session.add(user)
            test_session.commit()

            # Update user points and buffer
            user.points = 1000
            user.liquidity_buffer_deposit = 1000
            user.xp = 0
            test_session.commit()

            # Create prediction
            prediction = Prediction(
                user_id=1,
                market_id=1,
                stake=100,
                outcome=True,
                shares=0.5,
                shares_purchased=0.5,
                price=1.0
            )
            test_session.add(prediction)
            test_session.commit()
            
            # Resolve market with incorrect outcome
            market = Market(
                title="Test Market",
                description="Is this a test market?",
                resolution_date=datetime.utcnow() + timedelta(days=30),
                resolution_method="manual",
                yes_pool=1000.0,
                no_pool=1000.0,
                liquidity_pool=2000.0,
                resolved=True,
                resolved_outcome="NO",
                resolved_at=datetime.utcnow()
            )
            test_session.add(market)
            test_session.commit()
            
            # Resolve prediction
            PredictionService.resolve_prediction(prediction, market)
            
            # Verify no points awarded
            user = test_session.get(User, 1)
            assert user.points == 1000
            assert prediction.awarded_points == 0
            assert prediction.awarded_xp == 0

    def test_resolve_prediction_unresolved_market(self, test_app, test_session):
        """
        Test resolving prediction on unresolved market.
        """
        with test_app.app_context():
            # Create prediction
            prediction = Prediction(
                user_id=1,
                market_id=1,
                stake=100,
                outcome=True,
                shares=0.5,
                shares_purchased=0.5,
                price=1.0
            )
            test_session.add(prediction)
            test_session.commit()
            
            # Create unresolved market
            market = Market(
                title="Test Market",
                description="Is this a test market?",
                resolution_date=datetime.utcnow() + timedelta(days=30),
                resolution_method="manual",
                yes_pool=1000.0,
                no_pool=1000.0,
                liquidity_pool=2000.0,
                resolved=False
            )
            test_session.add(market)
            test_session.commit()
            
            # Resolve prediction should fail
            with pytest.raises(ValueError):
                PredictionService.resolve_prediction(prediction, market)

            # Verify prediction not resolved
            assert prediction.resolved_at is None
            assert prediction.awarded_points is None

    def test_place_prediction_zero_stake(self, test_app, test_session):
        """
        Test placing prediction with zero stake.
        """
        with test_app.app_context():
            # Create user
            user = User(username="test_user", email="test@example.com")
            user.liquidity_buffer_deposit = 100.0
            test_session.add(user)
            test_session.commit()
            
            # Create market
            market = Market(
                title="Test Market",
                description="Is this a test market?",
                resolution_date=datetime.utcnow() + timedelta(days=30),
                resolution_method="manual",
                yes_pool=1000.0,
                no_pool=1000.0,
                liquidity_pool=2000.0
            )
            test_session.add(market)
            test_session.commit()
            
            # Place prediction with zero stake
            with pytest.raises(ValueError):
                PredictionService.place_prediction(
                    user=user,
                    market=market,
                    stake=0,
                    outcome=True
                )

    def test_place_prediction_negative_stake(self, test_app, test_session):
        """
        Test placing prediction with negative stake.
        """
        with test_app.app_context():
            # Create user
            user = User(username="test_user", email="test@example.com")
            user.liquidity_buffer_deposit = 100.0
            test_session.add(user)
            test_session.commit()
            
            # Create market
            market = Market(
                title="Test Market",
                description="Is this a test market?",
                resolution_date=datetime.utcnow() + timedelta(days=30),
                resolution_method="manual",
                yes_pool=1000.0,
                no_pool=1000.0,
                liquidity_pool=2000.0
            )
            test_session.add(market)
            test_session.commit()
            
            # Place prediction with negative stake
            with pytest.raises(ValueError):
                PredictionService.place_prediction(
                    user=user,
                    market=market,
                    stake=-100,
                    outcome=True
                )

    def test_place_prediction_invalid_outcome(self, test_app, test_session):
        """
        Test placing prediction with invalid outcome.
        """
        with test_app.app_context():
            # Create user
            user = User(username="test_user", email="test@example.com")
            user.liquidity_buffer_deposit = 100.0
            test_session.add(user)
            test_session.commit()
            
            # Create market
            market = Market(
                title="Test Market",
                description="Is this a test market?",
                resolution_date=datetime.utcnow() + timedelta(days=30),
                resolution_method="manual",
                yes_pool=1000.0,
                no_pool=1000.0,
                liquidity_pool=2000.0
            )
            test_session.add(market)
            test_session.commit()
            
            # Place prediction with invalid outcome
            with pytest.raises(ValueError):
                PredictionService.place_prediction(
                    user=user,
                    market=market,
                    stake=100,
                    outcome="INVALID"
                )
