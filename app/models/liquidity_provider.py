# app/models/liquidity_provider.py

from app.extensions import db
from datetime import datetime

class LiquidityProvider(db.Model):
    __tablename__ = 'liquidity_providers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'))
    amount = db.Column(db.Float, nullable=False)
    contributed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="liquidity_providers")
    market = db.relationship("Market", back_populates="liquidity_providers")