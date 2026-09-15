from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from models import Admin

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.is_active_flag and admin.check_password(password):
            login_user(admin)
            return redirect(url_for("chatbot.shop"))
        error = "이메일 또는 비밀번호가 올바르지 않습니다."
    return render_template("login.html", error=error)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
