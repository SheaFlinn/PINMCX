from app import db

from datetime import datetime

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    xp = db.Column(db.Integer, default=0)
    liquidity_buffer_deposit = db.Column(db.Float, default=0.0)
    reliability_index = db.Column(db.Float, default=0.0)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_check_in_date = db.Column(db.DateTime)
    points = db.Column(db.Integer, default=0)
    predictions_count = db.Column(db.Integer, default=0)
    accuracy = db.Column(db.Float, default=0.0)
    is_admin = db.Column(db.Boolean, default=False)
    last_active = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    predictions = db.relationship('Prediction', back_populates='user')
    markets = db.relationship('Market', back_populates='creator', cascade='all, delete-orphan')
    ledger_entries = db.relationship('UserLedger', back_populates='user', cascade='all, delete-orphan')

    def __init__(self, username, email, password_hash=None, xp=0,
                 liquidity_buffer_deposit=0.0, reliability_index=0.0,
                 current_streak=0, longest_streak=0, last_check_in_date=None,
                 points=0, predictions_count=0, accuracy=0.0, is_admin=False,
                 last_active=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.xp = xp
        self.liquidity_buffer_deposit = liquidity_buffer_deposit
        self.reliability_index = reliability_index
        self.current_streak = current_streak
        self.longest_streak = longest_streak
        self.last_check_in_date = last_check_in_date
        self.points = points
        self.predictions_count = predictions_count
        self.accuracy = accuracy
        self.is_admin = is_admin
        self.last_active = last_active

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Set user's password hash."""
        self.password_hash = password

    def check_password(self, password):
        """Check if provided password matches stored hash."""
        return self.password_hash == password


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
 932aef4 (LOCKED: All model stubs added, migrations clean through Badge/UserBadge)
