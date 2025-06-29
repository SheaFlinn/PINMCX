# app/models/market_event.py

from app import db

class MarketEvent(db.Model):
    __tablename__ = 'market_events'

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    event_type = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())