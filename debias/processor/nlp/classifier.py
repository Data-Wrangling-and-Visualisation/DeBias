from transformers import pipeline

from debias.processor.nlp.config import NEWS_CATEGORIES
from debias.processor.nlp.utils import normalize_text


class ZeroShotClassifier:
    """Classify news articles with zero-shot classification"""

    def __init__(self, model: str):
        super().__init__()
        self.classifier = pipeline(
            "zero-shot-classification",
            model,
            device=-1,  # Use CPU
        )

    def classify(self, title: str, content: str = "") -> str:
        text = normalize_text(title)
        if content:
            text = f"{text} {normalize_text(content)}"

        result = self.classifier(text, NEWS_CATEGORIES, multi_label=False)
        return result["labels"][0]
