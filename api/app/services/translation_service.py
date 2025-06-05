import json
from typing import Dict, Any, Optional
from flask import current_app
from googletrans import Translator
import google.generativeai as genai

class TranslationService:
    """Service to handle language detection and translation"""

    @staticmethod
    def detect_language(text: str) -> str:
        """Detect language of input text using Google Translate"""
        try:
            translator = Translator()
            detection = translator.detect(text)
            return detection.lang
        except Exception as e:
            print(f"Language detection error: {str(e)}")
            return "en"  # Default to English on error

    @staticmethod
    def translate_with_google(text: str, target_language: str = 'en', source_language: Optional[str] = None) -> str:
        """Translate text using Google Translate"""
        try:
            translator = Translator()
            result = translator.translate(text, dest=target_language, src=source_language)
            return result.text
        except Exception as e:
            print(f"Google translation error: {str(e)}")
            return text  # Return original text on error

    @staticmethod
    def translate_with_llm(text: str, target_language: str = 'en', source_language: Optional[str] = None, 
                           model: str = "gemini-2.5-flash") -> str:
        """Translate text using LLM (Gemini)"""
        try:
            # Configure the Gemini API
            genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
            
            # Define prompt for translation
            prompt = f"""
            Translate the following text from {source_language if source_language else 'detected language'} to {target_language}.
            Preserve all formatting, including markdown syntax.
            Only respond with the translation, nothing else.
            
            Text to translate: {text}
            """
            
            # Get response from Gemini
            generation_config = {
                "temperature": 0.1,  # Lower temperature for more accurate translation
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            model_instance = genai.GenerativeModel(model_name=model, generation_config=generation_config)
            response = model_instance.generate_content(prompt)
            
            return response.text
        except Exception as e:
            print(f"LLM translation error: {str(e)}")
            return text  # Return original text on error

    @staticmethod
    def translate(text: str, target_language: str = 'en', source_language: Optional[str] = None, 
                  method: str = "google", model: str = "gemini-2.5-flash") -> Dict[str, Any]:
        """
        Translate text with specified method
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'es', 'fr')
            source_language: Source language code (optional)
            method: Translation method ("google", "llm", or "both")
            model: LLM model to use
            
        Returns:
            Dictionary with translation results
        """
        # Detect language if not provided
        if not source_language:
            source_language = TranslationService.detect_language(text)
            
        # Skip translation if source and target are the same
        if source_language == target_language:
            return {
                "translated_text": text,
                "original_language": source_language,
                "target_language": target_language,
                "method": "none",
                "google_translation": text,
                "llm_translation": text,
            }
        
        # Perform translation based on method
        google_translation = None
        llm_translation = None
        translated_text = text
        
        if method == "google" or method == "both":
            google_translation = TranslationService.translate_with_google(
                text, target_language, source_language
            )
            if method == "google":
                translated_text = google_translation
                
        if method == "llm" or method == "both":
            llm_translation = TranslationService.translate_with_llm(
                text, target_language, source_language, model
            )
            if method == "llm":
                translated_text = llm_translation
                
        if method == "both":
            # Default to Google translation as primary
            translated_text = google_translation
        
        # Build result
        result = {
            "translated_text": translated_text,
            "original_language": source_language,
            "target_language": target_language,
            "method": method,
        }
        
        # Include individual translations if both methods were used
        if method == "both":
            result["google_translation"] = google_translation
            result["llm_translation"] = llm_translation
            
        return result