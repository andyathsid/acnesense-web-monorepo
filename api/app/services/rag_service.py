import json
import time
import re
from typing import Dict, List, Any, Optional
from operator import itemgetter
from flask import current_app
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from langchain_google_vertexai import VertexAIEmbeddings, ChatVertexAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_qdrant import QdrantVectorStore
from app.services.translation_service import TranslationService

# Improved QA Template with better instructions
QA_TEMPLATE = """You are an expert dermatology assistant for the Acne Sense app. Your primary goal is to provide accurate, compassionate, and helpful answers to user questions about acne.

CONTEXT:
{context}

USER'S QUESTION: {question}

INSTRUCTIONS:
1.  Carefully read the USER'S QUESTION and the CONTEXT.
2.  **Respond in the following language: {target_language}**. If the question is in a different language, translate your understanding of the question if necessary, but the final answer must be in {target_language}.
3.  **Prioritize the CONTEXT**: If the CONTEXT contains information that directly and sufficiently answers the USER'S QUESTION, formulate your answer based *only* on that information.
4.  **Use General Knowledge if Context is Insufficient**: If the CONTEXT does *not* contain relevant information, or if it's insufficient to fully answer the USER'S QUESTION, you may use your general dermatological knowledge to provide a helpful answer.
    *   In such cases, clearly state that the information is general advice (e.g., "Generally, for sensitive skin..." or "While our specific knowledge base doesn't cover this, common advice includes...").
    *   If you have no relevant information either from context or general knowledge, then respond with: "I'm sorry, but I don't have enough specific information to answer that question right now. It might be best to consult with a dermatologist for personalized advice."
5.  **Professional Tone**: Present your answer in a compassionate, professional, and easy-to-understand manner.
6.  **No Mention of "CONTEXT"**: Do not mention the word "CONTEXT" or "knowledge base" in your answer to the user.
7.  **Details from Context**: If using context, use specific details from it, such as treatment recommendations, ingredients, or timelines.
8.  **Multiple Options**: If multiple treatment options are mentioned (either in context or general knowledge), present them clearly.
9.  **Safety First**: Always err on the side of caution. If the question involves a serious medical concern or requires a diagnosis, advise the user to consult a healthcare professional.

ANSWER:"""

