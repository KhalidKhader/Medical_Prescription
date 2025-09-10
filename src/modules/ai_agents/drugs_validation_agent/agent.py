"""Drugs Validation Agent - Validates medication information"""

from typing import Dict, Any
from src.modules.ai_agents.utils.base_agent import BaseAgent
from src.core.settings.logging import logger
from .prompts import get_medication_validation_prompt
from .tools import validate_medication_data


class DrugsValidationAgent(BaseAgent):
    """Agent for validating medication information"""
    
    def __init__(self):
        super().__init__("DrugsValidationAgent")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate medications in the state"""
        try:
            logger.info("--- AGENT: Drugs Validation ---")
            
            medications = state.get("processed_medications", [])
            if not medications:
                return self.add_warning(state, "No medications found for validation")
            
            self.scratchpad.add_thought(f"Validating {len(medications)} medications")
            
            validated_medications = []
            for i, medication in enumerate(medications):
                self.scratchpad.add_action(f"Validating medication {i+1}")
                validated_med = validate_medication_data(medication)
                validated_medications.append(validated_med)
            
            self.scratchpad.add_observation("Medication validation completed")
            
            return {
                **state,
                "validated_medications": validated_medications
            }
            
        except Exception as e:
            logger.error(f"Medication validation failed: {e}")
            return self.create_error_response(str(e), state)
    
    def get_prompt(self, **kwargs) -> str:
        return get_medication_validation_prompt(**kwargs)