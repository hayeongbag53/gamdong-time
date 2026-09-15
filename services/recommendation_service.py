"""Turn a set of similar past orders into a concrete product/price/reason
recommendation, per spec section 15-17. The draft is always built from real
order-history rows (never invented figures); `ai_service` may then rewrite
the wording, but the underlying facts come from here.
"""

from services import ai_service

TOP_N = 3


def _weighted_product_scores(top_results):
    scores = {}
    for result in top_results:
        order = result["order"]
        weight = (order.satisfaction_score or 3.0) * (result["similarity"] / 100 or 0.1)
        for op in order.order_products:
            if not op.product:
                continue
            name = op.product.product_name
            scores[name] = scores.get(name, 0) + weight
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


def _price_range(top_results, conditions):
    if conditions.get("budget_per_person"):
        budget = conditions["budget_per_person"]
        low, high = budget * 0.94, budget
    else:
        prices = [r["order"].price_per_person for r in top_results if r["order"].price_per_person]
        if not prices:
            return None
        low, high = min(prices), max(prices)
    return f"{int(low):,} ~ {int(high):,}원"


def _build_reasons(top_results, conditions):
    reasons = []
    if conditions.get("purpose"):
        reasons.append(f"현재 요청 목적({conditions['purpose']})과 동일한 과거 사례 존재")
    if conditions.get("quantity"):
        reasons.append("유사한 규모의 주문 수량 사례 존재")
    if conditions.get("budget_per_person"):
        reasons.append("현재 요청 예산 범위 내 구성 가능")
    high_satisfaction = [r for r in top_results if (r["order"].satisfaction_score or 0) >= 4.5]
    if high_satisfaction:
        best = high_satisfaction[0]["order"]
        reasons.append(
            f"{best.customer.company_name} 사례 기준 고객 만족도 {best.satisfaction_score:.1f}점"
        )
    if any(r["order"].reorder for r in top_results):
        reasons.append("재주문이 발생했던 상품 구성 포함")
    if not reasons:
        reasons.append("입력하신 조건과 부분적으로 유사한 과거 사례를 참고했습니다")
    return reasons


def _additional_suggestions(top_results, conditions, recommended_products):
    suggestions = []

    if conditions.get("quantity") and conditions["quantity"] >= 500:
        suggestions.append("주문 수량이 500개 이상이므로 패키지 커스텀 옵션을 함께 제안해보세요")

    if conditions.get("delivery_days") and conditions["delivery_days"] <= 21:
        suggestions.append(
            f"납기가 {conditions['delivery_days']}일이므로 국내 재고 상품 중심으로 구성하는 것이 안전합니다"
        )

    budget = conditions.get("budget_per_person")
    if budget and recommended_products:
        prod_names = [p for p, _ in recommended_products]
        if len(prod_names) >= 3:
            suggestions.append(
                f"예산이 빠듯하다면 '{prod_names[-1]}'을(를) 제외해 단가를 낮추는 방안도 검토해보세요"
            )

    if conditions.get("industry") and "IT" in (conditions.get("industry") or ""):
        suggestions.append("과거 IT기업 사례에서는 메시지 카드 등 개인화 구성 요소의 만족도가 높았습니다")

    return suggestions


def generate_recommendation(conditions, similar_results):
    if not similar_results:
        return {
            "products": [],
            "expected_price": None,
            "reasons": [],
            "suggestions": [],
            "ai_text": (
                "현재 조건과 충분히 유사한 과거 주문 사례를 찾지 못했습니다.\n\n"
                "검색 범위를 확대하여 다음 조건으로 다시 확인할 수 있습니다.\n"
                "- 예산 ±20%\n- 주문 수량 ±30%\n- 동일 목적의 다른 업종\n\n"
                "확대 검색을 진행하시겠습니까?"
            ),
        }

    top_results = similar_results[:TOP_N]
    product_scores = _weighted_product_scores(top_results)
    recommended_products = product_scores[:4] or [
        (name, 1) for name in top_results[0]["order"].product_names[:4]
    ]
    product_names = [p for p, _ in recommended_products]

    expected_price = _price_range(top_results, conditions)
    reasons = _build_reasons(top_results, conditions)
    suggestions = _additional_suggestions(top_results, conditions, recommended_products)

    top_order = top_results[0]["order"]
    companies = ", ".join(
        sorted({r["order"].customer.company_name for r in top_results if r["order"].customer})
    )

    fallback_lines = [
        f"현재 고객 요청과 가장 유사한 사례는 {companies}의 주문입니다.",
        "",
        f"{top_order.customer.company_name}은(는) {top_order.quantity}명 규모로 "
        f"1인당 {int(top_order.price_per_person):,}원의 구성을 제공했으며, "
        f"만족도 {top_order.satisfaction_score or '-'}점을 기록했습니다.",
        "",
        "추천 구성",
    ]
    fallback_lines += [f"{i+1}. {name}" for i, name in enumerate(product_names)]
    fallback_lines += [
        "",
        f"예상 단가: {expected_price}" if expected_price else "",
        "",
        "추천 이유",
    ]
    fallback_lines += [f"- {r}" for r in reasons]
    fallback_text = "\n".join(line for line in fallback_lines if line != "" or True).strip()

    system_prompt = (
        "당신은 사내 기업선물몰 '감동타임'의 영업 지원 AI입니다. 아래 제공된 과거 주문 데이터"
        "(회사명, 수량, 단가, 만족도, 상품 구성)만을 근거로 답변하세요. 제공되지 않은 "
        "회사명, 상품, 가격을 임의로 만들어내지 마세요. 한국어로, 간결하고 실무적으로 답하세요."
    )
    user_prompt = (
        f"현재 고객 요청: {conditions.get('raw_text')}\n\n"
        f"참고할 과거 유사 사례 (유사도순): "
        + "; ".join(
            f"{r['order'].customer.company_name} (수량 {r['order'].quantity}, "
            f"단가 {int(r['order'].price_per_person):,}원, 만족도 {r['order'].satisfaction_score}, "
            f"유사도 {r['similarity']}%)"
            for r in top_results
        )
        + f"\n\n초안 추천: {fallback_text}\n\n"
        "위 초안을 다듬어 고객 제안용 한국어 답변으로 작성하세요."
    )

    ai_text = ai_service.generate_text(system_prompt, user_prompt, fallback_text)

    return {
        "products": product_names,
        "expected_price": expected_price,
        "reasons": reasons,
        "suggestions": suggestions,
        "ai_text": ai_text,
    }
