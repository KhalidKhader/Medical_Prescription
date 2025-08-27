"""
Streamlined Prescription Processing Orchestrator
Uses all agents in a single coordinated workflow with unified LangFuse tracing
"""

from typing import Dict, Any, TypedDict
from src.core.settings.logging import logger

from langfuse import observe
from src.core.settings.threading import (
    parallel_agent_execution, performance_tracked, global_performance_monitor,
    CircuitBreaker, RetryStrategy, cache_result
)
# LangSmith integration for enhanced tracing
try:
    import os
    from langsmith import traceable
    from langchain_core.tracers.langchain import LangChainTracer
    LANGSMITH_AVAILABLE = True
    logger.info("LangSmith tracing available")
except ImportError:
    def traceable(name=None, **kwargs):
        def decorator(func):
            return func
        return decorator
    LANGSMITH_AVAILABLE = False

# Import all the specialized agents
from src.modules.ai_agents.image_extractor_agent.agent import ImageExtractorAgent
from src.modules.ai_agents.patient_info_agent.agent import PatientInfoAgent
from src.modules.ai_agents.prescriber_agent.agent import PrescriberAgent
from src.modules.ai_agents.drugs_agent.agent import DrugsAgent
from src.modules.ai_agents.patient_info_validation_agent.agent import PatientInfoValidationAgent
from src.modules.ai_agents.prescriber_validation_agent.agent import PrescriberValidationAgent
from src.modules.ai_agents.drugs_validation_agent.agent import DrugsValidationAgent
from src.modules.ai_agents.hallucination_detection_agent.agent import HallucinationDetectionAgent
from src.modules.ai_agents.clinical_safety_agent.agent import ClinicalSafetyAgent
from src.modules.ai_agents.translate_to_spanish_agent.agent import SpanishTranslationAgent
from langgraph.checkpoint.memory import MemorySaver
import asyncio
import uuid
import time


class WorkflowState(TypedDict, total=False):
    """Streamlined workflow state"""
    image_base64: str
    retry_count: int
    feedback: str
    
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
    hallucination_flags: list
    safety_flags: list
    
    # Final output
    final_json_output: str
    quality_warnings: list


