import requests
import time
from flask import current_app

def warm_up_model(model_name="qwen2:7b", max_retries=3):
    """Warm up the Ollama model to reduce first-request latency"""
    for attempt in range(max_retries):
        try:
            # Make a simple request to load the model
            response = requests.post(
                current_app.config['OLLAMA_API_URL'],
                json={
                    'model': model_name,
                    'prompt': 'Hello',
                    'stream': False
                },
                timeout=120  # Increased timeout for model loading
            )
            
            if response.status_code == 200:
                print(f"Model {model_name} warmed up successfully")
                return True
            else:
                print(f"Warmup attempt {attempt + 1} failed: {response.status_code}")
                
        except Exception as e:
            print(f"Warmup attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(10)  # Wait before retry
    
    print(f"Failed to warm up model {model_name} after {max_retries} attempts")
    return False