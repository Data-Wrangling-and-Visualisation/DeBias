import os
import json
import dateutil.parser
from typing import Dict, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from datetime import datetime

from utils import clean_text, normalize_text
from config import MAX_CONTENT_LENGTH
from models import RawNewsData

def parse_news(html_content: str, url: str = None) -> RawNewsData:
    """Parse HTML content to extract article data"""
    # Parse HTML
    soup = BeautifulSoup(html_content, "html.parser")
    # Extract title
    title = extract_title(soup)
    # Extract datetime
    datetime_obj = extract_date(soup)
    # Extract website name
    website_name = extract_website(soup, url)
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
    """Extract article date from HTML using a simple, generalized approach"""
    # Try meta tags with common date attributes
    for meta in soup.find_all('meta'):
        attr_value = meta.get('content')
        if attr_value and any(date_attr in meta.attrs for date_attr in ['pubdate', 'publishdate', 'timestamp', 'date']):
            try:
                return dateutil.parser.parse(attr_value)
            except:
                pass
    
    # Try time tags
    for time in soup.find_all('time'):
        date_text = time.get('datetime') or time.text
        try:
            return dateutil.parser.parse(date_text)
        except:
            pass
    
    # Try JSON-LD
    for script in soup.find_all('script', {'type': 'application/ld+json'}):
        try:
            data = json.loads(script.string)
            date_str = data.get('datePublished') or data.get('dateModified')
            if date_str:
                return dateutil.parser.parse(date_str)
        except:
            pass
    
    # Try common date-related classes
    for element in soup.find_all(class_=lambda c: c and 'date' in c.lower()):
        try:
            return dateutil.parser.parse(element.text)
        except:
            pass
    
    return None


def extract_website(soup: BeautifulSoup, url: str = None) -> str:
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
        elif url:
            try:
                domain = urlparse(url).netloc
                website_name = domain.replace('www.', '')
            except:
                pass
    
    return website_name


def extract_content(soup: BeautifulSoup) -> str:
    """Extract article content from HTML"""
    article = soup.find('article') or soup.find('main')
    paragraphs = article.find_all('p') if article else soup.find_all('p', limit=30)
    content = ' '.join(p.get_text(strip=True) for p in paragraphs)
    return clean_text(content[:MAX_CONTENT_LENGTH])