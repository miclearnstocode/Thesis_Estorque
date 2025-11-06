from tkinter import messagebox
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import hashlib, os, re
from database import DatabaseHandler
from PIL import Image
import sys, os
from time import time
from postgres_manager import PostgresManager  # Add this import

class LoginForm(ctk.CTkFrame):
    def __init__(self, master, login_success_callback=None, admin_login_callback=None):
        super().__init__(master)
        self.master = master
        
        # Database Handler
        self.db_handler = DatabaseHandler()
        self.failed_attempts = []
        self.lockout_until = 0  # timestamp when user can try again
        # Login success callback
        self.login_success_callback = login_success_callback
        self.admin_login_callback = admin_login_callback

        # Get screen dimensions
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Load and resize the background image to fit the screen
        self.background_image = Image.open(self.resource_path("Image/Gradient.jpg"))
        self.background_image = self.background_image.resize((screen_width, screen_height), Image.LANCZOS)
        self.background_photo = ctk.CTkImage(light_image=self.background_image, dark_image=self.background_image, size=(screen_width, screen_height))

        # Create a label to hold the background image
        self.background_label = ctk.CTkLabel(self.master, image=self.background_photo, text="")
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Create a frame holder for the label with a background color
        frame_holder = ctk.CTkFrame(self.master, width=400, height=100, fg_color="lightgray")  # Adjust width and height as needed
        frame_holder.place(x=400, y=10)  # Position the frame

        # Create a label for student appraisal inside the frame
        appraisal_label = ctk.CTkLabel(frame_holder, text="Student Appraisal and Monitoring using Machine Learning", font=("Vivaldi", 24, "bold"),text_color="black")
        appraisal_label.pack(pady=10, padx=10)  # Add padding for better visibility

        frame_holder.lift()

        # Define frame dimensions and position
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        frame_x = int(screen_width / 2)
        frame_y = int(screen_height / 2)
        
        # Load and resize the CSD logo
        self.nami_image = Image.open(self.resource_path("Image/CSD.jpg"))
        csd_width = 100
        csd_height = 100
        self.nami_image = self.nami_image.resize((csd_width, csd_height), Image.LANCZOS)
        self.nami_photo = ctk.CTkImage(light_image=self.nami_image, dark_image=self.nami_image, size=(100, 100))

        # Load and resize the Capiz State University logo
        self.capsu_image = Image.open(self.resource_path("Image/Capiz_State_University_2.png"))
        capsu_width = 150
        capsu_height = 150
        self.capsu_image = self.capsu_image.resize((capsu_width, capsu_height), Image.LANCZOS)
        self.capsu_photo = ctk.CTkImage(light_image=self.capsu_image, dark_image=self.capsu_image, size=(150, 150))

        # Create and place the CapSU logo
        self.capsu_logo_label = ctk.CTkLabel(self.master, image=self.capsu_photo, text="", bg_color='#2196F3')
        self.capsu_logo_label.place(x=self.master.winfo_screenwidth() - capsu_width - 20, y=20)

        # Create a container frame
        self.container = ctk.CTkFrame(self.master, width=400, height=500, fg_color="white", corner_radius=15, border_width=0, border_color="black" )
        self.container.place(x=frame_x, y=frame_y, anchor="center")
        self.container.pack_propagate(False)
        self.container.grid_propagate(False)
        # Create login widgets
        self.create_login_widgets()
        
    @staticmethod  
    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS  # PyInstaller temp folder
        except AttributeError:
            base_path = os.path.abspath(".")  # Running normally
        return os.path.join(base_path, relative_path)

    def create_login_widgets(self):
        # Clear existing widgets except the CSD logo
        if self.container and self.container.winfo_exists():
            for widget in self.container.winfo_children():
                widget.destroy()

        # Add the CSD logo at the top
        self.csd_logo = ctk.CTkLabel(self.container, image=self.nami_photo, text="")
        self.csd_logo.pack(pady=(20, 10))
        
        title_label = ctk.CTkLabel(self.container, text="Login", font=ctk.CTkFont(family="Helvetica", size=24, weight="bold"))
        title_label.pack(pady=(0, 20))

        # Email entry
        email_label = ctk.CTkLabel(self.container, text="Email", font=ctk.CTkFont(size=14))
        email_label.pack(anchor="w", padx=20)

        self.email_entry = ctk.CTkEntry(self.container, width=280, height=40, placeholder_text="Enter your email", corner_radius=30)
        self.email_entry.pack(fill="x", padx=20, pady=(0, 10))
        self.email_entry.bind("<Return>", lambda event: self.focus_next_widget())
        self.email_entry.bind("<KeyRelease>", self.auto_complete_gmail)

        # Password entry
        password_label = ctk.CTkLabel(self.container, text="Password", font=ctk.CTkFont(size=14))
        password_label.pack(anchor="w", padx=20)

        self.password_entry = ctk.CTkEntry(self.container, show="*", placeholder_text="Enter your password", height=40, corner_radius=30)
        self.password_entry.pack(fill="x", padx=20, pady=(0, 10))
        self.password_entry.bind("<Return>", lambda event: self.validate_login())

        self.show_password_cb = ctk.CTkCheckBox(self.container, text="Show", width=20, height=20, checkbox_width=16, checkbox_height=16, corner_radius=3, fg_color="#2196F3", hover_color="#1976D2", command=lambda: self.toggle_password_visibility(self.password_entry), font=("Helvetica", 12))
        self.show_password_cb.pack(anchor="w", padx=20)

        # Error label (add this before the login button)
        self.error_label = ctk.CTkLabel(self.container, text="", text_color="red", font=ctk.CTkFont("Helvetica", size=14), wraplength=280)
        self.error_label.pack(pady=(5, 0))

        login_icon = Image.open(self.resource_path("icons/logins.png"))
        self.login_icon = ctk.CTkImage(light_image=login_icon, dark_image=login_icon, size=(30, 30))
        login_button = ctk.CTkButton(self.container, text="Login", image=self.login_icon, command=self.validate_login, width=80, height=40, text_color="black", fg_color="transparent", hover_color="#707070", border_color="grey", border_width=1, corner_radius=30, font=ctk.CTkFont(size=15, weight="bold"))
        login_button.pack(fill='x', padx=20, pady=(1, 20))

        # Registration link
        reg_label = ctk.CTkLabel(self.container,  text="Don't have an account?", font=ctk.CTkFont(size=12),text_color="black")
        reg_label.place(x=91, y=431)

        register_link = ctk.CTkLabel(self.container, text="Register", font=ctk.CTkFont(size=12, underline=True), text_color="blue", cursor="hand2")
        register_link.place(x=221, y=431)
        register_link.bind("<Button-1>", self.open_registration)
        self.timer_label = ctk.CTkLabel(self.container, text="", text_color="red")
        self.timer_label.pack(pady=(10, 0))

    def auto_complete_gmail(self, event):
        """Automatically complete the email domain when typing in the email entry"""
        current_text = self.email_entry.get()
        if current_text.endswith("@") and current_text.count("@") == 1:
            self.email_entry.insert("end", "gmail.com")
            self.email_entry.icursor("end")

    def focus_next_widget(self):
        """Move focus to password entry when Enter is pressed in email entry"""
        self.password_entry.focus_set()

    def toggle_password_visibility(self, entry_widget):
        """Toggle password visibility for the specified entry widget"""
        if entry_widget == self.password_entry:
            is_checked = self.show_password_cb.get()
        else:
            is_checked = self.show_confirm_password_cb.get()
        entry_widget.configure(show="" if is_checked else "•")

    def hash_password(self, password, salt=None):
        if salt is None:
            salt = os.urandom(32).hex()
        
        salted_password = password + salt
        hashed_password = hashlib.sha256(salted_password.encode()).hexdigest()
        
        return hashed_password, salt

    def validate_login(self):
        current_time = time()
        # Clear any previous error message
        self.error_label.configure(text="")
        
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        if current_time < self.lockout_until:
            wait_time = int(self.lockout_until - current_time)
            self.error_label.configure(text=f"Too many failed attempts. Please try again in {wait_time} seconds.")
            return
            
        if not email or not password:
            self.error_label.configure(text="Please enter both email and password")
            return
            
        # Admin credentials check - bypass all other validations
        if email == "admin@gmail.com" and password == "BSCS@2024!":
            self.error_label.configure(text="Admin Login Successful!", text_color="green")
            if self.admin_login_callback:
                self.after(1000, self.admin_login_callback)
            return

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self.error_label.configure(text="Invalid email format")
            return
        
        try:
            user_data = self.db_handler.get_user_by_email(email)
            
            if user_data:
                hashed_password, _ = self.hash_password(password, user_data['salt'])
                
                if hashed_password == user_data['password']:
                    # Check if user is active
                    if not user_data['is_active']:
                        self.error_label.configure(text="Account is not yet activated. Please wait for admin approval.")
                        return

                    # Update last_login timestamp
                    self.db_handler.cursor.execute("UPDATE admin_management SET last_login = NOW() WHERE id = %s", (user_data['id'],))
                    self.db_handler.conn.commit()
                    # Success case
                    self.error_label.configure(text="Login Successful!", text_color="green")
                    if self.login_success_callback:
                        self.after(1000, self.login_success_callback)
                    else:
                        self.after(1000, self.master.destroy)
                else:
                    self.error_label.configure(text="Invalid email or password")
            else:
                self.error_label.configure(text="User not found")
        
        except Exception as e:
            self.error_label.configure(text=f"Login error: {str(e)}")
            
        # Additional validation for failed attempts
        if self.is_login_valid(email, password):
            # Reset failed attempts if login is valid
            self.failed_attempts.clear()
            self.lockout_until = 0
            if self.login_success_callback:
                self.login_success_callback()
        else:
            self.failed_attempts.append(current_time)
            self.failed_attempts = [t for t in self.failed_attempts if current_time - t < 60]  # Keep only last 60 seconds
            if len(self.failed_attempts) >= 5:
                self.lockout_until = current_time + 900 # 15 minutes
                messagebox.showerror("Login Failed", "Too many failed attempts locked for 15 minutes. Please try again later.")
                self.start_countdown(self.lockout_until)  # Start countdown for 15 minutes
            else:
                remaining = 5 - len(self.failed_attempts)
                self.error_label.configure(text=f"Invalid email or password. {remaining} attempts remaining.")

    def is_login_valid(self, email, password):
        """Check if the provided email and password are valid"""
        try:
            user_data = self.db_handler.get_user_by_email(email)
            if user_data:
                hashed_password, _ = self.hash_password(password, user_data['salt'])
                return hashed_password == user_data['password']
            return False
        except Exception as e:
            print(f"Error validating login: {e}")
            return False
    
    def start_countdown(self, seconds_left):
        if seconds_left > 0:
            mins, secs = divmod(seconds_left, 60)
            time_str = f"Locked out: {mins:02}:{secs:02} remaining"
            self.timer_label.configure(text=time_str)
            # Schedule the next update after 1 second
            self.after(1000, self.start_countdown, seconds_left - 1)
        else:
            self.timer_label.configure(text="You can try logging in again.")
            self.lockout_until = 0  # unlock

    def open_registration(self, event=None):
        if hasattr(self, 'form_frame') and self.form_frame.winfo_exists():
            self.form_frame.destroy()

        # Create the registration form
        self.registration_form = RegistrationForm(
            master=self.master, 
            db_handler=self.db_handler, 
            hash_function=self.hash_password, 
            back_callback=self.create_login_widgets,
            login_success_callback=self.login_success_callback,  # Pass the login success callback
            admin_login_callback=self.admin_login_callback)

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

        # Load and resize the background image to fit the entire screen
        bg_image = Image.open(LoginForm.resource_path("Image/loginform.jpg"))
        self.background_photo = ctk.CTkImage(light_image=bg_image, dark_image=bg_image, size=(screen_width, screen_height))

        # Create a label to hold the background image
        self.background_label = ctk.CTkLabel(self.original_master, image=self.background_photo, text="")
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

        frame_width = 400
        frame_height = 400

        self.overlay_frame = ctk.CTkFrame(self.master, width=frame_width, height=frame_height, fg_color="transparent", corner_radius=15, border_width=1)
        self.overlay_frame.place(x=500, y=100)

        # Now create the widgets
        self.create_registration_widgets()

    def create_registration_widgets(self):
        # Title
        title_label = ctk.CTkLabel(self.overlay_frame, text="Register", font=ctk.CTkFont(family="Helvetica", size=24, weight="bold"), text_color="black")
        title_label.pack(pady=20)

        # Create a scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self.overlay_frame, fg_color="transparent",width=330, height=400 )
        self.scrollable_frame.pack(expand=True, fill='both', padx=20, pady=(0,10))

        # Name container
        name_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        name_frame.pack(fill='x', pady=5)
        
        name_label = ctk.CTkLabel(name_frame, text="Full Name", font=ctk.CTkFont(size=14), text_color="black")
        name_label.pack(anchor='w')
        
        self.name_entry = ctk.CTkEntry(name_frame, placeholder_text="Enter your full name", height=35, corner_radius=30)
        self.name_entry.pack(fill='x')
        self.name_entry.bind("<Return>", lambda event: self.email_entry.focus_set())
        self.name_entry.bind("<KeyRelease>", self.validate_name_input)
        
        # Add name requirements label
        name_requirements = ctk.CTkLabel(
            name_frame, 
            text="Only letters and spaces allowed",
            font=ctk.CTkFont(size=12),
            text_color="gray")
        name_requirements.pack(anchor='w')

        # Email container
        email_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        email_frame.pack(fill='x', pady=5)
        
        email_label = ctk.CTkLabel(email_frame, text="Email", font=ctk.CTkFont(size=14), text_color="black")
        email_label.pack(anchor='w')
        
        self.email_entry = ctk.CTkEntry(email_frame, placeholder_text="Enter your email", height=35, corner_radius=30)
        self.email_entry.pack(fill='x')
        self.email_entry.bind("<Return>", lambda event: self.password_entry.focus_set())

        # Password container
        password_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        password_frame.pack(fill='x', pady=5)
        
        password_label = ctk.CTkLabel(password_frame, text="Password", font=ctk.CTkFont(size=14), text_color="black")
        password_label.pack(anchor='w')
        
        pass_label = ctk.CTkLabel(password_frame, text="Password must contain e.g. A,3,n", font=("Helviteca", 12), text_color="gray")
        pass_label.pack(anchor='w')
        
        # Add password entry and show checkbox in a container
        password_entry_frame = ctk.CTkFrame(password_frame, fg_color="transparent")
        password_entry_frame.pack(fill='x')
        
        self.password_entry = ctk.CTkEntry(password_entry_frame, show="•", placeholder_text="Enter your password", height=35, corner_radius=30)
        self.password_entry.pack(side="left", fill="x", expand=True)
        self.password_entry.bind("<Return>", lambda event: self.confirm_password_entry.focus_set())
        
        self.show_password_cb = ctk.CTkCheckBox(password_entry_frame,text="Show",width=20,height=20,checkbox_width=16,checkbox_height=16,corner_radius=3,fg_color="#2196F3",hover_color="#1976D2",command=lambda: self.toggle_password_visibility(self.password_entry), font=("Helvetica", 12))
        self.show_password_cb.pack(side="right", padx=(5, 0))

        # Confirm Password container
        confirm_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        confirm_frame.pack(fill='x', pady=5)
        
        confirm_label = ctk.CTkLabel(confirm_frame, text="Confirm Password", font=ctk.CTkFont(size=14), text_color="black")
        confirm_label.pack(anchor='w')
        
        # Add confirm password entry and show checkbox in a container
        confirm_entry_frame = ctk.CTkFrame(confirm_frame, fg_color="transparent")
        confirm_entry_frame.pack(fill='x')
        
        self.confirm_password_entry = ctk.CTkEntry(confirm_entry_frame, show="•", placeholder_text="Confirm your password", height=35, corner_radius=30)
        self.confirm_password_entry.pack(side="left", fill="x", expand=True)
        self.confirm_password_entry.bind("<Return>", lambda event: self.register_user())
        
        self.show_confirm_password_cb = ctk.CTkCheckBox(confirm_entry_frame,text="Show",width=20,height=20,checkbox_width=16,checkbox_height=16,corner_radius=3,fg_color="#2196F3",hover_color="#1976D2",command=lambda: self.toggle_password_visibility(self.confirm_password_entry),font=("Helvetica", 12))
        self.show_confirm_password_cb.pack(side="right", padx=(5, 0))
       
        # Add error label above register button
        self.reg_error_label = ctk.CTkLabel(self.scrollable_frame, text="", text_color="red", font=ctk.CTkFont(size=12), wraplength=280)
        self.reg_error_label.pack(pady=(5, 0))

        regis_icon =Image.open(LoginForm.resource_path("icons/register.png"))
        self.regis_icon = ctk.CTkImage(light_image=regis_icon, dark_image=regis_icon, size=(30, 30))
        register_button = ctk.CTkButton(self.scrollable_frame, text="Register", image=self.regis_icon,command=self.register_user, corner_radius=30, height=40, font=ctk.CTkFont(size=15, weight="bold"))
        register_button.pack(pady=30)
        
        self.overlay_frame.bind("<Return>", lambda event: self.register_user())
        self.scrollable_frame.bind("<Return>", lambda event: self.register_user())

        go_login = ctk.CTkLabel(self.scrollable_frame, text="Already have an account?", font=ctk.CTkFont(size=12), text_color="black")
        go_login.place(x=72, y=460)

        login_link= ctk.CTkLabel(self.scrollable_frame,text="Login", font=ctk.CTkFont(size=12, underline=True), text_color="blue", cursor="hand2")
        login_link.place(x=212, y=460)
        login_link.bind("<Button-1>", self.handle_back_click)

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
    
    def validate_email(self, event):
        email = self.email_entry.get()

        valid_email = ''.join(c for c in email if c.isalpha() or c.isspace())

        if valid_email != email:
            self.email_entry.delete(0, 'end')
            self.email_entry.insert(0, valid_email)

    def register_user(self):
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
            self.reg_error_label.configure(text="Please enter your full name")
            return

        if not email:
            self.reg_error_label.configure(text="Email is required")
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

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self.reg_error_label.configure(text="Invalid email format")
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
                    text_color="green"
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
            print(f"Full registration error: {e}")
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
        # Clear all widgets in the original_master
        if self.original_master.winfo_exists():
            for widget in self.original_master.winfo_children():
                widget.destroy()
            
        # Create new login form
        LoginForm(self.original_master, self.login_success_callback, self.admin_login_callback)

    def validate_password(self, password):
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

    def show_message(self, message, is_success=True):
        """Show a message to the user with appropriate styling"""
        if is_success:
            self.reg_error_label.configure(text=f"✅ {message}", text_color="green")
        else:
            self.reg_error_label.configure(text=f"❌ {message}", text_color="red")