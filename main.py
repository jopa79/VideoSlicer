"""Main entry point for the application."""
import tkinter as tk
import os
import sys
import logging
import argparse
from pathlib import Path

from gui.main_window import VideoSlicerGUI
from utils import check_ffmpeg_installed, setup_logger
from constants import APP_NAME
from config import ConfigManager

def main():
    """Start the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Video Slicer Application")
    parser.add_argument("--theme", choices=["light", "dark"], default=None, 
                       help="Set the application theme")
    args = parser.parse_args()
    
    # Set up logger
    logger = setup_logger("video_slicer")
    
    # Set better DPI awareness on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    # Load configuration
    config_manager = ConfigManager()
    
    # Create the root window
    root = tk.Tk()
    root.title(APP_NAME)
    
    # Set icon if available
    try:
        icon_path = os.path.join(os.path.dirname(__file__), "ressources", "icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception as e:
        logger.warning(f"Could not set icon: {e}")
    
    # Apply theme from command line argument if provided, otherwise from config
    theme = args.theme if args.theme else config_manager.get('DEFAULT', 'theme', 'dark')
    
    try:
        import sv_ttk
        sv_ttk.set_theme(theme)
        logger.info(f"Applied Sun Valley theme: {theme}")
    except ImportError:
        logger.warning("Sun Valley theme not available. Using default theme.")
    
    # Create the application
    app = VideoSlicerGUI(root, config_manager)
    
    # Center the window on the screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'+{x}+{y}')
    
    # Start the application
    root.mainloop()
    
    # Save configuration on exit
    if config_manager:
        config_manager.save_config()

if __name__ == '__main__':
    main()
