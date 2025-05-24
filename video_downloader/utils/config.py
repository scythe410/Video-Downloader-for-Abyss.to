"""
Application configuration management
"""

import json
import os

class Config:
    def __init__(self):
        self.config_file = "config.json"
        self.default_config = {
            "download_directory": "./downloads",
            "default_quality": "720p",
            "max_retries": 3,
            "timeout": 30
        }
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = self.default_config.copy()
                self.save_config()
        except Exception:
            self.config = self.default_config.copy()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_download_directory(self):
        """Get download directory"""
        return self.config.get("download_directory", "./downloads")
    
    def set_download_directory(self, directory):
        """Set download directory"""
        self.config["download_directory"] = directory
        self.save_config()
