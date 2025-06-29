from app import db
from .contract import Contract
from datetime import datetime
from .market import Market

class LiquidityPool(db.Model):
    __tablename__ = 'liquidity_pools'

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    cap = db.Column(db.Float, nullable=False)
    current_liquidity = db.Column(db.Float, nullable=False)
    max_liquidity = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Relationships
    markets = db.relationship('Market', back_populates='liquidity_pool')
    contract = db.relationship('Contract', back_populates='liquidity_pool', uselist=False)

    def __init__(self, cap, current_liquidity, max_liquidity):
        self.cap = cap
        self.current_liquidity = current_liquidity
        self.max_liquidity = max_liquidity

    def __repr__(self):
        return f'<LiquidityPool cap={self.cap}>'
