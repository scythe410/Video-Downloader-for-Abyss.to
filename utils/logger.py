"""
Logging configuration for the application
"""

import logging
import os
from datetime import datetime

def setup_logger():
    """Setup application logging"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"downloader_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('video_downloader')
