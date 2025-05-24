"""
Video ID extraction from various websites
"""

import requests
import re
from bs4 import BeautifulSoup

class VideoExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_abyss_id(self, webpage_url):
        """Extract abyss.to video ID from webpage"""
        try:
            response = self.session.get(webpage_url, timeout=30)
            response.raise_for_status()
            
            # Multiple patterns to find abyss.to video IDs
            patterns = [
                r'abyss\.to/([a-zA-Z0-9]+)',
                r'player-cdn\.com/\?v=([a-zA-Z0-9]+)',
                r'hydrax.*?([a-zA-Z0-9]{10,})',
                r'embed.*?abyss.*?([a-zA-Z0-9]{8,})'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                if matches:
                    return matches[0]
            
            # Try parsing with BeautifulSoup for iframe sources
            soup = BeautifulSoup(response.text, 'html.parser')
            iframes = soup.find_all('iframe')
            
            for iframe in iframes:
                src = iframe.get('src', '')
                if 'abyss.to' in src or 'player-cdn.com' in src:
                    for pattern in patterns:
                        match = re.search(pattern, src)
                        if match:
                            return match.group(1)
            
            return None
            
        except Exception as e:
            print(f"Error extracting video ID: {e}")
            return None
