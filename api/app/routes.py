import uuid
import time
import traceback
from flask import Blueprint, request, jsonify, current_app

from app.services.rag_service import rag, process_diagnosis
from app.services.db_service import save_conversation, save_feedback

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