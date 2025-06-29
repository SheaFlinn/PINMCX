# app/models/platform_wallet.py

from app import db

class PlatformWallet(db.Model):
    __tablename__ = 'platform_wallets'

    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())