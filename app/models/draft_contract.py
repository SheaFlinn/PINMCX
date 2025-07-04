from app.extensions import db
import uuid
from datetime import datetime

class DraftContract(db.Model):
    __tablename__ = "contract_drafts"  # MUST MATCH exactly

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    question = db.Column(db.String(256), nullable=False)
    outcomes = db.Column(db.PickleType, nullable=False)
    resolution_criteria = db.Column(db.String(256), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    city = db.Column(db.String(64), nullable=False)
    xp_weight = db.Column(db.Float, nullable=False, default=1.0)
    initial_odds = db.Column(db.Float, nullable=False, default=0.5)
    liquidity_cap = db.Column(db.Integer, nullable=False, default=1000)
    source = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(64), nullable=False, default="draft")

    def to_dict(self):
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "question": self.question,
            "outcomes": self.outcomes,
            "resolution_criteria": self.resolution_criteria,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "city": self.city,
            "xp_weight": self.xp_weight,
            "initial_odds": self.initial_odds,
            "liquidity_cap": self.liquidity_cap,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "status": self.status
        }
