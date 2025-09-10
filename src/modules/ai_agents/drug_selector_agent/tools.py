"""
Smart Drug Selector Agent - Enhanced search without regex patterns
Uses comprehensive RxNorm search strategies for optimal drug matching
"""

from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from src.core.settings.config import settings
from src.core.settings.logging import logger
from src.core.services.neo4j.rxnorm_rag_service import rxnorm_service
import json
from src.modules.ai_agents.drug_selector_agent.prompts import build_drug_selection_prompt
from src.core.services.neo4j.get_drug_info import get_drug_info


class DrugSelectorAgent:
    """Enhanced drug selector using comprehensive search strategies"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            temperature=0,
            google_api_key=settings.google_api_key
        )
    
    @staticmethod
    async def llm_select_best_match(
        candidates: List[Dict[str, Any]], 
        original_medication: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to select the best drug match avoiding wrong suffixes"""
        
        if not candidates:
            return None
        
        # Build selection prompt
        prompt = build_drug_selection_prompt(candidates, original_medication)
        
        try:
            message = HumanMessage(content=prompt)
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-pro",
                temperature=0,
                google_api_key=settings.google_api_key
            )
            response = await llm.ainvoke([message])
            
            # Parse response
            # Clean and validate response content
            response_content = response.content.strip()
            if not response_content:
                logger.warning("Empty response from LLM drug selection")
                return candidates[0]
            
            # Try to parse JSON with error handling
            try:
                selection_data = json.loads(response_content)
            except json.JSONDecodeError:
                # Try to repair JSON if malformed
                from json_repair import repair_json
                try:
                    repaired_json = repair_json(response_content)
                    selection_data = json.loads(repaired_json)
                    logger.info("Successfully repaired malformed JSON from LLM")
                except Exception:
                    logger.error(f"Failed to parse LLM response as JSON: {response_content[:200]}...")
                    return candidates[0]
            
            selected_rxcui = selection_data.get("selected_rxcui")
            
            if not selected_rxcui:
                logger.warning("No selected_rxcui in LLM response")
                return candidates[0]
            
            # Find selected candidate
            for candidate in candidates:
                if str(candidate.get('rxcui', '')) == str(selected_rxcui):
                    logger.info(f"🎯 LLM selected: {candidate.get('drug_name')} (RXCUI: {selected_rxcui})")
                    return candidate
            
            logger.warning(f"Selected RXCUI {selected_rxcui} not found in candidates")
                    
        except Exception as e:
            logger.error(f"LLM drug selection failed: {e}")
        
        # Fallback to first candidate
        return candidates[0]
    
# Create an instance of the agent to use for the module-level function
_drug_selector = DrugSelectorAgent()

# Module-level function that delegates to the instance method
async def llm_select_best_match(candidates: List[Dict[str, Any]], original_medication: Dict[str, Any]) -> Dict[str, Any]:
    return await _drug_selector.llm_select_best_match(candidates, original_medication)