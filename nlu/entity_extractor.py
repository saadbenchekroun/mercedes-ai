"""
Entity extraction module using spaCy.
"""
import logging
import spacy
from typing import Dict, List, Any, Optional
import json
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)

class EntityExtractor:
    """Extracts entities from text using spaCy."""
    
    def __init__(self):
        """Initialize the entity extractor."""
        # Load spaCy model
        self.nlp = spacy.load(settings.SPACY_MODEL)
        
        # Load custom entity patterns
        self.custom_patterns = self._load_custom_patterns()
        
        # Add custom patterns to the pipeline
        ruler = self.nlp.add_pipe("entity_ruler")
        ruler.add_patterns(self.custom_patterns)
        
        logger.info("Entity extractor initialized")
    
    def _load_custom_patterns(self) -> List[Dict[str, Any]]:
        """
        Load custom entity patterns from file.
        
        Returns:
            List[Dict[str, Any]]: List of entity patterns
        """
        patterns_file = Path(settings.NLU_MODEL_PATH) / "entity_patterns.json"
        
        if patterns_file.exists():
            try:
                with open(patterns_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading entity patterns: {str(e)}")
                return []
        else:
            logger.warning(f"Entity patterns file not found: {patterns_file}")
            return []
    
    async def extract(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract entities from text.
        
        Args:
            text: Input text
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Extracted entities by type
        """
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            # Extract entities
            entities = {}
            for ent in doc.ents:
                if ent.label_ not in entities:
                    entities[ent.label_] = []
                
                entities[ent.label_].append({
                    "text": ent.text,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "confidence": self._calculate_confidence(ent)
                })
            
            logger.debug(f"Extracted entities: {entities}")
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction error: {str(e)}")
            return {}
    
    def _calculate_confidence(self, entity: spacy.tokens.Span) -> float:
        """
        Calculate confidence score for an entity.
        
        Args:
            entity: spaCy entity span
            
        Returns:
            float: Confidence score
        """
        # Base confidence on entity length and context
        confidence = 0.5
        
        # Adjust for entity length
        if len(entity.text.split()) > 1:
            confidence += 0.2
        
        # Adjust for entity type
        if entity.label_ in ["PERSON", "GPE", "ORG"]:
            confidence += 0.1
        
        # Adjust for context
        if entity.root.dep_ in ["nsubj", "dobj"]:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def get_entity_types(self) -> List[str]:
        """
        Get list of supported entity types.
        
        Returns:
            List[str]: List of entity types
        """
        return list(self.nlp.get_pipe("ner").labels)
    
    def add_custom_pattern(self, pattern: Dict[str, Any]):
        """
        Add a custom entity pattern.
        
        Args:
            pattern: Entity pattern to add
        """
        try:
            # Add pattern to the ruler
            ruler = self.nlp.get_pipe("entity_ruler")
            ruler.add_patterns([pattern])
            
            # Save updated patterns
            patterns_file = Path(settings.NLU_MODEL_PATH) / "entity_patterns.json"
            patterns_file.parent.mkdir(parents=True, exist_ok=True)
            
            current_patterns = self._load_custom_patterns()
            current_patterns.append(pattern)
            
            with open(patterns_file, "w") as f:
                json.dump(current_patterns, f, indent=2)
            
            logger.info(f"Added custom entity pattern: {pattern}")
            
        except Exception as e:
            logger.error(f"Error adding custom pattern: {str(e)}")
            raise
    
    def remove_custom_pattern(self, pattern_id: str):
        """
        Remove a custom entity pattern.
        
        Args:
            pattern_id: ID of pattern to remove
        """
        try:
            # Remove pattern from the ruler
            ruler = self.nlp.get_pipe("entity_ruler")
            ruler.remove_pattern(pattern_id)
            
            # Update patterns file
            patterns_file = Path(settings.NLU_MODEL_PATH) / "entity_patterns.json"
            current_patterns = self._load_custom_patterns()
            current_patterns = [p for p in current_patterns if p["id"] != pattern_id]
            
            with open(patterns_file, "w") as f:
                json.dump(current_patterns, f, indent=2)
            
            logger.info(f"Removed custom entity pattern: {pattern_id}")
            
        except Exception as e:
            logger.error(f"Error removing custom pattern: {str(e)}")
            raise 