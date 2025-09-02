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
from .prompts import build_drug_selection_prompt


class SmartDrugSelectorAgent:
    """Enhanced drug selector using comprehensive search strategies"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            temperature=0,
            google_api_key=settings.google_api_key
        )
    
    async def validate_and_correct_drug(self, medication_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate drug selection using enhanced search strategies"""
        
        drug_name = medication_data.get("drug_name", "")
        strength = medication_data.get("strength", "")
        candidates = medication_data.get("all_candidates", [])
        
        if not drug_name:
            return medication_data
        
        # Use enhanced search if no good candidates or strength mismatch
        if not candidates or self._needs_enhanced_search(medication_data):
            logger.info(f"🔍 Performing enhanced search for: {drug_name}")
            return await self._enhanced_drug_search(medication_data)
        
        return medication_data
    
    def _needs_enhanced_search(self, medication_data: Dict[str, Any]) -> bool:
        """Determine if enhanced search is needed"""
        candidates = medication_data.get("all_candidates", [])
        original_strength = medication_data.get("strength", "")
        
        if not candidates:
            return True
        
        # Check if any candidate has appropriate form/strength match
        if original_strength:
            strength_found = any(
                self._strength_compatible(original_strength, candidate.get("strength", ""))
                for candidate in candidates
            )
            if not strength_found:
                return True
        
        return False
    
    def _strength_compatible(self, original: str, candidate: str) -> bool:
        """Check if strengths are compatible using string matching"""
        if not original or not candidate:
            return False
        
        # Simple numeric extraction without regex
        orig_nums = ''.join(c for c in original if c.isdigit() or c == '.')
        cand_nums = ''.join(c for c in candidate if c.isdigit() or c == '.')
        
        return orig_nums == cand_nums if orig_nums and cand_nums else False
    
    async def _enhanced_drug_search(self, medication_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform enhanced drug search using multiple strategies"""
        
        drug_name = medication_data.get("drug_name", "")
        strength = medication_data.get("strength", "")
        instructions = medication_data.get("instructions_for_use", "")
        
        # Build comprehensive search context
        context = {
            "original_drug": drug_name,
            "strength": strength,
            "instructions": instructions,
            "patient_context": medication_data.get("patient_context", {})
        }
        
        try:
            # Use comprehensive search from RxNorm service
            enhanced_results = await rxnorm_service.get_comprehensive_drug_info(
                drug_name=drug_name,
                strength=strength,
                instructions=instructions,
                context=context
            )
            
            if enhanced_results:
                # Use LLM to select best match from enhanced results
                best_match = await self._llm_select_best_match(
                    enhanced_results, medication_data
                )
                
                if best_match:
                    logger.info(f"✅ Enhanced search found: {best_match.get('drug_name')}")
                    
                    # Update medication data
                    medication_data.update({
                        "rxcui": best_match.get("rxcui"),
                        "drug_name": best_match.get("drug_name"),
                        "generic_name": best_match.get("generic_name"),
                        "verified_name": best_match.get("drug_name"),
                        "brand_drug": best_match.get("brand_name"),
                        "search_method": "enhanced_comprehensive",
                        "all_candidates": enhanced_results[:5],
                        "enhancement_applied": True
                    })
        
        except Exception as e:
            logger.error(f"Enhanced search failed: {e}")
        
        return medication_data
    
    async def _llm_select_best_match(
        self, 
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
            response = await self.llm.ainvoke([message])
            
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
    