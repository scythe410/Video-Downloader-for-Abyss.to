"""
Fragment-based video downloading
"""

import requests
import os
import base64
import json
import time
from urllib.parse import urljoin, urlparse
import m3u8

class FragmentDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Origin': 'https://abyss.to',
            'Referer': 'https://abyss.to/',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        })
        self.base_url = "https://abyss.to"
        self.api_url = "https://api.abyss.to"
    
    def get_video_info(self, video_id):
        """Get video metadata and available qualities"""
        try:
            info_url = f"{self.api_url}/videos/{video_id}/info"
            response = self.session.get(info_url)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('success'):
                raise ValueError(f"Failed to get video info: {data.get('message', 'Unknown error')}")
                
            return data['data']
            
        except Exception as e:
            raise Exception(f"Failed to get video info: {str(e)}")
    
    def get_fragment_urls(self, video_id, quality='auto'):
        """Get HLS playlist and fragment URLs"""
        try:
            # Get stream URL
            stream_url = f"{self.api_url}/videos/{video_id}/stream"
            response = self.session.get(stream_url)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('success'):
                raise ValueError(f"Failed to get stream URL: {data.get('message', 'Unknown error')}")
            
            # Get master playlist
            playlist_url = data['data']['url']
            response = self.session.get(playlist_url)
            response.raise_for_status()
            
            master_playlist = m3u8.loads(response.text)
            
            # Select quality
            selected_playlist = None
            if quality == 'auto':
                # Choose highest quality
                selected_playlist = sorted(
                    master_playlist.playlists,
                    key=lambda p: p.stream_info.resolution[0] if p.stream_info.resolution else 0,
                    reverse=True
                )[0]
            else:
                # Find closest matching quality
                target_height = int(quality.rstrip('p'))
                selected_playlist = min(
                    master_playlist.playlists,
                    key=lambda p: abs(p.stream_info.resolution[1] - target_height) if p.stream_info.resolution else float('inf')
                )
            
            # Get fragment playlist
            response = self.session.get(selected_playlist.uri)
            response.raise_for_status()
            
            fragment_playlist = m3u8.loads(response.text)
            base_url = os.path.dirname(selected_playlist.uri) + '/'
            
            return [{
                'url': urljoin(base_url, segment.uri),
                'duration': segment.duration
            } for segment in fragment_playlist.segments]
            
        except Exception as e:
            raise Exception(f"Failed to get fragment URLs: {str(e)}")
    
    def download_video(self, video_id, quality='auto', download_dir=None, progress_callback=None):
        """Download video by ID"""
        try:
            if not download_dir:
                download_dir = os.getcwd()
            
            # Create temp directory for fragments
            temp_dir = os.path.join(download_dir, f"temp_{video_id}")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Get video information
            video_info = self.get_video_info(video_id)
            output_filename = f"{video_id}_{int(time.time())}.mp4"
            output_path = os.path.join(download_dir, output_filename)
            
            # Get fragment URLs
            fragments = self.get_fragment_urls(video_id, quality)
            total_fragments = len(fragments)
            
            if progress_callback:
                progress_callback(0, total_fragments)
            
            # Download fragments
            fragment_paths = []
            for i, fragment in enumerate(fragments, 1):
                fragment_path = os.path.join(temp_dir, f"fragment_{i}.ts")
                fragment_paths.append(fragment_path)
                
                response = self.session.get(fragment['url'], stream=True)
                response.raise_for_status()
                
                with open(fragment_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                if progress_callback:
                    progress_callback(i, total_fragments)
            
            # Combine fragments
            with open(output_path, 'wb') as outfile:
                for fragment_path in fragment_paths:
                    with open(fragment_path, 'rb') as infile:
                        outfile.write(infile.read())
            
            # Clean up temp files
            for fragment_path in fragment_paths:
                try:
                    os.remove(fragment_path)
                except:
                    pass
            try:
                os.rmdir(temp_dir)
            except:
                pass
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to download video: {str(e)}")
            
        finally:
            # Ensure temp directory is cleaned up
            if 'temp_dir' in locals():
                try:
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
