
import customtkinter as ctk
import hashlib, os, re
from database import DatabaseHandler
from PIL import Image
import sys, os
import time

class LoginForm(ctk.CTkFrame):
    def __init__(self, master, login_success_callback=None, admin_login_callback=None):
        super().__init__(master)
        self.master = master
        
        # Database Handler
        self.db_handler = DatabaseHandler()
        self.failed_attempts = []
        self.lockout_until = 0
        
        # Callbacks
        self.login_success_callback = login_success_callback
        self.admin_login_callback = admin_login_callback

        # Setup the UI
        self.setup_ui()

    def setup_ui(self):
        """Setup the complete UI with modern design"""
        # Get screen dimensions
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Load and resize background
        self.background_image = Image.open(self.resource_path("Image/Gradient.jpg"))
        self.background_image = self.background_image.resize((screen_width, screen_height), Image.LANCZOS)
        self.background_photo = ctk.CTkImage(light_image=self.background_image, dark_image=self.background_image, size=(screen_width, screen_height))

        # Background label
        self.background_label = ctk.CTkLabel(self.master, image=self.background_photo, text="")
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Load logos
        self.load_logos()
        
        # Create main container
        self.create_main_container()
        
        # Create login widgets
        self.create_login_widgets()

    def load_logos(self):
        """Load and prepare all logos"""
        # CSD Logo
        self.nami_image = Image.open(self.resource_path("Image/CSD.jpg"))
        self.nami_image = self.nami_image.resize((100, 100), Image.LANCZOS)
        self.nami_photo = ctk.CTkImage(
            light_image=self.nami_image, 
            dark_image=self.nami_image, 
            size=(100, 100)
        )

        # CapSU Logo
        self.capsu_image = Image.open(self.resource_path("Image/Capiz_State_University_2.png"))
        self.capsu_image = self.capsu_image.resize((150, 150), Image.LANCZOS)
        self.capsu_photo = ctk.CTkImage(
            light_image=self.capsu_image, 
            dark_image=self.capsu_image, 
            size=(150, 150)
        )

    def create_main_container(self):
        """Create the main login container"""
        # Title frame at top
        title_frame = ctk.CTkFrame(
            self.master, 
            width=600, 
            height=80, 
            fg_color="#FFFFFF",  # Solid white instead of rgba
            corner_radius=15
        )
        title_frame.place(relx=0.5, y=40, anchor="center")
        
        title_label = ctk.CTkLabel(title_frame,text="Student Appraisal and Monitoring using Machine Learning",font=("Segoe UI", 24, "bold"),text_color="#2c3e50")
        title_label.pack(expand=True)
        
        # CapSU logo at top right
        self.capsu_logo_label = ctk.CTkLabel(self.master, image=self.capsu_photo, text="")
        self.capsu_logo_label.place(relx=0.95, y=20, anchor="ne")

        # Main login container
        self.container = ctk.CTkFrame(
            self.master,
            width=420,
            height=650,
            fg_color="#FFFFFF",  # Solid white
            corner_radius=25,
            border_width=2,
            border_color="#e0e0e0") # Light gray border
        self.container.place(relx=0.5, rely=0.55, anchor="center")
        self.container.pack_propagate(False)

    def create_login_widgets(self):
        """Create all login widgets with modern styling"""
        # Clear existing widgets
        for widget in self.container.winfo_children():
            widget.destroy()

        # CSD Logo
        self.csd_logo = ctk.CTkLabel(self.container, image=self.nami_photo, text="")
        self.csd_logo.pack(pady=(30, 10))

        # Welcome Title
        welcome_label = ctk.CTkLabel(self.container,text="Welcome Back!",font=("Segoe UI", 26, "bold"),text_color="#2c3e50")
        welcome_label.pack(pady=(0, 5))

        # Subtitle
        subtitle_label = ctk.CTkLabel(self.container,text="Log in to your account",font=("Segoe UI", 14),text_color="#7f8c8d")
        subtitle_label.pack(pady=(0, 30))

        # Email Section
        email_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        email_frame.pack(fill="x", padx=35, pady=(0, 15))

        email_label = ctk.CTkLabel(
            email_frame,
            text="Email Address",
            font=("Segoe UI", 14, "bold"),
            text_color="#2c3e50"
        )
        email_label.pack(anchor="w", pady=(0, 8))

        self.email_entry = ctk.CTkEntry(
            email_frame,
            width=320,
            height=45,
            placeholder_text="Enter your email",
            corner_radius=12,
            border_width=2,
            border_color="#e0e0e0",
            fg_color="#f8f9fa",
            text_color="#2c3e50",
            font=("Segoe UI", 14))
        self.email_entry.pack(fill="x")
        self.email_entry.bind("<Return>", lambda event: self.focus_next_widget())
        self.email_entry.bind("<KeyRelease>", self.auto_complete_gmail)

        # Password Section
        password_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        password_frame.pack(fill="x", padx=35, pady=(0, 20))

        password_label = ctk.CTkLabel(
            password_frame,
            text="Password",
            font=("Segoe UI", 14, "bold"),
            text_color="#2c3e50"
        )
        password_label.pack(anchor="w", pady=(0, 8))

        self.password_entry = ctk.CTkEntry(
            password_frame,
            width=320,
            height=45,
            placeholder_text="Enter your password",
            show="•",
            corner_radius=12,
            border_width=2,
            border_color="#e0e0e0",
            fg_color="#f8f9fa",
            text_color="#2c3e50",
            font=("Segoe UI", 14)
        )
        self.password_entry.pack(fill="x")
        self.password_entry.bind("<Return>", lambda event: self.validate_login())

        # Show Password Checkbox
        self.show_password_cb = ctk.CTkCheckBox(
            password_frame,
            text="Show Password",
            width=20,
            height=20,
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=4,
            fg_color="#3498db",
            hover_color="#2980b9",
            border_color="#3498db",
            text_color="#2c3e50",
            font=("Segoe UI", 12),
            command=lambda: self.toggle_password_visibility(self.password_entry)
        )
        self.show_password_cb.pack(anchor="w", pady=(12, 0))

        # Error Label
        self.error_label = ctk.CTkLabel(
            self.container,
            text="",
            text_color="#e74c3c",
            font=("Segoe UI", 12),
            wraplength=320
        )
        self.error_label.pack(pady=(5, 10))

        # Login Button
        login_icon = Image.open(self.resource_path("icons/logins.png"))
        self.login_icon = ctk.CTkImage(
            light_image=login_icon, 
            dark_image=login_icon, 
            size=(24, 24)
        )
        
        self.login_button = ctk.CTkButton(self.container,
            text="Log In",
            image=self.login_icon,
            command=self.validate_login,
            width=320,
            height=50,
            corner_radius=12,
            fg_color="#3498db",
            hover_color="#2980b9",
            text_color="white",font=("Segoe UI", 16, "bold"))
        self.login_button.pack(pady=(5, 10))

        # Timer Label for lockout
        self.timer_label = ctk.CTkLabel(
            self.container,
            text="",
            text_color="#e74c3c",
            font=("Segoe UI", 12, "bold")
        )
        self.timer_label.pack(pady=(0, 10))

        # Registration Section
        reg_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        reg_frame.pack(pady=(0, 10))

        reg_label = ctk.CTkLabel(
            reg_frame,
            text="Don't have an account?",
            font=("Segoe UI", 14),
            text_color="#7f8c8d"
        )
        reg_label.pack(side="left", padx=(0, 5))

        self.register_link = ctk.CTkLabel(
            reg_frame,
            text="Create Account",
            font=("Segoe UI", 14, "bold", "underline"),
            text_color="#3498db",
            cursor="hand2"
        )
        self.register_link.pack(side="left")
        self.register_link.bind("<Button-1>", self.open_registration)

    @staticmethod  
    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def auto_complete_gmail(self, event):
        """Automatically complete the email domain"""
        current_text = self.email_entry.get()
        if current_text.endswith("@") and current_text.count("@") == 1:
            self.email_entry.insert("end", "gmail.com")
            self.email_entry.icursor(len(current_text))

    def focus_next_widget(self):
        """Move focus to password entry"""
        self.password_entry.focus_set()

    def toggle_password_visibility(self, entry_widget):
        """Toggle password visibility"""
        if entry_widget == self.password_entry:
            is_checked = self.show_password_cb.get()
        else:
            is_checked = self.show_confirm_password_cb.get()
        entry_widget.configure(show="" if is_checked else "•")

    def hash_password(self, password, salt=None):
        """Hash password with salt"""
        if salt is None:
            salt = os.urandom(32).hex()
        
        salted_password = password + salt
        hashed_password = hashlib.sha256(salted_password.encode()).hexdigest()
        
        return hashed_password, salt

    def validate_login(self):
        """Validate login credentials"""
        current_time = time.time()
        
        # Clear previous error
        self.error_label.configure(text="")
        
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        # Check lockout
        if current_time < self.lockout_until:
            wait_time = int(self.lockout_until - current_time)
            self.error_label.configure(text=f"Account locked. Try again in {wait_time} seconds.")
            return
            
        # Basic validation
        if not email or not password:
            self.error_label.configure(text="Please enter both email and password")
            return
            
        # Admin bypass
        if email == "admin@gmail.com" and password == "BSCS@2024!":
            self.error_label.configure(text="Admin login successful!", text_color="#27ae60")
            if self.admin_login_callback:
                self.after(1000, self.admin_login_callback)
            return

        # Email format validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self.error_label.configure(text="Please enter a valid email address")
            return
        
        try:
            user_data = self.db_handler.get_user_by_email(email)
            
            if user_data:
                hashed_password, _ = self.hash_password(password, user_data['salt'])
                
                if hashed_password == user_data['password']:
                    if not user_data['is_active']:
                        self.error_label.configure(text="Account pending admin approval")
                        return

                    # Update last login
                    self.db_handler.cursor.execute(
                        "UPDATE admin_management SET last_login = NOW() WHERE id = %s", 
                        (user_data['id'],)
                    )
                    self.db_handler.conn.commit()
                    
                    # Success
                    self.error_label.configure(text="Login successful!", text_color="#27ae60")
                    self.failed_attempts.clear()
                    
                    if self.login_success_callback:
                        self.after(1000, self.login_success_callback)
                else:
                    self.handle_failed_attempt(current_time)
            else:
                self.handle_failed_attempt(current_time)
        
        except Exception as e:
            self.error_label.configure(text=f"Login error: {str(e)}")

    def handle_failed_attempt(self, current_time):
        """Handle failed login attempts"""
        self.failed_attempts.append(current_time)
        # Keep only attempts from last 60 seconds
        self.failed_attempts = [t for t in self.failed_attempts if current_time - t < 60]
        
        remaining = 5 - len(self.failed_attempts)
        
        if len(self.failed_attempts) >= 5:
            self.lockout_until = current_time + 900  # 15 minutes
            self.error_label.configure(text="Too many failed attempts. Locked for 15 minutes.")
            self.start_countdown(900)
        else:
            self.error_label.configure(
                text=f"Invalid email or password. {remaining} attempts remaining."
            )

    def start_countdown(self, seconds_left):
        """Start countdown for lockout period"""
        if seconds_left > 0:
            mins, secs = divmod(seconds_left, 60)
            time_str = f"Locked: {mins:02}:{secs:02} remaining"
            self.timer_label.configure(text=time_str)
            self.after(1000, self.start_countdown, seconds_left - 1)
        else:
            self.timer_label.configure(text="")
            self.lockout_until = 0
            self.failed_attempts.clear()

    def is_login_valid(self, email, password):
        """Check if login credentials are valid"""
        try:
            user_data = self.db_handler.get_user_by_email(email)
            if user_data:
                hashed_password, _ = self.hash_password(password, user_data['salt'])
                return hashed_password == user_data['password']
            return False
        except Exception as e:
            print(f"Error validating login: {e}")
            return False

    def open_registration(self, event=None):
        """Open registration form"""
        if hasattr(self, 'form_frame') and self.form_frame.winfo_exists():
            self.form_frame.destroy()

        self.registration_form = RegistrationForm(
            master=self.master, 
            db_handler=self.db_handler, 
            hash_function=self.hash_password, 
            back_callback=self.create_login_widgets,
            login_success_callback=self.login_success_callback,
            admin_login_callback=self.admin_login_callback
        )

