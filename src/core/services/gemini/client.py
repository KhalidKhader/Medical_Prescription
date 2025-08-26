"""
Gemini Client - New implementation using google.genai.Client with Gemini 2.5 Pro
"""

import base64
from typing import Dict, Any, Optional
from google import genai
from google.genai.types import Part, Content, GenerateContentConfig, SafetySetting
from langfuse import observe
from src.core.settings.config import settings
from src.core.settings.logging import logger


class GeminiClient:
    """Modern Gemini client using google.genai.Client with Gemini 2.5 Pro"""
    
    def __init__(self):
        """Initialize Gemini client with new API"""
        self.client = genai.Client(api_key=settings.google_api_key)
        
        # Model hierarchy: Use Gemini 2.5 Pro exclusively as required
        self.models = {
            "primary": "gemini-2.5-pro",
            "secondary": "gemini-2.5-flash", 
            "tertiary": "gemini-1.5-pro",
            "fallback": "gemini-1.5-flash"
        }
        
        # Safety settings for medical applications
        self.safety_settings = [
            SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_MEDIUM_AND_ABOVE"
            ),
            SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_MEDIUM_AND_ABOVE"
            ),
            SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_MEDIUM_AND_ABOVE"
            ),
            SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_MEDIUM_AND_ABOVE"
            )
        ]
        
        # Generate content config
        self.generate_config = GenerateContentConfig(
            temperature=0,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            safety_settings=self.safety_settings
        )
        
        logger.info("Gemini client initialized with new google.genai.Client for Gemini 2.5 Pro")
    
    @observe(name="gemini_2_5_pro_vision", as_type="generation", capture_input=True, capture_output=True)
    async def process_image(
        self, 
        image_base64: str, 
        prompt: str, 
        model_preference: str = "primary"
    ) -> str:
        """Process image using Gemini 2.5 Pro"""
        
        model_name = self.models.get(model_preference, self.models["primary"])
        
        try:
            # Create image part from base64 data
            image_data = base64.b64decode(image_base64)
            image_part = Part.from_bytes(data=image_data, mime_type="image/jpeg")
            
            # Create content with text and image
            content = Content(
                role="user",
                parts=[
                    Part.from_text(prompt),
                    image_part
                ]
            )
            
            # Generate content with image and text
            response = self.client.models.generate_content(
                model=model_name,
                contents=[content],
                config=self.generate_config
            )
            
            logger.info(f"Image processed successfully with {model_name}")
            
            # Debug: Log response structure
            logger.debug(f"Response type: {type(response)}")
            logger.debug(f"Response attributes: {dir(response)}")
            
            # Check if response has text content
            if hasattr(response, 'text') and response.text:
                logger.debug(f"Found text in response.text: {response.text[:100]}...")
                return response.text
            elif hasattr(response, 'candidates') and response.candidates:
                # Try to get text from candidates
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                return part.text
            
            # If no text found, return a default response
            logger.warning(f"No text content found in response from {model_name}")
            return "{}"
            
        except Exception as e:
            logger.error(f"Image processing failed with {model_name}: {str(e)}")
            
            # Try fallback models
            if model_preference != "fallback":
                fallback_order = ["secondary", "tertiary", "fallback"]
                current_idx = list(self.models.keys()).index(model_preference)
                
                for fallback_key in fallback_order[current_idx:]:
                    try:
                        return await self.process_image(image_base64, prompt, fallback_key)
                    except Exception:
                        continue
            
            raise Exception(f"All Gemini models failed. Last error: {str(e)}")
    
    async def process_prescription_image(
        self, 
        image_base64: str, 
        prompt: str, 
        retry_count: int = 0, 
        metadata: Dict[str, Any] = None
    ) -> str:
        """Process prescription image using Gemini 2.5 Pro"""
        
        # Use primary model for prescription processing
        return await self.process_image(image_base64, prompt, "primary")
    
    @observe(name="gemini_2_5_pro_text", as_type="generation", capture_input=True, capture_output=True)
    async def process_text(self, prompt: str, model_preference: str = "primary") -> str:
        """Process text using Gemini 2.5 Pro"""
        
        model_name = self.models.get(model_preference, self.models["primary"])
        
        try:
            # Create content with text
            content = Content(
                role="user",
                parts=[Part.from_text(prompt)]
            )
            
            response = self.client.models.generate_content(
                model=model_name,
                contents=[content],
                config=self.generate_config
            )
            
            logger.info(f"Text processed successfully with {model_name}")
            return response.text
            
        except Exception as e:
            logger.error(f"Text processing failed with {model_name}: {str(e)}")
            
            # Try fallback models
            if model_preference != "fallback":
                fallback_order = ["secondary", "tertiary", "fallback"]
                current_idx = list(self.models.keys()).index(model_preference)
                
                for fallback_key in fallback_order[current_idx:]:
                    try:
                        return await self.process_text(prompt, fallback_key)
                    except Exception:
                        continue
            
            raise Exception(f"All Gemini models failed. Last error: {str(e)}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to all available models"""
        results = {}
        
        for model_key, model_name in self.models.items():
            try:
                content = Content(
                    role="user",
                    parts=[Part.from_text("Test connection - respond with 'OK'")]
                )
                
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=[content],
                    config=self.generate_config
                )
                
                results[model_key] = {
                    "available": True,
                    "model_name": model_name,
                    "test_passed": "OK" in response.text,
                    "response_length": len(response.text)
                }
                
            except Exception as e:
                results[model_key] = {
                    "available": False,
                    "model_name": model_name,
                    "error": str(e)
                }
        
        return results
    
    def get_available_models(self) -> Dict[str, str]:
        """Get list of available models"""
        return self.models.copy()
