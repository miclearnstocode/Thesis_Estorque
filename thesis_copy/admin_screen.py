import logging
from tkinter import ttk, messagebox
import customtkinter as ctk
from database import DatabaseHandler
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk
from tkinter import messagebox
import threading
import time
import queue, os
from PIL import Image
from loginform import LoginForm

class LoadingScreen(ctk.CTkToplevel):
    def __init__(self, parent, message="Refreshing..."):
        super().__init__(parent)
        self.title("Loading")
        self.geometry("300x200")
        self.overrideredirect(True)
        self.configure(fg_color="white")
        
        """Namion ko pa gid ya desig diri since ini ang 
        medyo kalain kay ang combination sini indi 
        manami kag ya structure ka admin kalain"""
        
        # Center the loading screen
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        window_width = 300
        window_height = 200
        x = parent_x + (parent_width // 2) - (window_width // 2)
        y = parent_y + (parent_height // 2) - (window_height // 2)
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Create a semi-transparent background
        self.attributes("-alpha", 0.8)
        
        # Loading frame
        loading_frame = ctk.CTkFrame(self, fg_color="transparent")
        loading_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Spinning loading indicator
        self.loading_label = ctk.CTkLabel(loading_frame, text="", font=ctk.CTkFont(size=16, weight="bold"))
        self.loading_label.pack(expand=True, fill="both")
        
        # Spinner animation
        self.spinner_frames = [
            "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛"]
        self.current_frame = 0
        
        # Message label
        self.message_label = ctk.CTkLabel(loading_frame, text=message, font=ctk.CTkFont(size=14))
        self.message_label.pack(pady=(10, 0))
        
        # Start spinning animation
        self.animate_spinner()
    
    def animate_spinner(self):
        """Create spinning animation"""
        self.loading_label.configure(text=self.spinner_frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % len(self.spinner_frames)
        self.after(100, self.animate_spinner)

class AdminScreen(ctk.CTkFrame):
    def enhanced_refresh(self):
        """Enhanced refresh method with loading screen and thread-safe updates"""
        def refresh_task(result_queue):
            try:
                # Simulate some loading time (optional)
                time.sleep(1)  
                
                # Prepare refresh data
                user_data = self.prepare_user_refresh()
                stats_data = self.prepare_statistics_refresh()
                
                # Put results in queue
                result_queue.put((user_data, stats_data))
            
            except Exception as e:
                result_queue.put(('error', str(e)))
        
        def process_refresh_results():
            try:
                # Check if there are results
                if not result_queue.empty():
                    result = result_queue.get_nowait()
                    
                    # Check for error
                    if result[0] == 'error':
                        messagebox.showerror("Refresh Error", result[1])
                        return
                    
                    # Unpack results
                    user_data, stats_data = result
                    
                    # Update user management table
                    self.update_user_table(user_data)
                    
                    # Update statistics plots
                    self.update_statistics_plots(stats_data)
                    
                    # Close loading screen
                    if hasattr(self, 'loading_screen'):
                        self.loading_screen.destroy()
                    
                    messagebox.showinfo("Refresh", "Data successfully updated!")
                else:
                    # Continue checking if results are not ready
                    self.after(100, process_refresh_results)
            except Exception as e:
                messagebox.showerror("Processing Error", str(e))
                if hasattr(self, 'loading_screen'):
                    self.loading_screen.destroy()
        
        # Create a queue for thread-safe communication
        result_queue = queue.Queue()
        
        # Create loading screen
        self.loading_screen = LoadingScreen(self, message="Refreshing data...")
        
        # Start refresh thread
        threading.Thread(target=refresh_task, args=(result_queue,),daemon=True).start()
        
        # Start processing results
        self.after(100, process_refresh_results)
    
    def prepare_user_refresh(self):
        """Prepare user data for refresh"""
        # Implement your user data retrieval logic
        # Return a dataframe or list of user data
        try:
            db = DatabaseHandler()
            user_data = db.get_all_users()  # Implement this method in your DatabaseHandler
            db.close_db_connection()
            return user_data
        except Exception as e:
            raise Exception(f"User data refresh failed: {e}")
    
    def prepare_statistics_refresh(self):
        """Prepare statistics data for refresh"""
        # Implement your statistics data retrieval logic
        try:
            db = DatabaseHandler()
            stats_data = {'year_counts': db.get_students_per_year(),'level_counts': db.get_students_per_level()}
            db.close_db_connection()
            return stats_data
        except Exception as e:
            raise Exception(f"Statistics refresh failed: {e}")
    
    def update_user_table(self, user_data):
        """Update user management table with new data"""
        # Clear existing table
        for item in self.user_table.get_children():
            self.user_table.delete(item)
        
        # Insert new data
        for user in user_data:
            self.user_table.insert('', 'end', values=user)
    
    def update_statistics_plots(self, stats_data):
        """Update statistics plots with new data"""
        # Clear existing plots
        for ax in self.axes:
            ax.clear()
        
        # Recreate plots with new data
        years = list(stats_data['year_counts'].keys())
        year_counts = list(stats_data['year_counts'].values())
        levels = list(stats_data['level_counts'].keys())
        level_counts = list(stats_data['level_counts'].values())
        
        # Replot with dynamic coloring
        def get_color(count, max_count):
            if count <= max_count * 0.3:
                return '#FF6347'  # Tomato Red
            elif count <= max_count * 0.7:
                return '#1E90FF'  # Dodger Blue
            else:
                return '#32CD32'  # Lime Green
        
        # First plot (Students per Enrolled Year)
        max_year_count = max(year_counts)
        year_colors = [get_color(count, max_year_count) for count in year_counts]
        self.axes[0].barh(years, year_counts, color=year_colors)
        self.axes[0].set_title('Students per Enrolled Year')
        
        # Second plot (Students per Year Level)
        max_level_count = max(level_counts)
        level_colors = [get_color(count, max_level_count) for count in level_counts]
        self.axes[1].bar(levels, level_counts, color=level_colors)
        self.axes[1].set_title('Students per Year Level')
        
        # Refresh the canvas to show updated plots
        self.canvas.draw()
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.db_handler = DatabaseHandler()
        
        # Bind cleanup method to window destroy event
        self.bind("<Destroy>", self.cleanup)
        
        # Main container with grid layout
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Configure grid weights for columns and rows
        self.main_container.grid_columnconfigure(0, weight=1)  # Left frame
        self.main_container.grid_columnconfigure(1, weight=4)  # Center frame - increased ratio
        self.main_container.grid_columnconfigure(2, weight=1)  # Right frame
        self.main_container.grid_rowconfigure(0, weight=2)  # Top row
        self.main_container.grid_rowconfigure(1, weight=1)  # Bottom row
        
        # Create frames
        self.left_frame = ctk.CTkFrame(master=self.main_container, fg_color="#F0F0F0")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        # Button style configuration
        button_style = {
            "fg_color": "transparent",    
            "hover_color": "#707070",     
            "text_color": "black",        
            "height": 32,                 
            "border_width": 1,            
            "border_color": "black"}
        # Button container frame in left frame
        button_container = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        button_container.pack(fill="x", pady=20, padx=10)
        
        # Title for buttons
        button_title = ctk.CTkLabel(button_container,text="Controls",font=ctk.CTkFont(size=16, weight="bold"))
        button_title.pack(pady=(0, 10))
        
        home_icon =Image.open(LoginForm.resource_path("icons/Home.png"))
        self.home_icon =ctk.CTkImage(light_image=home_icon, dark_image=home_icon, size=(20, 20))
        self.home_btn = ctk.CTkButton(button_container,text="Home",image=self.home_icon,command=self.return_to_home,width=150,**button_style)
        self.home_btn.pack(pady=5)
        
        # Refresh button
        # Update refresh button to use enhanced method
        self.refresh_btn = ctk.CTkButton(button_container, text="Refresh", command=self.enhanced_refresh, width=150,**button_style)
        self.refresh_btn.pack(pady=5)
        
        
        # Center Frame (for Treeview)
        self.center_frame = ctk.CTkFrame(self.main_container)
        self.center_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Right Frame
        self.right_frame = ctk.CTkFrame(self.main_container, fg_color="#F0F0F0")
        self.right_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        
        user_icon = Image.open(LoginForm.resource_path("icons/user.png"))
        self.user_icon = ctk.CTkImage(light_image=user_icon, dark_image=user_icon, size=(30, 30))

        try:
            user_icon = Image.open(LoginForm.resource_path("icons/user.png"))
            self.user_icon = ctk.CTkImage(light_image=user_icon, dark_image=user_icon, size=(30, 30))
            title_label = ctk.CTkLabel(self.center_frame, text="User Account Management",image=self.user_icon,
                font=ctk.CTkFont("Helvetica", size=20, weight="bold"), text_color='grey50')
        except Exception as e:
            print(f"Failed to load user icon: {e}")
            # Create label without icon if image loading fails
            title_label = ctk.CTkLabel(self.center_frame, text="User Account Management",font=ctk.CTkFont("Helvetica", size=20, weight="bold"), text_color='grey50')
        title_label.pack(pady=10)
        
        # Create Treeview frame with reduced height
        tree_frame = ctk.CTkFrame(self.center_frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10)) 
        
        # Configure column weights to center the treeview
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Add bottom frame that stretches across columns 1 and 2
        self.bottom_frame = ctk.CTkFrame(self.main_container,fg_color="#F0F0F0", height=350)
        self.bottom_frame.grid(row=1, rowspan=2, column=0, columnspan=4, sticky="n", padx=10, pady=10)
        
        # Configure frame heights
        self.center_frame.configure(height=200)  # Adjust this value as needed
        self.right_frame.configure(height=200)   # Match center frame height
        
        # Prevent automatic resizing
        self.center_frame.grid_propagate(False)
        self.right_frame.grid_propagate(False)
        self.bottom_frame.grid_propagate(False)
        self.setup_bottom_frame()
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        y_scroll.grid(row=0, column=1, sticky="ns")
        
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal")
        x_scroll.grid(row=1, column=0, sticky="ew")
        
        # Configure Treeview style
        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', 12),rowheight=35)
        style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'))
        
        # Configure alternating colors
        style.map('Treeview', background=[('selected', '#0078D7')],)  # Selection color

        style.configure('Treeview', 
            background='white',  # Default background
            fieldbackground='white',  # Color of empty space
            selectbackground='#0078D7'  # Selection color
        )

        # Create Treeview
        self.user_tree = ttk.Treeview(tree_frame,columns=('ID', 'Name', 'Email', 'Status', 'Pause'),
            show='headings', yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set, height=20,style="Treeview")
        self.user_tree.grid(row=0, column=0, sticky="nsew")
        
        # Add tag configuration for alternating rows
        self.user_tree.tag_configure('oddrow', background='#F5F5F5')
        self.user_tree.tag_configure('evenrow', background='white')
        
        # Configure scrollbars
        y_scroll.config(command=self.user_tree.yview)
        x_scroll.config(command=self.user_tree.xview)
        
        # Configure columns
        self.user_tree.heading('ID', text='ID')
        self.user_tree.heading('Name', text='Name')
        self.user_tree.heading('Email', text='Email')
        self.user_tree.heading('Status', text='Status')
        self.user_tree.heading('Pause', text='Pause/Activate Account')
        
        # Column widths and alignment
        self.user_tree.column('ID', width=50, anchor="center")
        self.user_tree.column('Name', width=200, anchor="center")
        self.user_tree.column('Email', width=250, anchor="center")
        self.user_tree.column('Status', width=100, anchor="center")
        self.user_tree.column('Pause', width=100, anchor="center")
        
        # Bind checkbox click event
        self.user_tree.bind('<ButtonRelease-1>', self.handle_checkbox_click)
        
        # Dictionary to store checkbox states
        self.checkbox_states = {}        
        # Load initial data
        self.refresh_users()

    def create_statistics_plots(self):
        """display statistics plots in bottom frame"""
        try:
            # Clear any existing plots
            plt.close('all')
            
            # Create a container frame for canvas and scrollbar
            container_frame = ctk.CTkFrame(self.bottom_frame)
            container_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Configure grid to center the content
            container_frame.grid_columnconfigure(0, weight=1)
            container_frame.grid_rowconfigure(0, weight=1)
            
            # Create a figure with two subplots side by side
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
            
            # First histogram: Students per Enrolled Year
            query_by_year = """
                SELECT ENROLLED_YEAR, COUNT(*) as count 
                FROM student_information 
                GROUP BY ENROLLED_YEAR 
                ORDER BY ENROLLED_YEAR
            """
            self.db_handler.cursor.execute(query_by_year)
            year_data = self.db_handler.cursor.fetchall()
            
            years = [str(year[0]) for year in year_data]  # Enrolled Years
            year_counts = [year[1] for year in year_data]  # Number of Students
            
            def get_year_color(count, max_count):
                if count <= max_count * 0.3:  # Low range
                    return '#FF6347'  # Tomato Red
                elif count <= max_count * 0.7:  # Medium range
                    return '#1E90FF'  # Dodger Blue
                else:  # High range
                    return '#32CD32'  # Lime Green

            max_year_count = max(year_counts)
            year_colors = [get_year_color(count, max_year_count) for count in year_counts]
            ax1.barh(years, year_counts, color=year_colors)
            ax1.set_title('Students Enrolled per Year', fontsize=12, fontweight='bold')
            ax1.set_xlabel('Number of Students', fontsize=10)  # X-axis label
            ax1.set_ylabel('Enrolled Year', fontsize=10)  # Y-axis label
            ax1.tick_params(axis='both', labelsize=8)
            
            # Add value labels to the bars
            for i, v in enumerate(year_counts):
                ax1.text(v, i, str(v), va='center', fontsize=8)
                    
            # Second histogram: Students per Year Level
            query_by_level = """
                SELECT YR, COUNT(*) as count 
                FROM student_information 
                GROUP BY YR 
                ORDER BY YR
            """
            self.db_handler.cursor.execute(query_by_level)
            level_data = self.db_handler.cursor.fetchall()
            
            # Function to add ordinal suffix
            def ordinal(n):
                n = int(n)  # Convert to integer
                return "%d%s" % (n, "tsnrhtdd"[((n//10%10!=1)*(n%10<4)*n%10)::4])
            
            # Convert year level to integer before using ordinal function
            levels = [f"{ordinal(level[0])} Year" for level in level_data]
            level_counts = [level[1] for level in level_data]
            
            def get_level_color(count, max_count):
                if count <= max_count * 0.3:  # Low range
                    return '#FF4500'  # Orange Red
                elif count <= max_count * 0.7:  # Medium range
                    return '#32CD32'  # Lime Green
                else:  # High range
                    return '#1E90FF'  # Dodger Blue

            max_level_count = max(level_counts)
            level_colors = [get_level_color(count, max_level_count) for count in level_counts]
            ax2.bar(levels, level_counts, color=level_colors)
            ax2.set_title('Students Enrolled per Year Level', fontsize=12, fontweight='bold')
            ax2.set_xlabel('Year Level', fontsize=10)
            ax2.set_ylabel('Number of Students', fontsize=10)
            ax2.tick_params(axis='both', labelsize=8)
            
            # Add value labels to the bars
            for i, v in enumerate(level_counts):
                ax2.text(i, v, str(v), ha='center', va='bottom', fontsize=8)

            # Adjust layout
            plt.tight_layout(pad=3.0)
            fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.1)
            
            # Create canvas for the plots
            if hasattr(self, 'canvas'):
                self.canvas.get_tk_widget().destroy()
            
            # Create canvas
            self.canvas = FigureCanvasTkAgg(fig, master=container_frame)
            self.canvas.draw()
            
            # Create scrollbars
            v_scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=self.canvas.get_tk_widget().yview)
            h_scrollbar = ttk.Scrollbar(container_frame, orient="horizontal", command=self.canvas.get_tk_widget().xview)
            
            # Configure canvas with scrollbars
            self.canvas.get_tk_widget().configure(
                yscrollcommand=v_scrollbar.set,
                xscrollcommand=h_scrollbar.set
            )

            self.canvas.get_tk_widget().grid(
                row=0, 
                column=0, 
                sticky="nsew", 
                padx=10, 
                pady=10
            )
            v_scrollbar.grid(row=0, column=1, sticky="ns")
            h_scrollbar.grid(row=1, column=0, sticky="ew")
            
            # Configure grid weights
            container_frame.grid_columnconfigure(0, weight=1)
            container_frame.grid_rowconfigure(0, weight=1)
            
            # Update scroll region
            self.canvas.get_tk_widget().update_idletasks()
            self.canvas.get_tk_widget().config(scrollregion=self.canvas.get_tk_widget().bbox("all"))
            
        except Exception as e:
            print(f"Error creating statistics plots: {e}")
            messagebox.showerror("Error", f"Failed to create statistics: {e}")
    def setup_bottom_frame(self):
        """Setup the bottom frame with statistics"""
        # Clear any existing widgets in bottom frame
        for widget in self.bottom_frame.winfo_children():
            widget.destroy()
        
        bottom_title = ctk.CTkLabel(self.bottom_frame,text="Database Status",font=ctk.CTkFont(size=16, weight="bold"))
        bottom_title.pack(pady=(10,5), padx=10, anchor="center")
        
        self.create_statistics_plots()

    def refresh_statistics(self):
        """Refresh the statistics display"""
        self.setup_bottom_frame()

    def refresh_users(self):
        """Refresh the user list display with robust error handling"""
        try:
            # Clear existing items in the treeview
            for item in self.user_tree.get_children():
                self.user_tree.delete(item)
            
            # Execute query to fetch users
            query = "SELECT id, username, email, is_active FROM admin_management"
            self.db_handler.cursor.execute(query)
            users = self.db_handler.cursor.fetchall()
            
            # Process and display users
            for index, user in enumerate(users):
                user_id, username, email, is_active = user
                
                # Determine status and checkbox representation
                checkbox = '☒' if not is_active else '☐'
                status = 'Active' if is_active else 'Paused'
                
                tags = (
                    'evenrow' if index % 2 == 0 else 'oddrow', 
                    status.lower()
                )
                
                # Insert user into treeview
                self.user_tree.insert('', 'end', values=(
                    user_id,    # ID
                    username,   # Username
                    email,      # Email
                    status,     # Status
                    checkbox    # Pause checkbox
                ), tags=tags)
            
            # Configure row and status colors
            self.user_tree.tag_configure('active', foreground='green')
            self.user_tree.tag_configure('paused', foreground='red')
            
        except Exception as e:
            # Comprehensive error handling
            error_message = f"Error fetching users: {e}"
            logging.error(error_message)
            messagebox.showerror("Database Error", error_message)

    def update_user_status(self, user_id, new_status):
        """Update user status in the database
        Args:
            user_id: The ID of the user to update
            new_status: Boolean indicating the new status (True for active, False for paused)
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            self.db_handler.cursor.execute(
                "UPDATE admin_management SET is_active = %s WHERE id = %s",
                (new_status, user_id)
            )
            self.db_handler.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Failed to update user status: {e}")
            self.db_handler.conn.rollback()
            return False

    def handle_checkbox_click(self, event):
        """Handle user status toggle via checkbox click"""
        try:
            # Identify the clicked cell and column
            region = self.user_tree.identify_region(event.x, event.y)
            if region != "cell":
                return
            
            column = self.user_tree.identify_column(event.x)
            if column != '#5':  # Pause checkbox column
                return
            
            # Get the selected row
            selected_items = self.user_tree.selection()
            if not selected_items:
                return
            status_msg = []

            for item in selected_items:
                values = self.user_tree.item(item)['values']
                if not values:
                    continue
            
                user_id = values[0]
                
                # Fetch current user status
                self.db_handler.cursor.execute(
                    "SELECT is_active FROM admin_management WHERE id = %s",
                    (user_id,)
                )
                result = self.db_handler.cursor.fetchone()
                
                if result is None:
                    messagebox.showerror("Error", "User not found in database")
                    return
                
                # Toggle user status
                current_status = result[0]
                new_status = not current_status
                
                # Update user status
                if self.update_user_status(user_id, new_status):
                    self.refresh_users()
                    status_msg = "activated" if new_status else "paused"
                    messagebox.showinfo("Success", f"Account {status_msg} successfully!")
                else:
                    messagebox.showerror("Error", "Failed to update account status")
            # Show all status messages at once
            if status_msg:
                messagebox.showinfo("Status Update", (status_msg))
            
            # Refresh the user list after processing all selected items
            self.refresh_users()

        except Exception as e:
            error_message = f"Failed to update status: {e}"
            logging.error(error_message)
            messagebox.showerror("Error", error_message)
            
            # Rollback transaction if needed
            if hasattr(self.db_handler, 'conn'):
                self.db_handler.conn.rollback()

    # Remove the toggle_user_status method since we're handling it directly in the checkbox click
    def refresh_screen(self):
        """Refresh both the user tree and pending accounts"""
        self.refresh_users()
        self.load_pending_accounts()
    
    def cleanup(self, event=None):
        """Clean up database connections and matplotlib figures when the window is destroyed"""
        try:
            # Clear all matplotlib figures
            plt.close('all')
            
            # Destroy canvas if it exists
            if hasattr(self, 'canvas'):
                self.canvas.get_tk_widget().destroy()
                del self.canvas
            
            # Clean up database connections
            if hasattr(self, 'db_handler'):
                if self.db_handler.cursor:
                    self.db_handler.cursor.close()
                if self.db_handler.conn:
                    self.db_handler.conn.close()
                print("Database connections cleaned up successfully")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            # Only handle cleanup if this widget is being destroyed
            if event and event.widget == self:
                try:
                    # Clear any references
                    self.db_handler = None
                    print("AdminScreen cleanup completed")
                except Exception as e:
                    print(f"Error clearing references: {e}")

    def toggle_user_status(self):
        """Toggle status for selected users"""
        selected_users = [user_id for user_id, is_checked in self.checkbox_states.items() if is_checked]
        
        if not selected_users:
            messagebox.showwarning("Warning", "Please select users to toggle status.")
            return
        
        try:
            for user_id in selected_users:
                # Get current status
                self.db_handler.cursor.execute(
                    "SELECT is_active FROM Admin_management WHERE id = %s",
                    (user_id,)
                )
                current_status = self.db_handler.cursor.fetchone()[0]
                
                # Toggle status
                new_status = not current_status
                self.db_handler.cursor.execute(
                    "UPDATE Admin_management SET is_active = %s WHERE id = %s",
                    (new_status, user_id)
                )
            
            self.db_handler.conn.commit()
            self.checkbox_states.clear()  # Clear selections after update
            self.refresh_users()
            messagebox.showinfo("Success", "User status updated successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update user status: {e}")
            self.db_handler.conn.rollback()
    
    def return_to_home(self):
        """Return to the main menu"""
        self.destroy()  # Remove current admin screen
        self.controller.show_main_menu()  # Show the main menu
    
    def setup_right_frame(self):
        # Title for Account Approvals
        approval_title = ctk.CTkLabel(
            master=self.right_frame,
            text="Account Approvals",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        approval_title.pack(pady=(20, 10))

        # Create scrollable frame for pending accounts
        self.pending_accounts_frame = ctk.CTkScrollableFrame(
            master=self.right_frame,
            width=200,
            height=400
        )
        self.pending_accounts_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Add Approve Selected button
        self.approve_btn = ctk.CTkButton(
            master=self.right_frame,
            text="Approve Selected",
            command=self.approve_selected_accounts,
            width=150
        )
        self.approve_btn.pack(pady=(0, 20))

        # Load pending accounts
        self.load_pending_accounts()

    def load_pending_accounts(self):
        """Load and display pending accounts"""
        # Clear existing widgets
        for widget in self.pending_accounts_frame.winfo_children():
            widget.destroy()

        try:
            # Fetch pending accounts from database
            query = """
            SELECT id, name 
            FROM users 
            WHERE status = 'Inactive' 
            ORDER BY registration_date DESC
            """
            self.db_handler.cursor.execute(query)
            pending_accounts = self.db_handler.cursor.fetchall()

            # Reset approval checkboxes
            self.approval_checkboxes = {}

            # Handle no pending accounts
            if not pending_accounts:
                no_pending_label = ctk.CTkLabel(
                    self.pending_accounts_frame,
                    text="No pending accounts",
                    text_color="gray"
                )
                no_pending_label.pack(pady=10)
                return

            # Create checkboxes for pending accounts
            for user_id, name in pending_accounts:
                checkbox_var = ctk.BooleanVar()
                checkbox = ctk.CTkCheckBox(
                    self.pending_accounts_frame,
                    text=name, 
                    variable=checkbox_var,
                    font=ctk.CTkFont(size=12)
                )
                checkbox.pack(pady=5, padx=10, anchor="w")
                self.approval_checkboxes[user_id] = checkbox_var

        except Exception as e:
            error_message = f"Failed to load pending accounts: {e}"
            logging.error(error_message)
            messagebox.showerror("Error", error_message)
            
    def approve_selected_accounts(self):
        """Approve selected accounts and update their status to 'Active'."""
        approved_count = 0
        cursor = None
        try:
            # Create a new cursor for this operation
            cursor = self.db_handler.conn.cursor(buffered=True)

            for user_id, checkbox_var in self.approval_checkboxes.items():
                if checkbox_var.get():  # If checkbox is checked
                    # Verify the user exists before updating
                    check_query = "SELECT * FROM users WHERE id = %s"
                    cursor.execute(check_query, (user_id,))
                    
                    # Fetch the result to ensure there are no unread results
                    existing_user = cursor.fetchone()
                    
                    if not existing_user:
                        print(f"No user found with ID {user_id}")
                        continue  # Skip to the next user if not found

                    # Proceed with update if user exists
                    update_query = "UPDATE users SET status = 'Active' WHERE id = %s"
                    cursor.execute(update_query, (user_id,))
                    
                    rows_affected = cursor.rowcount
                    if rows_affected > 0:
                        approved_count += 1
                    else:
                        print(f"Failed to update status for user ID {user_id}")

            if approved_count > 0:
                self.db_handler.conn.commit()
                messagebox.showinfo("Success", f"{approved_count} account(s) approved successfully!")
                # Refresh the display
                self.load_pending_accounts()
                self.refresh_users()  # Also refresh the main user list
            else:
                messagebox.showinfo("Info", "No accounts selected for approval")

        except Exception as e:
            print(f"Error approving accounts: {e}")
            self.db_handler.conn.rollback()
            messagebox.showerror("Error", f"Failed to approve accounts: {e}")
        finally:
            if cursor:
                cursor.close()