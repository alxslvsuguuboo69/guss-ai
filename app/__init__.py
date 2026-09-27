import os
from flask import Flask
from app.config import Config

def create_app():
    # Se define la ruta base de la carpeta 'app'
    base_dir = os.path.abspath(os.path.dirname(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, 'templates'),
        static_folder=os.path.join(base_dir, 'static')
    )

    app.config.from_object(Config)

    from app.routes.chat_routes import chat_bp
    app.register_blueprint(chat_bp)

    return app
