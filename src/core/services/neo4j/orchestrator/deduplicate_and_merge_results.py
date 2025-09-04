
from typing import Dict, Any, List
from src.core.settings.logging import logger

def deduplicate_and_merge_results(all_results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
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