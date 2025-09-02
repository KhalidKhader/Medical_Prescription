"""
Instructions of Use Validation Agent
Validates medication instructions for safety, completeness, and clinical accuracy
"""

import logging
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.settings.config import settings

from .prompts import (
    get_instruction_validation_prompt,
    get_safety_cross_check_prompt,
)
from .tools import (
    validate_instruction_components,
    assess_safety_risks,
    validate_spanish_translation,
    repair_validation_json
)
from langfuse import observe


logger = logging.getLogger(__name__)


class InstructionsOfUseValidationAgent:
    """Agent for validating medication instructions for safety and clinical accuracy"""
    
    def __init__(self):
        """Initialize the Instructions of Use Validation Agent"""
        try:
            # Initialize Gemini 2.5 Pro model
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-pro",
                temperature=0,
                max_output_tokens=4096,
                google_api_key=settings.google_api_key
            )
            
            logger.info("✅ Instructions of Use Validation Agent initialized with Gemini 2.5 Pro")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Instructions Validation Agent: {e}")
            raise
    
    @observe(name="validate_medication_instructions", as_type="generation", capture_input=True, capture_output=True)
    async def validate_medication_instructions(
        self, 
        instruction_data: Dict[str, Any], 
        rxnorm_context: Dict[str, Any],
        patient_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive validation of medication instructions
        
        Args:
            instruction_data: Generated instruction data to validate
            rxnorm_context: RxNorm clinical context
            patient_context: Patient information (optional)
            
        Returns:
            Comprehensive validation results
        """
        try:
            drug_name = instruction_data.get("drug_name", "Unknown")
            logger.info(f"🔍 VALIDATION AGENT: Validating instructions for {drug_name}")
            
            # Step 1: Component validation
            logger.info("📋 Step 1: Validating instruction components...")
            structured_instructions = instruction_data.get("structured_instructions", {})
            component_validation = validate_instruction_components(structured_instructions)
            
            # Step 2: Safety risk assessment
            logger.info("🛡️ Step 2: Assessing safety risks...")
            safety_assessment = assess_safety_risks(drug_name, structured_instructions, rxnorm_context)
            
            # Step 3: Spanish translation validation
            logger.info("🌐 Step 3: Validating Spanish translation...")
            spanish_validation = validate_spanish_translation(
                instruction_data.get("sig_english", ""),
                instruction_data.get("sig_spanish", "")
            )
            
            # Step 4: Clinical validation using LLM
            logger.info("🏥 Step 4: Performing clinical validation...")
            clinical_validation = await self._perform_clinical_validation(
                instruction_data, rxnorm_context, patient_context
            )
            
            # Step 5: Safety cross-check
            logger.info("🔒 Step 5: Performing safety cross-check...")
            safety_cross_check = await self._perform_safety_cross_check(
                drug_name, instruction_data.get("sig_english", ""), patient_context
            )
            
            # Step 6: Compile final validation results
            logger.info("📊 Step 6: Compiling final validation results...")
            final_validation = self._compile_validation_results(
                component_validation,
                safety_assessment,
                spanish_validation,
                clinical_validation,
                safety_cross_check,
                instruction_data
            )
            
            logger.info(f"✅ Validation complete for {drug_name}: {final_validation.get('final_recommendation', 'UNKNOWN')}")
            return final_validation
            
        except Exception as e:
            logger.error(f"❌ Instruction validation failed: {e}")
            return {
                "validation_passed": False,
                "final_recommendation": "REJECT",
                "overall_score": 0,
                "critical_error": str(e),
                "pharmacist_notes": f"Validation system error: {str(e)} - Manual review required"
            }
    
    async def _perform_clinical_validation(
        self, 
        instruction_data: Dict[str, Any], 
        rxnorm_context: Dict[str, Any],
        patient_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform clinical validation using LLM"""
        try:
            prompt = get_instruction_validation_prompt(instruction_data, rxnorm_context)
            
            if patient_context:
                prompt += f"\n\nPatient Context: {patient_context}"
            
            response = await self.llm.ainvoke(prompt)
            validation_data = repair_validation_json(response.content)
            
            return validation_data
            
        except Exception as e:
            logger.error(f"❌ Clinical validation failed: {e}")
            return {
                "validation_passed": False,
                "overall_score": 0,
                "clinical_safety": {"is_safe": False, "concerns": [f"Validation error: {str(e)}"]},
                "error": str(e)
            }
    
    async def _perform_safety_cross_check(
        self, 
        drug_name: str, 
        instructions: str, 
        patient_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform safety cross-check using LLM"""
        try:
            prompt = get_safety_cross_check_prompt(drug_name, instructions, patient_context)
            response = await self.llm.ainvoke(prompt)
            safety_data = repair_validation_json(response.content)
            
            return safety_data
            
        except Exception as e:
            logger.error(f"❌ Safety cross-check failed: {e}")
            return {
                "safety_approved": False,
                "risk_level": "CRITICAL",
                "final_safety_decision": "UNSAFE",
                "error": str(e)
            }
    
    def _compile_validation_results(
        self,
        component_validation: Dict[str, Any],
        safety_assessment: Dict[str, Any],
        spanish_validation: Dict[str, Any],
        clinical_validation: Dict[str, Any],
        safety_cross_check: Dict[str, Any],
        instruction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compile all validation results into final assessment"""
        try:
            # Calculate overall scores
            component_score = component_validation.get("overall_score", 0)
            spanish_score = spanish_validation.get("accuracy_score", 0)
            clinical_score = clinical_validation.get("overall_score", 0)
            
            overall_score = (component_score + spanish_score + clinical_score) / 3
            
            # Determine safety status
            is_safe = (
                safety_assessment.get("overall_risk") in ["LOW", "MODERATE"] and
                clinical_validation.get("clinical_safety", {}).get("is_safe", False) and
                safety_cross_check.get("safety_approved", False)
            )
            
            # Determine completeness
            is_complete = (
                component_validation.get("all_valid", False) and
                clinical_validation.get("completeness", {}).get("is_complete", False)
            )
            
            # Final recommendation
            if not is_safe:
                final_recommendation = "REJECT"
            elif is_safe and is_complete and overall_score >= 80:
                final_recommendation = "APPROVE"
            else:
                final_recommendation = "REVIEW_REQUIRED"
            
            # Compile all issues and concerns
            all_issues = []
            all_issues.extend(component_validation.get("issues", []))
            all_issues.extend(safety_assessment.get("safety_concerns", []))
            all_issues.extend(spanish_validation.get("issues", []))
            all_issues.extend(clinical_validation.get("clinical_safety", {}).get("concerns", []))
            
            # Create comprehensive validation result
            validation_result = {
                "validation_passed": final_recommendation == "APPROVE",
                "final_recommendation": final_recommendation,
                "overall_score": round(overall_score, 1),
                "validation_summary": {
                    "component_score": component_score,
                    "safety_score": 100 - len(safety_assessment.get("safety_concerns", [])) * 20,
                    "spanish_score": spanish_score,
                    "clinical_score": clinical_score
                },
                "safety_assessment": {
                    "is_safe": is_safe,
                    "risk_level": safety_assessment.get("overall_risk", "UNKNOWN"),
                    "safety_concerns": all_issues,
                    "monitoring_required": safety_assessment.get("monitoring_required", [])
                },
                "completeness_assessment": {
                    "is_complete": is_complete,
                    "missing_components": component_validation.get("issues", []),
                    "recommendations": clinical_validation.get("completeness", {}).get("recommendations", [])
                },
                "spanish_validation": spanish_validation,
                "pharmacist_notes": self._generate_pharmacist_notes(
                    final_recommendation, all_issues, safety_assessment, clinical_validation
                ),
                "approved_instructions": self._get_approved_instructions(
                    final_recommendation, instruction_data, clinical_validation
                )
            }
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Result compilation failed: {e}")
            return {
                "validation_passed": False,
                "final_recommendation": "REJECT",
                "overall_score": 0,
                "error": str(e)
            }
    
    def _generate_pharmacist_notes(
        self, 
        recommendation: str, 
        issues: list, 
        safety_assessment: Dict[str, Any],
        clinical_validation: Dict[str, Any]
    ) -> str:
        """Generate pharmacist notes based on validation results"""
        try:
            notes = []
            
            if recommendation == "APPROVE":
                notes.append("Instructions validated and approved for patient use.")
            elif recommendation == "REJECT":
                notes.append("Instructions REJECTED due to safety concerns.")
            else:
                notes.append("Instructions require pharmacist review before approval.")
            
            if issues:
                notes.append(f"Issues identified: {', '.join(issues[:3])}{'...' if len(issues) > 3 else ''}")
            
            if safety_assessment.get("overall_risk") in ["HIGH", "CRITICAL"]:
                notes.append(f"HIGH RISK medication - {safety_assessment.get('overall_risk')} risk level.")
            
            monitoring = safety_assessment.get("monitoring_required", [])
            if monitoring:
                notes.append(f"Monitoring required: {', '.join(monitoring[:2])}")
            
            return " ".join(notes)
            
        except Exception as e:
            return f"Note generation error: {str(e)}"
    
    def _get_approved_instructions(
        self, 
        recommendation: str, 
        instruction_data: Dict[str, Any],
        clinical_validation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get approved instructions based on validation results"""
        try:
            if recommendation == "APPROVE":
                return {
                    "sig_english": instruction_data.get("sig_english"),
                    "sig_spanish": instruction_data.get("sig_spanish")
                }
            elif clinical_validation.get("approved_instructions"):
                return clinical_validation["approved_instructions"]
            else:
                return {
                    "sig_english": None,
                    "sig_spanish": None
                }
                
        except Exception as e:
            logger.error(f"❌ Approved instructions error: {e}")
            return {"sig_english": None, "sig_spanish": None}
