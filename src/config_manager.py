class ConfigManager:
    """Configuration manager with validation and defaults"""
    
    def __init__(self, config_file=None):
        # Default configuration
        self.config = {
            "base_url": "",
            "excel_path": "CDB-Translate.xlsx",
            "username": "",
            "password": "",
            "browsers": ["chrome"],
            "screenshot_on_mismatch": True,
            "check_dynamic_content": True,
            "headless": False,
            "wait_time": 10,
            "navigation_paths": [
                ["Dashboard"],
                ["Account"],
                ["Account", "Account List"]
            ],
            "report_dir": "reports",
            "screenshots_dir": "screenshots",
            "logs_dir": "logs",
            "log_level": "INFO"
        }
        
        # Load from file if provided
        if config_file:
            self.load_config(config_file)
            
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
                self.config.update(loaded_config)
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Error loading config file: {str(e)}")
            
    def validate(self):
        """Validate the configuration"""
        required_fields = ["base_url", "excel_path"]
        missing = [field for field in required_fields if not self.config.get(field)]
        
        if missing:
            raise ValueError(f"Missing required configuration fields: {', '.join(missing)}")
            
        # Validate URL format
        if not self.config["base_url"].startswith(("http://", "https://")):
            raise ValueError(f"Invalid base_url: {self.config['base_url']}. Must start with http:// or https://")
            
        # Validate Excel file exists
        if not os.path.exists(self.config["excel_path"]):
            raise ValueError(f"Excel file not found: {self.config['excel_path']}")
            
        # Validate browsers
        valid_browsers = ["chrome", "firefox", "edge"]
        invalid_browsers = [b for b in self.config["browsers"] if b not in valid_browsers]
        if invalid_browsers:
            raise ValueError(f"Invalid browser(s): {', '.join(invalid_browsers)}. Supported browsers: {', '.join(valid_browsers)}")
            
        return True