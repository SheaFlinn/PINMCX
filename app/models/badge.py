# app/models/badge.py

from app import db

class Badge(db.Model):
    __tablename__ = 'badges'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256))

    # Use backref to avoid circular import
    user_badges = db.relationship('UserBadge', backref='badge', lazy='dynamic')