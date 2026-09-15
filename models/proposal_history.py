from datetime import datetime

from . import db


class ProposalHistory(db.Model):
    __tablename__ = "proposal_histories"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)
    customer_name_text = db.Column(db.String(100))
    request_text = db.Column(db.Text, nullable=False)
    ai_proposal = db.Column(db.Text)
    final_proposal = db.Column(db.Text)
    recommended_products_json = db.Column(db.Text)  # JSON list[str]
    expected_price = db.Column(db.String(50))
    reference_summary_json = db.Column(db.Text)  # JSON list[dict]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship("Admin")
    customer = db.relationship("Customer")
