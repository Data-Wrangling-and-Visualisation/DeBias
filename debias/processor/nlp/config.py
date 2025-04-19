import re
from typing import Dict, Set

# Regex patterns
WHITESPACE_PATTERN = re.compile(r"\s+")
SPECIAL_CHARS_PATTERN = re.compile(r"[^\w\s]")

# Enhanced stopwords for news context
STOP_WORDS: Set[str] = {
    "said",
    "says",
    "told",
    "according",
    "reported",
    "going",
    "latest",
    "news",
    "press",
    "associated",
    "world",
    "update",
    "live",
    "breaking",
    "exclusive",
    "report",
    "today",
    "yesterday",
    "tomorrow",
    "week",
    "month",
    "year",
}

PUBLISHER_NAMES = {
    "skynews",
    "bbc",
    "cnn",
    "reuters",
    "apnews",
    "theguardian",
    "nytimes",
    "wsj",
    "ft",
    "bloomberg",
    "sky news",
    "bbc news",
    "world news",
    "latest news",
    "breaking news",
    "ap news",
    "the associated press",
    "the guardian",
    "new york times",
    "wall street journal",
    "financial times",
    "bloomberg",
}

NEWS_CATEGORIES = [
    "politics",
    "business",
    "technology",
    "health",
    "science",
    "sports",
    "entertainment",
    "world",
    "environment",
]

SPACY_MODEL = "en_core_web_lg"
TRANSFORMER_MODEL = "facebook/bart-large-mnli"

# Output settings
SNIPPET_LENGTH = 200
MAX_KEYWORDS = 8
MAX_CONTENT_LENGTH = 1000
