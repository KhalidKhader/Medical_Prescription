"""Drugs Agent - Medication processing with RxNorm mapping"""

from typing import Dict, Any
from src.modules.ai_agents.utils.base_agent import BaseAgent
from src.core.settings.logging import logger
from .tools import process_medication_parallel
from .prompts import get_medication_processing_prompt
from src.modules.ai_agents.drug_selector_agent.agent import SmartDrugSelectorAgent


class DrugsAgent(BaseAgent):
    """Agent for processing medications with RxNorm integration"""
    
    def __init__(self):
        super().__init__("DrugsAgent")
        self.drug_selector = SmartDrugSelectorAgent()
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process medications with RxNorm mapping and enhancement"""
        try:
            logger.info("--- AGENT: Drugs Processing ---")
            
            medications = state.get("medications_to_process", [])
            if not medications:
                return self.add_warning(state, "No medications found to process")
            
            self.scratchpad.add_thought(f"Processing {len(medications)} medications")
            self.scratchpad.add_action("Starting parallel medication processing")
            
            processed_medications_with_candidates = await process_medication_parallel(medications, state)

            final_medications = []
            for med_data in processed_medications_with_candidates:
                if med_data.get("all_candidates"):
                    drug_name_field = med_data.get('drug_name')
                    drug_name_str = drug_name_field.get('value') if isinstance(drug_name_field, dict) else drug_name_field
                    
                    self.scratchpad.add_action(f"Running smart selection for {drug_name_str}")

                    selector_state = await self.drug_selector.process({
                        "drug_name": drug_name_str,
                        "candidates": med_data.get("all_candidates"),
                        "original_medication": med_data
                    })
                    selected_med = selector_state.get("selected_drug")
                    if selected_med:
                        final_medications.append({**med_data, **selected_med})
                    else:
                        final_medications.append(med_data)
                else:
                    final_medications.append(med_data)

            self.scratchpad.add_observation(f"Successfully processed {len(final_medications)} medications")
            
            return {
                **state,
                "processed_medications": final_medications
            }
        except Exception as e:
            logger.error(f"Medication processing failed: {e}")
            return self.create_error_response(str(e), state)
    
    def get_prompt(self, **kwargs) -> str:
        return get_medication_processing_prompt(**kwargs)