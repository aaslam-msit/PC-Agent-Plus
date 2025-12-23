"""
Intelligent Router Module for dynamic model selection
"""

from .complexity_scorer import ComplexityScorer
from .model_selector import ModelSelector
from .budget_tracker import BudgetTracker


class RouterAgent:
    """Main router agent coordinating all routing components"""
    
    def __init__(self, config: dict):
        self.config = config
        self.complexity_scorer = ComplexityScorer(config)
        self.budget_tracker = BudgetTracker(config)
        self.model_selector = ModelSelector(config)
        
        self.routing_history = []
        print("Router Agent initialized")
    
    def select_model(self, subtask_description: str, context: dict = None) -> tuple:
        """
        Select appropriate model for a subtask
        
        Args:
            subtask_description: Description of the subtask
            context: Additional context information
            
        Returns:
            Tuple of (model_type, model_client, complexity_score)
        """
        # Calculate complexity
        complexity = self.complexity_scorer.calculate_complexity(
            subtask_description, context
        )
        
        # Check budget constraints
        budget_status = self.budget_tracker.check_budget_status()
        
        # Select model
        model_type, model_client = self.model_selector.select_model(
            complexity, budget_status
        )
        
        # Log routing decision
        self.routing_history.append({
            'subtask': subtask_description[:50],
            'complexity': complexity,
            'model_type': model_type,
            'budget_remaining': budget_status['remaining']
        })
        
        return model_type, model_client, complexity
    
    def update_routing_performance(self, subtask_description: str, 
                                 model_type: str, success: bool):
        """
        Update routing system based on performance
        
        Args:
            subtask_description: Subtask description
            model_type: Model type used
            success: Whether the task was successful
        """
        # Update complexity scorer
        self.complexity_scorer.update_model_performance(
            subtask_description, model_type, success
        )
        
        # Update budget
        if model_type != "rule":
            cost = self.model_selector.get_model_cost(model_type)
            self.budget_tracker.record_expense(cost)
        
        print(f"Updated routing: {model_type} {'succeeded' if success else 'failed'}")
    
    def get_routing_stats(self) -> dict:
        """Get routing statistics"""
        return {
            'total_decisions': len(self.routing_history),
            'model_distribution': self._calculate_model_distribution(),
            'avg_complexity': self._calculate_average_complexity(),
            'budget_used': self.budget_tracker.get_total_expenses(),
            'budget_remaining': self.budget_tracker.get_remaining_budget()
        }
    
    def _calculate_model_distribution(self) -> dict:
        """Calculate distribution of model usage"""
        distribution = {}
        for decision in self.routing_history:
            model_type = decision['model_type']
            distribution[model_type] = distribution.get(model_type, 0) + 1
        
        # Convert to percentages
        total = len(self.routing_history)
        if total > 0:
            distribution = {k: v/total for k, v in distribution.items()}
        
        return distribution
    
    def _calculate_average_complexity(self) -> float:
        """Calculate average complexity score"""
        if not self.routing_history:
            return 0.0
        
        total = sum(decision['complexity'] for decision in self.routing_history)
        return total / len(self.routing_history)


__all__ = ['RouterAgent', 'ComplexityScorer', 'ModelSelector', 'BudgetTracker']