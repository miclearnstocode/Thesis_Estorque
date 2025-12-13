# postgres_manager.py
import os
import sys
import subprocess
import time
import psutil
import socket
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler('postgres_auto.log'),logging.StreamHandler()])

class PostgresManager:
    def __init__(self):
        self.postgres_path = self.find_postgres_installation()
        self.data_dir = None
        self.process = None
        self.db_password = 'comscie@2025'
        self.port = 5432  # Default port
        self.alternative_ports = [5433, 5434, 5435, 5436, 5437, 5438, 5439]
        self.current_port = None
        
    def find_postgres_installation(self):
        """Find PostgreSQL installation automatically"""
        logging.info("Searching for PostgreSQL installation...")
        
        # Common installation paths
        possible_paths = [
            r"D:\programs\Postgres18\bin",
            r"C:\Program Files\PostgreSQL\18\bin",
            r"C:\Program Files\PostgreSQL\17\bin",
            r"C:\Program Files\PostgreSQL\16\bin",
            r"C:\Program Files\PostgreSQL\15\bin",
            r"C:\Program Files\PostgreSQL\14\bin",
            r"C:\Program Files\PostgreSQL\13\bin",
            r"C:\Program Files\PostgreSQL\12\bin",
            r"C:\Program Files (x86)\PostgreSQL\18\bin",
            r"C:\Program Files (x86)\PostgreSQL\17\bin",
            r"C:\Program Files (x86)\PostgreSQL\16\bin",
        ]
        
        # Add environment variable paths
        env_paths = [
            os.environ.get('POSTGRES_PATH', ''),
            os.path.join(os.environ.get('ProgramFiles', ''), 'PostgreSQL\\18\\bin'),
            os.path.join(os.environ.get('ProgramFiles', ''), 'PostgreSQL\\17\\bin'),
            os.path.join(os.environ.get('ProgramFiles', ''), 'PostgreSQL\\16\\bin'),
        ]
        
        all_paths = possible_paths + [p for p in env_paths if p]
        
        for path in all_paths:
            if path and os.path.exists(path):
                pg_ctl_path = os.path.join(path, 'pg_ctl.exe')
                if os.path.exists(pg_ctl_path):
                    logging.info(f"Found PostgreSQL at: {path}")
                    return path
        
        logging.error("PostgreSQL installation not found")
        return None
    
    def find_data_directory(self):
        """Find PostgreSQL data directory"""
        if not self.postgres_path:
            return None
            
        # Common data directory locations
        possible_data_dirs = [
            r"D:\programs\Postgres18\data",
            r"C:\Program Files\PostgreSQL\18\data",
            r"C:\Program Files\PostgreSQL\17\data",
            r"C:\Program Files\PostgreSQL\16\data",
            r"C:\Program Files (x86)\PostgreSQL\18\data",
            r"C:\Program Files (x86)\PostgreSQL\17\data",
            r"C:\Program Files (x86)\PostgreSQL\16\data",
            r"C:\ProgramData\PostgreSQL\18\data",
            r"C:\ProgramData\PostgreSQL\17\data",
            r"C:\ProgramData\PostgreSQL\16\data",
            os.path.join(os.path.dirname(self.postgres_path), 'data'),
        ]
        
        for data_dir in possible_data_dirs:
            if data_dir and os.path.exists(data_dir):
                # Check if it's a PostgreSQL data directory
                postgresql_conf = os.path.join(data_dir, 'postgresql.conf')
                pg_hba_conf = os.path.join(data_dir, 'pg_hba.conf')
                pg_version = os.path.join(data_dir, 'PG_VERSION')
                
                if os.path.exists(postgresql_conf) or os.path.exists(pg_hba_conf) or os.path.exists(pg_version):
                    logging.info(f"Found PostgreSQL data directory: {data_dir}")
                    self.data_dir = data_dir
                    
                    # Check current port from config
                    self.current_port = self.get_port_from_config()
                    logging.info(f"Current configured port: {self.current_port}")
                    
                    return data_dir
        
        logging.error("PostgreSQL data directory not found")
        return None
    
    def get_port_from_config(self):
        """Read port from postgresql.conf"""
        if not self.data_dir:
            return 5432
            
        postgresql_conf = os.path.join(self.data_dir, 'postgresql.conf')
        if not os.path.exists(postgresql_conf):
            return 5432
            
        try:
            with open(postgresql_conf, 'r') as f:
                content = f.read()
                
            # Look for port setting
            import re
            port_match = re.search(r'port\s*=\s*(\d+)', content, re.IGNORECASE)
            if port_match:
                return int(port_match.group(1))
        except:
            pass
            
        return 5432
    
    def is_port_available(self, port):
        """Check if a port is available"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result != 0  # 0 means port is in use
        except:
            return False
    
    def find_available_port(self):
        """Find an available port for PostgreSQL"""
        # First try the default port
        if self.is_port_available(self.port):
            logging.info(f"Default port {self.port} is available")
            return self.port
            
        # Try alternative ports
        for port in self.alternative_ports:
            if self.is_port_available(port):
                logging.info(f"Alternative port {port} is available")
                return port
                
        # If no ports available, use default anyway (will fail later with clear error)
        logging.warning(f"No ports available, using default {self.port}")
        return self.port
    
    def update_port_in_config(self, port):
        """Update PostgreSQL configuration with new port"""
        if not self.data_dir:
            return False
            
        postgresql_conf = os.path.join(self.data_dir, 'postgresql.conf')
        if not os.path.exists(postgresql_conf):
            return False
            
        try:
            with open(postgresql_conf, 'r') as f:
                content = f.read()
            
            # Update or add port setting
            import re
            if re.search(r'port\s*=', content, re.IGNORECASE):
                # Update existing port setting
                new_content = re.sub(r'port\s*=\s*\d+', f'port = {port}', content, flags=re.IGNORECASE)
            else:
                # Add port setting at the end
                new_content = content + f'\nport = {port}\n'
            
            # Write back
            with open(postgresql_conf, 'w') as f:
                f.write(new_content)
                
            logging.info(f"Updated PostgreSQL port to {port} in config")
            self.current_port = port
            return True
            
        except Exception as e:
            logging.error(f"Failed to update port in config: {e}")
            return False
    
    def enable_and_start_service(self):
        """Enable and start PostgreSQL Windows service"""
        # First, find the service name
        service_names = [
            'postgresql-x64-18',
            'postgresql-x64-17',
            'postgresql-x64-16',
            'postgresql-x64-15',
            'postgresql-x64-14',
            'postgresql-x64-13',
            'postgresql-x64-12',
            'postgresql',
        ]
        
        for service_name in service_names:
            try:
                # Check if service exists
                check_result = subprocess.run(
                    ['sc', 'query', service_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if check_result.returncode == 0:
                    # Service exists, try to enable and start it
                    logging.info(f"Found PostgreSQL service: {service_name}")
                    
                    # Enable service (set to automatic)
                    logging.info(f"Enabling service {service_name}...")
                    enable_result = subprocess.run(
                        ['sc', 'config', service_name, 'start=auto'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if enable_result.returncode == 0:
                        logging.info(f"Service {service_name} enabled successfully")
                    else:
                        logging.warning(f"Could not enable service: {enable_result.stderr}")
                    
                    # Start service
                    logging.info(f"Starting service {service_name}...")
                    start_result = subprocess.run(
                        ['sc', 'start', service_name],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if start_result.returncode == 0:
                        logging.info(f"Service {service_name} started successfully")
                        return True
                    else:
                        logging.warning(f"Could not start service: {start_result.stderr}")
                        
            except Exception as e:
                logging.debug(f"Service {service_name} not found or error: {e}")
                continue
        
        logging.error("No PostgreSQL service could be started")
        return False
        
    def start_postgres_with_pg_ctl(self, port=None):
        """Start PostgreSQL using pg_ctl with specified port"""
        if not self.postgres_path or not self.data_dir:
            return False
            
        pg_ctl_path = os.path.join(self.postgres_path, 'pg_ctl.exe')
        if not os.path.exists(pg_ctl_path):
            return False
            
        # Use specified port or current port
        use_port = port if port else self.current_port
        
        # Check if PostgreSQL is already running on this port BEFORE trying to start
        if self.is_postgres_running(port=use_port):
            logging.info(f"✅ PostgreSQL is already running on port {use_port} (checked before pg_ctl)")
            self.current_port = use_port
            return True
        
        # Update config with port if needed
        if use_port and use_port != self.get_port_from_config():
            self.update_port_in_config(use_port)
        
        logging.info(f"Starting PostgreSQL on port {use_port}...")
        
        cmd = [
            pg_ctl_path,
            '-D', self.data_dir,
            'start',
            '-w',
            '-t', '90'  # 90 second timeout
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            stdout, stderr = process.communicate(timeout=100)
            
            logging.info(f"pg_ctl output: {stdout}")
            if stderr:
                logging.warning(f"pg_ctl errors: {stderr}")
            
            if process.returncode == 0:
                logging.info("PostgreSQL started successfully with pg_ctl")
                self.current_port = use_port
                return True
            else:
                # Check if error is because it's already running
                if "already running" in stderr.lower() or "another server might be running" in stderr.lower():
                    logging.info("PostgreSQL might already be running (from pg_ctl error)")
                    # Double-check if it's actually running
                    if self.is_postgres_running(port=use_port):
                        logging.info("✅ Confirmed PostgreSQL is running")
                        self.current_port = use_port
                        return True
                    else:
                        logging.warning("pg_ctl says it's running but we can't connect")
                        
                logging.error(f"pg_ctl failed with code: {process.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            logging.warning("pg_ctl command timed out")
            # Check if it started anyway
            if self.is_postgres_running(port=use_port):
                logging.info("✅ PostgreSQL started despite timeout")
                self.current_port = use_port
                return True
            return False
            
        except Exception as e:
            logging.error(f"Error starting PostgreSQL: {e}")
            return False
        
    def test_connection(self, port=None, timeout=5):
        """Test database connection on specified port"""
        try:
            import psycopg2
            use_port = port if port else self.current_port
            conn = psycopg2.connect(
                host='localhost',
                database='postgres',
                user='postgres',
                password=self.db_password,
                port=use_port,
                connect_timeout=timeout)
            conn.close()
            logging.info(f"Connection test successful on port {use_port}")
            return True
        except Exception as e:
            logging.debug(f"Connection test failed on port {use_port}: {e}")
            return False
    
    def is_postgres_running(self, port=None):
        """Check if PostgreSQL is running on specified port"""
        # First check connection - this is the most reliable
        use_port = port if port else self.current_port
        
        if self.test_connection(port=use_port, timeout=3):
            logging.info(f"PostgreSQL is running and accessible on port {use_port}")
            return True
            
        # Check processes as fallback
        try:
            postgres_processes = []
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    proc_name = proc.info['name'].lower()
                    if 'postgres' in proc_name:
                        postgres_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                    continue
            
            if postgres_processes:
                logging.info(f"Found {len(postgres_processes)} PostgreSQL processes")
                # Check if any of them are listening on our port
                try:
                    import psutil
                    connections = psutil.net_connections()
                    for conn in connections:
                        if conn.status == 'LISTEN' and conn.laddr.port == use_port:
                            logging.info(f"Found process listening on port {use_port}: {conn}")
                            return True
                except:
                    pass
                
                # If we found processes but can't check ports, assume it's running
                return True
                
        except Exception as e:
            logging.debug(f"Error checking processes: {e}")
            
        return False

    def start_postgres(self):
        """Main method to start PostgreSQL with automatic configuration"""
        logging.info("Starting PostgreSQL with automatic configuration...")
        
        # Find installation if not already found
        if not self.postgres_path:
            self.postgres_path = self.find_postgres_installation()
        
        if not self.postgres_path:
            logging.error("Cannot start PostgreSQL: Installation not found")
            return False
        
        # Find data directory
        if not self.data_dir:
            self.data_dir = self.find_data_directory()
        
        if not self.data_dir:
            logging.error("Cannot start PostgreSQL: Data directory not found")
            return False
        
        # Get current port from config
        self.current_port = self.get_port_from_config()
        
        # FIRST: Check if PostgreSQL is already running
        logging.info(f"Checking if PostgreSQL is already running on port {self.current_port}...")
        if self.is_postgres_running(port=self.current_port):
            logging.info(f"✅ PostgreSQL is already running on port {self.current_port}")
            return True
        
        # If not running, also check default port 5432
        if self.current_port != 5432:
            logging.info("Checking default port 5432...")
            if self.is_postgres_running(port=5432):
                logging.info("✅ PostgreSQL is running on default port 5432")
                self.current_port = 5432
                return True
        
        # SECOND: Check all alternative ports
        logging.info("Checking alternative ports...")
        for port in [self.current_port, 5432] + self.alternative_ports:
            if self.is_postgres_running(port=port):
                logging.info(f"✅ PostgreSQL found running on port {port}")
                self.current_port = port
                return True
        
        # THIRD: If PostgreSQL is not running anywhere, then try to start it
        logging.info("PostgreSQL is not running, attempting to start...")
        
        # Find available port
        available_port = self.find_available_port()
        
        # Try to enable and start Windows service first
        logging.info("Attempting to start via Windows service...")
        if self.enable_and_start_service():
            # Wait a bit and test connection
            time.sleep(3)
            if self.is_postgres_running(port=available_port):
                logging.info("✅ PostgreSQL started via service")
                return True
        
        # If service method failed, try direct pg_ctl start
        logging.info("Service method failed, trying direct start with pg_ctl...")
        
        # Update port in config if needed
        if available_port != self.current_port:
            self.update_port_in_config(available_port)
        
        # Start with pg_ctl
        if self.start_postgres_with_pg_ctl(port=available_port):
            return True
        
        # Last resort: try with different ports
        logging.info("Trying alternative ports...")
        for port in [self.current_port] + self.alternative_ports:
            if port == self.current_port:
                continue  # Already tried
                
            logging.info(f"Trying port {port}...")
            if self.update_port_in_config(port):
                if self.start_postgres_with_pg_ctl(port=port):
                    return True
        
        logging.error("All PostgreSQL startup methods failed")
        return False

    def ensure_postgres_running(self):
        """Ensure PostgreSQL is running, start if necessary"""
        # First check if it's already running on current port
        if self.is_postgres_running(port=self.current_port):
            logging.info(f"✅ PostgreSQL is already running on port {self.current_port}")
            return True
        
        # Check all possible ports where PostgreSQL might be running
        all_ports_to_check = [5432, self.current_port] + self.alternative_ports
        
        for port in all_ports_to_check:
            if self.is_postgres_running(port=port):
                logging.info(f"✅ Found PostgreSQL running on port {port}")
                self.current_port = port
                return True
        
        # If not running anywhere, then start it
        logging.info("PostgreSQL is not running, starting it now...")
        return self.start_postgres()

    def get_connection_info(self):
        """Get connection information for database handler"""
        return {
            'host': 'localhost',
            'port': self.current_port,
            'user': 'postgres',
            'password': self.db_password,
            'database': 'postgres'
        }