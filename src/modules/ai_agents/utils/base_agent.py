"""
Abstract Base Agent - Common functionality for all AI agents
Provides standardized structure, observability, and performance tracking
"""

from typing import Dict, Any, List
from abc import ABC, abstractmethod
from src.modules.ai_agents.utils.json_parser import parse_json
from src.core.settings.logging import logger
from langchain_core.messages import HumanMessage
from src.core.services.gemini.client import gemini_client
from langfuse import observe
import time
from src.modules.ai_agents.utils.agent_scratchpad import AgentScratchpad


class BaseAgent(ABC):
    """Base class for all AI agents with standard structure"""
    
    def __init__(self, agent_name: str):
        """Initialize base agent"""
        self.agent_name = agent_name
        self.scratchpad = AgentScratchpad()
        
        # Initialize LLM from the central client
        self.llm = gemini_client.langchain_llm
        
        logger.info(f"{agent_name} initialized")
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def get_prompt(self, **kwargs) -> str:
        """Get formatted prompt - must be implemented by subclasses"""
        pass
    
    def get_enhanced_prompt(self, base_prompt: str) -> str:
        """Enhance prompt with scratchpad context"""
        context = self.scratchpad.get_context()
        if context:
            return f"{base_prompt}\n\nContext from previous processing:\n{context}"
        return base_prompt
    
    @observe(capture_input=True, capture_output=True)
    async def call_llm(self, prompt: str) -> str:
        """Call LLM with observability and error handling"""
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"{self.agent_name} LLM call failed: {e}")
            raise
    
    async def call_llm_with_image(self, messages: list) -> str:
        """Call LLM with image support for vision models"""
        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"{self.agent_name} Vision LLM call failed: {e}")
            raise
    

    @observe(capture_input=True, capture_output=True)
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent with observability"""
        try:
            self.scratchpad.add_action(f"Starting {self.agent_name} processing")
            result = await self.process(data)
            self.scratchpad.add_observation(f"{self.agent_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{self.agent_name} failed: {e}")
            self.scratchpad.add_observation(f"{self.agent_name} failed: {e}")
            raise
    
    def parse_json(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response with error handling"""
        return parse_json(response_text)
    
    def add_warning(self, state: Dict[str, Any], warning: str) -> Dict[str, Any]:
        """Add warning to state"""
        warnings = state.get("quality_warnings", [])
        warnings.append(f"{self.agent_name}: {warning}")
        return {**state, "quality_warnings": warnings}
    
    def create_error_response(self, error: str, state: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standardized error response"""
        base_response = {
            "success": False,
            "error": error,
            "agent": self.agent_name
        }
        if state:
            return {**state, **base_response}
        return base_response
    

