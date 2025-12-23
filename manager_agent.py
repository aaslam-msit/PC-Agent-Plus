"""
Manager Agent for instruction decomposition and high-level task management
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class Subtask:
    """Represents a parameterized subtask"""
    id: str
    description: str
    parameters: Dict[str, Any]
    dependencies: List[str]
    expected_output: Optional[str] = None
    complexity: float = 0.5


class ManagerAgent:
    """Decomposes complex instructions into parameterized subtasks"""
    
    def __init__(self, model_client=None):
        self.model_client = model_client
        self.communication_hub = {}
        logger.info("Manager Agent initialized")
    
    def decompose_instruction(self, instruction: str) -> List[Subtask]:
        """
        Decompose complex instruction into subtasks
        
        Args:
            instruction: User instruction string
            
        Returns:
            List of parameterized subtasks
        """
        logger.info(f"Decomposing instruction: {instruction[:50]}...")
        
        # In production, this would use an LLM
        # For demo, we use rule-based decomposition
        subtasks = self._rule_based_decomposition(instruction)
        
        if self.model_client and len(subtasks) == 0:
            # Fallback to LLM decomposition
            subtasks = self._llm_based_decomposition(instruction)
        
        logger.info(f"Decomposed into {len(subtasks)} subtasks")
        return subtasks
    
    def _rule_based_decomposition(self, instruction: str) -> List[Subtask]:
        """Rule-based instruction decomposition"""
        subtasks = []
        
        # Example decomposition patterns
        if "search" in instruction.lower() and "excel" in instruction.lower():
            subtasks = [
                Subtask(
                    id="search_1",
                    description="Search for information on Chrome",
                    parameters={"query": "extract query from instruction"},
                    dependencies=[],
                    complexity=0.6
                ),
                Subtask(
                    id="excel_1",
                    description="Create Excel spreadsheet with results",
                    parameters={"data": "from search_1"},
                    dependencies=["search_1"],
                    complexity=0.7
                )
            ]
        elif "word" in instruction.lower() and "format" in instruction.lower():
            subtasks = [
                Subtask(
                    id="open_word",
                    description="Open Word document",
                    parameters={"file_path": "extract from instruction"},
                    dependencies=[],
                    complexity=0.3
                ),
                Subtask(
                    id="format_text",
                    description="Format text in Word",
                    parameters={"format_type": "bold/italic/underline"},
                    dependencies=["open_word"],
                    complexity=0.5
                )
            ]
        
        return subtasks
    
    def _llm_based_decomposition(self, instruction: str) -> List[Subtask]:
        """LLM-based instruction decomposition"""
        if not self.model_client:
            return []
        
        prompt = f"""
        Decompose this PC task instruction into subtasks:
        
        Instruction: {instruction}
        
        Output format (JSON):
        {{
            "subtasks": [
                {{
                    "id": "subtask_1",
                    "description": "description of subtask",
                    "parameters": {{"param1": "value1"}},
                    "dependencies": [],
                    "complexity": 0.5
                }}
            ]
        }}
        """
        
        try:
            response = self.model_client.generate(prompt)
            data = json.loads(response)
            
            subtasks = []
            for subtask_data in data.get("subtasks", []):
                subtask = Subtask(
                    id=subtask_data["id"],
                    description=subtask_data["description"],
                    parameters=subtask_data.get("parameters", {}),
                    dependencies=subtask_data.get("dependencies", []),
                    complexity=subtask_data.get("complexity", 0.5)
                )
                subtasks.append(subtask)
            
            return subtasks
            
        except Exception as e:
            logger.error(f"LLM decomposition failed: {e}")
            return []
    
    def update_communication_hub(self, subtask_id: str, output: Any):
        """Update communication hub with subtask output"""
        self.communication_hub[subtask_id] = output
        logger.debug(f"Updated hub: {subtask_id} = {output}")
    
    def get_parameter(self, parameter_name: str) -> Optional[Any]:
        """Get parameter value from communication hub"""
        return self.communication_hub.get(parameter_name)