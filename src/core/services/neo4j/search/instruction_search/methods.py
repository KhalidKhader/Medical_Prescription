"""
Instruction Search Module
Handles instruction-based drug searching in RxNorm using route and form analysis
"""
from typing import Dict, Any, List
from src.core.services.neo4j.search.instruction_search.queries import (
    search_by_route_query,
    search_by_form_query,
    search_by_route_and_strength_query,
    search_by_form_and_strength_query,
)
from src.core.services.neo4j.search.run_query import run_query
from src.core.settings.logging import logger

def analyze_instructions(instructions: str) -> Dict[str, Any]:
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

async def search_by_route_match(drug_name: str, route_hint: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for drugs by route"""
    return await run_query(
        query=search_by_route_query,
        params={"drug_name": drug_name, "route_hint": route_hint, "limit": limit},
        search_method="instruction_route_match",
        match_confidence=0.8,
    )

async def search_by_form_match(drug_name: str, form_hint: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for drugs by dosage form"""
    return await run_query(
        query=search_by_form_query,
        params={"drug_name": drug_name, "form_hint": form_hint, "limit": limit},
        search_method="instruction_form_match",
        match_confidence=0.8,
    )

async def search_by_route_and_strength_match(drug_name: str, route_hint: str, strength: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search by route and strength"""
    return await run_query(
        query=search_by_route_and_strength_query,
        params={"drug_name": drug_name, "route_hint": route_hint, "strength": strength, "limit": limit},
        search_method="instruction_route_strength_match",
        match_confidence=0.8,
    )

async def search_by_form_and_strength_match(drug_name: str, form_hint: str, strength: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search by form and strength"""
    return await run_query(
        query=search_by_form_and_strength_query,
        params={"drug_name": drug_name, "form_hint": form_hint, "strength": strength, "limit": limit},
        search_method="instruction_form_strength_match",
        match_confidence=0.8,
    )

