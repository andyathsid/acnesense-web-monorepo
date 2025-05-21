import uuid
from flask import Flask, request, jsonify
import time
import traceback
from typing import Dict, List, Any

import rag
import db

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "time": time.time()})

@app.route("/question", methods=["POST"])
def handle_question():
    """Answer a question using RAG (similar to reference implementation)"""
    try:
        data = request.json
        question = data.get("question", "")
        model = data.get("model", "qwen2:7b")
        
        if not question:
            return jsonify({"error": "No question provided"}), 400
        
        # Generate a unique conversation ID
        conversation_id = str(uuid.uuid4())
        
        # Get answer with RAG including relevance evaluation
        answer_data = rag.rag(question, model=model)
        
        # Format result similar to reference
        result = {
            "conversation_id": conversation_id,
            "question": question,
            "answer": answer_data["answer"]
        }
        
        # Save conversation to database
        db.save_conversation(
            conversation_id=conversation_id,
            question=question,
            answer_data=answer_data
        )
        
        return jsonify(result)
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/feedback", methods=["POST"])
def handle_feedback():
    """Save user feedback on an answer"""
    try:
        data = request.json
        conversation_id = data.get("conversation_id")
        feedback = data.get("feedback")
        
        if not conversation_id or feedback not in [1, -1]:
            return jsonify({"error": "Invalid input"}), 400
            
        db.save_feedback(
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

@app.route("/diagnosis", methods=["POST"])
def diagnosis():
    """Process a diagnosis based on acne types and user info"""
    try:
        data = request.json
        acne_types = data.get("acne_types", [])
        user_info = data.get("user_info", {})
        model = data.get("model", "qwen2:7b")
        
        if not acne_types:
            return jsonify({"error": "No acne types provided"}), 400
        
        result = rag.process_diagnosis(acne_types, user_info, model=model)
        return jsonify({"recommendation": result})
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)