# VideoSlicer

VideoSlicer is a desktop application for automatically extracting high-quality video sequences based on scene detection.

## Features

- Automatically detect scene changes in videos
- Extract multiple sequences in high-quality formats
- Support for ProRes, H.264, and H.265 encoding
- Batch processing for multiple videos
- Modern, user-friendly interface with light/dark theme

## Requirements

- Python 3.8 or higher
- FFmpeg installed and in your system PATH
- OpenCV, NumPy, and other dependencies listed in requirements.txt

## Installation

1. **Clone the repository:**
   ```
   git clone https://github.com/yourusername/VideoSlicer.git
   cd VideoSlicer
   ```

2. **Create a virtual environment (optional but recommended):**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Install FFmpeg:**

   VideoSlicer requires FFmpeg to be installed on your system.

   **Windows:**
   - Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Add FFmpeg bin folder to your system PATH

   **macOS:**
   ```
   brew install ffmpeg
   ```

   **Linux:**
   ```
   sudo apt install ffmpeg  # Ubuntu/Debian
   sudo dnf install ffmpeg  # Fedora
   ```

   For ProRes support, make sure your FFmpeg installation includes the ProRes codec. Standard packages typically include H.264 and H.265 support.

5. **Prepare resources:**
   
   Create a `resources` folder in the project root and add your application icons:
   ```
   mkdir -p resources
   # Add icon.ico, logo.png etc. to this folder
   ```

## Usage

Run the application:
```
python main.py
```

### Command-line options:
```
python main.py --theme dark  # Start with dark theme
python main.py --theme light  # Start with light theme
```

## How It Works

1. **Scene Detection:** VideoSlicer analyzes the first 40 seconds of your video to detect scene changes using frame difference metrics
2. **Sequence Extraction:** After detecting scene changes, the app extracts multiple sequences starting from the first detected scene
3. **High-quality Export:** Sequences are exported using FFmpeg with your choice of codecs (ProRes, H.264, H.265) and quality settings

## Configuration

VideoSlicer saves your settings in a config file located at:
- Windows: `C:\Users\<username>\.video_slicer\config.json`
- macOS/Linux: `~/.video_slicer/config.json`

## Troubleshooting

### FFmpeg Issues

If you encounter FFmpeg-related errors:

1. Ensure FFmpeg is properly installed and in your system PATH
2. Check codec support by running: `ffmpeg -encoders`
3. For ProRes support issues, the application will automatically fall back to H.264

### Video Processing Problems

- For large videos, processing may take time
- Scene detection only analyzes the first 40 seconds for performance reasons
- If no scenes are detected, the application will start from the beginning of the video

## Development

### Project Structure

- `core/` - Core processing logic
- `gui/` - GUI components
- `resources/` - Application resources
- `utils.py` - Utility functions
- `config.py` - Configuration management
- `constants.py` - Application constants
- `main.py` - Application entry point

### Adding New Features

To extend VideoSlicer:

1. For new encoders, update the `check_ffmpeg_available()` method in `core/video_processor.py`
2. For UI changes, modify the appropriate files in the `gui/` directory
3. For new configuration options, update `config.py`

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.