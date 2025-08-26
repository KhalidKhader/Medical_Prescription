"""
Streamlined Prescription Processing Orchestrator
Uses all agents in a single coordinated workflow with unified LangFuse tracing
"""

from typing import Dict, Any, TypedDict
from src.core.settings.logging import logger

# Optional LangFuse import
try:
    from langfuse import observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    # Create a no-op decorator if LangFuse is not available
    def observe(name=None, **kwargs):
        def decorator(func):
            return func
        return decorator
    LANGFUSE_AVAILABLE = False
    logger.warning("LangFuse not available, using no-op decorator")

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
        logger.info("📝 Memory system initialized for workflow persistence")
        
        logger.info("✅ Streamlined Prescription Orchestrator initialized with core agents per scenario.mdc")
    
    @traceable(name="thinking_step")
    async def _thinking_step(self, agent_func, state: Dict[str, Any], step_name: str) -> Dict[str, Any]:
        """Enhanced thinking step with detailed logging and tracing"""
        logger.info(f"🧠 THINKING STEP: {step_name}")
        logger.info(f"📊 Input state keys: {list(state.keys())}")
        
        start_time = time.time()
        
        try:
            # Execute the agent function with enhanced monitoring
            result = await agent_func(state)
            
            processing_time = time.time() - start_time
            logger.info(f"⏱️ {step_name} completed in {processing_time:.2f}s")
            logger.info(f"📈 Output state keys: {list(result.keys())}")
            
            # Log any new warnings or errors
            if result.get("quality_warnings"):
                new_warnings = len(result.get("quality_warnings", [])) - len(state.get("quality_warnings", []))
                if new_warnings > 0:
                    logger.info(f"⚠️ {step_name} added {new_warnings} quality warnings")
            
            return result
            
        except Exception as e:
            logger.error(f"💥 {step_name} failed: {str(e)}")
            # Add error to state and continue workflow
            warnings = state.get("quality_warnings", [])
            warnings.append(f"{step_name} failed: {str(e)}")
            state["quality_warnings"] = warnings
            return state
    
    @observe(name="prescription_processing_complete_workflow", as_type="generation", capture_input=True, capture_output=True)
    async def process_prescription(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process prescription through complete workflow with single LangFuse trace
        
        Args:
            initial_state: Initial state with image_base64
            
        Returns:
            Final state with complete prescription data
        """
        logger.info("🚀 Starting streamlined prescription processing workflow")
        
        state = WorkflowState(**initial_state)
        state.setdefault("quality_warnings", [])
        state.setdefault("retry_count", 0)
        
        try:
            # Step 1: Image Extraction (Primary)
            logger.info("📷 Step 1: Image Extraction")
            state = await self.image_extractor.process(state)
            
            if not state.get("is_valid"):
                logger.warning("Image extraction failed, stopping workflow")
                return self._create_final_output(state, "Image extraction failed")
            
            # Step 2: Patient Info Processing
            logger.info("👤 Step 2: Patient Information Processing")
            if state.get("patient_data"):
                state = await self.patient_agent.process(state)
                state = await self.patient_validator.process(state)
            else:
                logger.warning("No patient data found in extraction")
            
            # Step 3: Prescriber Info Processing
            logger.info("👨‍⚕️ Step 3: Prescriber Information Processing")
            if state.get("prescriber_data"):
                state = await self.prescriber_agent.process(state)
                state = await self.prescriber_validator.process(state)
            else:
                logger.warning("No prescriber data found in extraction")
            
            # Step 4: Medications Processing (Core)
            logger.info("💊 Step 4: Medications Processing")
            if state.get("medications_to_process"):
                state = await self.drugs_agent.process(state)
                state = await self.drugs_validator.process(state)
            else:
                logger.warning("No medications found to process")
            
            # Step 5: Clinical Safety Review (NEW)
            logger.info("🛡️ Step 5: Clinical Safety Review")
            try:
                safety_result = await self.clinical_safety_agent.review_prescription_safety(
                    state.get("prescription_data", {})
                )
                state["safety_assessment"] = safety_result
                logger.info(f"Clinical safety review completed: {safety_result.get('safety_status', 'unknown')}")
            except Exception as e:
                logger.error(f"Clinical safety review failed: {e}")
                state.setdefault("quality_warnings", []).append(f"Safety review failed: {e}")
            
            # Step 6: Quality & Hallucination Detection  
            logger.info("🔍 Step 6: Quality & Hallucination Detection")
            state = await self.hallucination_detector.process(state)
            
            # Step 7: Spanish Translation
            logger.info("🌐 Step 7: Spanish Translation")
            state = await self.spanish_translator.process(state)
            
            # Step 8: Final Assembly with Enhanced Quality
            logger.info("📋 Step 8: Final Assembly")
            final_state = self._create_enhanced_final_output(state, "completed")
            
            logger.info("✅ Enhanced prescription processing completed successfully")
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow processing failed: {e}")
            return self._create_final_output(state, f"failed: {str(e)}")
    
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
