import re

import nltk

# Regex patterns
WHITESPACE_PATTERN = re.compile(r"\s+")
SPECIAL_CHARS_PATTERN = re.compile(r"[^\w\s]")

# Enhanced stopwords for news context
STOP_WORDS: set[str] = set(nltk.corpus.stopwords.words("english")).union({
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
})

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

# Output settings
SNIPPET_LENGTH = 200
MAX_KEYWORDS = 8
MAX_CONTENT_LENGTH = 1000
