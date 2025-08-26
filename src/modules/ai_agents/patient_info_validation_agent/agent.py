"""
Patient Info Validation Agent
Validates patient information using Gemini 2.5 Pro
"""

from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI

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
from .prompts import get_patient_validation_prompt
from src.modules.ai_agents.patient_info_agent.tools import (
    validate_patient_name,
    validate_date_of_birth,
    validate_patient_address,
    check_age_dob_consistency,
    repair_patient_json
)


class PatientInfoValidationAgent:
    """Agent for validating patient information using Gemini 2.5 Pro"""
    
    def __init__(self):
        """Initialize the patient validation agent with Gemini 2.5 Pro"""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro", 
            temperature=0,
            google_api_key=settings.google_api_key
        )
        logger.info("Patient Info Validation Agent initialized with Gemini 2.5 Pro")
    
    @observe(name="patient_validation",as_type="generation", capture_input=True, capture_output=True)
    async def validate_patient_info(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate patient information
        
        Args:
            state: Workflow state with patient data
            
        Returns:
            Updated state with validated patient info
        """
        logger.info("--- AGENT: Patient Info Validator ---")
        
        try:
            patient_data = state.get("patient_data", {})
            if not patient_data:
                return self._add_warning(state, "No patient data available for validation")
            
            # Perform validation using tools
            validation_results = self._perform_validation(patient_data)
            
            # Use Gemini for additional validation if needed
            if validation_results["needs_llm_validation"]:
                prompt = get_patient_validation_prompt(patient_data)
                response = await self.llm.ainvoke(prompt)
                
                # Parse validation response
                is_valid, validated_data, error_msg = repair_patient_json(response.content)
                if is_valid and validated_data:
                    validation_results["validated_data"] = validated_data
            
            logger.info(f"Patient validation results: {validation_results['summary']}")
            
            return {
                **state,
                "patient_data": validation_results["validated_data"],
                "patient_validation_results": validation_results,
                "quality_warnings": state.get("quality_warnings", []) + validation_results["warnings"]
            }
            
        except Exception as e:
            logger.error(f"Patient validation failed: {e}")
            return self._add_warning(state, f"Patient validation failed: {str(e)}")
    
    def _perform_validation(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive patient data validation using tools
        
        Args:
            patient_data: Patient data to validate
            
        Returns:
            Validation results dictionary
        """
        results = {
            "is_valid": True,
            "warnings": [],
            "validated_data": patient_data.copy(),
            "needs_llm_validation": False,
            "field_validations": {},
            "summary": "Patient data validation completed"
        }
        
        # Validate name
        if patient_data.get("full_name"):
            is_valid, cleaned_name = validate_patient_name(patient_data["full_name"])
            results["field_validations"]["full_name"] = {
                "valid": is_valid,
                "cleaned_value": cleaned_name
            }
            if is_valid:
                results["validated_data"]["full_name"] = cleaned_name
            else:
                results["warnings"].append("Invalid patient name format")
                results["is_valid"] = False
        
        # Validate date of birth
        if patient_data.get("date_of_birth"):
            is_valid, standardized_date, calculated_age = validate_date_of_birth(patient_data["date_of_birth"])
            results["field_validations"]["date_of_birth"] = {
                "valid": is_valid,
                "cleaned_value": standardized_date,
                "calculated_age": calculated_age
            }
            if is_valid:
                results["validated_data"]["date_of_birth"] = standardized_date
                if calculated_age:
                    results["validated_data"]["calculated_age"] = calculated_age
            else:
                results["warnings"].append("Invalid date of birth format")
                results["is_valid"] = False
        
        # Validate address
        if patient_data.get("address"):
            is_valid, cleaned_address = validate_patient_address(patient_data["address"])
            results["field_validations"]["address"] = {
                "valid": is_valid,
                "cleaned_value": cleaned_address
            }
            if is_valid:
                results["validated_data"]["address"] = cleaned_address
            else:
                results["warnings"].append("Invalid address format")
        
        # Check age-DOB consistency
        if patient_data.get("age") and patient_data.get("date_of_birth"):
            is_consistent = check_age_dob_consistency(patient_data["age"], patient_data["date_of_birth"])
            results["field_validations"]["age_dob_consistency"] = is_consistent
            if not is_consistent:
                results["warnings"].append("Age inconsistent with date of birth")
                results["needs_llm_validation"] = True
        
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
        return await self.validate_patient_info(state)
    
    def _add_warning(self, state: Dict[str, Any], warning: str) -> Dict[str, Any]:
        """Add warning to state"""
        warnings = state.get("quality_warnings", [])
        warnings.append(warning)
        return {
            **state,
            "quality_warnings": warnings
        }
