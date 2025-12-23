"""
Decision Agent for step-by-step action decision making
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class Action:
    """Represents an executable action"""
    type: str  # click, type, select, drag, scroll, shortcut, stop
    parameters: Dict[str, any]
    confidence: float
    reasoning: str


class DecisionAgent:
    """Makes step-by-step decisions for subtask execution"""
    
    # Supported action types
    ACTION_TYPES = {
        "click": {"x", "y", "button"},
        "double_click": {"x", "y", "button"},
        "type": {"text", "x", "y"},
        "select": {"text", "start_x", "start_y", "end_x", "end_y"},
        "drag": {"start_x", "start_y", "end_x", "end_y"},
        "scroll": {"x", "y", "direction", "amount"},
        "shortcut": {"keys"},
        "stop": {}
    }
    
    def __init__(self, model_client=None):
        self.model_client = model_client
        self.action_history: List[Action] = []
        logger.info("Decision Agent initialized")
    
    def decide_next_action(self, subtask: str, progress: str, 
                          reflection: Optional[str] = None) -> Action:
        """
        Decide the next action to take
        
        Args:
            subtask: Current subtask description
            progress: Progress summary
            reflection: Reflection from previous action (if any)
            
        Returns:
            Action to execute
        """
        logger.info(f"Deciding next action for subtask: {subtask[:50]}...")
        
        context = f"""
        Current Subtask: {subtask}
        Progress: {progress}
        Previous Reflection: {reflection or 'No reflection'}
        Action History: {self._format_action_history()}
        """
        
        # Generate action using model or rule-based approach
        if self.model_client and self._requires_complex_reasoning(subtask):
            action = self._model_based_decision(context)
        else:
            action = self._rule_based_decision(context)
        
        self.action_history.append(action)
        logger.debug(f"Decided action: {action.type} (confidence: {action.confidence})")
        
        return action
    
    def _requires_complex_reasoning(self, subtask: str) -> bool:
        """Determine if subtask requires complex reasoning"""
        complex_keywords = [
            "analyze", "summarize", "compare", "extract", 
            "translate", "calculate", "format", "organize"
        ]
        
        subtask_lower = subtask.lower()
        return any(keyword in subtask_lower for keyword in complex_keywords)
    
    def _rule_based_decision(self, context: str) -> Action:
        """Rule-based action decision"""
        # Simple heuristic-based decision making
        if "click" in context.lower():
            # Extract coordinates from context if possible
            coords = self._extract_coordinates(context)
            if coords:
                return Action(
                    type="click",
                    parameters={"x": coords[0], "y": coords[1], "button": "left"},
                    confidence=0.8,
                    reasoning="Rule-based click on detected coordinates"
                )
        
        if "type" in context.lower():
            # Extract text to type
            text_match = re.search(r'type\s+["\'](.+?)["\']', context.lower())
            if text_match:
                return Action(
                    type="type",
                    parameters={"text": text_match.group(1)},
                    confidence=0.7,
                    reasoning="Rule-based text input"
                )
        
        # Default action
        return Action(
            type="stop",
            parameters={},
            confidence=0.5,
            reasoning="No clear action identified"
        )
    
    def _model_based_decision(self, context: str) -> Action:
        """Model-based action decision using LLM"""
        if not self.model_client:
            return self._rule_based_decision(context)
        
        prompt = f"""
        Based on the context below, decide the next GUI action to take.
        
        Context:
        {context}
        
        Available action types: {list(self.ACTION_TYPES.keys())}
        
        Respond in JSON format:
        {{
            "action": "action_type",
            "parameters": {{"param1": "value1"}},
            "reasoning": "step-by-step reasoning",
            "confidence": 0.95
        }}
        """
        
        try:
            response = self.model_client.generate(prompt)
            # Parse JSON response (simplified)
            import json
            data = json.loads(response)
            
            return Action(
                type=data["action"],
                parameters=data["parameters"],
                confidence=data["confidence"],
                reasoning=data["reasoning"]
            )
            
        except Exception as e:
            logger.error(f"Model-based decision failed: {e}")
            return self._rule_based_decision(context)
    
    def _extract_coordinates(self, text: str) -> Optional[Tuple[int, int]]:
        """Extract coordinates from text using regex"""
        pattern = r'\((\d+),\s*(\d+)\)'
        matches = re.findall(pattern, text)
        
        if matches:
            x, y = map(int, matches[0])
            return (x, y)
        
        return None
    
    def _format_action_history(self) -> str:
        """Format action history for context"""
        if not self.action_history:
            return "No previous actions"
        
        recent = self.action_history[-5:]  # Last 5 actions
        formatted = []
        for i, action in enumerate(recent, 1):
            formatted.append(f"{i}. {action.type}: {action.reasoning[:50]}...")
        
        return "\n".join(formatted)
    
    def validate_action(self, action: Action) -> bool:
        """Validate action parameters"""
        if action.type not in self.ACTION_TYPES:
            logger.warning(f"Invalid action type: {action.type}")
            return False
        
        required_params = self.ACTION_TYPES[action.type]
        missing_params = required_params - set(action.parameters.keys())
        
        if missing_params:
            logger.warning(f"Missing parameters for {action.type}: {missing_params}")
            return False
        
        return True