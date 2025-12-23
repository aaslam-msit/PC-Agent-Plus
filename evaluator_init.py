"""
Automated Evaluation Framework for PC-Agent+
"""

from .file_monitor import FileSystemMonitor
from .visual_checker import VisualStateChecker
from .process_verifier import ProcessVerifier


class HybridEvaluator:
    """Main evaluator combining multiple evaluation methods"""
    
    def __init__(self, config: dict):
        self.config = config
        self.weights = config.get('task_types', {})
        
        # Initialize evaluation components
        self.file_monitor = FileSystemMonitor(config)
        self.visual_checker = VisualStateChecker(config)
        self.process_verifier = ProcessVerifier(config)
        
        self.evaluation_history = []
        print("Hybrid Evaluator initialized")
    
    def evaluate_task(self, task_description: str, expected_outcome: dict, 
                     actual_outcome: dict) -> dict:
        """
        Evaluate task execution against expected outcome
        
        Args:
            task_description: Description of the task
            expected_outcome: Dictionary of expected outcomes
            actual_outcome: Dictionary of actual outcomes
            
        Returns:
            Dictionary with evaluation results
        """
        print(f"Evaluating task: {task_description[:50]}...")
        
        # Determine task type for weight selection
        task_type = self._classify_task_type(task_description)
        weights = self.weights.get(task_type, self.weights.get('gui_interactions', {}))
        
        # Run individual evaluations
        file_score = 0.0
        visual_score = 0.0
        process_score = 0.0
        
        if 'files' in expected_outcome:
            file_score = self.file_monitor.evaluate_files(
                expected_outcome['files'], 
                actual_outcome.get('files', [])
            )
        
        if 'visual_state' in expected_outcome:
            visual_score = self.visual_checker.evaluate_visual_state(
                expected_outcome['visual_state'],
                actual_outcome.get('visual_state')
            )
        
        if 'processes' in expected_outcome:
            process_score = self.process_verifier.evaluate_processes(
                expected_outcome['processes'],
                actual_outcome.get('processes', [])
            )
        
        # Calculate weighted score
        total_score = (
            weights.get('file_weight', 0.33) * file_score +
            weights.get('visual_weight', 0.33) * visual_score +
            weights.get('process_weight', 0.33) * process_score
        )
        
        # Determine pass/fail
        threshold = weights.get('threshold', 0.7)
        passed = total_score >= threshold
        
        # Create evaluation result
        result = {
            'task_description': task_description,
            'task_type': task_type,
            'scores': {
                'file': file_score,
                'visual': visual_score,
                'process': process_score,
                'total': total_score
            },
            'weights': {
                'file': weights.get('file_weight', 0.33),
                'visual': weights.get('visual_weight', 0.33),
                'process': weights.get('process_weight', 0.33)
            },
            'passed': passed,
            'threshold': threshold,
            'timestamp': self._get_timestamp()
        }
        
        # Store in history
        self.evaluation_history.append(result)
        
        print(f"Evaluation complete: {'PASS' if passed else 'FAIL'} "
              f"(score: {total_score:.2f})")
        
        return result
    
    def _classify_task_type(self, task_description: str) -> str:
        """Classify task type based on description"""
        desc_lower = task_description.lower()
        
        # Check for file operations
        file_keywords = ['save', 'create', 'delete', 'move', 'copy', 
                        'rename', 'export', 'import']
        if any(keyword in desc_lower for keyword in file_keywords):
            return 'file_operations'
        
        # Check for app management
        app_keywords = ['open', 'close', 'launch', 'exit', 'start', 
                       'quit', 'run', 'execute']
        if any(keyword in desc_lower for keyword in app_keywords):
            return 'app_management'
        
        # Check for cross-app workflows
        app_count = len([app for app in ['chrome', 'word', 'excel', 'outlook'] 
                        if app in desc_lower])
        if app_count > 1:
            return 'cross_app_workflows'
        
        # Default to GUI interactions
        return 'gui_interactions'
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_evaluation_stats(self) -> dict:
        """Get evaluation statistics"""
        if not self.evaluation_history:
            return {'total': 0, 'passed': 0, 'failed': 0, 'avg_score': 0}
        
        total = len(self.evaluation_history)
        passed = sum(1 for result in self.evaluation_history if result['passed'])
        avg_score = sum(result['scores']['total'] 
                       for result in self.evaluation_history) / total
        
        return {
            'total_evaluations': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': passed / total,
            'average_score': avg_score,
            'task_type_distribution': self._get_task_type_distribution()
        }
    
    def _get_task_type_distribution(self) -> dict:
        """Get distribution of task types evaluated"""
        distribution = {}
        for result in self.evaluation_history:
            task_type = result['task_type']
            distribution[task_type] = distribution.get(task_type, 0) + 1
        
        # Convert to percentages
        total = len(self.evaluation_history)
        if total > 0:
            distribution = {k: v/total for k, v in distribution.items()}
        
        return distribution


__all__ = ['HybridEvaluator', 'FileSystemMonitor', 'VisualStateChecker', 'ProcessVerifier']