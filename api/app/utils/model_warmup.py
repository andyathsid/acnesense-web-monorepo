from flask import current_app
import numpy as np
import tflite_runtime.interpreter as tflite

def warm_up_diagnosis_models():
    """Warm up the diagnosis models (detection and classification) to reduce first-request latency"""
    try:
        # Get model paths
        detection_model_path = current_app.config.get('DETECTION_MODEL_PATH', 'models/detection/best.tflite')
        classification_model_path = current_app.config.get('CLASSIFICATION_MODEL_PATH', 'models/classification/model.tflite')
        
        print("Warming up detection model...")
        # Load TFLite detection model
        detection_interpreter = tflite.Interpreter(model_path=detection_model_path)
        detection_interpreter.allocate_tensors()
        
        # Get input and output details for detection model
        detection_input_details = detection_interpreter.get_input_details()
        detection_output_details = detection_interpreter.get_output_details()
        
        # Create dummy input for detection model
        detection_input_shape = detection_input_details[0]['shape']
        detection_dummy_input = np.zeros(detection_input_shape, dtype=np.float32)
        
        # Run inference on detection model
        detection_interpreter.set_tensor(detection_input_details[0]['index'], detection_dummy_input)
        detection_interpreter.invoke()
        _ = detection_interpreter.get_tensor(detection_output_details[0]['index'])
        
        print("Warming up classification model...")
        # Load TFLite classification model
        classification_interpreter = tflite.Interpreter(model_path=classification_model_path)
        classification_interpreter.allocate_tensors()
        
        # Get input and output details for classification model
        classification_input_details = classification_interpreter.get_input_details()
        classification_output_details = classification_interpreter.get_output_details()
        
        # Create dummy input for classification model
        classification_input_shape = classification_input_details[0]['shape']
        classification_dummy_input = np.zeros(classification_input_shape, dtype=np.float32)
        
        # Run inference on classification model
        classification_interpreter.set_tensor(classification_input_details[0]['index'], classification_dummy_input)
        classification_interpreter.invoke()
        _ = classification_interpreter.get_tensor(classification_output_details[0]['index'])
        
        print("Diagnosis models warmed up successfully")
        return True
        
    except Exception as e:
        print(f"Failed to warm up diagnosis models: {str(e)}")
        return False