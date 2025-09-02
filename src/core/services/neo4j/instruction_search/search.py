"""
Instruction Search Module
Handles instruction-based drug searching in RxNorm using route and form analysis
"""

from typing import Dict, Any, List
from neo4j import AsyncGraphDatabase
from src.core.settings.config import settings
from src.core.settings.logging import logger
from .queries import (
    search_by_route,
    search_by_form,
    search_by_route_and_strength,
    search_by_form_and_strength,
)

class InstructionSearchService:
    """Service for instruction-based drug searching in RxNorm"""
    
    def __init__(self, driver):
        self.driver = driver
    
    def _analyze_instructions(self, instructions: str) -> Dict[str, Any]:
        """Analyze instructions to extract route and form hints"""
        if not instructions:
            return {}
        
        instructions_lower = instructions.lower()
        analysis = {
            "route_hints": [],
            "form_hints": [],
            "frequency_hints": [],
            "administration_hints": []
        }
        
        # Route analysis
        if any(word in instructions_lower for word in ['ear', 'otic', 'au', 'ad', 'as']):
            analysis["route_hints"].append('otic')
        if any(word in instructions_lower for word in ['eye', 'ophthalmic', 'ou', 'od', 'os']):
            analysis["route_hints"].append('ophthalmic')
        if any(word in instructions_lower for word in ['oral', 'po', 'by mouth', 'swallow']):
            analysis["route_hints"].append('oral')
        if any(word in instructions_lower for word in ['topical', 'apply', 'skin']):
            analysis["route_hints"].append('topical')
        if any(word in instructions_lower for word in ['nasal', 'nose', 'nostril']):
            analysis["route_hints"].append('nasal')
        if any(word in instructions_lower for word in ['vaginal', 'vaginally']):
            analysis["route_hints"].append('vaginal')
        if any(word in instructions_lower for word in ['rectal', 'rectally']):
            analysis["route_hints"].append('rectal')
        if any(word in instructions_lower for word in ['inhale', 'inhalation', 'nebulize']):
            analysis["route_hints"].append('inhalation')
        
        # Form analysis
        if any(word in instructions_lower for word in ['tablet', 'tab']):
            analysis["form_hints"].append('tablet')
        if any(word in instructions_lower for word in ['capsule', 'cap']):
            analysis["form_hints"].append('capsule')
        if any(word in instructions_lower for word in ['drop', 'drops', 'gtt', 'gtts']):
            analysis["form_hints"].append('drops')
        if any(word in instructions_lower for word in ['cream', 'ointment', 'gel', 'lotion']):
            analysis["form_hints"].append('topical')
        if any(word in instructions_lower for word in ['injection', 'inject', 'im', 'iv', 'sq', 'sc']):
            analysis["form_hints"].append('injection')
        if any(word in instructions_lower for word in ['patch']):
            analysis["form_hints"].append('patch')
        if any(word in instructions_lower for word in ['inhaler', 'puff', 'spray']):
            analysis["form_hints"].append('inhaler')
        if any(word in instructions_lower for word in ['liquid', 'solution', 'syrup']):
            analysis["form_hints"].append('solution')
        
        # Administration hints
        if any(word in instructions_lower for word in ['instill', 'put in']):
            analysis["administration_hints"].append('instill')
        if any(word in instructions_lower for word in ['take', 'swallow']):
            analysis["administration_hints"].append('take')
        if any(word in instructions_lower for word in ['apply', 'rub']):
            analysis["administration_hints"].append('apply')
        if any(word in instructions_lower for word in ['insert']):
            analysis["administration_hints"].append('insert')
        
        return analysis
    
    async def search_by_instructions(self, drug_name: str, instructions: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for drugs based on instruction analysis"""
        try:
            analysis = self._analyze_instructions(instructions)
            if not any(analysis.values()):
                logger.info(f"No instruction hints found for '{instructions}'")
                return []
            
            all_results = []
            
            # Search by route hints
            for route_hint in analysis.get("route_hints", []):
                results = await self._search_by_route(drug_name, route_hint, limit)
                all_results.extend(results)
            
            # Search by form hints
            for form_hint in analysis.get("form_hints", []):
                results = await self._search_by_form(drug_name, form_hint, limit)
                all_results.extend(results)
            
            # Remove duplicates based on rxcui
            seen_rxcuis = set()
            unique_results = []
            for result in all_results:
                rxcui = result.get("rxcui")
                if rxcui and rxcui not in seen_rxcuis:
                    seen_rxcuis.add(rxcui)
                    result["instruction_analysis"] = analysis
                    unique_results.append(result)
            
            logger.info(f"Instruction search found {len(unique_results)} results for '{drug_name}' with instructions '{instructions}'")
            return unique_results[:limit]
            
        except Exception as e:
            logger.error(f"Instruction search failed: {e}")
            return []
    
    async def _search_by_route(self, drug_name: str, route_hint: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for drugs by route"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                query = search_by_route
                
                result = await session.run(query, drug_name=drug_name, route_hint=route_hint, limit=limit)
                
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
                        "search_method": "instruction_route_match",
                        "route_matched": route_hint,
                        "match_confidence": 0.85
                    })
                
                return drugs
                
        except Exception as e:
            logger.error(f"Route search failed for '{drug_name}' with route '{route_hint}': {e}")
            return []
    
    async def _search_by_form(self, drug_name: str, form_hint: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for drugs by dosage form"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                query = search_by_form 
                
                result = await session.run(query, drug_name=drug_name, form_hint=form_hint, limit=limit)
                
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
                        "search_method": "instruction_form_match",
                        "form_matched": form_hint,
                        "match_confidence": 0.8
                    })
                
                return drugs
                
        except Exception as e:
            logger.error(f"Form search failed for '{drug_name}' with form '{form_hint}': {e}")
            return []
    
    async def search_instructions_with_strength(self, drug_name: str, instructions: str, strength: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for drugs based on instructions and strength"""
        try:
            analysis = self._analyze_instructions(instructions)
            if not any(analysis.values()):
                return []
            
            all_results = []
            
            # Search by route hints with strength
            for route_hint in analysis.get("route_hints", []):
                results = await self._search_by_route_and_strength(drug_name, route_hint, strength, limit)
                all_results.extend(results)
            
            # Search by form hints with strength
            for form_hint in analysis.get("form_hints", []):
                results = await self._search_by_form_and_strength(drug_name, form_hint, strength, limit)
                all_results.extend(results)
            
            # Remove duplicates and enhance with analysis
            seen_rxcuis = set()
            unique_results = []
            for result in all_results:
                rxcui = result.get("rxcui")
                if rxcui and rxcui not in seen_rxcuis:
                    seen_rxcuis.add(rxcui)
                    result["instruction_analysis"] = analysis
                    unique_results.append(result)
            
            logger.info(f"Instruction with strength search found {len(unique_results)} results")
            return unique_results[:limit]
            
        except Exception as e:
            logger.error(f"Instruction with strength search failed: {e}")
            return []
    
    async def _search_by_route_and_strength(self, drug_name: str, route_hint: str, strength: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search by route and strength"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                query = search_by_route_and_strength 
                
                result = await session.run(query, drug_name=drug_name, route_hint=route_hint, strength=strength, limit=limit)
                
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
                        "search_method": "instruction_route_strength_match",
                        "route_matched": route_hint,
                        "match_confidence": 0.9
                    })
                
                return drugs
                
        except Exception as e:
            logger.error(f"Route and strength search failed: {e}")
            return []
    
    async def _search_by_form_and_strength(self, drug_name: str, form_hint: str, strength: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search by form and strength"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                query = search_by_form_and_strength 
                
                result = await session.run(query, drug_name=drug_name, form_hint=form_hint, strength=strength, limit=limit)
                
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
                        "search_method": "instruction_form_strength_match",
                        "form_matched": form_hint,
                        "match_confidence": 0.85
                    })
                
                return drugs
                
        except Exception as e:
            logger.error(f"Form and strength search failed: {e}")
            return []
