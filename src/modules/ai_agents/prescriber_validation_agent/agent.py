"""
Prescriber Validation Agent
Validates prescriber information using Gemini 2.5 Pro
"""

from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.settings.config import settings
from src.core.settings.logging import logger

from langfuse import observe


from .prompts import get_prescriber_validation_prompt
from src.modules.ai_agents.prescriber_agent.tools import (
    validate_npi_number,
    validate_dea_number,
    validate_prescriber_name,
    repair_prescriber_json,
    extract_prescriber_quality_metrics
)


class PrescriberValidationAgent:
    """Agent for validating prescriber information using Gemini 2.5 Pro"""
    
    def __init__(self):
        """Initialize the prescriber validation agent with Gemini 2.5 Pro"""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro", 
            temperature=0,
            google_api_key=settings.google_api_key
        )
        logger.info("Prescriber Validation Agent initialized with Gemini 2.5 Pro")
    
    @observe(name="prescriber_validation", as_type="generation", capture_input=True, capture_output=True)
    async def validate_prescriber_info(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate prescriber information
        
        Args:
            state: Workflow state with prescriber data
            
        Returns:
            Updated state with validated prescriber info
        """
        logger.info("--- AGENT: Prescriber Validator ---")
        
        try:
            prescriber_data = state.get("prescriber_data", {})
            if not prescriber_data:
                return self._add_warning(state, "No prescriber data available for validation")
            
            # Perform validation using tools
            validation_results = self._perform_validation(prescriber_data)
            
            # Use Gemini for additional validation if needed
            if validation_results["needs_llm_validation"]:
                prompt = get_prescriber_validation_prompt(prescriber_data)
                response = await self.llm.ainvoke(prompt)
                
                # Parse validation response
                is_valid, validated_data, error_msg = repair_prescriber_json(response.content)
                if is_valid and validated_data:
                    validation_results["validated_data"] = validated_data
            
            logger.info(f"Prescriber validation results: {validation_results['summary']}")
            
            return {
                **state,
                "prescriber_data": validation_results["validated_data"],
                "prescriber_validation_results": validation_results,
                "quality_warnings": state.get("quality_warnings", []) + validation_results["warnings"]
            }
            
        except Exception as e:
            logger.error(f"Prescriber validation failed: {e}")
            return self._add_warning(state, f"Prescriber validation failed: {str(e)}")
    
    def _perform_validation(self, prescriber_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive prescriber data validation using tools
        
        Args:
            prescriber_data: Prescriber data to validate
            
        Returns:
            Validation results dictionary
        """
        results = {
            "is_valid": True,
            "warnings": [],
            "validated_data": prescriber_data.copy(),
            "needs_llm_validation": False,
            "field_validations": {},
            "summary": "Prescriber data validation completed"
        }
        
        # Validate name
        if prescriber_data.get("full_name"):
            is_valid, cleaned_name = validate_prescriber_name(prescriber_data["full_name"])
            results["field_validations"]["full_name"] = {
                "valid": is_valid,
                "cleaned_value": cleaned_name
            }
            if is_valid:
                results["validated_data"]["full_name"] = cleaned_name
            else:
                results["warnings"].append("Invalid prescriber name format")
                results["is_valid"] = False
        
        # Validate NPI number
        if prescriber_data.get("npi_number"):
            is_valid, cleaned_npi = validate_npi_number(prescriber_data["npi_number"])
            results["field_validations"]["npi_number"] = {
                "valid": is_valid,
                "cleaned_value": cleaned_npi
            }
            if is_valid:
                results["validated_data"]["npi_number"] = cleaned_npi
            else:
                results["warnings"].append("Invalid NPI number format")
                results["is_valid"] = False
        
        # Validate DEA number
        if prescriber_data.get("dea_number"):
            is_valid, cleaned_dea = validate_dea_number(prescriber_data["dea_number"])
            results["field_validations"]["dea_number"] = {
                "valid": is_valid,
                "cleaned_value": cleaned_dea
            }
            if is_valid:
                results["validated_data"]["dea_number"] = cleaned_dea
            else:
                results["warnings"].append("Invalid DEA number format")
                results["is_valid"] = False
        
        # Determine if LLM validation is needed
        if results["warnings"] or not results["is_valid"]:
            results["needs_llm_validation"] = True
        
        return results
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process method for compatibility with workflow
        
        Args:
            state: Workflow state
            
        Returns:
            Updated state
        """
        return await self.validate_prescriber_info(state)
    
    def _add_warning(self, state: Dict[str, Any], warning: str) -> Dict[str, Any]:
        """Add warning to state"""
        warnings = state.get("quality_warnings", [])
        warnings.append(warning)
        return {
            **state,
            "quality_warnings": warnings
        }