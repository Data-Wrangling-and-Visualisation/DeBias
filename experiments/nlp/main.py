import os
import json
import argparse
from typing import List, Dict
import traceback

from config import SNIPPET_LENGTH
from utils import initialize_nltk, get_all_html_files, DateTimeEncoder
from models import RawNewsData, FormattedNewsData, Topic
from parser import parse_news
from extractor import SpacyKeywordExtractor
from classifier import ZeroShotClassifier


def process_html_content(
    html_content: str,
    url: str | None = None,
    keyword_extractor: SpacyKeywordExtractor | None = None,
    classifier: ZeroShotClassifier | None = None,
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

    keywords = [{"text": k.text, "type": k.type} for k in news_data.keywords_data]
    topics = [{"text": news_data.category, "type": "CATEGORY"}]

    return FormattedNewsData(
        article_datetime=news_data.datetime_obj,
        snippet=snippet,
        title=news_data.title,
        keywords=keywords,
        topics=topics,
    )


def process_input(
    input_path: str, keyword_extractor: SpacyKeywordExtractor, classifier: ZeroShotClassifier
) -> List[FormattedNewsData]:
    """Process the input path (file or directory) and return formatted data"""
    data = []

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    html_files = []

    if os.path.isfile(input_path):
        html_files = [input_path]
    elif os.path.isdir(input_path):
        html_files = get_all_html_files(input_path)

    for file_path in html_files:
        try:
            with open(file_path, encoding="utf8", errors="ignore") as f:
                html_content = f.read()
            news_data = process_html_content(html_content, file_path, keyword_extractor, classifier)
            formatted_data = format_output(news_data)

            data.append(formatted_data)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            traceback.print_exc()

    return data


def main():
    """Main entry point for the news parser"""
    parser = argparse.ArgumentParser(description="Parse news articles from HTML files")
    parser.add_argument("input_path", help="Path to an HTML file or directory containing HTML files")
    parser.add_argument(
        "--output", "-o", help="Output JSON file path (default: ./parsed_news.json)", default="./parsed_news.json"
    )
    parser.add_argument("--quiet", "-q", help="Reduce output verbosity", action="store_true")

    args = parser.parse_args()

    initialize_nltk()

    try:
        data = process_input(
            args.input_path, keyword_extractor=SpacyKeywordExtractor(), classifier=ZeroShotClassifier()
        )

        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        serializable_data = []
        for item in data:
            serializable_data.append({
                "article_datetime": item.article_datetime,
                "snippet": item.snippet,
                "title": item.title,
                "keywords": item.keywords,
                "topics": item.topics,
            })

        # Then serialize serializable_data instead of data
        with open(args.output, "w", encoding="utf-8") as outfile:
            json.dump(serializable_data, outfile, cls=DateTimeEncoder, indent=2, ensure_ascii=False)

        print(f"Processed {len(data)} news articles successfully.")
        print(f"Output saved to {args.output}")

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
