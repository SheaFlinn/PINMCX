from app.extensions import db
from datetime import datetime

class League(db.Model):
    __tablename__ = 'leagues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Add this relationship:
    members = db.relationship("LeagueMember", back_populates="league")
