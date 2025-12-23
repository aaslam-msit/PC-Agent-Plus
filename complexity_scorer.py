"""
Complexity scoring for task routing
"""

import re
from typing import Dict, List, Optional
import numpy as np
from loguru import logger


class ComplexityScorer:
    """Calculates complexity scores for tasks"""
    
    def __init__(self, config: dict):
        self.config = config
        self.weights = config.get('complexity_weights', {})
        self.history = []  # Store historical scores for learning
        logger.info("Complexity Scorer initialized")
    
    def calculate_complexity(self, task_description: str, 
                           context: Optional[Dict] = None) -> float:
        """
        Calculate complexity score (0-1) for a task
        
        Args:
            task_description: Description of the task
            context: Additional context information
            
        Returns:
            Complexity score between 0 and 1
        """
        logger.debug(f"Calculating complexity for: {task_description[:50]}...")
        
        # Extract features from task description
        features = self._extract_features(task_description, context)
        
        # Calculate weighted score
        score = self._calculate_weighted_score(features)
        
        # Apply sigmoid normalization to keep in 0-1 range
        normalized_score = self._sigmoid_normalize(score)
        
        # Clip to valid range
        normalized_score = max(0.0, min(1.0, normalized_score))
        
        # Store in history for learning
        self.history.append({
            'description': task_description,
            'features': features,
            'score': normalized_score,
            'context': context
        })
        
        logger.debug(f"Complexity score: {normalized_score:.3f}")
        return normalized_score
    
    def _extract_features(self, description: str, context: Optional[Dict]) -> Dict:
        """Extract complexity features from task description"""
        description_lower = description.lower()
        
        features = {
            'word_count': len(description.split()),
            'app_count': self._count_apps(description_lower),
            'has_inter_app_dependency': self._has_inter_app_dependency(description_lower),
            'requires_text_processing': self._requires_text_processing(description_lower),
            'requires_navigation': self._requires_navigation(description_lower),
            'requires_data_manipulation': self._requires_data_manipulation(description_lower),
            'step_count_estimate': self._estimate_step_count(description_lower),
            'has_conditional_logic': self._has_conditional_logic(description_lower),
        }
        
        # Add context features if available
        if context:
            features.update({
                'historical_success_rate': context.get('historical_success_rate', 0.5),
                'similar_tasks_complexity': context.get('similar_tasks_complexity', 0.5),
                'user_skill_level': context.get('user_skill_level', 0.5),
            })
        
        return features
    
    def _calculate_weighted_score(self, features: Dict) -> float:
        """Calculate weighted complexity score"""
        # Default weights if not configured
        default_weights = {
            'word_count': 0.1,
            'app_count': 0.2,
            'has_inter_app_dependency': 0.3,
            'requires_text_processing': 0.15,
            'requires_navigation': 0.1,
            'requires_data_manipulation': 0.2,
            'step_count_estimate': 0.15,
            'has_conditional_logic': 0.25,
            'historical_success_rate': 0.2,
        }
        
        weights = {**default_weights, **self.weights}
        
        score = 0.0
        total_weight = 0.0
        
        for feature_name, weight in weights.items():
            if feature_name in features:
                feature_value = features[feature_name]
                
                # Normalize feature values
                normalized_value = self._normalize_feature(feature_name, feature_value)
                
                score += normalized_value * weight
                total_weight += weight
        
        # Normalize by total weight
        if total_weight > 0:
            score /= total_weight
        
        return score
    
    def _normalize_feature(self, feature_name: str, value) -> float:
        """Normalize feature value to 0-1 range"""
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        elif isinstance(value, (int, float)):
            # Feature-specific normalization
            if feature_name == 'word_count':
                return min(value / 50, 1.0)
            elif feature_name == 'app_count':
                return min(value / 5, 1.0)
            elif feature_name == 'step_count_estimate':
                return min(value / 20, 1.0)
            elif feature_name == 'historical_success_rate':
                return 1.0 - value  # Lower success rate = higher complexity
            else:
                return min(value, 1.0)
        else:
            return 0.5
    
    def _sigmoid_normalize(self, x: float) -> float:
        """Apply sigmoid function for normalization"""
        return 1 / (1 + np.exp(-10 * (x - 0.5)))
    
    def _count_apps(self, description: str) -> int:
        """Count number of applications mentioned"""
        apps = ['chrome', 'word', 'excel', 'notepad', 'calculator', 
                'outlook', 'explorer', 'paint', 'powerpoint']
        
        return sum(1 for app in apps if app in description)
    
    def _has_inter_app_dependency(self, description: str) -> bool:
        """Check if task involves multiple apps with dependencies"""
        patterns = [
            r'from.*to.*',
            r'copy.*from.*to.*',
            r'import.*into.*',
            r'export.*from.*to.*',
            r'search.*and.*create.*',
        ]
        
        return any(re.search(pattern, description) for pattern in patterns)
    
    def _requires_text_processing(self, description: str) -> bool:
        """Check if task requires text processing"""
        keywords = ['edit', 'format', 'bold', 'italic', 'underline', 
                   'align', 'paragraph', 'font', 'style']
        
        return any(keyword in description for keyword in keywords)
    
    def _requires_navigation(self, description: str) -> bool:
        """Check if task requires GUI navigation"""
        keywords = ['open', 'close', 'navigate', 'go to', 'click', 
                   'select', 'find', 'search', 'browse']
        
        return any(keyword in description for keyword in keywords)
    
    def _requires_data_manipulation(self, description: str) -> bool:
        """Check if task requires data manipulation"""
        keywords = ['calculate', 'sum', 'average', 'sort', 'filter',
                   'analyze', 'graph', 'chart', 'formula', 'function']
        
        return any(keyword in description for keyword in keywords)
    
    def _estimate_step_count(self, description: str) -> int:
        """Estimate number of steps required"""
        # Simple heuristic based on sentence structure
        sentences = re.split(r'[.!?]+', description)
        steps = len(sentences)
        
        # Count action verbs
        action_verbs = ['click', 'type', 'open', 'close', 'save', 
                       'create', 'delete', 'move', 'copy', 'paste']
        
        verb_count = sum(1 for verb in action_verbs if verb in description)
        
        return max(steps, verb_count)
    
    def _has_conditional_logic(self, description: str) -> bool:
        """Check if task involves conditional logic"""
        keywords = ['if', 'then', 'else', 'when', 'unless', 
                   'depending on', 'based on', 'condition']
        
        return any(keyword in description for keyword in keywords)
    
    def update_model_performance(self, task_description: str, 
                               model_type: str, success: bool):
        """Update scorer based on model performance"""
        # In production: Update weights based on performance
        # For demo: Simple logging
        logger.info(f"Updating scorer: {model_type} {'succeeded' if success else 'failed'}")
        
        # Keep only recent history
        if len(self.history) > 1000:
            self.history = self.history[-1000:]