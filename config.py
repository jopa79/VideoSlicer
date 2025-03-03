"""Configuration settings for the application."""
import configparser
import os
import json
import logging
from pathlib import Path
from constants import MAX_ANALYSIS_DURATION, APP_NAME


# Default values as constants for easy import
DEFAULT_SEQUENCE_LENGTH = 10
DEFAULT_SCENE_THRESHOLD = 30.0
DEFAULT_NUM_SEQUENCES = 3
DEFAULT_OUTPUT_FORMAT = "prores"
DEFAULT_QUALITY = "medium"

# Output format definitions
OUTPUT_FORMATS = {
    'prores': {'extension': '.mov', 'description': 'ProRes 422',
                'profiles': {'low': 'ProRes 422 Proxy (smaller file)',
                             'medium': 'ProRes 422 LT (balanced)',
                             'high': 'ProRes 422 HQ (high quality)'}},
    'mp4': {'extension': '.mp4', 'description': 'MP4 (H.264)',
           'profiles': {'low': 'Fast encoding, lower quality',
                        'medium': 'Balanced quality and size',
                        'high': 'High quality, larger file size'}}
}

# Quality settings
QUALITY_SETTINGS = {
    'low': 'Low quality (smaller file size)',
    'medium': 'Medium quality (balanced)',
    'high': 'High quality (larger file size)'
}

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
            self.config_file_path = Path(os.path.join(self.config_dir, 'config.json'))
        else:
            self.config_dir = config_dir
            self.config_file_path = Path(os.path.join(self.config_dir, 'config.json'))
            
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Default configuration
        self.default_config = {
            'input_folder': str(Path.home()),
            'output_folder': str(Path.home()),
            'sequence_length': DEFAULT_SEQUENCE_LENGTH,
            'num_sequences': DEFAULT_NUM_SEQUENCES,
            'scene_threshold': DEFAULT_SCENE_THRESHOLD,
            'max_analysis_duration': MAX_ANALYSIS_DURATION,
            'output_format': DEFAULT_OUTPUT_FORMAT,
            'quality': DEFAULT_QUALITY,
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
        
        # Backwards compatibility: also support ini-style access for existing code
        self._ini_config = configparser.ConfigParser()
        self._init_ini_config()
        
    def _init_ini_config(self):
        """Initialize the INI-style config from the JSON config for backwards compatibility."""
        # Map our JSON config to INI sections
        self._ini_config['DEFAULT'] = {
            'sequence_length': str(self.config['sequence_length']),
            'scene_threshold': str(self.config['scene_threshold']),
            'num_sequences': str(self.config['num_sequences']),
            'output_format': self.config['output_format'],
            'quality': self.config['quality'],
            'max_analysis_duration': str(self.config['max_analysis_duration']),
            'theme': self.config['theme']
        }
        
        self._ini_config['OUTPUT_FORMATS'] = {
            'prores': str(OUTPUT_FORMATS['prores']),
            'mp4': str(OUTPUT_FORMATS['mp4'])
        }
        
        self._ini_config['QUALITY_SETTINGS'] = {
            'low': QUALITY_SETTINGS['low'],
            'medium': QUALITY_SETTINGS['medium'],
            'high': QUALITY_SETTINGS['high']
        }
        
    def load_config(self):
        """Load configuration from file or create default if it doesn't exist.
        
        Returns:
            dict: The loaded configuration.
        """
        try:
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, 'r') as f:
                    config = json.load(f)
                self.logger.info(f"Loaded configuration from {self.config_file_path}")
                
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
            with open(self.config_file_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.logger.info(f"Saved configuration to {self.config_file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            return False
    
    # JSON-style access methods
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
        
    # INI-style access methods (for backward compatibility)
    def getint(self, section, option, default=None):
        """Get an integer configuration value (INI style)."""
        try:
            return self._ini_config.getint(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default
    
    def getfloat(self, section, option, default=None):
        """Get a float configuration value (INI style)."""
        try:
            return self._ini_config.getfloat(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default
    
    # Recent files management
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