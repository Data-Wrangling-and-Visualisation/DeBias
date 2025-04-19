from datetime import datetime

from core.wordstore import Keyword, ProcessingResult, Topic
from pydantic import BaseModel
from debias.processor.nlp.classifier import ZeroShotClassifier
from debias.processor.nlp.extractor import SpacyKeywordExtractor
from debias.processor.nlp.parser import parse_news
from debias.processor.nlp.models import RawNewsData, FormattedNewsData
from debias.processor.nlp.config import SNIPPET_LENGTH
from debias.processor.app import keyword_extractor, classifier


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


def process_html_content(
    html_content: str,
    url,
    keyword_extractor: SpacyKeywordExtractor,
    classifier: ZeroShotClassifier,
) -> RawNewsData:
    """Process HTML content and return the extracted data"""
    news_data = parse_news(html_content, url)
    news_data.source_file = url

    if not news_data.title or news_data.title == "No title found":
        raise ValueError("No valid title found")

    if keyword_extractor:
        news_data.keywords_data = keyword_extractor.extract_unique_keywords(news_data.title, news_data.content)

    if classifier:
        news_data.category = classifier.classify(news_data.title_normalized, news_data.content_normalized)

    return news_data


def format_output(news_data: RawNewsData) -> FormattedNewsData:
    """Format the data according to the required JSON structure"""
    content_len = min(len(news_data.content), SNIPPET_LENGTH)
    snippet = news_data.content[:content_len] + "..." if news_data.content else ""

    keywords = [Keyword(text=k.text, type=k.type) for k in news_data.keywords_data] if news_data.keywords_data else []
    topics = [Topic(text=news_data.category or "", type="CATEGORY")]

    return FormattedNewsData(
        article_datetime=news_data.datetime_obj,
        snippet=snippet,
        title=news_data.title,
        keywords=keywords,
        topics=topics,
    )


def process_webpage(input: WebpageData) -> ProcessingResult | None:
    html_content = input.content
    news_data = process_html_content(html_content, input.url, keyword_extractor, classifier)
    formatted_data = format_output(news_data)

    snippet = formatted_data.snippet
    article_datetime = formatted_data.article_datetime
    title = formatted_data.title
    keywords: list[Keyword] = formatted_data.keywords
    topics: list[Topic] = formatted_data.topics

    if article_datetime is None:
        return None

    return ProcessingResult(
        absolute_url=input.url,
        url_hash=input.url,
        target_id=input.target_id,
        scrape_datetime=input.datetime,
        article_datetime=article_datetime,
        title=title,
        snippet=snippet,
        keywords=keywords,
        topics=topics,
    )
