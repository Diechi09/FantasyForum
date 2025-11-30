import os

from flask import Flask
from flask_wtf.csrf import generate_csrf

from .extensions import csrf, db, login_manager
from .services.monitoring import configure_application_insights, register_monitoring


def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    templates_path = os.path.join(base_dir, "..", "templates")
    static_path = os.path.join(base_dir, "..", "static")

    app = Flask(
        __name__, template_folder=os.path.abspath(templates_path), static_folder=os.path.abspath(static_path)
    )

    app.config["SECRET_KEY"] = "888888888188881"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    csrf.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message_category = "danger"

    from .models import User  # noqa: WPS433

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)

    from .routes import register_routes

    register_routes(app)
    register_monitoring(app)
    configure_application_insights(app)
    return app


from .models import Comment, Post, User  # noqa: E402

__all__ = ["create_app", "db", "login_manager", "csrf", "User", "Post", "Comment"]
