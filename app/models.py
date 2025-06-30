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
            password (str): The plaintext password to hash
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
        if not any(ub.badge.id == self.id for ub in user.user_badges):
            user_badge = UserBadge(user=user, badge=self)
            db.session.add(user_badge)
            db.session.commit()
            return user_badge
        return None

class Market(db.Model):
    __tablename__ = 'market'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    resolution_date = db.Column(db.DateTime, nullable=False)
    resolution_method = db.Column(db.Text, nullable=False)
    source_url = db.Column(db.String(200))
    domain = db.Column(db.String(50))
    parent_market_id = db.Column(db.Integer, db.ForeignKey('market.id'))
    original_source = db.Column(db.String(200))
    original_headline = db.Column(db.String(200))
    original_date = db.Column(db.DateTime)
    scraped_at = db.Column(db.DateTime)
    refined_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    refined_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    domain_tags = db.Column(db.JSON)
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
    
    def lineage(self):
        """Return a list of all parent markets in the lineage"""
        if not self.parent_market:
            return []
        return self.parent_market.lineage() + [self.parent_market]

    def lineage_chain(self):
        """Return a formatted string of the market lineage"""
        return ' → '.join([m.title for m in list(reversed(self.lineage)) + [self]])

    def __repr__(self):
        return f'<Market {self.title}>'

    def resolve(self, outcome: bool):
        """Resolve the market with a given outcome.
        
        Args:
            outcome (bool): True for YES, False for NO
        """
        if self.resolved:
            raise ValueError('Market is already resolved')
            
        if outcome not in ['YES', 'NO']:
            raise ValueError('Outcome must be either "YES" or "NO"')
            
        self.resolved = True
        self.resolved_outcome = outcome
        self.resolved_at = datetime.utcnow()
        
        # Calculate payouts for all predictions
        for prediction in self.predictions:
            if prediction.outcome == outcome:
                # Calculate payout based on pool sizes
                total_pool = self.yes_pool + self.no_pool
                if outcome == 'YES':
                    prediction.payout = prediction.shares * (total_pool / self.yes_pool)
                else:
                    prediction.payout = prediction.shares * (total_pool / self.no_pool)
                
                # Update user points
                prediction.user.points += prediction.payout
                
                # Award XP for correct prediction
                prediction.user.xp += 10
                prediction.xp_awarded = True
                
                # Update reliability index
                prediction.user.update_reliability(True)
            else:
                # Update reliability index for incorrect prediction
                prediction.user.update_reliability(False)
        
        # Log the resolution
        event = MarketEvent(
            market=self,
            event_type='market_resolved',
            user_id=None,
            description=f'Market "{self.title}" resolved with outcome {outcome}',
            event_data={
                'outcome': outcome,
                'total_pool': self.yes_pool + self.no_pool,
                'yes_pool': self.yes_pool,
                'no_pool': self.no_pool,
                'predictions': {
                    'total': len(self.predictions),
                    'correct': len([p for p in self.predictions if p.outcome == outcome])
                }
            }
        )
        db.session.add(event)
        
        # Distribute liquidity rewards
        self.distribute_liquidity_rewards()
        
        db.session.commit()
        return True

    def award_xp_for_predictions(self, base_xp_per_share: int = 10):
        """Award XP to users with correct predictions on this market.
        
        Args:
            base_xp_per_share (int): Base XP to award per share (default: 10)
        """
        if not self.resolved:
            raise ValueError('Market must be resolved to award XP')
            
        for prediction in self.predictions:
            if prediction.outcome == self.resolved_outcome and not prediction.xp_awarded:
                # Calculate XP based on shares
                xp = base_xp_per_share * prediction.shares
                
                # Award XP to user
                prediction.user.xp += xp
                prediction.xp_awarded = True
                
                # Log the XP award
                event = MarketEvent(
                    market=self,
                    event_type='xp_awarded',
                    user=prediction.user,
                    description=f'XP awarded for correct prediction on "{self.title}"',
                    event_data={
                        'shares': prediction.shares,
                        'xp': xp,
                        'total_xp': prediction.user.xp
                    }
                )
                db.session.add(event)
        
        db.session.commit()

    def distribute_liquidity_rewards(self, fee):
        """Distribute liquidity rewards to all liquidity providers based on their share.
        
        Args:
            fee (float): Total fee to distribute
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

class Prediction(db.Model):
    """Prediction model."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    outcome = db.Column(db.String(3), nullable=False)  # 'YES' or 'NO'
    amount = db.Column(db.Float, nullable=False)
    shares = db.Column(db.Float, default=0.0)
    average_price = db.Column(db.Float, default=0.0)
    payout = db.Column(db.Float, default=0)
    xp_awarded = db.Column(db.Boolean, default=False)
    used_liquidity_buffer = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='predictions')
    market = db.relationship('Market', back_populates='predictions')

class MarketEvent(db.Model):
    """Model to track important events in a market's lifecycle"""
    id = db.Column(db.Integer, primary_key=True)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    event_type = db.Column(db.String, nullable=False)  # Add required event_type field
    description = db.Column(db.String(200), nullable=False)
    event_data = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    market = db.relationship('Market', back_populates='events')
    user = db.relationship('User', back_populates='events')
    
    @classmethod
    def log_market_creation(cls, market, user_id):
        """Log the creation of a new market"""
        return cls(
            market_id=market.id,
            event_type='market_created',
            user_id=user_id,
            description=f'Market "{market.title}" created',
            event_data={
                'title': market.title,
                'description': market.description,
                'resolution_date': market.resolution_date.isoformat(),
                'resolution_method': market.resolution_method,
                'domain': market.domain,
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
    def log_market_resolution(cls, market, user_id):
        """Log market resolution"""
        return cls(
            market_id=market.id,
            event_type='market_resolved',
            user_id=user_id,
            description=f'Market "{market.title}" resolved',
            event_data={
                'outcome': market.resolved_outcome,
                'resolved_at': datetime.utcnow().isoformat(),
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

class PlatformWallet(db.Model):
    """Platform wallet to track cumulative platform fees."""
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float, default=0.0)
    
    @classmethod
    def get_instance(cls):
        """Get or create the platform wallet instance."""
        wallet = cls.query.first()
        if not wallet:
            wallet = cls()
            db.session.add(wallet)
            db.session.commit()
        return wallet

    def add_fee(self, amount: float) -> None:
        """Add a fee amount to the wallet balance."""
        self.balance += amount
        db.session.commit()

    def __repr__(self):
        return f'<PlatformWallet id={self.id} balance={self.balance:.2f}>'
