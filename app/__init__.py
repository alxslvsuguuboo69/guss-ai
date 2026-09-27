import os
from flask import Flask
from app.config import Config

def create_app():
    # Obtiene la ruta absoluta de la carpeta raíz de la aplicación ('app')
    app_dir = os.path.dirname(os.path.abspath(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(app_dir, 'templates'),
        static_folder=os.path.join(app_dir, 'static'),
        static_url_path='/static'
    )

    app.config.from_object(Config)

    from app.routes.chat_routes import chat_bp
    app.register_blueprint(chat_bp)

    return app