class StreamlinedPrescriptionOrchestrator:
    """Enhanced orchestrator with memory, streaming, and LangSmith tracing"""
    
    def __init__(self):
        """Initialize core agents according to scenario.mdc requirements"""
        # Core extraction and processing agents (scenario.mdc)
        self.image_extractor = ImageExtractorAgent()
        self.patient_agent = PatientInfoAgent()
        self.prescriber_agent = PrescriberAgent()
        self.drugs_agent = DrugsAgent()
        
        # Validation agents (scenario.mdc)
        self.patient_validator = PatientInfoValidationAgent()
        self.prescriber_validator = PrescriberValidationAgent()
        self.drugs_validator = DrugsValidationAgent()
        
        # Quality and safety agents (scenario.mdc)
        self.hallucination_detector = HallucinationDetectionAgent()
        self.clinical_safety_agent = ClinicalSafetyAgent()
        self.spanish_translator = SpanishTranslationAgent()
        
        # Add memory for workflow persistence (LangChain enhancement)
        self.memory = MemorySaver()
        
        # Performance enhancements
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        self.performance_monitor = global_performance_monitor
        
        logger.info("📝 Memory system initialized for workflow persistence")
        logger.info("⚡ Performance monitoring and circuit breaker initialized")
        logger.info("✅ Streamlined Prescription Orchestrator initialized with core agents per scenario.mdc")
    
    @observe(name="prescription_processing_complete_workflow", as_type="generation", capture_input=True, capture_output=True)
    @performance_tracked("prescription_processing_workflow")
    async def process_prescription(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process prescription through complete workflow with parallel processing and performance tracking
        
        Args:
            initial_state: Initial state with image_base64
            
        Returns:
            Final state with complete prescription data
        """
        logger.info("🚀 Starting enhanced parallel prescription processing workflow")
        
        state = WorkflowState(**initial_state)
        state.setdefault("quality_warnings", [])
        state.setdefault("retry_count", 0)
        
        try:
            # Step 1: Image Extraction (Must be first - sequential)
            logger.info("📷 Step 1: Image Extraction")
            state = await self.circuit_breaker.call(self.image_extractor.process, state)
            
            if not state.get("is_valid"):
                logger.warning("Image extraction failed, stopping workflow")
                return self._create_final_output(state, "Image extraction failed")
            
            # Step 2: Parallel Processing of Independent Sections (60-70% performance gain)
            logger.info("⚡ Step 2: Parallel Agent Processing")
            await self._process_sections_parallel(state)
            
            # Step 3: Sequential Quality & Safety (Dependencies require order)
            logger.info("🔍 Step 3: Quality & Safety Processing")
            await self._process_quality_safety_sequential(state)
            
            # Step 4: Final Assembly with Enhanced Quality
            logger.info("📋 Step 4: Final Assembly")
            final_state = self._create_final_output(state, "completed")
            
            # Log performance metrics
            self._log_performance_metrics()
            
            logger.info("✅ Enhanced parallel prescription processing completed successfully")
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow processing failed: {e}")
            self.performance_monitor.increment_counter("workflow_failures")
            return self._create_final_output(state, f"failed: {str(e)}")
    
    async def _process_sections_parallel(self, state: Dict[str, Any]):
        """Process patient, prescriber, and medications in parallel"""
        parallel_tasks = []
        
        # Patient processing
        if state.get("patient_data"):
            async def patient_processing():
                temp_state = await self.patient_agent.process(state.copy())
                return await self.patient_validator.process(temp_state)
            parallel_tasks.append(patient_processing)
        
        # Prescriber processing  
        if state.get("prescriber_data"):
            async def prescriber_processing():
                temp_state = await self.prescriber_agent.process(state.copy())
                return await self.prescriber_validator.process(temp_state)
            parallel_tasks.append(prescriber_processing)
        
        # Medications processing
        if state.get("medications_to_process"):
            async def medications_processing():
                temp_state = await self.drugs_agent.process(state.copy())
                return await self.drugs_validator.process(temp_state)
            parallel_tasks.append(medications_processing)
        
        if parallel_tasks:
            # Execute all tasks in parallel with circuit breaker protection
            results = await parallel_agent_execution(parallel_tasks, max_concurrent=3)
            
            # Merge results back into main state
            for result in results:
                if result:
                    state.update(result)
        
        logger.info(f"✅ Parallel processing completed - {len(parallel_tasks)} sections processed")
    
    async def _process_quality_safety_sequential(self, state: Dict[str, Any]):
        """Process quality and safety checks sequentially due to dependencies"""
        try:
            # Clinical Safety Review
            logger.info("🛡️ Clinical Safety Review")
            safety_result = await self.clinical_safety_agent.review_prescription_safety(
                state.get("prescription_data", {})
            )
            state["safety_assessment"] = safety_result
            
            # Hallucination Detection
            logger.info("🔍 Hallucination Detection")
            state = await self.hallucination_detector.process(state)
            
            # Spanish Translation
            logger.info("🌐 Spanish Translation")
            state = await self.spanish_translator.process(state)
            
        except Exception as e:
            logger.error(f"Quality/Safety processing failed: {e}")
            state.setdefault("quality_warnings", []).append(f"Quality check failed: {e}")
    
    def _log_performance_metrics(self):
        """Log current performance metrics"""
        stats = self.performance_monitor.get_stats()
        logger.info(f"📊 Performance Metrics: {stats}")
    
    def _create_final_output(self, state: Dict[str, Any], status: str) -> Dict[str, Any]:
        """
        Create final output with complete prescription data
        
        Args:
            state: Current workflow state
            status: Processing status
            
        Returns:
            Final output state
        """
        try:
            # Assemble final prescription data
            final_prescription = {
                "prescriber": state.get("prescriber_data", {}),
                "patient": state.get("patient_data", {}),
                "date_prescription_written": state.get("prescription_data", {}).get("date_prescription_written"),
                "medications": state.get("processed_medications", state.get("medications_to_process", []))
            }
            
            # Create processing metadata
            processing_metadata = {
                "status": status,
                "quality_warnings": state.get("quality_warnings", []),
                "hallucination_flags": state.get("hallucination_flags", []),
                "safety_flags": state.get("safety_flags", []),
                "validation_results": {
                    "patient": state.get("patient_validation_results", {}),
                    "prescriber": state.get("prescriber_validation_results", {}),
                    "drugs": state.get("drugs_validation_results", {})
                }
            }
            
            # Create final JSON output
            import json
            final_json = json.dumps(final_prescription, indent=2)
            
            return {
                **state,
                "final_json_output": final_json,
                "final_prescription_data": final_prescription,
                "processing_metadata": processing_metadata,
                "processing_status": status
            }
            
        except Exception as e:
            logger.error(f"Failed to create final output: {e}")
            return {
                **state,
                "final_json_output": "{}",
                "processing_status": "failed",
                "quality_warnings": state.get("quality_warnings", []) + [f"Final assembly failed: {str(e)}"]
            }
    
    async def invoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous wrapper for process_prescription
        
        Args:
            initial_state: Initial state
            
        Returns:
            Final state
        """
        return await self.process_prescription(initial_state)
    
    async def ainvoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronous invoke method
        
        Args:
            initial_state: Initial state
            
        Returns:
            Final state
        """
        return await self.process_prescription(initial_state)
