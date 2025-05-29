import json
import time
import re
from typing import Dict, List, Any
from flask import current_app

# LangChain imports
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.schema import HumanMessage
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# Templates remain unchanged
DIAGNOSIS_TEMPLATE = """
You are an expert dermatology assistant for the Acne Sense app.
Create helpful recommendations based on the PATIENT PROFILE and ACNE INFORMATION provided.
Your response should be concise, informative, and structured in these sections:
1. OVERVIEW - Brief summary of detected acne condition (1-2 sentences)
2. RECOMMENDATIONS - Specific treatment suggestions based on acne type, skin type, and age
3. SKINCARE TIPS - Practical daily skincare advice tailored to the patient
4. IMPORTANT NOTES - Any warnings, timeline expectations, or when to consult a dermatologist

Your response should directly address their specific situation without asking follow-up questions.
Base your recommendations ONLY on the knowledge provided in ACNE INFORMATION.

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

def get_llm_client(model: str = None):
    """Get LLM client based on provider configuration"""
    provider = current_app.config.get('LLM_PROVIDER', 'vllm')
    
    if provider == 'openai':
        # For OpenAI models
        if not model or model.startswith('Qwen'):
            # Default to GPT model for OpenAI if specified model is not OpenAI compatible
            model = "gpt-3.5-turbo"
        
        chat_model = ChatOpenAI(
            model=model,
            openai_api_key=current_app.config.get('OPENAI_API_KEY'),
            temperature=0.1
        )
        return chat_model
        
    elif provider == 'vllm':
        # For local vLLM deployment
        from langchain.llms import OpenAI
        
        base_url = current_app.config.get('VLLM_API_URL', 'http://localhost:8080/v1')
        
        # Create a compatible OpenAI client pointing to vLLM server
        llm = OpenAI(
            model=model.split('/')[-1] if model else "Qwen2.5-3B-Instruct-AWQ",  # Extract model name 
            openai_api_base=base_url,
            # openai_api_key="dummy-key",  # vLLM doesn't require a real key
            temperature=0.1
        )
        return llm
    
    else:
        # Fallback to default handling
        raise ValueError(f"Unsupported LLM provider: {provider}")

def search(query: str, filter_dict: Dict = None, num_results: int = 5) -> List[Dict]:
    """Search the index with the given query and filters"""
    from flask import current_app
    
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
    """Get response from LLM using LangChain"""
    try:
        llm = get_llm_client(model)
        
        # For ChatOpenAI models
        if hasattr(llm, 'invoke'):
            response = llm.invoke(prompt)
            if hasattr(response, 'content'):  # For ChatOpenAI responses
                return response.content
            return str(response)
        
        # For standard LLM models
        return llm(prompt)
            
    except Exception as e:
        return f"Error connecting to LLM: {str(e)}"

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

def evaluate_relevance(question: str, answer: str, model: str = None) -> Dict[str, str]:
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

def process_diagnosis(acne_types: List[str], user_info: Dict[str, Any], model: str = None) -> str:
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

def rag(query: str, model: str = None) -> Dict[str, Any]:
    """Main RAG function to process a user query, now with relevance evaluation"""
    t0 = time.time()
    
    answer = answer_question(query, model=model)
    
    # Evaluate the relevance of the answer
    relevance_result = evaluate_relevance(query, answer, model)
    
    t1 = time.time()
    took = t1 - t0

    result = {
        "answer": answer,
        "model_used": model if model else current_app.config.get('DEFAULT_MODEL', 'Qwen2.5-3B-Instruct-AWQ'),
        "response_time": took,
        "relevance": relevance_result.get("Relevance", "UNKNOWN"),
        "relevance_explanation": relevance_result.get("Explanation", "Failed to parse evaluation")
    }
    
    return result