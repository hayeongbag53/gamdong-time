"""One-time sample data so the demo scenario in the spec (section 31) works
out of the box: a handful of customers, a product catalog, and past orders
with satisfaction/reorder data for the similarity search to work against."""

from datetime import date

from models import Admin, Customer, OrderHistory, OrderProduct, Product, db

LOGO_DIR = "/static/uploads/logos"
PRODUCT_DIR = "/static/uploads/products"


def seed_database():
    if Admin.query.first():
        return  # already seeded

    admin = Admin(
        employee_number="EMP001",
        name="관리자",
        email="admin@company.com",
        department="영업팀",
    )
    admin.set_password("admin1234")
    db.session.add(admin)

    customers = {
        "A기업": Customer(company_name="A기업", industry="제조", company_size="대기업", manager_name="김담당", logo_url=f"{LOGO_DIR}/a-corp.svg"),
        "B기업": Customer(company_name="B기업", industry="금융", company_size="대기업", manager_name="이담당", logo_url=f"{LOGO_DIR}/b-corp.svg"),
        "C기업": Customer(company_name="C기업", industry="IT", company_size="중견기업", manager_name="박담당", logo_url=f"{LOGO_DIR}/c-corp.svg"),
        "삼성전자": Customer(company_name="삼성전자", industry="제조", company_size="대기업", manager_name="최담당", logo_url=f"{LOGO_DIR}/samsung-electronics.svg"),
        "D스타트업": Customer(company_name="D스타트업", industry="IT", company_size="스타트업", manager_name="정담당", logo_url=f"{LOGO_DIR}/d-startup.svg"),
    }
    for c in customers.values():
        db.session.add(c)

    products = {
        "텀블러": Product(product_name="텀블러", category="생활용품", price=15000, image_url=f"{PRODUCT_DIR}/tumbler.svg"),
        "파우치": Product(product_name="파우치", category="생활용품", price=12000, image_url=f"{PRODUCT_DIR}/pouch.svg"),
        "노트": Product(product_name="노트", category="문구", price=6000, image_url=f"{PRODUCT_DIR}/notebook.svg"),
        "볼펜": Product(product_name="볼펜", category="문구", price=3000, image_url=f"{PRODUCT_DIR}/pen.svg"),
        "메시지카드": Product(product_name="메시지카드", category="문구", price=2000, image_url=f"{PRODUCT_DIR}/message_card.svg"),
        "무선충전기": Product(product_name="무선충전기", category="전자기기", price=25000, image_url=f"{PRODUCT_DIR}/charger.svg"),
    }
    for p in products.values():
        db.session.add(p)

    db.session.flush()  # assign ids

    def make_order(customer_name, purpose, quantity, price_per_person, item_names,
                    order_date, delivery_date, satisfaction, reorder, request_detail,
                    custom_detail, manager_comment):
        order = OrderHistory(
            customer_id=customers[customer_name].id,
            purpose=purpose,
            quantity=quantity,
            price_per_person=price_per_person,
            total_price=price_per_person * quantity,
            request_detail=request_detail,
            custom_detail=custom_detail,
            order_date=order_date,
            delivery_date=delivery_date,
            satisfaction_score=satisfaction,
            reorder=reorder,
            manager_comment=manager_comment,
        )
        db.session.add(order)
        db.session.flush()
        for name in item_names:
            product = products[name]
            db.session.add(
                OrderProduct(order_id=order.id, product_id=product.id, quantity=quantity, unit_price=product.price)
            )
        return order

    make_order(
        "A기업", "웰컴키트", 500, 48000, ["텀블러", "파우치", "노트"],
        date(2025, 9, 1), date(2025, 9, 19), 4.8, True,
        "신입사원 500명 대상 웰컴키트, 1인당 예산 5만원, 텀블러 필수 포함 요청",
        "회사 로고 각인 텀블러, 파우치 색상 2종 선택",
        "고객사 담당자 매우 만족, 다음 분기 재주문 협의 중",
    )
    make_order(
        "B기업", "웰컴키트", 600, 52000, ["텀블러", "파우치", "무선충전기"],
        date(2025, 6, 10), date(2025, 6, 30), 4.6, False,
        "신입사원 600명 웰컴키트, IT 기기 포함 희망",
        "무선충전기 회사 컬러 맞춤 제작",
        "납기 준수, 상품 구성 만족도 높음",
    )
    make_order(
        "C기업", "온보딩키트", 300, 65000, ["텀블러", "무선충전기", "메시지카드"],
        date(2025, 8, 5), date(2025, 8, 20), 4.9, True,
        "IT기업 신입 개발자 300명 대상 고급 온보딩 키트, 예산 1인당 7만원",
        "무선충전기 고급형, 메시지카드 개인 이름 각인",
        "고급스러운 구성으로 임직원 반응 매우 좋음, 익년 재주문 확정",
    )
    make_order(
        "삼성전자", "기념품", 1000, 32000, ["텀블러", "노트", "볼펜"],
        date(2025, 3, 12), date(2025, 4, 2), 4.3, True,
        "창립기념일 기념품, 1000명, 3만원대 예산",
        "노트 표지 특수 제작",
        "대량 생산 납기 이슈 있었으나 최종 만족",
    )
    make_order(
        "D스타트업", "행사상품", 150, 28000, ["파우치", "노트", "볼펜", "메시지카드"],
        date(2025, 5, 20), date(2025, 6, 3), 4.1, False,
        "스타트업 창립기념 행사 답례품, 3만원 이하 예산",
        "파우치에 캐릭터 인쇄",
        "예산 대비 만족스러운 구성",
    )
    make_order(
        "A기업", "행사상품", 200, 30000, ["파우치", "노트"],
        date(2024, 11, 1), date(2024, 11, 15), 4.5, True,
        "연말 행사 답례품, 200명 대상",
        "파우치 연말 한정 디자인",
        "재주문 고객사, 신뢰도 높음",
    )

    db.session.commit()
