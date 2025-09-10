"""Patient Information Agent - Extracts patient information from prescriptions"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage
from src.modules.ai_agents.utils.base_agent import BaseAgent
from src.core.settings.logging import logger
from .prompts import get_patient_extraction_prompt
from .tools import repair_patient_json, extract_patient_quality_metrics
from src.modules.ai_agents.utils.common_tools import calculate_patient_quality_metrics


class PatientInfoAgent(BaseAgent):
    """Agent for extracting patient information from prescriptions"""
    
    def __init__(self):
        super().__init__("PatientInfoAgent")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient information from prescription image"""
        try:
            logger.info("--- AGENT: Patient Information Extraction ---")
            
            image_base64 = state.get("image_base64")
            if not image_base64:
                return self.add_warning(state, "No image data available for patient extraction")
            
            self.scratchpad.add_thought("Extracting patient information from prescription image")
            self.scratchpad.add_action("Processing image for patient data")
            
            prompt = self.get_enhanced_prompt(self.get_prompt())
            
            # Create message with image
            message = HumanMessage(content=[
                {"type": "text", "text": prompt}, 
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ])
            
            response_text = await self.call_llm_with_image([message])
            patient_data = self.parse_json(response_text)
            
            if not patient_data:
                return self.add_warning(state, "Failed to extract valid patient information")
            
            quality_metrics = calculate_patient_quality_metrics(patient_data)
            logger.info(f"Extracted patient info: {patient_data.get('full_name', 'unknown')}")
            
            self.scratchpad.add_observation("Patient information extraction completed")
            
            return {
                **state,
                "patient_data": patient_data,
                "patient_quality_metrics": quality_metrics
            }
                
        except Exception as e:
            logger.error(f"Patient info extraction failed: {e}")
            return self.create_error_response(str(e), state)
    
    def get_prompt(self, **kwargs) -> str:
        return get_patient_extraction_prompt()
