from app.extensions import db

class PlatformWallet(db.Model):
    """Platform wallet to track cumulative platform fees."""
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float, default=0.0)

    @property
    def total_fees(self):
        """Return the total accumulated fees."""
        return self.balance

    @classmethod
    def get_instance(cls):
        """Get or create the singleton PlatformWallet instance."""
        wallet = cls.query.get(1)
        if not wallet:
            wallet = cls(id=1, balance=0.0)
            db.session.add(wallet)
            db.session.commit()
        return wallet

    def add_fee(self, amount: float) -> None:
        """Add a fee amount to the wallet balance."""
        self.balance += amount
        db.session.commit()

    def __repr__(self):
        return f'<PlatformWallet id={self.id} balance={self.balance:.2f}>'
