# Test Report
Run Time: 2025-07-03 13:34:51

## Summary
- Total tests: 6
- Passed: 2
- Failed: 4

## Failed Tests:
### tests/test_xp_service.py
```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.1, pluggy-1.6.0 -- /Users/georgeflinn/PM4/venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/georgeflinn/PM4
plugins: anyio-4.9.0
collecting ... collected 5 items

tests/test_xp_service.py::test_award_prediction_xp_success PASSED        [ 20%]
tests/test_xp_service.py::test_award_prediction_xp_failure ERROR         [ 40%]
tests/test_xp_service.py::test_check_in_streak_reset PASSED              [ 60%]
tests/test_xp_service.py::test_check_in_streak_continue PASSED           [ 80%]
tests/test_xp_service.py::test_check_in_same_day_no_change PASSED        [100%]

==================================== ERRORS ====================================
______________ ERROR at setup of test_award_prediction_xp_failure ______________

session = <sqlalchemy.orm.scoping.scoped_session object at 0x1059dfd60>

    @pytest.fixture
    def user_with_xp(session):
>       user = User(username="test", email="test@example.com", xp=50, predictions_count=2, successful_predictions=1)
E       TypeError: __init__() got an unexpected keyword argument 'xp'

tests/test_xp_service.py:36: TypeError
---------------------------- Captured stdout setup -----------------------------
Registered tables after init_app: dict_keys(['user', 'leagues', 'league_members', 'badges', 'user_badges', 'contract_drafts', 'published_contracts', 'market_event', 'market', 'platform_wallet', 'prediction', 'news_source', 'news_headline', 'liquidity_pools', 'liquidity_providers', 'user_ledger', 'amm_markets'])
=========================== short test summary info ============================
ERROR tests/test_xp_service.py::test_award_prediction_xp_failure - TypeError:...
========================== 4 passed, 1 error in 0.14s ==========================

```
### tests/test_amm_service.py
```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.1, pluggy-1.6.0 -- /Users/georgeflinn/PM4/venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/georgeflinn/PM4
plugins: anyio-4.9.0
collecting ... collected 13 items

tests/test_amm_service.py::TestAMMCore::test_get_current_odds_balanced PASSED [  7%]
tests/test_amm_service.py::TestAMMCore::test_share_allocation_small_stake_yes FAILED [ 15%]
tests/test_amm_service.py::TestAMMCore::test_share_allocation_large_stake_no FAILED [ 23%]
tests/test_amm_service.py::TestAMMCore::test_constant_product_invariance FAILED [ 30%]
tests/test_amm_service.py::TestAMMCore::test_odds_update_accuracy FAILED [ 38%]
tests/test_amm_service.py::TestAMMCore::test_zero_liquidity_error PASSED [ 46%]
tests/test_amm_service.py::TestAMMCore::test_tiny_liquidity FAILED       [ 53%]
tests/test_amm_service.py::TestAMMCore::test_large_stake_impact FAILED   [ 61%]
tests/test_amm_service.py::TestAMMService::test_calculate_share_allocation_no FAILED [ 69%]
tests/test_amm_service.py::TestAMMService::test_calculate_share_allocation_yes FAILED [ 76%]
tests/test_amm_service.py::TestAMMService::test_get_current_odds PASSED  [ 84%]
tests/test_amm_service.py::TestAMMService::test_invalid_outcome PASSED   [ 92%]
tests/test_amm_service.py::TestAMMService::test_negative_liquidity FAILED [100%]

=================================== FAILURES ===================================
______________ TestAMMCore.test_share_allocation_small_stake_yes _______________

self = <test_amm_service.TestAMMCore object at 0x10403b1c0>
balanced_pool = <test_amm_service.MockLiquidityPool object at 0x104045400>

    def test_share_allocation_small_stake_yes(self, balanced_pool):
        """Test YES-side share allocation for small stake"""
        initial_k = balanced_pool.yes_liquidity * balanced_pool.no_liquidity
    
        # Calculate allocation
>       result = AMMService.calculate_share_allocation(
            yes_liquidity=balanced_pool.yes_liquidity,
            no_liquidity=balanced_pool.no_liquidity,
            stake=10.0,
            outcome="YES"
        )

tests/test_amm_service.py:53: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

yes_liquidity = 100.0, no_liquidity = 100.0, stake = 10.0, outcome = 'YES'

    @staticmethod
    def calculate_share_allocation(yes_liquidity: float, no_liquidity: float, stake: float, outcome: bool) -> Dict[str, Any]:
        """
        Given a stake and outcome, calculate new liquidity values and shares allocated.
        Enforces the constant product invariant: x * y = k
    
        Args:
            yes_liquidity: Current YES pool liquidity
            no_liquidity: Current NO pool liquidity
            stake: Amount of stake to add
            outcome: True for YES position, False for NO position
    
        Returns:
            dict: Dictionary containing:
                - shares: Number of shares allocated
                - yes_liquidity: New YES pool liquidity
                - no_liquidity: New NO pool liquidity
                - price: Price per share
        """
        if not isinstance(outcome, bool):
>           raise ValueError("Outcome must be a boolean value (True for YES, False for NO)")
E           ValueError: Outcome must be a boolean value (True for YES, False for NO)

app/services/amm_service.py:57: ValueError
_______________ TestAMMCore.test_share_allocation_large_stake_no _______________

self = <test_amm_service.TestAMMCore object at 0x10403b3a0>
balanced_pool = <test_amm_service.MockLiquidityPool object at 0x10409cc40>

    def test_share_allocation_large_stake_no(self, balanced_pool):
        """Test NO-side share allocation for large stake"""
        initial_k = balanced_pool.yes_liquidity * balanced_pool.no_liquidity
    
        # Calculate allocation
>       result = AMMService.calculate_share_allocation(
            yes_liquidity=balanced_pool.yes_liquidity,
            no_liquidity=balanced_pool.no_liquidity,
            stake=500.0,
            outcome="NO"
        )

tests/test_amm_service.py:73: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

yes_liquidity = 100.0, no_liquidity = 100.0, stake = 500.0, outcome = 'NO'

    @staticmethod
    def calculate_share_allocation(yes_liquidity: float, no_liquidity: float, stake: float, outcome: bool) -> Dict[str, Any]:
        """
        Given a stake and outcome, calculate new liquidity values and shares allocated.
        Enforces the constant product invariant: x * y = k
    
        Args:
            yes_liquidity: Current YES pool liquidity
            no_liquidity: Current NO pool liquidity
            stake: Amount of stake to add
            outcome: True for YES position, False for NO position
    
        Returns:
            dict: Dictionary containing:
                - shares: Number of shares allocated
                - yes_liquidity: New YES pool liquidity
                - no_liquidity: New NO pool liquidity
                - price: Price per share
        """
        if not isinstance(outcome, bool):
>           raise ValueError("Outcome must be a boolean value (True for YES, False for NO)")
E           ValueError: Outcome must be a boolean value (True for YES, False for NO)

app/services/amm_service.py:57: ValueError
_________________ TestAMMCore.test_constant_product_invariance _________________

self = <test_amm_service.TestAMMCore object at 0x10403b580>
balanced_pool = <test_amm_service.MockLiquidityPool object at 0x1040e7b80>

    def test_constant_product_invariance(self, balanced_pool):
        """Test AMM constant product formula invariance"""
        initial_k = balanced_pool.yes_liquidity * balanced_pool.no_liquidity
    
        # Make multiple trades
        yes_liquidity = balanced_pool.yes_liquidity
        no_liquidity = balanced_pool.no_liquidity
    
        for stake in [10.0, 20.0, 30.0]:
>           result = AMMService.calculate_share_allocation(
                yes_liquidity=yes_liquidity,
                no_liquidity=no_liquidity,
                stake=stake,
                outcome="YES"
            )

tests/test_amm_service.py:97: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

yes_liquidity = 100.0, no_liquidity = 100.0, stake = 10.0, outcome = 'YES'

    @staticmethod
    def calculate_share_allocation(yes_liquidity: float, no_liquidity: float, stake: float, outcome: bool) -> Dict[str, Any]:
        """
        Given a stake and outcome, calculate new liquidity values and shares allocated.
        Enforces the constant product invariant: x * y = k
    
        Args:
            yes_liquidity: Current YES pool liquidity
            no_liquidity: Current NO pool liquidity
            stake: Amount of stake to add
            outcome: True for YES position, False for NO position
    
        Returns:
            dict: Dictionary containing:
                - shares: Number of shares allocated
                - yes_liquidity: New YES pool liquidity
                - no_liquidity: New NO pool liquidity
                - price: Price per share
        """
        if not isinstance(outcome, bool):
>           raise ValueError("Outcome must be a boolean value (True for YES, False for NO)")
E           ValueError: Outcome must be a boolean value (True for YES, False for NO)

app/services/amm_service.py:57: ValueError
____________________ TestAMMCore.test_odds_update_accuracy _____________________

self = <test_amm_service.TestAMMCore object at 0x10403b3d0>
balanced_pool = <test_amm_service.MockLiquidityPool object at 0x10403baf0>

    def test_odds_update_accuracy(self, balanced_pool):
        """Test accuracy of odds updates after trades"""
        # Initial odds should be 0.5
        odds = AMMService.get_current_odds(
            yes_liquidity=balanced_pool.yes_liquidity,
            no_liquidity=balanced_pool.no_liquidity
        )
        assert odds['yes'] == pytest.approx(0.5)
        assert odds['no'] == pytest.approx(0.5)
    
        # Make a trade
>       result = AMMService.calculate_share_allocation(
            yes_liquidity=balanced_pool.yes_liquidity,
            no_liquidity=balanced_pool.no_liquidity,
            stake=100.0,
            outcome="YES"
        )

tests/test_amm_service.py:121: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

yes_liquidity = 100.0, no_liquidity = 100.0, stake = 100.0, outcome = 'YES'

    @staticmethod
    def calculate_share_allocation(yes_liquidity: float, no_liquidity: float, stake: float, outcome: bool) -> Dict[str, Any]:
        """
        Given a stake and outcome, calculate new liquidity values and shares allocated.
        Enforces the constant product invariant: x * y = k
    
        Args:
            yes_liquidity: Current YES pool liquidity
            no_liquidity: Current NO pool liquidity
            stake: Amount of stake to add
            outcome: True for YES position, False for NO position
    
        Returns:
            dict: Dictionary containing:
                - shares: Number of shares allocated
                - yes_liquidity: New YES pool liquidity
                - no_liquidity: New NO pool liquidity
                - price: Price per share
        """
        if not isinstance(outcome, bool):
>           raise ValueError("Outcome must be a boolean value (True for YES, False for NO)")
E           ValueError: Outcome must be a boolean value (True for YES, False for NO)

app/services/amm_service.py:57: ValueError
_______________________ TestAMMCore.test_tiny_liquidity ________________________

self = <test_amm_service.TestAMMCore object at 0x10403b8e0>
tiny_pool = <test_amm_service.MockLiquidityPool object at 0x1040f7a60>

    def test_tiny_liquidity(self, tiny_pool):
        """Test behavior with very small liquidity amounts"""
        initial_k = tiny_pool.yes_liquidity * tiny_pool.no_liquidity
    
        # Calculate allocation
>       result = AMMService.calculate_share_allocation(
            yes_liquidity=tiny_pool.yes_liquidity,
            no_liquidity=tiny_pool.no_liquidity,
            stake=1e-7,
            outcome="YES"
        )

tests/test_amm_service.py:151: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

yes_liquidity = 1e-06, no_liquidity = 1e-06, stake = 1e-07, outcome = 'YES'

    @staticmethod
    def calculate_share_allocation(yes_liquidity: float, no_liquidity: float, stake: float, outcome: bool) -> Dict[str, Any]:
        """
        Given a stake and outcome, calculate new liquidity values and shares allocated.
        Enforces the constant product invariant: x * y = k
    
        Args:
            yes_liquidity: Current YES pool liquidity
            no_liquidity: Current NO pool liquidity
            stake: Amount of stake to add
            outcome: True for YES position, False for NO position
    
        Returns:
            dict: Dictionary containing:
                - shares: Number of shares allocated
                - yes_liquidity: New YES pool liquidity
                - no_liquidity: New NO pool liquidity
                - price: Price per share
        """
        if not isinstance(outcome, bool):
>           raise ValueError("Outcome must be a boolean value (True for YES, False for NO)")
E           ValueError: Outcome must be a boolean value (True for YES, False for NO)

app/services/amm_service.py:57: ValueError
_____________________ TestAMMCore.test_large_stake_impact ______________________

self = <test_amm_service.TestAMMCore object at 0x10403bac0>
balanced_pool = <test_amm_service.MockLiquidityPool object at 0x104045e80>

    def test_large_stake_impact(self, balanced_pool):
        """Test impact of very large stake on pool"""
        initial_k = balanced_pool.yes_liquidity * balanced_pool.no_liquidity
    
        # Calculate allocation
>       result = AMMService.calculate_share_allocation(
            yes_liquidity=balanced_pool.yes_liquidity,
            no_liquidity=balanced_pool.no_liquidity,
            stake=10000.0,
            outcome="YES"
        )

tests/test_amm_service.py:174: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

yes_liquidity = 100.0, no_liquidity = 100.0, stake = 10000.0, outcome = 'YES'

    @staticmethod
    def calculate_share_allocation(yes_liquidity: float, no_liquidity: float, stake: float, outcome: bool) -> Dict[str, Any]:
        """
        Given a stake and outcome, calculate new liquidity values and shares allocated.
        Enforces the constant product invariant: x * y = k
    
        Args:
            yes_liquidity: Current YES pool liquidity
            no_liquidity: Current NO pool liquidity
            stake: Amount of stake to add
            outcome: True for YES position, False for NO position
    
        Returns:
            dict: Dictionary containing:
                - shares: Number of shares allocated
                - yes_liquidity: New YES pool liquidity
                - no_liquidity: New NO pool liquidity
                - price: Price per share
        """
        if not isinstance(outcome, bool):
>           raise ValueError("Outcome must be a boolean value (True for YES, False for NO)")
E           ValueError: Outcome must be a boolean value (True for YES, False for NO)

app/services/amm_service.py:57: ValueError
______________ TestAMMService.test_calculate_share_allocation_no _______________

self = <test_amm_service.TestAMMService testMethod=test_calculate_share_allocation_no>

    def test_calculate_share_allocation_no(self):
        # Test NO allocation with small stake
>       result = AMMService.calculate_share_allocation(100, 100, 10, "NO")

tests/test_amm_service.py:225: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

yes_liquidity = 100, no_liquidity = 100, stake = 10, outcome = 'NO'

    @staticmethod
    def calculate_share_allocation(yes_liquidity: float, no_liquidity: float, stake: float, outcome: bool) -> Dict[str, Any]:
        """
        Given a stake and outcome, calculate new liquidity values and shares allocated.
        Enforces the constant product invariant: x * y = k
    
        Args:
            yes_liquidity: Current YES pool liquidity
            no_liquidity: Current NO pool liquidity
            stake: Amount of stake to add
            outcome: True for YES position, False for NO position
    
        Returns:
            dict: Dictionary containing:
                - shares: Number of shares allocated
                - yes_liquidity: New YES pool liquidity
                - no_liquidity: New NO pool liquidity
                - price: Price per share
        """
        if not isinstance(outcome, bool):
>           raise ValueError("Outcome must be a boolean value (True for YES, False for NO)")
E           ValueError: Outcome must be a boolean value (True for YES, False for NO)

app/services/amm_service.py:57: ValueError
______________ TestAMMService.test_calculate_share_allocation_yes ______________

self = <test_amm_service.TestAMMService testMethod=test_calculate_share_allocation_yes>

    def test_calculate_share_allocation_yes(self):
        # Test YES allocation with small stake
>       result = AMMService.calculate_share_allocation(100, 100, 10, "YES")

tests/test_amm_service.py:210: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

yes_liquidity = 100, no_liquidity = 100, stake = 10, outcome = 'YES'

    @staticmethod
    def calculate_share_allocation(yes_liquidity: float, no_liquidity: float, stake: float, outcome: bool) -> Dict[str, Any]:
        """
        Given a stake and outcome, calculate new liquidity values and shares allocated.
        Enforces the constant product invariant: x * y = k
    
        Args:
            yes_liquidity: Current YES pool liquidity
            no_liquidity: Current NO pool liquidity
            stake: Amount of stake to add
            outcome: True for YES position, False for NO position
    
        Returns:
            dict: Dictionary containing:
                - shares: Number of shares allocated
                - yes_liquidity: New YES pool liquidity
                - no_liquidity: New NO pool liquidity
                - price: Price per share
        """
        if not isinstance(outcome, bool):
>           raise ValueError("Outcome must be a boolean value (True for YES, False for NO)")
E           ValueError: Outcome must be a boolean value (True for YES, False for NO)

app/services/amm_service.py:57: ValueError
____________________ TestAMMService.test_negative_liquidity ____________________

self = <test_amm_service.TestAMMService testMethod=test_negative_liquidity>

    def test_negative_liquidity(self):
        with self.assertRaises(ZeroDivisionError):
>           AMMService.calculate_share_allocation(-100, 100, 10, "YES")

tests/test_amm_service.py:244: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    @staticmethod
    def calculate_share_allocation(yes_liquidity: float, no_liquidity: float, stake: float, outcome: bool) -> Dict[str, Any]:
        """
        Given a stake and outcome, calculate new liquidity values and shares allocated.
        Enforces the constant product invariant: x * y = k
    
        Args:
            yes_liquidity: Current YES pool liquidity
            no_liquidity: Current NO pool liquidity
            stake: Amount of stake to add
            outcome: True for YES position, False for NO position
    
        Returns:
            dict: Dictionary containing:
                - shares: Number of shares allocated
                - yes_liquidity: New YES pool liquidity
                - no_liquidity: New NO pool liquidity
                - price: Price per share
        """
        if not isinstance(outcome, bool):
>           raise ValueError("Outcome must be a boolean value (True for YES, False for NO)")
E           ValueError: Outcome must be a boolean value (True for YES, False for NO)

app/services/amm_service.py:57: ValueError
=========================== short test summary info ============================
FAILED tests/test_amm_service.py::TestAMMCore::test_share_allocation_small_stake_yes
FAILED tests/test_amm_service.py::TestAMMCore::test_share_allocation_large_stake_no
FAILED tests/test_amm_service.py::TestAMMCore::test_constant_product_invariance
FAILED tests/test_amm_service.py::TestAMMCore::test_odds_update_accuracy - Va...
FAILED tests/test_amm_service.py::TestAMMCore::test_tiny_liquidity - ValueErr...
FAILED tests/test_amm_service.py::TestAMMCore::test_large_stake_impact - Valu...
FAILED tests/test_amm_service.py::TestAMMService::test_calculate_share_allocation_no
FAILED tests/test_amm_service.py::TestAMMService::test_calculate_share_allocation_yes
FAILED tests/test_amm_service.py::TestAMMService::test_negative_liquidity - V...
========================= 9 failed, 4 passed in 0.06s ==========================

```
### tests/test_prediction_service.py
```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.1, pluggy-1.6.0 -- /Users/georgeflinn/PM4/venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/georgeflinn/PM4
plugins: anyio-4.9.0
collecting ... collected 11 items

tests/test_prediction_service.py::TestPredictionService::test_place_prediction_points PASSED [  9%]
tests/test_prediction_service.py::TestPredictionService::test_place_prediction_buffer PASSED [ 18%]
tests/test_prediction_service.py::TestPredictionService::test_resolve_prediction_correct FAILED [ 27%]
tests/test_prediction_service.py::TestPredictionService::test_resolve_prediction_incorrect FAILED [ 36%]
tests/test_prediction_service.py::TestPredictionService::test_place_prediction_insufficient_points PASSED [ 45%]
tests/test_prediction_service.py::TestPredictionService::test_place_prediction_insufficient_buffer PASSED [ 54%]
tests/test_prediction_service.py::TestPredictionService::test_place_prediction_insufficient_balance PASSED [ 63%]
tests/test_prediction_service.py::TestPredictionService::test_resolve_prediction_unresolved_market PASSED [ 72%]
tests/test_prediction_service.py::TestPredictionService::test_place_prediction_zero_stake PASSED [ 81%]
tests/test_prediction_service.py::TestPredictionService::test_place_prediction_negative_stake PASSED [ 90%]
tests/test_prediction_service.py::TestPredictionService::test_place_prediction_invalid_outcome PASSED [100%]

=================================== FAILURES ===================================
____________ TestPredictionService.test_resolve_prediction_correct _____________

self = <test_prediction_service.TestPredictionService object at 0x107ecdb20>
mock_xp_service = <MagicMock name='XPService' spec='XPService' id='4432311872'>
test_app = <Flask 'app'>
test_session = <sqlalchemy.orm.scoping.scoped_session object at 0x10793bd60>

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
>           assert prediction.awarded_xp > 0
E           TypeError: '>' not supported between instances of 'NoneType' and 'int'

tests/test_prediction_service.py:857: TypeError
---------------------------- Captured stdout setup -----------------------------
Registered tables after init_app: dict_keys(['user', 'leagues', 'league_members', 'badges', 'user_badges', 'contract_drafts', 'published_contracts', 'market_event', 'market', 'platform_wallet', 'prediction', 'news_source', 'news_headline', 'liquidity_pools', 'liquidity_providers', 'user_ledger', 'amm_markets'])
Registered tables after init_app: {'user': 'user', 'market': 'market', 'prediction': 'prediction', 'market_event': 'market_event', 'platform_wallet': 'platform_wallet', 'news_source': 'news_source', 'news_headline': 'news_headline', 'liquidity_pools': 'liquidity_pools', 'liquidity_providers': 'liquidity_providers', 'user_ledger': 'user_ledger', 'amm_markets': 'amm_markets'}
___________ TestPredictionService.test_resolve_prediction_incorrect ____________

self = <test_prediction_service.TestPredictionService object at 0x107ecd940>
mock_xp_service = <MagicMock name='XPService' spec='XPService' id='4431190624'>
test_app = <Flask 'app'>
test_session = <sqlalchemy.orm.scoping.scoped_session object at 0x10793bd60>

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
>           assert prediction.awarded_points == 0
E           assert None == 0
E            +  where None = <Prediction 1: 0.5 shares on Market 1>.awarded_points

tests/test_prediction_service.py:911: AssertionError
---------------------------- Captured stdout setup -----------------------------
Registered tables after init_app: dict_keys(['user', 'leagues', 'league_members', 'badges', 'user_badges', 'contract_drafts', 'published_contracts', 'market_event', 'market', 'platform_wallet', 'prediction', 'news_source', 'news_headline', 'liquidity_pools', 'liquidity_providers', 'user_ledger', 'amm_markets'])
Registered tables after init_app: {'user': 'user', 'market': 'market', 'prediction': 'prediction', 'market_event': 'market_event', 'platform_wallet': 'platform_wallet', 'news_source': 'news_source', 'news_headline': 'news_headline', 'liquidity_pools': 'liquidity_pools', 'liquidity_providers': 'liquidity_providers', 'user_ledger': 'user_ledger', 'amm_markets': 'amm_markets'}
=========================== short test summary info ============================
FAILED tests/test_prediction_service.py::TestPredictionService::test_resolve_prediction_correct
FAILED tests/test_prediction_service.py::TestPredictionService::test_resolve_prediction_incorrect
========================= 2 failed, 9 passed in 0.18s ==========================

```
