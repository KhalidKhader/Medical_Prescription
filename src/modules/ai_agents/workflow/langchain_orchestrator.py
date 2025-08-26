"""
Streamlined LangChain-based Prescription Processing Orchestrator
Implements the exact scenario workflow with optimized performance
"""

from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from src.core.settings.logging import logger

# Simplified workflow state matching scenario requirements
class WorkflowState(TypedDict, total=False):
    image_base64: str
    retry_count: int
    feedback: str
    raw_extraction_text: str
    is_valid: bool
    prescription_data: Dict[str, Any]
    medications_to_process: list
    processed_medications: list
    quality_warnings: list
    hallucination_flags: list
    safety_flags: list
    final_json_output: str
    final_supervisor_report: str
    supervisor_rules: str

# Import the streamlined nodes
from .langchain_nodes import (
    image_extractor_node,
    pydantic_validator_node,
    retry_handler_node,
    medication_processor_node,
    supervising_pharmacist_node,
    halt_node
)

class StreamlinedPrescriptionOrchestrator:
    """Streamlined orchestrator matching scenario requirements exactly"""
    
    def __init__(self):
        self.workflow = self._build_workflow()
        logger.info("Streamlined prescription workflow orchestrator initialized")
    
    def _build_workflow(self) -> StateGraph:
        """Build the streamlined workflow graph"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes - simplified to match scenario exactly
        workflow.add_node("extractor", image_extractor_node)
        workflow.add_node("validator", pydantic_validator_node)
        workflow.add_node("retry_handler", retry_handler_node)
        workflow.add_node("medication_processor", medication_processor_node)
        workflow.add_node("supervisor", supervising_pharmacist_node)
        workflow.add_node("halt_node", halt_node)
        
        # Set entry point
        workflow.set_entry_point("extractor")
        
        # Add edges - simplified workflow
        workflow.add_edge("extractor", "validator")
        
        # Conditional routing from validator
        workflow.add_conditional_edges(
            "validator",
            self._should_retry,
            {
                "retry": "retry_handler",
                "proceed": "medication_processor",
                "halt": "halt_node"
            }
        )
        
        # Retry loop
        workflow.add_edge("retry_handler", "extractor")
        
        # Main processing pipeline
        workflow.add_edge("medication_processor", "supervisor")
        
        # End states
        workflow.add_edge("supervisor", END)
        workflow.add_edge("halt_node", END)
        
        return workflow.compile()
    
    def _should_retry(self, state: Dict[str, Any]) -> str:
        """Determine if workflow should retry, proceed, or halt"""
        is_valid = state.get("is_valid", False)
        retry_count = state.get("retry_count", 0)
        max_retries = 1  # As per scenario requirements
        
        if is_valid:
            logger.info("Validation successful - proceeding to processing")
            return "proceed"
        elif retry_count < max_retries:
            logger.info(f"Validation failed - retrying (attempt {retry_count + 1}/{max_retries})")
            return "retry"
        else:
            logger.warning("Max retries reached - halting workflow")
            return "halt"
    
    async def ainvoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow asynchronously"""
        try:
            logger.info("Starting streamlined prescription processing workflow")
            
            # Add supervisor rules to state
            if "supervisor_rules" not in initial_state:
                initial_state["supervisor_rules"] = self._get_supervisor_rules()
            
            # Initialize counters
            initial_state.setdefault("retry_count", 0)
            initial_state.setdefault("quality_warnings", [])
            initial_state.setdefault("hallucination_flags", [])
            initial_state.setdefault("safety_flags", [])
            
            final_state = await self.workflow.ainvoke(initial_state)
            
            logger.info("Streamlined prescription processing workflow completed")
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                **initial_state,
                "final_json_output": f'{{"error": "Workflow execution failed", "details": "{str(e)}"}}',
                "final_supervisor_report": f"WORKFLOW ERROR: {str(e)}"
            }
    
    def invoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow synchronously"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.ainvoke(initial_state))
        except RuntimeError:
            # If no event loop is running, create a new one
            return asyncio.run(self.ainvoke(initial_state))
    
    def _get_supervisor_rules(self) -> str:
        """Get the supervisor rules (exact user prompt)"""
        return """
You are a clinical pharmacist in the United States with vast experience interpreting prescriptions.
You will be given an image of a handwritten or printed medical prescription.
Your task is to analyze the prescription carefully and extract the following information with maximum accuracy.

Follow these rules:
1. Only use information that is present in the prescription image — do not guess or infer any details about the patient, prescriber or drugs prescribed unless otherwise instructed.
2. For each element retutned, indicate your percentage of certainty (in the certainty field of the json).
3. Preserve the exact spelling, abbreviations, and capitalization from the prescription.
4. For numeric values, use integers or decimals exactly as written.
5. For units (mg, ml, tablets, etc.), include them exactly as shown.
6. You may use RxNorm to add additional elements not present in the prescription regarding the medications.   You will add the RxCUI (rxcui in json), DEA Controlled Drug Schedule (drug_schedule) and the original Brand Reference Drug (Brand_Drug in json).  If you can find the information, add an active NDC Number for both the medication prescribed (ndc in json) and the NDC for the original Brand reference product (brand_ndc).
7. You will also write a clear instruction for the patient on how to take the following medication based on the doctor's abbreviated instructions for use.   Your instructions should include a verb, quantity, route and frequency.  Please out put this instruction in the json in both english (sig_english) and spanish (sig_spanish).
8. If no quantity is written for a drug, then you may calculate or infer the quantity prescribed from the instructions assuming you will dispense a 30 days supply.  If you infer the quantity, then set the json value for infer_qty to Yes, otherwise set to No.
9. If a quantity is written but no days of use is clearly expressed, infer the days of use by utilizing the prescriber's instructions.  If you infered the days of use, then set the infer_days value of the json to Yes; otherwise set to No.
10. Look for the number of Refills written.  This may be by medication or written once for all medications.  Return this value as part of the json (refills).
11. Do not include any text outside the prescribed sections.

Return your answer **only** as valid JSON with the following structure:

{
  "prescriber": {
    "full_name": "string or null",
    "state_license_number": "string or null",
"npi_number": "string or null",
"dea_number": "string or null",
    "address": "string or null",
    "contact_number": "string or null",
"certainty": "numeric or null"
  },
  "patient": {
    "full_name": "string or null",
    "date_of_birth": "string or null",
"age": "string or null",
"facility_name": "string or null",
    "address": "string or null",
"certainty": "numeric or null"
  },
  "date_prescription_written":"date or null",
  "medications": [
    {
      "drug_name": "string or null",
      "strength": "string or null",
      "instructions_for_use": "string or null",
      "quantity": "string or null",
 "infer_qty": "string or null",
      "days_of_use": "string or null",
 "infer_days": "string or null",
 "rxcui": "string or null",
 "ndc": "string or null",
 "drug_schedule": "string or null",
 "brand_drug": "string or null",
 "brand_ndc": "string or null",
 "sig_english": "string or null",
 "sig_spanish": "string or null",
 "refills": "string or null",
 "certainty": "numeric or null"
    }
  ]
}
"""

