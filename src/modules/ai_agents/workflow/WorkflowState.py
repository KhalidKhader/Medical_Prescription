from typing import Dict, Any, TypedDict


class WorkflowState(TypedDict, total=False):
    """Streamlined workflow state"""
    image_base64: str
    retry_count: int
    
    # Extraction results
    raw_extraction_text: str
    prescription_data: Dict[str, Any]
    is_valid: bool
    
    # Individual agent data
    patient_data: Dict[str, Any]
    prescriber_data: Dict[str, Any]
    medications_to_process: list
    processed_medications: list
    
    # Validation results
    patient_validation_results: Dict[str, Any]
    prescriber_validation_results: Dict[str, Any]
    drugs_validation_results: Dict[str, Any]
    
    # Final output
    final_json_output: str
    quality_warnings: list