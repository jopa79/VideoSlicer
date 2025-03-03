"""Configuration settings for the application."""
import configparser
import os
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

# Default configuration if config.ini is not found
DEFAULT_CONFIG = {
    'DEFAULT': {
        'sequence_length': str(10),  # seconds
        'scene_threshold': str(30.0),
        'num_sequences': str(3),
        'output_format': "prores",
        'quality': "medium",
        'max_analysis_duration': str(MAX_ANALYSIS_DURATION),  # seconds
        'theme': 'dark'
    },
    'OUTPUT_FORMATS': {
        'prores': {'extension': '.mov', 'description': 'ProRes 422',
                    'profiles': {'low': 'ProRes 422 Proxy (smaller file)',
                                 'medium': 'ProRes 422 LT (balanced)',
                                 'high': 'ProRes 422 HQ (high quality)'}},
        'mp4': {'extension': '.mp4', 'description': 'MP4 (H.264)',
               'profiles': {'low': 'Fast encoding, lower quality',
                            'medium': 'Balanced quality and size',
                            'high': 'High quality, larger file size'}}
    },
    'QUALITY_SETTINGS': {
        'low': 'Low quality (smaller file size)',
        'medium': 'Medium quality (balanced)',
        'high': 'High quality (larger file size)'
    }
}

class ConfigManager:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file_path = Path("./config.ini")
        
        if not self.config_file_path.exists():
            # Create a default config file if it doesn't exist
            self.config.read_dict(DEFAULT_CONFIG)
            self.save_config()
        else:
            # Attempt to read existing config.ini
            self.load_config()


    def load_config(self):
        self.config.read(str(self.config_file_path))

    def save_config(self):
        """Save configuration to config.ini file."""
        with open(self.config_file_path, 'w') as configfile:
            self.config.write(configfile)

    def get(self, section, option, default=None):
        try:
            return self.config.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
            
    def getint(self, section, option, default=None):
        try:
            return self.config.getint(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default
    
    def getfloat(self, section, option, default=None):
        try:
            return self.config.getfloat(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default

    def set(self, section, option, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))
