import json
import time
import re
from typing import Dict, List, Any
from flask import current_app
from openai import OpenAI
from app.utils.auth_utils import get_access_token
from app.services.translation_service import TranslationService

# Templates
DIAGNOSIS_TEMPLATE = """
You are an expert dermatology assistant for the Acne Sense app.
Create helpful recommendations based on the PATIENT PROFILE and ACNE INFORMATION provided.
Your response MUST be formatted in proper markdown syntax.

RESPONSE FORMAT REQUIREMENTS (STRICTLY FOLLOW):
- Start with a level 2 heading '## OVERVIEW'
- Then include a level 2 heading '## RECOMMENDATIONS'
- Then include a level 2 heading '## SKINCARE TIPS'
- Finally include a level 2 heading '## IMPORTANT NOTES'

Under each heading:
- Use **bold text** for important terms
- Use bullet points (each starting with '- ' or '* ') for lists
- Use *italics* for emphasis
- Format medication names as `code style` using backticks

Example format:
## OVERVIEW
Brief summary here.

## RECOMMENDATIONS
- First recommendation with **important term** and `medication`
- Second recommendation

## SKINCARE TIPS
* First tip with *emphasized point*
* Second tip

## IMPORTANT NOTES
Warning information here.

YOUR RESPONSE MUST STRICTLY FOLLOW THIS MARKDOWN FORMAT.

PATIENT PROFILE:
{patient_profile}

ACNE INFORMATION:
{acne_info}
""".strip()

QA_TEMPLATE = """
You are an expert dermatologist assistant for the Acne Sense app.
Answer the USER'S QUESTION based on the CONTEXT provided from our knowledge base.
Use only the facts from the CONTEXT when answering the QUESTION.
If you don't know the answer based on the context, say "I don't have enough information to answer that question."
Your responses should be informative, accurate, and presented in a compassionate, professional tone.

CONTEXT:
{context}

USER'S QUESTION: {query}
""".strip()

EVALUATION_TEMPLATE = """
You are an expert evaluator for a RAG system.
Your task is to analyze the relevance of the generated answer to the given question.
Based on the relevance of the generated answer, you will classify it
as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

Here is the data for evaluation:

Question: {question}
Generated Answer: {answer}

Please analyze the content and context of the generated answer in relation to the question
and provide your evaluation in parsable JSON without using code blocks:

{{
  "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
  "Explanation": "[Provide a brief explanation for your evaluation]"
}}
""".strip()

ACNE_DOC_TEMPLATE = """
Acne Type: {Acne Type}
Description: {Description}
Common Locations: {Common Locations}
Common Causes: {Common Causes}
Initial Treatment: {Initial Treatment}
OTC Ingredients: {OTC Ingredients}
Skincare Recommendations: {Skincare Recommendations}
Ingredients to Avoid: {Skincare Ingredients to Avoid}
When to Consult Dermatologist: {When to Consult Dermatologist}
Expected Timeline: {Expected Timeline}
Combination Considerations: {Combination Considerations}
Skin Type Adjustments: {Skin Type Adjustments}
Age-Specific Considerations: {Age-Specific Considerations}
""".strip()

FAQ_DOC_TEMPLATE = """
Question: {Question}
Answer: {Answer}
Category: {Category}
""".strip()

# Field weights based on optimization 
FIELD_WEIGHTS = {
    'Acne Type': 2.97,
    'Description': 1.35,
    'Common Locations': 0.61,
    'Common Causes': 1.18,
    'Initial Treatment': 1.61,
    'OTC Ingredients': 1.36,
    'Skincare Recommendations': 1.08,
    'Skincare Ingredients to Avoid': 1.35,
    'When to Consult Dermatologist': 2.83,
    'Expected Timeline': 0.32,
    'Combination Considerations': 2.08,
    'Skin Type Adjustments': 0.86,
    'Age-Specific Considerations': 1.64,
    'Question': 2.0,
    'Answer': 1.5,
    'Category': 0.5
}

