"""
Abyss.to Video Downloader
Main application entry point
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = str(Path(__file__).parent.absolute())
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from gui.main_window import VideoDownloaderApp

def main():
    """Main application entry point"""
    try:
        app = VideoDownloaderApp()
        app.mainloop()  # CustomTkinter uses mainloop() like regular tkinter
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
