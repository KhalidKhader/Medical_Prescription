import asyncio
from typing import Dict, Any, List, Optional
from src.core.settings.logging import logger
from src.core.services.neo4j.orchestrator.parallel_search_orchestrator import ParallelSearchOrchestrator
from src.core.services.neo4j.rxnorm_rag_service import rxnorm_service

client = ParallelSearchOrchestrator(rxnorm_service.driver)

async def parallel_search(
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
            client._run_search_method("exact_match", client.exact_search.search_exact_drug_name, drug_name, limit_per_method)
        )
        if strength:
            search_tasks.append(
                client._run_search_method("exact_match_strength", client.exact_search.search_exact_with_strength, drug_name, strength, limit_per_method)
            )
        
        # 2. Fuzzy match searches
        search_tasks.append(
            client._run_search_method("fuzzy_match", client.fuzzy_search.search_fuzzy_drug_name, drug_name, limit_per_method)
        )
        if strength:
            search_tasks.append(
                client._run_search_method("fuzzy_match_strength", client.fuzzy_search.search_fuzzy_with_strength, drug_name, strength, limit_per_method)
            )
        search_tasks.append(
            client._run_search_method("word_overlap", client.fuzzy_search.search_word_overlap, drug_name, limit_per_method)
        )
        
        # 3. Embedding searches
        search_tasks.append(
            client._run_search_method("embedding_search", client.embedding_search.search_by_embedding, drug_name, limit_per_method)
        )
        if strength:
            search_tasks.append(
                client._run_search_method("embedding_strength", client.embedding_search.search_by_embedding_with_strength, drug_name, strength, limit_per_method)
            )
        
        # 4. Brand searches
        search_tasks.append(
            client._run_search_method("brand_exact", client.brand_search.search_brand_exact, drug_name, limit_per_method)
        )
        search_tasks.append(
            client._run_search_method("brand_fuzzy", client.brand_search.search_brand_fuzzy, drug_name, limit_per_method)
        )
        search_tasks.append(
            client._run_search_method("generic_to_brand", client.brand_search.search_generic_to_brand, drug_name, limit_per_method)
        )
        if strength:
            search_tasks.append(
                client._run_search_method("brand_strength", client.brand_search.search_brand_with_strength, drug_name, strength, limit_per_method)
            )
        
        # 5. Synonym searches
        search_tasks.append(
            client._run_search_method("synonym_search", client.synonym_search.search_by_synonyms, drug_name, limit_per_method)
        )
        if strength:
            search_tasks.append(
                client._run_search_method("synonym_strength", client.synonym_search.search_synonyms_with_strength, drug_name, strength, limit_per_method)
            )
        
        # 6. Instruction searches
        if instructions:
            search_tasks.append(
                client._run_search_method("instruction_search", client.instruction_search.search_by_instructions, drug_name, instructions, limit_per_method)
            )
            if strength:
                search_tasks.append(
                    client._run_search_method("instruction_strength", client.instruction_search.search_instructions_with_strength, drug_name, instructions, strength, limit_per_method)
                )
            
            # Enhanced comprehensive instruction search with all context
            prescription_data = {
                "drug_name": drug_name,
                "strength": strength,
                "instructions": instructions,
                "synonyms": client.synonym_search.get_synonyms(drug_name)
            }
            search_tasks.append(
                client._run_search_method("comprehensive_instruction", client.strength_instruction_search.strength_instruction_search, prescription_data, limit_per_method)
            )
            
            # Strength-focused search if strength is provided
            if strength:
                search_tasks.append(
                    client._run_search_method("strength_focused", client.strength_instruction_search.strength_focused_search, drug_name, strength, client.synonym_search.get_synonyms(drug_name), limit_per_method)
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