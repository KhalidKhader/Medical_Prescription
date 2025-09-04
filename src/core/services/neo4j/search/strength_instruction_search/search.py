"""
Comprehensive Instruction Search Module
Enhanced instruction-based search that considers all extracted prescription data
"""
from src.core.settings.logging import logger
from src.core.services.neo4j.search.strength_instruction_search.service import strength_instruction_search, strength_focused_search


class StrengthInstructionSearchService:
    """Enhanced instruction search considering all prescription context"""
    
    def __init__(self):
        self.strength_instruction_search = strength_instruction_search
        self.strength_focused_search = strength_focused_search
        logger.info("Strength instruction search service initialized")

    
   