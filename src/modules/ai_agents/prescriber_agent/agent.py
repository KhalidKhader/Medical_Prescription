"""
Prescriber Agent
Extracts prescriber information from prescription images using Gemini 2.5 Pro
"""

from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from src.core.settings.config import settings
from src.core.settings.logging import logger

# Optional LangFuse import
try:
    from langfuse import observe
except ImportError:
    def observe(name=None, **kwargs):
        def decorator(func):
            return func
        return decorator
from .prompts import get_prescriber_extraction_prompt
from .tools import repair_prescriber_json, extract_prescriber_quality_metrics


class PrescriberAgent:
    """Agent for extracting prescriber information from prescriptions using Gemini 2.5 Pro"""
    
    def __init__(self):
        """Initialize the prescriber agent with Gemini 2.5 Pro"""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro", 
            temperature=0,
            google_api_key=settings.google_api_key
        )
        logger.info("Prescriber Agent initialized with Gemini 2.5 Pro")
    
    @observe(name="prescriber_extraction",as_type="generation", capture_input=True, capture_output=True)
    async def extract_prescriber_info(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract prescriber information from prescription image
        
        Args:
            state: Workflow state containing image data
            
        Returns:
            Updated state with prescriber data
        """
        logger.info("--- AGENT: Prescriber Information Extractor ---")
        
        try:
            image_base64 = state.get("image_base64")
            if not image_base64:
                return self._add_warning(state, "No image data available for prescriber extraction")
            
            # Get prescriber extraction prompt
            prompt = get_prescriber_extraction_prompt()
            
            # Create message with image
            message = HumanMessage(content=[
                {"type": "text", "text": prompt}, 
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ])
            
            logger.info("Extracting prescriber information using Gemini 2.5 Pro...")
            response = await self.llm.ainvoke([message])
            response_text = response.content
            
            # Parse and validate response using json_repair
            is_valid, prescriber_data, error_msg = repair_prescriber_json(response_text)
            
            if is_valid and prescriber_data:
                # Extract quality metrics
                quality_metrics = extract_prescriber_quality_metrics(prescriber_data)
                
                logger.info(f"Successfully extracted prescriber info: {prescriber_data.get('full_name', 'unknown')}")
                logger.info(f"Prescriber quality metrics: {quality_metrics}")
                
                return {
                    **state,
                    "prescriber_data": prescriber_data,
                    "prescriber_quality_metrics": quality_metrics
                }
            else:
                return self._add_warning(state, f"Failed to extract valid prescriber information: {error_msg}")
                
        except Exception as e:
            logger.error(f"Prescriber info extraction failed: {e}")
            return self._add_warning(state, f"Prescriber info extraction failed: {str(e)}")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process method for compatibility with workflow
        
        Args:
            state: Workflow state
            
        Returns:
            Updated state
        """
        return await self.extract_prescriber_info(state)
    
    def _add_warning(self, state: Dict[str, Any], warning: str) -> Dict[str, Any]:
        """Add warning to state"""
        warnings = state.get("quality_warnings", [])
        warnings.append(warning)
        return {
            **state,
            "quality_warnings": warnings
        }
