# app/models/liquidity_provider.py

from app import db

class LiquidityProvider(db.Model):
    __tablename__ = 'liquidity_providers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    contract_id = db.Column(db.Integer, nullable=False)
    provided_at = db.Column(db.DateTime, server_default=db.func.now())