import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import pandas as pd
from fuzzywuzzy import fuzz, process
from database import DatabaseHandler
from PIL import Image
import re 

class AppraisalScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.data_appraised = False
        self.matched_subjects = None 
        self.basic_info_entered = False
        
        # Set default colors
        self.button_color = "transparent"
        self.hover_color = "gray70"
        
        try:
            self.dept_bg = Image.open("Image/Gradient.jpg")
            self.bg_image_pil = self.dept_bg  
            
            # Create initial CTkImage with frame's size
            initial_width = self.winfo_width() or 736 
            initial_height = self.winfo_height() or 600  
            self.bg_image = ctk.CTkImage( light_image=self.bg_image_pil, dark_image=self.bg_image_pil, size=(initial_width, initial_height))

            self.bg_label = ctk.CTkLabel(self, image=self.bg_image, text="")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Bind resize event
            self.bind('<Configure>', self.resize_background)
            
        except Exception as e:
            print(f"Error loading background image: {e}")
        
        # Buttons with updated style
        button_style = { "fg_color": self.button_color, "hover_color": self.hover_color, "text_color": "black", "corner_radius": 10 }
        
        # Main title label
        self.label = ctk.CTkLabel(self, text="  Appraisal   ", font=("Vivaldi", 40), fg_color="grey70", text_color="black", corner_radius=50)
        self.label.grid(row=0, column=0, pady=30, columnspan=2)

        # Keep original notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, padx=10, pady=10, sticky="nsew", columnspan=2)

        # Frames
        self.frame1 = ctk.CTkFrame(self.notebook, fg_color="transparent", width=800)
        self.frame1.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.notebook.add(self.frame1, text="Basic Information")

        # Basic Information Frame
        self.basic_info_frame = ctk.CTkFrame(self.frame1, fg_color=("gainsboro", "grey79"), corner_radius=10, border_color="#FFFFFF",height=500)
        self.basic_info_frame.place(x=360, y=90)

        # Convert labels and entries to CTk widgets
        self.year_label = ctk.CTkLabel(self.basic_info_frame, text="Select Year:")
        self.year_label.grid(row=0, column=0, pady=5)
        self.year_var = ctk.StringVar()
        self.year_dropdown = ctk.CTkComboBox(self.basic_info_frame, values=[str(year) for year in range(2023, 2100)], variable=self.year_var, state="readonly")
        self.year_dropdown.grid(row=0, column=1)

        self.semester_label = ctk.CTkLabel(self.basic_info_frame, text="    Select Semester:")
        self.semester_label.grid(row=1, column=0, pady=5)
        self.semester_var = ctk.StringVar()
        self.semester_dropdown = ctk.CTkComboBox(self.basic_info_frame, values=["1st Semester", "2nd Semester"], variable=self.semester_var, state="readonly")
        self.semester_dropdown.grid(row=1, column=1)

        self.generate_button = ctk.CTkButton(self.basic_info_frame, text="Generate Appraised ID", command=self.generate_appraised_id, fg_color=self.button_color, hover_color=self.hover_color, text_color="black", corner_radius=10, border_color="grey70", border_width=1)
        self.generate_button.grid(row=2, column=0, columnspan=2, pady=5)

        self.appraised_id_label = ctk.CTkLabel(self.basic_info_frame, text="")
        self.appraised_id_label.grid(row=3, column=0, columnspan=2)

        # Replace the original entries creation with this call
        self.create_entries()
        right_icon = Image.open("icons/right.png")
        self.right_icon = ctk.CTkImage(light_image=right_icon, dark_image=right_icon, size=(20, 20))
        self.next_button = ctk.CTkButton(self.basic_info_frame, text="", image=self.right_icon, command=self.check_basic_info, width=50, **button_style, border_color="grey70", border_width=1)
        self.next_button.grid(row=13, column=1, pady=10)

        # Bind Enter key to the next button
        self.bind('<Return>', lambda e: self.check_basic_info())

        # Configure Treeview style
        style = ttk.Style()
        style.configure("Treeview", rowheight=35, font=("Helvetica", 12)) 
        style.configure("Treeview.Heading", font=("Helvetica", 12))
        
        # Keep original Treeview frames
        self.frame2 = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.frame2, text="Matched Subjects")

        self.tree1 = ttk.Treeview(self.frame2, columns=("Course_No", "Descriptive_Title", "Year_Level", "Units", "Lec", "Lab", "Prerequisite", "Grades"),show="headings", height=20)
        self.tree1.grid(row=0, column=0, sticky="nsew")

        self.tree1.heading("Course_No", text="Course No")
        self.tree1.heading("Descriptive_Title", text="Descriptive Title")
        self.tree1.heading("Year_Level", text="Year Level")
        self.tree1.heading("Units", text="Units")
        self.tree1.heading("Lec", text="Lec")
        self.tree1.heading("Lab", text="Lab")
        self.tree1.heading("Prerequisite", text="Prerequisite")
        self.tree1.heading("Grades", text="Grades")

        self.tree1.column("Course_No", width=50, anchor='center')
        self.tree1.column("Descriptive_Title", width=290, anchor='center')
        self.tree1.column("Year_Level", width=40, anchor='center')
        self.tree1.column("Units", width=25, anchor='center')
        self.tree1.column("Lec", width=25, anchor='center')
        self.tree1.column("Lab", width=25, anchor='center')
        self.tree1.column("Prerequisite", width=100, anchor='center')
        self.tree1.column("Grades", width=30, anchor='center')

        self.tree1.tag_configure('oddrow', background='lightgrey')
        self.tree1.tag_configure('evenrow', background='white')
        
        self.frame3 = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.frame3, text="Subject To Enroll")

        self.tree2 = ttk.Treeview(self.frame3, columns=("Course_No", "Descriptive_Title", "Year_Level", "Units", "Lec", "Lab", "Prerequisite","Grades"),show="headings", height=15)
        self.tree2.grid(row=0, column=0, sticky="nsew")

        self.tree2.heading("Course_No", text="Course No")
        self.tree2.heading("Descriptive_Title", text="Descriptive Title")
        self.tree2.heading("Year_Level", text="Year Level")
        self.tree2.heading("Units", text="Units")
        self.tree2.heading("Lec", text="Lec")
        self.tree2.heading("Lab", text="Lab")
        self.tree2.heading("Prerequisite", text="Prerequisite")
        self.tree2.heading("Grades", text="Grades")

        self.tree2.column("Course_No", width=50, anchor='center')
        self.tree2.column("Descriptive_Title", width=290, anchor='center')
        self.tree2.column("Year_Level", width=40, anchor='center')
        self.tree2.column("Units", width=25, anchor='center')
        self.tree2.column("Lec", width=25, anchor='center')
        self.tree2.column("Lab", width=25, anchor='center')
        self.tree2.column("Prerequisite", width=100, anchor='center')
        self.tree2.column("Grades", width=30, anchor='center')

        self.tree2.tag_configure('oddrow', background='lightgrey')
        self.tree2.tag_configure('evenrow', background='white')

        # Button frames
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.place(x=150, y=78)

        self.back_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=10)
        self.back_frame.place(x=5, y=86)

        appraise_icon = Image.open("icons/appraisal.png")
        self.appraise_icon = ctk.CTkImage(light_image=appraise_icon, dark_image=appraise_icon, size=(30, 30))
        self.appraise_button = ctk.CTkButton(button_frame, text="Appraise", image=self.appraise_icon, command=self.start_appraisal, **button_style, border_color="grey70", border_width=1)
        self.appraise_button.grid(row=0, column=0)
        save_icon = Image.open("icons/save.png")
        self.save_icon = ctk.CTkImage(light_image=save_icon, dark_image=save_icon, size=(30, 30))
        self.save_button = ctk.CTkButton(button_frame, text="Save", image=self.save_icon, command=self.save_to_database, state="disabled", **button_style, border_color="grey70", border_width=1)
        self.save_button.grid(row=0, column=1)

        self.note_label = ctk.CTkLabel(button_frame, text="NOTE: Please select student curriculum first, then existing curriculum when appraising", font=("Helvetica", 12, 'italic'), fg_color="transparent")
        self.note_label.grid(row=0, column=2, padx=10)

        back_icon = Image.open("icons/back.png")
        self.back_icon = ctk.CTkImage(light_image=back_icon, dark_image=back_icon, size=(20, 20))
        back_button = ctk.CTkButton(self.back_frame, text="Back", image=self.back_icon ,command=self.master.show_main_menu, border_color="grey70", border_width=1, **button_style)
        back_button.grid(row=1, column=1, padx=0.5)

        # Configure grid weights to allow proper expansion
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.frame2.grid_rowconfigure(0, weight=1)
        self.frame2.grid_columnconfigure(0, weight=1)
        self.frame3.grid_rowconfigure(0, weight=1)
        self.frame3.grid_columnconfigure(0, weight=1)

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        return file_path

    def process_data(self, old_file_path, new_file_path):
        try:
            df_old = pd.read_csv(old_file_path)
            df_new = pd.read_csv(new_file_path)

            # Clean Descriptive_Title columns
            df_old['Descriptive_Title'] = df_old['Descriptive_Title'].astype(str).str.strip()
            df_new['Descriptive_Title'] = df_new['Descriptive_Title'].astype(str).str.strip()

            # Clean column names
            df_old.columns = [col.strip() for col in df_old.columns]
            df_new.columns = [col.strip() for col in df_new.columns]

            # Check if 'Descriptive_Title' exists in both dataframes
            if 'Descriptive_Title' not in df_old.columns or 'Descriptive_Title' not in df_new.columns:
                messagebox.showerror("Error", "'Descriptive_Title' column is missing in one of the files.")
                return

            # Filter old curriculum to keep only rows where 'Grades' are not NaN like if the course no is credited or not
            filtered_old = df_old[df_old['Grades'].notna()]

            # Initialize a dictionary to store matched Descriptive_Titles and their corresponding grades
            matched_grades = {}

            # Perform fuzzy matching for each Descriptive_Title in the old curriculum
            for index, row in filtered_old.iterrows():
                old_title = row['Descriptive_Title']
                # Using token_sort_ratio to allow for matching even if word order changes
                match_result = process.extractOne(old_title, df_new['Descriptive_Title'], scorer=fuzz.token_sort_ratio)

                if match_result:
                    new_title, score, _ = match_result
                    # Adjust the threshold score based on your matching requirements
                    if score >= 80:  # Adjust the threshold score as needed
                        matched_grades[new_title] = row['Grades']

            # Update grades in the new curriculum DataFrame based on matched titles
            df_new['Grades'] = df_new['Descriptive_Title'].map(matched_grades)

            # Drop rows without valid 'Descriptive_Title' if necessary
            matched_subjects = df_new.dropna(subset=['Descriptive_Title'])

            # Sort the data by year (assuming you have a 'Year_Level' or equivalent column)
            if 'Year_Level' in matched_subjects.columns:
                matched_subjects = matched_subjects.sort_values(by=['Year_Level', 'Descriptive_Title'])

            return matched_subjects
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process data: {e}")
            return None

    def display_data(self, matched_subjects):
        # Clear existing data in the Treeview
        for child in self.tree1.get_children():
            self.tree1.delete(child)

        # Ensure required columns exist
        required_columns = ['Course_No', 'Descriptive_Title', 'Year_Level', 'Units', 'Lec', 'Lab', 'Prerequisite', 'Grades']
        for col in required_columns:
            if col not in matched_subjects.columns:
                print(f"Warning: Column {col} is missing")
                matched_subjects[col] = ''

        # Predefined order of year levels and semesters
        year_levels = ['1.1', '1.2', '2.1', '2.2', '3.1', '3.2', '4.1', '4.2']

        # Track overall total units, lec, and lab
        overall_total_units = 0
        overall_total_lec = 0
        overall_total_lab = 0

        # Iterate through predefined year levels and semesters
        for year_sem in year_levels:
            # Filter subjects for this specific year and semester
            group = matched_subjects[matched_subjects['Year_Level'].astype(str) == year_sem]
            
            # Skip if no subjects for this year and semester
            if group.empty:
                continue

            # Extract year and semester for title
            year, semester = map(int, year_sem.split('.'))

            # Insert title row for the year and semester
            title = f"{self.get_semester_title(year, semester)}"
            self.tree1.insert("", "end", values=["",title, "", "", "", "", "", "", ""], tags=('title_row',))
            
            # Track totals for this year level
            year_total_units = 0
            year_total_lec = 0
            year_total_lab = 0

            # Insert subjects for this year and semester
            row_index = 0
            for index, row in group.iterrows():
                # Prepare values for the treeview
                values = [
                    row.get('Course_No', ''),
                    row.get('Descriptive_Title', ''),
                    row.get('Year_Level', ''),
                    row.get('Units', ''),
                    row.get('Lec', ''),
                    row.get('Lab', ''),
                    row.get('Prerequisite', ''),
                    row.get('Grades', '')
                ]
                
                    # Determine the tag for the row based on the explicit counter
                tag = 'oddrow' if row_index % 2 == 0 else 'evenrow'
                row_index += 1
                # Insert row into treeview with the appropriate tag
                self.tree1.insert("", "end", values=values, tags=(tag,))

                # Update totals
                year_total_units += float(row.get('Units', 0))
                year_total_lec += float(row.get('Lec', 0))
                year_total_lab += float(row.get('Lab', 0))

            # Insert year level total row
            year_total_values = ["","Total", "", 
                f"{int(round(year_total_units))}", 
                f"{int(round(year_total_lec))}", 
                f"{int(round(year_total_lab))}",  "",  ""]
            self.tree1.insert("", "end", values=year_total_values, tags=('year_total_row',), )

            # Update overall totals
            overall_total_units += year_total_units
            overall_total_lec += year_total_lec
            overall_total_lab += year_total_lab

            # Insert a blank row for spacing
            self.tree1.insert("", "end", values=["", "", "", "", "", "", "", ""])

        # Add overall total row
        overall_total_values = ["",
            "Overall Total", 
            "",
            f"{int(round(overall_total_units))}", 
            f"{int(round(overall_total_lec))}", 
            f"{int(round(overall_total_lab))}", 
            "", 
            ""
        ]
        self.tree1.insert("", "end", values=overall_total_values, tags=('overall_total_row',))

        # If no data was inserted, show a message
        if len(self.tree1.get_children()) <= 1:  # 1 for overall total row
            messagebox.showinfo("No Data", "No subjects found for the selected curriculum.")
        # Configure row styles with corrected colors
        self.tree1.tag_configure('oddrow', background='#E5E5E5', font=('Helvetica', 12))  # Light gray for odd rows
        self.tree1.tag_configure('evenrow', background='#FFFFFF', font=('Helvetica', 12))  # White for even rows
        self.tree1.tag_configure('year_total_row', background='#E6FFE6', font=('Helvetica', 12, 'bold'))  # Light green for totals
        self.tree1.tag_configure('title_row', background='#E6E6FF', font=('Helvetica', 12, 'bold'))  # Light blue for titles


    def get_semester_title(self, year, semester):
        year_titles = {
            1: 'First Year',
            2: 'Second Year',
            3: 'Third Year',
            4: 'Fourth Year'}
        
        semester_titles = {
            1: 'First Semester',
            2: 'Second Semester'}
        
        return f"{year_titles.get(year, 'Unknown Year')} - {semester_titles.get(semester, 'Unknown Semester')}"
        
    def display_rows_grades(self, matched_subjects):
        # Clear existing data in the Treeview
        for child in self.tree2.get_children():
            self.tree2.delete(child)

        # Configure treeview font and style
        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', 13), rowheight=35)
        style.configure("Treeview.Heading", font=('Helvetica', 13, 'bold'))

        # Filter rows with no grades
        rows_needing_grades = matched_subjects[matched_subjects['Grades'].isna()]

        # Initialize totals for different levels
        overall_totals = {'Units': 0, 'Lec': 0, 'Lab': 0}

        # Configure row tags
        self.tree2.tag_configure('oddrow', background='#E5E5E5', font=('Helvetica', 13))
        self.tree2.tag_configure('evenrow', background='#FFFFFF', font=('Helvetica', 13))
        self.tree2.tag_configure('title_row', background='#E6E6FF', font=('Helvetica', 13, 'bold'))
        self.tree2.tag_configure('total_row', background='#E6FFE6', font=('Helvetica', 13, 'bold'))

        # Initialize storage for year-level totals
        year_level_totals = {str(i): {'Units': 0, 'Lec': 0, 'Lab': 0} for i in range(1, 5)}

        # Group data by year levels
        grouped_by_year = rows_needing_grades.groupby(rows_needing_grades['Year_Level'].astype(str).str.split('.').str[0])

        for year, year_group in grouped_by_year:

            # Iterate through each semester of this year
            for semester in ['1', '2']:
                year_sem = f"{year}.{semester}"
                semester_group = year_group[year_group['Year_Level'].astype(str) == year_sem]

                # Skip if no subjects for this semester
                if semester_group.empty:
                    continue

                # Insert Semester Title Row
                semester_title = f"{self.get_semester_title(int(year), int(semester))}"
                self.tree2.insert("", "end", values=["", semester_title, "", "", "", "", "", "", ""], tags=('title_row',))

                # Initialize semester totals
                semester_totals = {'Units': 0, 'Lec': 0, 'Lab': 0}

                # Insert rows for this semester
                for idx, (_, row) in enumerate(semester_group.iterrows()):
                    # Determine row tag
                    tag = 'oddrow' if idx % 2 == 0 else 'evenrow'

                    # Prepare values for insertion
                    values = [row.get(col, "") if pd.notna(row.get(col, "")) else "" for col in self.tree2["columns"]]

                    # Insert row
                    self.tree2.insert("", "end", values=values, tags=(tag,))
                    def safe_convert(value, default=0):
                        """
                        Safely converts a value to a float or int. If the conversion fails,
                        the default value is returned.
                        """
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            return default

                    # Update totals
                    units = safe_convert(row.get('Units', 0))
                    lec = safe_convert(row.get('Lec', 0))
                    lab = safe_convert(row.get('Lab', 0))

                    semester_totals['Units'] += units
                    semester_totals['Lec'] += lec
                    semester_totals['Lab'] += lab

                    year_level_totals[year]['Units'] += units
                    year_level_totals[year]['Lec'] += lec
                    year_level_totals[year]['Lab'] += lab

                    overall_totals['Units'] += units
                    overall_totals['Lec'] += lec
                    overall_totals['Lab'] += lab

                # Insert Semester Total Row
                semester_total_values = [
                    "", "Total", "",
                    f"{int(semester_totals['Units'])}",
                    f"{int(semester_totals['Lec'])}",
                    f"{int(semester_totals['Lab'])}"
                ] + [""] * (len(self.tree2["columns"]) - 4)
                self.tree2.insert("", "end", values=semester_total_values, tags=('total_row',))

                self.tree2.insert("", "end", values=[""] * len(self.tree2["columns"]))


        # Insert Overall Totals
        overall_total_values = [
            "", "Overall Totals",
            f"{int(overall_totals['Units'])}",
            f"{int(overall_totals['Lec'])}",
            f"{int(overall_totals['Lab'])}"
        ] + [""] * (len(self.tree2["columns"]) - 4)
        self.tree2.insert("", "end", values=overall_total_values, tags=('total_row',))

        # Handle empty data scenario
        if len(self.tree2.get_children()) <= 1:
            messagebox.showinfo("No Data", "No subjects found for the selected curriculum.")

    def generate_appraised_id(self):
        self.selected_year = self.year_var.get()
        selected_semester = self.semester_var.get()

        if self.selected_year and selected_semester:
            appraised_id = f"{self.selected_year}-{selected_semester}"
            self.appraised_id_label.configure(text=appraised_id)
            return True
        return False

    def check_basic_info(self):
            if (self.entries["ID No:"].get() and self.entries["Last Name:"].get() and
                self.entries["First Name:"].get() and self.entries["Middle Name:"].get() and
                self.entries["Year Level:"].get() and self.entries["Sex:"].get() and 
                self.entries["Age:"].get() and self.entries["Email Address:"].get()):
                if self.generate_appraised_id():
                    self.basic_info_entered = True
                    self.notebook.select(self.frame2)
                    return (
                        self.appraised_id_label.cget("text"),
                        self.entries["ID No:"].get(),
                        self.entries["Last Name:"].get(),
                        self.entries["First Name:"].get(),
                        self.entries["Middle Name:"].get(),
                        self.entries["Year Level:"].get(),
                        self.entries["Sex:"].get(),
                        self.entries["Age:"].get(),
                        self.entries["Email Address:"].get()
                    )
                else:
                    messagebox.showwarning("Warning", "Please complete the Appraised ID first.")
            else:
                messagebox.showwarning("Warning", "Please enter all basic information.")
    
    def start_appraisal(self):
        if self.basic_info_entered:
            old_file_path = self.select_file()
            new_file_path = self.select_file()

            matched_subjects = self.process_data(old_file_path, new_file_path)

            if matched_subjects is not None:
                self.matched_subjects = matched_subjects
                self.display_data(matched_subjects)
                self.display_rows_grades(matched_subjects)
                self.save_button.configure(state=tk.NORMAL)
                self.data_appraised = True
        else:
            messagebox.showwarning("Warning", "Please enter basic information first.")

    def save_to_database(self):
        if self.matched_subjects is not None:
            db_handler = DatabaseHandler()
            try:
                if self.basic_info_entered:
                    school_year = self.year_var.get()
                    if not school_year:
                        messagebox.showwarning("Warning", "Please select a school year.")
                        return
                    appraised_id, id_no, last_name, first_name, middle_name, year, sex, age, email_address = self.check_basic_info()
                    db_handler.save_appraised_data(appraised_id, id_no, last_name, first_name, middle_name, year, sex, age, email_address, self.matched_subjects, school_year)

                    messagebox.showinfo("Success", "Appraised data saved to the database successfully!")
                else:
                    messagebox.showwarning("Warning", "Please enter all basic information.")
            except Exception as e:
                # Print full traceback for debugging
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", f"Failed to save appraised data to database: {e}")
        else:
            messagebox.showwarning("Warning", "No appraised data to save.")

    def resize_background(self, event=None):
        """Update background image size when window is resized"""
        if hasattr(self, 'bg_image'):
            try:
                new_width = self.winfo_width()
                new_height = self.winfo_height()
                self.bg_image.configure(size=(new_width, new_height))
            except Exception as e:
                print(f"Error resizing background: {e}")

    def create_entries(self):
        labels_entries = [
            ("ID No:", 4, self.validate_id_no), 
            ("Last Name:", 5, self.validate_last_name), 
            ("First Name:", 6, self.validate_first_name), 
            ("Middle Name:", 7, self.validate_middle_name), 
            ("Year Level:", 8, self.validate_year_level), 
            ("Sex:", 9, self.validate_sex), 
            ("Age:", 10, self.validate_age), 
            ("Email Address:", 11, self.validate_email)]
        
        self.entries = {}
        for i, (label_text, row, validation_func) in enumerate(labels_entries):

            ctk.CTkLabel(self.basic_info_frame, text=label_text).grid(row=row, column=0)
            entry = ctk.CTkEntry(self.basic_info_frame, corner_radius=30, width=200, validate="key", validatecommand=(self.register(validation_func), '%P'))
            entry.grid(row=row, column=1, pady=4, padx=20)
            self.entries[label_text] = entry
            
            entry.bind('<Return>', lambda e, current=i, total=len(labels_entries): self.move_to_next_entry(e, current, total))
            entry.bind('<Tab>', lambda e, current=i, total=len(labels_entries): self.move_to_next_entry(e, current, total))

    def validate_id_no(self, new_value):
        # Allow only numbers and hyphens
        return re.match(r'^[0-9-]*$', new_value) is not None

    def validate_last_name(self, new_value):
        return self.validate_name(new_value, "Last Name:")

    def validate_first_name(self, new_value):
        return self.validate_name(new_value, "First Name:")

    def validate_middle_name(self, new_value):
        return self.validate_name(new_value, "Middle Name:")

    def validate_name(self, new_value, entry_label=None):
        # Strict pattern - only letters (including ñ/Ñ) and spaces
        if re.match(r'^[a-zA-ZñÑ\s]*$', new_value) is not None:
            # Remove multiple spaces and trailing spaces
            cleaned_name = ' '.join(word for word in new_value.split() if word)
            
            if cleaned_name or new_value == "":
                # Capitalize first letter of each word
                capitalized_name = ' '.join(word.capitalize() for word in cleaned_name.split())
                
                if entry_label:
                    # Update entry with cleaned and capitalized name
                    current_label = self.entries.get(entry_label)
                    if current_label:
                        current_label.delete(0, tk.END)
                        current_label.insert(0, capitalized_name)
                return True
        return False

    def validate_year_level(self, new_value):
        # Allow empty string for backspace/delete
        if new_value == "":
            return True
        # Allow only numbers 1-4
        return re.match(r'^[1-4]$', new_value) is not None

    def validate_sex(self, new_value):
        # Allow only M or F (case-insensitive)
        return re.match(r'^[mMfF]?$', new_value) is not None

    def validate_age(self, new_value):
        # Allow only numbers, max 3 digits
        return re.match(r'^[0-9]{0,2}$', new_value) is not None

    def validate_email(self, new_value):
        # Basic email validation
        return re.match(r'^[a-zA-Z0-9._%+-]*@?[a-zA-Z0-9.-]*\.?[a-zA-Z]*$', new_value) is not None

    def move_to_next_entry(self, event, current_index, total_entries):
        labels_order = ["ID No:", "Last Name:", "First Name:", "Middle Name:", "Year Level:", "Sex:", "Age:", "Email Address:"]
        
        # If not at the last entry, move to next
        if current_index < total_entries - 1:
            next_label = labels_order[current_index + 1]
            self.entries[next_label].focus_set()
        else:
            # If at last entry, move focus to the next button
            self.next_button.focus_set()
        
        # Prevent default Enter behavior
        return "break"