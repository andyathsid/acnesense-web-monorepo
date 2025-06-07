import os
import pandas as pd
from flask import current_app
from app.services.search_service import Index

def load_index(app=None):
    """Load data from CSV files and create search index"""
    if app:
        acne_types_path = app.config.get('ACNE_TYPES_PATH', 'data/knowledge-base/acne_types.csv')
        faqs_path = app.config.get('FAQS_PATH', 'data/knowledge-base/faqs.csv')
    else:
        # Fallback to environment variables or default paths
        from dotenv import load_dotenv
        load_dotenv()
        acne_types_path = os.getenv("ACNE_TYPES_PATH", "data/knowledge-base/acne_types.csv")
        faqs_path = os.getenv("FAQS_PATH", "data/knowledge-base/faqs.csv")
    
    # Load data
    acne_types_df = pd.read_csv(acne_types_path, sep=';')
    faqs_df = pd.read_csv(faqs_path, sep=';')

    # Convert to documents
    acne_documents = acne_types_df.to_dict(orient='records')
    faq_documents = faqs_df.to_dict(orient='records')
    
    # Add source information
    for doc in acne_documents:
        doc['source'] = 'acne_types'
    for doc in faq_documents:
        doc['source'] = 'faqs'
    
    all_documents = acne_documents + faq_documents
    
    # Create search index
    index = Index(
        text_fields=[
            'Acne Type', 'Description', 'Common Locations', 'Common Causes',
            'Initial Treatment', 'OTC Ingredients', 'Skincare Recommendations',
            'Skincare Ingredients to Avoid', 'When to Consult Dermatologist',
            'Expected Timeline', 'Combination Considerations', 'Skin Type Adjustments',
            'Age-Specific Considerations', 'Question', 'Answer', 'Category'
        ],
        keyword_fields=['source']
    )
    
    # Fit the index with all documents
    index.fit(all_documents)
    return index