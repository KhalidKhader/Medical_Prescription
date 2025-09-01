"""
Streamlined Prescription Orchestrator
Combined workflow orchestration with parallel processing and performance monitoring
"""

import asyncio
from typing import Dict, Any, TypedDict, Optional
from src.core.settings.logging import logger
from langfuse import observe
from langfuse import Langfuse
from src.core.settings.config import settings
from src.core.settings.threading import (
    parallel_agent_execution, performance_tracked, global_performance_monitor,
    CircuitBreaker
)
from src.modules.ai_agents.image_extractor_agent.agent import ImageExtractorAgent
from src.modules.ai_agents.patient_info_agent.agent import PatientInfoAgent
from src.modules.ai_agents.prescriber_agent.agent import PrescriberAgent
from src.modules.ai_agents.drugs_agent.agent import DrugsAgent
from src.modules.ai_agents.drugs_validation_agent.agent import DrugsValidationAgent
from src.modules.ai_agents.clinical_safety_agent.agent import ClinicalSafetyAgent
from langgraph.checkpoint.memory import MemorySaver
from .WorkflowState import WorkflowState




class PrescriptionOrchestrator:
    """Main orchestrator for prescription processing workflow with parallel processing"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the workflow orchestrator with optional configuration"""
        try:
            logger.info("Building prescription processing workflow")
            
            # Core extraction and processing agents
            self.image_extractor = ImageExtractorAgent()
            self.patient_agent = PatientInfoAgent()
            self.prescriber_agent = PrescriberAgent()
            self.drugs_agent = DrugsAgent()
            
            # Essential validation agents
            self.drugs_validator = DrugsValidationAgent()
            
            # Quality and safety agents
            self.clinical_safety_agent = ClinicalSafetyAgent()
            
            # Memory for workflow persistence
            self.memory = MemorySaver()
            
            # Performance enhancements
            self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=120)
            self.performance_monitor = global_performance_monitor

            # Initialize Langfuse for single trace consolidation
            self.langfuse = Langfuse(
                secret_key=settings.langfuse_secret_key,
                public_key=settings.langfuse_public_key,
                host=settings.langfuse_host
            )

            # Apply custom configuration if provided
            if config:
                logger.info(f"Applying custom workflow configuration: {config}")
                self._apply_configuration(config)
            
            logger.info("✅ Prescription workflow orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize prescription workflow: {e}")
            raise
    
    def _apply_configuration(self, config: Dict[str, Any]):
        """Apply custom configuration to the orchestrator"""
        # Apply max retries if specified
        max_retries = config.get("max_retries")
        if max_retries is not None:
            if 0 <= max_retries <= 10:
                self.circuit_breaker.failure_threshold = max_retries
                logger.info(f"Applied max retries configuration: {max_retries}")
            else:
                logger.warning(f"Invalid max_retries value: {max_retries}, using default")
    
    @observe(name="prescription_processing_workflow", as_type="generation", capture_input=True, capture_output=True)
    async def process_prescription(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Process prescription through complete workflow"""
        logger.info("🚀 Starting prescription processing workflow")
        
        state = WorkflowState(**initial_state)
        state.setdefault("quality_warnings", [])
        state.setdefault("retry_count", 0)
        
        try:
            # Log workflow start event
            self.langfuse.create_event(
                name="prescription_processing_started",
                input={
                    "image_present": "image_base64" in initial_state,
                    "initial_state_keys": list(initial_state.keys()),
                    "timestamp": initial_state.get("timestamp", "unknown")
                }
            )

            # Step 1: Image Extraction
            logger.info("📷 Step 1: Image Extraction")
            state = await self.circuit_breaker.call(self.image_extractor.process, state)

            self.langfuse.create_event(
                name="image_extraction_completed",
                input={
                    "is_valid": state.get("is_valid"),
                    "extraction_success": state.get("is_valid", False),
                    "raw_text_length": len(state.get("raw_extraction_text", ""))
                }
            )

            if not state.get("is_valid"):
                logger.warning("Image extraction failed, stopping workflow")
                self.langfuse.create_event(
                    name="workflow_stopped_early",
                    input={"reason": "image_extraction_failed"}
                )
                return self._create_final_output(state, "Image extraction failed")

            # Step 2: Parallel Processing
            logger.info("⚡ Step 2: Parallel Agent Processing")
            await self._process_sections_parallel(state)

            self.langfuse.create_event(
                name="parallel_processing_completed",
                input={
                    "medications_count": len(state.get("processed_medications", [])),
                    "patient_data_extracted": "patient_data" in state,
                    "prescriber_data_extracted": "prescriber_data" in state
                }
            )

            # Step 3: Quality & Safety
            logger.info("🔍 Step 3: Quality & Safety Processing")
            await self._process_quality_safety_sequential(state)
            
            # Step 4: Final Assembly
            logger.info("📋 Step 4: Final Assembly")
            final_state = self._create_final_output(state, "completed")

            self.langfuse.create_event(
                name="final_assembly_completed",
                input={
                    "final_json_size": len(final_state.get("final_json_output", "")),
                    "quality_warnings_count": len(final_state.get("quality_warnings", [])),
                    "processing_status": "completed"
                }
            )

            # Log performance metrics
            self._log_performance_metrics()

            logger.info("✅ Prescription processing completed successfully")

            # Log final completion event
            stats = self.performance_monitor.get_stats()
            workflow_stats = stats.get("timings", {}).get("prescription_processing_workflow", {})

            self.langfuse.create_event(
                name="prescription_processing_completed",
                input={
                    "total_medications": len(final_state.get("processed_medications", [])),
                    "processing_time_avg": workflow_stats.get("avg", 0),
                    "processing_time_count": workflow_stats.get("count", 0),
                    "status": "success"
                }
            )

            return final_state

        except Exception as e:
            logger.error(f"Workflow processing failed: {e}")
            self.performance_monitor.increment_counter("workflow_failures")

            # Log failure event
            self.langfuse.create_event(
                name="prescription_processing_failed",
                input={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "processing_stage": "unknown"
                }
            )

            return self._create_final_output(state, f"failed: {str(e)}")
    
    async def _process_sections_parallel(self, state: Dict[str, Any]):
        """Process patient, prescriber, and medications in parallel"""
        parallel_tasks = []
        
        # Patient processing
        if state.get("patient_data"):
            async def patient_processing():
                return await self.patient_agent.process(state.copy())
            parallel_tasks.append(patient_processing)
        
        # Prescriber processing
        if state.get("prescriber_data"):
            async def prescriber_processing():
                return await self.prescriber_agent.process(state.copy())
            parallel_tasks.append(prescriber_processing)
        
        # Medications processing
        if state.get("medications_to_process"):
            async def medications_processing():
                temp_state = await self.drugs_agent.process(state.copy())
                return await self.drugs_validator.process(temp_state)
            parallel_tasks.append(medications_processing)
        
        if parallel_tasks:
            # Execute all tasks in parallel
            results = await parallel_agent_execution(parallel_tasks, max_concurrent=3)

            # Track parallel execution results
            successful_tasks = sum(1 for r in results if r is not None)
            failed_tasks = len(parallel_tasks) - successful_tasks

            # Log parallel processing details
            self.langfuse.create_event(
                name="parallel_agent_execution_details",
                input={
                    "total_tasks": len(parallel_tasks),
                    "successful_tasks": successful_tasks,
                    "failed_tasks": failed_tasks,
                    "agent_types": ["patient", "prescriber", "drugs"]
                }
            )

            # Merge results back into main state
            for result in results:
                if result:
                    state.update(result)

        logger.info(f"✅ Parallel processing completed - {len(parallel_tasks)} sections processed")
    
    async def _process_quality_safety_sequential(self, state: Dict[str, Any]):
        """Process essential quality and safety checks"""
        try:
            logger.info("🛡️ Clinical Safety Check")
            safety_task = asyncio.create_task(
                self.clinical_safety_agent.review_prescription_safety(
                    state.get("prescription_data", {})
                )
            )
            try:
                safety_result = await asyncio.wait_for(safety_task, timeout=120)
                state["safety_assessment"] = safety_result

                # Log successful safety check
                self.langfuse.create_event(
                    name="clinical_safety_check_completed",
                    input={
                        "safety_review_performed": True,
                        "safety_warnings": len(state.get("quality_warnings", [])),
                        "medications_reviewed": len(state.get("processed_medications", [])),
                        "assessment_status": safety_result.get("status", "completed")
                    }
                )

                logger.info("✅ Safety check completed")
            except asyncio.TimeoutError:
                logger.warning("⚠️ Safety check timed out - skipping")
                state["safety_assessment"] = {"status": "skipped_for_performance"}
                safety_task.cancel()

                # Log timeout event
                self.langfuse.create_event(
                    name="clinical_safety_check_timeout",
                    input={
                        "timeout_seconds": 120,
                        "medications_count": len(state.get("processed_medications", [])),
                        "workflow_continued": True
                    }
                )

        except Exception as e:
            logger.error(f"Safety processing failed: {e}")
            state.setdefault("quality_warnings", []).append(f"Safety check failed: {e}")

            # Log safety check failure
            self.langfuse.create_event(
                name="clinical_safety_check_failed",
                input={
                    "error_message": str(e),
                    "error_type": type(e).__name__,
                    "workflow_continued": True
                }
            )
    
    def _log_performance_metrics(self):
        """Log current performance metrics"""
        stats = self.performance_monitor.get_stats()
        logger.info(f"📊 Performance Metrics: {stats}")
    
    def _create_final_output(self, state: Dict[str, Any], status: str) -> Dict[str, Any]:
        """Create final output with complete prescription data"""
        try:
            # Get safety assessment data
            safety_assessment = state.get("safety_assessment", {})

            # Assemble final prescription data
            final_prescription = {
                "prescriber": state.get("prescriber_data", {}),
                "patient": state.get("patient_data", {}),
                "date_prescription_written": state.get("prescription_data", {}).get("date_prescription_written"),
                "medications": state.get("processed_medications", state.get("medications_to_process", [])),
                "safety_assessment": {
                    "safety_status": safety_assessment.get("safety_status", "unknown"),
                    "safety_score": safety_assessment.get("safety_score", None),
                    "safety_flags": safety_assessment.get("safety_flags", []),
                    "recommendations": safety_assessment.get("recommendations", []),
                    "medication_safety_details": safety_assessment.get("medication_safety_details", []),
                    "review_summary": safety_assessment.get("review_summary", "")
                }
            }
            
            # Create processing metadata
            processing_metadata = {
                "status": status,
                "quality_warnings": state.get("quality_warnings", []),
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
    
    async def ainvoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow asynchronously"""
        return await self.process_prescription(initial_state)
    
    def invoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow synchronously"""
        return asyncio.run(self.ainvoke(initial_state))


# Factory function for building workflows
def build_prescription_workflow(config: Optional[Dict[str, Any]] = None) -> PrescriptionOrchestrator:
    """
    Build prescription processing workflow with optional configuration
    
    Args:
        config: Optional workflow configuration
        
    Returns:
        Configured prescription orchestrator
    """
    try:
        logger.info("Building prescription processing workflow")
        orchestrator = PrescriptionOrchestrator(config)
        logger.info("Prescription workflow built successfully")
        return orchestrator
        
    except Exception as e:
        logger.error(f"Failed to build prescription workflow: {e}")
        raise
