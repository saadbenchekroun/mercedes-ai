"""
LLM client for GPT-4 integration.
"""
import logging
import json
from typing import Dict, Any, List, Optional
import openai
from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    """Client for OpenAI's GPT-4 API."""
    
    def __init__(self):
        """Initialize the LLM client."""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4"
        self.max_tokens = 1000
        self.temperature = 0.7
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()
        
        logger.info("LLM client initialized")
    
    def _load_system_prompt(self) -> str:
        """
        Load system prompt from file.
        
        Returns:
            str: System prompt
        """
        try:
            with open(settings.PROMPT_PATH / "system_prompt.txt", "r") as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error loading system prompt: {str(e)}")
            return "You are a helpful AI assistant for the Mercedes-Benz S-Class."
    
    async def generate_response(
        self,
        user_input: str,
        context: Dict[str, Any],
        vehicle_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a response using GPT-4.
        
        Args:
            user_input: User's input text
            context: Conversation context
            vehicle_state: Current vehicle state
            
        Returns:
            Dict[str, Any]: Generated response
        """
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "system", "content": f"Vehicle State: {json.dumps(vehicle_state)}"}
            ]
            
            # Add conversation history
            for turn in context.get("conversation_history", [])[-5:]:  # Last 5 turns
                messages.append({
                    "role": "user" if turn.get("role") == "user" else "assistant",
                    "content": turn["text"]
                })
            
            # Add current user input
            messages.append({"role": "user", "content": user_input})
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            response_data = json.loads(response_text)
            
            logger.debug(f"Generated response: {response_data}")
            return response_data
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "text": "I apologize, but I'm having trouble processing your request right now.",
                "action": "error",
                "confidence": 0.0
            }
    
    async def generate_follow_up(self, context: Dict[str, Any]) -> List[str]:
        """
        Generate follow-up questions based on context.
        
        Args:
            context: Conversation context
            
        Returns:
            List[str]: List of follow-up questions
        """
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": "Generate 3 relevant follow-up questions based on the conversation context."},
                {"role": "system", "content": f"Context: {json.dumps(context)}"}
            ]
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=200,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            response_data = json.loads(response_text)
            
            return response_data.get("questions", [])
            
        except Exception as e:
            logger.error(f"Error generating follow-up questions: {str(e)}")
            return []
    
    async def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict[str, float]: Sentiment scores
        """
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": "Analyze the sentiment of the following text and return scores for positive, negative, and neutral."},
                {"role": "user", "content": text}
            ]
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=100,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            return json.loads(response_text)
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0} 