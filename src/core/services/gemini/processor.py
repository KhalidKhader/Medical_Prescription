"""
Gemini Processor - Core processing logic with fallback strategies
"""

import time
from typing import Dict, Any, Optional, List
from langchain_core.messages import HumanMessage, SystemMessage
from langfuse import observe, Langfuse
from src.core.settings.config import settings
from src.core.settings.logging import logger
from .models import GeminiModels


class GeminiProcessor:
    """Handles Gemini processing with fallback strategies and observability"""
    
    def __init__(self, models: GeminiModels):
        """Initialize processor with model manager"""
        self.models = models
        self.langfuse = Langfuse(
            secret_key=settings.langfuse_secret_key,
            public_key=settings.langfuse_public_key,
            host=settings.langfuse_host
        )
    
    @observe(name="gemini_vision_processing", as_type="generation", capture_input=True, capture_output=True)
    async def process_prescription_image(
        self, 
        image_base64: str, 
        prompt: str,
        retry_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process prescription image with hierarchical fallback"""
        
        start_time = time.time()
        
        message = HumanMessage(content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
        ])
        
        # Try models in fallback order
        fallback_order = self.models.get_fallback_order()
        last_error = None
        
        for i, model_type in enumerate(fallback_order):
            model = self.models.get_model(model_type)
            if not model:
                continue
            
            try:
                logger.info(f"Processing image with {model_type} model")
                
                response = await model.ainvoke([message])
                
                # Record success
                processing_time = time.time() - start_time
                self.models.record_success(model_type)
                
                # Log success to LangFuse
                self.langfuse.create_event(
                    name=f"gemini_{model_type}_success",
                    input={
                        "model_type": model_type,
                        "attempt": i + 1,
                        "processing_time": processing_time,
                        "response_length": len(response.content) if response.content else 0
                    }
                )
                
                logger.info(f"Vision processing successful with {model_type} model in {processing_time:.2f}s")
                return response.content
                
            except Exception as e:
                processing_time = time.time() - start_time
                last_error = e
                
                logger.warning(f"{model_type} model failed: {str(e)}")
                
                # Log failure to LangFuse
                self.langfuse.create_event(
                    name=f"gemini_{model_type}_failure",
                    input={
                        "model_type": model_type,
                        "attempt": i + 1,
                        "error": str(e),
                        "processing_time": processing_time
                    }
                )
                
                continue
        
        # All models failed
        self.models.record_failure()
        total_time = time.time() - start_time
        
        # Log final failure to LangFuse
        self.langfuse.create_event(
            name="gemini_all_models_failed",
            input={
                "error": str(last_error),
                "total_processing_time": total_time,
                "models_tried": len(fallback_order)
            }
        )
        
        raise Exception(f"All Gemini models failed. Last error: {str(last_error)}")
    
    @observe(name="gemini_text_processing", as_type="generation", capture_input=True, capture_output=True)
    async def process_text(self, prompt: str, context: str = None) -> str:
        """Process text with Gemini"""
        
        messages = []
        if context:
            messages.append(SystemMessage(content=context))
        messages.append(HumanMessage(content=prompt))
        
        # Try primary model first
        primary_model = self.models.get_model("primary")
        if primary_model:
            try:
                response = await primary_model.ainvoke(messages)
                return response.content
            except Exception as e:
                logger.error(f"Primary model text processing failed: {str(e)}")
        
        # Try fallback model
        fallback_model = self.models.get_model("fallback")
        if fallback_model:
            try:
                logger.info("Attempting text processing with fallback model")
                response = await fallback_model.ainvoke(messages)
                return response.content
            except Exception as e:
                logger.error(f"Fallback model also failed: {str(e)}")
                raise e
        
        raise Exception("No available models for text processing")
    
    async def process_batch(self, prompts: List[str]) -> List[str]:
        """Process multiple prompts in batch"""
        import asyncio
        
        tasks = [self.process_text(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch item {i} failed: {str(result)}")
                processed_results.append(f"Error: {str(result)}")
            else:
                processed_results.append(result)
        
        return processed_results
