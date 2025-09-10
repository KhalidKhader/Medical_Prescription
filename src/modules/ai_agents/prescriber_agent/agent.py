"""Prescriber Agent - Extracts prescriber information from prescriptions"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage
from src.modules.ai_agents.utils.base_agent import BaseAgent
from src.core.settings.logging import logger
from .prompts import get_prescriber_extraction_prompt
from .tools import extract_prescriber_quality_metrics


class PrescriberAgent(BaseAgent):
    """Agent for extracting prescriber information from prescriptions"""
    
    def __init__(self):
        super().__init__("PrescriberAgent")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract prescriber information from prescription image"""
        try:
            logger.info("--- AGENT: Prescriber Information Extraction ---")
            
            image_base64 = state.get("image_base64")
            if not image_base64:
                return self.add_warning(state, "No image data available for prescriber extraction")
            
            self.scratchpad.add_thought("Extracting prescriber information from image")
            self.scratchpad.add_action("Processing prescription image for prescriber data")
            
            prompt = self.get_enhanced_prompt(self.get_prompt())
            
            # Create message with image
            message = HumanMessage(content=[
                {"type": "text", "text": prompt}, 
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ])
            
            response_text = await self.call_llm_with_image([message])
            prescriber_data = self.parse_json(response_text)
            
            if not prescriber_data:
                return self.add_warning(state, "Failed to extract valid prescriber information")
            
            quality_metrics = extract_prescriber_quality_metrics(prescriber_data)
            logger.info(f"Extracted prescriber info: {prescriber_data.get('full_name', 'unknown')}")
            
            self.scratchpad.add_observation("Prescriber information extraction completed")
            
            return {
                **state,
                "prescriber_data": prescriber_data,
                "prescriber_quality_metrics": quality_metrics
            }
                
        except Exception as e:
            logger.error(f"Prescriber info extraction failed: {e}")
            return self.create_error_response(str(e), state)
    
    def get_prompt(self, **kwargs) -> str:
        return get_prescriber_extraction_prompt()
