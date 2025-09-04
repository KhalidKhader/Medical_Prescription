

from src.core.services.neo4j.search.run_query import run_query
from typing import Dict, Any, List
from src.core.settings.config import settings
from src.core.settings.logging import logger
from src.core.services.neo4j.search.strength_instruction_search.queries import (
    strength_instruction_search_query,
    strength_focused_search_query,
)
from src.core.services.neo4j.search.strength_instruction_search.methods import (
    analyze_comprehensive_context,
    normalize_strength,
)

async def strength_instruction_search(
    prescription_data: Dict[str, Any],
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Comprehensive search using all prescription context
    
    Args:
        prescription_data: Dict containing drug_name, strength, instructions, synonyms, etc.
        limit: Maximum results to return
    """
    try:
        context = analyze_comprehensive_context(prescription_data)

        if not any(context.values()):
            logger.info("No searchable context found in prescription data")
            return []

        # Build dynamic query based on available context
        params = {"limit": limit}

        # Base drug matching
        drug_conditions = []
        for i, drug_variant in enumerate(context["drug_variants"]):
            param_name = f"drug_variant_{i}"
            params[param_name] = drug_variant
            drug_conditions.append(f"toLower(d.name) CONTAINS ${param_name}")
            drug_conditions.append(f"toLower(d.full_name) CONTAINS ${param_name}")
            drug_conditions.append(f"toLower(d.generic_name) CONTAINS ${param_name}")
        drug_clause = " OR ".join(drug_conditions)

        # Strength filtering
        strength_clause = ""
        if context["strength_filters"]:
            strength_conditions = []
            for i, s_filter in enumerate(context["strength_filters"]):
                if "CONTAINS" in s_filter:
                    value = s_filter.split("'")[1]
                    param_name = f"strength_val_{i}"
                    params[param_name] = value
                    strength_conditions.append(f"toLower(d.strength) CONTAINS ${param_name}")
                elif "=" in s_filter:
                    value = s_filter.split("'")[1]
                    param_name = f"strength_exact_{i}"
                    params[param_name] = value
                    strength_conditions.append(f"toLower(d.strength) = ${param_name}")
            if strength_conditions:
                strength_clause = f" AND ({' OR '.join(strength_conditions)})"

        # Route filtering
        route_clause = ""
        if context["route_filters"]:
            route_conditions = [f"toLower(d.route) CONTAINS $route_{i}" for i, r in enumerate(context["route_filters"])]
            for i, r in enumerate(context["route_filters"]):
                params[f"route_{i}"] = r
            route_clause = f" AND ({' OR '.join(route_conditions)})"

        # Form filtering
        form_clause = ""
        if context["form_filters"]:
            form_conditions = [f"toLower(d.dose_form) CONTAINS $form_{i}" for i, f in enumerate(context["form_filters"])]
            for i, f in enumerate(context["form_filters"]):
                params[f"form_{i}"] = f
            form_clause = f" AND ({' OR '.join(form_conditions)})"

        # Build final query from external query constructor
        query = strength_instruction_search_query(drug_clause, strength_clause, route_clause, form_clause)
        
        # Add target parameters for scoring
        params["target_strength"] = prescription_data.get("strength", "")
        params["target_route"] = context["route_filters"][0] if context["route_filters"] else ""
        params["target_form"] = context["form_filters"][0] if context["form_filters"] else ""

        # Use the generic run_query function
        search_method = "strength_instruction_search"
        results = await run_query(query, params, search_method)

        # Post-process results to add context-specific fields
        for drug in results:
            context_score = float(drug.get("context_score", 0))
            drug["match_confidence"] = min(context_score / 10.0, 1.0)
            drug["context_used"] = {
                "drug_variants": len(context["drug_variants"]),
                "strength_matched": bool(context["strength_filters"]),
                "route_matched": bool(context["route_filters"]),
                "form_matched": bool(context["form_filters"]),
            }

        return results

    except Exception as e:
        logger.error(f"Strength instruction search service failed: {e}")
        return []

async def strength_focused_search(
    drug_name: str,
    strength: str,
    synonyms: List[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Strength-focused search for exact strength matching
    Args:
        drug_name: Primary drug name
        strength: Target strength (e.g., "800mg", "800")
        synonyms: Alternative drug names
        limit: Maximum results
    """
    try:
        if not strength:
            return []
            
        normalized_strength = normalize_strength(strength)
        if not normalized_strength:
            return []

        drug_variants = [drug_name.lower()]
        if synonyms:
            drug_variants.extend([s.lower() for s in synonyms])

        # Build query components
        strength_conditions = [
            f"toLower(d.strength) CONTAINS '{normalized_strength}'",
            f"toLower(d.strength) CONTAINS toLower($full_strength)"
        ]
        if 'mg' in strength.lower():
            base_num = normalized_strength
            strength_conditions.append(f"toLower(d.strength) CONTAINS '{base_num} mg'")
            strength_conditions.append(f"toLower(d.strength) CONTAINS '{base_num}mg'")
        
        params = {
            "limit": limit,
            "full_strength": strength.lower(),
            "normalized_strength": normalized_strength
        }
        drug_conditions = []
        for i, variant in enumerate(drug_variants):
            param_name = f"drug_{i}"
            params[param_name] = variant
            drug_conditions.append(f"toLower(d.name) CONTAINS ${param_name}")
            drug_conditions.append(f"toLower(d.full_name) CONTAINS ${param_name}")
            drug_conditions.append(f"toLower(d.generic_name) CONTAINS ${param_name}")

        drug_clause = " OR ".join(drug_conditions)
        strength_clause = " OR ".join(strength_conditions)
        
        query = strength_focused_search_query(drug_clause, strength_clause)
        
        # Use the generic run_query function
        search_method = "strength_focused_search"
        results = await run_query(query, params, search_method)
        
        # Post-process results to add method-specific fields
        for drug in results:
            strength_score = float(drug.get("strength_score", 0))
            drug["match_confidence"] = min(strength_score / 25.0, 1.0)
            drug["target_strength"] = strength
            drug["normalized_target"] = normalized_strength

        return results

    except Exception as e:
        logger.error(f"Strength-focused search failed: {e}")
        return []