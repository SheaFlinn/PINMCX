from app import db

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dummy_field = db.Column(db.String(64), nullable=True)  # stub only
