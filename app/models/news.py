from app import db
from datetime import datetime

class NewsSource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    selector = db.Column(db.String(100), nullable=False)
    date_selector = db.Column(db.String(100))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'selector': self.selector,
            'date_selector': self.date_selector,
            'active': self.active
        }

class NewsHeadline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    source_id = db.Column(db.Integer, db.ForeignKey('news_source.id'), nullable=False)
    source = db.relationship('NewsSource', backref='headlines')
    published_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
