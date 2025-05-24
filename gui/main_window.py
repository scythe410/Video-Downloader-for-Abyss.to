"""
Main GUI window implementation using CustomTkinter
"""

import customtkinter
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os

from downloader.video_extractor import VideoExtractor
from downloader.fragment_downloader import FragmentDownloader
from utils.config import Config

class VideoDownloaderApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.config = Config()
        self.video_extractor = VideoExtractor()
        self.fragment_downloader = FragmentDownloader()
        
        # Configure window
        self.setup_window()
        self.create_widgets()
    
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
        
        # Title
        self.title_label = customtkinter.CTkLabel(
            self.main_frame, 
            text="Abyss.to Video Downloader",
            font=customtkinter.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=20)
        
        # URL input section
        self.url_frame = customtkinter.CTkFrame(self.main_frame)
        self.url_frame.pack(fill="x", padx=20, pady=10)
        
        self.url_label = customtkinter.CTkLabel(self.url_frame, text="Video Website URL:")
        self.url_label.pack(anchor="w", padx=10, pady=5)
        
        self.url_entry = customtkinter.CTkEntry(
            self.url_frame, 
            width=500, 
            placeholder_text="Enter videowebsite.com URL containing abyss.to video"
        )
        self.url_entry.pack(fill="x", padx=10, pady=5)
        
        # Settings section
        self.settings_frame = customtkinter.CTkFrame(self.main_frame)
        self.settings_frame.pack(fill="x", padx=20, pady=10)
        
        # Quality selection
        self.quality_label = customtkinter.CTkLabel(self.settings_frame, text="Video Quality:")
        self.quality_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.quality_var = customtkinter.StringVar(value="720p")
        self.quality_menu = customtkinter.CTkOptionMenu(
            self.settings_frame, 
            values=["360p", "720p", "1080p"], 
            variable=self.quality_var
        )
        self.quality_menu.grid(row=0, column=1, padx=10, pady=5)
        
        # Download directory
        self.dir_label = customtkinter.CTkLabel(self.settings_frame, text="Download Directory:")
        self.dir_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.dir_button = customtkinter.CTkButton(
            self.settings_frame, 
            text="Choose Directory", 
            command=self.choose_directory
        )
        self.dir_button.grid(row=1, column=1, padx=10, pady=5)
        
        # Download section
        self.download_frame = customtkinter.CTkFrame(self.main_frame)
        self.download_frame.pack(fill="x", padx=20, pady=20)
        
        self.download_btn = customtkinter.CTkButton(
            self.download_frame, 
            text="Download Video", 
            command=self.start_download,
            height=40,
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        self.download_btn.pack(pady=10)
        
        # Progress section
        self.progress_frame = customtkinter.CTkFrame(self.main_frame)
        self.progress_frame.pack(fill="x", padx=20, pady=10)
        
        self.progress_label = customtkinter.CTkLabel(self.progress_frame, text="Progress:")
        self.progress_label.pack(anchor="w", padx=10, pady=5)
        
        self.progress = customtkinter.CTkProgressBar(self.progress_frame)
        self.progress.pack(fill="x", padx=10, pady=5)
        self.progress.set(0)
        
        self.status_label = customtkinter.CTkLabel(self.progress_frame, text="Ready to download")
        self.status_label.pack(anchor="w", padx=10, pady=5)
    
    def choose_directory(self):
        """Open directory chooser dialog"""
        directory = filedialog.askdirectory()
        if directory:
            self.config.set_download_directory(directory)
            messagebox.showinfo("Success", f"Download directory set to: {directory}")
    
    def start_download(self):
        """Start the download process"""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showerror("Error", "Please enter a video URL")
            return
        
        # Disable download button
        self.download_btn.configure(state="disabled")
        self.progress.set(0)
        
        # Start download in separate thread
        download_thread = threading.Thread(target=self.download_process, args=(url,))
        download_thread.daemon = True
        download_thread.start()
    
    def download_process(self, url):
        """Main download process"""
        try:
            # Update status
            self.status_label.configure(text="Extracting video information...")
            
            # Extract video ID
            video_id = self.video_extractor.extract_abyss_id(url)
            
            if not video_id:
                raise Exception("Could not find abyss.to video in the webpage")
            
            self.status_label.configure(text=f"Found video ID: {video_id}")
            
            # Download video
            success = self.fragment_downloader.download_video(
                video_id, 
                self.quality_var.get(),
                self.config.get_download_directory(),
                progress_callback=self.update_progress
            )
            
            if success:
                self.status_label.configure(text="Download completed successfully!")
                messagebox.showinfo("Success", "Video downloaded successfully!")
            else:
                raise Exception("Download failed")
                
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            # Re-enable download button
            self.download_btn.configure(state="normal")
    
    def update_progress(self, progress_value, status_text):
        """Update progress bar and status"""
        self.progress.set(progress_value)
        self.status_label.configure(text=status_text)
        self.update()
