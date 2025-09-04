"""
Image Extractor Agent
Primary agent for extracting prescription data from images using Gemini 2.5 Pro
"""

from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from src.core.settings.config import settings
from src.core.settings.logging import logger
from langfuse import observe

from src.modules.ai_agents.image_extractor_agent.prompts import USER_PROMPT
from src.modules.ai_agents.image_extractor_agent.tools import validate_extraction_json


class ImageExtractorAgent:
    """Agent for extracting prescription data from images using Gemini 2.5 Pro"""
    
    def __init__(self):
        """Initialize the image extractor agent with Gemini 2.5 Pro"""
        self.llm_vision = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro", 
            temperature=0,
            google_api_key=settings.google_api_key
        )
        logger.info("Image Extractor Agent initialized with Gemini 2.5 Pro")
    
    @observe(name="image_extraction_agent", as_type="generation", capture_input=True, capture_output=True)
    async def extract_prescription_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract prescription data from image using Gemini Vision
        
        Args:
            state: Workflow state containing image data
            
        Returns:
            Updated state with extracted data
        """
        logger.info("--- AGENT: Image Extractor ---")
        
        image_base64 = state.get("image_base64")
        if not image_base64:
            logger.error("No image provided for extraction")
            return {
                **state,
                "raw_extraction_text": None,
                "quality_warnings": state.get("quality_warnings", []) + ["No image provided for extraction"]
            }
        
        # Use the exact user prompt
        prompt = USER_PROMPT
        
        # Add retry feedback if available
        retry_count = state.get("retry_count", 0)
        if retry_count > 0:
            feedback = state.get("feedback", "")
            prompt += f"\n\nIMPORTANT FEEDBACK FROM PREVIOUS ATTEMPT:\n{feedback}\n\nPlease address the feedback and provide accurate extraction."
        
        try:
            # Create LangChain message with image
            message = HumanMessage(content=[
                {"type": "text", "text": prompt}, 
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ])
            
            logger.info("Invoking Gemini 2.5 Pro for prescription extraction with exact user prompt...")
            response = await self.llm_vision.ainvoke([message])
            logger.info("Gemini 2.5 Pro extraction complete")
            
            response_text = response.content
            logger.info(f"Extracted text length: {len(response_text) if response_text else 0} characters")
            
            # Validate the extracted JSON
            is_valid, parsed_data, error_msg = validate_extraction_json(response_text)
            
            if is_valid and parsed_data:
                logger.info("Successfully extracted and validated prescription data")
                
                # Prepare data for specialized agents
                medications_to_process = parsed_data.get("medications", [])
                patient_data = parsed_data.get("patient", {})
                prescriber_data = parsed_data.get("prescriber", {})
                
                return {
                    **state,
                    "raw_extraction_text": response_text,
                    "prescription_data": parsed_data,
                    "medications_to_process": medications_to_process,
                    "patient_data": patient_data,
                    "prescriber_data": prescriber_data,
                    "is_valid": True,
                    "extraction_completed": True
                }
            else:
                logger.warning(f"Extraction validation failed: {error_msg}")
                return {
                    **state,
                    "raw_extraction_text": response_text,
                    "is_valid": False,
                    "feedback": error_msg,
                    "quality_warnings": state.get("quality_warnings", []) + [f"Extraction validation failed: {error_msg}"]
                }
            
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            return {
                **state,
                "raw_extraction_text": None,
                "is_valid": False,
                "quality_warnings": state.get("quality_warnings", []) + [f"Image extraction failed: {str(e)}"]
            }
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process method for compatibility with workflow
        
        Args:
            state: Workflow state
            
        Returns:
            Updated state
        """
        return await self.extract_prescription_data(state)