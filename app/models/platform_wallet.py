# app/models/platform_wallet.py

from app import db

class PlatformWallet(db.Model):
    __tablename__ = 'platform_wallets'

    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    @property
    def total_fees(self):
        """Return the total accumulated fees."""
        return self.balance

    @classmethod
    def get_instance(cls):
        """Get or create the singleton PlatformWallet instance."""
        instance = cls.query.first()
        if not instance:
            instance = cls()
            db.session.add(instance)
            db.session.commit()
        return instance

    def add_fee(self, amount: float):
        """Add amount to platform wallet balance."""
        self.balance += amount
        db.session.commit()

    def __repr__(self):
        return f'<PlatformWallet balance={self.balance}>'

    created_at = db.Column(db.DateTime, server_default=db.func.now())
 932aef4 (LOCKED: All model stubs added, migrations clean through Badge/UserBadge)
