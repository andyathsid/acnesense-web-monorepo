import os
import pandas as pd
from minsearch import Index
from dotenv import load_dotenv

load_dotenv()
# Default paths to knowledge base files
ACNE_TYPES_PATH = os.getenv("ACNE_TYPES_PATH", "../data/knowledge-base/acne_types.csv")
FAQS_PATH = os.getenv("FAQS_PATH", "../data/knowledge-base/faqs.csv")

def load_index(acne_types_path=ACNE_TYPES_PATH, faqs_path=FAQS_PATH):
    """Load data from CSV files and create search index"""
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