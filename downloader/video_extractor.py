"""
Enhanced Video ID extraction with dynamic content loading support
"""

import requests
import re
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin, urlparse, parse_qs, unquote
import logging
import base64
import random
from string import punctuation
import cloudscraper
import json5
import hashlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import threading
import queue

logger = logging.getLogger('video_downloader')

class EnhancedVideoExtractor:
    def __init__(self):
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            },
            delay=10
        )
        
        # Enhanced headers that look more like a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive'
        })
        
        self.selenium_driver = None
        self.network_requests = []

    def setup_selenium_driver(self):
        """Setup Selenium WebDriver with network monitoring"""
        if self.selenium_driver:
            return
            
        try:
            logger.info("Setting up ChromeDriver for enhanced video extraction (this may take a moment on first run)...")
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')
            
            # Enable logging to capture network requests
            chrome_options.add_argument('--enable-logging')
            chrome_options.add_argument('--log-level=0')
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            
            service = Service(ChromeDriverManager().install())
            self.selenium_driver = webdriver.Chrome(service=service, options=chrome_options)
            self.selenium_driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except Exception as e:
            logger.warning(f"Failed to setup Selenium driver: {e}")
            self.selenium_driver = None

    def extract_video_info(self, webpage_url):
        """Extract video information from webpage with dynamic loading support"""
        try:
            logger.info(f"Fetching webpage: {webpage_url}")
            
            # First try the static method
            try:
                result = self._extract_static_content(webpage_url)
                if result:
                    return result
            except Exception as e:
                logger.info(f"Static extraction failed: {e}")
            
            # If static fails, try dynamic method
            logger.info("Attempting dynamic extraction with browser automation...")
            return self._extract_dynamic_content(webpage_url)
            
        except Exception as e:
            logger.error(f"Error during extraction: {str(e)}", exc_info=True)
            raise Exception(f"Failed to extract video info: {str(e)}")

    def _extract_static_content(self, webpage_url):
        """Original static content extraction method"""
        response = self.session.get(webpage_url, timeout=60, allow_redirects=True)
        response.raise_for_status()
        logger.info(f"Page status code: {response.status_code}")

        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        # Save page content for debugging
        with open('page_content.html', 'w', encoding='utf-8') as f:
            f.write(html)

        # Look for iframe or video player div
        player_elements = soup.find_all(['iframe', 'div'], class_=lambda x: x and any(term in str(x).lower() for term in ['player', 'video-container', 'video-wrapper']))
        
        for player_elem in player_elements:
            player_url = player_elem.get('src') if player_elem.name == 'iframe' else None
            
            if not player_url and player_elem.name == 'div':
                # Try to find player URL in div's data attributes
                for attr in player_elem.attrs:
                    if attr.startswith('data-') and any(x in attr for x in ['src', 'url', 'source']):
                        player_url = player_elem[attr]
                        break
            
            if player_url:
                logger.info(f"Found player URL: {player_url}")
                
                if not player_url.startswith(('http://', 'https://')):
                    player_url = urljoin(webpage_url, player_url)

                # Special handling for asmrfreeplayer.fun
                if 'asmrfreeplayer.fun' in player_url:
                    video_url = self._handle_asmrfree_player(player_url, webpage_url)
                    if video_url:
                        return self._create_video_info(video_url, webpage_url)

                # Update headers for player request
                self.session.headers.update({
                    'Referer': webpage_url,
                    'Origin': f"{urlparse(webpage_url).scheme}://{urlparse(webpage_url).netloc}",
                    'Sec-Fetch-Dest': 'iframe'
                })

                # Get the player page with retry mechanism
                max_retries = 3
                retry_delay = 2
                
                for attempt in range(max_retries):
                    try:
                        player_response = self.session.get(player_url, timeout=30)
                        if player_response.ok:
                            player_html = player_response.text
                            
                            # Try multiple methods to find video URL
                            video_url = (
                                self._extract_from_json_sources(player_html) or
                                self._extract_from_player_config(player_html) or
                                self._extract_from_encoded_sources(player_html) or
                                self._extract_from_script_variables(player_html)
                            )
                            
                            if video_url:
                                return self._create_video_info(video_url, webpage_url)
                        break
                    except requests.RequestException:
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            raise

        # Try WordPress ajax as fallback
        post_id = self._extract_post_id(soup)
        if post_id:
            logger.info(f"Found post ID: {post_id}")
            video_url = self._try_wordpress_ajax(webpage_url, post_id, html)
            if video_url and self._is_valid_video_url(video_url):
                return self._create_video_info(video_url, webpage_url)

        return None

    def _extract_dynamic_content(self, webpage_url):
        """Extract video content using browser automation"""
        self.setup_selenium_driver()
        
        if not self.selenium_driver:
            raise Exception("Browser automation not available - please install ChromeDriver")
        
        try:
            # Navigate to the page
            self.selenium_driver.get(webpage_url)
            time.sleep(3)  # Wait for initial load
            
            # Start monitoring network requests
            request_queue = queue.Queue()
            monitor_thread = threading.Thread(
                target=self._monitor_network_requests, 
                args=(request_queue,)
            )
            monitor_thread.daemon = True
            monitor_thread.start()
            
            # Look for video player elements
            video_found = False
            potential_players = [
                "iframe[src*='player']",
                ".video-player",
                ".player-container",
                "#video-player",
                "video",
                "[class*='jwplayer']",
                "[id*='player']"
            ]
            
            for selector in potential_players:
                try:
                    elements = self.selenium_driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        try:
                            # Try to click play button or the player itself
                            if self._interact_with_player(element):
                                video_found = True
                                break
                        except Exception as e:
                            logger.debug(f"Failed to interact with element {selector}: {e}")
                            continue
                    if video_found:
                        break
                except Exception as e:
                    logger.debug(f"Failed to find elements with selector {selector}: {e}")
                    continue
            
            # If no specific player found, try clicking common play button selectors
            if not video_found:
                play_selectors = [
                    ".play-button",
                    "[class*='play']",
                    "[aria-label*='play' i]",
                    "button[title*='play' i]",
                    ".vjs-big-play-button",
                    ".jwplayer .jw-display-icon-container"
                ]
                
                for selector in play_selectors:
                    try:
                        elements = self.selenium_driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed():
                                self._safe_click(element)
                                time.sleep(2)
                                video_found = True
                                break
                        if video_found:
                            break
                    except Exception as e:
                        logger.debug(f"Failed to click play button {selector}: {e}")
                        continue
            
            # Wait for network requests and analyze them
            time.sleep(5)  # Give time for video requests to be made
            
            # Check captured network requests for video URLs
            video_urls = []
            try:
                while not request_queue.empty():
                    request_data = request_queue.get_nowait()
                    url = request_data.get('url', '')
                    if self._is_valid_video_url(url):
                        video_urls.append(url)
            except:
                pass
            
            # Also check browser's performance logs
            try:
                logs = self.selenium_driver.get_log('performance')
                for log in logs:
                    message = json.loads(log['message'])
                    if message['message']['method'] == 'Network.responseReceived':
                        url = message['message']['params']['response']['url']
                        if self._is_valid_video_url(url):
                            video_urls.append(url)
            except Exception as e:
                logger.debug(f"Failed to get performance logs: {e}")
            
            # Try to extract video URLs from current page source
            if not video_urls:
                current_html = self.selenium_driver.page_source
                video_url = (
                    self._extract_from_json_sources(current_html) or
                    self._extract_from_player_config(current_html) or
                    self._extract_from_encoded_sources(current_html) or
                    self._extract_from_script_variables(current_html)
                )
                if video_url:
                    video_urls.append(video_url)
            
            if video_urls:
                # Return the first valid video URL found
                best_url = self._select_best_video_url(video_urls)
                return self._create_video_info(best_url, webpage_url)
            
            raise ValueError("No video URL found after dynamic analysis")
            
        finally:
            if self.selenium_driver:
                self.selenium_driver.quit()
                self.selenium_driver = None

    def _monitor_network_requests(self, request_queue):
        """Monitor network requests in a separate thread"""
        try:
            while True:
                try:
                    logs = self.selenium_driver.get_log('performance')
                    for log in logs:
                        message = json.loads(log['message'])
                        if message['message']['method'] in ['Network.requestWillBeSent', 'Network.responseReceived']:
                            url = message['message']['params'].get('request', {}).get('url') or \
                                  message['message']['params'].get('response', {}).get('url')
                            if url:
                                request_queue.put({'url': url, 'timestamp': time.time()})
                except:
                    pass
                time.sleep(0.5)
        except:
            pass

    def _interact_with_player(self, element):
        """Try to interact with a video player element"""
        try:
            # First try to click the element itself
            if element.is_displayed():
                self._safe_click(element)
                time.sleep(2)
                
                # If it's an iframe, switch to it and look for play button
                if element.tag_name == 'iframe':
                    try:
                        self.selenium_driver.switch_to.frame(element)
                        play_buttons = self.selenium_driver.find_elements(By.CSS_SELECTOR, 
                            ".play-button, [class*='play'], .vjs-big-play-button, .jwplayer .jw-display-icon-container")
                        for btn in play_buttons:
                            if btn.is_displayed():
                                self._safe_click(btn)
                                time.sleep(2)
                                break
                        self.selenium_driver.switch_to.default_content()
                    except Exception as e:
                        logger.debug(f"Failed to interact with iframe content: {e}")
                        self.selenium_driver.switch_to.default_content()
                
                return True
                
        except Exception as e:
            logger.debug(f"Failed to interact with player element: {e}")
            return False

    def _safe_click(self, element):
        """Safely click an element with multiple strategies"""
        try:
            # Try normal click first
            element.click()
        except:
            try:
                # Try JavaScript click
                self.selenium_driver.execute_script("arguments[0].click();", element)
            except:
                try:
                    # Try ActionChains click
                    ActionChains(self.selenium_driver).move_to_element(element).click().perform()
                except:
                    pass

    def _select_best_video_url(self, urls):
        """Select the best video URL from a list"""
        if not urls:
            return None
            
        # Prefer mp4 over m3u8, and longer URLs (often contain more metadata)
        urls.sort(key=lambda x: (
            '.mp4' in x.lower(),  # Prefer mp4
            len(x),  # Prefer longer URLs
            'high' in x.lower() or 'hd' in x.lower()  # Prefer high quality
        ), reverse=True)
        
        return urls[0]

    # Keep all the existing extraction methods
    def _extract_from_json_sources(self, html):
        """Extract video URL from JSON sources in page"""
        patterns = [
            r'sources?\s*[:=]\s*(\[{[^}]+}\])',
            r'playbackConfig\s*[:=]\s*({[^}]+})',
            r'playerConfig\s*[:=]\s*({[^}]+})'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE)
            for match in matches:
                try:
                    data = json5.loads(match.group(1))
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                url = item.get('file') or item.get('src') or item.get('url')
                                if url and self._is_valid_video_url(url):
                                    return url
                    elif isinstance(data, dict):
                        url = data.get('file') or data.get('videoUrl') or data.get('url')
                        if url and self._is_valid_video_url(url):
                            return url
                except:
                    continue
        return None

    def _extract_from_player_config(self, html):
        """Extract video URL from player configuration"""
        patterns = [
            r'file\s*:\s*["\']([^"\']+\.(?:mp4|m3u8)[^"\']*)["\']',
            r'source\s*:\s*["\']([^"\']+\.(?:mp4|m3u8)[^"\']*)["\']',
            r'src\s*:\s*["\']([^"\']+\.(?:mp4|m3u8)[^"\']*)["\']',
            r'["\']?url["\']?\s*:\s*["\']([^"\']+\.(?:mp4|m3u8)[^"\']*)["\']'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE)
            for match in matches:
                url = match.group(1)
                if self._is_valid_video_url(url):
                    return url
        return None

    def _extract_from_encoded_sources(self, html):
        """Extract video URL from encoded/encrypted sources"""
        patterns = [
            (r'atob\(["\']([^"\']+)["\']\)', 'base64'),
            (r'decodeURIComponent\(escape\(atob\(["\']([^"\']+)["\']\)\)\)', 'base64'),
            (r'decodeURIComponent\(["\']([^"\']+)["\']\)', 'uri'),
            (r'unescape\(["\']([^"\']+)["\']\)', 'uri')
        ]
        
        for pattern, encoding in patterns:
            matches = re.finditer(pattern, html)
            for match in matches:
                try:
                    encoded = match.group(1)
                    if encoding == 'base64':
                        decoded = base64.b64decode(encoded).decode('utf-8')
                    else:  # uri
                        from urllib.parse import unquote
                        decoded = unquote(encoded)
                    
                    # Look for URLs in decoded content
                    url_matches = re.findall(r'https?://[^\s<>"\']+?\.(?:mp4|m3u8)[^\s<>"\']*', decoded)
                    for url in url_matches:
                        if self._is_valid_video_url(url):
                            return url
                    
                    # Try parsing as JSON
                    try:
                        data = json5.loads(decoded)
                        if isinstance(data, dict):
                            url = data.get('file') or data.get('url') or data.get('src')
                            if url and self._is_valid_video_url(url):
                                return url
                    except:
                        pass
                except:
                    continue
        return None

    def _extract_from_script_variables(self, html):
        """Extract video URL from JavaScript variables"""
        patterns = [
            r'var\s+videoUrl\s*=\s*["\']([^"\']+)["\']',
            r'var\s+videoSrc\s*=\s*["\']([^"\']+)["\']',
            r'var\s+videoFile\s*=\s*["\']([^"\']+)["\']',
            r'var\s+mp4Url\s*=\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, html)
            for match in matches:
                url = match.group(1)
                if self._is_valid_video_url(url):
                    return url
        return None

    def _is_valid_video_url(self, url):
        """Check if URL points to a valid video file"""
        if not url or not isinstance(url, str):
            return False
            
        if not url.startswith(('http://', 'https://')):
            return False
            
        # Check extensions and paths
        if not re.search(r'\.(?:mp4|m3u8)(?:\?[^&]*)?$', url, re.IGNORECASE):
            return False
            
        # Exclude common script and library URLs
        exclude_patterns = [
            r'jwplayer\.js',
            r'player\.js',
            r'\.min\.js',
            r'/assets/',
            r'/static/',
            r'/lib/',
            r'/cdn-cgi/',
            r'/wp-content/plugins/',
            r'/wp-includes/'
        ]
        
        return not any(re.search(pattern, url, re.IGNORECASE) for pattern in exclude_patterns)

    def _try_wordpress_ajax(self, webpage_url, post_id, html):
        """Try WordPress AJAX methods to get video URL"""
        ajax_url = urljoin(webpage_url, '/wp-admin/admin-ajax.php')
        
        actions = ['get_player', 'load_player', 'get_video']
        
        for action in actions:
            try:
                self.session.headers.update({
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Origin': urlparse(webpage_url).scheme + '://' + urlparse(webpage_url).netloc,
                    'Referer': webpage_url
                })
                
                data = {
                    'action': action,
                    'post_id': post_id,
                    'nonce': self._extract_nonce(html)
                }
                
                response = self.session.post(ajax_url, data=data)
                
                if response.ok:
                    try:
                        result = response.json()
                        if result.get('success'):
                            html_content = result.get('data', {}).get('html', '')
                            if html_content:
                                url_matches = re.findall(r'https?://[^\s<>"\']+?\.(?:mp4|m3u8)[^\s<>"\']*', html_content)
                                for url in url_matches:
                                    if self._is_valid_video_url(url):
                                        return url
                    except:
                        pass
            except:
                continue
                
        return None

    def _extract_nonce(self, html):
        """Extract WordPress nonce from page"""
        patterns = [
            r'nonce["\']?\s*:\s*["\']([^"\']+)["\']',
            r'_wpnonce["\']?\s*:\s*["\']([^"\']+)["\']',
            r'<input[^>]+?name=["\']\w*nonce\w*["\']\s+value=["\']([\w-]+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ''

    def _extract_post_id(self, soup):
        """Extract WordPress post ID from page"""
        for element in soup.find_all(['article', 'div']):
            classes = element.get('class', [])
            if any('post-' in cls for cls in classes):
                for cls in classes:
                    if cls.startswith('post-'):
                        return cls.replace('post-', '')
        return None

    def _create_video_info(self, video_url, webpage_url):
        """Create video info dictionary"""
        if not self._is_valid_video_url(video_url):
            raise ValueError(f"Invalid video URL: {video_url}")
            
        try:
            video_id = self.extract_abyss_id(video_url)
        except:
            video_id = f"video_{int(time.time())}_{random.randint(1000, 9999)}"
        
        if not video_url.startswith('http'):
            video_url = urljoin(webpage_url, video_url)
        
        return {
            'video_id': video_id,
            'source_url': video_url,
            'webpage_url': webpage_url
        }

    def extract_abyss_id(self, url):
        """Extract video ID from URL"""
        # Try extracting from query string first
        query = parse_qs(urlparse(url).query)
        if 'v' in query:
            return query['v'][0]
            
        # Try extracting from path
        path_parts = urlparse(url).path.split('/')
        for part in path_parts:
            if part and len(part) >= 8 and not any(c in part for c in punctuation):
                return part
        
        # Return the last meaningful part of the path
        meaningful_parts = [p for p in path_parts if p and not p.endswith(('.mp4', '.m3u8'))]
        if meaningful_parts:
            return meaningful_parts[-1]
        
        raise ValueError(f"Could not extract video ID from URL: {url}")

    def _handle_asmrfree_player(self, player_url, referer):
        """Special handler for asmrfreeplayer.fun"""
        try:
            # Set headers specifically for asmrfreeplayer.fun
            player_headers = {
                'Referer': referer,
                'Origin': 'https://asmrfreeplayer.fun',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Dest': 'iframe'
            }
            
            # Create a timestamp for token generation
            timestamp = str(int(time.time()))
            token = hashlib.md5(f"asmrfree_{timestamp}".encode()).hexdigest()
            
            # Add custom parameters that the player might expect
            if '?' in player_url:
                player_url += f"&_t={timestamp}&token={token}"
            else:
                player_url += f"?_t={timestamp}&token={token}"
            
            # First request to get the player page
            self.session.headers.update(player_headers)
            player_response = self.session.get(player_url, timeout=30)
            
            if not player_response.ok:
                logger.warning(f"Player request failed with status {player_response.status_code}")
                return None
                
            player_html = player_response.text
            
            # Extract video configuration from various possible locations
            video_url = None
            
            # Method 1: Look for JW Player setup
            config_match = re.search(r'jwplayer\([\'"][^\'"]+[\'"]\)\.setup\s*\(\s*({[^}]+})', player_html)
            if config_match:
                try:
                    config = json5.loads(config_match.group(1))
                    if isinstance(config, dict):
                        video_url = config.get('file') or config.get('source')
                except Exception as e:
                    logger.debug(f"Failed to parse JW Player config: {e}")

            # Method 2: Look for source tags
            if not video_url:
                source_tags = BeautifulSoup(player_html, 'html.parser').find_all('source')
                for source in source_tags:
                    src = source.get('src')
                    if src and self._is_valid_video_url(src):
                        video_url = src
                        break
            
            # Method 3: Look for video element
            if not video_url:
                video_elem = BeautifulSoup(player_html, 'html.parser').find('video')
                if video_elem:
                    video_url = video_elem.get('src')
                    if not video_url:
                        sources = video_elem.find_all('source')
                        for source in sources:
                            src = source.get('src')
                            if src and self._is_valid_video_url(src):
                                video_url = src
                                break
            
            # Method 4: Try API endpoints
            if not video_url:
                api_url = urljoin(player_url, '/api/source')
                try:
                    api_response = self.session.post(api_url, data={'d': urlparse(player_url).netloc}, timeout=30)
                    if api_response.ok:
                        data = api_response.json()
                        if data.get('success'):
                            for file in data.get('data', []):
                                file_url = file.get('file')
                                if file_url and self._is_valid_video_url(file_url):
                                    video_url = file_url
                                    break
                except Exception as e:
                    logger.debug(f"API request failed: {e}")
            
            if video_url:
                logger.info(f"Successfully extracted video URL from asmrfreeplayer.fun: {video_url}")
                return video_url
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to handle asmrfreeplayer.fun: {e}")
            return None