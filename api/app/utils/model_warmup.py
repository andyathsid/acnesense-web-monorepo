import time
import google.generativeai as genai
from flask import current_app
import numpy as np
import tensorflow as tf
from ultralytics import YOLO

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

def warm_up_diagnosis_models():
    """Warm up the diagnosis models (detection and classification) to reduce first-request latency"""
    try:
        # Get model paths
        detection_model_path = current_app.config.get('DETECTION_MODEL_PATH', 'models/detection/best.pt')
        classification_model_path = current_app.config.get('CLASSIFICATION_MODEL_PATH', 'models/classification/model.tflite')
        
        print("Warming up detection model...")
        # Load YOLO model
        detection_model = YOLO(detection_model_path)
        # Run inference on a small dummy image to initialize the model
        dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
        _ = detection_model.predict(source=dummy_img, conf=0.25, imgsz=640, device='cpu', verbose=False)
        
        print("Warming up classification model...")
        # Load TFLite model
        interpreter = tf.lite.Interpreter(model_path=classification_model_path)
        interpreter.allocate_tensors()
        
        # Get input and output details
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        # Create dummy input
        input_shape = input_details[0]['shape']
        dummy_input = np.zeros(input_shape, dtype=np.float32)
        
        # Run inference
        interpreter.set_tensor(input_details[0]['index'], dummy_input)
        interpreter.invoke()
        _ = interpreter.get_tensor(output_details[0]['index'])
        
        print("Diagnosis models warmed up successfully")
        return True
        
    except Exception as e:
        print(f"Failed to warm up diagnosis models: {str(e)}")
        return False