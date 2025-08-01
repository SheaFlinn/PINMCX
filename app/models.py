from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.extensions import db
from sqlalchemy import func
import hashlib
from config import Config
import logging


def generate_contract_hash(contract_name):
    """Generate a SHA-256 hash for market integrity verification"""
    import hashlib
    return hashlib.sha256(contract_name.encode()).hexdigest()

# Association table for User-Badge relationship
class UserBadge(db.Model):
    __tablename__ = 'user_badges'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='user_badges')
    badge = db.relationship('Badge', back_populates='user_badges')

def generate_contract_hash(market):
    """Generate a SHA-256 hash for market integrity verification"""
    # Create a consistent string representation of the market
    hash_data = f"{market.title}|{market.original_source or ''}|{market.source_url or ''}|{market.resolved_outcome or ''}|{market.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if market.resolved_at else ''}"
    
    # Generate SHA-256 hash
    return hashlib.sha256(hash_data.encode()).hexdigest()

# Association table for User-Badge relationship
user_badges = db.Table('user_badges',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('badge.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    dummy_field = db.Column(db.String(50))  # temp field for migration check
    is_admin = db.Column(db.Boolean, default=False)  # Add admin flag
    
    # Gamification fields
    points = db.Column(db.Integer, default=0)
    lb_deposit = db.Column(db.Float, default=0.0)
    reliability_index = db.Column(db.Float, default=50.0)
    xp = db.Column(db.Integer, default=0)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_check_in_date = db.Column(db.DateTime)
    
    accuracy = db.Column(db.Float, default=0.0)
    predictions_count = db.Column(db.Integer, default=0)
    liquidity_buffer_deposit = db.Column(db.Float, default=0.0)
    
    # Relationships
    predictions = db.relationship('Prediction', back_populates='user', lazy=True)
    user_badges = db.relationship('UserBadge', back_populates='user', lazy='dynamic')
    badges = db.relationship('Badge', secondary='user_badges', back_populates='users')
    refined_markets = db.relationship('Market', back_populates='refiner', lazy=True)
    events = db.relationship('MarketEvent', back_populates='user', lazy=True)
    liquidity_providers = db.relationship('LiquidityProvider', back_populates='user')
    league_members = db.relationship('LeagueMember', back_populates='user')

    market_events = db.relationship('MarketEvent', back_populates='user', lazy=True)
    
    @property
    def badges(self):
        """Return all badges for this user"""
        return [ub.badge for ub in self.user_badges]

    @property
    def badges_sorted(self):
        """Return badges sorted by creation date"""
        return sorted(self.badges, key=lambda b: b.user_badges[0].created_at, reverse=True)

    def assign_badge(self, badge):
        """Assign a badge to this user"""
        if not any(ub.badge.id == badge.id for ub in self.user_badges):
            user_badge = UserBadge(user=self, badge=badge)
            db.session.add(user_badge)
            db.session.commit()
            return user_badge
        return None

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.last_active = datetime.utcnow()

    def set_password(self, password):
        """Set user password with proper hashing.
        
        Args:
            password (str): The plaintext password to hash and store
        """
        # Generate hash with consistent parameters
        password_hash = generate_password_hash(
            password, 
            method='pbkdf2:sha256',
            salt_length=16  # Explicit salt length for consistency
        )
        logging.info(f"Setting password for user {self.username}: hash={password_hash[:10]}...")
        self.password_hash = password_hash

    def check_password(self, password):
        """Verify if the provided password matches the stored hash.
        
        Args:
            password (str): The plaintext password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        logging.info(f"Checking password for user {self.username}: provided password hash={generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)[:10]}... stored hash={self.password_hash[:10]}...")
        
        # Verify hash with explicit method to ensure consistency
        return check_password_hash(
            self.password_hash,
            password
        )

    def deposit_to_lb(self, amount):
        """Deposit points to Liquidity Buffer"""
        if amount <= 0 or amount > self.points:
            return False
        self.points -= amount
        self.lb_deposit += amount
        return True

    def withdraw_from_lb(self, amount):
        """Withdraw points from Liquidity Buffer"""
        if amount <= 0 or amount > self.lb_deposit:
            return False
        self.points += amount
        self.lb_deposit -= amount
        return True

    def get_lb_yield(self):
        """Calculate daily yield from Liquidity Buffer"""
        total_lb = db.session.query(func.sum(User.lb_deposit)).scalar() or 0
        if total_lb == 0:
            return 0
        
        # Annual yield rate (4-8% as per the document)
        base_yield = 6  # 6% annual yield
        
        # Adjust yield based on market activity
        active_markets = Market.query.filter_by(resolved=False).count()
        yield_adjustment = min(2, active_markets / 10)  # Up to 2% bonus for active markets
        
        # Calculate daily yield
        daily_yield = (base_yield + yield_adjustment) / 365
        
        return (self.lb_deposit * daily_yield) / 100

    def update_reliability(self, was_correct):
        """Update reliability index based on prediction accuracy"""
        if was_correct:
            self.reliability_index = min(100.0, self.reliability_index + (20 / (1 + len(self.predictions))))
            self.xp += 10
        else:
            self.reliability_index = max(0.0, self.reliability_index - (10 / (1 + len(self.predictions))))

class Badge(db.Model):
    __tablename__ = 'badge'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(100))  # CSS class or image path
    
    # Relationship
    user_badges = db.relationship('UserBadge', back_populates='badge')
    users = db.relationship('User', secondary='user_badges', back_populates='badges')
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'description': self.description,
            'icon': self.icon
        }

    def assign_to_user(self, user):
        """Assign this badge to a user"""
        user_badge = UserBadge(user=user, badge=self)
        db.session.add(user_badge)
        db.session.commit()
        return user_badge

class Market(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    resolution_date = db.Column(db.DateTime, nullable=False)
    resolution_method = db.Column(db.Text, nullable=False)
    source_url = db.Column(db.String(200))
    domain = db.Column(db.String(50))  # Market domain category
    parent_market_id = db.Column(db.Integer, db.ForeignKey('market.id'))  # Reference to parent market
    original_source = db.Column(db.String(200))  # Original news source
    original_headline = db.Column(db.String(200))  # Original headline
    original_date = db.Column(db.DateTime)  # Original article date
    scraped_at = db.Column(db.DateTime)  # When the market was scraped
    refined_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # User who refined the market
    refined_at = db.Column(db.DateTime)  # When the market was refined
    approved_at = db.Column(db.DateTime)  # When the market was approved
    domain_tags = db.Column(db.JSON)  # Additional domain tags
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved = db.Column(db.Boolean, default=False)
    resolved_outcome = db.Column(db.String(3))
    resolved_at = db.Column(db.DateTime)
    yes_pool = db.Column(db.Float, default=1000.0)
    no_pool = db.Column(db.Float, default=1000.0)
    liquidity_pool = db.Column(db.Float, default=2000.0)
    liquidity_provider_shares = db.Column(db.Float, default=1.0)
    liquidity_fee = db.Column(db.Float, default=0.003)

    prediction_deadline = db.Column(db.DateTime, nullable=True, default=lambda: datetime.utcnow())
    resolution_deadline = db.Column(db.DateTime, nullable=True, default=lambda: datetime.utcnow())

    # Relationships
    parent_market = db.relationship('Market', remote_side=[id], back_populates='child_markets')
    child_markets = db.relationship('Market', back_populates='parent_market')
    refiner = db.relationship('User', back_populates='refined_markets')
    predictions = db.relationship('Prediction', back_populates='market', lazy=True)
    events = db.relationship('MarketEvent', back_populates='market', lazy=True)
    
    # Properties for lineage
    @property
    def lineage(self):
        """Return a list of all parent markets in the lineage"""
        lineage = []
        current = self
        while current.parent_market:
            lineage.append(current.parent_market)
            current = current.parent_market
        return lineage
    
    @property
    def lineage_chain(self):
        """Return a formatted string of the market lineage"""
        return ' → '.join([m.title for m in list(reversed(self.lineage)) + [self]])

    def __repr__(self):
        return f'<Market {self.id}: {self.title}>'
    
    # Relationship for LP positions
    liquidity_providers = db.relationship('LiquidityProvider', back_populates='market', lazy=True)

    @property
    def yes_price(self):
        """Calculate YES share price using AMM formula"""
        if self.no_pool == 0:
            return 1.0
        return self.yes_pool / self.no_pool
    
    @property
    def no_price(self):
        """Calculate NO share price using AMM formula"""
        if self.yes_pool == 0:
            return 1.0
        return self.no_pool / self.yes_pool
    
    def trade(self, user, amount, outcome):
        """
        Execute a trade on this market.
        
        Args:
            user: User making the trade
            amount: Amount of points to trade
            outcome: True for YES trade, False for NO trade
            
        Returns:
            Dict containing trade details:
            - price: Price per share
            - shares: Number of shares purchased
            - outcome: 'YES' or 'NO'
            
        Raises:
            ValueError: If trade amount is invalid
        """
        from app.services.points_trade_engine import PointsTradeEngine
        
        # Execute the trade through the trade engine
        trade_result = PointsTradeEngine.execute_trade(user, self, amount, outcome)
        
        # Log the trade event with values from trade result
        event = MarketEvent(
            market=self,
            event_type='trade',
            user=user,
            description=f"User {user.username} traded {amount:.2f} points on {trade_result['outcome']} outcome",
            event_data={
                'amount': amount,
                'price': trade_result['price'],
                'shares': trade_result['shares'],
                'outcome': trade_result['outcome']

        Execute a trade on the market.
        
        Args:
            user (User): User executing the trade
            amount (float): Points to trade
            outcome (bool): True for YES, False for NO
            
        Returns:
            dict: Trade result containing price and shares
            
        Raises:
            ValueError: If trade would exceed pool cap
        """
        # Validate amount
        if amount < Config.MIN_TRADE_SIZE or amount > Config.MAX_TRADE_SIZE:
            raise ValueError(f'Trade amount must be between {Config.MIN_TRADE_SIZE} and {Config.MAX_TRADE_SIZE} points')
            
        # Check pool cap
        total_pool = self.yes_pool + self.no_pool
        if total_pool + amount > Config.CONTRACT_POOL_CAP:
            raise ValueError(f'Market pool cap reached. Total pool cannot exceed {Config.CONTRACT_POOL_CAP} points')
            
        # Calculate price
        if outcome:  # Trading YES
            price = self.yes_pool / self.no_pool
            self.yes_pool += amount
            shares = amount / price
        else:  # Trading NO
            price = self.no_pool / self.yes_pool
            self.no_pool += amount
            shares = amount / price
            
        # Update prices
        self.update_prices()
        
        # Log the trade
        event = MarketEvent(
            market_id=self.id,
            event_type='trade_executed',
            user_id=user.id,
            description=f'Trade executed on market "{self.title}"',
            event_data={
                'amount': amount,
                'outcome': outcome,
                'price': price,
                'shares': shares,
                'total_pool': total_pool + amount
            }
        )
        db.session.add(event)
        

        return trade_result

    def resolve(self, outcome: bool):
        """Resolve the market with a given outcome"""
        if self.resolved:
            return
            
        self.resolved = True
        self.resolved_outcome = "YES" if outcome else "NO"
        self.resolved_at = datetime.utcnow()
        self.integrity_hash = generate_contract_hash(self.title)

        # Log market resolution event
        event = MarketEvent.log_market_resolution(self, user_id=None)
        db.session.add(event)

        # Award XP for correct predictions
        self.award_xp_for_predictions()
        
        # Calculate and award payouts for all predictions
        for prediction in self.predictions:
            if prediction.outcome == outcome:
                total_pool = self.yes_pool + self.no_pool
                if outcome:
                    payout = prediction.shares * (total_pool / self.yes_pool)
                else:
                    payout = prediction.shares * (total_pool / self.no_pool)
                
                # Use payout engine to handle points
                from app.services.points_payout_engine import PointsPayoutEngine
                PointsPayoutEngine.award_resolution_payout(
                    user=prediction.user,
                    amount=payout,
                    market_id=self.id
                )
                prediction.payout = payout
        
        return True


        return {
            'price': price,
            'shares': shares,
            'total_pool': total_pool + amount
        }
    
    def update_prices(self):
        # Update prices
        pass
    
    def distribute_liquidity_rewards(self, fee):
        """
        Distribute liquidity rewards to all liquidity providers based on their share.
        """
        if not self.liquidity_providers:
            return
            
        total_shares = sum(lp.shares for lp in self.liquidity_providers)
        
        for lp in self.liquidity_providers:
            reward = (fee * lp.shares) / total_shares

            
            # Use payout engine to handle points
            from app.services.points_payout_engine import PointsPayoutEngine
            PointsPayoutEngine.award_trade_payout(
                user=lp.user,
                amount=reward,
                market_id=self.id,
                outcome='LIQUIDITY'  # Special outcome type for liquidity rewards
            )

            lp.user.points += reward
            
            # Log the reward
            event = MarketEvent(
                market=self,
                event_type='liquidity_reward',
                user=lp.user,
                description=f'Liquidity reward distributed to user "{lp.user.username}"',
                event_data={
                    'amount': reward,
                    'total_shares': total_shares,
                    'lp_shares': lp.shares
                }
            )
            db.session.add(event)


    def award_xp_for_predictions(self, base_xp_per_share: int = 10):
        """
        Award XP to users with correct predictions on this market.
        
        Args:
            base_xp_per_share: Base XP amount per share (default 10)
            
        XP Awarding Rules:
        1. Market Resolution:
           - XP can only be awarded if market is resolved
           - Requires market.resolved = True and market.resolved_outcome != None
           
        2. Prediction Validity:
           - Only correct predictions receive XP
           - Prediction must match market.resolved_outcome (case-insensitive)
           - XP amount = base_xp_per_share * prediction.shares
           
        3. Prevention of Re-Award:
           - Each prediction has an xp_awarded flag
           - XP is never awarded twice for the same prediction
           - Flag is set to True after first XP award
           - Applies regardless of prediction correctness
           
        4. PointsService Integration:
           - Uses PointsPayoutEngine.award_resolution_payout() for actual XP awarding
           - Handles streaks, daily limits, and multipliers
           - XP is only awarded if user hasn't checked in today
        
        Returns:
            None
        """
        from app.services.points_payout_engine import PointsPayoutEngine
        from app.models import Prediction

        if not self.resolved or not self.resolved_outcome:
            return

        predictions = Prediction.query.filter_by(market_id=self.id).all()
        
        for prediction in predictions:
            # Skip if XP already awarded
            if prediction.xp_awarded:
                continue

            # Only award XP for correct predictions
            if prediction.outcome == (self.resolved_outcome == "YES"):
                xp_amount = base_xp_per_share * prediction.shares
                PointsPayoutEngine.award_resolution_payout(
                    user=prediction.user,
                    amount=xp_amount,
                    market_id=self.id
                )
                
            # Mark prediction as XP awarded (whether correct or not)
            prediction.xp_awarded = True
            db.session.add(prediction)

        db.session.commit()

    @classmethod
    def create_with_event(cls, **kwargs):
        """
        Create a market and log its creation event.

        Args:
            user_id: ID of the user creating the market
            **kwargs: Market creation arguments

        Returns:
            tuple: (Market instance, MarketEvent instance)
        """
        user_id = kwargs.pop('user_id', None)  # Extract user_id first

        market = cls(**kwargs)
        db.session.add(market)
        db.session.commit()  # Ensure market.id is assigned

        event = MarketEvent.log_market_creation(market, user_id)
        db.session.add(event)
        db.session.commit()

        return market, event

class Prediction(db.Model):
    """Prediction model."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    shares = db.Column(db.Float, nullable=False)
    platform_fee = db.Column(db.Float, nullable=True)  # 5% fee deducted from shares
    outcome = db.Column(db.Boolean, nullable=False)
    used_liquidity_buffer = db.Column(db.Boolean, default=False)  # Track if prediction used LB
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    xp_awarded = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', back_populates='predictions')
    market = db.relationship('Market', back_populates='predictions')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Handle market_id or market object
        market_id = kwargs.get('market_id')
        if not market_id and 'market' in kwargs and kwargs['market']:
            market_id = kwargs['market'].id

        # Handle user_id or user object
        user_id = kwargs.get('user_id')
        if not user_id and 'user' in kwargs and kwargs['user']:
            user_id = kwargs['user'].id

        # Log prediction if we have both market_id and user_id
        if market_id and user_id:
            market = Market.query.get(market_id)
            if market:
                print(f"Prediction logged for market: {market.title}")
                event = MarketEvent.log_prediction(market, user_id, self)
                db.session.add(event)

    def __repr__(self):
        return f'<Prediction {self.id}: {self.shares} shares on Market {self.market_id}>'

    def resolve(self, outcome):
        """Resolve the market with a given outcome"""
        if self.resolved:
            raise ValueError('Market is already resolved')
            
        if outcome not in ['YES', 'NO']:
            raise ValueError('Outcome must be either "YES" or "NO"')
            
        self.resolved = True
        self.resolved_outcome = outcome
        self.resolved_at = datetime.utcnow()
        self.integrity_hash = generate_contract_hash(self)
        
        # Calculate payouts for all predictions
        for prediction in self.predictions:
            if prediction.prediction == outcome:
                # Calculate payout based on pool sizes
                total_pool = self.yes_pool + self.no_pool
                if outcome == 'YES':
                    prediction.payout = prediction.shares * (total_pool / self.yes_pool)
                else:
                    prediction.payout = prediction.shares * (total_pool / self.no_pool)
                prediction.user.points += prediction.payout
        
        db.session.commit()

    def award_xp_for_predictions(self):
        """Award XP to users who made correct predictions on this market"""
        if not self.resolved:
            raise ValueError('Market must be resolved to award XP')
            
        for prediction in self.predictions:
            user = prediction.user
            
            # Calculate XP gain
            xp_gain = 0
            if (self.resolved_outcome == 'YES' and prediction.prediction == 'YES') or \
               (self.resolved_outcome == 'NO' and prediction.prediction == 'NO'):
                xp_gain = 10
                user.accuracy = (user.accuracy * user.predictions_count + 1) / (user.predictions_count + 1)
                user.reliability_index = min(100.0, user.reliability_index + 1)
            else:
                user.accuracy = (user.accuracy * user.predictions_count) / (user.predictions_count + 1)
                user.reliability_index = max(0.0, user.reliability_index - 0.5)
            
            # Update points
            if (self.resolved_outcome == 'YES' and prediction.prediction == 'YES') or \
               (self.resolved_outcome == 'NO' and prediction.prediction == 'NO'):
                user.points += 10
            else:
                user.points -= 5
            
            # Update XP and reliability
            user.xp += xp_gain
            user.predictions_count += 1
            
            # Log the XP award
            event = MarketEvent(
                market=self,
                event_type='xp_awarded',
                user=user,
                description=f'XP awarded for correct prediction on market "{self.title}"',
                event_data={
                    'xp_gain': xp_gain,
                    'points_gain': 10 if xp_gain > 0 else -5,
                    'accuracy': user.accuracy,
                    'reliability': user.reliability_index
                }
            )
            db.session.add(event)

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prediction = db.Column(db.String(3), nullable=False)
    shares = db.Column(db.Float, default=0.0)
    average_price = db.Column(db.Float, default=0.0)
    payout = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    market = db.relationship('Market', back_populates='predictions', lazy=True)
    user = db.relationship('User', back_populates='predictions', lazy=True)

class MarketEvent(db.Model):
    """Model to track important events in a market's lifecycle"""
    id = db.Column(db.Integer, primary_key=True)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    event_type = db.Column(db.String, nullable=False)  # Add required event_type field
    description = db.Column(db.String(200), nullable=False)
    event_data = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    market = db.relationship('Market', back_populates='events')
    user = db.relationship('User', back_populates='market_events')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        db.session.add(self)

    @staticmethod
    def log_prediction(market: Market, user_id: int, prediction: Prediction) -> 'MarketEvent':
        """
        Log a new prediction event.
        
        Args:
            market: Market object
            user_id: ID of the user making the prediction
            prediction: Prediction object
            
        Returns:
            MarketEvent object
        """
        event_data = {
            'prediction_id': prediction.id,
            'shares': prediction.shares,
            'outcome': prediction.outcome,
            'xp_awarded': prediction.xp_awarded
        }
        
        event = MarketEvent(
            market_id=market.id,
            user_id=user_id,
            event_type='prediction',  # Add event_type
            description=f"Prediction made by user {user_id} on market {market.id}",
            event_data=event_data
        )
        
        return event

    @classmethod
    def log_market_creation(cls, market, user_id):
        """Log the creation of a new market"""
        return cls(
            market_id=market.id,

            event_type='market_created',  # Add event_type

            user_id=user_id,
            description=f'Market "{market.title}" created',
            event_data={
                'title': market.title,

                'description': market.description,
                'resolution_date': market.resolution_date.isoformat(),
                'resolution_method': market.resolution_method,

                'domain': market.domain,
                'resolution_date': market.resolution_date.isoformat(),
                'resolution_method': market.resolution_method,
                'lineage': market.lineage_chain
            }
        )
    
    @classmethod
    def log_market_update(cls, market, user_id, changes):
        """Log an update to an existing market"""
        return cls(
            market_id=market.id,
            event_type='market_updated',
            user_id=user_id,
            description=f'Market "{market.title}" updated',
            event_data={
                'changes': changes,
                'domain': market.domain,
                'lineage': market.lineage_chain
            }
        )
    
    @classmethod
    def log_market_resolution(cls, market, user_id):

        """Log market resolution"""
        return cls(
            market_id=market.id,
            event_type='market_resolved',  # Add event_type

            user_id=user_id,
            description=f'Market "{market.title}" resolved',
            event_data={
                'outcome': market.resolved_outcome,

                'resolved_at': datetime.utcnow().isoformat(),

                'domain': market.domain,
                'resolution_date': market.resolved_at.isoformat(),
                'lineage': market.lineage_chain
            }
        )
    
    @classmethod
    def log_prediction(cls, market, user_id, prediction):
        """Log a user's prediction on a market"""
        return cls(
            market_id=market.id,
            event_type='prediction',
            user_id=user_id,
            description=f'Prediction made on market "{market.title}"',
            event_data={
                'prediction': prediction,
                'domain': market.domain,
                'lineage': market.lineage_chain
            }
        )
    
    @classmethod
    def log_lineage_change(cls, market, user_id, parent_market_id):
        """Log a change in market lineage"""
        return cls(
            market_id=market.id,
            event_type='lineage_changed',
            user_id=user_id,
            description=f'Market "{market.title}" lineage updated',
            event_data={
                'old_parent': market.parent_market_id,
                'new_parent': parent_market_id,
                'domain': market.domain,
                'lineage': market.lineage_chain
            }
        )
    
    def __repr__(self):
        return f'<MarketEvent {self.id}: {self.event_type} for Market {self.market_id}>'

class LiquidityPool(db.Model):
    __tablename__ = 'liquidity_pools'

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False, unique=True)
    max_liquidity = db.Column(db.Integer, nullable=False)  # cap funded from LB
    current_liquidity = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    contract = db.relationship('Contract', back_populates='liquidity_pool')

class AMMMarket(db.Model):
    __tablename__ = 'amm_markets'

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    base_pool = db.Column(db.Float, default=1000.0)
    quote_pool = db.Column(db.Float, default=1000.0)
    total_shares_yes = db.Column(db.Float, default=0.0)
    total_shares_no = db.Column(db.Float, default=0.0)

    contract = db.relationship('Contract', back_populates='amm_market', lazy='joined')

class Contract(db.Model):
    __tablename__ = 'contract'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    headline = db.Column(db.String(500), nullable=False)
    original_headline = db.Column(db.String(500))
    confidence = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    liquidity_pool = db.relationship('LiquidityPool', uselist=False, back_populates='contract')
    amm_market = db.relationship('AMMMarket', uselist=False, back_populates='contract', lazy='joined')

class AnchoredHash(db.Model):
    """Placeholder table for future blockchain anchoring"""
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(64), nullable=False)  # SHA-256 hash
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    anchored_at = db.Column(db.DateTime, default=datetime.utcnow)
    chain_name = db.Column(db.String(50))  # Placeholder for future chain name
    tx_id = db.Column(db.String(100))  # Optional transaction ID
    
    market = db.relationship('Market', backref='anchor')

