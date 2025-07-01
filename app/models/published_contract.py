from app import db
from datetime import datetime

class PublishedContract(db.Model):
    __tablename__ = 'published_contracts'

    id = db.Column(db.Integer, primary_key=True)
    draft_id = db.Column(db.Integer, db.ForeignKey('contract_drafts.id'), nullable=True)
    city = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    actor = db.Column(db.String(128))
    resolution_method = db.Column(db.String(256))
    source_url = db.Column(db.String(512))
    resolution_date = db.Column(db.DateTime)
    current_odds_yes = db.Column(db.Float, default=0.5)
    current_odds_no = db.Column(db.Float, default=0.5)
    xp_threshold = db.Column(db.Integer, default=0)
    total_volume_points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "city": self.city,
            "title": self.title,
            "description": self.description,
            "actor": self.actor,
            "resolution_method": self.resolution_method,
            "source_url": self.source_url,
            "resolution_date": self.resolution_date.isoformat() if self.resolution_date else None,
            "current_odds_yes": self.current_odds_yes,
            "current_odds_no": self.current_odds_no,
            "xp_threshold": self.xp_threshold,
            "total_volume_points": self.total_volume_points,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
