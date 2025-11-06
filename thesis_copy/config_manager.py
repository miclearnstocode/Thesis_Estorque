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
                    print(f"✅ Config loaded from: {config_path}")
                    break
                except Exception as e:
                    logging.warning(f"Failed to read config from {config_path}: {e}")
                    print(f"❌ Failed to load config from {config_path}: {e}")
                    continue
        
        if not config_found:
            logging.warning("No config file found, using defaults")
            print("⚠️  No config file found, using defaults")
            self.set_defaults()
    
    def set_defaults(self):
        """Set default configuration values for PostgreSQL"""
        if not self.config.has_section('database'):
            self.config.add_section('database')
        
        # PostgreSQL defaults - using default PostgreSQL user
        self.config.set('database', 'host', 'localhost')
        self.config.set('database', 'user', 'postgres')  # Default PostgreSQL user
        self.config.set('database', 'password', '')  # Empty password - user will set this
        self.config.set('database', 'database', 'department')
        self.config.set('database', 'port', '5432')  # PostgreSQL default port
        
        # Add PostgreSQL specific section
        if not self.config.has_section('postgresql'):
            self.config.add_section('postgresql')
        
        self.config.set('postgresql', 'auto_start', 'true')
        self.config.set('postgresql', 'data_dir', r'C:\Program Files\PostgreSQL\16\data')  # Common default path
        self.config.set('postgresql', 'bin_dir', r'C:\Program Files\PostgreSQL\16\bin')   # Common default path
        self.config.set('postgresql', 'service_name', 'postgresql-x64-16')  # Common default service name
    
    def get_database_config(self):
        """Get database configuration as dictionary"""
        config = {
            'host': self.config.get('database', 'host', fallback='localhost'),
            'user': self.config.get('database', 'user', fallback='postgres'),  # Default to postgres
            'password': self.config.get('database', 'password', fallback=''),
            'database': self.config.get('database', 'database', fallback='department'),
            'port': self.config.getint('database', 'port', fallback=5432),
        }
        print(f"🔧 Database config: {config}")
        return config
    
    def get_postgres_config(self):
        """Get PostgreSQL specific configuration"""
        return {
            'auto_start': self.config.getboolean('postgresql', 'auto_start', fallback=True),
            'data_dir': self.config.get('postgresql', 'data_dir', fallback=r'C:\Program Files\PostgreSQL\16\data'),
            'bin_dir': self.config.get('postgresql', 'bin_dir', fallback=r'C:\Program Files\PostgreSQL\16\bin'),
            'service_name': self.config.get('postgresql', 'service_name', fallback='postgresql-x64-16')
        }
    
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

    def save_database_config(self, host, user, password, database, port):
        """Save database configuration back to config file"""
        try:
            self.config.set('database', 'host', host)
            self.config.set('database', 'user', user)
            self.config.set('database', 'password', password)
            self.config.set('database', 'database', database)
            self.config.set('database', 'port', str(port))
            
            # Save to the first config location that exists, or create new one
            base_path = self.get_base_path()
            config_path = os.path.join(base_path, 'config.ini')
            
            with open(config_path, 'w') as configfile:
                self.config.write(configfile)
            
            logging.info(f"Database configuration saved to: {config_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to save database configuration: {e}")
            return False

# Create global instance
config_manager = ConfigManager()