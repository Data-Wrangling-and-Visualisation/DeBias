import os
import json
import dateutil.parser
from typing import Dict, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from datetime import datetime

from utils import clean_text, normalize_text
from models import RawNewsData

def parse_news(path: str) -> RawNewsData:
    """Parse HTML files to extract article data"""
    # Parse HTML
    with open(path, encoding="utf8", errors='ignore') as f:
        soup = BeautifulSoup(f, "html.parser")
    
    # Extract title
    title = extract_title(soup)
    
    # Extract datetime
    datetime_obj = extract_date(soup)
    
    # Extract website name
    website_name = extract_website(soup, path)
    
    # Extract content
    content = extract_content(soup)
    
    return RawNewsData(
        title=title,
        title_normalized=normalize_text(title),
        datetime_obj=datetime_obj,
        website=website_name,
        content=content,
        content_normalized=normalize_text(content)
    )

def extract_title(soup: BeautifulSoup) -> str:
    """Extract article title from HTML"""
    title = None
    if soup.title:
        title = soup.title.string
    if not title:
        headline = soup.find(['h1'], class_=lambda c: c and ('headline' in str(c).lower() or 'title' in str(c).lower()))
        if headline:
            title = headline.get_text(strip=True)
    if not title:
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "No title found"
    
    # Clean title
    return clean_text(title)

def extract_date(soup: BeautifulSoup) -> Optional[datetime]:
    """Extract article date from HTML"""
    date = None
    datetime_obj = None
    date_elements = [
        ('meta', {'property': 'article:published_time'}),
        ('meta', {'property': 'og:published_time'}),
        ('meta', {'name': 'date'}),
        ('meta', {'name': 'pubdate'}),
        ('meta', {'itemprop': 'datePublished'}),
        ('time', {'datetime': True})
    ]
    
    for tag, attrs in date_elements:
        element = soup.find(tag, attrs)
        if element:
            date_text = element.get('content') or element.get('datetime') or element.get_text(strip=True)
            try:
                parsed_date = dateutil.parser.parse(date_text, fuzzy=True)
                datetime_obj = parsed_date
                date = parsed_date.isoformat()
                break
            except:
                continue
    
    # Check JSON-LD for date
    if not date:
        for script in soup.find_all('script', {'type': 'application/ld+json'}):
            try:
                json_data = json.loads(script.string)
                date_field = json_data.get('datePublished') or json_data.get('dateModified')
                if date_field:
                    parsed_date = dateutil.parser.parse(date_field, fuzzy=True)
                    datetime_obj = parsed_date
                    date = parsed_date.isoformat()
                    break
            except:
                continue
    
    return datetime_obj

def extract_website(soup: BeautifulSoup, path: str) -> str:
    """Extract website name from HTML"""
    website_name = "Unknown"
    site_meta = soup.find('meta', {'property': 'og:site_name'})
    if site_meta and site_meta.get('content'):
        website_name = site_meta.get('content')
    else:
        canonical = soup.find('link', {'rel': 'canonical'})
        if canonical and canonical.get('href'):
            domain = urlparse(canonical.get('href')).netloc
            website_name = domain.replace('www.', '')
        else:
            website_name = os.path.basename(os.path.dirname(path))
    
    return website_name

def extract_content(soup: BeautifulSoup) -> str:
    """Extract article content from HTML"""
    article = soup.find('article') or soup.find('main')
    paragraphs = article.find_all('p') if article else soup.find_all('p', limit=30)
    content = ' '.join(p.get_text(strip=True) for p in paragraphs)
    return clean_text(content[:3000])