def search(query: str, filter_dict: Dict = None, num_results: int = 5) -> List[Dict]:
    """Search the index with the given query and filters"""
    
    if filter_dict is None:
        filter_dict = {}
    
    results = current_app.index.search(
        query=query, 
        filter_dict=filter_dict, 
        boost_dict=FIELD_WEIGHTS,
        num_results=num_results
    )
    
    return results

def build_context_from_documents(documents: List[Dict]) -> str:
    """Build context string from search result documents"""
    context = ""
    
    for doc in documents:
        if doc.get('source') == 'acne_types':
            try:
                context += ACNE_DOC_TEMPLATE.format(**doc) + "\n\n"
            except KeyError:
                # Handle missing keys
                pass
        elif doc.get('source') == 'faqs':
            try:
                context += FAQ_DOC_TEMPLATE.format(**doc) + "\n\n"
            except KeyError:
                # Handle missing keys
                pass
    
    return context


def call_llm(prompt: str, model: str = None) -> str:
    """Get response from Vertex AI using OpenAI client"""
    try:
        # Use the model from parameter or default from config
        model_name = model or current_app.config['DEFAULT_MODEL']
        vllm_api_url = current_app.config['VLLM_API_URL']
        
        # Get cached or fresh access token with better error handling
        try:
            access_token = get_access_token()
            if not access_token:
                raise Exception("Failed to obtain valid access token")
        except Exception as auth_error:
            current_app.logger.error(f"Authentication error: {str(auth_error)}")
            return f"Authentication failed: Unable to connect to Vertex AI. Please check service account configuration."
        
        # Initialize OpenAI client for Vertex AI
        client = OpenAI(
            api_key=access_token,
            base_url=vllm_api_url,
            timeout=60 
        )
        
        # Create chat completion with improved parameters
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant specializing in acne-related questions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2800,  
            temperature=0.7,   
            top_p=0.8,         
            presence_penalty=1.5,
            extra_body={
                "top_k": 20, 
                "chat_template_kwargs": {"enable_thinking": False},
            },
        )
        
        # Check if this is an error response
        if hasattr(response, 'object') and response.object == 'error':
            error_message = f"API Error: {response.type} - {response.message}"
            current_app.logger.error(error_message)
            return f"Error calling language model: {error_message}"
            
        # Only try to access choices if they exist
        if hasattr(response, 'choices') and response.choices:
            return response.choices[0].message.content
        else:
            error_msg = f"Unexpected API response format: {response}"
            current_app.logger.error(error_msg)
            return f"Error: {error_msg}"
        
    except Exception as e:
        error_msg = f"Error calling LLM: {str(e)}"
        current_app.logger.error(error_msg)
        return f"Error connecting to Vertex AI: {str(e)}"

# def call_llm(prompt: str, model: str = None) -> str:
#     """Get response from vLLM using OpenAI client"""
#     try:
#         # Use the model from parameter or default from config
#         model_name = model or current_app.config['DEFAULT_MODEL']
        
#         # Initialize OpenAI client for vLLM
#         client = OpenAI(
#             api_key="dummy-key",  # vLLM doesn't require real API key
#             base_url=current_app.config['VLLM_API_URL']
#         )
        
#         # Create chat completion
#         response = client.chat.completions.create(
#             model=model_name,
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant specializing in acne-related questions."},
#                 {"role": "user", "content": prompt}
#             ],
#             max_tokens=1000,
#             temperature=0.7
#         )
        
#         return response.choices[0].message.content
        
#     except Exception as e:
#         return f"Error connecting to vLLM: {str(e)}"


def answer_question(query: str, model: str = None) -> str:
    """Answer a question using RAG"""
    search_results = search(query, num_results=5)
    context = build_context_from_documents(search_results)
    
    prompt = QA_TEMPLATE.format(
        query=query,
        context=context
    )
    
    answer = call_llm(prompt, model)
    return answer