class NewsSource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    selector = db.Column(db.String(100), nullable=False)
    date_selector = db.Column(db.String(100))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # New fields for domain and weight
    domain_tag = db.Column(db.String(50))  # e.g., 'crime', 'infrastructure', 'weather'
    source_weight = db.Column(db.Float, default=1.0)  # 0.0 to 1.0, default 1.0 means neutral
    
    # Relationship
    headlines = db.relationship('NewsHeadline', back_populates='source', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'selector': self.selector,
            'date_selector': self.date_selector,
            'active': self.active,
            'domain_tag': self.domain_tag,
            'source_weight': self.source_weight
        }

class NewsHeadline(db.Model):
    __tablename__ = 'news_headline'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    url = db.Column(db.String(200))
    source_id = db.Column(db.Integer, db.ForeignKey('news_source.id'), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_published = db.Column(db.DateTime)
    domain_tag = db.Column(db.String(50))
    
    # Relationship
    source = db.relationship('NewsSource', back_populates='headlines')
    
    def __repr__(self):
        return f'<NewsHeadline {self.id}: {self.title[:50]}>'

class LiquidityProvider(db.Model):
    """Model to track liquidity providers and their shares"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    shares = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    market = db.relationship('Market', back_populates='liquidity_providers', lazy=True)
    user = db.relationship('User', back_populates='liquidity_providers')

class League(db.Model):
    """Model to track user leagues and rankings"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # League configuration
    update_interval = db.Column(db.Integer, default=7)  # Days between updates
    min_points = db.Column(db.Integer, default=1000)    # Minimum points to join
    max_members = db.Column(db.Integer, default=100)    # Maximum members
    
    # League members
    members = db.relationship('LeagueMember', back_populates='league', lazy=True)

    def __repr__(self):
        return f'<League {self.name}>'

class LeagueMember(db.Model):
    """Model to track user membership in leagues"""
    __tablename__ = 'league_member'
    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey('league.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    points = db.Column(db.Integer, default=0)
    rank = db.Column(db.Integer)
    __table_args__ = (db.UniqueConstraint('league_id', 'user_id', name='_league_user_uc'),)

    # Relationships
    league = db.relationship('League', back_populates='members')
    user = db.relationship('User', back_populates='league_members')
    
    def update_rank(self):
        """Update the member's rank based on points"""
        members = LeagueMember.query.filter_by(league_id=self.league_id).order_by(LeagueMember.points.desc()).all()
        for i, member in enumerate(members):
            member.rank = i + 1
        db.session.commit()

    def __repr__(self):
        return f'<LeagueMember {self.user.username} in {self.league.name}>'

class PlatformWallet(db.Model):
    """Platform wallet to track cumulative platform fees."""
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float, default=0.0)

    @property
    def total_fees(self):
        """Return the total accumulated fees."""
        return self.balance

    @classmethod
    def get_instance(cls):
        """Get or create the singleton PlatformWallet instance."""
        wallet = cls.query.get(1)
        if not wallet:
            wallet = cls(id=1, balance=0.0)
            db.session.add(wallet)
            db.session.commit()
        return wallet

    def add_fee(self, amount: float) -> None:
        """Add a fee amount to the wallet balance."""
        self.balance += amount
        db.session.commit()

    def __repr__(self):
        return f'<PlatformWallet id={self.id} balance={self.balance:.2f}>'
