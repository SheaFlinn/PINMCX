from app import db
from datetime import datetime

class ContractDraft(db.Model):
    __tablename__ = 'contract_drafts'

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(256), nullable=False)
    actor = db.Column(db.String(128))
    scope = db.Column(db.Text)
    timeline = db.Column(db.String(128))
    refined_title = db.Column(db.String(256))
    weight = db.Column(db.Float, default=0.5)
    bias_score = db.Column(db.Float, default=0.0)
    stage_log = db.Column(db.JSON, default=list)
    status = db.Column(db.String(32), default="draft")  # options: draft, rejected, published
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "city": self.city,
            "title": self.title,
            "refined_title": self.refined_title,
            "actor": self.actor,
            "scope": self.scope,
            "timeline": self.timeline,
            "weight": self.weight,
            "bias_score": self.bias_score,
            "stage_log": self.stage_log,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
