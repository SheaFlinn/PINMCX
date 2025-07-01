# app/models/league_member.py

from app.extensions import db
from datetime import datetime

class LeagueMember(db.Model):
    __tablename__ = 'league_members'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship("User", back_populates="league_members")
    league = db.relationship("League", back_populates="members")