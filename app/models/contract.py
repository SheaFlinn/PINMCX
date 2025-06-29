from datetime import datetime
from app.extensions import db


class Contract(db.Model):
    __tablename__ = 'contract'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    headline = db.Column(db.String(500), nullable=False)
    original_headline = db.Column(db.String(500))
    confidence = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    liquidity_pool = db.relationship(
        'LiquidityPool', uselist=False, back_populates='contract', lazy='joined'
    )
    amm_market = db.relationship(
        'AMMMarket', uselist=False, back_populates='contract', lazy='joined'
    )

    def __repr__(self):
        return f"<Contract {self.id}: {self.name}>"
