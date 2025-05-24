"""
Configuration management
"""

import os
import json

class Config:
    def __init__(self):
        self.config_file = "config.json"
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return self.get_default_config()
    
    def get_default_config(self):
        """Get default configuration"""
        return {
            'download_dir': os.path.expanduser("~/Downloads"),
            'default_quality': 'auto',
            'site_configs': {
                'asmrfree.com': {
                    'token_pattern': r'var\s+token\s*=\s*["\']([^"\']+)["\']',
                    'post_id_pattern': r'post-(\d+)',
                    'ajax_url': 'https://asmrfree.com/wp-admin/admin-ajax.php'
                }
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            }
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()
