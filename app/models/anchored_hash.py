# Placeholder model to resolve import error
from app.extensions import db

class AnchoredHash(db.Model):
    __tablename__ = 'anchored_hashes'

    id = db.Column(db.Integer, primary_key=True)
    hash_value = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
