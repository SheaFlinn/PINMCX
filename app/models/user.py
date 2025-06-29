from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from app.extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

    # Gamification fields
    points = db.Column(db.Integer, default=0)
    lb_deposit = db.Column(db.Float, default=0.0)
    reliability_index = db.Column(db.Float, default=50.0)
    xp = db.Column(db.Integer, default=0)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_check_in_date = db.Column(db.DateTime)
    predictions_count = db.Column(db.Integer, default=0)

    # Relationships
    predictions = db.relationship('Prediction', back_populates='user', lazy=True)
    user_badges = db.relationship('UserBadge', back_populates='user', lazy='dynamic')
    refined_markets = db.relationship('Market', back_populates='refiner', lazy=True)
    events = db.relationship('MarketEvent', back_populates='user', lazy=True)
    liquidity_providers = db.relationship('LiquidityProvider', back_populates='user')
    league_members = db.relationship('LeagueMember', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def deposit_to_lb(self, amount):
        if amount <= 0 or amount > self.points:
            return False
        self.points -= amount
        self.lb_deposit += amount
        return True

    def withdraw_from_lb(self, amount):
        if amount <= 0 or amount > self.lb_deposit:
            return False
        self.points += amount
        self.lb_deposit -= amount
        return True

    def get_lb_yield(self):
        total_lb = db.session.query(func.sum(User.lb_deposit)).scalar() or 0
        return 0 if total_lb == 0 else (self.lb_deposit * (6 / 365)) / 100  # 6% base yield
