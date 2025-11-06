# postgres_manager.py
import os
import sys
import subprocess
import time
import psutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('postgres_startup.log'),
        logging.StreamHandler()
    ]
)

class PostgresManager:
    def __init__(self):
        self.postgres_path = self.find_postgres_installation()
        self.data_dir = None
        self.process = None
        self.db_password = 'comscie@2025'  # Centralized password
        
    def find_postgres_installation(self):
        """Find PostgreSQL installation path automatically"""
        possible_paths = [
            # Common PostgreSQL installation paths on Windows
            r"D:\programs\Postgres18\bin",
            r"C:\Program Files\PostgreSQL\18\bin",
            r"C:\Program Files\PostgreSQL\17\bin",
            r"C:\Program Files\PostgreSQL\16\bin",
            r"C:\Program Files\PostgreSQL\15\bin",
            r"C:\Program Files\PostgreSQL\14\bin",
            r"C:\Program Files\PostgreSQL\13\bin",
            r"C:\Program Files\PostgreSQL\12\bin",
            
            # Environment variable paths
            os.environ.get('POSTGRES_PATH', ''),
            os.path.join(os.environ.get('ProgramFiles', ''), 'PostgreSQL\\18\\bin'),
            os.path.join(os.environ.get('ProgramFiles', ''), 'PostgreSQL\\17\\bin'),
            os.path.join(os.environ.get('ProgramFiles', ''), 'PostgreSQL\\16\\bin'),
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                pg_ctl_path = os.path.join(path, 'pg_ctl.exe')
                if os.path.exists(pg_ctl_path):
                    logging.info(f"Found PostgreSQL at: {path}")
                    return path
        
        logging.error("PostgreSQL installation not found in common locations")
        return None
    
    def find_data_directory(self):
        """Find PostgreSQL data directory"""
        if self.postgres_path:
            # Common data directory locations
            possible_data_dirs = [
                r"D:\programs\Postgres18\data",
                r"C:\Program Files\PostgreSQL\18\data",
                r"C:\Program Files\PostgreSQL\17\data",
                r"C:\Program Files\PostgreSQL\16\data",
                os.path.join(os.path.dirname(self.postgres_path), 'data'),
                # Also check AppData locations
                os.path.join(os.environ.get('APPDATA', ''), 'PostgreSQL\\18\\data'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'PostgreSQL\\18\\data'),
            ]
            
            for data_dir in possible_data_dirs:
                if data_dir and os.path.exists(data_dir):
                    # Check if it contains PostgreSQL files
                    postgresql_conf = os.path.join(data_dir, 'postgresql.conf')
                    pg_version = os.path.join(data_dir, 'PG_VERSION')
                    if os.path.exists(postgresql_conf) or os.path.exists(pg_version):
                        logging.info(f"Found PostgreSQL data directory: {data_dir}")
                        self.data_dir = data_dir
                        return data_dir
        
        logging.error("PostgreSQL data directory not found")
        return None
    
    def is_postgres_running(self):
        """Check if PostgreSQL is already running"""
        try:
            # Method 1: Check running processes
            postgres_running = False
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    proc_name = proc.info.get('name', '').lower()
                    if 'postgres' in proc_name:
                        postgres_running = True
                        logging.info(f"Found PostgreSQL process: {proc.info.get('name')}")
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if postgres_running:
                # Method 2: Verify it's accepting connections
                return self.test_connection()
            
            return False
                
        except Exception as e:
            logging.error(f"Error checking PostgreSQL status: {e}")
            return False
    
    def test_connection(self, timeout=5):
        """Test database connection"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host='localhost',
                database='postgres',
                user='postgres',
                password=self.db_password,
                connect_timeout=timeout
            )
            conn.close()
            logging.info("PostgreSQL connection test successful")
            return True
        except Exception as e:
            logging.debug(f"PostgreSQL connection test failed: {e}")
            return False
    
    def start_postgres(self):
        """Start PostgreSQL server with improved error handling"""
        logging.info("=" * 60)
        logging.info("Starting PostgreSQL startup procedure")
        logging.info("=" * 60)
        
        # Check if already running
        if self.is_postgres_running():
            logging.info("PostgreSQL is already running")
            return True
        
        # Verify installation
        if not self.postgres_path:
            logging.error("Cannot start PostgreSQL: Installation not found")
            return False
        
        # Find data directory
        if not self.data_dir:
            self.data_dir = self.find_data_directory()
            
        if not self.data_dir:
            logging.error("Cannot start PostgreSQL: Data directory not found")
            return False
        
        # Try primary startup method
        if self.start_postgres_with_pg_ctl():
            return True
        
        # Try Windows service method
        if self.start_postgres_as_service():
            return True
        
        logging.error("All PostgreSQL startup methods failed")
        return False
    
    def start_postgres_with_pg_ctl(self):
        """Start PostgreSQL using pg_ctl"""
        try:
            pg_ctl_path = os.path.join(self.postgres_path, 'pg_ctl.exe')
            
            if not os.path.exists(pg_ctl_path):
                logging.error(f"pg_ctl not found at: {pg_ctl_path}")
                return False
            
            logging.info(f"Starting PostgreSQL with pg_ctl from: {self.data_dir}")
            
            # Build command
            cmd = [
                pg_ctl_path,
                '-D', self.data_dir,
                'start',
                '-w',  # Wait for start to complete
                '-t', '60'  # Timeout in seconds
            ]
            
            logging.info(f"Executing command: {' '.join(cmd)}")
            
            # Execute pg_ctl start
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=70)
                
                logging.info(f"pg_ctl stdout: {stdout}")
                if stderr:
                    logging.warning(f"pg_ctl stderr: {stderr}")
                
                if process.returncode == 0:
                    logging.info("pg_ctl returned success")
                    
                    # Wait for PostgreSQL to be ready
                    if self.wait_for_postgres(timeout=45):
                        logging.info("PostgreSQL started successfully with pg_ctl")
                        return True
                    else:
                        logging.error("PostgreSQL started but not accepting connections")
                        return False
                else:
                    logging.error(f"pg_ctl failed with return code: {process.returncode}")
                    return False
                    
            except subprocess.TimeoutExpired:
                logging.warning("pg_ctl command timed out")
                process.kill()
                
                # Check if it started despite timeout
                if self.wait_for_postgres(timeout=30):
                    logging.info("PostgreSQL started successfully (despite timeout)")
                    return True
                    
                return False
                
        except Exception as e:
            logging.error(f"Error starting PostgreSQL with pg_ctl: {e}")
            return False
    
    def start_postgres_as_service(self):
        """Start PostgreSQL as Windows service"""
        try:
            logging.info("Attempting to start PostgreSQL as Windows service")
            
            # Common PostgreSQL service names
            service_names = [
                'postgresql-x64-18',
                'postgresql-x64-17',
                'postgresql-x64-16',
                'postgresql-x64-15',
                'postgresql-x64-14',
                'postgresql',
            ]
            
            for service_name in service_names:
                try:
                    logging.info(f"Trying to start service: {service_name}")
                    
                    result = subprocess.run(
                        ['net', 'start', service_name],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        logging.info(f"Service '{service_name}' started successfully")
                        
                        # Wait for connection
                        if self.wait_for_postgres(timeout=30):
                            logging.info("PostgreSQL is accepting connections")
                            return True
                    else:
                        logging.debug(f"Service '{service_name}' start failed: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    logging.warning(f"Service '{service_name}' start timed out")
                except Exception as e:
                    logging.debug(f"Could not start service '{service_name}': {e}")
            
            logging.error("No PostgreSQL service could be started")
            return False
            
        except Exception as e:
            logging.error(f"Error starting PostgreSQL as service: {e}")
            return False
    
    def wait_for_postgres(self, timeout=45):
        """Wait for PostgreSQL to be ready to accept connections"""
        logging.info(f"Waiting for PostgreSQL to accept connections (timeout: {timeout}s)")
        
        start_time = time.time()
        attempt = 0
        
        while time.time() - start_time < timeout:
            attempt += 1
            
            if self.test_connection(timeout=3):
                logging.info(f"PostgreSQL ready after {attempt} attempts ({time.time() - start_time:.1f}s)")
                return True
            
            if attempt % 5 == 0:
                elapsed = time.time() - start_time
                logging.info(f"Still waiting... (attempt {attempt}, {elapsed:.1f}s elapsed)")
            
            time.sleep(2)
        
        logging.error(f"PostgreSQL did not become ready within {timeout} seconds")
        return False
    
    def stop_postgres(self):
        """Stop PostgreSQL server"""
        if not self.postgres_path or not self.data_dir:
            logging.warning("Cannot stop PostgreSQL: paths not initialized")
            return
        
        try:
            pg_ctl_path = os.path.join(self.postgres_path, 'pg_ctl.exe')
            
            logging.info("Stopping PostgreSQL...")
            
            subprocess.run(
                [pg_ctl_path, '-D', self.data_dir, 'stop', '-m', 'fast'],
                timeout=30,
                capture_output=True
            )
            
            logging.info("PostgreSQL stopped")
            
        except Exception as e:
            logging.error(f"Error stopping PostgreSQL: {e}")
    
    def ensure_postgres_running(self):
        """Ensure PostgreSQL is running, start if necessary"""
        logging.info("Ensuring PostgreSQL is running...")
        
        if self.is_postgres_running():
            logging.info("PostgreSQL is already running")
            return True
        else:
            logging.info("PostgreSQL not running, attempting to start...")
            success = self.start_postgres()
            
            if success:
                logging.info("PostgreSQL started successfully")
            else:
                logging.error("Failed to start PostgreSQL")
                
            return success
    
    def get_postgres_status(self):
        """Get detailed status information about PostgreSQL"""
        status = {
            'installation_found': self.postgres_path is not None,
            'installation_path': self.postgres_path,
            'data_directory_found': self.data_dir is not None,
            'data_directory': self.data_dir,
            'is_running': self.is_postgres_running(),
            'can_connect': self.test_connection(timeout=3)
        }
        
        return status