"""
Clinical Safety Agent - Comprehensive medication safety validation
Based on scenario.mdc requirements for clinical safety review
Refactored to use prompts.py and tools.py structure
"""

import logging
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.settings.config import settings
from .prompts import (
    get_medication_safety_assessment_prompt,
)
from .tools import (
    get_rxnorm_safety_context,
    validate_safety_assessment_response,
    get_default_safety_assessment,
    calculate_overall_safety_score,
    determine_safety_status,
    extract_critical_safety_flags,
    extract_safety_recommendations
)

from langfuse import observe


logger = logging.getLogger(__name__)


class ClinicalSafetyAgent:
    """Agent for comprehensive clinical safety validation"""
    
    def __init__(self):
        """Initialize the Clinical Safety Agent"""
        try:
            # Initialize Gemini 2.5 Pro model
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-pro",
                temperature=0,
                max_output_tokens=4096,
                google_api_key=settings.google_api_key
            )
            
            logger.info("✅ Clinical Safety Agent initialized with Gemini 2.5 Pro")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Clinical Safety Agent: {e}")
            raise

    @observe(name="clinical_safety_agent", as_type="generation", capture_input=True, capture_output=True)
    async def review_prescription_safety(self, prescription_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive clinical safety review of prescription data
        
        Args:
            prescription_data: Complete prescription data dictionary
            
        Returns:
            Dict containing safety assessment results
        """
        try:
            logger.info("--- AGENT: Clinical Safety Review ---")
            
            # Extract medications for safety review
            medications = prescription_data.get("medications", [])
            if not medications:
                return {
                    "safety_status": "no_medications",
                    "safety_score": 0,
                    "safety_flags": ["No medications found for safety review"],
                    "recommendations": []
                }
            
            # Perform comprehensive safety checks
            safety_results = []
            
            for i, medication in enumerate(medications):
                med_safety = await self._assess_medication_safety(medication, i + 1)
                safety_results.append(med_safety)
            
            # Calculate overall safety score using tools
            overall_safety_score = calculate_overall_safety_score(safety_results)
            
            # Determine overall safety status using tools
            safety_status = determine_safety_status(overall_safety_score)
            
            # Extract consolidated flags and recommendations using tools
            overall_safety_flags = extract_critical_safety_flags(safety_results)
            overall_recommendations = extract_safety_recommendations(safety_results)
            
            logger.info(f"✅ Clinical safety review completed - Status: {safety_status}, Score: {overall_safety_score:.1f}")
            
            return {
                "safety_status": safety_status,
                "safety_score": overall_safety_score,
                "safety_flags": overall_safety_flags,  # Already deduplicated by tools
                "recommendations": overall_recommendations,  # Already deduplicated by tools
                "medication_safety_details": safety_results,
                "review_summary": self._generate_safety_summary(safety_status, overall_safety_score, overall_safety_flags)
            }
            
        except Exception as e:
            logger.error(f"❌ Clinical safety review failed: {e}")
            return {
                "safety_status": "error",
                "safety_score": 0,
                "safety_flags": [f"Safety review error: {e}"],
                "recommendations": ["Manual pharmacist review required"],
                "error": str(e)
            }

    async def _assess_medication_safety(self, medication: Dict[str, Any], med_number: int) -> Dict[str, Any]:
        """Assess safety of individual medication using specialized prompts and tools"""
        try:
            drug_name = medication.get("drug_name", "Unknown")
            strength = medication.get("strength", "")
            instructions = medication.get("instructions_for_use", "")
            sig_english = medication.get("sig_english", "")
            
            logger.info(f"🔍 Assessing safety for medication {med_number}: {drug_name}")
            
            # Get RxNorm context for safety assessment
            rxnorm_context = get_rxnorm_safety_context(medication)
            
            # Build specialized safety assessment prompt
            safety_prompt = get_medication_safety_assessment_prompt(
                drug_name=drug_name,
                strength=strength,
                instructions=instructions,
                sig_english=sig_english,
                rxnorm_context=rxnorm_context
            )
            
            # Get safety assessment from Gemini 2.5 Pro
            response = await self.llm.ainvoke(safety_prompt)
            
            # Validate and repair the response using tools
            safety_data = validate_safety_assessment_response(response.content)
            
            logger.info(f"✅ Safety assessment completed for {drug_name}: Score {safety_data['safety_score']}, Risk {safety_data['risk_level']}")
            return safety_data
                
        except Exception as e:
            logger.error(f"❌ Medication safety assessment failed for {drug_name}: {e}")
            return get_default_safety_assessment(drug_name, str(e))

    def _generate_safety_summary(self, status: str, score: float, flags: List[str]) -> str:
        """Generate human-readable safety summary"""
        flag_count = len(flags)
        
        if status == "safe":
            return f"Prescription passes safety review (Score: {score:.1f}/100). {flag_count} minor considerations noted."
        elif status == "caution":
            return f"Prescription requires caution (Score: {score:.1f}/100). {flag_count} safety concerns identified - pharmacist review recommended."
        else:
            return f"Prescription has safety concerns (Score: {score:.1f}/100). {flag_count} safety flags raised - immediate pharmacist review required."
