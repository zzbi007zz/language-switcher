import json
from asyncio.log import logger


class ConfigManager:
    """Manage configuration for the translation testing"""
    
    def __init__(self, config_file=None):
        """
        Initialize with optional config file
        
        Args:
            config_file (str): Path to JSON configuration file
        """
        self.config = {
            "base_url": "https://corp-banking.sit.bic.tech/",
            "excel_path": "CDB-Translate.xlsx",
            "username": "sole",
            "password": "Password@123",
            "browsers": ["chrome"],
            "screenshot_on_mismatch": True,
            "check_dynamic_content": True,
            "headless": False,
            "wait_time": 10,
            "navigation_paths": []
        }
        
        if config_file:
            self.load_config(config_file)
    
    def load_config(self, config_file):
        """
        Load configuration from JSON file
        
        Args:
            config_file (str): Path to JSON configuration file
        """
        try:
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
                self.config.update(loaded_config)
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Error loading config file: {str(e)}")
    
    def get_config(self):
        """Get the current configuration"""
        return self.config
    
    def set_config(self, key, value):
        """Set a configuration value"""
        self.config[key] = value
    
    def save_config(self, config_file):
        """Save current configuration to file"""
        try:
            # Don't save credentials to file
            safe_config = self.config.copy()
            safe_config.pop("username", None)
            safe_config.pop("password", None)
            
            with open(config_file, 'w') as f:
                json.dump(safe_config, f, indent=4)
            logger.info(f"Saved configuration to {config_file}")
        except Exception as e:
            logger.error(f"Error saving config file: {str(e)}")
