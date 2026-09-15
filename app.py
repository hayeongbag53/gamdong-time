import os

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_wtf import CSRFProtect

load_dotenv()

from config import Config  # noqa: E402
from models import Admin, db  # noqa: E402

csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "로그인이 필요합니다."


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    from routes.admin import bp as admin_bp
    from routes.api import bp as api_bp
    from routes.auth import bp as auth_bp
    from routes.chatbot import bp as chatbot_bp
    from routes.history import bp as history_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()
        from seed import seed_database

        seed_database()

    return app


@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
