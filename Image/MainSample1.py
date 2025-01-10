from pydoc import text
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
from data_processor3 import process_data

# Function to handle navigation button clicks
def on_nav_click(nav_item):
    messagebox.showinfo("Navigation", f"You clicked on {nav_item}")

# Function to change the logo
def change_logo():
    # Choose a logo image
    logo_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
    if logo_path:
        try:
            width = simpledialog.askinteger("Input", "Enter the width of the logo:")
            height = simpledialog.askinteger("Input", "Enter the height of the logo:")
        
            if width and height:
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((width, height), Image.Resampling.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label.config(image=logo_photo)
                logo_label.image = logo_photo  # Keep a reference to avoid garbage collection
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while loading the image: {e}")

# Function to load and process the CSV file
def load_and_process_file():
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if file_path:
        try:
            processed_data = process_data(file_path)
            display_processed_data(processed_data)
            messagebox.showinfo("Success", "Data processed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

# Function to display the processed data in the content frame
# Function to display the processed data in the content frame
def display_processed_data(processed_data):
    # Clear existing widgets in the content frame
    for widget in content_frame.winfo_children():
        widget.destroy()
    # Create a Notebook widget to handle multiple tabs (one for each year level and cluster)
    notebook = ttk.Notebook(content_frame)
    notebook.pack(expand=True, fill='both')
    # Loop through each unique year level and cluster to create tabs and tables
    for year_level in processed_data['Year Level'].unique():
        for cluster_id in processed_data['Cluster'].unique():
            tab_frame = tk.Frame(notebook)
            notebook.add(tab_frame, text=f"Y{year_level} - C{cluster_id}")
            # Create Treeview widget for table
            columns = ('Course No.', 'Descriptive Title', 'Units', 'Lab', 'Lec', 'Grades')
            tree = ttk.Treeview(tab_frame, columns=columns, show='headings')
            tree.pack(side='top', expand=True, fill='both', padx=20, pady=20)  # Center the treeview with padding
            # Define column headings
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, anchor='center')  # Center align column content
            # Insert rows into the Treeview
            for _, row in processed_data[(processed_data['Year Level'] == year_level) & (processed_data['Cluster'] == cluster_id)].iterrows():
                tree.insert('', 'end', values=(row['Course No.'], row['Descriptive Title'], row['Units'], row['Lab'], row['Lec'], row['Grades']))
            # Calculate and display totals
            totals = processed_data[(processed_data['Year Level'] == year_level) & (processed_data['Cluster'] == cluster_id)][['Units', 'Lab', 'Lec']].sum()
            total_row = ('Total', '', totals['Units'], totals['Lab'], totals['Lec'], '')
            tree.insert('', 'end', values=total_row, tags=('total',))
            # Style for total row
            tree.tag_configure('total', font=("Times New Roman", 12))
            # Add a vertical scrollbar
            scrollbar = tk.Scrollbar(tab_frame, orient="vertical", command=tree.yview)
            scrollbar.pack(side='right', fill='y')
            tree.configure(yscrollcommand=scrollbar.set)
            # Add a horizontal scrollbar
            h_scrollbar = tk.Scrollbar(tab_frame, orient="horizontal", command=tree.xview)
            h_scrollbar.pack(side='bottom', fill='x')
            tree.configure(xscrollcommand=h_scrollbar.set)
            # Pack the Treeview in a frame to center it
            table_frame = tk.Frame(tab_frame)
            table_frame.pack(expand=True, fill='both')  # Center the table frame
            tree.pack(expand=True, fill='both')  # Center the treeview

    # Disable editing capabilities
    text.config(state=tk.DISABLED)

# Create the main window
root = tk.Tk()
root.title("Computer Science Department System")
root.geometry("800x600")

# Create a notebook for tabbed navigation
notebook = ttk.Notebook(root)
notebook.pack(side="left", fill="both", expand=True)

# Create tabs
home_tab = tk.Frame(notebook, bg="white")
courses_tab = tk.Frame(notebook, bg="white")
faculty_tab = tk.Frame(notebook, bg="white")
students_tab = tk.Frame(notebook, bg="white")
about_tab = tk.Frame(notebook, bg="white")

notebook.add(home_tab, text="Home")
notebook.add(courses_tab, text="Courses")
notebook.add(faculty_tab, text="Faculty")
notebook.add(students_tab, text="Students")
notebook.add(about_tab, text="About")

# Add content to the Home tab
home_label = tk.Label(home_tab, text="Welcome to the Computer Science Department", font=("Times New Roman", 24), bg="white")
home_label.pack(padx=20, pady=20)

# Add a label for the logo in the Home tab
logo_label = tk.Label(home_tab, bg="white")
logo_label.pack(pady=20)

# Create a frame for displaying processed data in the Courses tab
content_frame = tk.Frame(courses_tab, bg="white")
content_frame.pack(expand=True, fill="both")

# Add Load Data button to the Courses tab
load_data_button = tk.Button(courses_tab, text="Load Data", command=load_and_process_file, bg="#3498db", fg="white", font=("Times New Roman", 12), relief="flat")
load_data_button.pack(pady=20)

# Create a menu bar
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# Add a "Settings" menu with the option to change the logo
settings_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Settings", menu=settings_menu)
settings_menu.add_command(label="Change Logo", command=change_logo)

# Run the Tkinter main loop
root.mainloop()
