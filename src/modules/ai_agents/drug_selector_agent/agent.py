"""Smart Drug Selector Agent - Enhanced drug validation and selection"""

from typing import Dict, Any, List
from src.modules.ai_agents.utils.base_agent import BaseAgent
from src.core.settings.logging import logger
from .tools import llm_select_best_match
from .prompts import build_drug_selection_prompt


class SmartDrugSelectorAgent(BaseAgent):
    """Agent for intelligent drug selection and validation"""
    
    def __init__(self):
        super().__init__("SmartDrugSelectorAgent")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and correct drug information using smart selection"""
        try:
            drug_name = state.get("drug_name")
            candidates = state.get("candidates", [])
            original_medication = state.get("original_medication", {})
            
            logger.info(f"--- AGENT: Drug Selection for {drug_name} ---")
            self.scratchpad.add_thought(f"Processing drug selection for: {drug_name}")
            
            if not drug_name:
                return self.add_warning(state, "No drug name provided for selection")
            
            if not candidates:
                self.scratchpad.add_observation("No candidates provided for drug selection")
                return state
            
            self.scratchpad.add_action("Selecting best drug match using LLM")
            selected_drug = await llm_select_best_match(candidates, original_medication)
            self.scratchpad.add_observation(f"Selected drug: {selected_drug.get('drug_name', 'Unknown') if selected_drug else 'None'}")
            
            # Update state with selected drug
            state['selected_drug'] = selected_drug
            return state
            
        except Exception as e:
            logger.error(f"Drug selection failed: {e}")
            return self.create_error_response(str(e), state)
    
    def get_prompt(self, **kwargs) -> str:
        return build_drug_selection_prompt(**kwargs)