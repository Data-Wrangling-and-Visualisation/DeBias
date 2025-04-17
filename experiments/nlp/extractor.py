from typing import List, Dict, Set
import spacy
from nltk.tokenize import word_tokenize
from collections import defaultdict

from config import SPACY_MODEL, MAX_KEYWORDS
from utils import clean_text, is_valid_keyword, normalize_text
from models import Keyword

class SpacyKeywordExtractor:
    """Base class for keyword extraction using spaCy"""
    def __init__(self):
        self.nlp = spacy.load(SPACY_MODEL)

    def extract_unique_keywords(self, title: str, content: str = "") -> List[Keyword]:
        """Extract unique keywords using spaCy NER"""
        normalized_title = normalize_text(title)
        normalized_content = normalize_text(content) if content else ""
        
        # Combine with title repeated for emphasis
        text_to_process = f"{normalized_title} {normalized_title} {normalized_content}"
        
        doc = self.nlp(text_to_process)
        entities = []
        seen_texts = set()
        
        # Process named entities
        for ent in doc.ents:
            entity_text = clean_text(ent.text)
            
            if not is_valid_keyword(entity_text):
                continue
            
            if entity_text.lower() in seen_texts:
                continue
                
            entities.append(Keyword(
                text=entity_text,
                type=ent.label_
            ))
            seen_texts.add(entity_text.lower())

        # Return top keywords
        return entities[:MAX_KEYWORDS]
        """
        Check for entity overlap using hash tables and two pointers
        Returns list of entities with overlapping entities removed
        """
        if len(entities) <= 1:
            return entities
            
        # Convert to lowercase for comparison
        entity_texts = [e.text.lower() for e in entities]
        
        # Create token sets for each entity
        token_sets = []
        for text in entity_texts:
            tokens = set(word_tokenize(text))
            token_sets.append(tokens)
        
        # Create prefix hash for fast substring checks
        prefix_map = defaultdict(list)
        for i, text in enumerate(entity_texts):
            # Add entity index to all its possible prefixes
            words = text.split()
            if words:
                prefix_map[words[0]].append(i)
        
        # Track which entities to keep
        keep_entity = [True] * len(entities)
        
        # Compare entities using two pointers approach
        for i in range(len(entities)):
            if not keep_entity[i]:
                continue
                
            text_i = entity_texts[i]
            tokens_i = token_sets[i]
            words_i = text_i.split()
            
            # Only check entities that share the first word (using hash table)
            candidates = prefix_map.get(words_i[0], []) if words_i else []
            
            for j in candidates:
                if i == j or not keep_entity[j]:
                    continue
                    
                text_j = entity_texts[j]
                tokens_j = token_sets[j]
                
                # Check if one is a substring of the other
                if text_i in text_j or text_j in text_i:
                    # Keep the shorter one if it's a person, otherwise keep the longer one
                    if entities[i].type == "PERSON" and entities[j].type != "PERSON":
                        keep_entity[j] = False
                    elif entities[j].type == "PERSON" and entities[i].type != "PERSON":
                        keep_entity[i] = False
                        break  # No need to check more entities against i
                    else:
                        # Keep the one with higher priority type, or the shorter one if same type
                        priority_i = PRIORITY_ENTITIES.get(entities[i].type, 99)
                        priority_j = PRIORITY_ENTITIES.get(entities[j].type, 99)
                        
                        if priority_i < priority_j:
                            keep_entity[j] = False
                        elif priority_i > priority_j:
                            keep_entity[i] = False
                            break
                        else:  # Same priority, keep shorter one
                            if len(text_i) <= len(text_j):
                                keep_entity[j] = False
                            else:
                                keep_entity[i] = False
                                break
                
                # Check for high token overlap (more than 50%)
                elif tokens_i and tokens_j:
                    overlap = tokens_i.intersection(tokens_j)
                    if len(overlap) / min(len(tokens_i), len(tokens_j)) > 0.5:
                        # Similar logic as above for deciding which to keep
                        priority_i = PRIORITY_ENTITIES.get(entities[i].type, 99)
                        priority_j = PRIORITY_ENTITIES.get(entities[j].type, 99)
                        
                        if priority_i < priority_j:
                            keep_entity[j] = False
                        elif priority_i > priority_j:
                            keep_entity[i] = False
                            break
                        else:
                            if len(text_i) <= len(text_j):
                                keep_entity[j] = False
                            else:
                                keep_entity[i] = False
                                break
        
        # Return only the entities we decided to keep
        return [entities[i] for i in range(len(entities)) if keep_entity[i]]