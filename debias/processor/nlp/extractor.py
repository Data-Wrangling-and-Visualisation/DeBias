from typing import List, Dict, Set
import spacy
from nltk.tokenize import word_tokenize
from collections import defaultdict

from config import SPACY_MODEL, MAX_KEYWORDS
from utils import clean_text, is_valid_keyword, normalize_text
from models import Keyword


class SpacyKeywordExtractor:
    """Base class for keyword extraction using spaCy"""

    def __init__(self):
        self.nlp = spacy.load(SPACY_MODEL)

    def extract_unique_keywords(self, title: str, content: str = "") -> List[Keyword]:
        """Extract unique keywords using spaCy NER"""
        normalized_title = normalize_text(title)
        normalized_content = normalize_text(content) if content else ""

        # Combine with title repeated for emphasis
        text_to_process = f"{normalized_title} {normalized_title} {normalized_content}"

        doc = self.nlp(text_to_process)
        entities = []
        seen_texts = set()

        # Process named entities
        for ent in doc.ents:
            entity_text = clean_text(ent.text)

            if not is_valid_keyword(entity_text):
                continue

            if entity_text.lower() in seen_texts:
                continue

            entities.append(Keyword(text=entity_text, type=ent.label_))
            seen_texts.add(entity_text.lower())

        # Return top keywords
        return entities[:MAX_KEYWORDS]
