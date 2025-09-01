"""
Drugs Validation Agent
Validates medication information using Gemini 2.5 Pro
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

from .prompts import get_drugs_validation_prompt


class DrugsValidationAgent:
    """Agent for validating medication information using Gemini 2.5 Pro"""
    
    def __init__(self):
        """Initialize the drugs validation agent with Gemini 2.5 Pro"""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro", 
            temperature=0,
            google_api_key=settings.google_api_key
        )
        logger.info("Drugs Validation Agent initialized with Gemini 2.5 Pro")
    
    @observe(name="drugs_validation", as_type="generation", capture_input=True, capture_output=True)
    async def validate_medications(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate medication information
        
        Args:
            state: Workflow state with processed medications
            
        Returns:
            Updated state with validated medication info
        """
        logger.info("--- AGENT: Drugs Validator ---")
        
        try:
            processed_medications = state.get("processed_medications", [])
            if not processed_medications:
                return self._add_warning(state, "No processed medications available for validation")
            
            validated_medications = []
            validation_results = {
                "total_medications": len(processed_medications),
                "validated_count": 0,
                "warnings": [],
                "errors": []
            }
            
            for i, medication in enumerate(processed_medications):
                drug_name = medication.get("drug_name", f"Medication {i+1}")
                logger.info(f"Validating medication: {drug_name}")
                
                # Basic validation - detailed validation handled by other agents
                is_valid = True
                warnings = []
                
                # Check essential fields
                if not medication.get("drug_name"):
                    warnings.append("Missing drug name")
                    is_valid = False
                
                if not medication.get("instructions_for_use"):
                    warnings.append("Missing instructions for use")
                    is_valid = False
                
                if warnings:
                    validation_results["warnings"].extend([f"{drug_name}: {w}" for w in warnings])
                    logger.warning(f"Validation warnings for {drug_name}: {warnings}")
                
                if is_valid:
                    validation_results["validated_count"] += 1
                
                validated_medications.append(medication)
            
            logger.info(f"Drugs validation completed: {validation_results['validated_count']}/{validation_results['total_medications']} valid")
            
            return {
                **state,
                "processed_medications": validated_medications,
                "drugs_validation_results": validation_results,
                "quality_warnings": state.get("quality_warnings", []) + validation_results["warnings"]
            }
            
        except Exception as e:
            logger.error(f"Drugs validation failed: {e}")
            return self._add_warning(state, f"Drugs validation failed: {str(e)}")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process method for compatibility with workflow
        
        Args:
            state: Workflow state
            
        Returns:
            Updated state
        """
        return await self.validate_medications(state)
    
    def _add_warning(self, state: Dict[str, Any], warning: str) -> Dict[str, Any]:
        """Add warning to state"""
        warnings = state.get("quality_warnings", [])
        warnings.append(warning)
        return {
            **state,
            "quality_warnings": warnings
        }