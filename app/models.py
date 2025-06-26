from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.extensions import db
from sqlalchemy import func
import hashlib
from config import Config
import logging

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
    
    # Relationships
    predictions = db.relationship('Prediction', back_populates='user', lazy=True)
    badges = db.relationship('Badge', secondary='user_badges', back_populates='users')
    refined_markets = db.relationship('Market', back_populates='refiner', lazy=True)
    events = db.relationship('MarketEvent', back_populates='user', lazy=True)
    liquidity_providers = db.relationship('LiquidityProvider', back_populates='user')
    league_members = db.relationship('LeagueMember', back_populates='user')
    
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
    users = db.relationship('User', secondary='user_badges', back_populates='badges')
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'description': self.description,
            'icon': self.icon
        }

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
        return ' → '.join([m.title for m in reversed(self.lineage) + [self]])
    
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
    event_type = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    description = db.Column(db.Text)
    event_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    market = db.relationship('Market', back_populates='events', lazy=True)
    user = db.relationship('User', back_populates='events', lazy=True)
    
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
        """Log the resolution of a market"""
        return cls(
            market_id=market.id,
            event_type='market_resolved',
            user_id=user_id,
            description=f'Market "{market.title}" resolved',
            event_data={
                'outcome': market.resolved_outcome,
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
