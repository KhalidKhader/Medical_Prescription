"""
Comprehensive Instruction Search Module
Enhanced instruction-based search that considers all extracted prescription data
"""

from typing import Dict, Any, List
from neo4j import AsyncGraphDatabase
from src.core.settings.config import settings
from src.core.settings.logging import logger
from .queries import (
    strength_instruction_search,
    strength_focused_search,
)

class StrengthInstructionSearchService:
    """Enhanced instruction search considering all prescription context"""
    
    def __init__(self, driver):
        self.driver = driver
    
    def _extract_strength_numbers(self, strength: str) -> str:
        """Extract numeric part of strength for comparison"""
        if not strength:
            return ""
        # Extract digits and decimal points
        numeric_part = ''.join(c for c in strength if c.isdigit() or c == '.')
        return numeric_part.strip('.').lstrip('0') if numeric_part else ""

    def _normalize_strength(self, strength: str) -> str:
        """Normalize strength for better matching"""
        if not strength:
            return ""

        # Extract the numeric part
        numeric_part = self._extract_strength_numbers(strength)

        # Remove leading zeros and trailing dots
        if numeric_part:
            numeric_part = numeric_part.strip('.').lstrip('0')
            if not numeric_part:
                numeric_part = "0"

        return numeric_part
    
    def _analyze_comprehensive_context(self, prescription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze all prescription data for comprehensive search context"""
        context = {
            "drug_variants": [],
            "strength_filters": [],
            "route_filters": [],
            "form_filters": [],
            "brand_generic_hints": []
        }
        
        drug_name = prescription_data.get("drug_name", "")
        strength = prescription_data.get("strength", "")
        instructions = prescription_data.get("instructions", "")
        synonyms = prescription_data.get("synonyms", [])
        
        # Drug name variants
        context["drug_variants"] = [drug_name.lower()]
        if synonyms:
            context["drug_variants"].extend([s.lower() for s in synonyms])
        
        # Strength context
        if strength:
            strength_num = self._extract_strength_numbers(strength)
            if strength_num:
                context["strength_filters"] = [
                    f"CONTAINS '{strength_num}'",
                    f"CONTAINS '{strength.lower()}'",
                    f"= '{strength.lower()}'"
                ]
        
        # Route and form analysis from instructions
        if instructions:
            inst_lower = instructions.lower()
            
            # Route analysis
            if any(word in inst_lower for word in ['oral', 'po', 'by mouth', 'swallow', 'take']):
                context["route_filters"].append("oral")
            if any(word in inst_lower for word in ['eye', 'ophthalmic', 'ou', 'od', 'os', 'instill']):
                context["route_filters"].append("ophthalmic")
            if any(word in inst_lower for word in ['ear', 'otic', 'au', 'ad', 'as']):
                context["route_filters"].append("otic")
            if any(word in inst_lower for word in ['topical', 'apply', 'skin']):
                context["route_filters"].append("topical")
            if any(word in inst_lower for word in ['nasal', 'nose', 'nostril']):
                context["route_filters"].append("nasal")
            if any(word in inst_lower for word in ['inhale', 'inhalation', 'puff']):
                context["route_filters"].append("inhalation")
            
            # Form analysis
            if any(word in inst_lower for word in ['tablet', 'tab']):
                context["form_filters"].append("tablet")
            if any(word in inst_lower for word in ['capsule', 'cap']):
                context["form_filters"].append("capsule")
            if any(word in inst_lower for word in ['drop', 'drops', 'gtt', 'gtts']):
                context["form_filters"].append("drops")
                context["form_filters"].append("solution")
            if any(word in inst_lower for word in ['cream', 'ointment', 'gel']):
                context["form_filters"].append("cream")
                context["form_filters"].append("ointment")
            if any(word in inst_lower for word in ['injection', 'inject']):
                context["form_filters"].append("injection")
            if any(word in inst_lower for word in ['inhaler', 'spray']):
                context["form_filters"].append("inhaler")
            if any(word in inst_lower for word in ['liquid', 'solution', 'syrup']):
                context["form_filters"].append("solution")
                context["form_filters"].append("liquid")
        
        return context
    
    async def strength_instruction_search(
        self, 
        prescription_data: Dict[str, Any], 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Comprehensive search using all prescription context
        
        Args:
            prescription_data: Dict containing drug_name, strength, instructions, synonyms, etc.
            limit: Maximum results to return
        """
        try:
            context = self._analyze_comprehensive_context(prescription_data)
            
            if not any(context.values()):
                logger.info("No searchable context found in prescription data")
                return []
            
            # Build dynamic query based on available context
            query_parts = []
            params = {"limit": limit}
            
            # Base drug matching with all variants
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
                for i, strength_filter in enumerate(context["strength_filters"]):
                    if "CONTAINS" in strength_filter:
                        # Extract the value from CONTAINS 'value'
                        value = strength_filter.split("'")[1]
                        param_name = f"strength_val_{i}"
                        params[param_name] = value
                        strength_conditions.append(f"toLower(d.strength) CONTAINS ${param_name}")
                    elif "=" in strength_filter:
                        # Extract the value from = 'value'
                        value = strength_filter.split("'")[1]
                        param_name = f"strength_exact_{i}"
                        params[param_name] = value
                        strength_conditions.append(f"toLower(d.strength) = ${param_name}")
                
                if strength_conditions:
                    strength_clause = f" AND ({' OR '.join(strength_conditions)})"
            
            # Route filtering
            route_clause = ""
            if context["route_filters"]:
                route_conditions = []
                for i, route in enumerate(context["route_filters"]):
                    param_name = f"route_{i}"
                    params[param_name] = route
                    route_conditions.append(f"toLower(d.route) CONTAINS ${param_name}")
                
                route_clause = f" AND ({' OR '.join(route_conditions)})"
            
            # Form filtering
            form_clause = ""
            if context["form_filters"]:
                form_conditions = []
                for i, form in enumerate(context["form_filters"]):
                    param_name = f"form_{i}"
                    params[param_name] = form
                    form_conditions.append(f"toLower(d.dose_form) CONTAINS ${param_name}")
                
                form_clause = f" AND ({' OR '.join(form_conditions)})"
            
            # Build final query
            query = strength_instruction_search(drug_clause, strength_clause, route_clause, form_clause) 
            
            # Add target parameters for scoring
            params["target_strength"] = prescription_data.get("strength", "")
            params["target_route"] = context["route_filters"][0] if context["route_filters"] else ""
            params["target_form"] = context["form_filters"][0] if context["form_filters"] else ""
            
            async with self.driver.session(database=settings.neo4j_database) as session:
                result = await session.run(query, **params)
                
                drugs = []
                async for record in result:
                    drugs.append({
                        "rxcui": record.get("rxcui"),
                        "drug_name": record.get("drug_name"),
                        "full_name": record.get("full_name"),
                        "generic_name": record.get("generic_name"),
                        "strength": record.get("strength"),
                        "route": record.get("route"),
                        "dose_form": record.get("dose_form"),
                        "term_type": record.get("term_type"),
                        "search_method": "strength_instruction_search",
                        "context_score": float(record.get("context_score", 0)),
                        "match_confidence": min(float(record.get("context_score", 0)) / 10.0, 1.0),
                        "context_used": {
                            "drug_variants": len(context["drug_variants"]),
                            "strength_matched": bool(context["strength_filters"]),
                            "route_matched": bool(context["route_filters"]),
                            "form_matched": bool(context["form_filters"])
                        }
                    })
                
                logger.info(f"Comprehensive instruction search found {len(drugs)} results")
                return drugs
                
        except Exception as e:
            logger.error(f"Comprehensive instruction search failed: {e}")
            return []
    
    async def strength_focused_search(
        self,
        drug_name: str,
        strength: str,
        synonyms: List[str] = None,
        limit: int = 10
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

            # Normalize the target strength
            normalized_strength = self._normalize_strength(strength)
            if not normalized_strength:
                return []

            # Build drug name variants
            drug_variants = [drug_name.lower()]
            if synonyms:
                drug_variants.extend([s.lower() for s in synonyms])

            # Build comprehensive strength matching conditions
            strength_conditions = []

            # Exact numeric match
            strength_conditions.append(f"toLower(d.strength) CONTAINS '{normalized_strength}'")

            # Full strength string match
            strength_conditions.append(f"toLower(d.strength) CONTAINS toLower($full_strength)")

            # Unit variations (mg, mg/ml, etc.)
            if 'mg' in strength.lower():
                base_num = normalized_strength
                strength_conditions.append(f"toLower(d.strength) CONTAINS '{base_num} mg'")
                strength_conditions.append(f"toLower(d.strength) CONTAINS '{base_num}mg'")

            # Build drug matching conditions
            drug_conditions = []
            params = {
                "limit": limit,
                "full_strength": strength.lower(),
                "normalized_strength": normalized_strength
            }

            for i, variant in enumerate(drug_variants):
                param_name = f"drug_{i}"
                params[param_name] = variant
                drug_conditions.append(f"toLower(d.name) CONTAINS ${param_name}")
                drug_conditions.append(f"toLower(d.full_name) CONTAINS ${param_name}")
                drug_conditions.append(f"toLower(d.generic_name) CONTAINS ${param_name}")

            drug_clause = " OR ".join(drug_conditions)
            strength_clause = " OR ".join(strength_conditions)

            query = strength_focused_search(drug_clause, strength_clause) 

            async with self.driver.session(database=settings.neo4j_database) as session:
                result = await session.run(query, **params)

                drugs = []
                async for record in result:
                    drugs.append({
                        "rxcui": record.get("rxcui"),
                        "drug_name": record.get("drug_name"),
                        "full_name": record.get("full_name"),
                        "generic_name": record.get("generic_name"),
                        "strength": record.get("strength"),
                        "route": record.get("route"),
                        "dose_form": record.get("dose_form"),
                        "term_type": record.get("term_type"),
                        "search_method": "strength_focused_search",
                        "strength_score": float(record.get("strength_score", 0)),
                        "match_confidence": min(float(record.get("strength_score", 0)) / 25.0, 1.0),
                        "target_strength": strength,
                        "normalized_target": normalized_strength
                    })

                logger.info(f"Strength-focused search found {len(drugs)} results for '{drug_name} {strength}' (normalized: {normalized_strength})")
                return drugs

        except Exception as e:
            logger.error(f"Strength-focused search failed: {e}")
            return []
