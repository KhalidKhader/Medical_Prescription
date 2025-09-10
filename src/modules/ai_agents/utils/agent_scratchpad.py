"""
Agent Scratchpad - Enhanced reasoning and memory for AI agents
Implements LangChain-style scratchpad for better decision making
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from src.core.settings.logging import logger


@dataclass
class AgentAction:
    """Represents an action taken by an agent"""
    tool: str
    tool_input: Dict[str, Any]
    log: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentObservation:
    """Represents an observation from an action"""
    content: str
    success: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentStep:
    """Represents a complete step in agent reasoning"""
    action: AgentAction
    observation: AgentObservation


class AgentScratchpad:
    """Enhanced scratchpad for agent reasoning and memory"""
    
    def __init__(self):
        self.observations = []
        self.thoughts = []
        self.actions = []
        self.results = []
        self.current_step = 0
    
    def add_observation(self, observation: str):
        """Add an observation to the scratchpad"""
        self.observations.append({
            "step": self.current_step,
            "timestamp": datetime.now().isoformat(),
            "content": observation
        })
    
    def add_thought(self, thought: str):
        """Add a thought/reasoning to the scratchpad"""
        self.thoughts.append({
            "step": self.current_step,
            "timestamp": datetime.now().isoformat(),
            "content": thought
        })
    
    def add_action(self, action: str, inputs: Dict[str, Any] = None):
        """Add an action to the scratchpad"""
        self.actions.append({
            "step": self.current_step,
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "inputs": inputs or {}
        })
    
    def add_result(self, result: Any):
        """Add a result to the scratchpad"""
        self.results.append({
            "step": self.current_step,
            "timestamp": datetime.now().isoformat(),
            "content": str(result)
        })
        self.current_step += 1
    
    def get_formatted_scratchpad(self) -> str:
        """Get formatted scratchpad for prompt injection"""
        formatted = []
        
        for i in range(self.current_step):
            step_content = []
            
            # Add observations for this step
            step_observations = [obs for obs in self.observations if obs["step"] == i]
            for obs in step_observations:
                step_content.append(f"Observation: {obs['content']}")
            
            # Add thoughts for this step
            step_thoughts = [thought for thought in self.thoughts if thought["step"] == i]
            for thought in step_thoughts:
                step_content.append(f"Thought: {thought['content']}")
            
            # Add actions for this step
            step_actions = [action for action in self.actions if action["step"] == i]
            for action in step_actions:
                step_content.append(f"Action: {action['action']}")
                if action["inputs"]:
                    step_content.append(f"Action Input: {action['inputs']}")
            
            # Add results for this step
            step_results = [result for result in self.results if result["step"] == i]
            for result in step_results:
                step_content.append(f"Result: {result['content']}")
            
            if step_content:
                formatted.append(f"Step {i + 1}:")
                formatted.extend([f"  {content}" for content in step_content])
        
        return "\n".join(formatted)
    
    def clear(self):
        """Clear the scratchpad"""
        self.observations.clear()
        self.thoughts.clear()
        self.actions.clear()
        self.results.clear()
        self.current_step = 0


class EnhancedAgentMixin:
    """Mixin to add enhanced agent capabilities"""
    
    def __init__(self):
        self.scratchpad = AgentScratchpad()
        self.performance_metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "average_response_time": 0.0,
            "last_call_time": None
        }
    
    def get_enhanced_prompt(self, base_prompt: str) -> str:
        """Enhance prompt with scratchpad context"""
        scratchpad_content = self.scratchpad.get_formatted_scratchpad()
        if scratchpad_content:
            return f"{base_prompt}\n\nPrevious reasoning:\n{scratchpad_content}\n\nBased on the above context, proceed with the task:"
        return base_prompt
