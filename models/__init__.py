from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .admin import Admin  # noqa: E402,F401
from .customer import Customer  # noqa: E402,F401
from .product import Product  # noqa: E402,F401
from .order_history import OrderHistory, OrderProduct  # noqa: E402,F401
from .chat_history import ChatHistory  # noqa: E402,F401
from .proposal_history import ProposalHistory  # noqa: E402,F401
