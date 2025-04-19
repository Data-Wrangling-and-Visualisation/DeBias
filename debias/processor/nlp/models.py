from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass
from datetime import datetime
from debias.core.wordstore import Keyword, Topic


@dataclass
class RawNewsData:
    """Model for the raw parsed news data"""

    title: str
    title_normalized: str
    datetime_obj: Optional[datetime]
    website: str
    content: str
    content_normalized: str
    source_file: str | None = None
    keywords_data: List[Keyword] | None = None
    category: str | None = None

    def __post_init__(self):
        if self.keywords_data is None:
            self.keywords_data = []


@dataclass
class FormattedNewsData:
    """Model for the final output format"""

    article_datetime: Optional[datetime]
    snippet: str
    title: str
    keywords: List[Keyword]
    topics: List[Topic]
