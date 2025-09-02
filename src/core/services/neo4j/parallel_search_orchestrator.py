"""
Parallel Search Orchestrator
Coordinates all search methods in parallel for optimal performance
"""

import asyncio
from typing import Dict, Any, List, Optional
from src.core.settings.logging import logger
from .exact_match_search.search import ExactMatchSearchService
from .fuzzy_match_search.search import FuzzyMatchSearchService
from .embedding_search.search import EmbeddingSearchService
from .brand_search.search import BrandSearchService
from .synonym_search.search import SynonymSearchService
from .instruction_search.search import InstructionSearchService
from .strength_instruction_search.search import StrengthInstructionSearchService


class ParallelSearchOrchestrator:
    """Orchestrates parallel drug searches across all search methods"""
    
    def __init__(self, driver):
        self.driver = driver
        
        # Initialize all search services
        self.exact_search = ExactMatchSearchService(driver)
        self.fuzzy_search = FuzzyMatchSearchService(driver)
        self.embedding_search = EmbeddingSearchService(driver)
        self.brand_search = BrandSearchService(driver)
        self.synonym_search = SynonymSearchService(driver)
        self.instruction_search = InstructionSearchService(driver)
        self.strength_instruction_search = StrengthInstructionSearchService(driver)
    
    async def comprehensive_parallel_search(
        self,
        drug_name: str,
        strength: str = None,
        instructions: str = None,
        safety_context: Dict[str, Any] = None,
        limit_per_method: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Execute all search methods in parallel for comprehensive results
        
        Args:
            drug_name: Drug name to search for
            strength: Drug strength (optional)
            instructions: Usage instructions (optional)
            safety_context: Safety assessment context (optional)
            limit_per_method: Results limit per search method
            
        Returns:
            Dictionary with results from each search method
        """
        logger.info(f"🚀 Starting comprehensive parallel search for '{drug_name}'")
        
        try:
            # Create all search tasks to run in parallel
            search_tasks = []
            
            # 1. Exact match searches
            search_tasks.append(
                self._run_search_method("exact_match", self.exact_search.search_exact_drug_name, drug_name, limit_per_method)
            )
            if strength:
                search_tasks.append(
                    self._run_search_method("exact_match_strength", self.exact_search.search_exact_with_strength, drug_name, strength, limit_per_method)
                )
            
            # 2. Fuzzy match searches
            search_tasks.append(
                self._run_search_method("fuzzy_match", self.fuzzy_search.search_fuzzy_drug_name, drug_name, limit_per_method)
            )
            if strength:
                search_tasks.append(
                    self._run_search_method("fuzzy_match_strength", self.fuzzy_search.search_fuzzy_with_strength, drug_name, strength, limit_per_method)
                )
            search_tasks.append(
                self._run_search_method("word_overlap", self.fuzzy_search.search_word_overlap, drug_name, limit_per_method)
            )
            
            # 3. Embedding searches
            search_tasks.append(
                self._run_search_method("embedding_search", self.embedding_search.search_by_embedding, drug_name, limit_per_method)
            )
            if strength:
                search_tasks.append(
                    self._run_search_method("embedding_strength", self.embedding_search.search_by_embedding_with_strength, drug_name, strength, limit_per_method)
                )
            
            # 4. Brand searches
            search_tasks.append(
                self._run_search_method("brand_exact", self.brand_search.search_brand_exact, drug_name, limit_per_method)
            )
            search_tasks.append(
                self._run_search_method("brand_fuzzy", self.brand_search.search_brand_fuzzy, drug_name, limit_per_method)
            )
            search_tasks.append(
                self._run_search_method("generic_to_brand", self.brand_search.search_generic_to_brand, drug_name, limit_per_method)
            )
            if strength:
                search_tasks.append(
                    self._run_search_method("brand_strength", self.brand_search.search_brand_with_strength, drug_name, strength, limit_per_method)
                )
            
            # 5. Synonym searches
            search_tasks.append(
                self._run_search_method("synonym_search", self.synonym_search.search_by_synonyms, drug_name, limit_per_method)
            )
            if strength:
                search_tasks.append(
                    self._run_search_method("synonym_strength", self.synonym_search.search_synonyms_with_strength, drug_name, strength, limit_per_method)
                )
            
            # 6. Instruction searches
            if instructions:
                search_tasks.append(
                    self._run_search_method("instruction_search", self.instruction_search.search_by_instructions, drug_name, instructions, limit_per_method)
                )
                if strength:
                    search_tasks.append(
                        self._run_search_method("instruction_strength", self.instruction_search.search_instructions_with_strength, drug_name, instructions, strength, limit_per_method)
                    )
                
                # Enhanced comprehensive instruction search with all context
                prescription_data = {
                    "drug_name": drug_name,
                    "strength": strength,
                    "instructions": instructions,
                    "synonyms": self.synonym_search.get_synonyms(drug_name)
                }
                search_tasks.append(
                    self._run_search_method("comprehensive_instruction", self.strength_instruction_search.strength_instruction_search, prescription_data, limit_per_method)
                )
                
                # Strength-focused search if strength is provided
                if strength:
                    search_tasks.append(
                        self._run_search_method("strength_focused", self.strength_instruction_search.strength_focused_search, drug_name, strength, self.synonym_search.get_synonyms(drug_name), limit_per_method)
                    )
            
            # Execute all searches in parallel
            logger.info(f"⚡ Executing {len(search_tasks)} search methods in parallel")
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Process results
            consolidated_results = {}
            for i, result in enumerate(search_results):
                if isinstance(result, Exception):
                    logger.error(f"Search method {i} failed: {result}")
                    continue
                
                method_name, method_results = result
                consolidated_results[method_name] = method_results
                logger.info(f"✅ {method_name}: {len(method_results)} results")
            
            # Log summary
            total_results = sum(len(results) for results in consolidated_results.values())
            logger.info(f"🎯 Parallel search completed: {total_results} total results from {len(consolidated_results)} methods")
            
            return consolidated_results
            
        except Exception as e:
            logger.error(f"Parallel search orchestration failed: {e}")
            return {}
    
    async def _run_search_method(self, method_name: str, search_func, *args) -> tuple:
        """Run a single search method and return results with method name"""
        try:
            results = await search_func(*args)
            return method_name, results
        except Exception as e:
            logger.error(f"Search method '{method_name}' failed: {e}")
            return method_name, []
    
    def deduplicate_and_merge_results(self, all_results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Deduplicate and merge results from all search methods
        
        Args:
            all_results: Dictionary of results from each search method
            
        Returns:
            Deduplicated and merged list of drug results
        """
        try:
            seen_rxcuis = set()
            merged_results = []
            
            # Priority order for search methods (strength-focused first, then exact matches)
            method_priority = [
                "strength_focused", "comprehensive_instruction",  # Highest priority
                "exact_match", "exact_match_strength",
                "brand_exact", "brand_strength",
                "fuzzy_match_strength", "fuzzy_match",
                "synonym_search", "synonym_strength",
                "embedding_search", "embedding_strength",
                "instruction_search", "instruction_strength",
                "brand_fuzzy", "generic_to_brand",
                "word_overlap"
            ]
            
            # Process results in priority order
            for method in method_priority:
                if method in all_results:
                    for result in all_results[method]:
                        rxcui = result.get("rxcui")
                        if rxcui and rxcui not in seen_rxcuis:
                            seen_rxcuis.add(rxcui)
                            
                            # Add search method info
                            result["search_methods_found"] = [method]
                            result["primary_search_method"] = method
                            merged_results.append(result)
                        elif rxcui and rxcui in seen_rxcuis:
                            # Add this search method to existing result
                            for existing in merged_results:
                                if existing.get("rxcui") == rxcui:
                                    if "search_methods_found" not in existing:
                                        existing["search_methods_found"] = [existing.get("search_method", "unknown")]
                                    existing["search_methods_found"].append(method)
                                    break
            
            # Add remaining results from any method not in priority list
            for method, results in all_results.items():
                if method not in method_priority:
                    for result in results:
                        rxcui = result.get("rxcui")
                        if rxcui and rxcui not in seen_rxcuis:
                            seen_rxcuis.add(rxcui)
                            result["search_methods_found"] = [method]
                            result["primary_search_method"] = method
                            merged_results.append(result)
            
            logger.info(f"🔄 Deduplication complete: {len(merged_results)} unique drugs from {len(seen_rxcuis)} RXCUIs")
            return merged_results
            
        except Exception as e:
            logger.error(f"Result deduplication failed: {e}")
            return []
    
    def calculate_comprehensive_scores(
        self,
        results: List[Dict[str, Any]],
        original_drug: str,
        strength: str = None,
        instructions: str = None,
        safety_context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate comprehensive relevance scores for all results
        
        Args:
            results: List of drug results
            original_drug: Original drug name from prescription
            strength: Drug strength
            instructions: Usage instructions
            safety_context: Safety assessment context
            
        Returns:
            Results with comprehensive scores
        """
        try:
            for result in results:
                score = 0.0
                scoring_details = {}
                
                # Base score from search method confidence
                base_confidence = result.get("match_confidence", 0.7)
                score += base_confidence * 30  # Up to 30 points
                scoring_details["base_confidence"] = base_confidence
                
                # Drug name matching (30 points max)
                drug_name = result.get("drug_name", "").lower()
                original_lower = original_drug.lower()
                
                if drug_name == original_lower:
                    score += 30
                    scoring_details["name_match"] = "exact"
                elif original_lower in drug_name or drug_name in original_lower:
                    score += 20
                    scoring_details["name_match"] = "partial"
                else:
                    score += 10
                    scoring_details["name_match"] = "weak"
                
                # Strength matching (20 points max)
                if strength and result.get("strength"):
                    result_strength = result.get("strength", "").lower()
                    strength_nums = ''.join(c for c in strength if c.isdigit())
                    result_nums = ''.join(c for c in result_strength if c.isdigit())
                    
                    if strength_nums and result_nums and strength_nums == result_nums:
                        score += 20
                        scoring_details["strength_match"] = "exact"
                    elif strength.lower() in result_strength:
                        score += 15
                        scoring_details["strength_match"] = "partial"
                    else:
                        score += 5
                        scoring_details["strength_match"] = "weak"
                
                # Multiple search method bonus (10 points max)
                search_methods = result.get("search_methods_found", [])
                if len(search_methods) > 1:
                    score += min(len(search_methods) * 2, 10)
                    scoring_details["multi_method_bonus"] = len(search_methods)
                
                # Primary search method bonus (15 points max) - prioritize strength-focused methods
                primary_method = result.get("primary_search_method", "")
                if primary_method in ["strength_focused", "comprehensive_instruction"]:
                    score += 15  # Highest priority for strength-focused searches
                    scoring_details["strength_method_bonus"] = 15
                elif primary_method in ["exact_match", "exact_match_strength"]:
                    score += 10
                elif primary_method in ["brand_exact", "brand_strength"]:
                    score += 8
                elif primary_method in ["fuzzy_match_strength", "synonym_search"]:
                    score += 6
                else:
                    score += 3
                scoring_details["primary_method_bonus"] = primary_method

                # Additional strength score bonus (20 points max)
                if result.get("strength_score", 0) > 0:
                    strength_bonus = min(result.get("strength_score", 0) / 25.0 * 20, 20)
                    score += strength_bonus
                    scoring_details["strength_focused_bonus"] = strength_bonus
                
                # Safety context bonus (if available)
                if safety_context:
                    # This would be implemented based on safety assessment structure
                    scoring_details["safety_bonus"] = 0
                
                result["comprehensive_score"] = round(score, 2)
                result["scoring_details"] = scoring_details
            
            # Sort by comprehensive score
            results.sort(key=lambda x: x.get("comprehensive_score", 0), reverse=True)
            
            logger.info(f"📊 Comprehensive scoring complete for {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Comprehensive scoring failed: {e}")
            return results
