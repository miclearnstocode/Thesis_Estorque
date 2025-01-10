import pandas as pd 
import functools
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from database import DatabaseHandler
from PIL import Image
import customtkinter as ctk
from sklearn.cluster import AgglomerativeClustering
import numpy as np

class CurriculumScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.raw_data = pd.DataFrame()
        self.db_handler = DatabaseHandler()

        try:
            bg_image = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/Image/student.JPG")
            self.bg_image = ctk.CTkImage(light_image=bg_image,dark_image=bg_image,size=(self.master.winfo_width(), self.master.winfo_height()))
            
            self.bg_label = ctk.CTkLabel(self,image=self.bg_image,text="")
            self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
            
            # Bind resize event after defining the method
            self.bind('<Configure>', lambda event: self.resize_background(event))
            
        except Exception as e:
            print(f"Error loading background image: {e}")
            self.configure(bg="white")  # Use bg instead of fg_color for Frame

        self.create_widgets()

    def resize_background(self, event):
        """Update background image size when window is resized"""
        if hasattr(self, 'bg_image'):
            try:
                new_width = self.winfo_width()
                new_height = self.winfo_height()
                self.bg_image.configure(size=(new_width, new_height))
            except Exception as e:
                print(f"Error resizing background: {e}")

    def create_widgets(self):
        # Button style configuration
        button_style = {
            "fg_color": "transparent",    
            "hover_color": "#707070",     
            "text_color": "black",        
            "height": 32,                 
            "border_width": 1,            
            "border_color": "black"}

        # Additional style for regular buttons
        regular_button_style = {**button_style,"width": 120}

        # Additional style for back button
        back_button_style = {**button_style,"width": 32 }

        ctk.CTkLabel(self,  text="Curriculum", font=("Vivaldi", 40, "bold"), text_color="black", fg_color="transparent",  corner_radius=50, padx=20, pady=10).pack(pady=15)
        # Frame to hold the import buttons and school year selection
        import_frame = ctk.CTkFrame(self, fg_color="transparent")
        import_frame.pack(pady=10)

        # School year selection
        school_years =[f"{year}-{year+1}" for year in range(2020, 2100)]
        self.school_year_label = ctk.CTkLabel(import_frame, text="S.Y. Revision:", text_color="black")
        self.school_year_label.pack(side=tk.LEFT, padx=5)
        
        self.school_year_combo = ctk.CTkOptionMenu(import_frame,  values=school_years, width=120, height=32, fg_color="white", button_color="ghost white", button_hover_color="#707070", dropdown_fg_color="white", dropdown_hover_color="#707070", dropdown_text_color="black", text_color="black")
        self.school_year_combo.pack(side=tk.LEFT, padx=10)
        csv_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/csv_format.png") 
        self.csv_icon = ctk.CTkImage(light_image=csv_icon, dark_image=csv_icon, size=(30, 30))
                # Add buttons
        existing_curriculum_button = ctk.CTkButton(
            import_frame, 
            text="Existing Curriculum", 
            image=self.csv_icon, 
            command=functools.partial(self.load_and_process_file, "Existing Curriculum (CSV)"),
            **regular_button_style
        )
        existing_curriculum_button.pack(side=tk.LEFT, padx=5)

        new_curriculum_button = ctk.CTkButton(
            import_frame, 
            text="New Curriculum", 
            image=self.csv_icon, 
            command=functools.partial(self.load_and_process_file, "New Curriculum (CSV)"),
            **regular_button_style
        )
        new_curriculum_button.pack(side=tk.LEFT, padx=5)

        # Add tooltips
        CTkToolTip(existing_curriculum_button, "Use a CSV file format")
        CTkToolTip(new_curriculum_button, "Use a CSV file format.")

        # Configure Treeview style for row height
        style = ttk.Style()
        style.configure("Treeview", rowheight=35, font=("Helvetica", 12)) 
        style.configure("Treeview.Heading", font=("Helvetica", 12))
        # Modified Treeview columns to include Prerequisite before Grades
        self.tree = ttk.Treeview(self, columns=(
            "Course_No", "Descriptive_Title", "Year_Level", 
            "Units", "Lec", "Lab", "Prerequisite", "Grades", "SY_Revision"
        ), show="headings")
        
        # Set headings
        self.tree.heading("Course_No", text="Course No")
        self.tree.heading("Descriptive_Title", text="Descriptive Title")
        self.tree.heading("Year_Level", text="Year Level")
        self.tree.heading("Units", text="Units")
        self.tree.heading("Lec", text="Lec")
        self.tree.heading("Lab", text="Lab")
        self.tree.heading("Prerequisite", text="Prerequisite")
        self.tree.heading("Grades", text="Grades")
        self.tree.heading("SY_Revision", text="S.Y. Revision")

        # Adjust column widths
        self.tree.column("Course_No", width=50, anchor="center")
        self.tree.column("Descriptive_Title", width=290, anchor="center")
        self.tree.column("Year_Level", width=30, anchor="center")
        self.tree.column("Units", width=25, anchor="center")
        self.tree.column("Lec", width=25, anchor="center")
        self.tree.column("Lab", width=25, anchor="center")
        self.tree.column("Prerequisite", width=100, anchor="center")
        self.tree.column("Grades", width=30, anchor="center")
        self.tree.column("SY_Revision", width=80, anchor="center")

        self.tree.pack(pady=10, fill=tk.BOTH, expand=True)

        # Back and Save button frame
        self.back_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.back_frame.place(x=30, y=108)

        save_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/save.png")
        self.save_icon = ctk.CTkImage(light_image=save_icon, dark_image=save_icon, size=(30, 30))
        self.save_button = ctk.CTkButton(self.back_frame, text="Save Data", image=self.save_icon, command=self.save_data_to_database,state="disabled",**regular_button_style)
        self.save_button.pack(side=tk.RIGHT, padx=10)

        back_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/back.png")
        self.back_icon = ctk.CTkImage(light_image=back_icon, dark_image=back_icon, size=(20, 20))
        ctk.CTkButton(self.back_frame, text="Back", image=self.back_icon, command=self.master.show_main_menu, **back_button_style).pack(side=tk.LEFT, padx=10)


    def load_and_process_file(self, title):
        # Check if a school year is selected
        if self.school_year_combo.get() == "Select S.Y.":
            messagebox.showerror("Error", "Please select a School Year first")
            return

        file_path = filedialog.askopenfilename(title=title, filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                # Read the CSV file
                self.raw_data = pd.read_csv(file_path, na_values=['nan'])
                self.raw_data['Prerequisite'] = self.raw_data['Prerequisite'].fillna('')
                self.raw_data['SY_Revision'] = self.school_year_combo.get()

                # Convert columns to numeric, handling any potential errors
                self.raw_data['Year_Level'] = pd.to_numeric(self.raw_data['Year_Level'], errors='coerce')
                self.raw_data['Units'] = pd.to_numeric(self.raw_data['Units'], errors='coerce')
                self.raw_data['Lec'] = pd.to_numeric(self.raw_data['Lec'], errors='coerce')
                self.raw_data['Lab'] = pd.to_numeric(self.raw_data['Lab'], errors='coerce')

                # Predefined order of year levels
                year_level_order = [
                    1.1, 1.2, 
                    2.1, 2.2, 
                    3.1, 3.2, 
                    4.1, 4.2
                ]

                # Create a categorical column with the predefined order
                self.raw_data['Year_Level_Ordered'] = pd.Categorical(
                    self.raw_data['Year_Level'], 
                    categories=year_level_order, 
                    ordered=True
                )

                # Sort the data using the new categorical column
                grouped_data = self.raw_data.sort_values('Year_Level_Ordered')

                # Clear existing data in the Treeview
                self.tree.delete(*self.tree.get_children())

                # Configure Treeview style
                style = ttk.Style()
                style.configure("Treeview", font=('Helvetica', 13),  rowheight=35)
                style.configure("Treeview.Heading",  font=('Helvetica', 13, 'bold'))

                # Define tags for different row types
                self.tree.tag_configure('oddrow',  background='lightgrey',  font=('Helvetica', 13))
                self.tree.tag_configure('evenrow',  background='white',  font=('Helvetica', 13))
                self.tree.tag_configure('spacer',  background='white',  font=('Helvetica', 13))
                self.tree.tag_configure('total_row',  background='lightblue',   font=('Helvetica', 13, 'bold'))
                self.tree.tag_configure('section_title',   background='#E0E0E0',  font=('Helvetica', 13, 'bold'))

                # Keep track of the last year level to add spacing and totals
                current_year_level = None

                # Function to get semester description
                def get_semester_description(year_level):
                    year = int(year_level)
                    semester = 2 if str(year_level).endswith('.2') else 1
                    year_suffix = 'st' if year == 1 else 'nd' if year == 2 else 'rd' if year == 3 else 'th'
                    semester_suffix = 'st' if semester == 1 else 'nd'
                    return f"{year}{year_suffix} Year, {semester}{semester_suffix} Semester"

                # Insert data into the Treeview with spacing, totals, and section titles
                for index, row in grouped_data.iterrows():
                    # Check if we're starting a new year level group
                    if current_year_level != row['Year_Level']:
                        # If not the first iteration, add total row for previous year level
                        if current_year_level is not None:
                            # Calculate totals for the previous year level
                            year_level_data = grouped_data[grouped_data['Year_Level'] == current_year_level]
                            total_units = year_level_data['Units'].sum()
                            total_lec = year_level_data['Lec'].sum()
                            total_lab = year_level_data['Lab'].sum()

                            # Insert total row
                            self.tree.insert("", "end", values=("",
                                "Total", 
                                "", 
                                total_units, 
                                total_lec, 
                                total_lab, 
                                "", "", ""
                            ), tags=('total_row',))

                            # Add spacing rows
                            for _ in range(2):
                                self.tree.insert("", "end", values=("",)*9, tags=('spacer',))

                        # Insert section title for the new year level
                        semester_description = get_semester_description(row['Year_Level'])
                        self.tree.insert("", "end", values=("",semester_description, "", "", "", "", "", "", ""), tags=('section_title',))

                        # Update current year level
                        current_year_level = row['Year_Level']

                    # Determine row tag
                    tag = 'oddrow' if index % 2 == 0 else 'evenrow'

                    # Insert the actual data row
                    self.tree.insert("", "end", values=(
                        row['Course_No'],
                        row['Descriptive_Title'],
                        row['Year_Level'],
                        row['Units'],
                        row['Lec'],
                        row['Lab'],
                        row['Prerequisite'],
                        row.get('Grades', ''),
                        row['SY_Revision']
                    ), tags=(tag,))

                # Add total row for the last year level
                if current_year_level is not None:
                    year_level_data = grouped_data[grouped_data['Year_Level'] == current_year_level]
                    total_units = year_level_data['Units'].sum()
                    total_lec = year_level_data['Lec'].sum()
                    total_lab = year_level_data['Lab'].sum()

                    # Insert final total row
                    self.tree.insert("", "end", values=( 
                        "Total Units, Lec, Lab Hours", 
                        "", 
                        total_units, 
                        total_lec, 
                        total_lab, 
                        "", "", ""
                    ), tags=('total_row',))

                # Enable the Save button now that the data is loaded
                self.save_button.configure(state="normal")

            except pd.errors.EmptyDataError as e:
                messagebox.showerror("Error", f"Error loading CSV file: {e}. Please check if the file is empty or corrupted.")
            except pd.errors.ParserError as e:
                messagebox.showerror("Error", f"Error parsing CSV file: {e}. Please check the file format and syntax.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
    
    def save_data_to_database(self):
        if not self.raw_data.empty:
            try:
                self.db_handler.saving_curriculum_data(self.raw_data)
                messagebox.showinfo("Success", "Data saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
        else:
            messagebox.showerror("Error", "No data to save")
class CTkToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None

        # Bind hover events
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return

        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # Remove borders
        self.tooltip_window.wm_geometry(f"+{self.widget.winfo_rootx() + 20}+{self.widget.winfo_rooty() + 20}")

        # Add a label to the tooltip
        label = ctk.CTkLabel(self.tooltip_window, text=self.text, fg_color="gray", corner_radius=5, text_color="white")
        label.pack(padx=5, pady=5)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