class RegistrationForm:
    def __init__(self, master, db_handler, hash_function, back_callback, login_success_callback=None, admin_login_callback=None):
        self.master = master
        self.hash_password = hash_function
        self.back_callback = back_callback
        self.db_handler = db_handler
        self.original_master = master
        self.login_success_callback = login_success_callback
        self.admin_login_callback = admin_login_callback
        
        # Get screen dimensions
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Clear existing widgets first
        if self.original_master.winfo_exists():
            for widget in self.original_master.winfo_children():
                widget.destroy()

        # Load and resize the background image
        bg_image = Image.open(LoginForm.resource_path("Image/loginform.jpg"))
        self.background_photo = ctk.CTkImage(
            light_image=bg_image, 
            dark_image=bg_image, 
            size=(screen_width, screen_height)
        )

        # Create background label
        self.background_label = ctk.CTkLabel(
            self.original_master, 
            image=self.background_photo, 
            text=""
        )
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Main container - same size as login
        self.overlay_frame = ctk.CTkFrame(
            self.master,
            width=420,
            height=650,  # Same height as login
            fg_color="#FFFFFF",
            corner_radius=25,
            border_width=2,
            border_color="#e0e0e0"
        )
        self.overlay_frame.place(relx=0.5, rely=0.55, anchor="center")
        self.overlay_frame.pack_propagate(False)

        # Create widgets
        self.create_registration_widgets()

    def create_registration_widgets(self):
        """Create all registration widgets with modern styling"""
        # Title Section
        title_label = ctk.CTkLabel(
            self.overlay_frame,
            text="Create Account",
            font=("Segoe UI", 26, "bold"),
            text_color="#2c3e50"
        )
        title_label.pack(pady=(25, 5))

        subtitle_label = ctk.CTkLabel(
            self.overlay_frame,
            text="Join us today",
            font=("Segoe UI", 14),
            text_color="#7f8c8d"
        )
        subtitle_label.pack(pady=(0, 20))

        # Create scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.overlay_frame, 
            fg_color="transparent",
            width=360,
            height=450
        )
        self.scrollable_frame.pack(expand=True, fill='both', padx=25, pady=(0, 15))

        # Full Name Section
        name_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        name_frame.pack(fill='x', pady=(0, 15))
        
        name_label = ctk.CTkLabel(
            name_frame,
            text="Full Name",
            font=("Segoe UI", 14, "bold"),
            text_color="#2c3e50"
        )
        name_label.pack(anchor='w', pady=(0, 8))
        
        self.name_entry = ctk.CTkEntry(
            name_frame,
            placeholder_text="Enter your full name",
            height=45,
            corner_radius=12,
            border_width=2,
            border_color="#e0e0e0",
            fg_color="#f8f9fa",
            text_color="#2c3e50",
            font=("Segoe UI", 14)
        )
        self.name_entry.pack(fill='x')
        self.name_entry.bind("<Return>", lambda event: self.email_entry.focus_set())
        self.name_entry.bind("<KeyRelease>", self.validate_name_input)
        
        # Name requirements
        name_requirements = ctk.CTkLabel(
            name_frame, 
            text="Only letters and spaces allowed",
            font=("Segoe UI", 12),
            text_color="#95a5a6"
        )
        name_requirements.pack(anchor='w', pady=(5, 0))

        # Email Section
        email_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        email_frame.pack(fill='x', pady=(0, 15))
        
        email_label = ctk.CTkLabel(
            email_frame,
            text="Email Address",
            font=("Segoe UI", 14, "bold"),
            text_color="#2c3e50"
        )
        email_label.pack(anchor='w', pady=(0, 8))
        
        self.email_entry = ctk.CTkEntry(
            email_frame,
            placeholder_text="Enter your email",
            height=45,
            corner_radius=12,
            border_width=2,
            border_color="#e0e0e0",
            fg_color="#f8f9fa",
            text_color="#2c3e50",
            font=("Segoe UI", 14)
        )
        self.email_entry.pack(fill='x')
        self.email_entry.bind("<Return>", lambda event: self.password_entry.focus_set())

        # Password Section
        password_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        password_frame.pack(fill='x', pady=(0, 15))
        
        password_label = ctk.CTkLabel(
            password_frame,
            text="Password",
            font=("Segoe UI", 14, "bold"),
            text_color="#2c3e50"
        )
        password_label.pack(anchor='w', pady=(0, 8))
        
        # Password requirements
        pass_requirements = ctk.CTkLabel(
            password_frame,
            text="Must contain uppercase, number, and be 8+ characters",
            font=("Segoe UI", 12),
            text_color="#95a5a6"
        )
        pass_requirements.pack(anchor='w', pady=(0, 8))
        
        # Password entry with show/hide
        password_entry_frame = ctk.CTkFrame(password_frame, fg_color="transparent")
        password_entry_frame.pack(fill='x')
        
        self.password_entry = ctk.CTkEntry(
            password_entry_frame,
            show="•",
            placeholder_text="Enter your password",
            height=45,
            corner_radius=12,
            border_width=2,
            border_color="#e0e0e0",
            fg_color="#f8f9fa",
            text_color="#2c3e50",
            font=("Segoe UI", 14)
        )
        self.password_entry.pack(side="left", fill="x", expand=True)
        self.password_entry.bind("<Return>", lambda event: self.confirm_password_entry.focus_set())
        
        self.show_password_cb = ctk.CTkCheckBox(
            password_entry_frame,
            text="Show",
            width=20,
            height=20,
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=4,
            fg_color="#3498db",
            hover_color="#2980b9",
            border_color="#3498db",
            text_color="#2c3e50",
            font=("Segoe UI", 12),
            command=lambda: self.toggle_password_visibility(self.password_entry)
        )
        self.show_password_cb.pack(side="right", padx=(10, 0))

        # Confirm Password Section
        confirm_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        confirm_frame.pack(fill='x', pady=(0, 20))
        
        confirm_label = ctk.CTkLabel(
            confirm_frame,
            text="Confirm Password",
            font=("Segoe UI", 14, "bold"),
            text_color="#2c3e50"
        )
        confirm_label.pack(anchor='w', pady=(0, 8))
        
        # Confirm password entry with show/hide
        confirm_entry_frame = ctk.CTkFrame(confirm_frame, fg_color="transparent")
        confirm_entry_frame.pack(fill='x')
        
        self.confirm_password_entry = ctk.CTkEntry(
            confirm_entry_frame,
            show="•",
            placeholder_text="Confirm your password",
            height=45,
            corner_radius=12,
            border_width=2,
            border_color="#e0e0e0",
            fg_color="#f8f9fa",
            text_color="#2c3e50",
            font=("Segoe UI", 14)
        )
        self.confirm_password_entry.pack(side="left", fill="x", expand=True)
        self.confirm_password_entry.bind("<Return>", lambda event: self.register_user())
        
        self.show_confirm_password_cb = ctk.CTkCheckBox(
            confirm_entry_frame,
            text="Show",
            width=20,
            height=20,
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=4,
            fg_color="#3498db",
            hover_color="#2980b9",
            border_color="#3498db",
            text_color="#2c3e50",
            font=("Segoe UI", 12),
            command=lambda: self.toggle_password_visibility(self.confirm_password_entry)
        )
        self.show_confirm_password_cb.pack(side="right", padx=(10, 0))

        # Error Label
        self.reg_error_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="",
            text_color="#e74c3c",
            font=("Segoe UI", 12),
            wraplength=320
        )
        self.reg_error_label.pack(pady=(10, 5))

        # Register Button
        regis_icon = Image.open(LoginForm.resource_path("icons/register.png"))
        self.regis_icon = ctk.CTkImage(
            light_image=regis_icon, 
            dark_image=regis_icon, 
            size=(24, 24)
        )
        
        register_button = ctk.CTkButton(
            self.scrollable_frame,
            text="Create Account",
            image=self.regis_icon,
            command=self.register_user,
            width=320,
            height=50,
            corner_radius=12,
            fg_color="#27ae60",
            hover_color="#219653",
            text_color="white",
            font=("Segoe UI", 16, "bold")
        )
        register_button.pack(pady=(10, 20))

        # Login Link Section
        login_frame = ctk.CTkFrame(self.overlay_frame, fg_color="transparent")
        login_frame.pack(pady=(0, 25))

        go_login = ctk.CTkLabel(
            login_frame,
            text="Already have an account?",
            font=("Segoe UI", 14),
            text_color="#7f8c8d"
        )
        go_login.pack(side="left", padx=(0, 5))

        login_link = ctk.CTkLabel(
            login_frame,
            text="Login Here",
            font=("Segoe UI", 14, "bold", "underline"),
            text_color="#3498db",
            cursor="hand2"
        )
        login_link.pack(side="left")
        login_link.bind("<Button-1>", self.handle_back_click)

        # Bind Enter key to register
        self.overlay_frame.bind("<Return>", lambda event: self.register_user())

    def toggle_password_visibility(self, entry_widget):
        """Toggle password visibility for the specified entry widget"""
        if entry_widget == self.password_entry:
            is_checked = self.show_password_cb.get()
        else:
            is_checked = self.show_confirm_password_cb.get()
        entry_widget.configure(show="" if is_checked else "•")
    
    def validate_name_input(self, event):
        """Validate name input to allow only letters and spaces"""
        name = self.name_entry.get()
        # Keep only letters and spaces
        valid_name = ''.join(c for c in name if c.isalpha() or c.isspace())
    
        # If the input was modified, update the entry
        if valid_name != name:
            self.name_entry.delete(0, 'end')
            self.name_entry.insert(0, valid_name)

    def register_user(self):
        """Register new user with validation"""
        # Clear any previous error message
        self.reg_error_label.configure(text="")
        
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        # Validation checks
        if not name:
            self.reg_error_label.configure(text="Name is required")
            return
        
        if not all(c.isalpha() or c.isspace() for c in name):
            self.reg_error_label.configure(text="Name can only contain letters and spaces")
            return
        
        if len(name.split()) < 2:
            self.reg_error_label.configure(text="Please enter your full name (first and last)")
            return

        if not email:
            self.reg_error_label.configure(text="Email is required")
            return

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self.reg_error_label.configure(text="Please enter a valid email address")
            return

        if not password:
            self.reg_error_label.configure(text="Password is required")
            return

        if not confirm_password:
            self.reg_error_label.configure(text="Please confirm your password")
            return

        if password != confirm_password:
            self.reg_error_label.configure(text="Passwords do not match")
            return

        # Password validation
        is_valid, message = self.validate_password(password)
        if not is_valid:
            self.reg_error_label.configure(text=message)
            return

        try:
            # Check if user already exists
            existing_user = self.db_handler.get_user_by_email(email)
            
            if existing_user:
                self.reg_error_label.configure(text="Email already registered")
                return

            # Get next available user ID
            new_id = self.db_handler.get_next_user_id()
            if not new_id:
                self.reg_error_label.configure(text="Failed to generate user ID. Please try again.")
                return

            # Hash the password
            hashed_password, salt = self.hash_password(password)
            
            # Save the new user
            success = self.db_handler.save_user(
                id=new_id, 
                email=email, 
                hashed_password=hashed_password, 
                salt=salt, 
                username=name
            )
            
            if success:
                # Show success message
                self.reg_error_label.configure(
                    text="✅ Registration successful! Please wait for admin approval.", 
                    text_color="#27ae60"
                )
                
                # Clear form fields
                self.name_entry.delete(0, 'end')
                self.email_entry.delete(0, 'end')
                self.password_entry.delete(0, 'end')
                self.confirm_password_entry.delete(0, 'end')
                
                # Auto-redirect to login after 2 seconds
                self.master.after(2000, self.redirect_to_login)
                
            else:
                self.reg_error_label.configure(text="❌ Registration failed. Please try again.")
                
        except Exception as e:
            print(f"Registration error: {e}")
            error_message = str(e)
            if "duplicate key" in error_message.lower():
                self.reg_error_label.configure(text="❌ Email already registered")
            elif "connection" in error_message.lower():
                self.reg_error_label.configure(text="❌ Database connection error. Please try again.")
            else:
                self.reg_error_label.configure(text=f"❌ Registration error: {error_message}")

    def redirect_to_login(self):
        """Redirect to login form after successful registration"""
        # Clear all widgets
        if self.original_master.winfo_exists():
            for widget in self.original_master.winfo_children():
                widget.destroy()
            
        # Create new login form
        LoginForm(self.original_master, self.login_success_callback, self.admin_login_callback)

    def handle_back_click(self, event=None):
        """Handle back to login click"""
        # Clear all widgets in the original_master
        if self.original_master.winfo_exists():
            for widget in self.original_master.winfo_children():
                widget.destroy()
            
        # Create new login form
        LoginForm(self.original_master, self.login_success_callback, self.admin_login_callback)

    def validate_password(self, password):
        """Validate password strength"""
        has_upper = any(c.isupper() for c in password)
        has_number = any(c.isdigit() for c in password)
        has_special = not password.isalnum()  # Checks for special characters
        is_long_enough = len(password) >= 8

        if not has_upper:
            return False, "Password must contain at least one uppercase letter"
        if not has_number:
            return False, "Password must contain at least one number"
        if has_special:
            return False, "Password must not contain special characters"
        if not is_long_enough:
            return False, "Password must be at least 8 characters long"
        
        return True, "Password is valid"