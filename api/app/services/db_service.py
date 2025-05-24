from datetime import datetime
from supabase import create_client
from flask import current_app

def get_supabase_client():
    """Get the Supabase client using app config"""
    return create_client(
        current_app.config['SUPABASE_URL'], 
        current_app.config['SUPABASE_KEY']
    )

def save_conversation(conversation_id, question, answer_data):
    """Save conversation data to Supabase."""
    timestamp = datetime.now().isoformat()
    supabase = get_supabase_client()
    
    # Prepare the data for insertion
    conversation_data = {
        "id": conversation_id,
        "question": question,
        "answer": answer_data["answer"],
        "model_used": answer_data["model_used"],
        "response_time": answer_data["response_time"],
        "relevance": answer_data.get("relevance", "UNKNOWN"),
        "relevance_explanation": answer_data.get("relevance_explanation", ""),
        "timestamp": timestamp
    }
    
    # Insert into the conversations table
    supabase.table("conversations").insert(conversation_data).execute()
    
    return conversation_id

def save_feedback(conversation_id, feedback):
    """Save user feedback to Supabase."""
    timestamp = datetime.now().isoformat()
    supabase = get_supabase_client()
    
    # Prepare the feedback data
    feedback_data = {
        "conversation_id": conversation_id,
        "feedback": feedback,
        "timestamp": timestamp
    }
    
    # Insert into the feedback table
    supabase.table("feedback").insert(feedback_data).execute()
    
    return True