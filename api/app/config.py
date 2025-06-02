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
    
    model_name = os.getenv('DEFAULT_MODEL', 'Qwen2.5-3B-Instruct-AWQ')
    if not model_name.startswith('/models/'):
        model_name = f"/models/{model_name}"
    DEFAULT_MODEL = model_name
    VLLM_API_URL = os.getenv('VLLM_API_URL', 'http://acne-sense-vllm:8080/v1')
    
    VERTEX_AI_API_KEY = os.getenv('VERTEX_AI_API_KEY', '')
    
    # File storage paths
    UPLOAD_DIR = os.getenv('UPLOAD_DIR', 'instance/uploads')
    CROP_DIR = os.getenv('CROP_DIR', 'instance/crops')
    RESULTS_DIR = os.getenv('RESULTS_DIR', 'instance/results')
    
    # ML models paths
    DETECTION_MODEL_PATH = os.getenv('DETECTION_MODEL_PATH', 'models/detection/yolo_v1.tflite')
    CLASSIFICATION_MODEL_PATH = os.getenv('CLASSIFICATION_MODEL_PATH', 'models/classification/cnn_v1.tflite')
    CLASS_INDEX_PATH = os.getenv('CLASS_INDEX_PATH', 'models/classification/labels.json')
