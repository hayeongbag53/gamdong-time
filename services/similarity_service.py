"""Rule-based natural-language condition extraction and similarity scoring.

This is the MVP implementation called out in the spec ("초기 MVP에서는 규칙
기반 점수 방식으로 구현할 수 있다"). It is intentionally dependency-free
(regex + keyword lists) so the whole flow works without any external AI
API; `services/ai_service.py` is where a real LLM/embedding model would
plug in later without changing the callers.
"""

import re

from models import Customer, OrderHistory

PURPOSE_KEYWORDS = [
    "웰컴키트", "온보딩키트", "온보딩 키트", "기념품", "행사상품", "행사 상품",
    "답례품", "창립기념품", "창립 기념품", "명절선물", "명절 선물", "판촉물",
]

INDUSTRY_KEYWORDS = [
    "IT", "아이티", "제조", "금융", "은행", "증권", "보험", "삼성", "계열사",
    "대기업", "중견기업", "중소기업", "스타트업", "공기업", "유통", "바이오",
]

PRODUCT_SYNONYMS = {
    "텀블러": ["텀블러"],
    "파우치": ["파우치"],
    "노트": ["노트", "다이어리"],
    "볼펜": ["볼펜", "펜"],
    "메시지카드": ["메시지카드", "메시지 카드", "카드"],
    "무선충전기": ["무선충전기", "무선 충전기", "충전기"],
}

_QUANTITY_RE = re.compile(r"([\d,]+)\s*(?:명|개)")
_MAN_WON_RE = re.compile(r"([\d,]+(?:\.\d+)?)\s*만\s*원")
_WON_RE = re.compile(r"([\d,]{4,})\s*원")
_WEEK_RE = re.compile(r"(\d+)\s*주")
_DAY_RE = re.compile(r"(\d+)\s*일")


def _to_int(num_str):
    return int(num_str.replace(",", ""))


def extract_conditions(text):
    """Parse a free-form Korean request into structured search conditions."""
    text = text or ""

    conditions = {
        "raw_text": text,
        "quantity": None,
        "budget_per_person": None,
        "purpose": None,
        "industry": None,
        "preferred_products": [],
        "delivery_days": None,
        "referenced_company": None,
    }

    qty_match = _QUANTITY_RE.search(text)
    if qty_match:
        conditions["quantity"] = _to_int(qty_match.group(1))

    man_match = _MAN_WON_RE.search(text)
    if man_match:
        conditions["budget_per_person"] = float(man_match.group(1)) * 10000
    else:
        won_match = _WON_RE.search(text)
        if won_match:
            conditions["budget_per_person"] = float(_to_int(won_match.group(1)))

    for kw in PURPOSE_KEYWORDS:
        if kw in text:
            conditions["purpose"] = kw
            break

    for kw in INDUSTRY_KEYWORDS:
        if kw in text:
            conditions["industry"] = kw
            break

    preferred = []
    for canonical, synonyms in PRODUCT_SYNONYMS.items():
        if any(s in text for s in synonyms):
            preferred.append(canonical)
    conditions["preferred_products"] = preferred

    week_match = _WEEK_RE.search(text)
    if week_match:
        conditions["delivery_days"] = int(week_match.group(1)) * 7
    else:
        day_match = _DAY_RE.search(text)
        if day_match:
            conditions["delivery_days"] = int(day_match.group(1))

    for customer in Customer.query.all():
        if customer.company_name and customer.company_name in text:
            conditions["referenced_company"] = customer.company_name
            break

    return conditions


def _dimension_scores(conditions, order):
    """Return {dimension: (weight, score)} only for dimensions the user
    actually gave a condition for, so an unspecified condition is skipped
    rather than penalizing every candidate equally."""

    dims = {}

    if conditions.get("purpose"):
        weight = 30
        score = 1.0 if order.purpose and conditions["purpose"] in order.purpose else 0.0
        dims["purpose"] = (weight, score)

    if conditions.get("budget_per_person") and order.price_per_person:
        weight = 20
        target = conditions["budget_per_person"]
        diff_ratio = abs(order.price_per_person - target) / target
        dims["budget"] = (weight, max(0.0, 1 - diff_ratio))

    if conditions.get("quantity") and order.quantity:
        weight = 15
        target = conditions["quantity"]
        diff_ratio = abs(order.quantity - target) / target
        dims["quantity"] = (weight, max(0.0, 1 - diff_ratio))

    if conditions.get("industry"):
        weight = 10
        industry = (order.customer.industry or "") if order.customer else ""
        score = 1.0 if conditions["industry"] in industry else 0.0
        dims["industry"] = (weight, score)

    if conditions.get("preferred_products"):
        weight = 15
        names = order.product_names
        matched = sum(
            1 for p in conditions["preferred_products"]
            if any(p in n for n in names)
        )
        dims["products"] = (weight, matched / len(conditions["preferred_products"]))

    if conditions.get("delivery_days") and order.delivery_days:
        weight = 10
        target = conditions["delivery_days"]
        diff_ratio = abs(order.delivery_days - target) / target
        dims["delivery"] = (weight, max(0.0, 1 - diff_ratio))

    return dims


def calculate_similarity(conditions, order):
    """0-100 similarity score between extracted conditions and one order."""
    dims = _dimension_scores(conditions, order)
    if not dims:
        # Nothing concrete to compare on — fall back to satisfaction so the
        # list still has a sensible order instead of an arbitrary tie.
        return round((order.satisfaction_score or 3.0) / 5.0 * 60, 1)

    total_weight = sum(w for w, _ in dims.values())
    total_score = sum(w * s for w, s in dims.values())
    return round(total_score / total_weight * 100, 1)


def search_similar_histories(conditions, limit=5):
    query = OrderHistory.query.join(Customer)

    if conditions.get("referenced_company"):
        query = query.filter(Customer.company_name == conditions["referenced_company"])

    orders = query.all()
    scored = [
        {"order": order, "similarity": calculate_similarity(conditions, order)}
        for order in orders
    ]
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:limit]
