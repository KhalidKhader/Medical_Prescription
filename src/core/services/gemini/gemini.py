"""
Google Gemini Service - Main interface combining all Gemini functionality
Refactored to <150 LOC and uses new google.genai.Client with Gemini 2.5 Pro
"""

import time
from typing import Dict, Any, Optional, List
from langfuse import observe
from src.core.settings.config import settings
from src.core.settings.logging import logger
from .client import GeminiClient
from .models import GeminiModels
from .processor import GeminiProcessor


class GeminiService:
    """Main Gemini service combining new client and legacy models"""
    
    def __init__(self):
        """Initialize Gemini service with both new and legacy clients"""
        
        # Initialize LangFuse for observability
        from langfuse import Langfuse
        self.langfuse = Langfuse(
            secret_key=settings.langfuse_secret_key,
            public_key=settings.langfuse_public_key,
            host=settings.langfuse_host
        )
        
        # New google.genai.Client (preferred for Gemini 2.5 Pro)
        try:
            self.new_client = GeminiClient()
            self.use_new_client = True
            logger.info("Initialized new google.genai.Client for Gemini 2.5 Pro")
        except Exception as e:
            logger.warning(f"Failed to initialize new client: {str(e)}")
            self.new_client = None
            self.use_new_client = False
        
        # Legacy LangChain models (fallback)
        self.models = GeminiModels()
        self.processor = GeminiProcessor(self.models)
        
        logger.info("GeminiService initialized with hybrid client approach")
    
    @property
    def task_model(self):
        """Get task model for backward compatibility"""
        return self.models.get_model("secondary")
    
    @property
    def vision_model(self):
        """Get vision model for backward compatibility"""
        return self.models.get_model("primary")
    
    @property
    def fallback_model(self):
        """Get fallback model for backward compatibility"""
        return self.models.get_model("fallback")
    
    async def process_prescription_image(
        self, 
        image_base64: str, 
        prompt: str,
        retry_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process prescription image with Gemini 2.5 Pro"""
        
        # Try new client first
        if self.use_new_client and self.new_client:
            try:
                return await self.new_client.process_image(image_base64, prompt)
            except Exception as e:
                logger.warning(f"New client failed: {str(e)}")
        
        # Fallback to legacy processor
        return await self.processor.process_prescription_image(image_base64, prompt, retry_count, metadata)
    
    async def process_text(self, prompt: str, context: str = None) -> str:
        """Process text with Gemini"""
        
        # Try new client first
        if self.use_new_client and self.new_client:
            try:
                return await self.new_client.process_text(prompt)
            except Exception as e:
                logger.warning(f"New client text processing failed: {str(e)}")
        
        # Fallback to legacy processor
        return await self.processor.process_text(prompt, context)
    
    async def process_batch(self, prompts: List[str]) -> List[str]:
        """Process multiple prompts in batch"""
        return await self.processor.process_batch(prompts)
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test overall Gemini connection"""
        
        health_result = {
            "status": "healthy",
            "models": {},
            "new_client_available": self.use_new_client,
            "legacy_models_available": True
        }
        
        # Test new client
        if self.use_new_client and self.new_client:
            try:
                new_client_results = await self.new_client.test_connection()
                health_result["models"]["new_client"] = new_client_results
            except Exception as e:
                health_result["models"]["new_client"] = {"error": str(e)}
                health_result["new_client_available"] = False
        
        # Test legacy models
        try:
            legacy_results = await self.models.test_all_models()
            health_result["models"]["legacy"] = legacy_results
        except Exception as e:
            health_result["models"]["legacy"] = {"error": str(e)}
            health_result["legacy_models_available"] = False
        
        # Determine overall status
        if not health_result["new_client_available"] and not health_result["legacy_models_available"]:
            health_result["status"] = "unhealthy"
        
        return health_result


# Global service instance
gemini_service = GeminiService()