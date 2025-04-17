import os
import json
from typing import List, Any, Dict, Optional
from datetime import datetime
import nltk
from config import WHITESPACE_PATTERN, SPECIAL_CHARS_PATTERN, STOP_WORDS, PUBLISHER_NAMES

def initialize_nltk():
    """Initialize NLTK resources"""
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('punkt', quiet=True)
    
    # Add standard stopwords to our custom set
    STOP_WORDS.update(set(nltk.corpus.stopwords.words('english')))


def clean_text(text: str) -> str:
    """Clean text by removing special characters and normalizing spaces"""
    if not text:
        return ""
    text = SPECIAL_CHARS_PATTERN.sub(' ', text)
    text = WHITESPACE_PATTERN.sub(' ', text).strip()
    return text


def normalize_text(text: str) -> str:
    """Convert text to lowercase and clean it"""
    if not text:
        return ""
    return clean_text(text.lower())


def get_all_html_files(root_dir: str) -> List[str]:
    """Get all HTML files recursively"""
    html_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(('.html', '.htm')):
                html_files.append(os.path.join(root, file))
    return html_files


def is_valid_keyword(keyword: str) -> bool:
    """Check if a keyword is valid"""
    # Skip stopwords, numbers
    if keyword.lower() in STOP_WORDS or keyword.replace(' ', '').isdigit():
        return False
    
    # Return all publisher names
    if any(term in keyword.lower() for term in PUBLISHER_NAMES):
        return False
        
    return True


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)
