from flask import Flask
from .config import Config
from flask_cors import CORS
from app.utils.auth_utils import initialize_token_cache

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app)
    
    # Initialize token cache
    initialize_token_cache(app)

    # Vector store initialization happens lazily in rag_service.py
    
    # Warm up models
    from app.utils.model_warmup import warm_up_diagnosis_models
    with app.app_context():
        warm_up_diagnosis_models()
    
    # Register blueprints
    from app.routes import api_bp
    app.register_blueprint(api_bp)
    
    return app
