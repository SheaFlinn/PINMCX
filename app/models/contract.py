from app import db
from datetime import datetime

class ContractDraft(db.Model):
    __tablename__ = 'contract_drafts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    purpose = db.Column(db.Text)
    scope = db.Column(db.Text)
    terms = db.Column(db.JSON)
    status = db.Column(db.String(50), default="draft")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_contract(self):
        from app.models.market import Market
        return Market(
            title=self.title,
            description=self.purpose,
            resolution_method=self.scope,
            source_url=self.terms.get("resolution_source"),
            resolution_date=datetime.utcnow()
        )
