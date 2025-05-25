from flask import Flask
from .config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize services
    from app.utils.index_loader import load_index
    app.index = load_index(app)
    
    # Warm up the model
    from app.utils.model_warmup import warm_up_model
    with app.app_context():
        warm_up_model(app.config['DEFAULT_MODEL'])
    
    # Register blueprints
    from app.routes import api_bp
    app.register_blueprint(api_bp)
    
    return app