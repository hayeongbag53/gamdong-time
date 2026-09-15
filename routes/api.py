import json

from flask import Blueprint, jsonify, request, send_file
from flask_login import current_user

from models import ChatHistory, Customer, ProposalHistory, db
from services import history_service, proposal_doc_service, recommendation_service, similarity_service
from utils.decorators import api_login_required
from utils.validators import clean_text

bp = Blueprint("api", __name__, url_prefix="/api")


def _run_pipeline(message):
    conditions = similarity_service.extract_conditions(message)
    similar = similarity_service.search_similar_histories(conditions, limit=5)
    recommendation = recommendation_service.generate_recommendation(conditions, similar)
    return conditions, similar, recommendation


@bp.route("/chat", methods=["POST"])
@api_login_required
def chat():
    payload = request.get_json(silent=True) or {}
    message = clean_text(payload.get("message"))
    if not message:
        return jsonify({"error": "message가 필요합니다."}), 400

    conditions, similar, recommendation = _run_pipeline(message)

    chat_row = ChatHistory(
        admin_id=current_user.id,
        user_message=message,
        ai_response=recommendation["ai_text"],
    )
    db.session.add(chat_row)
    db.session.commit()

    return jsonify(
        {
            "parsed_conditions": {
                k: v for k, v in conditions.items() if k != "raw_text"
            },
            "similar_histories": [
                history_service.serialize_order(r["order"], r["similarity"]) for r in similar
            ],
            "recommendation": recommendation,
        }
    )


@bp.route("/history", methods=["GET"])
@api_login_required
def history_list():
    args = request.args
    filters = {
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
    orders = history_service.search_history(filters)
    return jsonify([history_service.serialize_order(o) for o in orders])


@bp.route("/history/<int:order_id>", methods=["GET"])
@api_login_required
def history_detail(order_id):
    order = history_service.get_order_detail(order_id)
    return jsonify(history_service.serialize_order(order))


@bp.route("/recommend", methods=["POST"])
@api_login_required
def recommend():
    payload = request.get_json(silent=True) or {}
    message = clean_text(payload.get("message"))
    if not message:
        return jsonify({"error": "message가 필요합니다."}), 400

    conditions, similar, recommendation = _run_pipeline(message)
    return jsonify(
        {
            "parsed_conditions": {k: v for k, v in conditions.items() if k != "raw_text"},
            "similar_histories": [
                history_service.serialize_order(r["order"], r["similarity"]) for r in similar
            ],
            "recommendation": recommendation,
        }
    )


@bp.route("/proposals", methods=["POST"])
@api_login_required
def save_proposal():
    payload = request.get_json(silent=True) or {}
    request_text = clean_text(payload.get("request_text"))
    final_proposal = clean_text(payload.get("final_proposal"), max_length=4000)
    if not request_text or not final_proposal:
        return jsonify({"error": "request_text와 final_proposal이 필요합니다."}), 400

    customer_name = clean_text(payload.get("customer_name"), max_length=100) or None
    customer = None
    if customer_name:
        customer = Customer.query.filter_by(company_name=customer_name).first()

    products = payload.get("products") or []
    if not isinstance(products, list):
        products = []
    references = payload.get("references") or []
    if not isinstance(references, list):
        references = []

    proposal = ProposalHistory(
        admin_id=current_user.id,
        customer_id=customer.id if customer else None,
        customer_name_text=customer_name,
        request_text=request_text,
        ai_proposal=clean_text(payload.get("ai_proposal"), max_length=4000),
        final_proposal=final_proposal,
        recommended_products_json=json.dumps(products[:10], ensure_ascii=False),
        expected_price=clean_text(payload.get("expected_price"), max_length=50) or None,
        reference_summary_json=json.dumps(references[:5], ensure_ascii=False),
    )
    db.session.add(proposal)
    db.session.commit()

    return jsonify(
        {
            "id": proposal.id,
            "message": "최종 제안이 저장되었습니다.",
            "download_url": f"/api/proposals/{proposal.id}/download",
        }
    )


@bp.route("/proposals/<int:proposal_id>/download", methods=["GET"])
@api_login_required
def download_proposal(proposal_id):
    proposal = ProposalHistory.query.get_or_404(proposal_id)
    buffer = proposal_doc_service.generate_proposal_docx(proposal)
    filename = f"제안서_{proposal.customer_name_text or '고객사미정'}_{proposal.id}.docx"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
