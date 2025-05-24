# Abyss.to Video Downloader

A modern, user-friendly desktop application for downloading videos from Abyss.to. Built with Python and CustomTkinter for a native look and feel.

## Features

- 🎯 Simple and intuitive graphical user interface
- 📥 Fast video downloads with fragment-based downloading
- 💾 Configurable download directory
- 🔄 Multiple download methods for reliability
- 🎨 Modern and responsive UI with CustomTkinter
- 🚀 Background download processing
- 📊 Download progress tracking

## Installation

1. Make sure you have Python 3.10 or higher installed
2. Clone this repository or download the source code
3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python main.py
```

2. Enter the video URL in the input field
3. Select your desired download location (optional)
4. Click "Download" to start downloading

The application will automatically:
- Extract video information
- Select the best available quality
- Download and merge video fragments
- Save the final video file

## Project Structure

```
├── main.py                     # Main application entry point
├── gui/                        # GUI related modules
│   ├── main_window.py         # Main application window
│   └── components.py          # Reusable GUI components
├── downloader/                 # Download handling
│   ├── video_extractor.py     # Video info extraction
│   ├── fragment_downloader.py # Fragment download logic
│   └── alternative_methods.py # Backup download methods
├── utils/                     # Utility functions
│   ├── network.py            # Network operations
│   ├── file_handler.py       # File management
│   └── config.py             # Configuration handling
└── assets/                   # Application assets
    └── icons/               # Application icons
    └── styles/              # UI themes and styles
```

## Requirements

- Python 3.10+
- CustomTkinter 5.2.0+
- Requests 2.28.0+
- urllib3 2.0.0+
- python-dotenv 1.0.0+
- Pillow 10.0.0+
- BeautifulSoup4 4.12.0+

## Configuration

The application can be configured through the `config.json` file:
- Download directory
- Default video quality
- Network settings
- UI theme preferences

## Development

To contribute to the project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### Running Tests

```bash
python -m unittest discover tests
```

## Troubleshooting

If you encounter any issues:

1. Check your internet connection
2. Verify the video URL is correct
3. Ensure all dependencies are installed correctly
4. Check the application logs in the terminal


## Disclaimer

This tool is for educational purposes only. Make sure you have the right to download any content before using this tool.