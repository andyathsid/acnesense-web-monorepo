import uuid
import time
import traceback
import os
import shutil
import json  
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app

from app.services.rag_service import rag, process_diagnosis
from app.services.db_service import save_conversation, save_feedback
from app.services.diagnosis_service import DiagnosisPipeline

api_bp = Blueprint('api', __name__)

@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "time": time.time()})

@api_bp.route("/question", methods=["POST"])
def handle_question():
    """Answer a question using RAG"""
    try:
        data = request.json
        question = data.get("question", "")
        model = data.get("model", current_app.config['DEFAULT_MODEL'])
        
        if not question:
            return jsonify({"error": "No question provided"}), 400
        
        # Generate a unique conversation ID
        conversation_id = str(uuid.uuid4())
        
        # Get answer with RAG including relevance evaluation
        answer_data = rag(question, model=model)
        
        # Format result
        result = {
            "conversation_id": conversation_id,
            "question": question,
            "answer": answer_data["answer"]
        }
        
        # Save conversation to database
        save_conversation(
            conversation_id=conversation_id,
            question=question,
            answer_data=answer_data
        )
        
        return jsonify(result)
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@api_bp.route("/feedback", methods=["POST"])
def handle_feedback():
    """Save user feedback on an answer"""
    try:
        data = request.json
        conversation_id = data.get("conversation_id")
        feedback = data.get("feedback")
        
        if not conversation_id or feedback not in [1, -1]:
            return jsonify({"error": "Invalid input"}), 400
            
        save_feedback(
            conversation_id=conversation_id,
            feedback=feedback
        )
        
        result = {
            "message": f"Feedback received for conversation {conversation_id}: {feedback}"
        }
        return jsonify(result)
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@api_bp.route("/diagnosis", methods=["POST"])
def diagnosis():
    """Process a diagnosis based on acne types and user info"""
    try:
        data = request.json
        acne_types = data.get("acne_types", [])
        user_info = data.get("user_info", {})
        model = data.get("model", current_app.config['DEFAULT_MODEL'])
        
        if not acne_types:
            return jsonify({"error": "No acne types provided"}), 400
        
        result = process_diagnosis(acne_types, user_info, model=model)
        return jsonify({
            "recommendation": result,
            "format": "markdown"
        })
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@api_bp.route("/image-diagnosis", methods=["POST"])
def image_diagnosis():
    """Process an uploaded image for acne detection and classification"""
    try:
        # Check if image file is in request
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
            
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        # Generate unique filename to prevent collisions
        filename = f"{str(uuid.uuid4())}.jpg"
        upload_path = os.path.join(current_app.config['UPLOAD_DIR'], filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        
        # Save the uploaded file
        file.save(upload_path)
        
        try:
            # Initialize and run the diagnosis pipeline
            pipeline = DiagnosisPipeline(
                detection_model_path=current_app.config.get('DETECTION_MODEL_PATH'),
                classification_model_path=current_app.config.get('CLASSIFICATION_MODEL_PATH'),
                class_index_path=current_app.config.get('CLASS_INDEX_PATH')
            )
            
            # Process the image
            results = pipeline.process(upload_path)
            
            return jsonify(results)
            
        finally:
            # Clean up files after response is sent
            try:
                # Remove uploaded image
                if os.path.exists(upload_path):
                    os.remove(upload_path)
                    print(f"Cleaned up uploaded image: {upload_path}")
                
                # Clean up crops and result images (we already have them as base64 in the response)
                crop_dir = current_app.config.get('CROP_DIR', 'instance/crops')
                results_dir = current_app.config.get('RESULTS_DIR', 'instance/results')
                
                # Clean crop directory
                for crop_file in os.listdir(crop_dir):
                    try:
                        os.remove(os.path.join(crop_dir, crop_file))
                    except Exception as e:
                        print(f"Failed to remove crop file {crop_file}: {str(e)}")
                
                # Clean results directory
                for result_file in os.listdir(results_dir):
                    try:
                        os.remove(os.path.join(results_dir, result_file))
                    except Exception as e:
                        print(f"Failed to remove result file {result_file}: {str(e)}")
                
                print("Image cleanup completed successfully")
                
            except Exception as cleanup_error:
                # Log cleanup error but don't fail the request
                print(f"Error during file cleanup: {str(cleanup_error)}")
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@api_bp.route("/combined-diagnosis", methods=["POST"])
def combined_diagnosis():
    """Process an uploaded image or base64 image data and provide personalized recommendations in one step"""
    try:
        upload_path = None
        user_info = {}
        model = current_app.config['DEFAULT_MODEL']
        
        # Check if request is JSON (for base64) or form (for file upload)
        if request.is_json:
            # Handle base64 encoded image
            data = request.json
            base64_image = data.get('image')
            user_info = data.get('user_info', {})
            model = data.get('model', current_app.config['DEFAULT_MODEL'])
            
            if not base64_image:
                return jsonify({"error": "No image data provided"}), 400
                
            # Generate unique filename
            filename = f"{str(uuid.uuid4())}.jpg"
            upload_path = os.path.join(current_app.config['UPLOAD_DIR'], filename)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            
            # Decode and save base64 image
            try:
                import base64
                # Remove data URL prefix if present (e.g., "data:image/jpeg;base64,")
                if ',' in base64_image:
                    base64_image = base64_image.split(',', 1)[1]
                
                with open(upload_path, "wb") as f:
                    f.write(base64.b64decode(base64_image))
            except Exception as decode_error:
                return jsonify({"error": f"Invalid base64 image data: {str(decode_error)}"}), 400
        else:
            # Handle file upload (existing functionality)
            if 'image' not in request.files:
                return jsonify({"error": "No image provided"}), 400
                
            file = request.files['image']
            if file.filename == '':
                return jsonify({"error": "No selected file"}), 400
            
            # Parse user info from form data
            if 'user_info' in request.form:
                try:
                    user_info = json.loads(request.form['user_info'])
                except:
                    return jsonify({"error": "Invalid user_info JSON format"}), 400
            
            # Get model name if provided, otherwise use default
            if 'model' in request.form:
                model = request.form['model']
                
            # Generate unique filename to prevent collisions
            filename = f"{str(uuid.uuid4())}.jpg"
            upload_path = os.path.join(current_app.config['UPLOAD_DIR'], filename)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            
            # Save the uploaded file
            file.save(upload_path)
        
        try:
            # Initialize and run the diagnosis pipeline
            pipeline = DiagnosisPipeline(
                detection_model_path=current_app.config.get('DETECTION_MODEL_PATH'),
                classification_model_path=current_app.config.get('CLASSIFICATION_MODEL_PATH'),
                class_index_path=current_app.config.get('CLASS_INDEX_PATH')
            )
            
            # Process the image
            image_results = pipeline.process(upload_path)
            
            # Extract acne types from classification results
            acne_types = []
            for result in image_results.get("classification_results", []):
                if result.get("class") not in acne_types:
                    acne_types.append(result.get("class"))
            
            # If no acne types detected, return early with just image results but restructured
            if not acne_types:
                # Restructure the response (move metadata fields up)
                metadata = image_results.pop("metadata", {})
                restructured_results = {**image_results, **metadata}
                restructured_results["message"] = "No acne detected to generate recommendations"
                return jsonify(restructured_results)
            
            # Generate recommendations based on detected acne types
            recommendation = process_diagnosis(acne_types, user_info, model=model)
            
            # Restructure the response (move metadata fields up)
            metadata = image_results.pop("metadata", {})
            
            # Combine both results into a single response
            combined_results = {
                **image_results,
                **metadata,
                "acne_types": acne_types,
                "recommendation": recommendation,
                "format": "markdown"
            }
            
            return jsonify(combined_results)
            
        finally:
            # Clean up files after response is sent
            try:
                # Remove uploaded image
                if os.path.exists(upload_path):
                    os.remove(upload_path)
                    print(f"Cleaned up uploaded image: {upload_path}")
                
                # Clean up crops and result images
                crop_dir = current_app.config.get('CROP_DIR', 'instance/crops')
                results_dir = current_app.config.get('RESULTS_DIR', 'instance/results')
                
                # Clean crop directory
                for crop_file in os.listdir(crop_dir):
                    try:
                        os.remove(os.path.join(crop_dir, crop_file))
                    except Exception as e:
                        print(f"Failed to remove crop file {crop_file}: {str(e)}")
                
                # Clean results directory
                for result_file in os.listdir(results_dir):
                    try:
                        os.remove(os.path.join(results_dir, result_file))
                    except Exception as e:
                        print(f"Failed to remove result file {result_file}: {str(e)}")
            
            except Exception as cleanup_error:
                print(f"Error during file cleanup: {str(cleanup_error)}")
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500