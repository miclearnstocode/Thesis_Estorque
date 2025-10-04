import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from config_manager import config_manager
import mysql.connector

def test_config_manager():
    print("Testing Config Manager...")
    
    # Test database config
    db_config = config_manager.get_database_config()
    print("Database Configuration:")
    for key, value in db_config.items():
        print(f"  {key}: {value}")
    
    # Test database connection
    try:
        conn = mysql.connector.connect(**db_config)
        if conn.is_connected():
            print("✅ Database connection successful!")
            conn.close()
        else:
            print("❌ Database connection failed")
    except Exception as e:
        print(f"❌ Database connection error: {e}")
    
    # Test icon paths
    test_icons = ['home', 'save', 'search']
    print("\nIcon Paths:")
    for icon in test_icons:
        path = config_manager.get_icon_path(icon)
        print(f"  {icon}: {path}")

if __name__ == "__main__":
    test_config_manager()