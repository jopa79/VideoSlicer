"""Configuration file manager for saving and loading user settings."""
import os
import json
import logging
from pathlib import Path

class ConfigManager:
    """Manages saving and loading of application configuration."""
    
    def __init__(self, config_dir=None):
        """Initialize the configuration manager.
        
        Args:
            config_dir: Directory to store configuration files. If None,
                        uses the user's home directory.
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up config directory
        if config_dir is None:
            self.config_dir = os.path.join(str(Path.home()), '.video_slicer')
        else:
            self.config_dir = config_dir
            
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Path to the main config file
        self.config_file = os.path.join(self.config_dir, 'config.json')
        
        # Default configuration
        self.default_config = {
            'input_folder': str(Path.home()),
            'output_folder': str(Path.home()),
            'sequence_length': 10,
            'num_sequences': 3,
            'scene_threshold': 30.0,
            'max_analysis_duration': 40.0,
            'output_format': 'prores',
            'quality': 'medium',
            'language': 'en',
            'theme': 'dark',  # Default to dark theme
            'recent_files': [],
            'batch_settings': {
                'parallel_processing': True,
                'max_workers': 2
            }
        }
        
        # Current configuration (loaded from file or default)
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from file or create default if it doesn't exist.
        
        Returns:
            dict: The loaded configuration.
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                self.logger.info(f"Loaded configuration from {self.config_file}")
                
                # Merge with default config to ensure all keys exist
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
            else:
                self.logger.info("No configuration file found, using defaults")
                return self.default_config.copy()
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            return self.default_config.copy()
            
    def save_config(self):
        """Save the current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.logger.info(f"Saved configuration to {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            return False
            
    def get(self, key, default=None):
        """Get a configuration value.
        
        Args:
            key: The configuration key to get.
            default: Default value if key doesn't exist.
            
        Returns:
            The configuration value or default if not found.
        """
        return self.config.get(key, default)
        
    def set(self, key, value):
        """Set a configuration value.
        
        Args:
            key: The configuration key to set.
            value: The value to set.
        """
        self.config[key] = value
        
    def add_recent_file(self, file_path):
        """Add a file to the recent files list.
        
        Args:
            file_path: Path to the file to add.
        """
        recent_files = self.config.get('recent_files', [])
        
        # Remove if already exists
        if file_path in recent_files:
            recent_files.remove(file_path)
            
        # Add to the beginning
        recent_files.insert(0, file_path)
        
        # Limit to 10 recent files
        self.config['recent_files'] = recent_files[:10]
        
    def get_recent_files(self):
        """Get the list of recent files.
        
        Returns:
            list: List of recent file paths.
        """
        return self.config.get('recent_files', [])