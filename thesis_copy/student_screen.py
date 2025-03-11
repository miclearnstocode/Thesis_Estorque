import csv
from decimal import Decimal, InvalidOperation
import logging
import os
import subprocess
import tempfile
import textwrap
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from database import DatabaseHandler
from fuzzywuzzy import fuzz
from sklearn.cluster import AgglomerativeClustering
import numpy as np
from PIL import Image, ImageTk
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from datetime import datetime

class StudentScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.columns = ('ID_NO', 'STUDENT_NAME', 'YEAR_LEVEL', 'AGE', 'SEX', 'EMAIL_ADDRESS', 'SHS', 'ADDRESS')
        self.curriculum_data = []
        self.curri_data_irreg = []
        self.id_no = None

        # Load and resize the background image for the main frame
        self.main_bg_image = Image.open("Image/student.JPG")
        # Get the screen dimensions for full coverage
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        self.main_bg_image = self.main_bg_image.resize((screen_width, screen_height), Image.LANCZOS)
        self.main_bg_photo = ImageTk.PhotoImage(self.main_bg_image)

        # Create and place the background label
        self.bg_label = tk.Label(self, image=self.main_bg_photo, compound='center')
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        ctk.CTkLabel(self,  text="Student", font=("Vivaldi", 40, "bold"), text_color="black", fg_color="transparent",  corner_radius=50, padx=20, pady=10).pack(pady=30)
        # Button style configuration
        button_style = {
            "fg_color": "transparent",    
            "hover_color": "#707070",     
            "text_color": "black",        
            "height": 32,                 
            "border_width": 1,            
            "border_color": "black",
            "corner_radius": 20}
        
        self.regular_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.regular_frame.pack(pady=20)

        self.back_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=30, width=20, height=15)
        self.back_frame.place(x=50,y=110)
        try:
            irreg_icon = Image.open("icons/irregulars.png")
            self.irreg_icon =ctk.CTkImage(light_image=irreg_icon, dark_image=irreg_icon, size=(30, 30))
            regular_icon = Image.open("icons/regulars.png")
            self.regular_icon =ctk.CTkImage(light_image=regular_icon, dark_image=regular_icon, size=(30, 30))

            ctk.CTkButton(self.regular_frame, text="Regular", image=self.regular_icon,**button_style, font=('Helvetica',14, 'bold'),command=lambda: self.show_search("Regular")).pack(side=tk.RIGHT,padx=10)
            ctk.CTkButton(self.regular_frame, text="Irregular", image=self.irreg_icon, **button_style,font=('Helvetica',14, 'bold'),command=self.show_search_irregular).pack(side=tk.RIGHT, padx=10)
        except Exception as e:
            print(f"Error loading Irregular/Regular icon: {e}")
        # Frames for search bar and student list
        self.search_frame = tk.Frame(self, bg="ghost white")
        self.search_frame.place(x=10, y=190)

        self.student_list_frame = tk.Frame(self)
        self.student_list_frame.place(x=30, y=250)

        self.print_frame = tk.Frame(self)
        self.print_frame.pack(pady=10)

        back_icon = Image.open("icons/back.png")
        self.back_icon = ctk.CTkImage(light_image=back_icon, dark_image=back_icon, size=(20, 20))
        ctk.CTkButton(self.back_frame, text="Back",image=self.back_icon,**button_style, width=32 ,font=('Helvetica',14, 'bold'),command=self.master.show_main_menu).pack(side=tk.LEFT)
        # Add Summary button
        summary_icon = Image.open("icons/summary.png")  # Load your summary icon
        self.summary_icon = ctk.CTkImage(light_image=summary_icon, dark_image=summary_icon, size =(30, 30))
        ctk.CTkButton(self, text="Summary", image=self.summary_icon, **button_style, font=('Helvetica',14, 'bold'),command=self.show_summary).place(x=700, y=147)  # Place the Summary button at the specified coordinates
 
    def show_summary(self):
        # Create a summary frame
        summary_frame = ctk.CTkFrame(self, width=800, height=800, fg_color="gainsboro", corner_radius=30)
        summary_frame.place(x=60, y=200)

        ctk.CTkLabel(summary_frame, text="Enrollment Summary", font=("Vivaldi", 30, "bold")).pack(pady=20)

        # Create a Notebook for year levels
        notebook = ttk.Notebook(summary_frame, width=950, height=320)
        notebook.pack(pady=10, expand=True, fill='both')

        # Connect to the database
        db_handler = DatabaseHandler()
        try:
            query = """
                SELECT ID_NO, LAST_NAME, FIRST_NAME, MIDDLE_NAME, YR, TO_BE_ENROLLED_YEAR
                FROM student_information
            """
            db_handler.cursor.execute(query)
            results = db_handler.cursor.fetchall()

            # Organize data by year
            student_data = {"1st Year": [], "2nd Year": [], "3rd Year": [], "4th Year": []}
            unenrolled_students = []  # Store students who are not enrolled

            for row in results:
                id_no, last_name, first_name, middle_name, year, enrolled_year = row
                full_name = f"{last_name}, {first_name} {middle_name}".strip()
                status = "Enrolled" if enrolled_year else "Not Enrolled"

                student_data[f"{year}st Year"].append({"id_no": id_no, "name": full_name, "status": status, "year_to_enroll": enrolled_year or "N/A"})

                if not enrolled_year:  # If unenrolled, store their ID for printing
                    unenrolled_students.append(id_no)

            self.unenrolled_students = unenrolled_students  # Store for printing

            # Compute total unenrolled students
            total_students = sum(len(students) for students in student_data.values())
            total_unenrolled = len(unenrolled_students)

            # Generate tabs for each year level
            for year, students in student_data.items():
                tab = ctk.CTkFrame(notebook)
                notebook.add(tab, text=year)

                tree_frame = ctk.CTkFrame(tab)
                tree_frame.pack(pady=10, padx=10, fill="both", expand=True)

                # Create Treeview for student data
                columns = ("Name", "Status", "Year to Enroll")
                tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
                tree.pack(side="left", fill="both", expand=True)

                # Add scrollbar
                scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
                scrollbar.pack(side="right", fill="y")
                tree.configure(yscrollcommand=scrollbar.set)

                # Set column headings
                tree.heading("Name", text="Student Name", anchor="center")
                tree.heading("Status", text="Enroll Status", anchor="center")
                tree.heading("Year to Enroll", text="Year to Enroll", anchor="center")

                # Set column widths
                tree.column("Name", width=200, anchor="w")
                tree.column("Status", width=150, anchor="center")
                tree.column("Year to Enroll", width=150, anchor="center")

                # Add row styles
                tree.tag_configure("oddrow", background="#f0f0f0")
                tree.tag_configure("evenrow", background="#ffffff")

                for i, student in enumerate(students):
                    tag = "evenrow" if i % 2 == 0 else "oddrow"
                    tree.insert("", "end", values=(student["name"], student["status"], student["year_to_enroll"]), tags=(tag,))

            # Add a print button for unenrolled students
            if total_unenrolled > 0:
                print_button = ctk.CTkButton(
                    summary_frame, text="Print Unenrolled", text_color="black", font=('Helvetica', 14, 'bold'),
                    corner_radius=30, command=self.print_unenrolled_students
                )
                print_button.place(x=20, y=540)

            # Close button
            close_icon = Image.open("icons/close.png")
            self.close_icon = ctk.CTkImage(light_image=close_icon, dark_image=close_icon, size=(30, 30))
            ctk.CTkButton(summary_frame, text="Close", text_color="black", font=('Helvetica', 14, 'bold'),
                        corner_radius=30, image=self.close_icon, command=summary_frame.destroy).pack(pady=30, padx=30, side="right")

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to fetch student data: {str(e)}")

    def validate_input(self, new_value):
        if  len (new_value) > 11:
            return False
        # Allow letters, numbers, and hyphen
        return bool(re.match(r'^[a-zA-Z0-9-]*$', new_value))
    
    def show_search(self, status):
        # Clear search frame before showing new search bar
        for widget in self.search_frame.winfo_children():
            widget.destroy()

        # Search label
        ctk.CTkLabel(self.search_frame, text=f"{status} Students ID NO:", font=ctk.CTkFont(size=14)).pack(side="left", padx=5)
        # Search entry
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(self.search_frame, corner_radius=20 ,textvariable=self.search_var,  width=200,  height=32,  placeholder_text="e.g, 2021-322048", validate="key", validatecommand=(self.register(self.validate_input), '%P'))
        self.search_entry.pack(side="left", padx=5)
        try:
            search_icon = Image.open("icons/searchs.png")
            self.search_icon = ctk.CTkImage(light_image=search_icon, dark_image=search_icon,size=(30,30))
            # Search button
            search_button = ctk.CTkButton( self.search_frame, text="Search",image=self.search_icon, text_color="black", fg_color="transparent", border_width=1,command=self.search_student, width=100, height=32)
            search_button.pack(side="left", padx=(0, 5))
        except Exception as e:
            print(f"Error loading search icon: {e}")
       
        self.selected_year_semester = ctk.StringVar()
        year_semester_combobox = ctk.CTkComboBox(self.search_frame, values=['1.1', '1.2', '2.1', '2.2', '3.1', '3.2', '4.1', '4.2'],variable=self.selected_year_semester, width=100, height=32,state="readonly",command=lambda choice: self.check_enrollment_status(None))
        year_semester_combobox.pack(side="left", padx=5)
        year_semester_combobox.set("Select")  

        try:
            print_icon = Image.open("icons/prints.png")
            self.print_icon =ctk.CTkImage(light_image=print_icon, dark_image=print_icon, size=(30, 30)) 

            self.print_button = ctk.CTkButton( self.search_frame, text="Print", image=self.print_icon, text_color="black", fg_color="transparent", border_width=1,hover_color="grey70" ,command=self.print_students, width=100, height=32)
            self.print_button.pack(side="left", padx=(0, 5))
        except Exception as e:
            print(f"Error loading print icon: {e}")

        # Checkbox for enrollment status
        self.enroll_var = ctk.BooleanVar()
        self.enroll_checkbox = ctk.CTkCheckBox(self.search_frame, text="", text_color="white",variable=self.enroll_var, command=self.update_enroll_label, state="disabled")
        self.enroll_checkbox.pack(side="left", padx=5)
        
        # Enrollment status label
        self.enroll_label = ctk.CTkLabel(self.search_frame, text="Enroll", font=ctk.CTkFont(size=14))
        self.enroll_label.place(x=719, y=6)

        try:
            add_student = Image.open("icons/add_students.png")
            self.add_student=ctk.CTkImage(light_image=add_student, dark_image=add_student,size=(30,30))
            import_button = ctk.CTkButton( self.search_frame, text="Add Student", image=self.add_student, text_color="black", fg_color="transparent", border_width=1 ,hover_color="grey70",command=self.import_students, width=120, height=32)
            import_button.pack(side="left", padx=(0,5))
        except Exception as e:
            CTkMessagebox(title="Error",message=f"Error loading add student icon: {e}")
        # Bind the Enter key to search functionality
        self.search_entry.bind("<Return>", lambda event: self.search_student())
    
    def update_enroll_label(self):
        self.enroll_label.configure(text="Enrolled" if self.enroll_var.get() else "Enroll")
    

    def clear_all_displays(self):
        # Clear search frame
        for widget in self.search_frame.winfo_children():
            widget.destroy()
            
        # Clear main display frame if it exists
        if hasattr(self, 'display_frame'):
            for widget in self.student_list_frame.winfo_children():
                widget.destroy()
                
        # Clear treeview if it exists
        if hasattr(self, 'treeview'):
            self.treeview.delete(*self.curriculum_tree.get_children())
            
        # Clear any other frames or widgets that might exist
        if hasattr(self, 'result_frame'):
            for widget in self.student_list_frame.winfo_children():
                widget.destroy()
                
        if hasattr(self, 'detail_frame'):
            for widget in self.tree.winfo_children():
                widget.destroy()
                
        # Reset any variables if needed
        self.search_var = tk.StringVar()
        self.selected_year_semester = tk.StringVar()

    def check_enrollment_status(self, event=None): #add a year level parameter 
        id_no = self.search_var.get().strip()
        year_level = self.selected_year_semester.get()

        if id_no:
            db_handler = DatabaseHandler()
            try:
                student_data = db_handler.fetch_student_data(id_no, year_level)
                table_exists = student_data["table_exists"]
                has_grades = student_data["has_grades"]
                if table_exists:
                    if has_grades:
                        # If the table exists and has grades, disable the print button
                        self.print_button.configure(state="disabled")
                        messagebox.showinfo("Enrollment Status", "Student has grades for this semester.")
                    else:
                        # If the table exists but has no grades, enable the print button
                        self.print_button.configure(state="normal")
                        messagebox.showinfo("Enrollment Status", f"No Grades yet for {year_level}")
                else:
                    # If the table doesn't exist, enable the print button
                    self.print_button.configure(state="normal")
                    messagebox.showinfo("Enrollment Status", f"Not yet Enrolled {year_level}")

            except Exception as e:
                messagebox.showerror("Database Error", f"An error occurred while checking enrollment status: {str(e)}")
        else:
            # If no ID is entered, disable the print button
            self.print_button.configure(state="disabled")
            messagebox.showwarning("Input Error", f"Please Enter a student ID_NO")

    def check_prerequisites(self, student_data, selected_year_semester):
        enrollable_subjects = []
        prerequisite_subjects = []
        
        # Get curriculum data and grades
        curriculum_data = student_data.get("curriculum_regular_data", [])
        all_grades = {}
        if "grades_data" in student_data and student_data["grades_data"]:
            for semester_grades in student_data["grades_data"].values():
                all_grades.update(semester_grades)

        def find_matching_course(course_code):
            best_match = None
            best_ratio = 0
            for grade_course in all_grades.keys():
                ratio = fuzz.ratio(course_code.lower(), grade_course.lower())
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = grade_course
            return best_match if best_ratio >= 100 else None

        # Get current year level subjects
        current_year_subjects = [
            subject for subject in curriculum_data 
            if subject and str(subject.get('YEAR_LEVEL', '')) == str(selected_year_semester)
        ]

        # Analyze each subject for the current year
        for subject in current_year_subjects:
            course_no = subject.get('COURSE_NO', '').strip()
            prerequisite = subject.get('PREREQUISITE', '').strip()
            
            if not prerequisite:
                enrollable_subjects.append(subject)
                continue

            # Check prerequisites
            prerequisites = [p.strip() for p in prerequisite.split(',')]
            can_enroll = True

            for prereq in prerequisites:
                # First check if the prerequisite has a grade
                matching_course = find_matching_course(prereq)
                
                if not matching_course:  # No grade found for prerequisite
                    # Find the prerequisite subject in curriculum data
                    prereq_subject = next(
                        (s for s in curriculum_data if s and 
                        fuzz.ratio(s.get('COURSE_NO', '').strip().lower(), prereq.lower()) >= 100),
                        None
                    )
                    
                    if prereq_subject:
                        # Only append if the prerequisite has no grade
                        prereq_course_no = prereq_subject.get('COURSE_NO', '').strip()
                        if prereq_course_no not in all_grades:
                            if prereq_subject not in prerequisite_subjects:
                                prerequisite_subjects.append(prereq_subject)
                            can_enroll = False

            if can_enroll:
                enrollable_subjects.append(subject)

        return {
            'enrollable': enrollable_subjects,
            'prerequisite_subjects': prerequisite_subjects
        }
    

    def search_student(self):
        id_no = self.search_var.get().strip()
        if not id_no:
            messagebox.showerror("Input Error", "Please enter a valid ID_NO.")
            return
        if not re.match(r'^[\w-]+$', id_no):
            messagebox.showerror("Input Error", "Invalid ID_NO format.")
            return

        for widget in self.student_list_frame.winfo_children():
            widget.destroy()

        year_level = self.selected_year_semester.get()
        db_handler = DatabaseHandler()
        
        try:
            # Implement caching mechanism for frequently searched IDs
            if not hasattr(self, 'student_cache'):
                self.student_cache = {}  # Initialize cache if not exists
                
            # Check cache first
            if id_no in self.student_cache:
                student_data = self.student_cache[id_no]
                print("Retrieved from cache")
            else:
                # If not in cache, fetch from database
                student_data = db_handler.fetch_student_data(id_no, None)
                
                # Cache the result (with a maximum cache size)
                MAX_CACHE_SIZE = 100
                if len(self.student_cache) >= MAX_CACHE_SIZE:
                    # Remove oldest entry if cache is full
                    self.student_cache.pop(next(iter(self.student_cache)))
                self.student_cache[id_no] = student_data
                print("Retrieved from database")

            # Process the student data
            if student_data["curriculum_data"]:
                current_yr = student_data["curriculum_data"][0].get("YR", "1")
                
                # Use set for O(1) lookup time
                completed_semesters = set(db_handler.check_all_tables_for_grades(id_no).keys())
                
                # Use dictionary for O(1) lookup time
                year_semester_mapping = {
                    '1': ['1.1', '1.2'],
                    '2': ['2.1', '2.2'],
                    '3': ['3.1', '3.2'],
                    '4': ['4.1', '4.2']
                }
                
                # Use dictionary for O(1) lookup time
                semester_conversion = {
                    'first_year_first_semester': '1.1',
                    'first_year_second_semester': '1.2',
                    'second_year_first_semester': '2.1',
                    'second_year_second_semester': '2.2',
                    'third_year_first_semester': '3.1',
                    'third_year_second_semester': '3.2',
                    'fourth_year_first_semester': '4.1',
                    'fourth_year_second_semester': '4.2'
                }
                
                # Convert to set for O(1) lookup time
                completed_yr_sem = {semester_conversion[sem] for sem in completed_semesters 
                                if sem in semester_conversion}
                
                # Find next semester efficiently
                current_year_semesters = year_semester_mapping.get(str(current_yr), [])
                next_semester = next((sem for sem in current_year_semesters 
                                    if sem not in completed_yr_sem), None)
                
                # If no next semester in current year, calculate next year's first semester
                if not next_semester and int(current_yr) < 4:
                    next_yr = str(int(current_yr) + 1)
                    next_semester = f"{next_yr}.1"
                
                # Update UI
                if next_semester:
                    self.selected_year_semester.set(next_semester)
                    print(f"Setting semester to: {next_semester}")
                else:
                    self.selected_year_semester.set("Select")
                    print("No next semester found")

        except Exception as e:
            ctk.CTkMessageBox(title="Database Error", 
                            message=f"An error occurred while fetching student data: {str(e)}")
            return
        
        # Create a frame to hold the student data and curriculum data
        student_frame = ttk.Frame(self.student_list_frame)
        student_frame.pack(fill="both", expand=True)
        # Configure style for reduced row height

        style = ttk.Style()
        style.configure("Treeview", font=("Helvetica", 10), rowheight=20)

        # Treeview widget for displaying student data
        table_student = ("ID NO", "STUDENT NAME", "YEAR", "AGE", "SEX", "EMAIL_ADDRESS")
        self.tree = ttk.Treeview(student_frame, columns=table_student, show='headings', height=2)
        self.tree.pack(fill="both", expand=True)

        column_widths = {
            "ID NO": 130,
            "STUDENT NAME": 300,
            "YEAR": 80,
            "AGE": 80,
            "SEX": 80,
            "EMAIL_ADDRESS": 300
        }

        for column in table_student:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=column_widths.get(column, 150), anchor='center', stretch=True)


        # Maintain a set of inserted ID_NO to avoid duplicates
        inserted_ids = set()

        for row in student_data["curriculum_data"]:
            student_id = row.get("ID_NO", "")
            if student_id not in inserted_ids:
                self.tree.insert("", "end", values=(
                    student_id,
                    row.get("STUDENT_NAME", ""),
                    row.get("YR", ""),
                    row.get("AGE", ""),
                    row.get("SEX", ""),
                    row.get("EMAIL_ADDRESS", "")
                ))
                self.student_name = row.get("STUDENT_NAME", "")  
                self.year_level = row.get("YR", "")
                self.sex = row.get("SEX","")
                self.age = row.get("AGE","")
                inserted_ids.add(student_id)

        treeview_frame = ttk.Frame(student_frame)
        treeview_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Treeview", font=("Helvetica", 12),  rowheight=36, background="white", fieldbackground="white", foreground="black") 
        style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"), background="white", foreground="black")


        # Treeview widget for displaying curriculum data
        table_curriculum = ("Course No.", "Descriptive Title", "Year Level", "Units", "Lec", "Lab", "Pre-requisite", "Grade")
        self.curriculum_tree = ttk.Treeview(treeview_frame, columns=table_curriculum, show='headings', height=10, style="Treeview",)
        self.curriculum_tree.pack(side="left",fill="both", expand=True)

        # Replace with standard ttk.Scrollbar for guaranteed visibility
        vsb = ttk.Scrollbar(treeview_frame, orient="vertical", 
        command=self.curriculum_tree.yview)
        self.curriculum_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        # Adjust column widths for curriculum tree
        curriculum_column_widths = {
            "Course No.": 130,
            "Descriptive Title": 300,
            "Year Level": 90,
            "Units": 80,
            "Lec": 80,
            "Lab": 80,
            "Pre-requisite": 150,
            "Grade": 90
        }

        for column in table_curriculum:
            self.curriculum_tree.heading(column, text=column)
            self.curriculum_tree.column(
                column, 
                width=curriculum_column_widths.get(column, 150), 
                anchor='center',
                stretch=True
            )
        # Clear existing data
        for item in self.curriculum_tree.get_children():
            self.curriculum_tree.delete(item)

        displayed_courses = set()
        # Check if the data is not empty
        if student_data["curriculum_regular_data"]:
            current_year = None
            year_totals = {'units': 0, 'lec': 0, 'lab': 0}
            sorted_curriculum = sorted(student_data["curriculum_regular_data"],
            key=lambda x: ( float(x.get('YEAR_LEVEL', '0')), x.get('COURSE_NO', '')))
            def wrap_text(text, width=30):
                """Function to wrap text to multiple lines"""
                import textwrap
                return '\n'.join(textwrap.wrap(text, width=width))
            
            for i, row in enumerate(sorted_curriculum):
                if row:
                    course_key = (row.get('COURSE_NO', '').strip(), row.get('YEAR_LEVEL', ''))
                    if course_key in displayed_courses:
                        continue
                    displayed_courses.add(course_key)
                    # Convert values to strings
                    course_no = row.get('COURSE_NO', '').strip()
                    descriptive_title = wrap_text(row.get('DESCRIPTIVE_TITLE', '').strip(), width=40)
                    year_level = row.get('YEAR_LEVEL', '')
                    units = row.get('UNITS', '')
                    lec = row.get('LEC', '')
                    lab = row.get('LAB', '')
                    prerequisite = wrap_text(row.get('PREREQUISITE', '').strip(), width=18)

                    # If year level changes, insert total row for previous year
                    if current_year is not None and current_year != year_level:
                        total_values = [ "","Total", "",str(int(year_totals['units'])), str(int(year_totals['lec'])), str(int(year_totals['lab'])),"",""]
                        self.curriculum_tree.insert("", "end", values=total_values, tags=('total',))
                        
                        #empty row after total
                        self.curriculum_tree.insert("", "end", values=[""] * 8, tags=('empty_row',))
                        # Reset totals for new year
                        year_totals = {'units': 0, 'lec': 0, 'lab': 0}

                    current_year = year_level
                    
                    # Add to running totals
                    try:
                        year_totals['units'] += float(units) if units else 0
                        year_totals['lec'] += float(lec) if lec else 0
                        year_totals['lab'] += float(lab) if lab else 0
                    except ValueError:
                        pass  # Handle cases where conversion to float fails

                    grade = " "  # Default grade if not found
                    if student_data["grades_data"]:
                        for table, grades in student_data["grades_data"].items():
                            normalized_grades = {k.strip(): v for k, v in grades.items()}
                            if course_no in normalized_grades:
                                grade = normalized_grades[course_no]
                                break
                            for grade_course, grade_value in normalized_grades.items():
                                if fuzz.partial_ratio(course_no, grade_course) >= 100:
                                    grade = grade_value
                                    break

                    values = [course_no, descriptive_title, year_level, units, lec, lab, prerequisite, grade]

                    if grade.strip() == "":
                        tag = 'no_grade'
                    else:
                        tag = 'evenrow' if i % 2 == 0 else 'oddrow'

                    self.curriculum_tree.insert("", "end", values=values, tags=(tag,))

            # Insert total for the last year
            if current_year is not None:
                total_values = ["","Total", "", str(int(year_totals['units'])), str(int(year_totals['lec'])), str(int(year_totals['lab'])), "", ""]
                self.curriculum_tree.insert("", "end", values=total_values, tags=('total',))
                # Add empty row after final total
                empty_row = ["", "", "", "", "", "", "", ""]
                self.curriculum_tree.insert("", "end", values=empty_row, tags=('empty_row',))
        else:
            print("No data in curriculum_regular_data")

        # Configure tag colors
        self.curriculum_tree.tag_configure('empty_row', background='white', font=('Helvetica', 12))
        self.curriculum_tree.tag_configure('oddrow', background='#E5E5E5')
        self.curriculum_tree.tag_configure('evenrow', background='#FFFFFF')
        self.curriculum_tree.tag_configure('no_grade', foreground='red')
        self.curriculum_tree.tag_configure('total', background='#D3D3D3', font=('Helvetica', 12))  # Grey background for total rows

        # Store the retrieved student ID for later use in printing
        self.selected_id_no = id_no  

    def get_grade_for_course(self, grades_data, course_no):
        # Remove any leading/trailing whitespace from the course number
        course_no = course_no.strip()
        
        # Look for an exact match first
        if course_no in grades_data:
            return grades_data[course_no]
        
        # If not found, look for a match ignoring leading/trailing spaces
        for key, value in grades_data.items():
            if key.strip() == course_no:
                return value
        
        return ""
    
    def enable_enrollment_and_save(self, id_no):
        """
        Enables the enrollment checkbox and updates the database with the enrolled year.
        """
        # Enable the checkbox
        self.enroll_var.set(True)
        self.enroll_checkbox.configure(state="normal")
        self.update_enroll_label()

        # Get current year and the next academic year
        enrolled_year = datetime.now().year
        to_be_enrolled_years = f"{enrolled_year}-{enrolled_year + 1}"  # Example: "2025-2026"

        # Fetch student details
        db_handler = DatabaseHandler()
        try:
            student_data = db_handler.fetch_student_data(id_no, self.selected_year_semester.get())

            if student_data and student_data["curriculum_data"]:
                student_info = student_data["curriculum_data"][0]  # Assuming we use the first entry
                last_name = student_info.get("LAST_NAME", "")
                first_name = student_info.get("FIRST_NAME", "")
                middle_name = student_info.get("MIDDLE_NAME", "")
                bday = student_info.get("BDAY", "")

                # Save to the database
                self.saving_student(last_name, first_name, middle_name, [student_info], enrolled_year, bday, to_be_enrolled_years)
                messagebox.showinfo("Success", "Student enrollment status updated.")
            else:
                messagebox.showerror("Error", "No student data found.")

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update enrollment status: {str(e)}")

    def print_students(self):
        self.enroll_var.set(True)
        self.update_enroll_label()
        if not hasattr(self, 'selected_id_no'):
            messagebox.showinfo("No Student Selected", "Please search for a student first.")
            return

        id_no = self.selected_id_no
        year_level = self.selected_year_semester.get()

        if not year_level:
            messagebox.showerror("Input Error", "Please select a year and semester.")
            return

        db_handler = DatabaseHandler()
        self.enable_enrollment_and_save(id_no)
        try:
            self.curriculum_data = db_handler.fetch_student_data(id_no, year_level)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while fetching curriculum data: {str(e)}")
            return

        if not hasattr(self, 'curriculum_data') or not self.curriculum_data:
            messagebox.showerror("Error", "No curriculum data found")
            return
        
        # Create a new window for printing
        print_window = tk.Toplevel(self)
        print_window.title("Pre-Registration Form")
        print_window.geometry("794x1123")
        print_window.resizable(False, False)

        # Create a frame to hold the canvas and scrollbar together
        scrollable_frame = tk.Frame(print_window)
        scrollable_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(scrollable_frame, width=794, height=1123)
        canvas.pack(side="left", fill="both", expand=True)

        # Create a CTkScrollbar for the canvas
        scrollbar = ctk.CTkScrollbar(scrollable_frame, orientation="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        # Configure the canvas to work with the scrollbar
        canvas.configure(yscrollcommand=scrollbar.set)

        print_frame = ttk.Frame(canvas)
        canvas.create_window((20, 0), window=print_frame, anchor="center")

        # Heading
        heading_label = ttk.Label(print_frame, text="COMPUTER STUDIES DEPARTMENT", font=("Times New Roman", 18, "bold"))
        heading_label.pack(pady=(20, 10), anchor="center")

        pre_reg_label = ttk.Label(print_frame, text="PRE-REGISTRATION FORM", font=("Times New Roman", 18, "bold"))
        pre_reg_label.pack(pady=(10, 20))

        # Block of content on the left
        left_frame = tk.Frame(print_frame, padx=10)
        left_frame.pack(side=tk.TOP, anchor="w", pady=(0, 10), fill="x")
        name_frame = tk.Frame(left_frame)
        name_frame.pack(fill= "x", pady=(0,10))

        curriculum_data = self.curriculum_data.get("curriculum_data",[])
        # Fetch student details for display (assuming only one student is fetched)
        student_details = curriculum_data[0]  # Assuming at least one record exists
        student_name = student_details.get("STUDENT_NAME", "")
        year = student_details.get("YR", "")
        sex = student_details.get("SEX", "")
        age = student_details.get("AGE", "") 

        # Configure the grid columns
        name_frame.columnconfigure(0, weight=1)
        name_frame.columnconfigure(1, weight=1)
        name_frame.columnconfigure(2, weight=1)

        # Add labels to the grid
        ttk.Label(name_frame, text=f"Name: {student_name}", font=("Times New Roman", 12)).grid(row=0, column=0, sticky="w")
        ttk.Label(name_frame, text=f"Sex: {sex}", font=("Times New Roman", 12)).grid(row=0, column=1, sticky="we")
        ttk.Label(name_frame, text=f"Age: {age}", font=("Times New Roman", 12)).grid(row=0, column=2, sticky="we")
        ttk.Label(left_frame, text=f"Course/Year Level: {year}", font=("Times New Roman", 12)).pack(anchor="w")
        ttk.Label(left_frame, text="Address:_____________________________", font=("Times New Roman", 12)).pack(anchor="w")
        ttk.Label(left_frame, text="Parent/Guardian:______________________", font=("Times New Roman", 12)).pack(anchor="w")
        ttk.Label(left_frame, text="Contact No:__________________________", font=("Times New Roman", 12)).pack(anchor="w")

        # Table to display course information
        table_frame = tk.Frame(print_frame, padx=10, pady=10)
        table_frame.pack(side=tk.TOP, fill="both", expand=True)

        # Create Treeview for course information
        table_columns = ("Course No", "Descriptive Title", "Units", "Faculty")
        self.treeview = ttk.Treeview(table_frame, columns=table_columns, show="headings")
        
        # Set font
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Times New Roman", 12), background="#4a7a8c")
        style.configure("Treeview", font=("Times New Roman", 12,))
        for column in table_columns:
            self.treeview.column(column, anchor="center", width=180)
            self.treeview.heading(column, text=column, anchor="center")

        self.treeview.pack(expand=True, fill="both")

        # Get prerequisite analysis
        prerequisite_analysis = self.check_prerequisites(self.curriculum_data, self.selected_year_semester.get())

        total_units = 0
        seen_courses = set()

        # Add current semester courses
        for subject in prerequisite_analysis['enrollable']:
            course_no = subject.get('COURSE_NO', '')
            if course_no not in seen_courses:
                row_tuple = (
                    course_no,
                    subject.get('DESCRIPTIVE_TITLE', ''),
                    subject.get('UNITS', ''),
                    ''  # Faculty
                )
                self.treeview.insert("", "end", values=row_tuple)
                seen_courses.add(course_no)
                try:
                    units = int(subject.get('UNITS', 0))
                except (ValueError, TypeError):
                    units = 0
                total_units += units

        # Add prerequisite subjects with red background
        for subject in prerequisite_analysis['prerequisite_subjects']:
            course_no = subject.get('COURSE_NO', '')
            if course_no not in seen_courses:
                row_tuple = (
                    course_no,
                    subject.get('DESCRIPTIVE_TITLE', ''),
                    subject.get('UNITS', ''),
                    ''  # Faculty
                )
                self.treeview.insert("", "end", values=row_tuple, tags=('prerequisite',))
                seen_courses.add(course_no)
                try:
                    units = int(subject.get('UNITS', 0))
                except (ValueError, TypeError):
                    units = 0
                total_units += units

        # Add total units row
        self.treeview.insert("", "end", values=("Total", "", total_units, ""))

        # Configure tag for prerequisite subjects
        self.treeview.tag_configure('prerequisite', foreground='red')  #red for prerequisite subjects

        # Certification and signature area
        cert_frame = tk.Frame(print_frame, padx=10)
        cert_frame.pack(side=tk.TOP, pady=(0, 10), fill="x")

        cert_label = ttk.Label(cert_frame, text="This is to certify that the student indicated above is qualified to enroll this_______________", font=("Times New Roman", 12))
        cert_label.pack(anchor="w")

        underscore_label = ttk.Label(cert_frame, text="_"*30, font=("Times New Roman", 12))
        underscore_label.pack(side=tk.RIGHT, pady=(6, 7), anchor="w")

        signature_frame = tk.Frame(print_frame, padx=10)
        signature_frame.pack(side=tk.RIGHT, pady=(1, 30), anchor="w")

        ttk.Label(signature_frame, text="Name and Signature of Student", font=("Times New Roman", 11)).pack(anchor="se")

        # Left side (west)
        noted_frame = tk.Frame(print_frame, padx=10)
        noted_frame.pack(side=tk.LEFT, pady=(10, 0), anchor="sw")

        ttk.Label(noted_frame, text="Noted:", font=("Times New Roman", 12)).pack(anchor="w", pady=(10, 0))
        ttk.Label(noted_frame, text="MAREVIC P. NAVA, MSCS", font=("Times New Roman", 11)).pack(anchor="w", pady=(0,0))
        ttk.Label(noted_frame, text="Program Chair, BSCS", font=("Times New Roman", 11)).pack(anchor="w", pady=(0, 10))

        # Right side (east)
        received_frame = tk.Frame(print_frame, padx=10)
        received_frame.pack(side=tk.RIGHT, pady=(10, 0), anchor="sw")

        ttk.Label(received_frame, text="Received:", font=("Times New Roman", 12)).pack(anchor="sw", pady=(10, 0))
        ttk.Label(received_frame, text="MARIA JONACEL B. SAZON", font=("Times New Roman", 11)).pack(anchor="sw", pady=(0,0))
        ttk.Label(received_frame, text="College Registrar", font=("Times New Roman", 11)).pack(anchor="sw", pady=(0, 10))
        
        print_frame.update_idletasks()  # Update "requested size" from children
        canvas.config(scrollregion=canvas.bbox("all"))
        # Optional: Bind the scrollbar to the canvas for better scrolling experience
        def on_canvas_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        print_frame.bind("<Configure>", on_canvas_configure)
        print_window.focus_set()
        print_window.bind('<Control-p>', lambda event: self.print_content(print_window))

    def print_content(self, print_window):

        # Create a sanitized filename from student name
        def sanitize_filename(name):
            # Remove invalid filename characters and replace spaces with underscores
            invalid_chars = '<>:"/\\|?*'
            filename = ''.join(c for c in name if c not in invalid_chars)
            filename = filename.replace(' ', '_')
            return filename

        # Create filename with student name and timestamp
        student_filename = sanitize_filename(self.student_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"{student_filename}_{timestamp}.pdf"
        
        # Create the PDF in temp directory with custom filename
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, pdf_filename)

        # Year level mapping
        year_mapping = {
            '1': '1st Year',
            '2': '2nd Year',
            '3': '3rd Year',
            '4': '4th Year'
        }
        
        # Convert year level to proper format
        formatted_year = year_mapping.get(str(self.year_level), self.year_level)
        # Get current school year
        db_handler = DatabaseHandler()
        current_school_year = db_handler.get_latest_school_year(self.selected_id_no)

        # Create the PDF
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4

        pdfmetrics.registerFont(TTFont('TimesNewRoman', 'C://Windows//Fonts//times.ttf'))
        pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', 'timesbd.ttf'))
        c.setFont('TimesNewRoman', 12)

        image_path = "Image\Header.jpg"  # Update this path to your image
        header_height = 80  
        c.drawImage(image_path, 0, height - header_height, width=width, height=header_height)

        header_space = 150 
        y = height - header_space
        y = height - 100
        # Set the font to bold
        c.setFont("TimesNewRoman-Bold", 14)
        c.drawCentredString(width / 2, y, "COMPUTER STUDIES DEPARTMENT")
        y -= 20
        c.drawCentredString(width / 2, y, "PRE-REGISTRATION FORM")
        y -= 30
        c.drawCentredString(width / 2, y, f"A.Y. {current_school_year or '______'}")
        y -= 20  
        c.drawCentredString(width / 2, y, f"{formatted_year}")
        y -= 30 
        # Reset the font to normal
        c.setFont("TimesNewRoman", 14)

        c.drawString(40, y, f"Name: {self.student_name}")
        c.drawString(285, y, f"Sex: {self.sex}")
        c.drawString(450, y,f"Age: {self.age}")
        y -= 20
        c.drawString(40, y, f"Course/Year Level: {self.year_level}")
        y -= 20
        c.drawString(40, y, "Address:____________________________")
        y -= 20
        c.drawString(40, y, "Parent/Guardian:______________________")
        y -= 20
        c.drawString(40, y, "Contact No:__________________________")
        y -= 20


        table_columns = ["Course Number", "Course Title", "Unit Credit", "Faculty"]
        data = [table_columns]

        total_units = 0
        seen_rows = set()

        # Get prerequisite analysis
        prerequisite_analysis = self.check_prerequisites(self.curriculum_data, self.selected_year_semester.get())

        # Add current semester courses
        for subject in prerequisite_analysis['enrollable']:
            course_no = subject.get('COURSE_NO', '')
            if course_no not in seen_rows:
                descriptive_title = textwrap.fill(subject.get('DESCRIPTIVE_TITLE', ''), 40)
                units = subject.get('UNITS', 0)
                faculty = ""

                data.append([course_no, descriptive_title, units, faculty])
                seen_rows.add(course_no)
                try:
                    unit = int(units)
                except (ValueError, TypeError):
                    unit = 0
                total_units += unit

        # Add prerequisite subjects
        for subject in prerequisite_analysis['prerequisite_subjects']:
            course_no = subject.get('COURSE_NO', '')
            if course_no not in seen_rows:
                descriptive_title = textwrap.fill(subject.get('DESCRIPTIVE_TITLE', ''), 40)
                units = subject.get('UNITS', 0)
                faculty = ""

                data.append([course_no, descriptive_title, units, faculty])
                seen_rows.add(course_no)
                try:
                    unit = int(units)
                except (ValueError, TypeError):
                    unit = 0
                total_units += unit

        data.append(["Total ", "", total_units])

        # Calculate dynamic row heights based on content
        row_heights = []
        for row in data:
            max_lines = max(len(str(cell).split('\n')) for cell in row)
            row_heights.append(max(20, max_lines * 15))  # Minimum 20, or 15 points per line

        # Update Table creation with row heights
        t = Table(data, 
                 colWidths=[1.5*inch, 3.5*inch, 1*inch, 1.5*inch],
                 rowHeights=row_heights)

        # Keep existing table styles
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),  # Grid lines
            ('BOX', (0,0), (-1,-1), 0.5, colors.black),  # Border around the table
            ('FONTNAME', (0,0), (-1,-1), 'TimesNewRoman'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'TimesNewRoman-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('FONTNAME', (0,1), (0,-1), 'TimesNewRoman-Bold'),  # Bold font for Course No
            ('FONTNAME', (2,-1), (2,-1), 'TimesNewRoman-Bold'),
        ]))

        # Draw the table on the canvas
        w, h = t.wrapOn(c, width, height)
        t.drawOn(c, 30, y - h)

        # Move down a bit to avoid overwriting
        y -= h + 40

        # Certification and signature area
        c.drawString(50, y, f"This is to certify that the student indicated above is qualified to enroll this A.Y. {current_school_year or '_______________'}")
        y -= + 50
        c.drawString(390, y, "__________________________")
        y -= 20
        c.drawString(400, y, "Name and Signature of Student")
        
        #initial y position
        y -= 50

        #starting y position for alignment purposes
        start_y = y

        # Draw the "Noted:" section on the left
        c.drawString(40, start_y, "Noted:")
        y = start_y - 30
        c.drawString(40, y, "MAREVIC P. NAVA, MSCS")
        y -= 20
        c.drawString(40, y, "Program Chair, BSCS")

        # Reset y to the starting position for the "Received:" section
        y = start_y

        # Draw the "Received:" section on the right
        c.drawRightString(410, y, "Received:")
        y -= 30
        c.drawRightString(515, y, "MARIA JONACEL B. SAZON")
        y -= 20
        c.drawRightString(462, y, "College Registrar")        
        
        # Draw footer image
        footer_image_path = "Image/Footer.jpg"  # Update this path to your footer image
        footer_height = 50  # Adjust height as needed
        c.drawImage(footer_image_path, 0, 0, width=width, height=footer_height)
        # Save the PDF
        c.save()

        try:
            if os.name == 'nt':  # Windows
                chrome_path = r'c:/Program Files/Google/Chrome/Application/chrome.exe'
                if os.path.exists(chrome_path):
                    if os.path.exists(pdf_path):
                        subprocess.run([chrome_path, pdf_path], shell=False)
                    else:
                        messagebox.showerror("Printing Error", "PDF file not found.")
                else:
                    chrome_path = r'c:/Program Files/Google/Chrome/Application/chrome.exe'
                    if os.path.exists(chrome_path):
                        if os.path.exists(pdf_path):
                            subprocess.run([chrome_path, pdf_path], shell=False)
                        else:
                            messagebox.showerror("Printing Error", "PDF file not found.")
                    else:
                        messagebox.showerror("Printing Error", "Google Chrome executable not found.")
            else:
                messagebox.showerror("Printing Error", "Printing is only supported on Windows.")
        except Exception as e:
            messagebox.showerror("Printing Error", f"An error occurred while printing: {str(e)}")
        finally:
            print_window.destroy()
        
    def show_search_irregular(self):
        # Clear search frame before showing new search bar
        for widget in self.search_frame.winfo_children():
            widget.destroy()
 
        # Search label
        ctk.CTkLabel(self.search_frame, text="Irregular Students ID NO:",font=ctk.CTkFont(size=14)).pack(side="left", padx=5)
        def validate_input(new_value):
            # Allow only letters, numbers, and hyphen
            return re.match(r'^[a-zA-Z0-9-]*$', new_value) is not None

        # Search entry
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry( self.search_frame, corner_radius=20 ,textvariable=self.search_var,  width=200,  height=32,  placeholder_text="Enter ID", validate="key", validatecommand=(self.register(validate_input), '%P'))
        self.search_entry.pack(side="left", padx=5)

        search_icon = Image.open("icons/searchs.png")
        self.search_icons = ctk.CTkImage(light_image=search_icon, dark_image=search_icon,size=(30,30))
        search_button = ctk.CTkButton( self.search_frame, text="Search",image=self.search_icons, command=self.search_student_irregular, text_color="black", fg_color="transparent", hover_color="grey70", border_width=1, width=100, height=32)
        search_button.pack(side="left", padx=(0, 5))

        # Year and Semester dropdown
        self.selected_year_semester = ctk.StringVar()
        self.year_semester_combobox = ctk.CTkComboBox(self.search_frame, values=['1.1', '1.2', '2.1', '2.2', '3.1', '3.2', '4.1', '4.2'],variable=self.selected_year_semester, width=100, height=32, state="readonly",command=lambda choice: self.check_enrollment_irregular(None))
        self.year_semester_combobox.pack(side="left", padx=5)
        self.year_semester_combobox.set("Select")  # Set default text

        print_icon = Image.open("icons/prints.png")
        self.print_icons =ctk.CTkImage(light_image=print_icon, dark_image=print_icon, size=(30, 30))
        self.print_button = ctk.CTkButton( self.search_frame, text="Print", image=self.print_icons ,command=self.print_students_irregular, fg_color="transparent", hover_color="grey70", border_width=1, text_color="black", width=100,height=32)
        self.print_button.pack(side="left", padx=(0, 5))

        # Bind the Enter key to search functionality
        self.search_entry.bind("<Return>", lambda event: self.search_student_irregular())
        
        # Checkbox for enrollment status
        self.enroll_vars = ctk.BooleanVar()
        self.enroll_checkboxs = ctk.CTkCheckBox(self.search_frame, text="", text_color="white",variable=self.enroll_vars, command=self.update_enroll_labels, state="disabled")
        self.enroll_checkboxs.pack(side="left", padx=5)
        
        # Enrollment status label
        self.enroll_labels = ctk.CTkLabel(self.search_frame, text="Enroll", font=ctk.CTkFont(size=14))
        self.enroll_labels.place(x=725, y=6)
    
    def update_enroll_labels(self):
        self.enroll_labels.configure(text="Enrolled" if self.enroll_vars.get() else "Enroll")
    
    def check_enrollment_irregular(self, event=None):
        id_no = self.search_var.get().strip()
        selected_year_level = self.selected_year_semester.get().strip()
        
        if not id_no:
            CTkMessagebox(title="Input Error", message="Please Enter a student ID_NO")
            self.print_button.configure(state="disabled")
            return None

        db_handler = DatabaseHandler()
        try:
            # Fetch all student data from appraised_curriculum
            appraised_data = db_handler.fetch_irregular_students(id_no)

            if not appraised_data:
                logging.info(f"No data found for ID_NO: {id_no}. Allowing new enrollment.")
                CTkMessagebox(title="Enrollment Status", message="No records found. Student can enroll.")
                self.print_button.configure(state="normal")
                return appraised_data

            # Prepare data for clustering
            def convert_year_level_to_numeric(year_level):
                # Ensure year_level is converted to string
                year_level = str(year_level)
                # Convert year level to a numeric representation
                year, semester = map(int, year_level.split('.'))
                return year + (semester / 10)  # e.g., 3.1 becomes 3.1, 3.2 becomes 3.2

            year_levels = np.array([
                convert_year_level_to_numeric(record['year_level']) 
                for record in appraised_data
            ]).reshape(-1, 1)
            
            # Apply Agglomerative Clustering
            clustering_model = AgglomerativeClustering(n_clusters=1, metric='euclidean', linkage='ward')
            clustering_model.fit(year_levels)
            labels = clustering_model.labels_

            # Determine the next semester based on completed courses
            def suggest_next_semester(data, labels):
                # Semester progression mapping
                semester_progression = {
                    '1.1': '1.2', '1.2': '2.1', 
                    '2.1': '2.2', '2.2': '3.1', 
                    '3.1': '3.2', '3.2': '4.1', 
                    '4.1': '4.2', '4.2': 'Graduate'
                }

                # Track semester completion and labels
                semester_info = {}
                for i, record in enumerate(data):
                    year_level = str(record['year_level'])
                    
                    # Check if grades indicate course completion
                    is_completed = (
                        record['grades'] not in ['', '0.00'] and 
                        (isinstance(record['grades'], (int, float, Decimal)) and float(record['grades']) >= 1.0) or
                        (isinstance(record['grades'], str) and record['grades'] != '' and float(record['grades']) >= 1.0)
                    )
                    
                    # Store semester information with its cluster label
                    semester_info[year_level] = {
                        'completed': is_completed,
                        'label': labels[i]
                    }

                # Sort semesters by year and semester
                sorted_semesters = sorted(
                    semester_info.keys(), 
                    key=lambda x: (int(x.split('.')[0]), int(x.split('.')[1]))
                )

                # Find the most recent completed semester in the same cluster
                current_cluster = labels[0]  # Use the first label as reference
                for semester in reversed(sorted_semesters):
                    # Check if semester is in the same cluster and completed
                    if (semester_info[semester]['label'] == current_cluster and 
                        semester_info[semester]['completed']):
                        
                        # Get the next semester in progression
                        next_semester = semester_progression.get(semester)
                        
                        # Validate next semester
                        while next_semester:
                            # Check if next semester exists in original data and is not completed
                            if (next_semester in semester_info and 
                                not semester_info[next_semester]['completed']):
                                return next_semester
                            
                            # Move to the next semester in progression
                            next_semester = semester_progression.get(next_semester)

                # Fallback: return the first semester if no progression found
                return sorted_semesters[0] if sorted_semesters else '1.1'

            # Get suggested semester
            suggested_semester = suggest_next_semester(appraised_data, labels)

            # Automatically set the combobox to the suggested semester
            if suggested_semester in self.year_semester_combobox.cget("values"):
                logging.info(f"Setting semester to: {suggested_semester}")
                self.year_semester_combobox.set(suggested_semester)
                self.selected_year_semester.set(suggested_semester)

                # Provide feedback if selected semester differs from suggested
                if selected_year_level != suggested_semester:
                    CTkMessagebox(
                        title="Semester Suggestion", 
                        message=f"Recommended semester is {suggested_semester}. Please verify."
                    )

            # Enable print button
            self.print_button.configure(state="normal")

            return appraised_data

        except Exception as e:
            logging.error(f"Enrollment check error: {str(e)}")
            CTkMessagebox(
                title="Database Error", 
                message=f"An error occurred while checking enrollment status: {str(e)}"
            )
            self.print_button.configure(state="disabled")
            return None
                                                
    def check_prerequisites_irregular(self, appraised_data, selected_year_semester):
        enrollable_subjects = []
        prerequisite_subjects = []
        corequisite_subjects = []
        failed_subjects = []
        no_grade_courses = []

        # Define year level order and mappings
        year_levels = ['1.1', '1.2', '2.1', '2.2', '3.1', '3.2', '4.1', '4.2']
        
        # Get current year and semester
        current_year = selected_year_semester.split('.')[0]
        current_semester = selected_year_semester.split('.')[1]

        def is_current_or_previous_year(year_level):
            """Check if the year level is current or previous"""
            try:
                year = year_level.split('.')[0]
                return int(year) <= int(current_year)
            except (ValueError, AttributeError, IndexError):
                return False

        def should_include_subject(subject):
            """Check if subject should be included based on grade and year level"""
            grade = str(subject.get('grades', '0.00')).strip()
            year_level = str(subject.get('year_level', '')).strip()
            
            try:
                grade_decimal = Decimal(grade)
                # Only include if grade is 0.00 and year level is current or previous
                return (grade_decimal == Decimal('0.00') and 
                        is_current_or_previous_year(year_level))
            except (InvalidOperation, TypeError):
                return False

        # First pass: Build requirement mappings
        course_requirements = {}
        requirement_status = {}
        requirement_type = {}

        for subject in appraised_data:
            course_no = subject.get('course_no', '').strip()
            requirements = subject.get('prerequisite', '')
            
            if requirements and isinstance(requirements, str):
                requirements = requirements.strip()
                req_list = [r.strip() for r in requirements.split(',') if r.strip()]
                if req_list:
                    course_requirements[course_no] = req_list
                    requirement_type[course_no] = ('corequisite' 
                        if len(req_list) >= 3 else 'prerequisite')

        # Second pass: Check requirement completion status
        for subject in appraised_data:
            course_no = subject.get('course_no', '').strip()
            grade = str(subject.get('grades', '0.00')).strip()
            
            try:
                grade_decimal = Decimal(grade)
                requirement_status[course_no] = {
                    'grade': grade_decimal,
                    'completed': grade_decimal > Decimal('0.00') and grade_decimal != Decimal('5.00')
                }
            except (InvalidOperation, TypeError):
                requirement_status[course_no] = {
                    'grade': Decimal('0.00'),
                    'completed': False
                }

        # Main processing loop
        for subject in appraised_data:
            course_no = subject.get('course_no', '').strip()
            subject_year_level = str(subject.get('year_level', '0'))
            grade_info = requirement_status.get(course_no, {})
            grade = grade_info.get('grade', Decimal('0.00'))

            # Skip if subject has a grade or is from a future year
            if not should_include_subject(subject):
                continue

            # Check requirements
            if course_no in course_requirements:
                missing_reqs = []
                for req in course_requirements[course_no]:
                    req_subject = next(
                        (s for s in appraised_data if s.get('course_no', '').strip() == req), 
                        None
                    )
                    if req_subject and should_include_subject(req_subject):
                        if requirement_type[course_no] == 'prerequisite':
                            if req_subject not in prerequisite_subjects:
                                prerequisite_subjects.append(req_subject)
                                print(f"Added prerequisite: {req} (Year: {req_subject.get('year_level')})")
                        else:  # corequisite
                            if req_subject not in corequisite_subjects:
                                corequisite_subjects.append(req_subject)
                                print(f"Added corequisite: {req} (Year: {req_subject.get('year_level')})")

            # Handle current year level subjects
            if subject_year_level == selected_year_semester:
                if grade == Decimal('5.00'):
                    failed_subjects.append(subject)
                elif grade == Decimal('0.00'):
                    no_grade_courses.append(subject)
                    # Only add to enrollable if it's the current year level
                    enrollable_subjects.append(subject)

        # Debug logging
        print(f"\nFinal Summary for {selected_year_semester}:")
        print(f"Enrollable Subjects: {len(enrollable_subjects)}")
        for subj in enrollable_subjects:
            print(f"  - {subj.get('course_no')}: Year {subj.get('year_level')}")
        
        print(f"\nPrerequisite Subjects: {len(prerequisite_subjects)}")
        for subj in prerequisite_subjects:
            print(f"  - {subj.get('course_no')}: Year {subj.get('year_level')}")
        
        print(f"\nCorequisite Subjects: {len(corequisite_subjects)}")
        for subj in corequisite_subjects:
            print(f"  - {subj.get('course_no')}: Year {subj.get('year_level')}")

        return {
            'enrollable_subject': enrollable_subjects,
            'prerequisite_subject': prerequisite_subjects,
            'corequisite_subject': corequisite_subjects,
            'failed_subject': failed_subjects,
            'no_grade_course': no_grade_courses
        }

    def search_student_irregular(self):
        identifier = self.search_var.get().strip().capitalize()
        if not identifier:
            messagebox.showerror("Input Error", "Please enter a valid id no  or last name")
            return

        # Clear any previous widgets
        for widget in self.student_list_frame.winfo_children():
            widget.destroy() 

        is_id_number = bool(re.match(r'^[\d-]+$', identifier))
        is_name = bool(re.match(r'^[a-zA-Z\s]+$', identifier))

        if not (is_id_number or is_name):
            messagebox.showerror("Input Error", "Invalid format. Please enter either:\n- ID Number (numbers and hyphens only)\n- Last Name (letters only)")
            return
        year_level = self.selected_year_semester.get()

        db_handler = DatabaseHandler()
        try:
            self.appraised_data = db_handler.fetch_irregular_students(identifier)
            if self.appraised_data:
                # Get current year from appraised_curriculum
                current_yr = self.appraised_data[0].get('year')  # This gets the 'year' column value
                print(f"Student's current year from appraised curriculum: {current_yr}")
                
                # Set available semesters based on current year
                if current_yr:
                    # For the current year level, show both semesters
                    current_year_sems = [f"{current_yr}.1", f"{current_yr}.2"]
                    self.selected_year_semester.set(current_year_sems[0])  # Default to first semester
                    print(f"Setting semester to: {current_year_sems[0]}")
                else:
                    self.selected_year_semester.set("Select")
                    print("No year level found in appraised curriculum")


            # Create a frame to hold the student data and curriculum data
            student_frame = tk.Frame(self.student_list_frame)
            student_frame.pack(fill="both", expand=True)

            style = ttk.Style()
            style.configure("Treeview", font=("Helvetica", 12), rowheight=20)
            # Treeview widget for displaying student data

            table_student = ("ID NO", "STUDENT NAME", "YEAR", "AGE", "SEX", "EMAIL_ADDRESS")
            self.tree = ttk.Treeview(student_frame, columns=table_student, show='headings', height=2)
            self.tree.pack(fill="both", expand=True)

            column_widths = {
                "ID NO": 130,
                "STUDENT NAME": 300,
                "YEAR": 80,
                "AGE": 80,
                "SEX": 80,
                "EMAIL_ADDRESS": 300
            }

            for column in table_student:
                self.tree.heading(column, text=column)
                self.tree.column(column, width=column_widths.get(column, 150), anchor='center', stretch=True)



            self.student_record = {}
            # Insert student data
            if self.appraised_data:
                student_info = self.appraised_data[0] 
                # Concatenate name fields with proper formatting
                last_name = student_info.get("last_name", "").strip()
                first_name = student_info.get("first_name", "").strip()
                middle_name = student_info.get("middle_name", "").strip()
                student_name = f"{last_name} {first_name} {middle_name}".strip()
                self.tree.insert("", "end", values=(
                    student_info.get("id_no", ""),
                    student_name, 
                    student_info.get("year", ""),
                    student_info.get("age", ""),
                    student_info.get("sex", ""),
                    student_info.get("email_address", "")
                ))
                self.student_name_irreg = student_name            
                self.year = student_info.get("year", "")
                self.sex_irreg = student_info.get("sex", "")
                self.age_irreg = student_info.get("age", "")

            treeview_frame = ttk.Frame(student_frame)
            treeview_frame.pack(fill="both", expand=True)
            style = ttk.Style()
            style.configure("Treeview", font=("Helvetica", 12),  rowheight=35, background="white", fieldbackground="white", foreground="black") 
            style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"), background="white", foreground="black")
            
            # Treeview widget for displaying curriculum data
            table_curriculum = ("Course_No", "Descriptive_Title", "Year_Level", "Units", "Lec", "Lab", "Prerequisite", "Grade")
            self.curriculum_tree = ttk.Treeview(treeview_frame, columns=table_curriculum, show='headings', height=10, style="Treeview")
            self.curriculum_tree.pack(side="left", fill="both", expand=True)

            vsb = ttk.Scrollbar(treeview_frame, orient="vertical", command=self.curriculum_tree.yview)
            self.curriculum_tree.configure(yscrollcommand=vsb.set)
            vsb.pack(side="right", fill="y")

            curriculum_column_widths = {
                "Course No.": 130,
                "Descriptive Title": 300,
                "Year Level": 90,
                "Units": 80,
                "Lec": 80,
                "Lab": 80,
                "Pre-requisite": 150,
                "Grade": 90
            }

            for column in table_curriculum:
                self.curriculum_tree.heading(column, text=column)
                self.curriculum_tree.column(
                    column, 
                    width=curriculum_column_widths.get(column, 150), 
                    anchor='center',
                    stretch=True
                )
            # Clear existing data
            for item in self.curriculum_tree.get_children():
                self.curriculum_tree.delete(item)

            if  self.appraised_data:
                irreg_current_year = None
                year_total = {'units': 0, 'lec': 0, 'lab': 0}

                # Insert curriculum data
                for i, row in enumerate(self.appraised_data):
                    course_no = row.get('course_no', '').strip()
                    descriptive_title = row.get('descriptive_title', '').strip()
                    year_level = str(row.get('year_level', ''))
                    units = str(row.get('units', ''))
                    lec = str(row.get('lec', ''))
                    lab = str(row.get('lab', ''))
                    prerequisite = row.get('prerequisite', '').strip()
                    grade = str(row.get('grades', ''))
                    grade = '' if grade == '0.00' else grade

                    if irreg_current_year is not None and  irreg_current_year != year_level:
                        total_values = ["", "Total", "",str(int(year_total['units'])), str(int(year_total['lec'])),str(int(year_total['lab'])), "", ""]
                        self.curriculum_tree.insert("", 'end', values=total_values, tags=('total',))

                        #empty rows
                        empty_rows = ["", "", "", "", "", "", "", ""]
                        self.curriculum_tree.insert("", "end", values=empty_rows, tags=('empty_row',))

                        # Reset totals for new year
                        year_total = {'units': 0, 'lec': 0, 'lab': 0}
                    
                    irreg_current_year = year_level
                        # Add to running totals
                    try:
                        year_total['units'] += float(units) if units else 0
                        year_total['lec'] += float(lec) if lec else 0
                        year_total['lab'] += float(lab) if lab else 0
                    except ValueError:
                        pass  # Handle cases where conversion to float fails
                    values = [course_no, descriptive_title, year_level, units, lec, lab, prerequisite, grade]

                    # Determine the tag based on grade and row number
                    if grade is None or grade.strip() == '':
                        tag = '0.00'
                    else:
                        tag = 'evenrow' if i % 2 == 0 else 'oddrow'

                    self.curriculum_tree.insert("", "end", values=values, tags=(tag,))
                        # After the loop, check if the last semester was "4.2" and insert totals
                if irreg_current_year == "4.2":
                    total_values = ["", "Total", "", str(int(year_total['units'])), str(int(year_total['lec'])), str(int(year_total['lab'])), "", ""]
                    self.curriculum_tree.insert("", 'end', values=total_values, tags=('total',))

                    # Empty rows
                    empty_rows = ["", "", "", "", "", "", "", ""]
                    self.curriculum_tree.insert("", "end", values=empty_rows, tags=('empty_row',))          
            # Configure tag colors
            self.curriculum_tree.tag_configure('oddrow', background='#E5E5E5')
            self.curriculum_tree.tag_configure('evenrow', background='#FFFFFF')
            self.curriculum_tree.tag_configure('0.00', foreground= 'red')  # Light red for rows with no grade

            # Store the retrieved student ID for later use in printing
            self.selected_id_no = identifier

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def print_students_irregular(self):
        self.enroll_vars.set(True)
        self.update_enroll_labels()
        if not hasattr(self, 'selected_id_no'):
            messagebox.showinfo("No Student Selected", "Please search for a student first.")
            return

        id_no = self.selected_id_no
        year_level = self.selected_year_semester.get()

        if not year_level:
            messagebox.showerror("Input Error", "Please select a year and semester.")
            return

        db_handler = DatabaseHandler()
        try:
            # Fetch irregular student data
            self.curri_data_irreg = db_handler.fetch_irregular_students(id_no)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while fetching curriculum data: {str(e)}")
            return

        if not self.curri_data_irreg:
            messagebox.showinfo("No Curriculum Data", "No curriculum data found for the selected semester.")
            return 

        # Create a new window for printing
        print_window = tk.Toplevel(self)
        print_window.title("Pre-Registration Form")
        print_window.geometry("794x1123")

        canvas = tk.Canvas(print_window, width=794, height=1123)
        canvas.pack()

        print_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=print_frame, anchor="nw")

        # Heading
        heading_label = ttk.Label(print_frame, text="COMPUTER STUDIES DEPARTMENT", font=("Times New Roman", 18, "bold"))
        heading_label.pack(pady=(20, 10), anchor="center")

        pre_reg_label = ttk.Label(print_frame, text="PRE-REGISTRATION FORM", font=("Times New Roman", 18, "bold"))
        pre_reg_label.pack(pady=(10, 20))

        # Block of content on the left
        left_frame = tk.Frame(print_frame, padx=10)
        left_frame.pack(side=tk.TOP, anchor="w", pady=(0, 10), fill="x")
        name_frame = tk.Frame(left_frame)
        name_frame.pack(fill= "x", pady=(0,10))
        # Fetch student details for display (assuming only one student is fetched)
        student_details = self.curri_data_irreg[0]  # Assuming at least one record exists
        student_name = self.student_name_irreg
        self.year = student_details.get("year", "")
        self.sex_irreg = student_details.get("sex", "")
        self.age_irreg = student_details.get("age", "") 

        # Configure the grid columns
        name_frame.columnconfigure(0, weight=1)
        name_frame.columnconfigure(1, weight=1)
        name_frame.columnconfigure(2, weight=1)

        # Add labels to the grid
        ttk.Label(name_frame, text=f"Name: {student_name}", font=("Times New Roman", 12)).grid(row=0, column=0, sticky="w")
        ttk.Label(name_frame, text=f"Sex: {self.sex_irreg}", font=("Times New Roman", 12)).grid(row=0, column=1, sticky="we")
        ttk.Label(name_frame, text=f"Age: {self.age_irreg}", font=("Times New Roman", 12)).grid(row=0, column=2, sticky="we")
        ttk.Label(left_frame, text=f"Course/Year Level: {self.year}", font=("Times New Roman", 12)).pack(anchor="w")
        ttk.Label(left_frame, text="Address:_____________________________", font=("Times New Roman", 12)).pack(anchor="w")
        ttk.Label(left_frame, text="Parent/Guardian:______________________", font=("Times New Roman", 12)).pack(anchor="w")
        ttk.Label(left_frame, text="Contact No:__________________________", font=("Times New Roman", 12)).pack(anchor="w")

        # Button to select fallback subject
        fallback_button = ctk.CTkButton(left_frame, bg_color="transparent", corner_radius= 30, text_color="black" ,text="Select Special Class", command=self.select_fallback_subject)
        fallback_button.pack(anchor="w", pady=(10, 0))
        # Table to display course information
        table_frame = tk.Frame(print_frame, padx=10, pady=10)
        table_frame.pack(side=tk.TOP, fill="both", expand=True)


        # Create Treeview for course information
        table_columns = ("Course No", "Descriptive Title", "Units", "Faculty")
        self.treeview = ttk.Treeview(table_frame, columns=table_columns, show="headings")

        # Set font
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Times New Roman", 12, 'bold'))
        style.configure("Treeview", font=("Times New Roman", 12,))
        for column in table_columns:
            self.treeview.column(column, anchor="center", width=200)
            self.treeview.heading(column, text=column, anchor="center")

        self.treeview.pack(expand=True, fill="both")

        # Create dictionaries to store subjects by their type
        subject_groups = {
            'enrollable': [],
            'no_grade': [],
            'prerequisite': [],
            'failed': []
        }

        # Check prerequisites
        prereq_analysis = self.check_prerequisites_irregular(self.curri_data_irreg, self.selected_year_semester.get())
        total_units = 0
        seen_courses = set()

        # Collect enrollable subjects first
        for subject in prereq_analysis['enrollable_subject']:
            if isinstance(subject, dict):
                course_no = subject.get('course_no', '')
                if course_no not in seen_courses:
                    subject_groups['enrollable'].append({
                        'data': (
                            course_no,
                            subject.get('descriptive_title', ''),
                            subject.get('units', ''),
                            ''
                        ),
                        'tag': '',
                        'units': subject.get('units', 0)
                    })
                    seen_courses.add(course_no)

        # Define a comprehensive mapping of year levels to allowed no-grade course semesters
        no_grade_semester_mapping = {
            '2.1': ['1.1'],    # For 2.1, only 1.1 no-grade courses are allowed
            '2.2': ['1.2'],    # For 2.2, only 1.2 no-grade courses are allowed
            '3.1': ['2.1'],    # For 3.1, only 2.1 no-grade courses are allowed
            '3.2': ['2.2'],    # For 3.2, only 2.2 no-grade courses are allowed
            '4.1': ['3.1'],    # For 4.1, only 3.1 no-grade courses are allowed
            '4.2': ['3.2']     # For 4.2, only 3.2 no-grade courses are allowed
        }

        # Collect no grade courses with semester-based limitation
        semester_no_grade_courses = {
            '1.1': [], '1.2': [], 
            '2.1': [], '2.2': [], 
            '3.1': [], '3.2': [], 
            '4.1': [], '4.2': []
        }

        # Get the selected year semester
        selected_year_semester = str(self.selected_year_semester.get())

        # Collect no grade courses
        for subject in prereq_analysis['no_grade_course']:
            course_no = subject.get('course_no', '')
            subject_year_level = str(subject.get('year_level', ''))
            
            # Check if the current selection has specific no-grade course restrictions
            if selected_year_semester in no_grade_semester_mapping:
                allowed_semesters = no_grade_semester_mapping[selected_year_semester]
                
                # Check if the subject's year level is in the allowed semesters
                if subject_year_level in allowed_semesters:
                    # Ensure only one no-grade course is added for the allowed semester
                    if not semester_no_grade_courses[subject_year_level]:
                        subject_groups['no_grade'].append({
                            'data': (
                                course_no,
                                subject.get('descriptive_title', ''),
                                subject.get('units', 0),
                                ''
                            ),
                            'tag': 'no_grade',
                            'units': subject.get('units', 0)
                        })
                        semester_no_grade_courses[subject_year_level].append(course_no)
                        seen_courses.add(course_no)
            
            # Handle special case for year levels before 2.1 (if needed)
            elif selected_year_semester in ['1.1', '1.2']:
                # For 1.1 and 1.2, allow all no-grade courses
                if subject_year_level in semester_no_grade_courses and not semester_no_grade_courses[subject_year_level]:
                    subject_groups['no_grade'].append({
                        'data': (
                            course_no,
                            subject.get('descriptive_title', ''),
                            subject.get('units', 0),
                            ''
                        ),
                        'tag': 'no_grade',
                        'units': subject.get('units', 0)
                    })
                    semester_no_grade_courses[subject_year_level].append(course_no)
                    seen_courses.add(course_no)


        # Collect prerequisite subjects
        for subject in prereq_analysis['prerequisite_subject']:
            course_no = subject.get('course_no', '')
            if course_no not in seen_courses:
                subject_groups['prerequisite'].append({
                    'data': (
                        course_no,
                        subject.get('descriptive_title', ''),
                        subject.get('units', ''),
                        ''
                    ),
                    'tag': 'prerequisite',
                    'units': subject.get('units', 0)
                })
                seen_courses.add(course_no)

        # Collect failed subjects
        for subject in prereq_analysis['failed_subject']:
            if isinstance(subject, dict):
                course_no = subject.get('course_no', '')
                if course_no not in seen_courses:
                    subject_groups['failed'].append({
                        'data': (
                            course_no,
                            subject.get('descriptive_title', ''),
                            subject.get('units', ''),
                            ''
                        ),
                        'tag': 'failed',
                        'units': subject.get('units', 0)
                    })
                    seen_courses.add(course_no)

        # Now insert subjects in the desired order
        display_order = ['enrollable', 'no_grade', 'prerequisite', 'failed']
        total_units = 0

        for category in display_order:
            for subject in subject_groups[category]:
                self.treeview.insert(
                    "",
                    "end",
                    values=subject['data'],
                    tags=(subject['tag'],) if subject['tag'] else ()
                )
                try:
                    units = int(subject['units'])
                except (ValueError, TypeError):
                    units = 0
                total_units += units

        # Add total units row
        self.treeview.insert("", "end", values=("Total", "", total_units, ""))

        # Configure tags for different types of subjects
        self.treeview.tag_configure('prerequisite', foreground='red')
        self.treeview.tag_configure('failed', foreground='blue')
        self.treeview.tag_configure('no_grade', foreground='gray')

        # Certification and signature area
        cert_frame = tk.Frame(print_frame, padx=10)
        cert_frame.pack(side=tk.TOP, pady=(0, 10), fill="x")

        cert_label = ttk.Label(cert_frame, text="This is to certify that the student indicated above is qualified to enroll this_______________", font=("Times New Roman", 12))
        cert_label.pack(anchor="w")

        # Create a frame for the signature area
        signature_frame = tk.Frame(cert_frame, padx=20)
        signature_frame.pack(side=tk.RIGHT, pady=(30, 10), anchor="se")

        # Add the underscore label
        underscore_label = ttk.Label(signature_frame, text="_______________________", font=("Times New Roman", 11))
        underscore_label.pack(anchor="e")  # Align to the end (right side)

        # Add the name and signature label below the underscore
        name_signature_label = ttk.Label(signature_frame, text="Name and Signature of Student", font=("Times New Roman", 11))
        name_signature_label.pack(anchor="e", pady=(5, 10))  # Add some top padding for spacing

        # Create a frame to contain both noted and received sections
        footer_frame = tk.Frame(print_frame, width=794)
        footer_frame.pack(pady=(10, 10), fill="x")

        # Configure the grid to have two equal columns
        footer_frame.columnconfigure(0, weight=1)
        footer_frame.columnconfigure(1, weight=1)

        # Left side (west) - Noted
        noted_frame = tk.Frame(footer_frame, padx=10)
        noted_frame.grid(row=0, column=0, sticky="w", padx=(10, 5))

        ttk.Label(noted_frame, text="Noted:", font=("Times New Roman", 11)).pack(anchor="w", pady=(10, 0))
        ttk.Label(noted_frame, text="MAREVIC P. NAVA, MSCS", font=("Times New Roman", 11)).pack(anchor="w", pady=(0, 0))
        ttk.Label(noted_frame, text="Program Chair, BSCS", font=("Times New Roman", 11)).pack(anchor="w", pady=(0, 10))

        # Right side (east) - Received
        received_frame = tk.Frame(footer_frame, padx=10)
        received_frame.grid(row=0, column=1, sticky="sw", padx=(5, 10))

        ttk.Label(received_frame, text="Received:", font=("Times New Roman", 11)).pack(anchor="sw", pady=(10, 0), padx=(0, 10))
        ttk.Label(received_frame, text="MARIA JONACEL B. SAZON", font=("Times New Roman", 11)).pack(anchor="sw", pady=(0, 0), padx=(0,10))
        ttk.Label(received_frame, text="College Registrar", font=("Times New Roman", 11)).pack(anchor="sw", pady=(0, 10), padx=(0, 10))
        
        print_window.focus_set()
        print_window.bind('<Control-p>', lambda event: self.print_content_irregular(print_window))
    
    def select_fallback_subject(self):
        # Open a new window to select a fallback subject
        fallback_window = tk.Toplevel(self)
        fallback_window.title("Special Class")
        fallback_window.geometry("500x400")

        # Create a listbox to display available subjects
        subject_listbox = tk.Listbox(fallback_window, selectmode=tk.SINGLE)
        subject_listbox.pack(expand=True, fill="both", padx=10, pady=10)

        # Fetch available subjects from the database
        db_handler = DatabaseHandler()
        available_subjects = db_handler.fetch_available_fallback_subjects(self.selected_id_no)

        # Populate the listbox with available subjects
        for subject in available_subjects:
            subject_listbox.insert(tk.END, f"{subject['course_no']} - {subject['descriptive_title']} ({subject['units']})")

        # Button to confirm selection
        confirm_button = ctk.CTkButton(fallback_window, corner_radius=30 , text_color="black",text="Add Subject", command=lambda: self.add_selected_subject(subject_listbox, fallback_window))
        confirm_button.pack(pady=(10, 0))
        
    def add_selected_subject(self, listbox, window):
        # Get the selected subject
        selected_index = listbox.curselection()
        if selected_index:
            selected_subject = listbox.get(selected_index)
            # Parse the selected subject to extract course number and title
            course_no, title_info = selected_subject.split(" - ")
            title, units_info = title_info.rsplit("(", 1)
            units = units_info.split(")")[0].strip()

            # Insert the selected subject into the Treeview
            self.treeview.insert("", "end", values=(course_no, title.strip(), units, ""))
            self.update_total_units()
            window.destroy()  # Close the selection window
        else:
            messagebox.showwarning("No Selection", "Please select a subject to add.")

    def update_total_units(self):
        total_units = 0
        for item in self.treeview.get_children():
            values = self.treeview.item(item, 'values')
            try:
                # Check if the first value is 'Total', if so, skip it
                if values[0] == "Total":
                    continue
                # Convert units to integer, handling potential string or float inputs
                units = int(float(values[2]))
                total_units += units

            except (ValueError, IndexError):
                continue  # Skip if there's an error converting units

        # Clear the existing total units row if it exists
        for item in self.treeview.get_children():
            values = self.treeview.item(item, 'values')
            if values[0] == "Total":
                self.treeview.delete(item)

        # Add the updated total units row
        self.treeview.insert("", "end", values=("Total", "", total_units, ""))


    def print_content_irregular(self, print_window):
        def sanitize_filename(name):
            # Remove invalid filename characters and replace spaces with underscores
            invalid_chars = '<>:"/\\|?*'
            filename = ''.join(c for c in name if c not in invalid_chars)
            filename = filename.replace(' ', '_')
            return filename

        # Create filename with student name and timestamp
        student_filename = sanitize_filename(self.student_name_irreg)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"{student_filename}_{timestamp}.pdf"
        
        # Create the PDF in temp directory with custom filename
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, pdf_filename)
        
        # Year level mapping
        year_mapping = {
            '1': '1st Year',
            '2': '2nd Year',
            '3': '3rd Year',
            '4': '4th Year'
        }
        
        # Convert year level to proper format
        formatted_year = year_mapping.get(str(self.year), self.year)
        # Get current school year
        db_handler = DatabaseHandler()
        current_school_year = db_handler.get_latest_school_year_irregular(self.selected_id_no)
        

        # Create the PDF
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4

        pdfmetrics.registerFont(TTFont('TimesNewRoman', 'C://Windows//Fonts//times.ttf'))
        pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', 'timesbd.ttf'))
        c.setFont('TimesNewRoman', 12)

        image_path = "Image\Header.jpg"  # Update this path to your image
        header_height = 80  
        c.drawImage(image_path, 0, height - header_height, width=width, height=header_height)

        header_space = 150 
        y = height - header_space
        y = height - 100
        # Set the font to bold
        c.setFont("TimesNewRoman-Bold", 14)
        c.drawCentredString(width / 2, y, "COMPUTER STUDIES DEPARTMENT")
        y -= 20
        c.drawCentredString(width / 2, y, "PRE-REGISTRATION FORM")
        y -= 30
        c.drawCentredString(width / 2, y, f"A.Y. {current_school_year or '______'}")
        y -= 20  
        c.drawCentredString(width / 2, y, f"{formatted_year}")
        y -= 30 
        # Reset the font to normal
        c.setFont("TimesNewRoman", 14)

        c.drawString(40, y, f"Name: {self.student_name_irreg}")
        c.drawString(285, y, f"Sex: {self.sex_irreg}")
        c.drawString(450, y,f"Age: {self.age_irreg}")
        y -= 20
        c.drawString(40, y, f"Course/Year Level: {self.year}")
        y -= 20
        c.drawString(40, y, "Address:______________________________")
        y -= 20
        c.drawString(40, y, "Parent/Guardian:______________________")
        y -= 20
        c.drawString(40, y, "Contact No:___________________________")
        y -= 20


        table_columns = ["Course Number", "Course Title", "Unit Credit", "Faculty"]
        data = [table_columns]
        total_units = 0        
        # Retrieve courses from the Treeview
        for item in self.treeview.get_children():
            values = self.treeview.item(item, 'values')
            course_no = textwrap.fill((values[0]),40)
            descriptive_title = textwrap.fill((values[1]),40)
            units = values[2]
            faculty = values[3]

            # Prepare subject data for the table
            data.append([course_no, descriptive_title, units, faculty])
            #descriptive_title = textwrap.fill(subject.get('DESCRIPTIVE_TITLE', ''), 40)
            # Add to total units
            try:
                total_units += int(units)  # Ensure units are summed correctly
            except (ValueError, TypeError):
                continue  # Skip if there's an error in conversion

        # Calculate dynamic row heights based on content
        row_heights = []
        for row in data:
            max_lines = max(len(str(cell).split('\n')) for cell in row)
            row_heights.append(max(20, max_lines * 15))  # Minimum 20, or 15 points per line

        # Update Table creation with row heights
        t = Table(data, 
                 colWidths=[1.5*inch, 3.5*inch, 1*inch, 1.5*inch],
                 rowHeights=row_heights)

        # Keep existing table styles
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),  # Grid lines
            ('BOX', (0,0), (-1,-1), 0.5, colors.black),  # Border around the table
            ('FONTNAME', (0,0), (-1,-1), 'TimesNewRoman'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'TimesNewRoman-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('FONTNAME', (0,1), (0,-1), 'TimesNewRoman-Bold'),  # Bold font for Course No
            ('FONTNAME', (2,-1), (2,-1), 'TimesNewRoman-Bold'),
        ]))

        # Draw the table on the canvas
        w, h = t.wrapOn(c, width, height)
        t.drawOn(c, 30, y - h)

        # this to avoid overwriting
        y -= h + 30

        # Certification and signature area
        c.drawString(50, y, f"This is to certify that the student indicated above is qualified to enroll this A.Y. {current_school_year or '_______________'}")
        y -= + 50
        c.drawString(370, y, "_____________________________")
        y -= 20
        c.drawString(390, y, "Name and Signature of Student")

        # Set the initial y position
        y -= 50

        # Save the starting y position for alignment purposes
        start_y = y

        # Draw the "Noted:" section on the left
        c.drawString(40, start_y, "Noted:")
        y = start_y - 30
        c.drawString(40, y, "MAREVIC P. NAVA, MSCS")
        y -= 20
        c.drawString(40, y, "Program Chair, BSCS")

        # Reset y to the starting position for the "Received:" section
        y = start_y

        # Draw the "Received:" section on the right
        c.drawRightString(410, y, "Received:")
        y -= 30
        c.drawRightString(515, y, "MARIA JONACEL B. SAZON")
        y -= 20
        c.drawRightString(462, y, "College Registrar")        

        # Draw footer image
        footer_image_path = "Image/Footer.jpg"  # Update this path to your footer image
        footer_height = 50  # Adjust height as needed
        c.drawImage(footer_image_path, 0, 0, width=width, height=footer_height)
        c.save()

        try:
            if os.name == 'nt':  # Windows
                chrome_path = r'c:/Program Files/Google/Chrome/Application/chrome.exe'
                if os.path.exists(chrome_path):
                    if os.path.exists(pdf_path):
                        subprocess.run([chrome_path, pdf_path], shell=False)
                    else:
                        messagebox.showerror("Printing Error", "PDF file not found.")
                else:
                    messagebox.showerror("Printing Error", "Google Chrome executable not found.")
            else:
                messagebox.showerror("Printing Error", "Printing is only supported on Windows.")
        except Exception as e:
            messagebox.showerror("Printing Error", f"An error occurred while printing: {str(e)}")
        finally:
            print_window.destroy()


    def import_students(self):
        # Clear student list frame
        for widget in self.student_list_frame.winfo_children():
            widget.destroy()

        select_icon = Image.open("icons/select.png")
        self.select_icon =ctk.CTkImage(light_image=select_icon, dark_image=select_icon, size=(20, 20))
        ctk.CTkLabel(self.student_list_frame, text="Select a file to import:", image=self.select_icon,compound="left",font=ctk.CTkFont(size=14)).pack(pady=10)

        # File selection frame
        file_frame = ctk.CTkFrame(self.student_list_frame, fg_color="transparent")
        file_frame.pack(fill="x", padx=20, pady=5)

        self.file_entry = ctk.CTkEntry(file_frame,width=400,height=32,placeholder_text="Select CSV file...")
        self.file_entry.pack(side="left", padx=(0, 10))

        browse_icon = Image.open("icons/browse.png")
        self.browse_icon =ctk.CTkImage(light_image=browse_icon, dark_image=browse_icon, size=(20, 20))
        ctk.CTkButton(file_frame,text="Browse", image=self.browse_icon,command=self.browse_file, width=100, height=32).pack(side="left", padx=5)

        import_icon = Image.open("icons/import.png")
        self.import_icon =ctk.CTkImage(light_image=import_icon, dark_image=import_icon, size=(20, 20))
        ctk.CTkButton(file_frame, text="Import", image=self.import_icon ,command=self.import_students_callback, width=100, height=32).pack(side="left", padx=5)

        # Add enrolled year selection
        year_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        year_frame.pack(side="left", padx=5)
        
        ctk.CTkLabel(
            year_frame,
            text="Enroll for Year:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=5)

        # Create list of years from 2020 to 2099
        years = [str(year) for year in range(2020, 2100)]
        self.enrolled_year_var = ctk.StringVar()
        self.enrolled_year_var.set("Select Year")  # Set default text
        
        year_dropdown = ctk.CTkComboBox(
            year_frame,
            values=years,
            variable=self.enrolled_year_var,
            width=100,
            height=32,
            state="readonly"
        )
        year_dropdown.pack(side="left", padx=5)

        # Treeview frame
        treeview_frame = ctk.CTkFrame(self.student_list_frame)
        treeview_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Scrollbars
        treeview_scrollbar = ttk.Scrollbar(treeview_frame, orient="vertical")
        treeview_scrollbar.pack(side="right", fill="y")

        treeview_scrollbar_x = ttk.Scrollbar(treeview_frame, orient="horizontal")
        treeview_scrollbar_x.pack(side="bottom", fill="x")

        # Configure Treeview style
        style = ttk.Style()
        style.configure("Treeview", background="#ffffff", foreground="black", fieldbackground="#ffffff", rowheight=25)
        style.configure("Treeview.Heading", background="#e7e7e7",font=('Helvetica', 12, 'bold'))

        # Create and configure Treeview
        self.treeview = ttk.Treeview( treeview_frame, yscrollcommand=treeview_scrollbar.set, xscrollcommand=treeview_scrollbar_x.set, style="Treeview")
        self.treeview.pack(fill="both", expand=True)

        # Configure scrollbars
        treeview_scrollbar.config(command=self.treeview.yview)
        treeview_scrollbar_x.config(command=self.treeview.xview)

        # Configure columns (remove ENROLLED_YEAR from display)
        self.columns = ('ID_NO', 'STUDENT_NAME', 'YR', 'AGE', 'SEX', 'EMAIL_ADDRESS', 'SHS', 'ADDRESS')
        self.treeview['columns'] = self.columns
        self.treeview['show'] = 'headings'  

        # Configure headings and columns (remove ENROLLED_YEAR)
        column_widths = {
            'ID_NO': (80, tk.NO),
            'STUDENT_NAME': (200, tk.YES),
            'YR': (50, tk.NO),
            'AGE': (50, tk.NO),
            'SEX': (50, tk.NO),
            'EMAIL_ADDRESS': (200, tk.YES),
            'SHS': (100, tk.YES),
            'ADDRESS': (200, tk.YES)
        }

        for col in self.columns:
            self.treeview.heading(col, text=col)
            width, stretch = column_widths.get(col, (100, tk.YES))
            self.treeview.column(col, width=width, stretch=stretch)

        # Configure alternating row colors
        self.treeview.tag_configure('oddrow', background='#f0f0f0')
        self.treeview.tag_configure('evenrow', background='#ffffff')

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, file_path)

    def import_students_callback(self):
        file_path = self.file_entry.get()
        if file_path:
            # Validate year selection first
            enrolled_year = self.enrolled_year_var.get()
            if enrolled_year == "Select Year":
                messagebox.showerror("Error", "Please select an enrollment year.")
                return
            """Ang kung mag print ka naga change ya font ka akun nga treeview kay uhon ko ni makapuli ko jan 1, 2025
            subong ay dec 31 , 2024 11:57pm 3 minutes bag o ang new year"""
            try:
                with open(file_path, 'r') as csvfile:
                    reader = csv.DictReader(csvfile)
                    data = []
                    display_data = []
                    
                    # Process each row
                    for row in reader:
                        # Create display version with formatted student name
                        display_row = row.copy()
                        display_row['STUDENT_NAME'] = f"{row['LAST_NAME']}, {row['FIRST_NAME']} {row['MIDDLE_NAME']}".strip()
                        
                        # Add enrolled year to original data only (not display)
                        row['ENROLLED_YEAR'] = int(enrolled_year)  # Convert to integer
                        
                        # Fix the AGE key (remove space if it exists)
                        if 'AGE ' in row:
                            row['AGE'] = row['AGE '].strip()
                            display_row['AGE'] = row['AGE '].strip()
                            del row['AGE ']
                        
                        data.append(row)  # Original data for database (includes ENROLLED_YEAR)
                        display_data.append(display_row)  # Modified data for display (excludes ENROLLED_YEAR)
                    
                    # Clear existing data
                    self.treeview.delete(*self.treeview.get_children())

                    # Insert display data into treeview (without ENROLLED_YEAR)
                    for i, row in enumerate(display_data):
                        values = [
                            row.get('ID_NO', ''),
                            row.get('STUDENT_NAME', ''),  # Combined name for display only
                            row.get('YR', ''),
                            row.get('AGE', ''),
                            row.get('SEX', ''),
                            row.get('EMAIL_ADDRESS', ''),
                            row.get('SHS', ''),
                            row.get('ADDRESS', '')
                        ]
                        tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                        self.treeview.insert('', 'end', values=values, tags=(tag,))

                    # Save original data to database (with ENROLLED_YEAR)
                    db_handler = DatabaseHandler()
                    db_handler.insert_students('student_information', data)

                    messagebox.showinfo("Success", "Students imported successfully!")
            except csv.Error as err:
                messagebox.showerror("Error", "Error reading CSV file: " + str(err))
        else:
            messagebox.showerror("Error", "Please select a file to import.")
  