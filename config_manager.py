# config_manager.py
import os
import sys
import logging
from configparser import ConfigParser

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.config = ConfigParser()
        self.load_config()
        self._initialized = True
    
    def get_base_path(self):
        """Get the base path for file operations (works for both dev and PyInstaller)"""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return sys._MEIPASS
        else:
            # Running as script
            return os.path.dirname(os.path.abspath(__file__))
    
    def load_config(self):
        """Load configuration from multiple possible locations"""
        base_path = self.get_base_path()
        
        config_locations = [
            os.path.join(base_path, 'config.ini'),
            os.path.join(os.getcwd(), 'config.ini'),
            'config.ini',
            '../config.ini'
        ]
        
        config_found = False
        for config_path in config_locations:
            if os.path.exists(config_path):
                try:
                    self.config.read(config_path)
                    config_found = True
                    logging.info(f"Configuration loaded from: {config_path}")
                    print(f"✅ Config loaded from: {config_path}")  # Debug print
                    break
                except Exception as e:
                    logging.warning(f"Failed to read config from {config_path}: {e}")
                    print(f"❌ Failed to load config from {config_path}: {e}")  # Debug print
                    continue
        
        if not config_found:
            logging.warning("No config file found, using defaults")
            print("⚠️  No config file found, using defaults")  # Debug print
            self.set_defaults()
    
    def set_defaults(self):
        """Set default configuration values"""
        if not self.config.has_section('database'):
            self.config.add_section('database')
        
        self.config.set('database', 'host', 'localhost')
        self.config.set('database', 'user', 'comscie')
        self.config.set('database', 'password', 'BS_Comscie@2025!')
        self.config.set('database', 'database', 'department')
        self.config.set('database', 'port', '3306')
        self.config.set('database', 'allow_local_infile', 'True')
    
    def get_database_config(self):
        """Get database configuration as dictionary"""
        config = {
            'host': self.config.get('database', 'host', fallback='localhost'),
            'user': self.config.get('database', 'user', fallback='comscie'),
            'password': self.config.get('database', 'password', fallback='BS_Comscie@2025!'),
            'database': self.config.get('database', 'database', fallback='department'),
            'port': self.config.getint('database', 'port', fallback=3306),
            'allow_local_infile': self.config.getboolean('database', 'allow_local_infile', fallback=True)
        }
        print(f"🔧 Database config: {config}")  # Debug print
        return config
    
    def get_icon_path(self, icon_name):
        """Get icon path from configuration"""
        base_path = self.get_base_path()
        default_path = f'icons/{icon_name}.png'
        
        # Try to get from config
        try:
            configured_path = self.config.get('icons', icon_name)
            full_path = os.path.join(base_path, configured_path)
            if os.path.exists(full_path):
                return full_path
        except:
            pass
        
        # Fallback to default location
        fallback_path = os.path.join(base_path, default_path)
        if os.path.exists(fallback_path):
            return fallback_path
        
        # Final fallback
        return default_path

# Create global instance
config_manager = ConfigManager()