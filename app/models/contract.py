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
        import json
        from app.models.published_contract import Contract
        terms = self.terms
        if isinstance(terms, str):
            try:
                terms = json.loads(terms)
            except Exception:
                terms = {}
        return Contract(
            city=getattr(self, 'city', '') or '',
            title=self.title,
            description=self.purpose,
            resolution_method=self.scope,
            source_url=terms.get("resolution_source"),
            resolution_date=datetime.utcnow()  # Placeholder
        )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "purpose": self.purpose,
            "scope": self.scope,
            "terms": self.terms,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
