import os
import json
import argparse
from typing import List, Dict
import traceback

from config import SNIPPET_LENGTH
from utils import initialize_nltk, get_all_html_files, DateTimeEncoder
from models import RawNewsData, FormattedNewsData, Topic
from parser import parse_news
from extractor import extract_unique_keywords
from classifier import classify_news

def process_html_file(file_path: str) -> RawNewsData:
    """Process a single HTML file and return the extracted data"""
    # Parse article
    news_data = parse_news(file_path)
    news_data.source_file = file_path
    
    # Skip invalid articles
    if not news_data.title or news_data.title == "No title found":
        raise ValueError("No valid title found")
    
    # Extract keywords
    news_data.keywords_data = extract_unique_keywords(
        news_data.title, 
        news_data.content
    )
    
    # Classify article
    news_data.category = classify_news(
        news_data.title_normalized, 
        news_data.content_normalized
    )
    
    return news_data

def format_output(news_data: RawNewsData) -> FormattedNewsData:
    """Format the data according to the required JSON structure"""
    # Create the snippet
    content_len = min(len(news_data.content), SNIPPET_LENGTH)
    snippet = news_data.content[:content_len] + "..." if news_data.content else ""
    
    # Format the keywords
    keywords = [{"text": k.text, "type": k.type} for k in news_data.keywords_data]
    
    # Format the topics
    topics = [{"text": news_data.category, "type": "CATEGORY"}]
    
    # Format the output according to the required structure
    return FormattedNewsData(
        article_datetime=news_data.datetime_obj,
        snippet=snippet,
        keywords=keywords,
        topics=topics
    )

def process_input(input_path: str) -> List[FormattedNewsData]:
    """Process the input path (file or directory) and return formatted data"""
    data = []
    
    # Check if input path exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input path does not exist: {input_path}")
    
    # Process single file or directory
    if os.path.isfile(input_path):
        if input_path.endswith(('.html', '.htm')):
            try:
                print(f"Processing file: {input_path}")
                news_data = process_html_file(input_path)
                formatted_data = format_output(news_data)
                
                print(f"Title: {news_data.title}")
                print(f"Date: {news_data.date or 'Unknown'}")
                print(f"Category: {news_data.category}")
                print(f"Keywords: {', '.join([k.text for k in news_data.keywords_data])}")
                print("-" * 50)
                
                data.append(formatted_data)
            except Exception as e:
                print(f"Error processing {input_path}: {e}")
                traceback.print_exc()
        else:
            print(f"Skipping non-HTML file: {input_path}")
    
    elif os.path.isdir(input_path):
        # Get all HTML files
        all_html_files = get_all_html_files(input_path)
        print(f"Found {len(all_html_files)} HTML files to process in {input_path}")
        
        # Process files
        for file_path in all_html_files:
            try:
                print(f"Processing {file_path}...")
                
                # Process the file
                news_data = process_html_file(file_path)
                
                # Format according to the required output structure
                formatted_data = format_output(news_data)
                
                print(f"Title: {news_data.title}")
                print(f"Date: {news_data.date or 'Unknown'}")
                print(f"Category: {news_data.category}")
                print(f"Keywords: {', '.join([k.text for k in news_data.keywords_data])}")
                print("-" * 50)
                
                data.append(formatted_data)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                traceback.print_exc()
    
    return data

def main():
    """Main entry point for the news parser"""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Parse news articles from HTML files')
    parser.add_argument('input_path', help='Path to an HTML file or directory containing HTML files')
    parser.add_argument('--output', '-o', 
                        help='Output JSON file path (default: ./parsed_news.json)',
                        default='./parsed_news.json')
    parser.add_argument('--quiet', '-q', 
                        help='Reduce output verbosity',
                        action='store_true')
    
    args = parser.parse_args()
    
    # Initialize NLTK resources
    initialize_nltk()
    
    try:
        # Process the input path
        data = process_input(args.input_path)
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Save to JSON
        with open(args.output, "w", encoding="utf-8") as outfile:
            json.dump(data, outfile, cls=DateTimeEncoder, indent=2, ensure_ascii=False)
        
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