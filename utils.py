"""Utility functions for the application."""
import os
import platform
import subprocess
import shutil
import logging
import time
import cv2
from PIL import Image
from datetime import datetime
from pathlib import Path

def check_ffmpeg_installed():
    """Check if FFmpeg is installed and functional."""
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

def get_ffmpeg_version():
    """Get the installed FFmpeg version."""
    try:
        result = subprocess.run(["ffmpeg", "-version"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
        if result.returncode == 0:
            # Extract version from the first line
            first_line = result.stdout.split('\n')[0]
            return first_line
        return None
    except Exception as e:
        logging.error(f"Error getting FFmpeg version: {e}")
        return None

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
