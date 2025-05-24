"""
Video ID extraction from various websites
"""

import requests
import re
from bs4 import BeautifulSoup
import json

class VideoExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
    
    def extract_video_info(self, webpage_url):
        """Extract video information from webpage"""
        try:
            # First get the webpage content
            response = self.session.get(webpage_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for iframe that might contain the video
            iframes = soup.find_all('iframe')
            video_url = None
            
            # First try to find direct abyss.to iframe
            for iframe in iframes:
                src = iframe.get('src', '')
                if 'abyss.to' in src or 'player-cdn.com' in src:
                    video_url = src
                    break
            
            # If no direct iframe found, look for embedded player data
            if not video_url:
                scripts = soup.find_all('script')
                for script in scripts:
                    content = script.string or ''
                    if 'player.src' in content or 'playerInstance' in content:
                        # Try to find video URL in script content
                        matches = re.findall(r'(https?://[^\s<>"\']+?(?:abyss\.to|player-cdn\.com)[^\s<>"\']*)', content)
                        if matches:
                            video_url = matches[0]
                            break
            
            if not video_url:
                # Look for video URL in page source
                matches = re.findall(r'(https?://[^\s<>"\']+?(?:abyss\.to|player-cdn\.com)[^\s<>"\']*)', response.text)
                if matches:
                    video_url = matches[0]
            
            if not video_url:
                raise ValueError("No video URL found in the webpage")
            
            # Clean up the URL
            video_url = video_url.replace('\\', '').strip('"\'')
            
            # Extract video ID from URL
            video_id = self.extract_abyss_id(video_url)
            
            return {
                'video_id': video_id,
                'source_url': video_url,
                'webpage_url': webpage_url
            }
            
        except Exception as e:
            raise Exception(f"Failed to extract video info: {str(e)}")
    
    def extract_abyss_id(self, url):
        """Extract abyss.to video ID from URL"""
        patterns = [
            r'abyss\.to/([a-zA-Z0-9]+)',
            r'player-cdn\.com/\?v=([a-zA-Z0-9]+)',
            r'hydrax.*?([a-zA-Z0-9]{10,})',
            r'embed.*?abyss.*?([a-zA-Z0-9]{8,})',
            r'[?&]v=([a-zA-Z0-9]+)',
            r'/e/([a-zA-Z0-9]+)',
            r'/v/([a-zA-Z0-9]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, url, re.IGNORECASE)
            if matches:
                return matches[0]
        
        raise ValueError(f"Could not extract video ID from URL: {url}")
