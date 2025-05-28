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
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gemini-2.5-flash')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')