from functools import wraps

from flask import jsonify
from flask_login import current_user


def api_login_required(view):
    """Like flask_login's login_required, but returns 401 JSON instead of
    redirecting to the login page — used for /api/* endpoints called from
    JavaScript rather than a browser navigation."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        return view(*args, **kwargs)

    return wrapped
