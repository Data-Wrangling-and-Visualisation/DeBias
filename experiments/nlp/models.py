from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Keyword:
    """Data model for a keyword"""

    text: str
    type: str
    source: str = "named_entity"


@dataclass
class Topic:
    """Data model for a topic"""

    text: str
    type: str


@dataclass
class RawNewsData:
    """Model for the raw parsed news data"""

    title: str
    title_normalized: str
    datetime_obj: Optional[datetime] = None
    website: str = "Unknown"
    content: str = ""
    content_normalized: str = ""
    source_file: str = ""
    keywords_data: List[Keyword] = None  # type: ignore
    category: str = ""

    def __post_init__(self):
        if self.keywords_data is None:
            self.keywords_data = []


@dataclass
class FormattedNewsData:
    """Model for the final output format"""

    article_datetime: Optional[datetime]
    snippet: str
    title: str
    keywords: List[Dict[str, str]]
    topics: List[Dict[str, str]]
