import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        load_dotenv(".env.prod", override=True)
    else:
        load_dotenv(".env.dev", override=True)
        
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Knowledge base paths
    ACNE_TYPES_PATH = os.getenv('ACNE_TYPES_PATH', 'data/knowledge-base/acne_types.csv')
    FAQS_PATH = os.getenv('FAQS_PATH', 'data/knowledge-base/faqs.csv')
    
    # LLM configuration
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gemini-2.5-flash-preview-05-20')
    
    # Extract project and endpoint IDs from environment variables
    PROJECT_ID = os.getenv('PROJECT_ID', '143761779858')
    REGION = os.getenv('REGION', 'asia-southeast1')
    ENDPOINT_ID = os.getenv('ENDPOINT_ID', '2946528434718769152')
    
    # Gemini model settings
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-preview-05-20')
    GEMINI_LOCATION = os.getenv('GEMINI_LOCATION', 'us-central1')
    
    # Build the Vertex AI URL 
    VLLM_API_URL = os.getenv('VLLM_API_URL', 
                        f"https://{REGION.strip()}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID.strip()}/locations/{REGION.strip()}/endpoints/{ENDPOINT_ID.strip()}")
    
    # Additional LLM settings
    LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '2048'))
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.7'))
    LLM_TOP_P = float(os.getenv('LLM_TOP_P', '0.95'))
    LLM_TIMEOUT = int(os.getenv('LLM_TIMEOUT', '60'))
    
    # File storage paths
    UPLOAD_DIR = os.getenv('UPLOAD_DIR', 'instance/uploads')
    CROP_DIR = os.getenv('CROP_DIR', 'instance/crops')
    RESULTS_DIR = os.getenv('RESULTS_DIR', 'instance/results')
    
    # ML models paths
    DETECTION_MODEL_PATH = os.getenv('DETECTION_MODEL_PATH', 'models/detection/yolo_v2.tflite')
    CLASSIFICATION_MODEL_PATH = os.getenv('CLASSIFICATION_MODEL_PATH', 'models/classification/cnn_v1.tflite')
    CLASS_INDEX_PATH = os.getenv('CLASS_INDEX_PATH', 'models/classification/labels.json')
    
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'service-account-key.json')
    
    # Qdrant configuration
    QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
    QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
    QDRANT_COLLECTION_NAME = os.getenv('QDRANT_COLLECTION_NAME', 'acne_knowledge_base')
    VERTEX_AI_EMBEDDING_MODEL = os.getenv('VERTEX_AI_EMBEDDING_MODEL', 'text-embedding-004')
