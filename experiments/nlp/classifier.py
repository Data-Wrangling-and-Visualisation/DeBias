from typing import Set
from nltk.tokenize import word_tokenize
from config import NEWS_CATEGORIES, TRANSFORMER_MODEL
from utils import normalize_text
from transformers import pipeline
from utils import Singleton


class ZeroShotClassifier(metaclass=Singleton):
    """Classify news articles with zero-shot classification"""
    def __init__(self):
        super().__init__()
        self.classifier = pipeline(
            "zero-shot-classification",
            model=TRANSFORMER_MODEL,
            device=-1  # Use CPU
        )
    
    def classify(self, title: str, content: str = "") -> str:
        text = normalize_text(title)
        if content:
            text = f"{text} {normalize_text(content)}"
        
        result = self.classifier(text, NEWS_CATEGORIES, multi_label=False)
        return result["labels"][0]