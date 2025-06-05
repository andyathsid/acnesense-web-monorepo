import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Supabase configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Knowledge base paths
    ACNE_TYPES_PATH = os.getenv('ACNE_TYPES_PATH', 'data/knowledge-base/acne_types.csv')
    FAQS_PATH = os.getenv('FAQS_PATH', 'data/knowledge-base/faqs.csv')
    
    # LLM configuration
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gemini-2.0-flash')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # File storage paths
    UPLOAD_DIR = os.getenv('UPLOAD_DIR', 'instance/uploads')
    CROP_DIR = os.getenv('CROP_DIR', 'instance/crops')
    RESULTS_DIR = os.getenv('RESULTS_DIR', 'instance/results')
    
    # ML models paths
    DETECTION_MODEL_PATH = os.getenv('DETECTION_MODEL_PATH', 'models/detection/best_float32.tflite')
    CLASSIFICATION_MODEL_PATH = os.getenv('CLASSIFICATION_MODEL_PATH', 'models/classification/model.tflite')
    CLASS_INDEX_PATH = os.getenv('CLASS_INDEX_PATH', 'models/classification/labels.json')