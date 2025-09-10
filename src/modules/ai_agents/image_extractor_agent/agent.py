"""Image Extractor Agent - Prescription data extraction from images"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage
from src.modules.ai_agents.utils.base_agent import BaseAgent
from src.core.settings.logging import logger
from .prompts import get_image_extraction_prompt
from .tools import validate_extraction_json


class ImageExtractorAgent(BaseAgent):
    """Agent for extracting prescription data from images"""
    
    def __init__(self):
        super().__init__("ImageExtractorAgent")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract prescription data from image using Gemini Vision"""
        try:
            logger.info("--- AGENT: Image Extractor ---")
            
            image_base64 = state.get("image_base64")
            if not image_base64:
                return self.create_error_response("No image provided for extraction", state)
            
            self.scratchpad.add_thought("Processing prescription image for data extraction")
            self.scratchpad.add_action("Analyzing image with vision model")
            
            prompt = self.get_enhanced_prompt(self.get_prompt())
            
            message = HumanMessage(content=[
                {"type": "text", "text": prompt}, 
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ])
            
            response = await self.call_llm_with_image([message])
            result = self._process_extraction_response(state, response)
            
            self.scratchpad.add_observation("Image extraction processing completed")
            return result
            
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            return self.create_error_response(str(e), state)
    
    def get_prompt(self, **kwargs) -> str:
        return get_image_extraction_prompt()
    
    def _process_extraction_response(self, state: Dict[str, Any], response: str) -> Dict[str, Any]:
        """Process and validate extraction response"""
        is_valid, parsed_data, error_msg = validate_extraction_json(response)
        
        if is_valid and parsed_data:
            return {
                **state,
                "raw_extraction_text": response,
                "prescription_data": parsed_data,
                "medications_to_process": parsed_data.get("medications", []),
                "patient_data": parsed_data.get("patient_data", {}),
                "prescriber_data": parsed_data.get("prescriber_data", {}),
                "is_valid": True,
                "extraction_completed": True
            }
        else:
            return self.add_warning(state, f"Extraction validation failed: {error_msg}")