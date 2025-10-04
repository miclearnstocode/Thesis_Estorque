import os
import sys
import subprocess
import psutil
import time
import threading
import logging
from tkinter import messagebox

class XAMPPManager:
    def __init__(self):
        self.xampp_paths = self.find_xampp_paths()
        self.apache_process = None
        self.mysql_process = None
        self.services_started = False
        
    def find_xampp_paths(self):
        """Find XAMPP installation paths"""
        possible_paths = [
            r"C:\xampp",
            r"D:\xampp",
            r"E:\xampp", 
            os.path.join(os.environ.get('ProgramFiles', ''), 'xampp'),
            os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'xampp')
        ]
        
        for path in possible_paths:
            control_panel = os.path.join(path, 'xampp-control.exe')
            if os.path.exists(control_panel):
                logging.info(f"XAMPP found at: {path}")
                return path
        return None
    
    def is_service_running(self, service_name):
        """Check if a service is running"""
        try:
            for proc in psutil.process_iter(['name']):
                if service_name.lower() in proc.info['name'].lower():
                    return True
            return False
        except Exception as e:
            logging.error(f"Error checking service {service_name}: {e}")
            return False
    
    def start_mysql(self):
        """Start MySQL service"""
        try:
            if self.is_service_running('mysqld'):
                logging.info("MySQL is already running")
                return True
                
            if not self.xampp_paths:
                logging.error("XAMPP path not found")
                return False
                
            mysql_executable = os.path.join(self.xampp_paths, 'mysql', 'bin', 'mysqld.exe')
            if os.path.exists(mysql_executable):
                # Start MySQL as a subprocess
                self.mysql_process = subprocess.Popen(
                    [mysql_executable],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                logging.info("MySQL service started")
                return True
            else:
                logging.error(f"MySQL executable not found at: {mysql_executable}")
                return False
        except Exception as e:
            logging.error(f"Failed to start MySQL: {e}")
            return False
    
    def start_apache(self):
        """Start Apache service"""
        try:
            if self.is_service_running('httpd'):
                logging.info("Apache is already running")
                return True
                
            if not self.xampp_paths:
                logging.error("XAMPP path not found")
                return False
                
            apache_executable = os.path.join(self.xampp_paths, 'apache', 'bin', 'httpd.exe')
            if os.path.exists(apache_executable):
                self.apache_process = subprocess.Popen(
                    [apache_executable],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                logging.info("Apache service started")
                return True
            else:
                logging.error(f"Apache executable not found at: {apache_executable}")
                return False
        except Exception as e:
            logging.error(f"Failed to start Apache: {e}")
            return False
    
    def wait_for_mysql_ready(self, timeout=30):
        """Wait for MySQL to be ready to accept connections"""
        import mysql.connector
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Try to connect to MySQL
                conn = mysql.connector.connect(
                    host='localhost',
                    user='comscie',
                    password='BS_Comscie@2025!',
                    connection_timeout=5
                )
                if conn.is_connected():
                    conn.close()
                    logging.info("MySQL is ready and accepting connections")
                    return True
            except Exception:
                # MySQL not ready yet, wait and retry
                time.sleep(2)
        
        logging.error("MySQL failed to start within timeout period")
        return False
    
    def start_xampp_control_panel(self):
        """Start XAMPP Control Panel for manual control"""
        try:
            if not self.xampp_paths:
                return False
                
            control_panel = os.path.join(self.xampp_paths, 'xampp-control.exe')
            if os.path.exists(control_panel):
                subprocess.Popen([control_panel])
                logging.info("XAMPP Control Panel started")
                return True
        except Exception as e:
            logging.error(f"Failed to start XAMPP Control Panel: {e}")
        return False
    
    def stop_services(self):
        """Stop services when application closes"""
        try:
            logging.info("Stopping XAMPP services...")
            
            # Terminate subprocesses
            if self.apache_process:
                self.apache_process.terminate()
            if self.mysql_process:
                self.mysql_process.terminate()
            
            # Wait for processes to terminate
            time.sleep(2)
            
            # Force kill if still running
            for proc in psutil.process_iter():
                try:
                    if proc.name().lower() in ['httpd.exe', 'mysqld.exe']:
                        proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            self.services_started = False
            logging.info("XAMPP services stopped")
            
        except Exception as e:
            logging.error(f"Error stopping services: {e}")
    
    def check_and_start_services(self):
        """Main method to check and start services"""
        logging.info("Checking XAMPP services...")
        
        # Check if XAMPP is installed
        if not self.xampp_paths:
            logging.warning("XAMPP not found. Please install XAMPP or start services manually.")
            return False
        
        # Check if services are already running
        mysql_running = self.is_service_running('mysqld')
        apache_running = self.is_service_running('httpd')
        
        if mysql_running and apache_running:
            logging.info("Both MySQL and Apache are already running")
            self.services_started = True
            return True
        
        # Start services that aren't running
        services_ok = True
        
        if not mysql_running:
            logging.info("Starting MySQL...")
            if not self.start_mysql():
                services_ok = False
                logging.error("Failed to start MySQL")
        
        if not apache_running:
            logging.info("Starting Apache...")
            if not self.start_apache():
                services_ok = False
                logging.error("Failed to start Apache")
        
        if services_ok:
            # Wait for MySQL to be ready
            if not mysql_running:  # Only wait if we started it
                logging.info("Waiting for MySQL to be ready...")
                if self.wait_for_mysql_ready():
                    self.services_started = True
                    logging.info("All services started successfully")
                    return True
                else:
                    logging.error("MySQL failed to become ready")
                    return False
            else:
                self.services_started = True
                return True
        
        return False

# Global instance
xampp_manager = XAMPPManager()