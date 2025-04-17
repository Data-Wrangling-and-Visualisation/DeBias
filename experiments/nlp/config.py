import re
from typing import Dict, Set

# Regex patterns
WHITESPACE_PATTERN = re.compile(r'\s+')
SPECIAL_CHARS_PATTERN = re.compile(r'[^\w\s]')

# Enhanced stopwords for news context
STOP_WORDS: Set[str] = {
    'said', 'says', 'told', 'according', 'reported', 'going', 'latest', 'news',
    'sky', 'bbc', 'cnn', 'nbc', 'fox', 'reuters', 'ap', 'press', 'associated',
    'world', 'us', 'uk', 'update', 'live', 'breaking', 'exclusive', 'report',
    'today', 'yesterday', 'tomorrow', 'week', 'month', 'year'
}

# News entity priorities
PRIORITY_ENTITIES: Dict[str, int] = {
    "PERSON": 1, 
    "ORG": 2, 
    "GPE": 3, 
    "LOC": 4,
    "PRODUCT": 5, 
    "EVENT": 6, 
    "NORP": 7,
    "FAC": 8,
    "WORK_OF_ART": 9
}

# News categories
NEWS_CATEGORIES = [
    "politics", "business", "technology", "health", "science", 
    "sports", "entertainment", "world", "environment"
]

# NLP settings
DEFAULT_SPACY_MODEL = "en_core_web_sm"
PREFERRED_SPACY_MODELS = ["en_core_web_lg", "en_core_web_trf", "en_core_web_sm"]
TRANSFORMER_MODEL = "facebook/bart-large-mnli"

# Output settings
SNIPPET_LENGTH = 200
MAX_KEYWORDS = 8