from typing import Set
from nltk.tokenize import word_tokenize
from config import NEWS_CATEGORIES, CATEGORY_KEYWORDS, TRANSFORMER_MODEL
from utils import normalize_text

# Global transformer classifier
classifier = None

def initialize_classifier():
    """Initialize the transformer classifier"""
    global classifier
    if classifier is None:
        try:
            from transformers import pipeline
            classifier = pipeline(
                "zero-shot-classification",
                model=TRANSFORMER_MODEL,
                device=-1  # Use CPU
            )
            print(f"Initialized zero-shot classifier using {TRANSFORMER_MODEL}")
        except Exception as e:
            print(f"Error initializing transformer: {e}")
            classifier = None

def classify_news(title: str, content: str = "") -> str:
    """Classify news article using transformer-based zero-shot classification"""
    # Initialize transformer model (with caching)
    initialize_classifier()
    
    if classifier is None:
        return keyword_based_classification(title, content)
    
    try:
        # Prepare text for classification
        text = normalize_text(title)
        if content:
            text = f"{text} {normalize_text(content[:300])}"
        
        # Classify
        result = classifier(text, NEWS_CATEGORIES, multi_label=False)
        return result["labels"][0]
    except Exception as e:
        print(f"Error in classification: {e}")
        return keyword_based_classification(title, content)

def keyword_based_classification(title: str, content: str = "") -> str:
    """Fallback classification using keyword matching"""
    # Normalize and tokenize
    text = normalize_text(title + " " + (content[:200] if content else ""))
    tokens = set(word_tokenize(text))
    
    # Count matches
    matches = {category: 0 for category in CATEGORY_KEYWORDS}
    for category, terms in CATEGORY_KEYWORDS.items():
        for term in terms:
            if term in tokens or term in text:
                matches[category] += 1
    
    # Return best match
    best_category = max(matches.items(), key=lambda x: x[1])
    return best_category[0] if best_category[1] > 0 else "general"