def evaluate_relevance(question: str, answer: str, model: str = "qwen2:7b") -> Dict[str, str]:
    """Evaluate the relevance of the answer to the question"""
    prompt = EVALUATION_TEMPLATE.format(
        question=question,
        answer=answer
    )
    
    evaluation = call_llm(prompt, model)
    
    try:
        # Extract JSON from the response
        json_match = re.search(r'({.*})', evaluation.replace('\n', ' '))
        if json_match:
            json_str = json_match.group(1)
            json_eval = json.loads(json_str)
            return json_eval
        else:
            return {"Relevance": "UNKNOWN", "Explanation": "Failed to parse evaluation"}
    except json.JSONDecodeError:
        return {"Relevance": "UNKNOWN", "Explanation": "Failed to parse evaluation"}

def process_diagnosis(acne_types: List[str], user_info: Dict[str, Any], model: str = "qwen2:7b") -> str:
    """Process CV diagnosis results and provide recommendations"""
    patient_profile = f"""
    Age: {user_info.get('age', 'Unknown')}
    Skin Type: {user_info.get('skin_type', 'Unknown')}
    Skin Tone: {user_info.get('skin_tone', 'Unknown')}
    Sensitivity: {user_info.get('skin_sensitivity', 'Unknown')}
    """.strip()
    
    # Retrieve relevant acne information
    acne_info = ""
    
    for acne_type in acne_types:
        search_results = search(
            query=acne_type,
            filter_dict={"source": "acne_types"},
            num_results=1
        )
        
        if search_results:
            acne_info += build_context_from_documents(search_results)
    
    # If we have multiple acne types, search for combination considerations
    if len(acne_types) > 1:
        combination_query = " ".join(acne_types) + " combination"
        combo_results = search(
            query=combination_query,
            num_results=3
        )
        if combo_results:
            acne_info += "\n\nCombination Considerations:\n"
            acne_info += build_context_from_documents(combo_results)
    
    # Build the final prompt
    prompt = DIAGNOSIS_TEMPLATE.format(
        patient_profile=patient_profile,
        acne_info=acne_info
    )
    
    # Get response from LLM
    response = call_llm(prompt, model)
    
    return response

def rag(query: str, target_language: str = "en", 
                    translation_method: str = "google", 
                    model: str = None) -> Dict[str, Any]:
    """
    Multilingual RAG function to handle queries in any language
    
    Args:
        query: User query in any language
        target_language: Language to return answer in (default: "en")
        translation_method: Translation method ("google", "llm", "both")
        model: LLM model to use (default: from configuration)
        
    Returns:
        Dictionary with answer and metadata
    """
    # Use the model from config if not specified
    if model is None:
        model = current_app.config['DEFAULT_MODEL']
        
    t0 = time.time()
    
    # Initialize translation service
    translation_svc = TranslationService()
    
    # Step 1: Detect language and translate query to English if needed
    source_language = translation_svc.detect_language(query)
    original_query = query
    
    # Translate query to English for processing if it's not already in English
    if source_language != "en":
        query_translation = translation_svc.translate(
            text=query,
            target_language="en",
            source_language=source_language,
            method=translation_method,
            model=model
        )
        query = query_translation["translated_text"]
    
    # Step 2: Process the query with English RAG
    answer_in_english = answer_question(query, model=model)
    
    # Step 3: Translate answer back to source language if needed
    final_answer = answer_in_english
    if target_language != "en":
        answer_translation = translation_svc.translate(
            text=answer_in_english,
            target_language=target_language,
            source_language="en",
            method=translation_method,
            model=model
        )
        final_answer = answer_translation["translated_text"]
    
    # Step 4: Evaluate relevance on English content
    relevance_result = evaluate_relevance(
        question=query if source_language == "en" else original_query,
        answer=answer_in_english,
        model=model
    )
    
    # Calculate timing
    t1 = time.time()
    took = t1 - t0

    # Prepare result
    result = {
        "answer": final_answer,
        "model_used": model,
        "response_time": took,
        "original_language": source_language,
        "target_language": target_language,
        "translation_method": translation_method,
        "relevance": relevance_result.get("Relevance", "UNKNOWN"),
        "relevance_explanation": relevance_result.get("Explanation", "Failed to parse evaluation")
    }
    
    return result