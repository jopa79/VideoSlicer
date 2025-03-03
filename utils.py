"""Utility functions for the application."""
import os
import platform
import subprocess
import shutil
import logging
import time
import cv2
from PIL import Image
import zipfile
import tarfile
import urllib.request
from datetime import datetime
from pathlib import Path

def get_ffmpeg_directory():
    """Get the directory where FFmpeg should be stored locally.
    
    Returns:
        Path: Directory path for local FFmpeg
    """
    # Store FFmpeg in a 'bin' subdirectory of the application
    return Path(os.path.dirname(os.path.abspath(__file__))) / "bin"

def get_ffmpeg_executable():
    """Get the path to the FFmpeg executable.
    
    Returns:
        Path: Path to the FFmpeg executable
    """
    ffmpeg_dir = get_ffmpeg_directory()
    system = platform.system()
    
    if system == "Windows":
        return ffmpeg_dir / "ffmpeg.exe"
    else:
        return ffmpeg_dir / "ffmpeg"

def check_ffmpeg_installed():
    """Check if FFmpeg is installed locally in the application directory.
    
    Returns:
        bool: True if FFmpeg is installed locally, False otherwise
    """
    ffmpeg_path = get_ffmpeg_executable()
    return ffmpeg_path.exists()

def download_ffmpeg():
    """Download and install FFmpeg locally for the current platform.
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Create the bin directory if it doesn't exist
    ffmpeg_dir = get_ffmpeg_directory()
    ffmpeg_dir.mkdir(exist_ok=True, parents=True)
    
    # Get the appropriate download URL for the current platform
    system = platform.system()
    
    if system == "Windows":
        # Windows - use a static build from gyan.dev
        download_url = "https://github.com/GyanD/codexffmpeg/releases/download/6.1.1/ffmpeg-6.1.1-essentials_build.zip"
        download_path = ffmpeg_dir / "ffmpeg.zip"
    elif system == "Darwin":  # macOS
        machine = platform.machine()
        if machine == "arm64":  # Apple Silicon
            download_url = "https://evermeet.cx/ffmpeg/getrelease/zip/ffmpeg/6.1.1"
        else:  # Intel Mac
            download_url = "https://evermeet.cx/ffmpeg/getrelease/zip/ffmpeg/6.1.1"
        download_path = ffmpeg_dir / "ffmpeg.zip"
    else:  # Linux
        # Linux - use static build
        download_url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        download_path = ffmpeg_dir / "ffmpeg.tar.xz"
    
    try:
        # Download FFmpeg
        logger.info(f"Downloading FFmpeg from {download_url}")
        urllib.request.urlretrieve(download_url, download_path)
        
        # Extract the downloaded archive
        if system == "Windows":
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(ffmpeg_dir)
                
            # Find the extracted ffmpeg.exe and move it to the bin directory
            for root, dirs, files in os.walk(ffmpeg_dir):
                if "ffmpeg.exe" in files:
                    shutil.move(os.path.join(root, "ffmpeg.exe"), ffmpeg_dir / "ffmpeg.exe")
                    break
                    
        elif system == "Darwin":  # macOS
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(ffmpeg_dir)
                
            # Make sure it's executable
            os.chmod(ffmpeg_dir / "ffmpeg", 0o755)
            
        else:  # Linux
            with tarfile.open(download_path, 'r:xz') as tar_ref:
                tar_ref.extractall(ffmpeg_dir)
                
            # Find the extracted ffmpeg and move it to the bin directory
            for root, dirs, files in os.walk(ffmpeg_dir):
                if "ffmpeg" in files and not root.endswith("bin"):
                    shutil.move(os.path.join(root, "ffmpeg"), ffmpeg_dir / "ffmpeg")
                    break
                    
            # Make sure it's executable
            os.chmod(ffmpeg_dir / "ffmpeg", 0o755)
        
        # Clean up the downloaded archive
        download_path.unlink()
        
        logger.info(f"FFmpeg installed successfully to {ffmpeg_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading FFmpeg: {e}")
        return False

def run_ffmpeg_command(cmd):
    """Run an FFmpeg command using the local installation.
    
    Args:
        cmd: Command list, where the first element is usually 'ffmpeg'
        
    Returns:
        subprocess.CompletedProcess: Result of the command
    """
    # Replace the 'ffmpeg' command with the path to our local executable
    if cmd[0] == "ffmpeg":
        cmd[0] = str(get_ffmpeg_executable())
    
    return subprocess.run(cmd, capture_output=True, text=True)

def check_ffmpeg_installed_system():
    """Check if FFmpeg is installed and functional on the system (legacy function)."""
    try:
        if platform.system() == "Windows":
            cmd = ["where", "ffmpeg"]
        else:
            cmd = ["which", "ffmpeg"]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Verify FFmpeg works by checking version (more robust)
        version_result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
        return True  # FFmpeg is installed and functional
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg check failed: {e}")
        return False  # FFmpeg not found or not working
    except FileNotFoundError:
        logging.error("ffmpeg command not found")
        return False  # ffmpeg command not found

def get_free_disk_space(path):
    """Get free disk space in bytes."""
    try:
        if platform.system() == "Windows":
            total, used, free = shutil.disk_usage(path)
            return free
        else:
            stats = os.statvfs(path)
            return stats.f_frsize * stats.f_bavail
    except Exception as e:
        logging.error(f"Error getting disk space: {e}")
        return 0

def format_time(seconds):
    """Format seconds as HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def format_file_size(size_bytes):
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {units[i]}"

def setup_logger(name, log_level=logging.INFO):
    """Set up a logger with file and console handlers."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:  # Only add handlers if they don't exist
        logger.setLevel(log_level)
        
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        log_filename = logs_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(log_level)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

def get_videos_folder():
    """Get the user's videos folder path."""
    if platform.system() == "Windows":
        return os.path.join(os.path.expanduser("~"), "Videos")
    elif platform.system() == "Darwin":  # macOS
        return os.path.join(os.path.expanduser("~"), "Movies")
    else:  # Linux and others
        return os.path.join(os.path.expanduser("~"), "Videos")

def is_valid_video_file(file_path):
    """Check if a file is a valid video file."""
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return False
    try:
        cap = cv2.VideoCapture(file_path)
        is_valid = cap.isOpened()
        cap.release()
        return is_valid
    except Exception as e:
        logging.error(f"Error checking video file: {file_path}, {e}")
        return False


def create_thumbnail(video_path, timestamp=0, size=(320, 180)):
    """Create a thumbnail image from a video at the specified timestamp."""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise ValueError("Could not read frame from video")
            
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize(size, Image.LANCZOS)
        return img
    except Exception as e:
        logging.exception(f"Error creating thumbnail: {e}")
        return None

class Timer:
    """Simple timer for measuring elapsed time."""
    
    def __init__(self):
        self.start_time = None
        self.elapsed = 0
        
    def start(self):
        self.start_time = time.time()
        self.elapsed = 0
        
    def stop(self):
        if self.start_time is not None:
            self.elapsed = time.time() - self.start_time
            self.start_time = None
        return self.elapsed
        
    def reset(self):
        self.start_time = None
        self.elapsed = 0
        
    def get_elapsed(self):
        if self.start_time is not None:
            return time.time() - self.start_time
        return self.elapsed
        
    def get_elapsed_formatted(self):
        return format_time(self.get_elapsed())
