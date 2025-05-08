"""
Intent classification module using spaCy.
"""
import logging
import spacy
from typing import Dict, Any, List, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from config import settings

logger = logging.getLogger(__name__)

class IntentClassifier:
    """Classifies user intents using spaCy and transformers."""
    
    def __init__(self):
        """Initialize the intent classifier."""
        # Load spaCy model
        self.nlp = spacy.load(settings.SPACY_MODEL)
        
        # Load transformer model for intent classification
        self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "bert-base-uncased",
            num_labels=len(self._get_intent_labels())
        )
        
        # Move model to GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        # Set model to evaluation mode
        self.model.eval()
        
        logger.info(f"Intent classifier initialized on {self.device}")
    
    def _get_intent_labels(self) -> List[str]:
        """
        Get list of intent labels.
        
        Returns:
            List[str]: List of intent labels
        """
        return [
            "greeting",
            "farewell",
            "help",
            "climate_control",
            "navigation",
            "media_control",
            "phone_call",
            "vehicle_status",
            "settings",
            "weather",
            "traffic",
            "unknown"
        ]
    
    async def classify(self, text: str) -> Tuple[str, float]:
        """
        Classify the intent of the input text.
        
        Args:
            text: Input text to classify
            
        Returns:
            Tuple[str, float]: (intent, confidence)
        """
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            # Get transformer model prediction
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=1)
                confidence, predicted = torch.max(probabilities, dim=1)
            
            # Get intent label
            intent = self._get_intent_labels()[predicted.item()]
            confidence = confidence.item()
            
            # Apply confidence threshold
            if confidence < settings.INTENT_CONFIDENCE_THRESHOLD:
                intent = "unknown"
            
            logger.debug(f"Classified intent: {intent} (confidence: {confidence:.2f})")
            return intent, confidence
            
        except Exception as e:
            logger.error(f"Intent classification error: {str(e)}")
            return "unknown", 0.0
    
    def get_intent_features(self, text: str) -> Dict[str, Any]:
        """
        Extract features relevant to intent classification.
        
        Args:
            text: Input text
            
        Returns:
            Dict[str, Any]: Intent features
        """
        doc = self.nlp(text)
        
        features = {
            "entities": [ent.text for ent in doc.ents],
            "verbs": [token.lemma_ for token in doc if token.pos_ == "VERB"],
            "nouns": [token.lemma_ for token in doc if token.pos_ == "NOUN"],
            "is_question": any(token.dep_ == "aux" for token in doc),
            "sentiment": doc.sentiment,
            "key_phrases": [chunk.text for chunk in doc.noun_chunks]
        }
        
        return features
    
    def update_model(self, training_data: List[Dict[str, Any]]):
        """
        Update the intent classification model with new training data.
        
        Args:
            training_data: List of training examples
        """
        try:
            # Prepare training data
            texts = [example["text"] for example in training_data]
            labels = [self._get_intent_labels().index(example["intent"]) 
                     for example in training_data]
            
            # Tokenize inputs
            inputs = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)
            
            # Convert labels to tensor
            labels = torch.tensor(labels).to(self.device)
            
            # Set model to training mode
            self.model.train()
            
            # Training loop
            optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-5)
            
            for epoch in range(3):  # 3 epochs
                optimizer.zero_grad()
                outputs = self.model(**inputs, labels=labels)
                loss = outputs.loss
                loss.backward()
                optimizer.step()
                
                logger.info(f"Epoch {epoch + 1}, Loss: {loss.item():.4f}")
            
            # Set model back to evaluation mode
            self.model.eval()
            
            logger.info("Intent classification model updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating intent classification model: {str(e)}")
            raise 