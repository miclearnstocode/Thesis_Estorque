import logging
from CTkMessagebox import CTkMessagebox
import customtkinter as ctk
from PIL import Image
import importlib
import threading
import sys , time
import psycopg2
import student_screen , curriculum_screen, archive_screen, appraisal_screen
import grade_screen, admin_screen
from server import Peer
from loginform import LoginForm
from database import DatabaseHandler
import database
import socket
import urllib.request
import psutil
from tkinter import messagebox
from postgres_manager import PostgresManager

class Application(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ComputerScience Application")
        self.postgres_manager = PostgresManager()  
        
        self.current_user_email = None
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Set window to full screen dimensions
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Make window fullscreen
        self.attributes('-fullscreen', True)
        
        # Add escape key binding to exit fullscreen
        self.bind("<Escape>", self.exit_fullscreen)
        
        # Set default color theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Load all images at initialization
        self.load_images()

        # Initialize database_ready flag
        self.database_ready = False
        
        # Start PostgreSQL BEFORE showing any UI
        self.start_postgresql()
        
    def start_postgresql(self):
        """Start PostgreSQL server with blocking UI until ready"""
        # Withdraw main window
        self.withdraw()
        
        # Create startup dialog
        startup_dialog = ctk.CTkToplevel(self)
        startup_dialog.title("Starting Database")
        startup_dialog.geometry("450x200")
        startup_dialog.resizable(False, False)
        startup_dialog.attributes('-topmost', True)
        startup_dialog.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close button
        
        # Center the dialog
        startup_dialog.update_idletasks()
        x = (self.winfo_screenwidth() - 450) // 2
        y = (self.winfo_screenheight() - 200) // 2
        startup_dialog.geometry(f"450x200+{x}+{y}")
        
        # Add loading content
        loading_label = ctk.CTkLabel(startup_dialog, text="Starting PostgreSQL Database...", font=("Helvetica", 16, "bold"))
        loading_label.pack(pady=20)
        
        progress_bar = ctk.CTkProgressBar(startup_dialog,width=350, mode='indeterminate')
        progress_bar.pack(pady=15)
        progress_bar.start()
        
        status_label = ctk.CTkLabel(startup_dialog, text="Initializing database server...",font=("Helvetica", 12))
        status_label.pack(pady=10)
        
        def update_status(message):
            """Update status message in UI thread"""
            status_label.configure(text=message)
            startup_dialog.update()
        
        def start_database():
            """Start database in separate thread"""
            try:
                update_status("Checking PostgreSQL installation...")
                
                if not self.postgres_manager.postgres_path:
                    self.after(0, lambda: self.show_error_and_quit(startup_dialog,"PostgreSQL installation not found. Please install PostgreSQL and try again."))
                    return
                
                update_status("Locating data directory...")
                
                if not self.postgres_manager.find_data_directory():
                    self.after(0, lambda: self.show_error_and_quit(startup_dialog,"PostgreSQL data directory not found. Please check your PostgreSQL installation."))
                    return
                
                update_status("Starting PostgreSQL server (this may take a moment)...")
                
                # Start PostgreSQL
                if not self.postgres_manager.start_postgres():
                    # Even if start_postgres returns False, check if it's actually running
                    update_status("Verifying database status...")
                    time.sleep(3)
                    
                    if not self.postgres_manager.is_postgres_running():
                        self.after(0, lambda: self.show_error_and_quit(
                            startup_dialog,
                            "Failed to start PostgreSQL server. The server may already be running or there's a configuration issue."
                        ))
                        return
                    else:
                        update_status("PostgreSQL is running, verifying connection...")
                
                update_status("Verifying database connection...")
                
                # Give extra time for database to be fully ready
                time.sleep(2)
                
                # Verify database connection with retries
                connection_verified = False
                for attempt in range(5):
                    try:
                        update_status(f"Testing connection (attempt {attempt + 1}/5)...")
                        
                        if self.postgres_manager.test_connection(timeout=5):
                            connection_verified = True
                            break
                        
                        time.sleep(2)
                        
                    except Exception as e:
                        logging.warning(f"Connection test {attempt + 1} failed: {e}")
                        if attempt < 4:
                            time.sleep(2)
                
                if not connection_verified:
                    self.after(0, lambda: self.show_error_and_quit(startup_dialog,"PostgreSQL started but cannot accept connections. Please check your database configuration."))
                    return
                
                update_status("Database started successfully!")
                time.sleep(0.5)
                
                # Set database ready flag
                self.database_ready = True
                
                # Close startup dialog and show main window
                self.after(0, lambda: self.complete_startup(startup_dialog))
                
            except Exception as e:
                logging.error(f"Error in start_database: {e}")
                self.after(0, lambda: self.show_error_and_quit(startup_dialog,f"Critical error starting database: {str(e)}"))
        
        # Start database initialization in separate thread
        db_thread = threading.Thread(target=start_database, daemon=True)
        db_thread.start()
        
    def show_error_and_quit(self, dialog, message):
        """Show error message and quit application"""
        dialog.destroy()
        CTkMessagebox(title="Database Error", message=message,icon="cancel")
        self.quit()
    
    def complete_startup(self, dialog):
        """Complete startup process after database is ready"""
        dialog.destroy()
        self.deiconify()
        
        # Now create login frame
        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.pack(expand=True, fill="both")
        
        # Create login form with callbacks
        self.login_form = LoginForm(self.login_frame, login_success_callback=self.login_success, admin_login_callback=self.admin_login_success)
        
        # Preload grade data
        self.grade_data = self.preload_grade_data()
    
    def start_server(self):
        # Start the server in a separate thread to avoid blocking the UI
        server = Peer()
        server.start_server

    def preload_grade_data(self):
        """Preload grade data for all semesters"""
        try:
            # For now, return empty data to avoid the error
            return {}
        except Exception as e:
            print(f"Error preloading grade data: {e}")
            return {}

    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode (optional)"""
        self.attributes('-fullscreen', False)

    def show_splash_screen(self):
        # Load and set background image first (behind splash)
        bg_image = Image.open(LoginForm.resource_path("Image/Gradient.jpg"))
        self.splash_bg = ctk.CTkImage(light_image=bg_image, dark_image=bg_image, size=(self.winfo_screenwidth(), self.winfo_screenheight()))
        
        # Create background label that covers entire screen
        self.bg_window = ctk.CTkToplevel(self)
        self.bg_window.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        self.bg_window.overrideredirect(True)
        
        bg_label = ctk.CTkLabel(self.bg_window, image=self.splash_bg, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Create splash screen window
        self.splash = ctk.CTkToplevel(self.bg_window)
        self.splash.title("")
        self.splash.geometry("400x500")
        self.splash.overrideredirect(True) 
        
        # Center the splash screen
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 500) // 2
        self.splash.geometry(f"400x500+{x}+{y}")
        
        # Configure white background for splash
        self.splash.configure(fg_color="white")
        
        # Load CapSU logo
        try:
            csu_logo = Image.open(LoginForm.resource_path("Image/Capiz_State_University_2.png"))
            self.csu_logo_image = ctk.CTkImage(light_image=csu_logo,dark_image=csu_logo,size=(300, 300))
            
            # Create and pack logo label
            logo_label = ctk.CTkLabel(self.splash,image=self.csu_logo_image,text="")
            logo_label.pack(pady=30)
            
        except Exception as e:
            print(f"Error loading CapSU logo: {e}")
        
        # Add welcome text
        welcome_label = ctk.CTkLabel(self.splash,text="Bachelor of Science in Computer Science  ", font=("Vivaldi", 20, "bold"),text_color="black")
        welcome_label.pack(pady=10)
        
        # Add progress bar
        self.progress = ctk.CTkProgressBar(self.splash,width=300,height=15,corner_radius=10,mode="determinate",progress_color="#1E90FF")
        self.progress.pack(pady=20)
        self.progress.set(0)
        
        # Loading text
        self.loading_label = ctk.CTkLabel(self.splash,text="Loading...",font=("Helvetica", 12, 'bold'),text_color="black")
        self.loading_label.pack(pady=5)
        
        # Make splash screen appear on top
        self.splash.lift()
        self.splash.attributes('-topmost', True)
        
        # Start progress bar update
        self.update_progress_bar()

    def update_progress_bar(self):
        def progress():
            try:
                # Define system components to check with more detailed messages and weights
                components = [
                    ("Checking system compatibility", self.check_system_requirements, 15),
                    ("Loading essential modules", self.check_modules, 20),
                    ("Establishing database connection", self.check_database, 25),
                    ("Initializing user interface", self.check_ui_components, 15),
                    ("Performing final system checks", self.check_final_setup, 15),
                    ("Verifying network connectivity", self.check_network, 10)]
                
                # Calculate total weight to ensure 100%
                total_weight = sum(weight for _, _, weight in components)
                
                # Track cumulative progress
                cumulative_progress = 0
                
                # Ensure initial message
                self.splash.after(0, self.loading_label.configure, {'text': "Starting system initialization...", 'text_color': "blue"})
                
                # Iterate through components with detailed progress tracking
                for message, check_function, weight in components:
                    try:
                        # Update loading message
                        def update_loading(msg, color="black"):
                            if hasattr(self, 'loading_label') and self.loading_label:
                                self.loading_label.configure(text=msg, text_color=color)
                        
                        # Dispatch message update
                        self.splash.after(0, update_loading, f"{message}...", "blue")
                        
                        # Small delay to show message
                        time.sleep(0.5)
                        
                        # Perform component check
                        check_result = check_function()
                        
                        if not check_result:
                            raise Exception(f"Failed to {message.lower()}")
                        
                        # Calculate and update progress
                        cumulative_progress += weight
                        progress_value = cumulative_progress / total_weight
                        
                        # Update progress bar
                        def update_progress():
                            if hasattr(self, 'progress') and self.progress:
                                self.progress.set(min(progress_value, 1.0))
                        
                        self.splash.after(0, update_progress)
                        
                        # Success indication
                        self.splash.after(0, update_loading, f"{message}... ✓", "green")
                        
                        # Small delay to show success
                        time.sleep(0.3)
                    
                    except Exception as component_error:
                        # Error handling
                        error_msg = f"Error in {message}: {str(component_error)}"
                        self.splash.after(0, update_loading, error_msg, "red")
                        
                        # Raise to potentially stop further processing
                        raise
                
                # Final setup
                def finalize_startup():
                    if hasattr(self, 'progress') and self.progress:
                        self.progress.set(1)
                    
                    if hasattr(self, 'loading_label') and self.loading_label:
                        self.loading_label.configure(text="System ready!", text_color='green')
                
                self.splash.after(0, finalize_startup)
                
                # Close splash screen and show main menu
                def close_splash():
                    if hasattr(self, 'splash') and self.splash:
                        self.splash.destroy()
                    self.show_with_transition()
                
                self.splash.after(1000, close_splash)
                
            except Exception as e:
                def handle_error(error_message=None):
                    # Update loading label
                    if hasattr(self, 'loading_label') and self.loading_label:
                        self.loading_label.configure(text=error_message if error_message else "An error occurred", text_color='red')
                    
                    # Show error dialog
                    CTkMessagebox(title="System Initialization Error",  message=error_message if error_message else "An error occurred", icon="cancel", option_1="Exit")
                    
                    # Attempt graceful shutdown
                    self.quit()
                
                self.splash.after(0, handle_error, str(e))

        
        # Start progress in a daemon thread
        threading.Thread(target=progress, daemon=True).start()
        
    def check_system_requirements(self):
        """Check if system meets basic requirements"""
        try:
            # Check Python version
            if sys.version_info < (3, 7):
                raise Exception("Python 3.7 or higher is required")
            
            if psutil.virtual_memory().available < 500 * 1024 * 1024:
                print("Warning: Low available memory. The application may run slowly.")
                        
            return True
        except Exception as e:
            print(f"System requirements check failed: {e}")
            return False

    def check_modules(self):
        """Check if all required modules are available"""
        required_modules = ['customtkinter', 'PIL', 'psycopg2', 'pandas', 'CTkMessagebox']

        try:
            for module in required_modules:
                importlib.import_module(module)
            return True
        except ImportError as e:
            print(f"Module check failed: {e}")
            return False

    def check_database(self):
        """Check database connectivity and required tables - PostgreSQL version"""
        db = None
        try:
            # Wait a bit more for database to be fully ready after pg_ctl timeout
            if not self.database_ready:
                logging.info("Database not marked as ready, waiting for initialization...")
                time.sleep(3)
            
            # Ensure PostgreSQL is actually running
            if not self.postgres_manager.is_postgres_running():
                logging.error("PostgreSQL is not running")
                raise Exception("Database server is not running")
            
            # Try to establish connection with retries
            max_retries = 3
            db = None
            
            for attempt in range(max_retries):
                try:
                    logging.info(f"Attempting database connection (attempt {attempt + 1}/{max_retries})...")
                    db = DatabaseHandler()
                    
                    # Check if connection object exists and is valid
                    if not hasattr(db, 'conn') or db.conn is None:
                        raise Exception("Database connection object not created")
                    
                    # Check if connection is open (closed == 0 means open in psycopg2)
                    if db.conn.closed != 0:
                        raise Exception(f"Database connection is closed (status: {db.conn.closed})")
                    
                    # Check if cursor exists
                    if not hasattr(db, 'cursor') or db.cursor is None:
                        raise Exception("Database cursor not created")
                    
                    logging.info("Database connection successful")
                    break  # Connection successful, exit retry loop
                        
                except Exception as conn_error:
                    logging.warning(f"Connection attempt {attempt + 1} failed: {str(conn_error)}")
                    if db:
                        try:
                            db.close_db_connection()
                        except:
                            pass
                        db = None
                    
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Wait before retry
                    else:
                        raise Exception(f"Failed to connect after {max_retries} attempts: {str(conn_error)}")
            
            # If we don't have a valid connection at this point, fail
            if not db or not db.conn or db.conn.closed != 0:
                raise Exception("No valid database connection established")
            
            # Check required tables
            required_tables = ['curriculum_regular', 'student_information', 'admin_management']
            
            logging.info("Checking required tables...")
            for table in required_tables:
                try:
                    db.cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = %s
                        )
                    """, (table,))
                    
                    result = db.cursor.fetchone()
                    
                    if not result:
                        raise Exception(f"Could not check if table '{table}' exists")
                    
                    # RealDictCursor returns a dict-like object
                    exists = result[0] if isinstance(result, tuple) else result.get('exists', False)
                    
                    if not exists:
                        logging.error(f"Required table '{table}' not found")
                        raise Exception(f"Required table '{table}' not found")
                    else:
                        logging.info(f"Table '{table}' exists ✓")
                        
                except psycopg2.Error as table_error:
                    logging.error(f"Database error checking table '{table}': {str(table_error)}")
                    raise Exception(f"Database error checking table '{table}': {str(table_error)}")
                except Exception as table_error:
                    logging.error(f"Error checking table '{table}': {str(table_error)}")
                    raise Exception(f"Error checking table '{table}': {str(table_error)}")
            
            # Close connection
            if db:
                try:
                    db.close_db_connection()
                    logging.info("Database connection closed")
                except Exception as close_error:
                    logging.warning(f"Error closing database connection: {str(close_error)}")
            
            logging.info("Database check completed successfully ✓")
            return True
            
        except Exception as e:
            error_msg = str(e) if str(e) else "Unknown database error"
            logging.error(f"Database check failed: {error_msg}")
            print(f"Database check failed: {error_msg}")
            
            # Clean up connection if it exists
            if db:
                try:
                    db.close_db_connection()
                except:
                    pass
            
            return False
        
    def check_ui_components(self):
        """Check if UI components are properly loaded"""
        required_attributes = ['dept_logo_image','splash','progress','loading_label']
        missing = []
        for attr in required_attributes:
            if not hasattr(self, attr):
                print(f"Warning: Missing UI component: {attr}")
                missing.append(attr)
        if missing:
            print(f"Warning: The following UI components are missing: {', '.join(missing)}")
        return True

    def check_final_setup(self):
        """Perform final checks before system launch"""
        try:
            # Check if threading is available and active
            if not threading.current_thread():
                raise Exception("Threading system not initialized")
            
            # Check if main thread is alive and running
            main_thread = threading.main_thread()
            if not main_thread.is_alive():
                raise Exception("Main thread is not active")
            
            return True
        
        except Exception as e:
            print(f"Final setup check failed: {e}")
            return False

    def check_network(self):
        """Check if network is available"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            try:
                urllib.request.urlopen('http://www.google.com', timeout=3)
                return True
            except:
                print("Warning: No network connection detected")
                return True  # Don't fail on network issues

    def load_images(self):
        """Load and store all images used in the application"""
        try:
            # Department logo
            dept_logo = Image.open(LoginForm.resource_path("thesis_copy/pictures/department_logo.jpg"))
            self.dept_logo_image = ctk.CTkImage(light_image=dept_logo, dark_image=dept_logo, size=(300, 300))

        except Exception as e:
            print(f"Error loading images: {e}")

    def admin_login_success(self):
        """Handle successful admin login"""
        try:
            # Clear any existing widgets
            for widget in self.winfo_children():
                widget.destroy()
            
            # Create and show new admin screen
            self.admin_screen = admin_screen.AdminScreen(self, self)
            self.admin_screen.pack(fill="both", expand=True)
        except Exception as e:
            print(f"Error creating admin screen: {e}")
            messagebox.showerror("Error", f"Failed to load admin screen: {e}")

    def login_success(self):
        self.login_frame.destroy()
        self.show_splash_screen()

    def registration_sucess(self):
        self.login_frame.destroy()
        self.show_splash_screen()

    def show_main_menu(self):
        """Initialize and show the main menu with optimized loading"""
        try:
            # Clear any existing widgets
            for widget in self.winfo_children():
                widget.destroy()

            # Initialize frames
            self.setup_frames()
            self.setup_background()
            self.setup_logo()
            self.setup_title()
            self.create_navigation_buttons()
            self.setup_grid()
            
        except Exception as e:
            print(f"Error setting up main menu: {e}")

    def setup_frames(self):
        """Initialize main frames"""
        self.left_frame = ctk.CTkFrame(self, width=364, height=600, fg_color="#FFD700")
        self.left_frame.grid(row=0, column=0, rowspan=1, sticky="nsew")

        self.right_frame = ctk.CTkFrame(self, width=736, height=600, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, rowspan=2, columnspan=2, sticky="nsew")

        # Add window controls
        self.create_window_controls()

    def setup_background(self):
        """Load and set up background image"""
        try:
            self.dept_bg = Image.open(LoginForm.resource_path("Image/background.jpg"))
            self.bg_image_pil = self.dept_bg
            
            initial_width = self.right_frame.winfo_width() or 736
            initial_height = self.right_frame.winfo_height() or 600
            
            self.bg_image = ctk.CTkImage(light_image=self.bg_image_pil,dark_image=self.bg_image_pil,size=(initial_width, initial_height))

            self.bg_label = ctk.CTkLabel(self.right_frame, image=self.bg_image, text="")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Bind resize event
            self.right_frame.bind('<Configure>', self.resize_background)
            
        except Exception as e:
            print(f"Error loading background: {e}")

    def setup_logo(self):
        """Set up department logo"""
        try:
            self.logo_label = ctk.CTkLabel(self.left_frame, image=self.dept_logo_image, text="")
            self.logo_label.pack(pady=170, anchor="center")
        except Exception as e:
            print(f"Error loading logo: {e}")

    def setup_title(self):
        """Set up main title"""
        self.title_label = ctk.CTkLabel(self.right_frame, text="Bachelor of Science in Computer Science", font=("Vivaldi", 45, "bold"))
        self.title_label.pack(pady=70)

    def setup_grid(self):
        """Configure grid weights"""
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(0, weight=1)

    def resize_background(self, event):
        """Handle background image resizing"""
        try:
            new_width = event.width
            new_height = event.height
            
            self.bg_image = ctk.CTkImage(light_image=self.bg_image_pil,dark_image=self.bg_image_pil,size=(new_width, new_height))
            
            self.bg_label.configure(image=self.bg_image)
        except Exception as e:
            print(f"Error resizing background: {e}")

    def create_navigation_buttons(self):
        try:
            # Load icons with correct path
            student_icon = Image.open(LoginForm.resource_path("icons/student.png"))
            self.student_icon = ctk.CTkImage(light_image=student_icon, dark_image=student_icon, size=(30, 30))
            
            grade_icon = Image.open(LoginForm.resource_path("icons/grade.png"))
            self.grade_icon = ctk.CTkImage(light_image=grade_icon, dark_image=grade_icon, size=(30, 30))
            
            curriculum_icon = Image.open(LoginForm.resource_path("icons/curriculum2.png"))
            self.curriculum_icon = ctk.CTkImage(light_image=curriculum_icon, dark_image=curriculum_icon, size=(30, 30))
            
            appraisal_icon = Image.open(LoginForm.resource_path("icons/appraisal.png"))
            self.appraisal_icon = ctk.CTkImage(light_image=appraisal_icon, dark_image=appraisal_icon, size=(30, 30))
            
            archive_icon = Image.open(LoginForm.resource_path("icons/archives.png"))
            self.archive_icon = ctk.CTkImage(light_image=archive_icon, dark_image=archive_icon, size=(30, 30))
        except Exception as e:
            print(f"Error loading icons: {e}")
            self.student_icon = None
            self.grade_icon = None
            self.curriculum_icon = None
            self.appraisal_icon = None
            self.archive_icon = None

        self.screens = {
            "Student": (student_screen.StudentScreen, self.student_icon),
            "Grade": (grade_screen.GradeScreen, self.grade_icon),
            "Curriculum": (curriculum_screen.CurriculumScreen, self.curriculum_icon),
            "Appraisal": (appraisal_screen.AppraisalScreen, self.appraisal_icon),
            "Archive": (archive_screen.ArchiveScreen, self.archive_icon),}

        for text, (screen_class, icon) in self.screens.items():
            button = ctk.CTkButton(self.right_frame,text="  "+text,image=icon, compound="left",font=("Helvetica", 16, "bold"), width=200,  height=40, fg_color="transparent",  text_color="black",  hover_color=("gray70", "gray30"),border_width=2,border_color=("gray10", "gray90"),anchor="center",command=lambda sc=screen_class, t=text: self.show_screen(sc, t))
            button.pack(pady=15)

        self.current_screen = None
        
    def show_screen(self, screen_class, screen_name):
        """Handle screen switching with modern progress bar"""
        # Clean up current screen
        if self.current_screen:
            self.current_screen.grid_forget()
            self.current_screen.destroy()

        if screen_name == "Grade":
            # Create separate loading window
            self.loading_window = ctk.CTkToplevel(self)
            self.loading_window.title("Loading Grades Module")
            self.loading_window.geometry("350x350")
            self.loading_window.resizable(False, False)
            
            # Center the loading window
            self.loading_window.transient(self)
            self.loading_window.grab_set()
            
            # Make it appear centered on main window
            main_x = self.winfo_x()
            main_y = self.winfo_y()
            main_width = self.winfo_width()
            main_height = self.winfo_height()
            
            load_width = 450
            load_height = 350
            
            x = main_x + (main_width - load_width) // 2
            y = main_y + (main_height - load_height) // 2
            
            self.loading_window.geometry(f"{load_width}x{load_height}+{x}+{y}")
            
            # Create loading content
            loading_container = ctk.CTkFrame(self.loading_window, fg_color="transparent")
            loading_container.pack(expand=True, fill="both", padx=40, pady=40)
            
            # Loading title
            loading_title = ctk.CTkLabel(loading_container,text="Loading Grades Module",font=("Segoe UI", 24, "bold"),text_color="#2c3e50")
            loading_title.pack(pady=(0, 30))
            
            # Progress percentage (large and prominent)
            self.progress_var = ctk.StringVar(value="0%")
            progress_label = ctk.CTkLabel(loading_container,textvariable=self.progress_var,font=("Segoe UI", 32, "bold"),text_color="#3498db")
            progress_label.pack(pady=(0, 20))
            
            # Modern progress bar container
            progress_container = ctk.CTkFrame(loading_container, fg_color="transparent")
            progress_container.pack(fill="x", pady=(0, 15))
            
            # Main progress bar
            self.progress_bar = ctk.CTkProgressBar(progress_container,width=300,height=12,progress_color="#3498db",corner_radius=6,mode="determinate")
            self.progress_bar.pack(fill="x")
            self.progress_bar.set(0)
            
            # Progress steps container
            steps_container = ctk.CTkFrame(loading_container, fg_color="transparent")
            steps_container.pack(fill="x", pady=(0, 20))
            
            # Status text
            self.status_var = ctk.StringVar(value="Initializing module...")
            status_label = ctk.CTkLabel(loading_container,textvariable=self.status_var,font=("Segoe UI", 14),text_color="#7f8c8d",wraplength=350)
            status_label.pack(pady=(0, 10))
            
            # Loading steps indicator
            self.steps_var = ctk.StringVar(value="Step 1 of 5")
            steps_label = ctk.CTkLabel(loading_container,textvariable=self.steps_var,font=("Segoe UI", 12),text_color="#95a5a6")
            steps_label.pack()

            def initialize_grade_screen():
                """Background task for loading"""
                steps = [("Loading database tables...", 20, "Step 1 of 5"),("Preparing grade interface...", 40, "Step 2 of 5"),
                    ("Loading student records...", 60, "Step 3 of 5"),("Initializing components...", 80, "Step 4 of 5"),
                    ("Finalizing setup...", 95, "Step 5 of 5"),("Ready!", 100, "Complete")]
                
                try:
                    for message, percentage, step_text in steps:
                        # Update progress in main thread
                        self.after(0, lambda msg=message, perc=percentage, step=step_text: 
                                update_progress(msg, perc, step))
                        
                        # Simulate work being done
                        time.sleep(0.8)
                        
                        # Actual loading work
                        if "database" in message:
                            importlib.reload(database)
                        elif "interface" in message:
                            importlib.reload(grade_screen)
                        elif "records" in message:
                            pass  # Actual record loading happens later
                    
                    # Return success
                    return screen_class
                    
                except Exception as e:
                    print(f"Error in background thread: {e}")
                    return None

            def update_progress(message, percentage, step_text):
                """Update loading progress (runs in main thread)"""
                if hasattr(self, 'status_var') and hasattr(self, 'progress_var') and hasattr(self, 'steps_var'):
                    self.status_var.set(message)
                    self.progress_var.set(f"{percentage}%")
                    self.steps_var.set(step_text)
                    self.progress_bar.set(percentage / 100)
                    
                    # Change progress bar color based on percentage
                    if percentage < 30:
                        self.progress_bar.configure(progress_color="#e74c3c")  # Red
                    elif percentage < 70:
                        self.progress_bar.configure(progress_color="#f39c12")  # Orange
                    else:
                        self.progress_bar.configure(progress_color="#27ae60")  # Green
                    
                    # Stop animation and close window when 100%
                    if percentage >= 100:
                        self.after(800, close_loading_window)  # Slightly longer delay to show completion

            def close_loading_window():
                """Close the loading window and cleanup"""
                try:
                    # Close the loading window
                    if hasattr(self, 'loading_window') and self.loading_window and self.loading_window.winfo_exists():
                        self.loading_window.destroy()
                        self.loading_window = None
                except Exception as e:
                    print(f"Error closing loading window: {e}")

            def on_loading_complete(result):
                """Handle loading completion (runs in main thread)"""
                try:
                    if result is None:
                        # Loading failed - show error
                        close_loading_window()
                        CTkMessagebox(title="Loading Error",message="Failed to load grade module. Please try again.",icon="cancel")
                        self.show_main_menu()
                        return
                    
                    # Loading successful - create screen
                    screen_instance = result(self)
                    
                    # Ensure loading window is closed
                    close_loading_window()
                    
                    screen_instance.grid(row=0, column=1, sticky="nsew")
                    self.current_screen = screen_instance
                    
                    self.rowconfigure(0, weight=1)
                    self.columnconfigure(1, weight=1)
                    
                except Exception as e:
                    print(f"Error completing loading: {e}")
                    # Force cleanup
                    close_loading_window()
                    self.show_main_menu()

            def run_background_task():
                """Run background task and schedule completion in main thread"""
                try:
                    result = initialize_grade_screen()
                    # Use after_idle to ensure main thread is ready
                    self.after_idle(lambda: on_loading_complete(result))
                except Exception as e:
                    print(f"Background task error: {e}")
                    self.after_idle(lambda: on_loading_complete(None))
            
            # Start background loading
            threading.Thread(target=run_background_task, daemon=True).start()
            
        else:
            # Handle other screens (non-Grade) - quick loading with simple progress
            loading_frame = ctk.CTkFrame(self, fg_color="#f8f9fa", corner_radius=10)
            loading_frame.grid(row=0, column=1, sticky="nsew")
            
            loading_container = ctk.CTkFrame(loading_frame, fg_color="transparent")
            loading_container.place(relx=0.5, rely=0.5, anchor="center")
            
            loading_label = ctk.CTkLabel(loading_container,text=f"Loading {screen_name} Module...",font=("Segoe UI", 18, "bold"),text_color="#2c3e50")
            loading_label.pack(pady=(0, 15))
            
            # Simple progress bar for other screens
            quick_progress = ctk.CTkProgressBar(loading_container,width=200,height=8,progress_color="#3498db",corner_radius=4,mode="indeterminate")
            quick_progress.pack(pady=(0, 10))
            quick_progress.start()
            
            status_label = ctk.CTkLabel(loading_container,text="Please wait...",font=("Segoe UI", 12),text_color="#7f8c8d")
            status_label.pack()
            
            def load_other_screen():
                """Quick load for other screens"""
                try:
                    # Stop progress bar first
                    quick_progress.stop()
                    
                    module_map = {"Student": student_screen,"Curriculum": curriculum_screen,"Appraisal": appraisal_screen,"Archive": archive_screen,}
                    
                    if screen_name in module_map:
                        importlib.reload(database)
                        module = module_map[screen_name]
                        importlib.reload(module)
                        screen_class = getattr(module, f"{screen_name}Screen")

                    screen = screen_class(self)
                    
                    # Ensure loading frame is destroyed
                    if loading_frame.winfo_exists():
                        loading_frame.destroy()
                    
                    screen.grid(row=0, column=1, sticky="nsew")
                    self.current_screen = screen

                    self.rowconfigure(0, weight=1)
                    self.columnconfigure(1, weight=1)
                    
                except Exception as e:
                    print(f"Error loading {screen_name}: {e}")
                    if loading_frame.winfo_exists():
                        loading_frame.destroy()
                    self.show_main_menu()
            
            # Quick load with slight delay
            self.after(100, load_other_screen)
            
    def create_window_controls(self):
        """Create window control buttons"""
        control_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        control_frame.pack(side="top", anchor="ne", padx=10, pady=10)

        self.fullscreen_button = ctk.CTkButton(control_frame,text="⤡", width=30,height=30,font=("Times New Roman", 19),command=self.toggle_fullscreen,fg_color="transparent",text_color="black",hover_color=("gray70", "gray30"))
        self.fullscreen_button.pack(side="right", padx=5)

        logout_icon = Image.open(LoginForm.resource_path("icons/logout.png"))
        self.logout_icon=ctk.CTkImage(light_image=logout_icon, dark_image=logout_icon, size=(30,30))
        self.close_button = ctk.CTkButton(control_frame,text="Logout", image=self.logout_icon,width=60,height=30,font=("Times New Roman", 19),command=self.logout, corner_radius=30,fg_color="transparent",text_color="black",hover_color=("gray70", "gray30"))
        self.close_button.pack(side="right", padx=5)
    
    def logout(self):
        """Handle logout functionality"""
        def handle_logout():
        
            if hasattr(self, 'current_screen') and self.current_screen:
                self.current_screen.destroy()
            
            for widget in self.winfo_children():
                widget.destroy()
            
            self.login_frame = ctk.CTkFrame(self)
            self.login_frame.pack(expand=True, fill="both")
            self.login_form = LoginForm(self.login_frame, login_success_callback=self.login_success, admin_login_callback=self.admin_login_success)

        def on_button_click():
            msg = CTkMessagebox(title="Logout",message="Are you sure you want to logout?",icon="question",option_1="Yes",option_2="No")
            
            def handle_enter(event):
                msg.destroy()
                handle_logout()
            
            msg.bind("<Return>", handle_enter)
            msg.focus_set()
            
            response = msg.get()
            
            if response == "Yes":
                handle_logout()
        
        on_button_click()

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        is_fullscreen = self.attributes('-fullscreen')
        self.attributes('-fullscreen', not is_fullscreen)
        
        if is_fullscreen:
            self.fullscreen_button.configure(text="⤡")
        else:
            self.fullscreen_button.configure(text="⤢")

    def show_with_transition(self):
        """Show main menu with an uncover transition effect from right to left"""
        def uncover():
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            if self.splash.winfo_exists():
                self.splash.geometry(f"{screen_width}x{screen_height}+0+0")
                self.splash.update()
            
            for x in range(0, screen_width + 20, 20):
                if self.splash.winfo_exists():
                    self.splash.geometry(f"{screen_width}x{screen_height}+{x}+0")
                    self.splash.update()
                    time.sleep(0.01)
                else:
                    break
            
            if self.splash.winfo_exists():
                self.splash.destroy()

        self.show_main_menu()
        uncover()

if __name__ == "__main__":
    app = Application()
    app.mainloop()