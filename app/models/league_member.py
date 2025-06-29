# app/models/league_member.py

from app import db

class LeagueMember(db.Model):
    __tablename__ = 'league_members'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    league_id = db.Column(db.Integer, nullable=False)
    joined_at = db.Column(db.DateTime, server_default=db.func.now())