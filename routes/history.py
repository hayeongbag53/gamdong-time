from flask import Blueprint, render_template, request
from flask_login import login_required

from services.history_service import get_order_detail, search_history

bp = Blueprint("history", __name__, url_prefix="/admin/history")


def _filters_from_args(args):
    return {
        "company": args.get("company") or None,
        "industry": args.get("industry") or None,
        "quantity_min": args.get("quantity_min", type=int),
        "quantity_max": args.get("quantity_max", type=int),
        "price_min": args.get("price_min", type=float),
        "price_max": args.get("price_max", type=float),
        "satisfaction_min": args.get("satisfaction_min", type=float),
        "product": args.get("product") or None,
        "date_from": args.get("date_from") or None,
        "date_to": args.get("date_to") or None,
    }


@bp.route("/")
@login_required
def list_view():
    filters = _filters_from_args(request.args)
    orders = search_history(filters)
    return render_template("admin/history.html", orders=orders, filters=filters)


@bp.route("/<int:order_id>")
@login_required
def detail_view(order_id):
    order = get_order_detail(order_id)
    return render_template("admin/history_detail.html", order=order)
