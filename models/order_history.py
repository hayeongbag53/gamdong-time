from datetime import datetime

from . import db


class OrderHistory(db.Model):
    __tablename__ = "order_histories"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    purpose = db.Column(db.String(100))
    quantity = db.Column(db.Integer, nullable=False, default=0)
    price_per_person = db.Column(db.Float, nullable=False, default=0)
    total_price = db.Column(db.Float, nullable=False, default=0)
    request_detail = db.Column(db.Text)
    custom_detail = db.Column(db.Text)
    order_date = db.Column(db.Date)
    delivery_date = db.Column(db.Date)
    satisfaction_score = db.Column(db.Float)
    reorder = db.Column(db.Boolean, default=False)
    manager_comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="orders")
    order_products = db.relationship(
        "OrderProduct", back_populates="order", cascade="all, delete-orphan"
    )

    @property
    def delivery_days(self):
        if self.order_date and self.delivery_date:
            return (self.delivery_date - self.order_date).days
        return None

    @property
    def product_names(self):
        return [op.product.product_name for op in self.order_products if op.product]


class OrderProduct(db.Model):
    __tablename__ = "order_products"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order_histories.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False, default=0)

    order = db.relationship("OrderHistory", back_populates="order_products")
    product = db.relationship("Product")
