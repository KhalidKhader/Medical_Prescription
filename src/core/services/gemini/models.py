"""
Gemini Models - Model management and initialization
"""

from typing import Dict, Any, Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.settings.config import settings
from src.core.settings.logging import logger


class GeminiModels:
    """Manages Gemini model instances and fallback strategies"""
    
    def __init__(self):
        """Initialize all Gemini models"""
        self.models = {}
        self.model_stats = {
            "primary_success_count": 0,
            "secondary_success_count": 0,
            "fallback_success_count": 0,
            "total_failures": 0
        }
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all model instances"""
        # Use Gemini 2.5 Pro as required
        model_configs = [
            ("primary", "gemini-2.5-pro"),  # Primary model
            ("secondary", "gemini-2.5-pro"), 
            ("fallback", "gemini-2.5-pro")  # All use 2.5 Pro as required
        ]
        
        for model_key, model_name in model_configs:
            try:
                model = ChatGoogleGenerativeAI(
                    model=model_name,
                    temperature=settings.gemini_temperature,
                    max_output_tokens=settings.gemini_max_tokens,
                    google_api_key=settings.google_api_key
                )
                self.models[model_key] = model
                logger.info(f"Initialized {model_key} model: {model_name}")
                
            except Exception as e:
                logger.warning(f"Failed to initialize {model_key} model ({model_name}): {str(e)}")
                self.models[model_key] = None
    
    def get_model(self, model_type: str) -> Optional[ChatGoogleGenerativeAI]:
        """Get model by type"""
        return self.models.get(model_type)
    
    def get_available_models(self) -> Dict[str, ChatGoogleGenerativeAI]:
        """Get all available models"""
        return {k: v for k, v in self.models.items() if v is not None}
    
    async def test_model(self, model_type: str) -> Dict[str, Any]:
        """Test a specific model"""
        try:
            model = self.get_model(model_type)
            if not model:
                return {
                    "available": False,
                    "error": f"Model {model_type} not initialized"
                }
            
            # Test with simple message
            test_response = await model.ainvoke("Health check - respond OK")
            
            # Check if response is valid
            if test_response and test_response.content:
                self.model_stats[f"{model_type}_success_count"] += 1
                return {
                    "available": True,
                    "test_passed": True,
                    "response_length": len(test_response.content),
                    "model_name": getattr(model, 'model_name', getattr(model, 'model', 'gemini-2.5-pro'))
                }
            else:
                self.model_stats["total_failures"] += 1
                return {
                    "available": False,
                    "error": "Empty response from model"
                }
                
        except Exception as e:
            self.model_stats["total_failures"] += 1
            logger.error(f"Model {model_type} test failed: {str(e)}")
            return {
                "available": False,
                "error": str(e)
            }
    
    async def test_all_models(self) -> Dict[str, Any]:
        """Test all available models"""
        results = {}
        
        for model_type in ["primary", "secondary", "fallback"]:
            results[model_type] = await self.test_model(model_type)
        
        return results
    
