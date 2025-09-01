"""
Gemini Client - Consolidated implementation with processing and models
"""

import base64
import time
from typing import Dict, Any, Optional
from google import genai
from google.genai.types import Part, Content, GenerateContentConfig, SafetySetting
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import observe
from langfuse import Langfuse
from src.core.settings.config import settings
from src.core.settings.logging import logger


class GeminiClient:
    """Consolidated Gemini client with processing capabilities"""

    def __init__(self):
        """Initialize Gemini client"""
        self.client = genai.Client(api_key=settings.google_api_key)

        # Use Gemini 2.5 Pro as primary model
        self.model = "gemini-2.5-pro"

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

        # Initialize Langfuse
        self.langfuse = Langfuse(
            secret_key=settings.langfuse_secret_key,
            public_key=settings.langfuse_public_key,
            host=settings.langfuse_host
        )

        logger.info("Gemini client initialized with Gemini 2.5 Pro")
    
    @observe(name="gemini_vision", as_type="generation", capture_input=True, capture_output=True)
    async def process_image(self, image_base64: str, prompt: str) -> str:
        """Process image using Gemini 2.5 Pro"""
        
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
            
            # Generate content
            response = self.client.models.generate_content(
                model=self.model,
                contents=[content],
                config=self.generate_config
            )
            
            logger.info(f"Image processed successfully with {self.model}")
            
            # Return response text
            if hasattr(response, 'text') and response.text:
                return response.text
            
            # Fallback: try to get text from candidates
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                return part.text
            
            logger.warning("No text content found in response")
            return "{}"
            
        except Exception as e:
            logger.error(f"Image processing failed: {str(e)}")
            raise Exception(f"Image processing failed: {str(e)}")
    
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Gemini connection"""
        try:
            content = Content(
                role="user",
                parts=[Part.from_text("Test connection - respond with 'OK'")]
            )
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=[content],
                config=self.generate_config
            )
            
            return {
                "available": True,
                "model_name": self.model,
                "test_passed": "OK" in response.text,
                "response_length": len(response.text)
            }
            
        except Exception as e:
            return {
                "available": False,
                "model_name": self.model,
                "error": str(e)
            }
    
    # Enhanced processing with image preprocessing integration
    @observe(name="gemini_enhanced_vision", as_type="generation", capture_input=True, capture_output=True)
    async def process_prescription_image(
        self,
        image_base64: str,
        prompt: str,
        enhancement_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Process prescription image with Gemini 2.5 Pro and image preprocessing.

        Args:
            image_base64: Base64 encoded image
            prompt: Processing prompt
            enhancement_level: "minimal", "standard", or "aggressive"

        Returns:
            Dictionary containing processed result and metadata
        """
        from src.core.services.image.preprocessing import image_preprocessor

        start_time = time.time()

        try:
            # Step 1: Preprocess image for better OCR
            logger.info(f"Preprocessing image with {enhancement_level} enhancement")
            preprocessing_result = image_preprocessor.preprocess_prescription_image(
                image_base64, enhancement_level
            )

            # Use preprocessed image if successful
            processed_image_base64 = preprocessing_result.get(
                "processed_image_base64", image_base64
            )

            # Step 2: Process with Gemini Vision
            result = await self.process_image(processed_image_base64, prompt)

            processing_time = time.time() - start_time

            return {
                "result": result,
                "processing_metadata": {
                    "total_time": processing_time,
                    "preprocessing_success": preprocessing_result["processing_metadata"]["processing_success"],
                    "enhancement_level": enhancement_level,
                    "original_size": preprocessing_result["processing_metadata"].get("original_size"),
                    "processed_size": preprocessing_result["processing_metadata"].get("processed_size")
                }
            }

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Enhanced image processing failed: {str(e)}")
            raise Exception(f"Enhanced image processing failed: {str(e)}")
