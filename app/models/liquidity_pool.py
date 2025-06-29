from app import db
from .contract import Contract

class LiquidityPool(db.Model):
    __tablename__ = 'liquidity_pools'

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    cap = db.Column(db.Float, nullable=True)  # optional for now
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
