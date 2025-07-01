from app import db
from datetime import datetime

class League(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    members = db.relationship('LeagueMember', backref='league', lazy=True)

class LeagueMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey('league.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
