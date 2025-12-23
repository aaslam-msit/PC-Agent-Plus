"""
PC-Agent+ Core Framework
Enhanced hierarchical multi-agent collaboration system
"""

__version__ = "1.0.0"
__author__ = "Ambreen Aslam"
__email__ = "ambreengillanii@gmail.com"

from .orchestrator import PCAgentPlus
from .agents import ManagerAgent, ProgressAgent, DecisionAgent, ReflectionAgent
from .router import RouterAgent
from .evaluator import HybridEvaluator

__all__ = [
    'PCAgentPlus',
    'ManagerAgent',
    'ProgressAgent',
    'DecisionAgent',
    'ReflectionAgent',
    'RouterAgent',
    'HybridEvaluator',
]