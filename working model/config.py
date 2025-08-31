"""
Configuration management for GHCS application.
Handles service availability and dependency isolation.
"""
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class Config:
    """Configuration class for managing service availability and settings."""
    
    def __init__(self):
        self.settings = self._load_default_settings()
        self._load_environment_overrides()
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """Load default configuration settings."""
        return {
            'AI_SERVICE_ENABLED': True,
            'BLOCKCHAIN_SERVICE_ENABLED': True,
            'AI_MODEL_NAME': 'gemini-2.5-flash',
            'API_KEY_FILE': 'api_key.txt',
            'DATA_FILE': 'ghcs_data.json',
            'SECRET_KEY': 'a_very_secret_and_secure_key_for_hackout25',
            'LOG_LEVEL': 'INFO',
            'BLOCKCHAIN_NETWORK': 'development',  # development, testnet, mainnet
            'BROWNIE_ENABLED': True,  # Enabled in task 2
        }
    
    def _load_environment_overrides(self):
        """Load configuration overrides from environment variables."""
        env_mappings = {
            'GHCS_AI_ENABLED': 'AI_SERVICE_ENABLED',
            'GHCS_BLOCKCHAIN_ENABLED': 'BLOCKCHAIN_SERVICE_ENABLED',
            'GHCS_AI_MODEL': 'AI_MODEL_NAME',
            'GHCS_API_KEY_FILE': 'API_KEY_FILE',
            'GHCS_DATA_FILE': 'DATA_FILE',
            'GHCS_SECRET_KEY': 'SECRET_KEY',
            'GHCS_LOG_LEVEL': 'LOG_LEVEL',
            'GHCS_BLOCKCHAIN_NETWORK': 'BLOCKCHAIN_NETWORK',
            'GHCS_BROWNIE_ENABLED': 'BROWNIE_ENABLED',
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert string boolean values
                if env_value.lower() in ('true', 'false'):
                    self.settings[config_key] = env_value.lower() == 'true'
                else:
                    self.settings[config_key] = env_value
                logger.info(f"Config override: {config_key} = {self.settings[config_key]}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self.settings.get(key, default)
    
    def is_ai_enabled(self) -> bool:
        """Check if AI service is enabled."""
        return self.get('AI_SERVICE_ENABLED', False)
    
    def is_blockchain_enabled(self) -> bool:
        """Check if blockchain service is enabled."""
        return self.get('BLOCKCHAIN_SERVICE_ENABLED', False)
    
    def is_brownie_enabled(self) -> bool:
        """Check if Brownie framework is enabled."""
        return self.get('BROWNIE_ENABLED', False)

# Global configuration instance
config = Config()