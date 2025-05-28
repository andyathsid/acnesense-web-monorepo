import time
import google.generativeai as genai
from flask import current_app

def warm_up_model(model_name="gemini-2.5-flash", max_retries=3):
    """Warm up the Gemini model to reduce first-request latency"""
    for attempt in range(max_retries):
        try:
            # Configure the Gemini API
            genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
            
            # Create a Gemini model instance
            generation_config = {
                "temperature": 0.4,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 128,  # Small output for warmup
            }
            
            # Make a simple request to test the model
            model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
            response = model.generate_content("Hello")
            
            print(f"Model {model_name} warmed up successfully")
            return True
            
        except Exception as e:
            print(f"Warmup attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(10)  # Wait before retry
    
    print(f"Failed to warm up model {model_name} after {max_retries} attempts")
    return False