from models import Customer, OrderHistory, OrderProduct, Product


def search_history(filters):
    """filters: dict with any of company, industry, quantity_min,
    quantity_max, price_min, price_max, product, satisfaction_min,
    date_from, date_to."""

    query = OrderHistory.query.join(Customer)

    company = filters.get("company")
    if company:
        query = query.filter(Customer.company_name.ilike(f"%{company}%"))

    industry = filters.get("industry")
    if industry:
        query = query.filter(Customer.industry.ilike(f"%{industry}%"))

    if filters.get("quantity_min"):
        query = query.filter(OrderHistory.quantity >= filters["quantity_min"])
    if filters.get("quantity_max"):
        query = query.filter(OrderHistory.quantity <= filters["quantity_max"])

    if filters.get("price_min"):
        query = query.filter(OrderHistory.price_per_person >= filters["price_min"])
    if filters.get("price_max"):
        query = query.filter(OrderHistory.price_per_person <= filters["price_max"])

    if filters.get("satisfaction_min"):
        query = query.filter(OrderHistory.satisfaction_score >= filters["satisfaction_min"])

    if filters.get("date_from"):
        query = query.filter(OrderHistory.order_date >= filters["date_from"])
    if filters.get("date_to"):
        query = query.filter(OrderHistory.order_date <= filters["date_to"])

    product = filters.get("product")
    if product:
        query = (
            query.join(OrderProduct, OrderProduct.order_id == OrderHistory.id)
            .join(Product, Product.id == OrderProduct.product_id)
            .filter(Product.product_name.ilike(f"%{product}%"))
        )

    return query.order_by(OrderHistory.order_date.desc()).all()


def get_order_detail(order_id):
    return OrderHistory.query.get_or_404(order_id)


def serialize_order(order, similarity=None):
    return {
        "id": order.id,
        "company_name": order.customer.company_name if order.customer else None,
        "company_logo": order.customer.logo_url if order.customer else None,
        "industry": order.customer.industry if order.customer else None,
        "purpose": order.purpose,
        "quantity": order.quantity,
        "price_per_person": order.price_per_person,
        "total_price": order.total_price,
        "products": [
            {
                "name": op.product.product_name if op.product else None,
                "image_url": op.product.image_url if op.product else None,
                "unit_price": op.unit_price,
                "quantity": op.quantity,
            }
            for op in order.order_products
        ],
        "order_date": order.order_date.isoformat() if order.order_date else None,
        "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None,
        "delivery_days": order.delivery_days,
        "satisfaction_score": order.satisfaction_score,
        "reorder": order.reorder,
        "manager_comment": order.manager_comment,
        "request_detail": order.request_detail,
        "custom_detail": order.custom_detail,
        "similarity": similarity,
    }
