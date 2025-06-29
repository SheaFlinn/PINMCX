from datetime import datetime
from app.extensions import db


class LiquidityPool(db.Model):
    __tablename__ = 'liquidity_pools'

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False, unique=True)
    max_liquidity = db.Column(db.Integer, nullable=False)
    current_liquidity = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    contract = db.relationship('Contract', back_populates='liquidity_pool')

    def __repr__(self):
        return f"<LiquidityPool ContractID={self.contract_id} Max={self.max_liquidity} Current={self.current_liquidity}>"
