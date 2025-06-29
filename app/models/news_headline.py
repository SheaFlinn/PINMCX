# app/models/news_headline.py

from app import db

class NewsHeadline(db.Model):
    __tablename__ = 'news_headlines'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())