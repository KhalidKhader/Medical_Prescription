"""Patient and Prescriber Information Agent - Extracts combined patient and prescriber information from prescriptions"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage
from src.modules.ai_agents.utils.base_agent import BaseAgent
from src.core.settings.logging import logger
from src.modules.ai_agents.utils.json_parser import parse_json, clean_json_text, extract_json_from_text
from .prompts import get_patient_prescriber_extraction_prompt
from .tools import extract_combined_quality_metrics
from src.modules.ai_agents.utils.common_tools import calculate_patient_quality_metrics


class PatientPrescriberInfoAgent(BaseAgent):
    """Agent for extracting both patient and prescriber information from prescriptions"""
    
    def __init__(self):
        super().__init__("PatientPrescriberInfoAgent")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient and prescriber information from prescription image"""
        try:
            logger.info("--- AGENT: Patient and Prescriber Information Extraction ---")
            
            image_base64 = state.get("image_base64")
            if not image_base64:
                return self.add_warning(state, "No image data available for information extraction")
            
            self.scratchpad.add_thought("Extracting patient and prescriber information from prescription image")
            self.scratchpad.add_action("Processing image for comprehensive data")
            
            prompt = self.get_enhanced_prompt(self.get_prompt())
            
            # Create message with image
            message = HumanMessage(content=[
                {"type": "text", "text": prompt}, 
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ])
            
            response_text = await self.call_llm_with_image([message])
            # Use the json_parser utilities for robust parsing
            cleaned_text = clean_json_text(response_text)
            extracted_data = parse_json(cleaned_text)
            
            if not extracted_data:
                # Try extracting JSON from mixed content as fallback
                extracted_data = extract_json_from_text(response_text)
                
            if not extracted_data:
                return self.add_warning(state, "Failed to extract valid information")
            
            # Split the data into patient and prescriber components
            patient_data = {
                "full_name": extracted_data.get("patient_name"),
                "date_of_birth": extracted_data.get("patient_dob"),
                "age": extracted_data.get("patient_age"),
                "facility_name": extracted_data.get("patient_facility"),
                "address": extracted_data.get("patient_address"),
                "certainty": extracted_data.get("patient_certainty", 0)
            }
            
            prescriber_data = {
                "full_name": extracted_data.get("prescriber_name"),
                "state_license_number": extracted_data.get("state_license_number"),
                "npi_number": extracted_data.get("npi_number"),
                "dea_number": extracted_data.get("dea_number"),
                "address": extracted_data.get("prescriber_address"),
                "contact_number": extracted_data.get("prescriber_contact"),
                "certainty": extracted_data.get("prescriber_certainty", 0)
            }
            
            quality_metrics = extract_combined_quality_metrics(patient_data, prescriber_data)
            
            logger.info(f"Extracted patient info: {patient_data.get('full_name', 'unknown')}")
            logger.info(f"Extracted prescriber info: {prescriber_data.get('full_name', 'unknown')}")
            
            self.scratchpad.add_observation("Patient and prescriber information extraction completed")
            
            return {
                **state,
                "patient_data": patient_data,
                "prescriber_data": prescriber_data,
                "combined_quality_metrics": quality_metrics
            }
                
        except Exception as e:
            logger.error(f"Patient and prescriber info extraction failed: {e}")
            return self.create_error_response(str(e), state)
    
    def get_prompt(self, **kwargs) -> str:
        return get_patient_prescriber_extraction_prompt()
