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
            # Use safe methods that return default values if no data
            year_counts = self.get_safe_year_counts(db)
            level_counts = self.get_safe_level_counts(db)
            
            stats_data = {
                'year_counts': year_counts,
                'level_counts': level_counts
            }
            db.close_db_connection()
            return stats_data
        except Exception as e:
            raise Exception(f"Statistics refresh failed: {e}")
    
    def get_safe_year_counts(self, db):
        """Safely get year counts with default values"""
        try:
            query_by_year = """
                SELECT ENROLLED_YEAR, COUNT(*) as count 
                FROM student_information 
                GROUP BY ENROLLED_YEAR 
                ORDER BY ENROLLED_YEAR
            """
            db.cursor.execute(query_by_year)
            year_data = db.cursor.fetchall()
            
            if not year_data:
                return {'No Data': 0}
            
            return {str(year[0]): year[1] for year in year_data}
        except Exception as e:
            logging.warning(f"Error fetching year counts: {e}")
            return {'No Data': 0}
    
    def get_safe_level_counts(self, db):
        """Safely get level counts with default values"""
        try:
            query_by_level = """
                SELECT YR, COUNT(*) as count 
                FROM student_information 
                GROUP BY YR 
                ORDER BY YR
            """
            db.cursor.execute(query_by_level)
            level_data = db.cursor.fetchall()
            
            if not level_data:
                return {'No Data': 0}
            
            def ordinal(n):
                n = int(n) if n else 0
                return "%d%s" % (n, "tsnrhtdd"[((n//10%10!=1)*(n%10<4)*n%10)::4])
            
            return {f"{ordinal(level[0])} Year": level[1] for level in level_data}
        except Exception as e:
            logging.warning(f"Error fetching level counts: {e}")
            return {'No Data': 0}
    
    def update_user_table(self, user_data):
        """Update user management table with new data"""
        # Clear existing table
        for item in self.user_table.get_children():
            self.user_table.delete(item)
        
        # Insert new data or show "No Data" message
        if not user_data:
            self.user_table.insert('', 'end', values=('No Data', 'No Data', 'No Data', 'No Data', 'No Data'))
        else:
            for user in user_data:
                self.user_table.insert('', 'end', values=user)
    
    def update_statistics_plots(self, stats_data):
        """Update statistics plots with new data"""
        try:
            # Clear existing plots
            for ax in self.axes:
                ax.clear()
            
            # Check if we have actual data
            year_counts = stats_data['year_counts']
            level_counts = stats_data['level_counts']
            
            # Create default data if no real data exists
            if not year_counts or list(year_counts.keys()) == ['No Data']:
                year_counts = {'No Data Available': 1}
            
            if not level_counts or list(level_counts.keys()) == ['No Data']:
                level_counts = {'No Data Available': 1}
            
            years = list(year_counts.keys())
            year_counts_list = list(year_counts.values())
            levels = list(level_counts.keys())
            level_counts_list = list(level_counts.values())
            
            # Function to get color for bars
            def get_color(count, max_count):
                if max_count == 0:  # Handle case where all counts are zero
                    return '#808080'  # Gray for no data
                if count <= max_count * 0.3:
                    return '#FF6347'  # Tomato Red
                elif count <= max_count * 0.7:
                    return '#1E90FF'  # Dodger Blue
                else:
                    return '#32CD32'  # Lime Green
            
            # First plot (Students per Enrolled Year)
            max_year_count = max(year_counts_list) if year_counts_list else 1
            year_colors = [get_color(count, max_year_count) for count in year_counts_list]
            self.axes[0].barh(years, year_counts_list, color=year_colors)
            self.axes[0].set_title('Students per Enrolled Year')
            
            # Add value labels to the bars
            for i, v in enumerate(year_counts_list):
                self.axes[0].text(v, i, str(v), va='center', fontsize=8)
            
            # Second plot (Students per Year Level)
            max_level_count = max(level_counts_list) if level_counts_list else 1
            level_colors = [get_color(count, max_level_count) for count in level_counts_list]
            self.axes[1].bar(levels, level_counts_list, color=level_colors)
            self.axes[1].set_title('Students per Year Level')
            
            # Add value labels to the bars
            for i, v in enumerate(level_counts_list):
                self.axes[1].text(i, v, str(v), ha='center', va='bottom', fontsize=8)
            
            # Adjust layout for better appearance
            plt.tight_layout()
            
            # Refresh the canvas to show updated plots
            self.canvas.draw()
            
        except Exception as e:
            logging.error(f"Error updating statistics plots: {e}")
            # Create a simple error plot
            for ax in self.axes:
                ax.clear()
                ax.text(0.5, 0.5, 'Error Loading Data\n' + str(e), 
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Data Load Error')
            self.canvas.draw()
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.db_handler = DatabaseHandler()
        
        # Initialize axes list
        self.axes = []
        
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
        button_style = {"fg_color": "transparent", "hover_color": "#707070", "text_color": "black", "height": 32, "border_width": 1, "border_color": "black"}
        
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
        self.refresh_btn = ctk.CTkButton(button_container, text="Refresh", command=self.enhanced_refresh, width=150,**button_style)
        self.refresh_btn.pack(pady=5)
        
        # Center Frame (for Treeview)
        self.center_frame = ctk.CTkFrame(self.main_container)
        self.center_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Right Frame
        self.right_frame = ctk.CTkFrame(self.main_container, fg_color="#F0F0F0")
        self.right_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        
        # User icon and title
        try:
            user_icon = Image.open(LoginForm.resource_path("icons/user.png"))
            self.user_icon = ctk.CTkImage(light_image=user_icon, dark_image=user_icon, size=(30, 30))
            title_label = ctk.CTkLabel(self.center_frame, text="User Account Management",image=self.user_icon,
                font=ctk.CTkFont("Helvetica", size=20, weight="bold"), text_color='grey50')
        except Exception as e:
            print(f"Failed to load user icon: {e}")
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
        self.center_frame.configure(height=200)
        self.right_frame.configure(height=200)
        
        # Prevent automatic resizing
        self.center_frame.grid_propagate(False)
        self.right_frame.grid_propagate(False)
        self.bottom_frame.grid_propagate(False)
        
        # Setup the interface
        self.setup_treeview(tree_frame)
        self.setup_bottom_frame()
        
        # Load initial data
        self.refresh_users()

    def setup_treeview(self, tree_frame):
        """Setup the treeview with scrollbars and styling"""
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
        style.map('Treeview', background=[('selected', '#0078D7')])
        style.configure('Treeview', background='white',fieldbackground='white', selectbackground='#0078D7')

        # Create Treeview
        self.user_tree = ttk.Treeview(tree_frame,columns=('ID', 'Name', 'Email', 'Status', 'Pause'),
            show='headings', yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set, height=20,style="Treeview")
        self.user_tree.grid(row=0, column=0, sticky="nsew")
        
        # Add tag configuration for alternating rows
        self.user_tree.tag_configure('oddrow', background='#F5F5F5')
        self.user_tree.tag_configure('evenrow', background='white')
        self.user_tree.tag_configure('nodata', background='#FFE4E1', foreground='red')  # Light red for no data
        
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

    def create_statistics_plots(self):
        """Display statistics plots in bottom frame with error handling"""
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
            self.axes = [ax1, ax2]  # Store axes for later updates
            
            # Get data safely
            year_counts = self.get_safe_year_counts(self.db_handler)
            level_counts = self.get_safe_level_counts(self.db_handler)
            
            # Check if we have actual data
            if not year_counts or list(year_counts.keys()) == ['No Data']:
                year_counts = {'No Data Available': 1}
            
            if not level_counts or list(level_counts.keys()) == ['No Data']:
                level_counts = {'No Data Available': 1}
            
            years = list(year_counts.keys())
            year_counts_list = list(year_counts.values())
            levels = list(level_counts.keys())
            level_counts_list = list(level_counts.values())
            
            # Function to get color for bars
            def get_color(count, max_count):
                if max_count == 0:  # Handle case where all counts are zero
                    return '#808080'  # Gray for no data
                if count <= max_count * 0.3:
                    return '#FF6347'  # Tomato Red
                elif count <= max_count * 0.7:
                    return '#1E90FF'  # Dodger Blue
                else:
                    return '#32CD32'  # Lime Green

            # First histogram: Students per Enrolled Year
            max_year_count = max(year_counts_list) if year_counts_list else 1
            year_colors = [get_color(count, max_year_count) for count in year_counts_list]
            ax1.barh(years, year_counts_list, color=year_colors)
            ax1.set_title('Students Enrolled per Year', fontsize=12, fontweight='bold')
            ax1.set_xlabel('Number of Students', fontsize=10)
            ax1.set_ylabel('Enrolled Year', fontsize=10)
            ax1.tick_params(axis='both', labelsize=8)
            
            # Add value labels to the bars
            for i, v in enumerate(year_counts_list):
                ax1.text(v, i, str(v), va='center', fontsize=8)
                    
            # Second histogram: Students per Year Level
            max_level_count = max(level_counts_list) if level_counts_list else 1
            level_colors = [get_color(count, max_level_count) for count in level_counts_list]
            ax2.bar(levels, level_counts_list, color=level_colors)
            ax2.set_title('Students Enrolled per Year Level', fontsize=12, fontweight='bold')
            ax2.set_xlabel('Year Level', fontsize=10)
            ax2.set_ylabel('Number of Students', fontsize=10)
            ax2.tick_params(axis='both', labelsize=8)
            
            # Add value labels to the bars
            for i, v in enumerate(level_counts_list):
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
            self.canvas.get_tk_widget().configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

            self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
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
            # Create error display
            error_label = ctk.CTkLabel(self.bottom_frame, 
                                     text=f"Error loading statistics: {str(e)}", 
                                     text_color="red",
                                     font=ctk.CTkFont(size=12))
            error_label.pack(expand=True, fill="both", padx=20, pady=20)

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
            
            # Check if we have users
            if not users:
                # Insert "No Data" row
                self.user_tree.insert('', 'end', values=(
                    'No Data', 'No Data Available', 'No Data Available', 'No Data', 'No Data'
                ), tags=('nodata',))
                return
            
            # Process and display users
            for index, user in enumerate(users):
                user_id, username, email, is_active = user
                
                # Determine status and checkbox representation
                checkbox = '☒' if not is_active else '☐'
                status = 'Active' if is_active else 'Paused'
                
                tags = ('evenrow' if index % 2 == 0 else 'oddrow', status.lower())
                
                # Insert user into treeview
                self.user_tree.insert('', 'end', values=(user_id, username, email, status, checkbox), tags=tags)
            
            # Configure row and status colors
            self.user_tree.tag_configure('active', foreground='green')
            self.user_tree.tag_configure('paused', foreground='red')
            
        except Exception as e:
            # Comprehensive error handling
            error_message = f"Error fetching users: {e}"
            logging.error(error_message)
            # Insert error row
            self.user_tree.insert('', 'end', values=(
                'Error', 'Error Loading Data', str(e), 'Error', 'Error'
            ), tags=('nodata',))

    def update_user_status(self, user_id, new_status):
        """Update user status in the database"""
        try:
            self.db_handler.cursor.execute("UPDATE admin_management SET is_active = %s WHERE id = %s",(new_status, user_id))
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
            
            item = selected_items[0]
            values = self.user_tree.item(item)['values']
            
            # Check if this is a "No Data" row
            if values and values[0] in ['No Data', 'Error']:
                messagebox.showinfo("Info", "No user data available to modify.")
                return
            
            if not values:
                return
            
            user_id = values[0]
            
            # Fetch current user status
            self.db_handler.cursor.execute("SELECT is_active FROM admin_management WHERE id = %s",(user_id,))
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

        except Exception as e:
            error_message = f"Failed to update status: {e}"
            logging.error(error_message)
            messagebox.showerror("Error", error_message)
            
            # Rollback transaction if needed
            if hasattr(self.db_handler, 'conn'):
                self.db_handler.conn.rollback()

    def refresh_screen(self):
        """Refresh both the user tree and pending accounts"""
        self.refresh_users()
        if hasattr(self, 'load_pending_accounts'):
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
                self.db_handler.cursor.execute("SELECT is_active FROM admin_management WHERE id = %s", (user_id,))
                current_status = self.db_handler.cursor.fetchone()[0]
                
                # Toggle status
                new_status = not current_status
                self.db_handler.cursor.execute("UPDATE admin_management SET is_active = %s WHERE id = %s", (new_status, user_id))
            
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
        approval_title = ctk.CTkLabel(master=self.right_frame, text="Account Approvals", font=ctk.CTkFont(size=16, weight="bold"))
        approval_title.pack(pady=(20, 10))

        # Create scrollable frame for pending accounts
        self.pending_accounts_frame = ctk.CTkScrollableFrame(master=self.right_frame, width=200, height=400)
        self.pending_accounts_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Add Approve Selected button
        self.approve_btn = ctk.CTkButton(master=self.right_frame, text="Approve Selected", command=self.approve_selected_accounts, width=150)
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
                no_pending_label = ctk.CTkLabel(self.pending_accounts_frame, text="No pending accounts", text_color="gray")
                no_pending_label.pack(pady=10)
                return

            # Create checkboxes for pending accounts
            for user_id, name in pending_accounts:
                checkbox_var = ctk.BooleanVar()
                checkbox = ctk.CTkCheckBox(self.pending_accounts_frame, text=name, variable=checkbox_var, font=ctk.CTkFont(size=12))
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