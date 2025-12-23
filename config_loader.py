"""
Configuration loader for PC-Agent+
"""

import yaml
import os
from typing import Dict, Any
from loguru import logger


class ConfigLoader:
    """Loads and manages configuration files"""
    
    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        # Check if file exists
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found: {config_path}")
            logger.info("Creating default configuration...")
            return ConfigLoader._create_default_config()
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Configuration loaded from {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            return ConfigLoader._create_default_config()
    
    @staticmethod
    def _create_default_config() -> Dict[str, Any]:
        """Create default configuration"""
        return {
            'models': {
                'premium': {
                    'name': 'gpt-4o',
                    'cost_per_1k_tokens': 0.015,
                    'enabled': True
                },
                'mid': {
                    'name': 'claude-3.5-sonnet',
                    'cost_per_1k_tokens': 0.008,
                    'enabled': True
                },
                'open': {
                    'name': 'qwen2.5-vl-72b',
                    'cost_per_1k_tokens': 0.000,
                    'enabled': True
                },
                'rule': {
                    'name': 'rule-based',
                    'cost_per_1k_tokens': 0.000,
                    'enabled': True
                }
            },
            'thresholds': {
                'premium': 0.8,
                'mid': 0.5,
                'open': 0.2
            },
            'budget': {
                'daily_limit': 10.0,
                'warning_threshold': 2.0,
                'critical_threshold': 0.5
            },
            'router': {
                'mode': 'balanced'
            }
        }
    
    @staticmethod
    def save_config(config: Dict[str, Any], config_path: str):
        """
        Save configuration to YAML file
        
        Args:
            config: Configuration dictionary
            config_path: Path to save configuration
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            logger.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            logger.error(f"Error saving config to {config_path}: {e}")
    
    @staticmethod
    def merge_configs(base_config: Dict, override_config: Dict) -> Dict:
        """
        Merge two configurations, with override taking precedence
        
        Args:
            base_config: Base configuration
            override_config: Configuration to merge on top
            
        Returns:
            Merged configuration
        """
        merged = base_config.copy()
        
        for key, value in override_config.items():
            if (key in merged and isinstance(merged[key], dict) 
                and isinstance(value, dict)):
                merged[key] = ConfigLoader.merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    @staticmethod
    def validate_config(config: Dict) -> bool:
        """
        Validate configuration structure
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_sections = ['models', 'thresholds', 'budget']
        
        for section in required_sections:
            if section not in config:
                logger.error(f"Missing required section: {section}")
                return False
        
        # Validate models section
        models = config.get('models', {})
        required_models = ['premium', 'mid', 'open', 'rule']
        
        for model in required_models:
            if model not in models:
                logger.warning(f"Missing model configuration: {model}")
        
        # Validate thresholds
        thresholds = config.get('thresholds', {})
        for threshold in ['premium', 'mid', 'open']:
            if threshold not in thresholds:
                logger.warning(f"Missing threshold: {threshold}")
            else:
                value = thresholds[threshold]
                if not 0 <= value <= 1:
                    logger.error(f"Threshold {threshold} must be between 0 and 1")
                    return False
        
        # Validate budget
        budget = config.get('budget', {})
        for key in ['daily_limit', 'warning_threshold', 'critical_threshold']:
            if key not in budget:
                logger.warning(f"Missing budget key: {key}")
            else:
                if budget[key] < 0:
                    logger.error(f"Budget {key} cannot be negative")
                    return False
        
        logger.info("Configuration validation passed")
        return True