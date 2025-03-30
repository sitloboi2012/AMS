"""
Capability Registry Module

This module provides a registry for agent capabilities and a semantic matching system
for determining which capabilities are required for a given task using LLM.
"""

import json
import logging
from typing import Dict, Any, List, Set, Optional

import openai

from .models import AgentMetadata

logger = logging.getLogger(__name__)

# Type for task analysis result
TaskAnalysisResult = Dict[str, Any]

class CapabilityRegistry:
    """
    Registry for agent capabilities with semantic matching.
    
    This class manages the registration of capabilities and provides
    methods to match capabilities to tasks using LLM-based semantic matching.
    """
    
    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """
        Initialize a capability registry.
        
        Args:
            llm_config: Configuration for the LLM used for capability matching
        """
        self.capabilities: Dict[str, Dict[str, Any]] = {}
        self.llm_config = llm_config or {
            "model": "gpt-4o",
            "temperature": 0.1
        }
    
    def register_capability(
        self, 
        capability_name: str, 
        description: str,
        examples: Optional[List[str]] = None
    ) -> None:
        """
        Register a new capability.
        
        Args:
            capability_name: The name of the capability
            description: Detailed description of what the capability does
            examples: Optional list of example tasks that would require this capability
        """
        if capability_name in self.capabilities:
            logger.warning(f"Capability '{capability_name}' is already registered. Overwriting.")
        
        self.capabilities[capability_name] = {
            "description": description,
            "examples": examples or []
        }
        
        logger.info(f"Registered capability: {capability_name}")
    
    def unregister_capability(self, capability_name: str) -> bool:
        """
        Unregister a capability.
        
        Args:
            capability_name: The name of the capability to unregister
            
        Returns:
            True if the capability was found and removed, False otherwise
        """
        if capability_name in self.capabilities:
            del self.capabilities[capability_name]
            logger.info(f"Unregistered capability: {capability_name}")
            return True
        
        logger.warning(f"Capability '{capability_name}' not found in registry.")
        return False
    
    def get_all_capabilities(self) -> List[str]:
        """
        Get a list of all registered capabilities.
        
        Returns:
            List of capability names
        """
        return list(self.capabilities.keys())
    
    def get_capability_description(self, capability_name: str) -> Optional[str]:
        """
        Get the description of a capability.
        
        Args:
            capability_name: The name of the capability
            
        Returns:
            The description if the capability exists, None otherwise
        """
        if capability_name in self.capabilities:
            return self.capabilities[capability_name]["description"]
        return None
    
    async def analyze_capabilities_with_llm(
        self, 
        task: str, 
        task_analysis: Optional[TaskAnalysisResult] = None
    ) -> Dict[str, float]:
        """
        Analyze which capabilities are needed for a task using LLM.
        
        Args:
            task: The task description
            task_analysis: Optional additional task analysis information
            
        Returns:
            Dictionary mapping capability names to relevance scores (0-1)
        """
        if not self.capabilities:
            logger.warning("No capabilities registered. Cannot analyze task requirements.")
            return {}
        
        # Create capability descriptions for the prompt
        capability_descriptions = "\n".join([
            f"- {name}: {data['description']}" 
            for name, data in self.capabilities.items()
        ])
        
        # Create the system prompt
        system_prompt = f"""
        You are a task analyzer that identifies which capabilities are required for a given task.
        Analyze the task and determine which of the following capabilities are needed to complete it.

        Available capabilities:
        {capability_descriptions}

        For each capability, assign a score between 0.0 and 1.0:
        - 0.0: Not required at all for this task
        - 0.1-0.3: Slightly relevant
        - 0.4-0.6: Moderately relevant
        - 0.7-0.9: Highly relevant
        - 1.0: Essential, cannot complete the task without this capability

        Return your analysis as a JSON object with capability names as keys and scores as values.
        Example: {{"text_generation": 0.9, "research": 0.7, "code_generation": 0.0}}
        """
        
        # Prepare the user prompt
        user_prompt = f"Task: {task}"
        if task_analysis:
            # Include any additional task analysis if available
            user_prompt += f"\n\nAdditional analysis: {json.dumps(task_analysis, indent=2)}"
        
        try:
            response = openai.chat.completions.create(
                model=self.llm_config.get("model", "gpt-4o"),
                temperature=self.llm_config.get("temperature", 0.1),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extract the JSON response
            content = response.choices[0].message.content
            capability_scores = {}
            
            try:
                capability_scores = json.loads(content)
                
                # Validate the scores - ensure they're between 0 and 1
                for capability, score in capability_scores.items():
                    if not isinstance(score, (int, float)) or score < 0 or score > 1:
                        logger.warning(f"Invalid score for capability '{capability}': {score}. Setting to 0.0")
                        capability_scores[capability] = 0.0
                
                # Filter out capabilities that aren't registered
                capability_scores = {
                    name: score for name, score in capability_scores.items() 
                    if name in self.capabilities
                }
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response as JSON: {content}")
                # Extract scores using a fallback approach if JSON parsing fails
                capability_scores = self._extract_scores_from_text(content)
            
            logger.info(f"Capability analysis for task: {capability_scores}")
            return capability_scores
            
        except Exception as e:
            logger.error(f"Error analyzing task with LLM: {str(e)}")
            return {}
    
    def _extract_scores_from_text(self, text: str) -> Dict[str, float]:
        """
        Extract capability scores from free-form text when JSON parsing fails.
        
        Args:
            text: The text to parse
            
        Returns:
            Dictionary of capability names to scores
        """
        scores = {}
        
        # Look for patterns like "capability_name: 0.7" or "capability_name - 0.7"
        for capability_name in self.capabilities:
            for line in text.split('\n'):
                line = line.strip().lower()
                if capability_name.lower() in line:
                    # Try to extract a number from the line
                    import re
                    number_matches = re.findall(r'(\d+\.\d+|\d+)', line)
                    if number_matches:
                        try:
                            # Use the first number found
                            score = float(number_matches[0])
                            if 0 <= score <= 1:
                                scores[capability_name] = score
                                break
                        except ValueError:
                            pass
        
        return scores
    
    async def get_required_capabilities(
        self,
        task: str,
        task_analysis: Optional[TaskAnalysisResult] = None,
        threshold: float = 0.5
    ) -> Set[str]:
        """
        Get a set of capability names required for a task.
        
        Args:
            task: The task description
            task_analysis: Optional task analysis information
            threshold: Minimum score to consider a capability required (0-1)
            
        Returns:
            Set of required capability names
        """
        scores = await self.analyze_capabilities_with_llm(task, task_analysis)
        return {name for name, score in scores.items() if score >= threshold}
    
    def match_agent_to_capabilities(
        self,
        agent: AgentMetadata,
        required_capabilities: Set[str]
    ) -> Dict[str, bool]:
        """
        Check if an agent has the required capabilities.
        
        Args:
            agent: The agent metadata
            required_capabilities: Set of required capability names
            
        Returns:
            Dictionary mapping capability names to boolean (True if agent has it)
        """
        if not agent.capabilities:
            return {cap: False for cap in required_capabilities}
        
        agent_capability_names = {cap.name for cap in agent.capabilities}
        return {name: name in agent_capability_names for name in required_capabilities}
    
    async def filter_agents_by_capabilities(
        self,
        agents: List[AgentMetadata],
        task: str,
        task_analysis: Optional[TaskAnalysisResult] = None,
        threshold: float = 0.5,
        require_all: bool = False
    ) -> List[AgentMetadata]:
        """
        Filter a list of agents by task requirements.
        
        Args:
            agents: List of agents to filter
            task: The task description
            task_analysis: Optional task analysis information
            threshold: Minimum score to consider a capability required
            require_all: If True, agents must have all required capabilities
            
        Returns:
            Filtered and sorted list of agents
        """
        # Get required capabilities for this task
        required_capabilities = await self.get_required_capabilities(
            task, task_analysis, threshold
        )
        
        if not required_capabilities:
            logger.info("No specific capabilities required for this task")
            return agents
        
        logger.info(f"Required capabilities for task: {required_capabilities}")
        
        agent_matches = []
        
        for agent in agents:
            # Get capability matches for this agent
            matches = self.match_agent_to_capabilities(agent, required_capabilities)
            match_count = sum(1 for v in matches.values() if v)
            match_ratio = match_count / len(required_capabilities) if required_capabilities else 0
            
            # If we require all capabilities, skip agents that don't have them all
            if require_all and match_count < len(required_capabilities):
                continue
            
            # Otherwise, include the agent with its match metrics
            agent_matches.append((agent, match_count, match_ratio))
        
        # Sort by match count and then by match ratio
        agent_matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        filtered_agents = [agent for agent, _, _ in agent_matches]
        
        if not filtered_agents:
            logger.warning(f"No agents found matching required capabilities: {required_capabilities}")
            logger.info("Falling back to all available agents")
            return agents
        
        logger.info(f"Selected {len(filtered_agents)} agents based on capabilities")
        return filtered_agents


# Global instance of the registry with default settings
capability_registry = CapabilityRegistry()

# Register default capabilities
capability_registry.register_capability(
    "text_generation",
    "Ability to generate text responses based on prompts. This includes writing, explaining, describing, summarizing, and creating various forms of textual content.",
    ["Write a blog post about artificial intelligence", "Explain how photosynthesis works"]
)

capability_registry.register_capability(
    "code_generation",
    "Ability to write, understand, and debug code in various programming languages. Can implement algorithms, functions, and software solutions.",
    ["Write a Python function to sort a list", "Create a React component for a login form"]
)

capability_registry.register_capability(
    "research",
    "Ability to research information, gather data, and synthesize findings. Can analyze information from various sources to provide comprehensive answers.",
    ["Research the impact of climate change on agriculture", "Find information about quantum computing advances"]
)

capability_registry.register_capability(
    "tool_use",
    "Ability to use tools and APIs to accomplish tasks. Can interact with external systems, make API calls, and utilize specialized tools.",
    ["Use a weather API to get the forecast", "Search for information using a search engine"]
)

capability_registry.register_capability(
    "planning",
    "Ability to create detailed plans, strategies, and approaches for solving complex problems. Can break down tasks into manageable steps.",
    ["Create a project plan for developing a mobile app", "Outline steps for launching a marketing campaign"]
)

capability_registry.register_capability(
    "evaluation",
    "Ability to evaluate, assess, review, and provide critical feedback on content, code, or ideas. Can identify issues and suggest improvements.",
    ["Review this essay and provide feedback", "Evaluate the performance of this algorithm"]
) 