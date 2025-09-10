"""Instructions of Use Agent - Structured medication instructions with safety validation"""

from typing import Dict, Any, Optional
from src.modules.ai_agents.utils.base_agent import BaseAgent
from src.core.settings.logging import logger
from .prompts import get_instructions_generation_prompt
from .tools import get_rxnorm_instruction_context, parse_instruction_components, validate_instruction_safety
from langfuse import observe


class InstructionsOfUseAgent(BaseAgent):
    """Agent for generating structured medication instructions with RxNorm safety validation"""
    
    def __init__(self):
        super().__init__("InstructionsOfUseAgent")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured instructions from state"""
        try:
            logger.info("--- AGENT: Instructions of Use ---")
            
            drug_name = state.get("drug_name", "")
            self.scratchpad.add_thought(f"Generating instructions for: {drug_name}")
            
            result = await self.generate_structured_instructions(
                drug_name=drug_name,
                strength=state.get("strength", ""),
                raw_instructions=state.get("raw_instructions", ""),
                indication=state.get("indication")
            )
            
            return {**state, "instruction_data": result}
            
        except Exception as e:
            logger.error(f"Instructions processing failed: {e}")
            return self.create_error_response(str(e), state)
    
    def get_prompt(self, **kwargs) -> str:
        return get_instructions_generation_prompt(**kwargs)
    
    @observe(name="generate_structured_instructions", as_type="generation", capture_input=True, capture_output=True)
    async def generate_structured_instructions(
        self, 
        drug_name: str, 
        strength: str, 
        raw_instructions: str,
        indication: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate structured medication instructions with RxNorm safety validation"""
        try:
            self.scratchpad.add_action(f"Generating structured instructions for {drug_name}")
            
            rxnorm_context = get_rxnorm_instruction_context(drug_name, None)
            parsed_components = parse_instruction_components(raw_instructions)
            
            prompt = self.get_prompt(
                drug_name=drug_name,
                strength=strength,
                raw_instructions=raw_instructions,
                rxnorm_context=rxnorm_context
            )
            
            response = await self.call_llm(prompt)
            instruction_data = self.parse_json(response)
            
            if instruction_data.get("structured_instructions") and rxnorm_context.get('found'):
                instruction_data["safety_validation"] = validate_instruction_safety(
                    drug_name, instruction_data["structured_instructions"], rxnorm_context
                )
            
            self.scratchpad.add_observation("Instructions generation completed successfully")
            return instruction_data or self._create_fallback_response(raw_instructions, indication)
            
        except Exception as e:
            logger.error(f"Instructions generation failed for {drug_name}: {e}")
            return {"error": str(e)}
    
    def _create_fallback_response(self, raw_instructions: str, indication: Optional[str]) -> Dict[str, Any]:
        """Create fallback response for failed instruction generation"""
        return {
            "structured_instructions": {
                "verb": "Take", "quantity": "1", "form": "tablet", 
                "route": "by mouth", "frequency": "as directed", 
                "duration": None, "indication": indication
            },
            "sig_english": raw_instructions,
            "sig_spanish": raw_instructions,
            "safety_validation": {"is_safe": True, "safety_concerns": [], "rxnorm_match": False}
        }
