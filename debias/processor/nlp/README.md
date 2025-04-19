# News Article Parser

A modular system for extracting structured data from news article HTML files.

## Overview

This tool parses HTML news articles and extracts useful information in a standardized JSON format:

```json
{
  "article_datetime": "2023-01-15T12:30:45",
  "snippet": "The main content of the article...",
  "keywords": [{"text": "Politics", "type": "CATEGORY"}, {"text": "John Smith", "type": "PERSON"}],
  "topics": [{"text": "politics", "type": "CATEGORY"}]
}
```

## Installation

1. Install dependencies:
   ```bash
   uv add bs4 nltk spacy python-dateutil transformers torch
   ```
2. Download required spaCy models (at least one is required):
   ```bash
   # Recommended (larger, more accurate)
   python -m spacy download en_core_web_lg
   
   # Alternative (smaller, faster)
   python -m spacy download en_core_web_sm
   ```

## Project Structure

- `config.py` - Configuration settings and constants
- `utils.py` - Utility functions for text processing
- `models.py` - Data models for structured information
- `parser.py` - HTML document parsing
- `extractor.py` - Keyword extraction using NER
- `classifier.py` - Topic classification
- `main.py` - Command-line interface

## Usage

### Process a single HTML file:
```bash
python main.py path/to/file.html
```

### Process a directory of HTML files:
```bash
python main.py path/to/directory/
```

### Set custom output location:
```bash
python main.py path/to/file.html --output results/output.json
```

### Get help:
```bash
python main.py --help
```

## Configuration

Adjust parameters in `config.py` to customize:
- NLP models
- Keyword extraction settings
- Classification categories
- Output formatting

## Requirements

- Python 3.7+
- Beautiful Soup 4
- NLTK
- spaCy (with at least one English model)
- dateutil
- transformers (optional for advanced classification)

## Note

For optimal performance, the larger spaCy models (`en_core_web_lg` or `en_core_web_trf`) are recommended but require more memory. The system will fall back to smaller models if the larger ones aren't available.