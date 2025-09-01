"""
Spanish Translation Agent
Translates medication instructions to Spanish using Gemini 2.5 Pro
"""

from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.settings.config import settings
from src.core.settings.logging import logger
from langfuse import observe

from .prompts import get_spanish_translation_prompt


class SpanishTranslationAgent:
    """Agent for translating medication instructions to Spanish using Gemini 2.5 Pro"""
    
    def __init__(self):
        """Initialize the Spanish translation agent with Gemini 2.5 Pro"""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro", 
            temperature=0,
            google_api_key=settings.google_api_key
        )
        logger.info("Spanish Translation Agent initialized with Gemini 2.5 Pro")
    
    @observe(name="spanish_translation", as_type="generation", capture_input=True, capture_output=True)
    async def translate_medications(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate medication instructions to Spanish
        
        Args:
            state: Workflow state with processed medications
            
        Returns:
            Updated state with Spanish translations
        """
        logger.info("--- AGENT: Spanish Translator ---")
        
        try:
            processed_medications = state.get("processed_medications", [])
            if not processed_medications:
                return self._add_warning(state, "No processed medications available for translation")
            
            translated_medications = []
            translation_count = 0
            
            for medication in processed_medications:
                drug_name = medication.get("drug_name", "Unknown")
                sig_english = medication.get("sig_english")
                
                if sig_english:
                    try:
                        # Translate using Gemini
                        spanish_translation = await self._translate_to_spanish(sig_english)
                        medication["sig_spanish"] = spanish_translation
                        translation_count += 1
                        logger.info(f"Translated {drug_name} instructions to Spanish")
                    except Exception as e:
                        logger.error(f"Translation failed for {drug_name}: {e}")
                        medication["sig_spanish"] = ""
                else:
                    medication["sig_spanish"] = ""
                
                translated_medications.append(medication)
            
            logger.info(f"Spanish translation completed: {translation_count}/{len(processed_medications)} medications translated")
            
            return {
                **state,
                "processed_medications": translated_medications,
                "translation_results": {
                    "total_medications": len(processed_medications),
                    "translated_count": translation_count
                }
            }
            
        except Exception as e:
            logger.error(f"Spanish translation failed: {e}")
            return self._add_warning(state, f"Spanish translation failed: {str(e)}")
    
    async def _translate_to_spanish(self, sig_english: str) -> str:
        """
        Translate English sig to Spanish using Gemini 2.5 Pro
        
        Args:
            sig_english: English instructions
            
        Returns:
            Spanish translation
        """
        prompt = get_spanish_translation_prompt(sig_english)
        
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content.strip()
        except Exception as e:
            logger.error(f"Spanish translation failed: {e}")
            return ""  # Return empty if translation fails
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process method for compatibility with workflow
        
        Args:
            state: Workflow state
            
        Returns:
            Updated state
        """
        return await self.translate_medications(state)
    
    def _add_warning(self, state: Dict[str, Any], warning: str) -> Dict[str, Any]:
        """Add warning to state"""
        warnings = state.get("quality_warnings", [])
        warnings.append(warning)
        return {
            **state,
            "quality_warnings": warnings
        }