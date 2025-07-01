# app/models/user_badge.py

from app.extensions import db
from datetime import datetime
from app.models.user import User

class UserBadge(db.Model):
    __tablename__ = 'user_badges'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'), nullable=False)
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Keep relationship to User only
    user = db.relationship("User", back_populates="user_badges")
