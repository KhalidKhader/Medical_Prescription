"""
Prescription Workflow Orchestrator
Main workflow orchestration using LangGraph for prescription processing
"""

from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from src.core.settings.logging import logger


# Simple typed dict for workflow state
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

from .streamlined_orchestrator import StreamlinedPrescriptionOrchestrator


class PrescriptionOrchestrator:
    """Main orchestrator for prescription processing workflow"""
    
    def __init__(self):
        """Initialize the workflow orchestrator"""
        # Use the streamlined orchestrator with all agents
        self._streamlined = StreamlinedPrescriptionOrchestrator()
        logger.info("Prescription workflow orchestrator initialized with streamlined agent pipeline")
    
    def _build_workflow(self) -> StateGraph:
        """Legacy method - now delegated to streamlined orchestrator"""
        return self._streamlined.workflow
    
    async def ainvoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow asynchronously - delegated to streamlined orchestrator"""
        return await self._streamlined.process_prescription(initial_state)
    
    def invoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow synchronously - delegated to streamlined orchestrator"""
        import asyncio
        return asyncio.run(self.ainvoke(initial_state))

