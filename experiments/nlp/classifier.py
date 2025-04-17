from typing import Set
from nltk.tokenize import word_tokenize
from config import NEWS_CATEGORIES, TRANSFORMER_MODEL
from utils import normalize_text
from transformers import pipeline


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class NewsClassifier(metaclass=Singleton):
    """Base class for text classifiers"""
    def __init__(self):
        self.classifier = None

    def classify(self, title: str, content: str = "") -> str:
        raise NotImplementedError("Subclasses should implement this method")


class ZeroShotClassifier(NewsClassifier, metaclass=Singleton):
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