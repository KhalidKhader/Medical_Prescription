"""
Instruction Search Module
Handles instruction-based drug searching in RxNorm using route and form analysis
"""

from src.core.settings.logging import logger
from src.core.services.neo4j.search.instruction_search.service import search_by_instructions, search_instructions_with_strength

class InstructionSearchService:    
    """Service for instruction-based drug searching in RxNorm"""
    def __init__(self):
        self.search_by_instructions = search_by_instructions
        self.search_instructions_with_strength = search_instructions_with_strength
        logger.info("Instruction search service initialized")
