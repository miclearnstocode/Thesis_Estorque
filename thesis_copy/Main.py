from CTkMessagebox import CTkMessagebox
import customtkinter as ctk
from PIL import Image
import importlib
import threading
import sys , time
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

class Application(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BS Computer Science")
        #self.show_splash_screen()
        # Create and start the server in a separate thread
        self.server = Peer()  # Create the server instance
        self.server_thread = threading.Thread(target=self.server.start_server)
        self.server_thread.daemon = True
        self.server_thread.start()
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

        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.pack(expand=True, fill="both")

        # Then create login form with callbacks
        self.login_form = LoginForm(
            self.login_frame, 
            login_success_callback=self.login_success,
            admin_login_callback=self.admin_login_success)
        self.grade_data = self.preload_grade_data()
        
    def start_server(self):
        # Start the server in a separate thread to avoid blocking the UI
        server = Peer()
        server.start_server

    def preload_grade_data(self):
        """Preload grade data for all semesters"""
        try:
            db = DatabaseHandler()
            grade_data = db.preload_grade_data()
            db.close_db_connection()
            return grade_data
        except Exception as e:
            print(f"Error preloading grade data: {e}")
            return {}

    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode (optional)"""
        self.attributes('-fullscreen', False)

    def show_splash_screen(self):
        # Load and set background image first (behind splash)
        bg_image = Image.open("Image/Gradient.jpg")
        self.splash_bg = ctk.CTkImage(
            light_image=bg_image,
            dark_image=bg_image,
            size=(self.winfo_screenwidth(), self.winfo_screenheight())
        )
        
        # Create background label that covers entire screen
        self.bg_window = ctk.CTkToplevel(self)
        self.bg_window.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        self.bg_window.overrideredirect(True)
        
        bg_label = ctk.CTkLabel(
            self.bg_window,
            image=self.splash_bg,
            text=""
        )
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
        
        # Load CSU logo
        try:
            csu_logo = Image.open("Image/Capiz_State_University 2.png")
            self.csu_logo_image = ctk.CTkImage(light_image=csu_logo,dark_image=csu_logo,size=(300, 300))
            
            # Create and pack logo label
            logo_label = ctk.CTkLabel(self.splash,image=self.csu_logo_image,text="")
            logo_label.pack(pady=30)
            
        except Exception as e:
            print(f"Error loading CSU logo: {e}")
        """ Naga ubra pa ko thesis ko December 31, 2024 11:57pm 3 
            minutes bag o ang new year sang 2025"""
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
                    ("Verifying network connectivity", self.check_network, 10)
                ]
                
                # Calculate total weight to ensure 100%
                total_weight = sum(weight for _, _, weight in components)
                
                # Track cumulative progress
                cumulative_progress = 0
                
                # Ensure initial message
                self.splash.after(0, self.loading_label.configure, {
                    'text': "Starting system initialization...",
                    'text_color': "blue"
                })
                
                # Iterate through components with detailed progress tracking
                for message, check_function, weight in components:
                    try:
                        # Update loading message
                        def update_loading(msg, color="black"):
                            if hasattr(self, 'loading_label') and self.loading_label:
                                self.loading_label.configure(
                                    text=msg, 
                                    text_color=color
                                )
                        
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
                        self.loading_label.configure(
                            text="System ready!",
                            text_color='green'
                        )
                
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
                        self.loading_label.configure(
                            text=error_message if error_message else "An error occurred",
                            text_color='red'
                        )
                    
                    # Show error dialog
                    CTkMessagebox(
                        title="System Initialization Error", 
                        message=error_message if error_message else "An error occurred",
                        icon="cancel",
                        option_1="Exit"
                    )
                    
                    # Attempt graceful shutdown
                    self.quit()
                
                self.splash.after(0, handle_error, str(e))  # Pass the error message

        
        # Start progress in a daemon thread
        threading.Thread(target=progress, daemon=True).start()
        
        
    def check_system_requirements(self):
        """Check if system meets basic requirements"""
        try:
            # Check Python version
            if sys.version_info < (3, 7):
                raise Exception("Python 3.7 or higher is required")
            
            # Check available memory
            if psutil.virtual_memory().available < 500 * 1024 * 1024:  # 500MB
                raise Exception("Insufficient memory available")
            
            return True
        except Exception as e:
            print(f"System requirements check failed: {e}")
            return False

    def check_modules(self):
        """Check if all required modules are available"""
        required_modules = [
            'customtkinter',
            'PIL',
            'mysql.connector',
            'pandas',
            'CTkMessagebox'
        ]
        
        try:
            for module in required_modules:
                importlib.import_module(module)
            return True
        except ImportError as e:
            print(f"Module check failed: {e}")
            return False

    def check_database(self):
        """Check database connectivity and required tables"""
        try:
            db = DatabaseHandler()
            if not db.conn.is_connected():
                raise Exception("Database connection failed")
            
            # Check required tables
            required_tables = [
                'curriculum_regular',
                'student_information',
                'admin_management'
            ]
            
            for table in required_tables:
                db.cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if not db.cursor.fetchone():
                    raise Exception(f"Required table '{table}' not found")
            
            db.close_db_connection()
            return True
        except Exception as e:
            print(f"Database check failed: {e}")
            return False

    def check_ui_components(self):
        """Check if UI components are properly loaded"""
        try:
            required_attributes = [
                'dept_logo_image',
                'splash',
                'progress',
                'loading_label'
            ]
            
            for attr in required_attributes:
                if not hasattr(self, attr):
                    raise Exception(f"Missing UI component: {attr}")
            
            return True
        except Exception as e:
            print(f"UI component check failed: {e}")
            return False

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
            
            # Check number of active threads
            active_threads = threading.active_count()
            print(f"Active threads: {active_threads}")
            
            # Check thread daemon status
            current_thread = threading.current_thread()
            print(f"Current thread daemon status: {current_thread.daemon}")
            
            # Check if thread can be created
            try:
                test_thread = threading.Thread(target=lambda: None)
                test_thread.start()
                test_thread.join(timeout=1.0)  # Wait for test thread with timeout
            except Exception as thread_error:
                raise Exception(f"Thread creation test failed: {thread_error}")
            
            return True
        
        except Exception as e:
            print(f"Final setup check failed: {e}")
            self.loading_label.configure(text=f"Threading check failed: {e}")
            return False

    def check_network(self):
        """Check if network is available"""
        try:
            # Try to connect to a reliable host (Google's DNS server)
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            try:
                # Fallback: Try to connect to a common website
                urllib.request.urlopen('http://www.google.com', timeout=3)
                return True
            except:
                error_message = "No network connection detected"
                self.loading_label.configure(text=error_message)
                raise Exception(error_message)
        return False
      
    def load_images(self):
        """Load and store all images used in the application"""
        try:
            # Department logo
            dept_logo = Image.open("thesis_copy/pictures/department_logo.jpg")
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
            self.dept_bg = Image.open("Image/background.jpg")
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
            
            # Create new CTkImage with updated size
            self.bg_image = ctk.CTkImage(light_image=self.bg_image_pil,dark_image=self.bg_image_pil,size=(new_width, new_height))
            
            # Update the background label
            self.bg_label.configure(image=self.bg_image)
        except Exception as e:
            print(f"Error resizing background: {e}")

    def create_navigation_buttons(self):
        try:
            # Load icons with correct path
            student_icon = Image.open("icons/student.png")
            self.student_icon = ctk.CTkImage(light_image=student_icon, dark_image=student_icon, size=(30, 30))
            
            grade_icon = Image.open("icons/grade.png")
            self.grade_icon = ctk.CTkImage(light_image=grade_icon, dark_image=grade_icon, size=(30, 30))
            
            curriculum_icon = Image.open("icons/curriculum2.png")
            self.curriculum_icon = ctk.CTkImage(light_image=curriculum_icon, dark_image=curriculum_icon, size=(30, 30))
            
            appraisal_icon = Image.open("icons/appraisal.png")
            self.appraisal_icon = ctk.CTkImage(light_image=appraisal_icon, dark_image=appraisal_icon, size=(30, 30))
            
            archive_icon = Image.open("icons/archives.png")
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

        # Initialize current screen tracker
        self.current_screen = None

    def show_screen(self, screen_class, screen_name):
        """Handle screen switching with loading screen for grades"""
        if self.current_screen:
            self.current_screen.grid_forget()
            self.current_screen.destroy()

        # Show loading screen only for Grade screen
        if screen_name == "Grade":
            # Create and show loading screen
            loading_frame = ctk.CTkFrame(self, fg_color="white")
            loading_frame.grid(row=0, column=1, sticky="nsew")
            
            # Center the loading content
            loading_frame.grid_rowconfigure(0, weight=1)
            loading_frame.grid_columnconfigure(0, weight=1)
            
            loading_container = ctk.CTkFrame(loading_frame, fg_color="transparent")
            loading_container.grid(row=0, column=0)
            
            empty_img = ctk.CTkImage(
                light_image=Image.new("RGB", (300, 40), color="white"),
                dark_image=Image.new("RGB", (300, 40), color="white"),
                size=(300, 40)
            )

            loading_label = ctk.CTkLabel(
                loading_container,
                text="Loading Grades Module",
                font=("Helvetica", 16, "bold"),
                image=empty_img,
                compound="center"  # Text will be centered over image
            )
            loading_label.pack(pady=10)
            
            # Progress bar
            progress = ctk.CTkProgressBar(
                loading_container,
                width=300,
                height=15,
                corner_radius=10,
                mode="indeterminate"
            )
            progress.pack(pady=10)
            progress.start()
            
            # Status message
            status_label = ctk.CTkLabel(
                loading_container,
                text="Initializing...",
                font=("Helvetica", 12)
            )
            status_label.pack(pady=5)

            def update_status(message):
                status_label.configure(text=message)
                self.update()

            def initialize_grade_screen():
                try:
                    update_status("Loading database tables...")
                    # Reload the database module
                    importlib.reload(database)
                    
                    update_status("Preparing grade interface...")
                    # Reload the grade_screen module
                    importlib.reload(grade_screen)
                    
                    update_status("Loading student records...")
                    # Create the grade screen instance
                    screen = screen_class(self)
                    
                    update_status("Finalizing...")
                    # Configure grid weights
                    self.rowconfigure(0, weight=1)
                    self.columnconfigure(1, weight=1)
                    
                    # Remove loading screen
                    loading_frame.destroy()
                    
                    # Show the grade screen
                    screen.grid(row=0, column=1, sticky="nsew")
                    self.current_screen = screen
                    
                except Exception as e:
                    error_msg = f"Error loading grade screen: {str(e)}"
                    print(error_msg)
                    CTkMessagebox(
                        title="Loading Error",
                        message=error_msg,
                        icon="cancel"
                    )
                    # Remove loading screen and show main menu
                    loading_frame.destroy()
                    self.show_main_menu()

            # Start initialization in a separate thread
            threading.Thread(target=initialize_grade_screen, daemon=True).start()
            
        else:
            # For other screens, load normally
            # Reload the appropriate module
            module_map = {
                "Student": student_screen,
                "Curriculum": curriculum_screen,
                "Appraisal": appraisal_screen,
                "Archive": archive_screen,
            }
            
            if screen_name in module_map:
                importlib.reload(database)
                module = module_map[screen_name]
                importlib.reload(module)
                screen_class = getattr(module, f"{screen_name}Screen")

            # Create and show new screen
            screen = screen_class(self)
            screen.grid(row=0, column=1, sticky="nsew")
            self.current_screen = screen

            # Configure grid weights
            self.rowconfigure(0, weight=1)
            self.columnconfigure(1, weight=1)


    def create_window_controls(self):
        """Create window control buttons"""
        control_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        control_frame.pack(side="top", anchor="ne", padx=10, pady=10)

        # Exit fullscreen button
        self.fullscreen_button = ctk.CTkButton(control_frame,text="⤡", width=30,height=30,font=("Times New Roman", 19),command=self.toggle_fullscreen,fg_color="transparent",text_color="black",hover_color=("gray70", "gray30"))
        self.fullscreen_button.pack(side="right", padx=5)

        logout_icon = Image.open("icons/logout.png")
        self.logout_icon=ctk.CTkImage(light_image=logout_icon, dark_image=logout_icon, size=(30,30))
        self.close_button = ctk.CTkButton(control_frame,text="Logout", image=self.logout_icon,width=60,height=30,font=("Times New Roman", 19),command=self.logout, corner_radius=30,fg_color="transparent",text_color="black",hover_color=("gray70", "gray30"))
        self.close_button.pack(side="right", padx=5)
    
    def logout(self):
        """Handle logout functionality"""
        def handle_logout():
        
            if hasattr(self, 'current_screen') and self.current_screen:
                self.current_screen.destroy()
            
            # Clear main menu widgets
            for widget in self.winfo_children():
                widget.destroy()
            
            # Recreate login frame and form with all necessary callbacks
            self.login_frame = ctk.CTkFrame(self)
            self.login_frame.pack(expand=True, fill="both")
            self.login_form = LoginForm(
                self.login_frame, 
                login_success_callback=self.login_success,
                admin_login_callback=self.admin_login_success
            )

        def on_button_click():
            msg = CTkMessagebox(
                title="Logout",
                message="Are you sure you want to logout?",
                icon="question",
                option_1="Yes",
                option_2="No"
            )
            
            def handle_enter(event):
                msg.destroy()
                handle_logout()
            
            # Bind Enter key to the message box
            msg.bind("<Return>", handle_enter)
            # Focus the message box to capture key events
            msg.focus_set()
            
            response = msg.get()
            
            if response == "Yes":
                handle_logout()
        
        # Call the button click handler directly
        on_button_click()

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        is_fullscreen = self.attributes('-fullscreen')
        self.attributes('-fullscreen', not is_fullscreen)
        
        # Update button text based on state
        if is_fullscreen:
            self.fullscreen_button.configure(text="⤡")  # or "□"
        else:
            self.fullscreen_button.configure(text="⤢")  # or "❐"

    def show_with_transition(self):
        """Show main menu with an uncover transition effect from right to left"""
        def uncover():
            # Get the screen width and height
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            # Set the initial position of the splash screen
            if self.splash.winfo_exists():
                self.splash.geometry(f"{screen_width}x{screen_height}+0+0")
                self.splash.update()
            
            # Animate the splash screen moving off-screen to the right
            for x in range(0, screen_width + 20, 20):
                if self.splash.winfo_exists():
                    self.splash.geometry(f"{screen_width}x{screen_height}+{x}+0")
                    self.splash.update()
                    time.sleep(0.01)
                else:
                    break
            
            # Destroy the splash screen after the animation
            if self.splash.winfo_exists():
                self.splash.destroy()

        self.show_main_menu()  # Set up the main menu
        uncover()  # Apply uncover effect

if __name__ == "__main__":
    app = Application()
    app.preload_grade_data()
    app.mainloop()
        
