from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.extensions import db
from sqlalchemy import func
import logging

# Association table for User-Badge relationship
class UserBadge(db.Model):
    __tablename__ = 'user_badges'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='user_badges')
    badge = db.relationship('Badge', back_populates='user_badges')

class Badge(db.Model):
    __tablename__ = 'badge'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(100))
    
    user_badges = db.relationship('UserBadge', back_populates='badge')

    def assign_to_user(self, user):
        if not any(ub.badge.id == self.id for ub in user.user_badges):
            user_badge = UserBadge(user=user, badge=self)
            db.session.add(user_badge)
            db.session.commit()
            return user_badge
        return None

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

    predictions = db.relationship('Prediction', back_populates='user', lazy=True)
    user_badges = db.relationship('UserBadge', back_populates='user', lazy='dynamic')
    refined_markets = db.relationship('Market', back_populates='refiner', lazy=True)
    events = db.relationship('MarketEvent', back_populates='user', lazy=True)
    liquidity_providers = db.relationship('LiquidityProvider', back_populates='user')
    league_members = db.relationship('LeagueMember', back_populates='user')

    @property
    def badges(self):
        return [ub.badge for ub in self.user_badges]

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
