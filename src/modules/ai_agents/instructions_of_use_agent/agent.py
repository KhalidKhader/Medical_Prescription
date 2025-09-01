"""
Instructions of Use Agent
Generates accurate, structured medication instructions with RxNorm safety validation
"""

import logging
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.settings.config import settings

from .prompts import (
    get_instructions_generation_prompt,
    get_rxnorm_safety_prompt,
    get_spanish_translation_prompt
)
from .tools import (
    get_rxnorm_instruction_context,
    parse_instruction_components,
    validate_instruction_safety,
    repair_instruction_json
)
from langfuse import observe


logger = logging.getLogger(__name__)


class InstructionsOfUseAgent:
    """Agent for generating structured medication instructions with RxNorm safety validation"""
    
    def __init__(self):
        """Initialize the Instructions of Use Agent"""
        try:
            # Initialize Gemini 2.5 Pro model
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-pro",
                temperature=0,
                max_output_tokens=4096,
                google_api_key=settings.google_api_key
            )
            
            logger.info("✅ Instructions of Use Agent initialized with Gemini 2.5 Pro")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Instructions of Use Agent: {e}")
            raise
    
    @observe(name="generate_structured_instructions", as_type="generation", capture_input=True, capture_output=True)
    async def generate_structured_instructions(
        self, 
        drug_name: str, 
        strength: str, 
        raw_instructions: str,
        indication: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured medication instructions with RxNorm safety validation
        
        Args:
            drug_name: Name of the medication
            strength: Medication strength/dosage
            raw_instructions: Raw prescription instructions
            indication: Purpose/indication (optional)
            
        Returns:
            Structured instructions with safety validation
        """
        try:
            logger.info(f"🏥 INSTRUCTIONS AGENT: Processing {drug_name} {strength}")
            logger.info(f"📝 Raw instructions: '{raw_instructions}'")
            
            # Step 1: Get RxNorm clinical context
            logger.info("🔍 Step 1: Retrieving RxNorm clinical context...")
            rxnorm_context = get_rxnorm_instruction_context(drug_name, None)  # No rxnorm_data available here
            
            # Step 2: Parse instruction components
            logger.info("📋 Step 2: Parsing instruction components...")
            parsed_components = parse_instruction_components(raw_instructions)
            
            # Step 3: Generate structured instructions with clinical context
            logger.info("🏥 Step 3: Generating structured instructions...")
            prompt = get_instructions_generation_prompt(
                drug_name=drug_name,
                strength=strength,
                raw_instructions=raw_instructions,
                rxnorm_context=rxnorm_context if rxnorm_context.get('found') else None
            )
            
            # Add indication if provided
            if indication:
                prompt += f"\n\nIndication: {indication}"
            
            response = await self.llm.ainvoke(prompt)
            
            # Step 4: Repair and validate JSON response
            logger.info("🔧 Step 4: Processing and validating response...")
            instruction_data = repair_instruction_json(response.content)
            
            # Step 5: Safety validation against RxNorm
            logger.info("🛡️ Step 5: Performing safety validation...")
            if instruction_data.get("structured_instructions") and rxnorm_context.get('found'):
                safety_validation = validate_instruction_safety(
                    drug_name=drug_name,
                    structured_instructions=instruction_data["structured_instructions"],
                    rxnorm_context=rxnorm_context
                )
                instruction_data["safety_validation"] = safety_validation
            
            # Step 6: Enhance with RxNorm context
            logger.info("📊 Step 6: Adding RxNorm clinical context...")
            instruction_data["rxnorm_context"] = rxnorm_context
            instruction_data["parsed_components"] = parsed_components
            
            # Step 7: Final validation and cleanup
            final_result = self._finalize_instructions(instruction_data, drug_name, strength)
            
            logger.info(f"✅ Instructions generation complete for {drug_name}")
            return final_result
            
        except Exception as e:
            logger.error(f"❌ Instructions generation failed for {drug_name}: {e}")
            return {
                "structured_instructions": {
                    "verb": None,
                    "quantity": None,
                    "form": None,
                    "route": None,
                    "frequency": None,
                    "duration": None,
                    "indication": indication
                },
                "sig_english": raw_instructions,
                "sig_spanish": raw_instructions,
                "safety_validation": {
                    "is_safe": False,
                    "safety_concerns": [f"Processing error: {str(e)}"],
                    "rxnorm_match": False,
                    "clinical_notes": "Manual review required due to processing error"
                },
                "certainty": 0,
                "error": str(e)
            }
    
    def _finalize_instructions(self, instruction_data: Dict[str, Any], drug_name: str, strength: str) -> Dict[str, Any]:
        """
        Finalize and validate instruction data
        
        Args:
            instruction_data: Generated instruction data
            drug_name: Medication name
            strength: Medication strength
            
        Returns:
            Finalized instruction data
        """
        try:
            # Ensure all required fields exist
            if not instruction_data.get("structured_instructions"):
                instruction_data["structured_instructions"] = {
                    "verb": "Take",
                    "quantity": "1",
                    "form": "tablet",
                    "route": "by mouth",
                    "frequency": "as directed",
                    "duration": None,
                    "indication": None
                }
            
            # Ensure sig fields exist
            if not instruction_data.get("sig_english"):
                components = instruction_data["structured_instructions"]
                instruction_data["sig_english"] = self._build_sig_from_components(components)
            
            if not instruction_data.get("sig_spanish"):
                instruction_data["sig_spanish"] = self._translate_to_spanish_simple(
                    instruction_data["sig_english"]
                )
            
            # Add metadata
            instruction_data["drug_name"] = drug_name
            instruction_data["strength"] = strength
            instruction_data["agent_version"] = "1.0"
            instruction_data["processing_complete"] = True
            
            return instruction_data
            
        except Exception as e:
            logger.error(f"❌ Instruction finalization failed: {e}")
            return instruction_data
    
    def _build_sig_from_components(self, components: Dict[str, Any]) -> str:
        """Build sig string from structured components"""
        try:
            parts = []
            
            if components.get("verb"):
                parts.append(components["verb"])
            
            if components.get("quantity"):
                parts.append(components["quantity"])
            
            if components.get("form"):
                parts.append(components["form"])
            
            if components.get("route"):
                parts.append(components["route"])
            
            if components.get("frequency"):
                parts.append(components["frequency"])
            
            if components.get("duration"):
                parts.append(components["duration"])
            
            if components.get("indication"):
                parts.append(f"for {components['indication']}")
            
            return " ".join(filter(None, parts))
            
        except Exception as e:
            logger.error(f"❌ Sig building failed: {e}")
            return "Take as directed"
    
    def _translate_to_spanish_simple(self, english_sig: str) -> str:
        """Simple Spanish translation fallback"""
        try:
            # Basic translation mappings (without accents)
            translations = {
                "take": "tome",
                "tablet": "tableta",
                "capsule": "capsula",
                "by mouth": "por la boca",
                "once daily": "una vez al dia",
                "twice daily": "dos veces al dia",
                "three times daily": "tres veces al dia",
                "as needed": "segun sea necesario",
                "for pain": "para el dolor",
                "for infection": "para la infeccion",
                "for": "para"
            }
            
            spanish_sig = english_sig.lower()
            for english, spanish in translations.items():
                spanish_sig = spanish_sig.replace(english, spanish)
            
            return spanish_sig.title()
            
        except Exception as e:
            logger.error(f"❌ Simple Spanish translation failed: {e}")
            return english_sig
    
    @observe(name="validate_generated_instructions", as_type="generation", capture_input=True, capture_output=True)
    async def validate_generated_instructions(self, instruction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate generated instructions for completeness and safety
        
        Args:
            instruction_data: Generated instruction data
            
        Returns:
            Validation results
        """
        try:
            logger.info("🔍 Validating generated instructions...")
            
            validation = {
                "is_complete": True,
                "is_safe": True,
                "completeness_score": 100,
                "safety_score": 100,
                "missing_fields": [],
                "safety_concerns": [],
                "validation_passed": True
            }
            
            # Check completeness
            required_fields = ["verb", "quantity", "route", "frequency"]
            structured = instruction_data.get("structured_instructions", {})
            
            for field in required_fields:
                if not structured.get(field):
                    validation["missing_fields"].append(field)
                    validation["completeness_score"] -= 25
            
            if validation["missing_fields"]:
                validation["is_complete"] = False
            
            # Check safety validation
            safety_data = instruction_data.get("safety_validation", {})
            if not safety_data.get("is_safe", True):
                validation["is_safe"] = False
                validation["safety_concerns"].extend(safety_data.get("safety_concerns", []))
                validation["safety_score"] = safety_data.get("safety_score", 0)
            
            # Final validation
            if not validation["is_complete"] or not validation["is_safe"]:
                validation["validation_passed"] = False
            
            logger.info(f"✅ Validation complete: {validation['validation_passed']}")
            return validation
            
        except Exception as e:
            logger.error(f"❌ Instruction validation failed: {e}")
            return {
                "is_complete": False,
                "is_safe": False,
                "validation_passed": False,
                "error": str(e)
            }
