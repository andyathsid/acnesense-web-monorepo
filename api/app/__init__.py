from flask import Flask
from .config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize services if needed
    from app.utils.index_loader import load_index
    # Pass app instance directly to load_index
    app.index = load_index(app)
    
    # Register blueprints
    from app.routes import api_bp
    app.register_blueprint(api_bp)
    
    return app