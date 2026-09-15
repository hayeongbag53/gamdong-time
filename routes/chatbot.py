from flask import Blueprint, redirect, render_template, url_for
from flask_login import login_required

bp = Blueprint("chatbot", __name__)


@bp.route("/")
@login_required
def index():
    return redirect(url_for("chatbot.shop"))


@bp.route("/shop")
@login_required
def shop():
    return render_template("shop.html")
