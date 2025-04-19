from datetime import datetime

from core.wordstore import Keyword, ProcessingResult, Topic
from pydantic import BaseModel


class WebpageData(BaseModel):
    url: str
    """url of the fetch resource"""
    target_id: str
    """id of the target from the config"""
    filepath: str
    """filepath in s3 storage"""
    content: str
    """downloaded file content as string"""
    metadata: int
    """metadata id in metastore"""
    datetime: datetime
    """scraped at"""


def process_webpage(input: WebpageData) -> ProcessingResult | None:
    html_content = input.content

    ...  # todo: add processing
    snippet = ""
    article_datetime = None
    keywords: list[Keyword] = []
    topics: list[Topic] = []

    if article_datetime is None:
        return None

    return ProcessingResult(
        absolute_url=input.url,
        url_hash=input.url,
        target_id=input.target_id,
        scrape_datetime=input.datetime,
        article_datetime=article_datetime,
        snippet=snippet,
        keywords=keywords,
        topics=topics,
    )
