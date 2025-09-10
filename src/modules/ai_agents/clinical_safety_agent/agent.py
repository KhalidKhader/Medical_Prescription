"""Clinical Safety Agent - Comprehensive medication safety validation"""

from typing import Dict, Any
from src.modules.ai_agents.utils.base_agent import BaseAgent
from src.core.settings.logging import logger
from .prompts import get_medication_safety_assessment_prompt
from .tools import get_rxnorm_safety_context, calculate_overall_safety_score


class ClinicalSafetyAgent(BaseAgent):
    """Agent for comprehensive clinical safety validation"""
    
    def __init__(self):
        super().__init__("ClinicalSafetyAgent")

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive clinical safety review of prescription data"""
        try:
            logger.info("--- AGENT: Clinical Safety Review ---")
            
            medications = state.get("medications", [])
            if not medications:
                return self.create_error_response("No medications found for safety review", state)
            
            self.scratchpad.add_thought(f"Reviewing safety for {len(medications)} medications")
            
            safety_results = []
            for i, medication in enumerate(medications):
                self.scratchpad.add_action(f"Assessing safety for medication {i+1}")
                med_safety = await self._assess_medication_safety(medication, i + 1)
                safety_results.append(med_safety)
            
            overall_safety_score = calculate_overall_safety_score(safety_results)
            self.scratchpad.add_observation(f"Overall safety score: {overall_safety_score}")
            
            return {
                **state,
                "safety_status": "safe" if overall_safety_score >= 80 else "unsafe",
                "safety_score": overall_safety_score,
                "medication_safety_details": safety_results
            }
            
        except Exception as e:
            logger.error(f"Clinical safety review failed: {e}")
            return self.create_error_response(str(e), state)
    
    def get_prompt(self, **kwargs) -> str:
        return get_medication_safety_assessment_prompt(**kwargs)
    
    async def review_prescription_safety(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Review prescription safety - alias for process method"""
        return await self.process(state)
    
    async def _assess_medication_safety(self, medication: Dict[str, Any], med_number: int) -> Dict[str, Any]:
        """Assess safety of individual medication"""
        try:
            drug_name = medication.get("drug_name", "Unknown")
            logger.info(f"Assessing safety for medication {med_number}: {drug_name}")
            
            rxnorm_context = get_rxnorm_safety_context(medication)
            safety_prompt = self.get_prompt(
                drug_name=medication.get("drug_name", "Unknown"),
                strength=medication.get("strength", ""),
                instructions=medication.get("instructions_for_use", ""),
                sig_english=medication.get("sig_english", ""),
                rxnorm_context=rxnorm_context
            )
            
            response = await self.call_llm(safety_prompt)
            safety_data = self.parse_json(response)
            
            return safety_data or {"safety_score": 50, "risk_level": "moderate"}
                
        except Exception as e:
            logger.error(f"Medication safety assessment failed: {e}")
            return {"safety_score": 0, "risk_level": "critical", "error": str(e)}
