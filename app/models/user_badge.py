# app/models/user_badge.py

from app import db

class UserBadge(db.Model):
    __tablename__ = 'user_badges'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    badge_id = db.Column(db.Integer, nullable=False)
