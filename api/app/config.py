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
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'Qwen/Qwen2.5-7B-Instruct')
    OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
    VLLM_API_URL = os.getenv('VLLM_API_URL', 'http://localhost:8080/v1/completions')
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'vllm')  # Options: 'ollama', 'vllm'