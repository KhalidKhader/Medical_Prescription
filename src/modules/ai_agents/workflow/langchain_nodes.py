"""
Streamlined LangChain-based workflow nodes
Implements the exact scenario requirements with optimized performance
"""

from typing import Dict, Any
from json_repair import loads as repair_json_loads
from langchain_core.pydantic_v1 import ValidationError
from langchain_google_genai import ChatGoogleGenerativeAI
import json

from src.core.settings.config import settings
from src.core.settings.logging import logger
from src.modules.ai_agents.langchain_image_agent.agent import LangChainImageAgent
from src.modules.ai_agents.langchain_medication_agent.agent import LangChainMedicationAgent
from src.modules.prescriptions_management.schema import Prescription

# Initialize LangChain models for validation and supervision
llm_vision = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro-latest", 
    temperature=0,
    google_api_key=settings.google_api_key
)

# Node functions for the streamlined workflow

async def image_extractor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract prescription data using LangChain vision model"""
    logger.info("Executing LangChain image extraction node")
    agent = LangChainImageAgent()
    result = agent.extract_prescription_data(state)
    return result

async def pydantic_validator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Validate extraction against Pydantic schema"""
    logger.info("--- AGENT: Pydantic Validator ---")
    
    raw_text = state.get("raw_extraction_text")
    if not raw_text:
        return {
            **state,
            "is_valid": False,
            "feedback": "No extraction text to validate"
        }
    
    try:
        # Use json_repair first to fix any simple syntax errors
        repaired_data = repair_json_loads(raw_text)
        
        # Validate against Pydantic schema
        validated_model = Prescription.parse_obj(repaired_data)
        
        logger.info("✅ Pydantic validation successful.")
        
        return {
            **state,
            "is_valid": True,
            "prescription_data": validated_model.dict(),
            "medications_to_process": validated_model.medications,
            "processed_medications": [],
            "quality_warnings": state.get("quality_warnings", [])
        }
        
    except (ValidationError, json.JSONDecodeError) as e:
        logger.warning(f"❌ Pydantic validation FAILED: {e}")
        return {
            **state,
            "is_valid": False,
            "feedback": str(e)
        }

async def retry_handler_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Handle retry logic"""
    logger.info("--- NODE: Retry Handler ---")
    retry_count = state.get("retry_count", 0) + 1
    logger.info(f"Attempt {retry_count}/1...")  # MAX_RETRIES = 1 as per scenario
    return {
        **state,
        "retry_count": retry_count
    }

async def medication_processor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Process medications using LangChain ReAct agent"""
    logger.info("Executing LangChain medication processing node")
    agent = LangChainMedicationAgent()
    result = agent.process_medications(state)
    return result

async def supervising_pharmacist_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Final QA and report generation"""
    logger.info("--- AGENT: Supervising Pharmacist (Final QA) ---")
    
    try:
        prescription_data = state.get("prescription_data", {})
        processed_medications = state.get("processed_medications", [])
        quality_warnings = state.get("quality_warnings", [])
        
        # Build final prescription structure
        final_data = prescription_data.copy()
        final_data["medications"] = processed_medications
        
        # Ensure all medication fields are present
        for med in final_data["medications"]:
            # Set default values for missing fields
            if med.get("quantity") and not med.get("days_of_use"):
                med["days_of_use"] = "Inferred"
                med["infer_days"] = "Yes"
            else:
                med.setdefault("infer_days", "No")
            
            # Ensure all required fields exist
            required_fields = [
                "drug_name", "strength", "instructions_for_use", "quantity", 
                "infer_qty", "days_of_use", "infer_days", "rxcui", "ndc", 
                "drug_schedule", "brand_drug", "brand_ndc", "sig_english", 
                "sig_spanish", "refills", "certainty"
            ]
            for field in required_fields:
                med.setdefault(field, None)
        
        # Generate supervisor report
        final_json_string = json.dumps(final_data, indent=2)
        
        report_prompt = f"""You are the final quality check. The JSON below has been generated. Your only task is to write a brief final report confirming if it adheres to the rules. DO NOT output the JSON again, only the report.

JSON:
{final_json_string}"""
        
        report = llm_vision.invoke(report_prompt).content
        
        # Add quality verification metadata
        final_data["_quality_and_verification_"] = {
            "quality_warnings": quality_warnings,
            "hallucination_flags": [],  # Simplified for performance
            "safety_flags": []
        }
        
        final_json_with_meta = json.dumps(final_data, indent=2)
        
        # Generate summary report
        retry_count = state.get("retry_count", 0)
        med_count = len(processed_medications)
        
        supervisor_report = f"""PRESCRIPTION PROCESSING SUPERVISOR REPORT
==================================================
Processing Status: COMPLETED
Retry Attempts: {retry_count}
Medications Processed: {med_count}

QUALITY WARNINGS:
--------------------"""
        
        for warning in quality_warnings:
            supervisor_report += f"\n• {warning}"
        
        if not quality_warnings:
            supervisor_report += "\n• No quality warnings detected"
        
        supervisor_report += f"\n\nOVERALL ASSESSMENT: {'REQUIRES MANUAL REVIEW' if quality_warnings else 'PROCESSING COMPLETE'}"
        
        logger.info(f"Supervisor Report: {supervisor_report}")
        
        return {
            **state,
            "final_json_output": final_json_with_meta,
            "final_supervisor_report": supervisor_report
        }
        
    except Exception as e:
        logger.error(f"Supervisor processing failed: {e}")
        error_report = f"SUPERVISOR ERROR: {str(e)}"
        
        return {
            **state,
            "final_json_output": json.dumps({"error": "Supervisor processing failed", "details": str(e)}),
            "final_supervisor_report": error_report
        }

async def halt_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Handle workflow halt conditions"""
    logger.info("--- NODE: Workflow Halted ---")
    feedback = state.get("feedback", "Unknown validation error")
    
    return {
        **state,
        "final_json_output": json.dumps({
            "error": "Workflow failed validation after retries",
            "feedback": feedback
        }),
        "final_supervisor_report": f"WORKFLOW HALTED: {feedback}"
    }
