"""
Main GUI window implementation using CustomTkinter
"""

import customtkinter
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import traceback

from downloader.video_extractor import EnhancedVideoExtractor
from downloader.fragment_downloader import FragmentDownloader
from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger()

class VideoDownloaderApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.config = Config()
        self.video_extractor = EnhancedVideoExtractor()
        self.fragment_downloader = FragmentDownloader()
        
        # Configure window
        self.setup_window()
        self.create_widgets()
        
        # Download state
        self.current_download = None
        
        # Bind cleanup to window close
        self.protocol("WM_DELETE_WINDOW", self.cleanup)
        
        logger.info("Application initialized")
    
    def setup_window(self):
        """Configure main window properties"""
        self.title("Abyss.to Video Downloader")
        self.geometry("700x500")
        self.resizable(True, True)
        
        # Set theme
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")
    
    def create_widgets(self):
        """Create and layout GUI widgets"""
        # Main frame
        self.main_frame = customtkinter.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # URL input frame
        self.url_frame = customtkinter.CTkFrame(self.main_frame)
        self.url_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.url_label = customtkinter.CTkLabel(
            self.url_frame,
            text="Video URL:",
            font=customtkinter.CTkFont(size=14)
        )
        self.url_label.pack(side="left", padx=(10, 5))
        
        self.url_entry = customtkinter.CTkEntry(
            self.url_frame,
            placeholder_text="Enter ASMR website URL...",
            width=400
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Download location frame
        self.location_frame = customtkinter.CTkFrame(self.main_frame)
        self.location_frame.pack(fill="x", padx=20, pady=10)
        
        self.location_label = customtkinter.CTkLabel(
            self.location_frame,
            text="Save to:",
            font=customtkinter.CTkFont(size=14)
        )
        self.location_label.pack(side="left", padx=(10, 5))
        
        self.location_entry = customtkinter.CTkEntry(
            self.location_frame,
            placeholder_text="Download location...",
            width=300
        )
        self.location_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.location_entry.insert(0, os.path.expanduser("~/Downloads"))
        
        self.browse_button = customtkinter.CTkButton(
            self.location_frame,
            text="Browse",
            width=100,
            command=self.browse_location
        )
        self.browse_button.pack(side="right", padx=5)
        
        # Progress frame
        self.progress_frame = customtkinter.CTkFrame(self.main_frame)
        self.progress_frame.pack(fill="x", padx=20, pady=10)
        
        self.progress_bar = customtkinter.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=10)
        self.progress_bar.set(0)
        
        self.status_label = customtkinter.CTkLabel(
            self.progress_frame,
            text="Ready",
            font=customtkinter.CTkFont(size=12)
        )
        self.status_label.pack(pady=5)
        
        # Control buttons
        self.button_frame = customtkinter.CTkFrame(self.main_frame)
        self.button_frame.pack(fill="x", padx=20, pady=10)
        
        self.download_button = customtkinter.CTkButton(
            self.button_frame,
            text="Download",
            width=150,
            command=self.start_download
        )
        self.download_button.pack(side="left", padx=5)
        
        self.cancel_button = customtkinter.CTkButton(
            self.button_frame,
            text="Cancel",
            width=150,
            state="disabled",
            command=self.cancel_download
        )
        self.cancel_button.pack(side="left", padx=5)
    
    def browse_location(self):
        """Open directory selection dialog"""
        directory = filedialog.askdirectory(
            initialdir=self.location_entry.get()
        )
        if directory:
            self.location_entry.delete(0, tk.END)
            self.location_entry.insert(0, directory)
    
    def update_progress(self, current, total):
        """Update progress bar and status"""
        progress = current / total if total > 0 else 0
        self.progress_bar.set(progress)
        self.status_label.configure(
            text=f"Downloading... {current}/{total} fragments ({int(progress * 100)}%)"
        )
    
    def start_download(self):
        """Start the download process"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a video URL")
            return
            
        save_dir = self.location_entry.get().strip()
        if not os.path.isdir(save_dir):
            try:
                os.makedirs(save_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Could not create download directory: {str(e)}")
                return
        
        # Disable controls during download
        self.url_entry.configure(state="disabled")
        self.location_entry.configure(state="disabled")
        self.browse_button.configure(state="disabled")
        self.download_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        
        # Start download in background thread
        self.current_download = threading.Thread(
            target=self.download_video,
            args=(url, save_dir)
        )
        self.current_download.start()
    
    def download_video(self, url, save_dir):
        """Download video in background thread"""
        try:
            logger.info(f"Starting download from URL: {url}")
            self.status_label.configure(text="Extracting video information...")
            
            video_info = self.video_extractor.extract_video_info(url)
            logger.info(f"Video info extracted: {video_info}")
            
            self.status_label.configure(text="Starting download...")
            output_path = self.fragment_downloader.download_video(
                video_info['video_id'],
                quality='auto',
                download_dir=save_dir,
                progress_callback=self.update_progress
            )
            
            logger.info(f"Download completed: {output_path}")
            self.status_label.configure(text=f"Download complete! Saved to: {output_path}")
            messagebox.showinfo("Success", "Video downloaded successfully!")
            
        except Exception as e:
            logger.error(f"Download failed: {str(e)}\n{traceback.format_exc()}")
            self.status_label.configure(text="Download failed!")
            error_message = str(e)
            if "403" in error_message:
                error_message = "Access denied. The website may be blocking automated access."
            elif "404" in error_message:
                error_message = "Video not found. It may have been removed or the URL is incorrect."
            messagebox.showerror("Error", f"Download failed: {error_message}")
            
        finally:
            # Re-enable controls
            self.url_entry.configure(state="normal")
            self.location_entry.configure(state="normal")
            self.browse_button.configure(state="normal")
            self.download_button.configure(state="normal")
            self.cancel_button.configure(state="disabled")
            self.progress_bar.set(0)
    
    def cancel_download(self):
        """Cancel current download"""
        if self.current_download and self.current_download.is_alive():
            # Set a flag to stop the download
            if hasattr(self.fragment_downloader, 'cancel_download'):
                self.fragment_downloader.cancel_download()
            self.status_label.configure(text="Cancelling download...")
    
    def cleanup(self):
        """Clean up resources before closing"""
        try:
            if self.video_extractor and hasattr(self.video_extractor, 'selenium_driver') and self.video_extractor.selenium_driver:
                self.video_extractor.selenium_driver.quit()
        except Exception as e:
            logger.warning(f"Error cleaning up Selenium driver: {e}")
        finally:
            self.quit()
