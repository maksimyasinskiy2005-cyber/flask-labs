import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()

# Налаштування перенаправлення для неавторизованих користувачів (Частина 2, п. 6)
login_manager.login_view = "user.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"


def create_app(config_name: str = "config.DevConfig"):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_name)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    from app.routes import post_bp
    from app.user_routes import user_bp

    app.register_blueprint(post_bp)
    app.register_blueprint(user_bp)

    return app
