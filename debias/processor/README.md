# Processor Module

This module is responsible for processing raw webpage data (HTML content) to extract meaningful information using Natural Language Processing (NLP).

## Functionality

1.  **Parses HTML:** Extracts the main title, content, and publication date from the raw HTML.
2.  **Extracts Keywords:** Identifies relevant keywords from the article's title and content (using `SpacyKeywordExtractor`).
3.  **Classifies Content:** Determines the topic or category of the article (using `ZeroShotClassifier`).
4.  **Formats Output:** Structures the extracted information (title, snippet, keywords, topics, dates) into a standardized `ProcessingResult` object.

## Main Entry Point

The primary function is `process_webpage`, which takes `WebpageData` (containing URL, HTML content, etc.) as input and returns a `ProcessingResult` object or `None` if essential information (like the article date) cannot be extracted.