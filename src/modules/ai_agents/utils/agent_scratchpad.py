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


class AgentScratchpad:
    """Agent scratchpad for tracking thoughts and observations"""
    
    def __init__(self):
        self.thoughts = []
        self.observations = []
        self.actions = []
    
    def add_thought(self, thought: str):
        """Add a thought to the scratchpad"""
        self.thoughts.append(f"Thought: {thought}")
    
    def add_observation(self, observation: str):
        """Add an observation to the scratchpad"""
        self.observations.append(f"Observation: {observation}")
    
    def add_action(self, action: str):
        """Add an action to the scratchpad"""
        self.actions.append(f"Action: {action}")
    
    def get_context(self) -> str:
        """Get formatted scratchpad context"""
        all_entries = self.thoughts + self.observations + self.actions
        return "\n".join(all_entries[-10:])  # Last 10 entries
    
    def clear(self):
        """Clear the scratchpad"""
        self.thoughts.clear()
        self.observations.clear()
        self.actions.clear()