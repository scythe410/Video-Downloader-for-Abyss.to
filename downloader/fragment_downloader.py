"""
Fragment-based video downloading
"""

import requests
import os
import base64
import json
from urllib.parse import urljoin

class FragmentDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_video(self, video_id, quality, download_dir, progress_callback=None):
        """Download video by ID"""
        try:
            # Get video information
            video_info = self.get_video_info(video_id)
            if not video_info:
                return False
            
            # Get fragment URLs
            fragments = self.get_fragment_urls(video_id, quality)
            if not fragments:
                return False
            
            # Download fragments
            return self.download_fragments(fragments, video_id, download_dir, progress_callback)
            
        except Exception as e:
            print(f"Download error: {e}")
            return False
    
    def get_video_info(self, video_id):
        """Get video metadata"""
        try:
            info_url = f"https://player-cdn.com/?v={video_id}"
            response = self.session.get(info_url)
            
            # Extract encoded video info
            atob_pattern = r'atob\("([^"]+)"\)'
            match = re.search(atob_pattern, response.text)
            
            if match:
                video_info = base64.b64decode(match.group(1)).decode('utf-8')
                return json.loads(video_info)
            
            return None
            
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def get_fragment_urls(self, video_id, quality):
        """Get list of video fragment URLs"""
        # Implementation depends on current abyss.to structure
        # This is a placeholder that should be updated based on actual API
        try:
            manifest_url = f"https://api.hydrax.net/video/{video_id}/manifest"
            response = self.session.get(manifest_url)
            
            # Parse manifest to get fragment URLs
            fragments = []
            # Add actual parsing logic here
            
            return fragments
            
        except Exception as e:
            print(f"Error getting fragments: {e}")
            return []
    
    def download_fragments(self, fragments, video_id, download_dir, progress_callback):
        """Download and combine video fragments"""
        try:
            os.makedirs(download_dir, exist_ok=True)
            temp_dir = os.path.join(download_dir, f"temp_{video_id}")
            os.makedirs(temp_dir, exist_ok=True)
            
            fragment_files = []
            total_fragments = len(fragments)
            
            for i, fragment_url in enumerate(fragments):
                if progress_callback:
                    progress = (i + 1) / total_fragments
                    progress_callback(progress, f"Downloading fragment {i+1}/{total_fragments}")
                
                # Download fragment
                response = self.session.get(fragment_url, timeout=30)
                fragment_file = os.path.join(temp_dir, f"fragment_{i:04d}.mp4")
                
                with open(fragment_file, 'wb') as f:
                    f.write(response.content)
                
                fragment_files.append(fragment_file)
            
            # Combine fragments
            output_file = os.path.join(download_dir, f"video_{video_id}.mp4")
            self.combine_fragments(fragment_files, output_file)
            
            # Cleanup temp files
            import shutil
            shutil.rmtree(temp_dir)
            
            return True
            
        except Exception as e:
            print(f"Error downloading fragments: {e}")
            return False
    
    def combine_fragments(self, fragment_files, output_file):
        """Combine video fragments"""
        with open(output_file, 'wb') as outfile:
            for fragment_file in fragment_files:
                with open(fragment_file, 'rb') as infile:
                    outfile.write(infile.read())
