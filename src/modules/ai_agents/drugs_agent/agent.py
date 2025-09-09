"""
Drugs Agent - Medication processing with RxNorm mapping using Gemini 2.5 Pro
Processes medications and enriches them with RxNorm data
"""

from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.settings.config import settings
from src.core.settings.logging import logger
from src.core.settings.threading import parallel_agent_execution
from langfuse import observe
from src.modules.ai_agents.drugs_agent.tools import (
    get_rxnorm_drug_info,
    calculate_quantity_from_sig,
    infer_days_from_quantity,
    generate_sig_english,
)

# Import new instruction agents
from src.modules.ai_agents.instructions_of_use_agent.agent import InstructionsOfUseAgent
from src.modules.ai_agents.instructions_of_use_validation_agent.agent import InstructionsOfUseValidationAgent
from src.modules.ai_agents.drug_selector_agent.agent import SmartDrugSelectorAgent
from src.modules.ai_agents.parse_drug_components.agent import DrugComponentsAgent


class DrugsAgent:
    """Agent for processing medications with RxNorm integration using Gemini 2.5 Pro"""
    
    def __init__(self):
        """Initialize the drugs agent with Gemini 2.5 Pro"""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro", 
            temperature=0,
            google_api_key=settings.google_api_key
        )
        
        # Initialize instruction agents
        self.instructions_agent = InstructionsOfUseAgent()
        self.validation_agent = InstructionsOfUseValidationAgent()
        self.smart_selector = SmartDrugSelectorAgent()
        self.drug_parser = DrugComponentsAgent()
        
        logger.info("Drugs Agent initialized with Gemini 2.5 Pro and instruction agents")
    
    @observe(name="drugs_processing", as_type="generation", capture_input=True, capture_output=True)
    async def process_medications(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process medications with RxNorm mapping and enhancement
        
        Args:
            state: Workflow state containing medications to process
            
        Returns:
            Updated state with processed medications
        """
        logger.info("--- AGENT: Drugs Processor ---")
        
        medications_to_process = state.get("medications_to_process", [])
        if not medications_to_process:
            logger.warning("No medications found to process")
            return self._add_warning(state, "No medications found to process")
        
        processed_medications = []
        quality_warnings = state.get("quality_warnings", [])
        
        logger.info(f"🚀 Processing {len(medications_to_process)} medications in parallel")
        
        # Create parallel tasks for all medications
        medication_tasks = []
        for medication in medications_to_process:
            async def process_med_task(med=medication):
                try:
                    drug_name = med.get('drug_name', 'unknown')
                    logger.info(f"Processing: {drug_name}")
                    return await self.process_single_medication(med, state)
                except Exception as e:
                    error_msg = f"Failed to process {med.get('drug_name', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    quality_warnings.append(error_msg)
                    return med  # Return original on failure

            medication_tasks.append(process_med_task)
        
        # Process all medications in parallel (major performance gain)
        processed_medications = await parallel_agent_execution(medication_tasks, max_concurrent=5)
        logger.info(f"✅ Completed parallel processing of {len(processed_medications)} medications")
        
        return {
            **state,
            "processed_medications": processed_medications,
            "quality_warnings": quality_warnings
        }
    
    async def process_single_medication(self, medication: Dict[str, Any], state: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a single medication with full enhancement using safety context

        Args:
            medication: Medication data to process
            state: Workflow state containing safety assessment

        Returns:
            Enhanced medication data
        """
        drug_name = medication.get("drug_name")
        if not drug_name:
            return medication

        enhanced_med = medication.copy()

        # Parse drug components to get clean drug name for search
        parsed_components = await self.drug_parser.parse_drug_components(drug_name)
        clean_drug_name = parsed_components.get("drug_name", drug_name)
        
        # Validate that parsing didn't substitute the drug name
        if self._is_drug_substitution(drug_name, clean_drug_name):
            logger.warning(f"Drug substitution detected: '{drug_name}' -> '{clean_drug_name}', using original")
            clean_drug_name = drug_name
        
        # Update medication with parsed components
        enhanced_med.update({
            "drug_name": clean_drug_name,
            "strength": parsed_components.get("strength") or enhanced_med.get("strength"),
            "form": parsed_components.get("form") or enhanced_med.get("form"),
            "original_drug_string": drug_name  # Keep original for reference
        })

        # Extract safety assessment and context for better drug matching
        safety_assessment = state.get("safety_assessment", {}) if state else {}
        context = self._build_drug_context(enhanced_med, state)

        # Step 1: Get RxNorm information with clean drug name
        rxnorm_data = await get_rxnorm_drug_info(
            drug_name=clean_drug_name,
            strength=enhanced_med.get("strength"),
            instructions=enhanced_med.get("instructions_for_use")
        )
        enhanced_med.update(rxnorm_data)
        
        # Step 1.5: Smart drug validation and correction
        enhanced_med = await self.smart_selector.validate_and_correct_drug(enhanced_med)
        
        # Step 2: Generate structured instructions with RxNorm safety validation
        if enhanced_med.get("instructions_for_use"):
            try:
                logger.info(f"🏥 Generating structured instructions for {drug_name}")
                logger.info(f"📝 Raw instructions: '{enhanced_med['instructions_for_use']}'")
                
                instruction_result = await self.instructions_agent.generate_structured_instructions(
                    drug_name=drug_name,
                    strength=enhanced_med.get("strength", ""),
                    raw_instructions=enhanced_med["instructions_for_use"],
                    indication=enhanced_med.get("indication")
                )
                
                logger.info(f"✅ Instruction generation completed for {drug_name}")
                
                # Update medication with structured instruction data
                if instruction_result.get("structured_instructions"):
                    enhanced_med["structured_instructions"] = instruction_result["structured_instructions"]
                    logger.info(f"📋 Added structured instructions for {drug_name}")
                
                if instruction_result.get("sig_english"):
                    enhanced_med["sig_english"] = instruction_result["sig_english"]
                    logger.info(f"🇺🇸 Added English sig: {instruction_result['sig_english']}")
                
                if instruction_result.get("sig_spanish"):
                    enhanced_med["sig_spanish"] = instruction_result["sig_spanish"]
                    logger.info(f"🇪🇸 Added Spanish sig: {instruction_result['sig_spanish']}")
                
                # Add safety validation results
                if instruction_result.get("safety_validation"):
                    enhanced_med["instruction_safety"] = instruction_result["safety_validation"]
                    logger.info(f"🛡️ Added safety validation for {drug_name}")
                
            except Exception as e:
                logger.error(f"❌ Instruction generation failed for {drug_name}: {e}")
                # Fallback to simple sig generation
                if enhanced_med.get("instructions_for_use"):
                    enhanced_med["sig_english"] = generate_sig_english(enhanced_med["instructions_for_use"])
                    logger.info(f"🔄 Used fallback sig generation for {drug_name}")
        
        # Skip redundant validation here - handled by dedicated validation agent later
        
        # Step 4: Calculate quantity if missing (fallback method)
        if not enhanced_med.get("quantity") and enhanced_med.get("instructions_for_use"):
            calculated_qty, was_inferred = calculate_quantity_from_sig(enhanced_med["instructions_for_use"])
            enhanced_med["quantity"] = calculated_qty
            enhanced_med["infer_qty"] = "Yes" if was_inferred else "No"
        
        # Step 5: Infer days of use if needed
        if not enhanced_med.get("days_of_use") and enhanced_med.get("quantity") and enhanced_med.get("instructions_for_use"):
            inferred_days, was_inferred = infer_days_from_quantity(
                enhanced_med["quantity"], 
                enhanced_med["instructions_for_use"]
            )
            enhanced_med["days_of_use"] = inferred_days
            enhanced_med["infer_days"] = "Yes" if was_inferred else "No"
        
        # Data validation handled by dedicated validation agents - skip redundant step
        return enhanced_med
    
    # Translation is now handled by InstructionsOfUseAgent
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process method for compatibility with workflow
        
        Args:
            state: Workflow state
            
        Returns:
            Updated state
        """
        return await self.process_medications(state)
    
    def _add_warning(self, state: Dict[str, Any], warning: str) -> Dict[str, Any]:
        """Add warning to state"""
        warnings = state.get("quality_warnings", [])
        warnings.append(warning)
        return {
            **state,
            "quality_warnings": warnings
        }

    def _build_drug_context(self, medication: Dict[str, Any], state: Dict[str, Any] = None) -> Dict[str, Any]:
        """Build comprehensive context for drug matching"""
        context = {}

        # Extract brand information from medication
        if medication.get("brand_name"):
            context["brand_name"] = medication["brand_name"]

        # Extract generic name if different from drug_name
        if medication.get("generic_name"):
            context["generic_name"] = medication["generic_name"]
        elif medication.get("drug_name"):
            # Assume drug_name might be generic if no brand specified
            context["generic_name"] = medication["drug_name"]

        # Add patient information for context
        if state:
            patient_data = state.get("patient_data", {})
            if patient_data.get("age"):
                context["patient_age"] = patient_data["age"]
            if patient_data.get("weight"):
                context["patient_weight"] = patient_data["weight"]

            # Add prescriber specialty if available
            prescriber_data = state.get("prescriber_data", {})
            if prescriber_data.get("specialty"):
                context["prescriber_specialty"] = prescriber_data["specialty"]

        # Add indication for context
        if medication.get("indication"):
            context["indication"] = medication["indication"]

        return context

    def _is_drug_substitution(self, original: str, extracted: str) -> bool:
        """Check if extracted drug name is a substitution rather than extraction"""
        original_clean = original.lower().strip()
        extracted_clean = extracted.lower().strip()
        
        # If they're the same or extracted is contained in original, it's valid
        if extracted_clean == original_clean or extracted_clean in original_clean:
            return False
        
        # If original is contained in extracted, it's valid (e.g., "Lantus" -> "Lantus SoloStar")
        if original_clean in extracted_clean:
            return False
        
        # Check for common prefixes (first 3+ characters match)
        if len(original_clean) >= 3 and len(extracted_clean) >= 3:
            if original_clean[:3] == extracted_clean[:3]:
                return False
        
        # Otherwise, it's likely a substitution
        return True