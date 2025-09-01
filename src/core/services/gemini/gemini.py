"""
Google Gemini Service - Simplified service using consolidated client
"""

from typing import Dict, Any
from langfuse import observe
from src.core.settings.config import settings
from src.core.settings.logging import logger
from .client import GeminiClient


class GeminiService:
    """Simplified Gemini service using consolidated client"""

    def __init__(self):
        """Initialize Gemini service with consolidated client"""
        try:
            self.client = GeminiClient()
            logger.info("GeminiService initialized with consolidated client")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            raise
    
    @observe(name="process_prescription_image", as_type="generation", capture_input=True, capture_output=True)
    async def process_prescription_image(
        self,
        image_base64: str,
        prompt: str,
        enhancement_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Process prescription image with Gemini 2.5 Pro and automatic image preprocessing.

        This is the recommended method that includes image enhancement for better OCR results.

        Args:
            image_base64: Base64 encoded image
            prompt: Processing prompt
            enhancement_level: "minimal", "standard", or "aggressive"

        Returns:
            Dictionary containing processed result and metadata
        """
        return await self.client.process_prescription_image(
            image_base64, prompt, enhancement_level
        )

   

    @observe(name="process_text", as_type="generation", capture_input=True, capture_output=True)
    async def process_text(self, prompt: str, context: str = None) -> str:
        """Process text with Gemini 2.5 Pro"""
        return await self.client.process_text(prompt, context)

    async def process_batch(self, prompts: list) -> list:
        """Process multiple prompts in batch"""
        return await self.client.process_batch(prompts)

# Global service instance
gemini_service = GeminiService()