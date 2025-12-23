"""
Main orchestrator for PC-Agent+ framework
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from loguru import logger

from .agents import ManagerAgent, ProgressAgent, DecisionAgent, ReflectionAgent
from .router import RouterAgent
from .evaluator import HybridEvaluator
from utils.config_loader import ConfigLoader


@dataclass
class ExecutionResult:
    """Result of task execution"""
    success: bool
    subtask_results: List[Dict]
    total_cost: float
    total_time: float
    models_used: Dict[str, int]
    evaluation_scores: Optional[Dict] = None
    error_message: Optional[str] = None


class PCAgentPlus:
    """Main PC-Agent+ orchestrator class"""
    
    def __init__(self, config_path: str = "config/local.yaml"):
        # Load configuration
        self.config = ConfigLoader.load_config(config_path)
        logger.info(f"PC-Agent+ initialized with config: {config_path}")
        
        # Initialize components
        self._initialize_components()
        
        # Execution tracking
        self.execution_history = []
        self.current_task = None
    
    def _initialize_components(self):
        """Initialize all framework components"""
        # Initialize agents
        self.manager_agent = ManagerAgent()
        self.progress_agent = ProgressAgent()
        self.decision_agent = DecisionAgent()
        self.reflection_agent = ReflectionAgent()
        
        # Initialize router
        self.router_agent = RouterAgent(self.config)
        
        # Initialize evaluator
        self.evaluator = HybridEvaluator(self.config)
        
        logger.info("All components initialized")
    
    def execute(self, instruction: str, budget: Optional[float] = None, 
                mode: str = "balanced") -> ExecutionResult:
        """
        Execute a complex PC task
        
        Args:
            instruction: User instruction to execute
            budget: Budget for this task (overrides config)
            mode: Execution mode (cost_saving, performance, balanced)
            
        Returns:
            Execution result
        """
        logger.info(f"Starting execution: {instruction[:50]}...")
        start_time = time.time()
        
        # Set execution mode
        self.router_agent.config['router']['mode'] = mode
        
        # Override budget if specified
        if budget is not None:
            self.router_agent.budget_tracker.daily_budget = budget
        
        # Track execution
        self.current_task = {
            'instruction': instruction,
            'start_time': start_time,
            'mode': mode,
            'budget': budget
        }
        
        subtask_results = []
        models_used = {}
        total_cost = 0.0
        
        try:
            # Step 1: Decompose instruction
            subtasks = self.manager_agent.decompose_instruction(instruction)
            logger.info(f"Decomposed into {len(subtasks)} subtasks")
            
            # Step 2: Execute each subtask
            for i, subtask in enumerate(subtasks, 1):
                logger.info(f"Executing subtask {i}/{len(subtasks)}: {subtask.description}")
                
                subtask_result = self._execute_subtask(subtask)
                subtask_results.append(subtask_result)
                
                # Track model usage
                model_type = subtask_result.get('model_type', 'unknown')
                models_used[model_type] = models_used.get(model_type, 0) + 1
                
                # Track cost
                total_cost += subtask_result.get('cost', 0)
                
                # Update communication hub with subtask output
                if subtask_result.get('success'):
                    output = subtask_result.get('output')
                    if output:
                        self.manager_agent.update_communication_hub(subtask.id, output)
                
                # Check if we should continue
                if not subtask_result.get('success') and not self.config.get('continue_on_failure', False):
                    logger.warning(f"Subtask failed, aborting execution")
                    break
            
            # Step 3: Evaluate overall execution
            evaluation_result = self._evaluate_overall_execution(
                instruction, subtask_results
            )
            
            # Determine overall success
            overall_success = all(r.get('success', False) for r in subtask_results)
            
            execution_result = ExecutionResult(
                success=overall_success,
                subtask_results=subtask_results,
                total_cost=total_cost,
                total_time=time.time() - start_time,
                models_used=models_used,
                evaluation_scores=evaluation_result
            )
            
        except Exception as e:
            logger.error(f"Execution failed with error: {e}")
            execution_result = ExecutionResult(
                success=False,
                subtask_results=subtask_results,
                total_cost=total_cost,
                total_time=time.time() - start_time,
                models_used=models_used,
                error_message=str(e)
            )
        
        # Store in history
        self.execution_history.append({
            'task': self.current_task,
            'result': asdict(execution_result),
            'timestamp': time.time()
        })
        
        self.current_task = None
        logger.info(f"Execution completed: {'SUCCESS' if execution_result.success else 'FAILURE'}")
        
        return execution_result
    
    def _execute_subtask(self, subtask) -> Dict:
        """Execute a single subtask"""
        subtask_start = time.time()
        
        try:
            # Select model for this subtask
            model_type, model_client, complexity = self.router_agent.select_model(
                subtask.description
            )
            
            # Set model for decision agent
            self.decision_agent.model_client = model_client
            
            # Execute subtask
            result = self._execute_with_model(
                subtask, model_type, model_client
            )
            
            # Update router performance
            self.router_agent.update_routing_performance(
                subtask.description, model_type, result['success']
            )
            
            # Calculate cost
            cost = self._calculate_subtask_cost(model_type, complexity)
            
            result.update({
                'model_type': model_type,
                'complexity': complexity,
                'cost': cost,
                'execution_time': time.time() - subtask_start
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Subtask execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - subtask_start
            }
    
    def _execute_with_model(self, subtask, model_type: str, model_client) -> Dict:
        """Execute subtask using specified model"""
        # This is a simplified version
        # In production, this would coordinate between all agents
        
        if model_type == 'rule':
            # Rule-based execution
            return self._execute_rule_based(subtask)
        else:
            # Model-based execution
            return self._execute_model_based(subtask, model_client)
    
    def _execute_rule_based(self, subtask) -> Dict:
        """Execute using rule-based approach"""
        # Simple rule-based execution
        # In production, this would use a proper rule engine
        
        description = subtask.description.lower()
        
        if 'click' in description:
            return {
                'success': True,
                'output': 'click_executed',
                'action': 'click'
            }
        elif 'type' in description:
            return {
                'success': True,
                'output': 'text_typed',
                'action': 'type'
            }
        elif 'open' in description:
            return {
                'success': True,
                'output': 'application_opened',
                'action': 'open'
            }
        else:
            return {
                'success': False,
                'output': 'no_matching_rule',
                'action': 'unknown'
            }
    
    def _execute_model_based(self, subtask, model_client) -> Dict:
        """Execute using model-based approach"""
        try:
            # Use model to generate action sequence
            prompt = f"""
            Execute this PC task: {subtask.description}
            
            Available actions: click, type, select, drag, scroll, shortcut, stop
            
            Respond with action sequence in JSON format.
            """
            
            response = model_client.generate(prompt)
            
            # Parse response (simplified)
            actions = json.loads(response) if '[' in response else []
            
            return {
                'success': len(actions) > 0,
                'output': actions,
                'action_count': len(actions)
            }
            
        except Exception as e:
            logger.error(f"Model-based execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_subtask_cost(self, model_type: str, complexity: float) -> float:
        """Calculate cost for subtask execution"""
        model_config = self.config.get('models', {}).get(model_type, {})
        base_cost = model_config.get('cost_per_1k_tokens', 0)
        
        # Estimate token count based on complexity
        estimated_tokens = complexity * 1000
        
        return base_cost * (estimated_tokens / 1000)
    
    def _evaluate_overall_execution(self, instruction: str, 
                                  subtask_results: List[Dict]) -> Dict:
        """Evaluate overall execution"""
        if not self.config.get('evaluation', {}).get('enable_auto_eval', True):
            return {}
        
        # Create expected outcome based on instruction
        expected_outcome = self._create_expected_outcome(instruction)
        
        # Create actual outcome from subtask results
        actual_outcome = self._create_actual_outcome(subtask_results)
        
        # Run evaluation
        evaluation_result = self.evaluator.evaluate_task(
            instruction, expected_outcome, actual_outcome
        )
        
        return evaluation_result
    
    def _create_expected_outcome(self, instruction: str) -> Dict:
        """Create expected outcome based on instruction"""
        # Simplified version
        # In production, this would use NLP to parse expectations
        
        instruction_lower = instruction.lower()
        
        expected = {
            'files': [],
            'processes': [],
            'visual_state': {}
        }
        
        if 'save' in instruction_lower or 'create' in instruction_lower:
            expected['files'].append({'operation': 'created'})
        
        if 'open' in instruction_lower:
            # Extract application name
            apps = ['chrome', 'word', 'excel', 'notepad']
            for app in apps:
                if app in instruction_lower:
                    expected['processes'].append({
                        'name': f'{app}.exe',
                        'state': 'running'
                    })
        
        return expected
    
    def _create_actual_outcome(self, subtask_results: List[Dict]) -> Dict:
        """Create actual outcome from subtask results"""
        # Simplified version
        # In production, this would gather actual system state
        
        return {
            'files': ['temp_output.txt'],  # Example
            'processes': ['chrome.exe'],   # Example
            'visual_state': {}             # Would contain screenshots
        }
    
    def get_execution_stats(self) -> Dict:
        """Get execution statistics"""
        if not self.execution_history:
            return {'total_executions': 0, 'success_rate': 0}
        
        total = len(self.execution_history)
        successful = sum(1 for item in self.execution_history 
                        if item['result']['success'])
        
        total_cost = sum(item['result']['total_cost'] 
                        for item in self.execution_history)
        
        total_time = sum(item['result']['total_time'] 
                        for item in self.execution_history)
        
        # Model usage distribution
        model_usage = {}
        for item in self.execution_history:
            for model, count in item['result']['models_used'].items():
                model_usage[model] = model_usage.get(model, 0) + count
        
        return {
            'total_executions': total,
            'successful_executions': successful,
            'success_rate': successful / total if total > 0 else 0,
            'total_cost': total_cost,
            'average_cost': total_cost / total if total > 0 else 0,
            'total_time': total_time,
            'average_time': total_time / total if total > 0 else 0,
            'model_usage': model_usage
        }
    
    def save_execution_log(self, filepath: str = "execution_log.json"):
        """Save execution history to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.execution_history, f, indent=2, default=str)
            logger.info(f"Execution log saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving execution log: {e}")
    
    def load_execution_log(self, filepath: str = "execution_log.json"):
        """Load execution history from file"""
        try:
            with open(filepath, 'r') as f:
                self.execution_history = json.load(f)
            logger.info(f"Execution log loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading execution log: {e}")