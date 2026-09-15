from datetime import datetime

from . import db


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(50))
    company_size = db.Column(db.String(50))
    manager_name = db.Column(db.String(50))
    logo_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship("OrderHistory", back_populates="customer")
