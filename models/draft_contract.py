from app.extensions import db
from datetime import datetime

class DraftContract(db.Model):
    __tablename__ = "draft_contracts"

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.String(64), unique=True, nullable=False)
    question = db.Column(db.String(512), nullable=False)
    outcomes = db.Column(db.PickleType, nullable=False)
    resolution_criteria = db.Column(db.String(512), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    city = db.Column(db.String(64), nullable=False)
    xp_weight = db.Column(db.Float, nullable=False)
    initial_odds = db.Column(db.Float, nullable=False)
    liquidity_cap = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(32), default="draft")

    def __repr__(self):
        return f"<DraftContract {self.contract_id} - {self.city}>"
