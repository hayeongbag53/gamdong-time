from flask import Blueprint, render_template
from flask_login import current_user, login_required

from models import ChatHistory, Customer, OrderHistory, ProposalHistory

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@login_required
def dashboard():
    stats = {
        "customer_count": Customer.query.count(),
        "order_count": OrderHistory.query.count(),
        "proposal_count": ProposalHistory.query.count(),
        "recent_chats": (
            ChatHistory.query.filter_by(admin_id=current_user.id)
            .order_by(ChatHistory.created_at.desc())
            .limit(5)
            .all()
        ),
    }
    return render_template("admin/dashboard.html", stats=stats)
