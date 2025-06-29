# app/models/news_source.py

from app import db

class NewsSource(db.Model):
    __tablename__ = 'news_sources'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    url = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())