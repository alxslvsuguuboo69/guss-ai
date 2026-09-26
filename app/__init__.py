from flask import Flask
from app.config import Config
from app.routes.chat import chat_bp

def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(config_class)

    app.register_blueprint(chat_bp)

    return app
