from app import db
from datetime import datetime

class AMMMarket(db.Model):
    __tablename__ = 'amm_markets'

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('published_contracts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    base_pool = db.Column(db.Float, default=1000.0)
    quote_pool = db.Column(db.Float, default=1000.0)
    total_shares_yes = db.Column(db.Float, default=0.0)
    total_shares_no = db.Column(db.Float, default=0.0)

    contract = db.relationship('Contract', back_populates='amm_market', lazy='joined')