DIAGNOSIS_TEMPLATE = """
You are an expert dermatology assistant for the Acne Sense app.
Create helpful recommendations based on the PATIENT PROFILE, DETECTED ACNE TYPES, and ACNE INFORMATION provided.
Your response MUST be formatted in proper markdown syntax.

DETECTED ACNE TYPES:
{detected_acne_types}

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

**IMPORTANT: Your entire response, including all headings and content, MUST be in the following language: {target_language}.**

**CRITICAL: Base your recommendations ONLY on the DETECTED ACNE TYPES listed above. Do not discuss or mention any acne types not present in the DETECTED ACNE TYPES list.**

PATIENT PROFILE:
{patient_profile}

ACNE INFORMATION:
{acne_info}
"""

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
"""

# Global variables for initialized components
_embeddings = None
_vector_store = None
_llm = None

def get_embeddings():
    """Get or initialize Vertex AI embeddings"""
    global _embeddings
    if _embeddings is None:
        _embeddings = VertexAIEmbeddings(
            model_name=current_app.config['VERTEX_AI_EMBEDDING_MODEL'],
            project=current_app.config['PROJECT_ID'],
            location=current_app.config['GEMINI_LOCATION']
        )
    return _embeddings

def get_vector_store():
    """Get or initialize Qdrant vector store"""
    global _vector_store
    if _vector_store is None:
        qdrant_client = QdrantClient(
            url=current_app.config['QDRANT_URL'],
            api_key=current_app.config.get('QDRANT_API_KEY')
        )
        
        _vector_store = QdrantVectorStore(
            client=qdrant_client,
            collection_name=current_app.config['QDRANT_COLLECTION_NAME'],
            embedding=get_embeddings()
        )
    return _vector_store

def get_llm(thinking_budget: Optional[int] = None):
    """Get or initialize ChatVertexAI with optional thinking_budget override"""
    global _llm
    
    # If a specific thinking_budget is requested, create a new instance
    if thinking_budget is not None:
        return ChatVertexAI(
            model_name=current_app.config['GEMINI_MODEL'],
            project=current_app.config['PROJECT_ID'],
            location=current_app.config['GEMINI_LOCATION'],
            max_output_tokens=current_app.config.get('LLM_MAX_TOKENS', 2048),
            temperature=current_app.config.get('LLM_TEMPERATURE', 0.7),
            top_p=current_app.config.get('LLM_TOP_P', 0.8),
            top_k=current_app.config.get('LLM_TOP_K', 40),
            thinking_budget=thinking_budget
        )
    
    # Otherwise, use the cached instance with default thinking_budget=0
    if _llm is None:
        _llm = ChatVertexAI(
            model_name=current_app.config['GEMINI_MODEL'],
            project=current_app.config['PROJECT_ID'],
            location=current_app.config['GEMINI_LOCATION'],
            max_output_tokens=current_app.config.get('LLM_MAX_TOKENS', 8192),
            temperature=current_app.config.get('LLM_TEMPERATURE', 0.7),
            top_p=current_app.config.get('LLM_TOP_P', 0.8),
            top_k=current_app.config.get('LLM_TOP_K', 40),
            thinking_budget=0
        )
    return _llm

def get_retriever(num_results: int = 5, filter_dict: Optional[Dict] = None):
    """Get a retriever with optional filtering"""
    search_kwargs = {"k": num_results}
    
    if filter_dict:
        # Convert filter_dict to Qdrant filter format
        conditions = []
        for key, value in filter_dict.items():
            conditions.append(
                FieldCondition(
                    key=f"metadata.{key}",
                    match=MatchValue(value=value)
                )
            )
        
        if conditions:
            qdrant_filter = Filter(must=conditions)
            search_kwargs["filter"] = qdrant_filter
    
    return get_vector_store().as_retriever(search_kwargs=search_kwargs)

def format_docs_for_context(docs: List[Document]) -> str:
    """Format retrieved documents into context string"""
    return "\n\n".join([doc.page_content for doc in docs])

def answer_question(query: str, target_language: str = "en", model: str = None, num_results: int = 5, thinking_budget: Optional[int] = None) -> str:
    """Answer a question using RAG with Langchain"""
    try:
        # Get retriever and LLM
        retriever = get_retriever(num_results=num_results)
        llm = get_llm(thinking_budget=thinking_budget)
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_template(QA_TEMPLATE)
        
        # Create RAG chain using LCEL with proper input routing
        rag_chain = (
            {
                "context": itemgetter("question") | retriever | format_docs_for_context,
                "question": itemgetter("question"),
                "target_language": itemgetter("target_language")
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        
        # Invoke the chain with both query and target_language
        answer = rag_chain.invoke({"question": query, "target_language": target_language})
        return answer
        
    except Exception as e:
        current_app.logger.error(f"Error in answer_question: {str(e)}")
        return f"Error generating answer: {str(e)}"

def evaluate_relevance(question: str, answer: str, model: str = None) -> Dict[str, str]:
    """Evaluate the relevance of the answer to the question"""
    try:
        llm = get_llm()
        prompt = ChatPromptTemplate.from_template(EVALUATION_TEMPLATE)
        
        # Create evaluation chain
        eval_chain = prompt | llm | StrOutputParser()
        
        evaluation = eval_chain.invoke({
            "question": question,
            "answer": answer
        })
        
        # Extract JSON from the response
        json_match = re.search(r'({.*})', evaluation.replace('\n', ' '))
        if json_match:
            json_str = json_match.group(1)
            json_eval = json.loads(json_str)
            return json_eval
        else:
            return {"Relevance": "UNKNOWN", "Explanation": "Failed to parse evaluation"}
            
    except Exception as e:
        current_app.logger.error(f"Error in evaluate_relevance: {str(e)}")
        return {"Relevance": "UNKNOWN", "Explanation": f"Error: {str(e)}"}

def process_diagnosis(acne_types: List[str], user_info: Dict[str, Any], target_language: str = "en", model: str = None, thinking_budget: Optional[int] = None) -> Dict[str, str]:
    """Process diagnosis results and provide recommendations using RAG"""
    try:
        # Build patient profile
        patient_profile = f"""
        Age: {user_info.get('age', 'Unknown')}
        Skin Type: {user_info.get('skin_type', 'Unknown')}
        Skin Tone: {user_info.get('skin_tone', 'Unknown')}
        Sensitivity: {user_info.get('skin_sensitivity', 'Unknown')}
        """.strip()
        
        # Format detected acne types for the prompt
        detected_acne_types = "- " + "\n- ".join(acne_types)
        
        # Retrieve relevant acne information using server-side filtering
        acne_info_parts = []
        
        # Get information for each acne type using server-side filtering
        for acne_type in acne_types:
            try:
                # Use server-side filtering to get only acne_types documents
                retriever = get_retriever(num_results=3, filter_dict={"source": "acne_types"})
                search_results = retriever.invoke(acne_type)
                
                if search_results:
                    acne_info_parts.extend([doc.page_content for doc in search_results[:2]])
            except Exception as filter_error:
                current_app.logger.warning(f"Server-side filtering failed for {acne_type}, falling back to manual filtering: {str(filter_error)}")
                # Fallback to manual filtering if server-side filtering fails
                retriever = get_retriever(num_results=3)
                search_results = retriever.invoke(acne_type)
                acne_type_docs = [doc for doc in search_results if doc.metadata.get('source') == 'acne_types']
                if acne_type_docs:
                    acne_info_parts.extend([doc.page_content for doc in acne_type_docs[:2]])
        
        # If we have multiple acne types, search for combination considerations
        if len(acne_types) > 1:
            combination_query = " ".join(acne_types) + " combination treatment"
            try:
                # Try server-side filtering for combination considerations
                combo_retriever = get_retriever(num_results=2, filter_dict={"source": "acne_types"})
                combo_results = combo_retriever.invoke(combination_query)
            except Exception as combo_filter_error:
                current_app.logger.warning(f"Server-side filtering failed for combination query, falling back to manual filtering: {str(combo_filter_error)}")
                # Fallback to manual filtering
                combo_retriever = get_retriever(num_results=2)
                combo_results = combo_retriever.invoke(combination_query)
                combo_results = [doc for doc in combo_results if doc.metadata.get('source') == 'acne_types']
            
            if combo_results:
                acne_info_parts.append("COMBINATION CONSIDERATIONS:")
                acne_info_parts.extend([doc.page_content for doc in combo_results])
        
        acne_info = "\n\n".join(acne_info_parts)
        
        # Create diagnosis chain
        llm = get_llm(thinking_budget=thinking_budget)
        prompt = ChatPromptTemplate.from_template(DIAGNOSIS_TEMPLATE)
        
        diagnosis_chain = prompt | llm | StrOutputParser()
        
        # Generate response with detected acne types
        response = diagnosis_chain.invoke({
            "patient_profile": patient_profile,
            "detected_acne_types": detected_acne_types,
            "acne_info": acne_info,
            "target_language": target_language
        })
        
        # Parse the response into sections
        sections = parse_recommendation_sections(response)
        return sections
        
    except Exception as e:
        current_app.logger.error(f"Error in process_diagnosis: {str(e)}")
        # Return error in structured format
        return {
            "overview": f"Error generating diagnosis: {str(e)}",
            "recommendations": "Please consult with a dermatologist for specific treatment recommendations.",
            "skincare_tips": "Maintain good skincare hygiene and use appropriate products for your skin type.",
            "important_notes": "Consult a healthcare professional for serious skin concerns."
        }

def parse_recommendation_sections(recommendation_text: str) -> Dict[str, str]:
    """Parse recommendation text into structured sections"""
    sections = {
        "overview": "",
        "recommendations": "",
        "skincare_tips": "",
        "important_notes": ""
    }
    
    if not recommendation_text or not isinstance(recommendation_text, str):
        return sections
    
    try:
        # Split sections safely
        overview_match = recommendation_text.split('## OVERVIEW')
        if len(overview_match) > 1:
            overview_section = overview_match[1].split('## RECOMMENDATIONS')[0]
            sections["overview"] = overview_section.strip() if overview_section else ""
        
        recommendations_match = recommendation_text.split('## RECOMMENDATIONS')
        if len(recommendations_match) > 1:
            recommendations_section = recommendations_match[1].split('## SKINCARE TIPS')[0]
            sections["recommendations"] = recommendations_section.strip() if recommendations_section else ""
        
        skincare_tips_match = recommendation_text.split('## SKINCARE TIPS')
        if len(skincare_tips_match) > 1:
            skincare_tips_section = skincare_tips_match[1].split('## IMPORTANT NOTES')[0]
            sections["skincare_tips"] = skincare_tips_section.strip() if skincare_tips_section else ""
        
        important_notes_match = recommendation_text.split('## IMPORTANT NOTES')
        if len(important_notes_match) > 1:
            important_notes_section = important_notes_match[1]
            sections["important_notes"] = important_notes_section.strip() if important_notes_section else ""
            
    except Exception as e:
        current_app.logger.error(f"Error parsing recommendation sections: {str(e)}")
        # Fallback: put entire text in overview
        sections["overview"] = recommendation_text
    
    return sections

def rag(query: str, target_language: str = "en", 
        translation_method: str = "google", 
        model: str = None, thinking_budget: Optional[int] = None) -> Dict[str, Any]:
    """
    Streamlined RAG function with integrated multilingual support
    
    Args:
        query: User query in any language
        target_language: Language to return answer in (default: "en")
        translation_method: Translation method (deprecated, kept for compatibility)
        model: LLM model to use (default: from configuration)
        thinking_budget: Thinking budget for the LLM (default: None, uses cached instance with 0)
        
    Returns:
        Dictionary with answer and metadata
    """
    # Use the model from config if not specified
    if model is None:
        model = current_app.config['DEFAULT_MODEL']
        
    t0 = time.time()
    
    # Initialize translation service for language detection only
    translation_svc = TranslationService()
    
    # Step 1: Detect the original language for metadata
    source_language = translation_svc.detect_language(query)
    
    # Step 2: Process the query directly with RAG, letting the LLM handle the language
    final_answer = answer_question(query, target_language=target_language, model=model, thinking_budget=thinking_budget)
    
    # Step 3: Evaluate relevance (using the original query)
    relevance_result = evaluate_relevance(
        question=query,
        answer=final_answer,
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
        "translation_method": "integrated_llm",  # Updated to reflect new approach
        "relevance": relevance_result.get("Relevance", "UNKNOWN"),
        "relevance_explanation": relevance_result.get("Explanation", "Failed to parse evaluation")
    }
    
    return result

# Legacy function compatibility - these functions are no longer used but kept for backward compatibility
def search(query: str, filter_dict: Dict = None, num_results: int = 5) -> List[Dict]:
    """Legacy search function - replaced by Qdrant vector search"""
    current_app.logger.warning("Legacy search function called - this should be replaced with vector search")
    return []

def build_context_from_documents(documents: List[Dict]) -> str:
    """Legacy context builder - replaced by format_docs_for_context"""
    current_app.logger.warning("Legacy build_context_from_documents called")
    return ""

def call_llm(prompt: str, model: str = None) -> str:
    """Legacy LLM call - replaced by Langchain chains"""
    current_app.logger.warning("Legacy call_llm function called - this should be replaced with Langchain chains")
    try:
        llm = get_llm()
        result = llm.invoke(prompt)
        return result.content if hasattr(result, 'content') else str(result)
    except Exception as e:
        return f"Error: {str(e)}"
