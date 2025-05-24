"""
Abyss.to Video Downloader
Main application entry point
"""

import sys
import os
from gui.main_window import VideoDownloaderApp  # Changed to relative import

def main():
    """Main application entry point"""
    try:
        app = VideoDownloaderApp()
        app.mainloop()  # CustomTkinter uses mainloop() like regular tkinter
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Add parent directory to Python path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    main()
