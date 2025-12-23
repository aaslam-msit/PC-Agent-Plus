"""
Model selection based on complexity and budget
"""

from typing import Dict, Tuple, Optional
from loguru import logger


class ModelSelector:
    """Selects appropriate model based on complexity and budget"""
    
    def __init__(self, config: dict):
        self.config = config
        self.models = self._initialize_models(config)
        self.thresholds = config.get('thresholds', {})
        self.fallback_order = config.get('fallback', {}).get('fallback_order', [])
        logger.info("Model Selector initialized")
    
    def select_model(self, complexity: float, budget_status: Dict) -> Tuple[str, object]:
        """
        Select model based on complexity and budget
        
        Args:
            complexity: Complexity score (0-1)
            budget_status: Current budget status
            
        Returns:
            Tuple of (model_type, model_client)
        """
        logger.debug(f"Selecting model for complexity: {complexity:.3f}")
        
        # Get thresholds from config
        premium_threshold = self.thresholds.get('premium', 0.8)
        mid_threshold = self.thresholds.get('mid', 0.5)
        open_threshold = self.thresholds.get('open', 0.2)
        
        # Check budget constraints
        budget_critical = budget_status.get('is_critical', False)
        budget_remaining = budget_status.get('remaining', float('inf'))
        
        # Model selection logic
        if complexity > premium_threshold and not budget_critical:
            if self._can_afford_model('premium', budget_remaining):
                return 'premium', self.models['premium']
        
        if complexity > mid_threshold:
            if self._can_afford_model('mid', budget_remaining):
                return 'mid', self.models['mid']
            elif not budget_critical:
                # Fallback to premium if we can afford it
                if self._can_afford_model('premium', budget_remaining):
                    return 'premium', self.models['premium']
        
        if complexity > open_threshold:
            if self._can_afford_model('open', budget_remaining):
                return 'open', self.models['open']
            else:
                # Fallback to rule-based
                return 'rule', self.models['rule']
        
        # Default to rule-based
        return 'rule', self.models['rule']
    
    def _initialize_models(self, config: dict) -> Dict[str, object]:
        """Initialize model clients"""
        # In production, these would be actual model clients
        # For demo, we use mock objects
        models = {}
        
        model_configs = config.get('models', {})
        
        for model_type, model_config in model_configs.items():
            if model_config.get('enabled', False):
                # Create mock model client
                models[model_type] = self._create_mock_client(model_type, model_config)
                logger.info(f"Initialized {model_type} model")
        
        # Ensure at least rule-based model is available
        if 'rule' not in models:
            models['rule'] = self._create_mock_client('rule', {})
        
        return models
    
    def _create_mock_client(self, model_type: str, config: dict):
        """Create mock model client for demonstration"""
        class MockClient:
            def __init__(self, model_type, config):
                self.model_type = model_type
                self.config = config
            
            def generate(self, prompt, **kwargs):
                # Mock response based on model type
                if model_type == 'premium':
                    return f"[GPT-4o] Processed: {prompt[:50]}..."
                elif model_type == 'mid':
                    return f"[Claude-3.5] Processed: {prompt[:50]}..."
                elif model_type == 'open':
                    return f"[Qwen2.5-VL] Processed: {prompt[:50]}..."
                else:
                    return f"[Rule-based] Executing rule for: {prompt[:50]}..."
            
            def get_cost(self, prompt):
                # Mock cost calculation
                token_count = len(prompt.split()) * 1.3
                cost_per_token = config.get('cost_per_1k_tokens', 0) / 1000
                return token_count * cost_per_token
        
        return MockClient(model_type, config)
    
    def _can_afford_model(self, model_type: str, budget_remaining: float) -> bool:
        """Check if we can afford to use this model"""
        model_config = self.config.get('models', {}).get(model_type, {})
        min_cost = model_config.get('min_cost_per_call', 0.001)
        
        return budget_remaining >= min_cost
    
    def get_model_cost(self, model_type: str) -> float:
        """Get cost for using a model"""
        model_config = self.config.get('models', {}).get(model_type, {})
        return model_config.get('cost_per_1k_tokens', 0)
    
    def get_model_info(self, model_type: str) -> Dict:
        """Get information about a model"""
        return self.config.get('models', {}).get(model_type, {})
    
    def get_available_models(self) -> list:
        """Get list of available models"""
        return list(self.models.keys())
    
    def fallback_model(self, current_model: str) -> Optional[str]:
        """Get fallback model for the current model"""
        if current_model not in self.fallback_order:
            return None
        
        current_index = self.fallback_order.index(current_model)
        if current_index < len(self.fallback_order) - 1:
            return self.fallback_order[current_index + 1]
        
        return None