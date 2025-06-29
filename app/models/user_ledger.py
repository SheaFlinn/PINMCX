from app import db
from datetime import datetime

class UserLedger(db.Model):
    __tablename__ = 'user_ledger'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='ledger_entries')

    def __init__(self, user_id, amount, transaction_type, description=None):
        self.user_id = user_id
        self.amount = amount
        self.transaction_type = transaction_type
        self.description = description

    def __repr__(self):
        return f'<UserLedger {self.id}: {self.transaction_type} - {self.amount}>'
