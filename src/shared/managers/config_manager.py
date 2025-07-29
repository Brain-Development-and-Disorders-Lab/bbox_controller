"""
Configuration management for bbox_controller project
"""

import json
import os
from typing import Dict, Any


class ConfigManager:
    """Manages global experiment configuration with file-based storage and defaults"""
    
    DEFAULT_CONFIG = {
        "iti_minimum": 100,
        "iti_maximum": 1000,
        "response_limit": 1000,
        "cue_minimum": 5000,
        "cue_maximum": 10000,
        "hold_minimum": 100,
        "hold_maximum": 1000,
        "valve_open": 100,
        "punish_time": 1000
    }
    
    def __init__(self, config_file: str = None):
        if config_file is None:
            # Default to config.json in the same directory as this module
            import os
            self.config_file = os.path.join(os.path.dirname(__file__), "config.json")
        else:
            self.config_file = config_file
        self._config = None
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file, falling back to defaults"""
        if self._config is not None:
            return self._config
        
        config = self.DEFAULT_CONFIG.copy()
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    # Merge with defaults, file config takes precedence
                    if "task" in file_config:
                        config.update(file_config["task"])
                    else:
                        config.update(file_config)
        except Exception as e:
            print(f"Warning: Could not load config file {self.config_file}: {e}")
            print("Using default configuration")
        
        self._config = config
        return config
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file) if os.path.dirname(self.config_file) else '.', exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump({"task": config}, f, indent=2)
            
            self._config = config
            return True
        except Exception as e:
            print(f"Error saving config file {self.config_file}: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.load_config()


# Global config manager instance
config_manager = ConfigManager() 