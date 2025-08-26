"""
Hallucination Detection Agent
Detects potential hallucinations and inconsistencies in extracted prescription data using Gemini 2.5 Pro
"""

from typing import Dict, Any, List
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
from .prompts import (
    get_hallucination_check_prompt,
    get_consistency_check_prompt,
    get_medical_plausibility_check_prompt
)
from .tools import (
    detect_data_inconsistencies,
    validate_medical_plausibility,
    check_prescription_completeness
)


class HallucinationDetectionAgent:
    """Agent for detecting hallucinations and inconsistencies using Gemini 2.5 Pro"""
    
    def __init__(self):
        """Initialize the hallucination detection agent with Gemini 2.5 Pro"""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro", 
            temperature=0,
            google_api_key=settings.google_api_key
        )
        logger.info("Hallucination Detection Agent initialized with Gemini 2.5 Pro")
    
    @observe(name="hallucination_detection", as_type="generation", capture_input=True, capture_output=True)
    async def detect_hallucinations(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect potential hallucinations and inconsistencies in prescription data
        
        Args:
            state: Workflow state with prescription data
            
        Returns:
            Updated state with hallucination flags
        """
        logger.info("--- AGENT: Hallucination Detector ---")
        
        try:
            prescription_data = state.get("prescription_data", {})
            if not prescription_data:
                return self._add_warning(state, "No prescription data available for hallucination detection")
            
            hallucination_flags = []
            safety_flags = []
            
            # Check data consistency
            consistency_issues = detect_data_inconsistencies(prescription_data)
            if consistency_issues:
                hallucination_flags.extend(consistency_issues)
                logger.warning(f"Data consistency issues detected: {consistency_issues}")
            
            # Check medical plausibility
            medications = prescription_data.get("medications", [])
            patient_info = prescription_data.get("patient", {})
            
            if medications:
                plausibility_issues = await self._check_medical_plausibility(medications, patient_info)
                if plausibility_issues:
                    hallucination_flags.extend(plausibility_issues)
                    logger.warning(f"Medical plausibility issues detected: {plausibility_issues}")
            
            # Check prescription completeness
            completeness_issues = check_prescription_completeness(prescription_data)
            if completeness_issues:
                safety_flags.extend(completeness_issues)
                logger.info(f"Completeness issues detected: {completeness_issues}")
            
            # Use Gemini for advanced hallucination detection
            advanced_checks = await self._perform_advanced_hallucination_checks(prescription_data)
            if advanced_checks.get("hallucination_detected"):
                hallucination_flags.extend(advanced_checks.get("issues", []))
            
            logger.info(f"Hallucination detection completed. Flags: {len(hallucination_flags)} hallucinations, {len(safety_flags)} safety issues")
            
            return {
                **state,
                "hallucination_flags": hallucination_flags,
                "safety_flags": safety_flags,
                "hallucination_detection_results": {
                    "total_flags": len(hallucination_flags) + len(safety_flags),
                    "hallucination_score": min(len(hallucination_flags) * 10, 100),
                    "safety_score": min(len(safety_flags) * 5, 100)
                }
            }
            
        except Exception as e:
            logger.error(f"Hallucination detection failed: {e}")
            return self._add_warning(state, f"Hallucination detection failed: {str(e)}")
    
    async def _check_medical_plausibility(self, medications: List[Dict[str, Any]], patient_info: Dict[str, Any]) -> List[str]:
        """
        Check medical plausibility of medications using Gemini
        
        Args:
            medications: List of medications
            patient_info: Patient information
            
        Returns:
            List of plausibility issues
        """
        try:
            prompt = get_medical_plausibility_check_prompt(medications, patient_info)
            response = await self.llm.ainvoke(prompt)
            
            response_text = response.content.lower()
            issues = []
            
            if "questionable" in response_text or "review needed" in response_text:
                issues.append("Medical plausibility concerns identified")
            
            if "unusual" in response_text or "rare" in response_text:
                issues.append("Unusual drug combinations or dosages detected")
            
            return issues
            
        except Exception as e:
            logger.error(f"Medical plausibility check failed: {e}")
            return ["Medical plausibility check failed"]
    
    async def _perform_advanced_hallucination_checks(self, prescription_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform advanced hallucination detection using Gemini
        
        Args:
            prescription_data: Complete prescription data
            
        Returns:
            Dictionary with hallucination detection results
        """
        try:
            prompt = get_consistency_check_prompt(prescription_data)
            response = await self.llm.ainvoke(prompt)
            
            response_text = response.content.lower()
            
            results = {
                "hallucination_detected": False,
                "issues": [],
                "confidence": 0.8
            }
            
            # Analyze response for hallucination indicators
            if "inconsistent" in response_text or "contradictory" in response_text:
                results["hallucination_detected"] = True
                results["issues"].append("Data consistency issues detected")
            
            if "impossible" in response_text or "unrealistic" in response_text:
                results["hallucination_detected"] = True
                results["issues"].append("Unrealistic values detected")
            
            if "missing critical" in response_text:
                results["issues"].append("Critical information missing")
            
            return results
            
        except Exception as e:
            logger.error(f"Advanced hallucination check failed: {e}")
            return {
                "hallucination_detected": True,
                "issues": ["Hallucination detection system error"],
                "confidence": 0.0
            }
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process method for compatibility with workflow
        
        Args:
            state: Workflow state
            
        Returns:
            Updated state
        """
        return await self.detect_hallucinations(state)
    
    def _add_warning(self, state: Dict[str, Any], warning: str) -> Dict[str, Any]:
        """Add warning to state"""
        warnings = state.get("quality_warnings", [])
        warnings.append(warning)
        return {
            **state,
            "quality_warnings": warnings
        }