import csv
from decimal import Decimal
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
from fuzzywuzzy import fuzz, process
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
        self.main_bg_image = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/Image/student.JPG")
        # Get the screen dimensions for full coverage
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        self.main_bg_image = self.main_bg_image.resize((screen_width, screen_height), Image.LANCZOS)
        self.main_bg_photo = ImageTk.PhotoImage(self.main_bg_image)

        # Create and place the background label
        self.bg_label = tk.Label(self, image=self.main_bg_photo, compound='center')
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        # Update the title label to use CTk
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
        
        self.regular_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=20)
        self.regular_frame.pack(pady=20)

        self.back_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.back_frame.place(x=50,y=110)
        try:
            irreg_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/irregulars.png")
            self.irreg_icon =ctk.CTkImage(light_image=irreg_icon, dark_image=irreg_icon, size=(30, 30))
            regular_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/regulars.png")
            self.regular_icon =ctk.CTkImage(light_image=regular_icon, dark_image=regular_icon, size=(30, 30))

            ctk.CTkButton(self.regular_frame, text="Regular", image=self.regular_icon,**button_style,command=lambda: self.show_search("Regular")).pack(side=tk.RIGHT,padx=10)
            ctk.CTkButton(self.regular_frame, text="Irregular", image=self.irreg_icon, **button_style,command=self.show_search_irregular).pack(side=tk.RIGHT, padx=10)
        except Exception as e:
            print(f"Error loading Irregular/Regular icon: {e}")
        # Frames for search bar and student list
        self.search_frame = tk.Frame(self, bg="ghost white")
        self.search_frame.pack(pady=10)

        self.student_list_frame = tk.Frame(self)
        self.student_list_frame.pack(pady=10)

        self.print_frame = tk.Frame(self)
        self.print_frame.pack(pady=10)

        back_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/back.png")
        self.back_icon = ctk.CTkImage(light_image=back_icon, dark_image=back_icon, size=(20, 20))
        ctk.CTkButton(self.back_frame, text="Back",image=self.back_icon,**button_style ,command=self.master.show_main_menu).pack(side=tk.LEFT)
    
    def validate_input(self, new_value):
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
        self.search_entry = ctk.CTkEntry(self.search_frame,  textvariable=self.search_var,  width=200,  height=32,  placeholder_text="e.g, 2021-322048", validate="key", validatecommand=(self.register(self.validate_input), '%P'))
        self.search_entry.pack(side="left", padx=5)
        try:
            search_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/searchs.png")
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
            print_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/prints.png")
            self.print_icon =ctk.CTkImage(light_image=print_icon, dark_image=print_icon, size=(30, 30)) 

            self.print_button = ctk.CTkButton( self.search_frame, text="Print", image=self.print_icon, text_color="black", fg_color="transparent", border_width=1,hover_color="grey70" ,command=self.print_students, width=100, height=32)
            self.print_button.pack(side="left", padx=(0, 5))
        except Exception as e:
            print(f"Error loading print icon: {e}")
        try:
            add_student = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/add_students.png")
            self.add_student=ctk.CTkImage(light_image=add_student, dark_image=add_student,size=(30,30))
            import_button = ctk.CTkButton( self.search_frame, text="Add Student", image=self.add_student, text_color="black", fg_color="transparent", border_width=1 ,hover_color="grey70",command=self.import_students, width=120, height=32)
            import_button.pack(side="left", padx=(0,5))
        except Exception as e:
            print(f"Error loading add student icon: {e}")
        # Bind the Enter key to search functionality
        self.search_entry.bind("<Return>", lambda event: self.search_student())
    
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

    def check_enrollment_status(self, event=None):
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
            #student_data = db_handler.fetch_student_data(id_no, year_level)
            #print(f"Received grades data:  {student_data['grades_data']}")
            # Get student data
            student_data = db_handler.fetch_student_data(id_no, None)  # Pass None for year_level initially
            
            # Get student's current year level and completed semesters
            current_yr = None
            completed_semesters = set()
            
            if student_data["curriculum_data"]:
                current_yr = student_data["curriculum_data"][0].get("YR", "1")
                
                # Get completed semesters
                grades_data = db_handler.check_all_tables_for_grades(id_no)
                completed_semesters = set(grades_data.keys())
                
                # Determine next enrollable semester
                year_semester_mapping = {
                    '1': ['1.1', '1.2'],
                    '2': ['2.1', '2.2'],
                    '3': ['3.1', '3.2'],
                    '4': ['4.1', '4.2']
                }
                
                current_year_semesters = year_semester_mapping.get(str(current_yr), [])
                next_semester = None
                
                # Convert semester table names to year.semester format
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
                
                # Convert completed semesters to year.semester format
                completed_yr_sem = {semester_conversion[sem] for sem in completed_semesters if sem in semester_conversion}
                
                # Find next enrollable semester
                for sem in current_year_semesters:
                    if sem not in completed_yr_sem:
                        next_semester = sem
                        break
                
                # If both semesters of current year are complete, move to next year's first semester
                if not next_semester and int(current_yr) < 4:
                    next_yr = str(int(current_yr) + 1)
                    next_semester = f"{next_yr}.1"
                
                # Set the combobox value
                if next_semester:
                    self.selected_year_semester.set(next_semester)
                    print(f"Setting semester to: {next_semester}")
                else:
                    self.selected_year_semester.set("Select")
                    print("No next semester found")
        except Exception as e:
            ctk.CTkMessageBox(title="Database Error", message=f"An error occurred while fetching student data: {str(e)}")
            return

        # Create a frame to hold the student data and curriculum data
        student_frame = tk.Frame(self.student_list_frame)
        student_frame.pack(fill="both", expand=True)
        # Configure style for reduced row height
        style = ttk.Style()
        style.configure("Treeview", font=("Helvetica", 10), rowheight=20)

        # Treeview widget for displaying student data
        table_student = ("ID_NO", "STUDENT_NAME", "YEAR", "AGE", "SEX", "EMAIL_ADDRESS")
        self.tree = ttk.Treeview(student_frame, columns=table_student, show='headings', height=2)
        self.tree.pack(fill="both", expand=True)

        for column in table_student:
            self.tree.heading(column, text=column)
            if column == "STUDENT_NAME" or column == "EMAIL_ADDRESS":
                self.tree.column(column, width=210, anchor='center')
            elif column == "ID_NO":
                self.tree.column(column, width=100, anchor='center')
            else:
                self.tree.column(column, width=80, anchor='center')

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
        style.configure("Treeview", font=("Helvetica", 12),  rowheight=35, background="white", fieldbackground="white", foreground="black") 
        style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"), background="white", foreground="black")


        # Treeview widget for displaying curriculum data
        table_curriculum = ("Course_No", "Descriptive_Title", "Year_Level", "Units", "Lec", "Lab", "Pre-requisite", "Grade")
        self.curriculum_tree = ttk.Treeview(treeview_frame, columns=table_curriculum, show='headings', height=10, style="Treeview",)
        self.curriculum_tree.pack(side="left",fill="both", expand=True)

        # Replace with standard ttk.Scrollbar for guaranteed visibility
        vsb = ttk.Scrollbar(treeview_frame, 
                            orient="vertical", 
                            command=self.curriculum_tree.yview)
        self.curriculum_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        for column in table_curriculum:
            self.curriculum_tree.heading(column, text=column)
            if column == "Descriptive_Title":
                self.curriculum_tree.column(column, width=250, anchor='center')
            elif column == "Course_No":
                self.curriculum_tree.column(column, width=100, anchor='center')
            else:
                self.curriculum_tree.column(column, width=80, anchor='center')

        # Clear existing data
        for item in self.curriculum_tree.get_children():
            self.curriculum_tree.delete(item)

        # Check if the data is not empty
        if student_data["curriculum_regular_data"]:
            current_year = None
            year_totals = {'units': 0, 'lec': 0, 'lab': 0}
            
            for i, row in enumerate(student_data["curriculum_regular_data"]):
                if row:
                    # Convert values to strings
                    course_no = row.get('COURSE_NO', '').strip()
                    descriptive_title = row.get('DESCRIPTIVE_TITLE', '').strip()
                    year_level = row.get('YEAR_LEVEL', '')
                    units = row.get('UNITS', '')
                    lec = row.get('LEC', '')
                    lab = row.get('LAB', '')
                    prerequisite = row.get('PREREQUISITE', '').strip()

                    # If year level changes, insert total row for previous year
                    if current_year is not None and current_year != year_level:
                        total_values = [ "","Total", "",str(int(year_totals['units'])), str(int(year_totals['lec'])), str(int(year_totals['lab'])),"",""]
                        self.curriculum_tree.insert("", "end", values=total_values, tags=('total',))
                        
                        #empty row after total
                        empty_row = ["", "", "", "", "", "", "", ""]
                        self.curriculum_tree.insert("", "end", values=empty_row, tags=('empty_row',))
                        
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
        self.curriculum_tree.tag_configure('empty_row', background='white', font=('Times New Roman', 12))
        self.curriculum_tree.tag_configure('oddrow', background='#E5E5E5')
        self.curriculum_tree.tag_configure('evenrow', background='#FFFFFF')
        self.curriculum_tree.tag_configure('no_grade', foreground='red')
        self.curriculum_tree.tag_configure('total', background='#D3D3D3', font=('Times New Roman', 12))  # Grey background for total rows

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
    
    def print_students(self):
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
        # Create a temporary PDF file
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf_path = temp_pdf.name
        temp_pdf.close()
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

        image_path = "C:/Users/Admin/Documents/Document_thesis/Header.jpg"  # Update this path to your image
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
        
        # Save the PDF
        c.save()

        try:
            if os.name == 'nt':  # Windows
                chrome_path = r'c:/Program Files/Google/Chrome/Application/chrome.exe'
                if os.path.exists(chrome_path):
                    pdf_path = temp_pdf.name
                    if os.path.exists(pdf_path):
                        subprocess.run([chrome_path, pdf_path], shell=False)
                    else:
                        messagebox.showerror("Printing Error", "PDF file not found.")
                else:
                    chrome_path = r'c:/Program Files/Google/Chrome/Application/chrome.exe'
                    if os.path.exists(chrome_path):
                        pdf_path = temp_pdf.name
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
        print_window.destroy ()

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
        self.search_entry = ctk.CTkEntry( self.search_frame,  textvariable=self.search_var,  width=200,  height=32,  placeholder_text="Enter ID", validate="key", validatecommand=(self.register(validate_input), '%P'))
        self.search_entry.pack(side="left", padx=5)

        search_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/searchs.png")
        self.search_icons = ctk.CTkImage(light_image=search_icon, dark_image=search_icon,size=(30,30))
        search_button = ctk.CTkButton( self.search_frame, text="Search",image=self.search_icons, command=self.search_student_irregular, text_color="black", fg_color="transparent", hover_color="grey70", border_width=1, width=100, height=32)
        search_button.pack(side="left", padx=(0, 5))

        # Year and Semester dropdown
        self.selected_year_semester = ctk.StringVar()
        year_semester_combobox = ctk.CTkComboBox(self.search_frame, values=['1.1', '1.2', '2.1', '2.2', '3.1', '3.2', '4.1', '4.2'],variable=self.selected_year_semester, width=100, height=32, state="readonly",command=lambda choice: self.check_enrollment_irregular(None))
        year_semester_combobox.pack(side="left", padx=5)
        year_semester_combobox.set("Select")  # Set default text

        print_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/prints.png")
        self.print_icons =ctk.CTkImage(light_image=print_icon, dark_image=print_icon, size=(30, 30))
        self.print_button = ctk.CTkButton( self.search_frame, text="Print", image=self.print_icons ,command=self.print_students_irregular, fg_color="transparent", hover_color="grey70", border_width=1, text_color="black", width=100,height=32)
        self.print_button.pack(side="left", padx=(0, 5))

        # Bind the Enter key to search functionality
        self.search_entry.bind("<Return>", lambda event: self.search_student_irregular())
        

    def check_enrollment_irregular(self, event=None):
        id_no = self.search_var.get().strip()
        selected_year_level = self.selected_year_semester.get().strip()  # Assuming this variable holds the selected year level

        if not id_no:
            messagebox.showwarning("Input Error", "Please Enter a student ID_NO")
            self.print_button.config(state="disabled")
            return None  # Return None to indicate failure

        db_handler = DatabaseHandler()
        try:
            # Fetch all student data from appraised_curriculum
            appraised_data = db_handler.fetch_irregular_students(id_no)

            if not appraised_data:
                logging.info(f"No data found for ID_NO: {id_no}. Allowing new enrollment.")
                messagebox.showinfo("Enrollment Status", f"No records found. Student can enroll.")
                self.print_button.config(state="normal")
                return appraised_data  # Return empty list

            # Filter appraised_data for the selected year level
            filtered_data = [record for record in appraised_data if record['year_level'] == selected_year_level]

            if not filtered_data:
                logging.info(f"No records found for ID_NO: {id_no} in year level {selected_year_level}. Allowing new enrollment.")
                messagebox.showinfo("Enrollment Status", f"No records found for the selected year level. Student can enroll.")
                self.print_button.config(state="normal")
                return appraised_data  # Return all appraised data

            # Extract year levels for clustering
            year_levels = np.array([record['year_level'] for record in filtered_data]).reshape(-1, 1)

            # Apply Agglomerative Clustering
            if len(year_levels) > 1:  # Ensure there is more than one data point for clustering
                clustering_model = AgglomerativeClustering(n_clusters=1, metric='euclidean', linkage='ward')
                clustering_model.fit(year_levels)
                labels = clustering_model.labels_

                # Log the clusters
                unique_clusters = set(labels)
                logging.info(f"Clusters formed for ID_NO: {id_no}: {unique_clusters}")

            # Check if there are any enrollable subjects
            enrollable_subjects = [record for record in filtered_data if record.get('prerequisite', '') == '']

            if not enrollable_subjects:
                logging.info(f"No enrollable subjects found for ID_NO: {id_no} in year level {selected_year_level}. Student cannot enroll.")
                messagebox.showinfo("Enrollment Status", "No enrollable subjects available for this semester.")
                self.print_button.config(state="disabled")
                return appraised_data  # Return all appraised data

            # Check grades and determine enrollment eligibility
            can_enroll = False  # Flag to check if the student can enroll
            for record in filtered_data:
                grade = record.get('grades', '0.00')  # Default to '0.00' if grade is not found

                # Check for year level 3.1 with no grade or grade of '0.00'
                if selected_year_level == '3.1' and (grade == '0.00' or grade == ''):
                    can_enroll = True
                    logging.info(f"Year level {selected_year_level} with no grade or grade 0.00 found for ID_NO: {id_no}. Enabling enrollment.")
                    break  # No need to check further if enrollment is enabled

                # If there's a valid grade (not 0.00 and not empty)
                elif grade and grade != '':
                    logging.info(f"Valid grade found for ID_NO: {id_no}. Disabling enrollment.")
                    self.print_button.config(state="disabled")
                    messagebox.showinfo("Enrollment Status", "Student has grades for this semester. Cannot enroll again.")
                    return appraised_data  # Return all appraised data

            # Final decision based on the can_enroll flag
            if can_enroll:
                self.print_button.config(state="normal")
                messagebox.showinfo("Enrollment Status", "Student can enroll.")
            else:
                logging.info(f"No grades found for ID_NO: {id_no }. Enabling enrollment.")
                self.print_button.config(state="normal")
                CTkMessagebox(title="Enrollment Status", message="Student can enroll.")

            return appraised_data  # Return all appraised data

        except Exception as e:
            logging.error(f"An error occurred while checking enrollment status: {str(e)}")
            CTkMessagebox(title="Database Error", message="An error occurred while checking enrollment status: {str(e)}")
            self.print_button.config(state="disabled")
            return None  # Return None to indicate failure
    

    def check_prerequisites_irregular(self, appraised_data, selected_year_semester):
        enrollable_subjects = []
        prerequisite_subjects = []
        failed_subjects = []
        no_grade_courses = []

        # Define year level order and semester prerequisite mapping
        year_levels = ['1.1', '1.2', '2.1', '2.2', '3.1', '3.2', '4.1', '4.2']
        semester_prerequisite_mapping = {
            '1.2': ['1.1'],
            '2.1': ['1.2'],
            '2.2': ['2.1', '1.2'],
            '3.1': ['2.1'],
            '3.2': ['3.1', '2.2'],
            '4.1': ['3.2'],
            '4.2': ['4.1', '3.2']
        }

        selected_index = year_levels.index(selected_year_semester)
        prerequisite_semesters = semester_prerequisite_mapping.get(selected_year_semester, [])

        print(f"\nDEBUG: Selected Year Level: {selected_year_semester}")
        print(f"Prerequisite Semesters: {prerequisite_semesters}")

        # Track added no-grade courses and prerequisite subjects per semester
        semester_no_grade_courses = {
            '1.1': [], '1.2': [], 
            '2.1': [], '2.2': [], 
            '3.1': [], '3.2': [], 
            '4.1': [], '4.2': []
        }
        
        semester_prerequisite_subjects = {
            '1.1': [], '1.2': [], 
            '2.1': [], '2.2': [], 
            '3.1': [], '3.2': [], 
            '4.1': [], '4.2': []
        }

        # First pass: Check for no grade courses and prerequisite subjects
        for subject in appraised_data:
            subject_year_level = str(subject.get('year_level', '0'))
            course_no = subject.get('course_no', '').strip()
            grade = str(subject.get('grades', '0.00'))

            print(f"Checking subject: {course_no}, Year Level: {subject_year_level}, Grade: {grade}")

            # Convert grade to Decimal for comparison
            try:
                grade_decimal = Decimal(grade)
            except:
                grade_decimal = Decimal('0.00')

            try:
                subject_index = year_levels.index(subject_year_level)
                
                # Check if subject has no grade
                if grade_decimal == Decimal('0.00'):
                    # No-grade courses logic
                    if subject_index < selected_index:
                        if selected_year_semester in ['4.1', '4.2']:
                            # Final year: add all no-grade courses
                            print(f"Found no grade course (Final Year): {course_no} (Year Level: {subject_year_level})")
                            no_grade_courses.append(subject)
                        else:
                            # Other semesters: limit to one no-grade course per semester
                            if not semester_no_grade_courses[subject_year_level]:
                                print(f"Found no grade course: {course_no} (Year Level: {subject_year_level})")
                                no_grade_courses.append(subject)
                                semester_no_grade_courses[subject_year_level].append(course_no)
                            else:
                                print(f"Skipped additional no grade course: {course_no} (Year Level: {subject_year_level})")
                    
                    # Prerequisite subjects logic
                    # Only add if the subject's year level matches any of the prerequisite semesters
                    for prerequisite_semester in prerequisite_semesters:
                        if subject_year_level == prerequisite_semester:
                            # Check if the prerequisite subject specifically has a grade of 0.00
                            if grade_decimal == Decimal('0.00'):
                                if not semester_prerequisite_subjects[subject_year_level]:
                                    print(f"Found prerequisite subject for {selected_year_semester}: {course_no} (Year Level: {subject_year_level})")
                                    prerequisite_subjects.append(subject)
                                    semester_prerequisite_subjects[subject_year_level].append(course_no)
                                else:
                                    print(f"Skipped additional prerequisite subject: {course_no} (Year Level: {subject_year_level})")
            
            except ValueError:
                print(f"Invalid year level: {subject_year_level}")
                continue

        # Get current year subjects
        current_year_subjects = [
            subject for subject in appraised_data 
            if str(subject.get('year_level', '0')) == selected_year_semester
        ]

        # Process current year subjects independently
        for subject in current_year_subjects:
            course_no = subject.get('course_no', '').strip()
            grade = str(subject.get('grades', '0.00'))

            print(f"\nProcessing current year course: {course_no}")
            print(f"Grade: {grade}")

            # Current year courses can be enrolled directly
            enrollable_subjects.append(subject)

        # Debug logging
        print(f"\nDEBUG Summary:")
        print(f"Total Enrollable Subjects: {len(enrollable_subjects)}")
        print(f"Total No Grade Courses: {len(no_grade_courses)}")
        print(f"Total Prerequisite Subjects: {len(prerequisite_subjects)}")
        print(f"Total Failed Subjects: {len(failed_subjects)}")
        
        print("\nNo Grade Courses Details:")
        for course in no_grade_courses:
            print(f"Course: {course['course_no']} - Year Level: {course['year_level']} - Grade: {course.get('grades', '0.00')}")

        return {
            'enrollable_subject': enrollable_subjects,
            'no_grade_course': no_grade_courses,
            'prerequisite_subject': prerequisite_subjects,
            'failed_subject': failed_subjects
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
            self.appraised_data = db_handler.fetch_irregular_students(identifier,)
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
            table_student = ("ID_NO", "STUDENT_NAME", "YEAR", "AGE", "SEX", "EMAIL_ADDRESS")
            self.tree = ttk.Treeview(student_frame, columns=table_student, show='headings', height=2)
            self.tree.pack(fill="both", expand=True)

            for column in table_student:
                self.tree.heading(column, text=column)
                if column == "STUDENT_NAME" or column == "EMAIL_ADDRESS":
                    self.tree.column(column, width=210, anchor=tk.W)
                elif column == "ID_NO":
                    self.tree.column(column, width=100, anchor=tk.W)
                else:
                    self.tree.column(column, width=80, anchor=tk.W)
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

            for column in table_curriculum:
                self.curriculum_tree.heading(column, text=column)
                if column == "Descriptive_Title":
                    self.curriculum_tree.column(column, width=250, anchor='center')
                elif column == "Course_No":
                    self.curriculum_tree.column(column, width=100, anchor='center')
                else:
                    self.curriculum_tree.column(column, width=80, anchor='center')

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
            self.curri_data_irreg = db_handler.fetch_irregular_students(id_no,)

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

    def print_content_irregular(self, print_window):
        # Create a temporary PDF file
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf_path = temp_pdf.name
        temp_pdf.close()
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

        image_path = "C:/Users/Admin/Documents/Document_thesis/Header.jpg"  # Update this path to your image
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
        seen_rows = set()
        # Get prerequisite analysis for irregular students
        prerequisite_analysis = self.check_prerequisites_irregular(self.curri_data_irreg, self.selected_year_semester.get())

        # Define a comprehensive mapping of year levels to allowed no-grade course semesters
        no_grade_semester_mapping = {
            '2.1': ['1.1'],    # For 2.1, only 1.1 no-grade courses are allowed
            '2.2': ['1.2'],    # For 2.2, only 1.2 no-grade courses are allowed
            '3.1': ['2.1'],    # For 3.1, only 2.1 no-grade courses are allowed
            '3.2': ['2.2'],    # For 3.2, only 2.2 no-grade courses are allowed
            '4.1': ['3.1'],    # For 4.1, only 3.1 no-grade courses are allowed
            '4.2': ['3.2']     # For 4.2, only 3.2 no-grade courses are allowed
        }

        semester_no_grade_courses = {
            '1.1': [], '1.2': [], 
            '2.1': [], '2.2': [], 
            '3.1': [], '3.2': [], 
            '4.1': [], '4.2': []
        }

        # Get the selected year semester
        selected_year_semester = str(self.selected_year_semester.get())

        # Process subjects in order
        subject_categories = [
            ('enrollable_subject', 'enrollable'), ('no_grade_course', 'no_grade'), ('prerequisite_subject', 'prerequisite'), ('failed_subject', 'failed')]

        for category, category_name in subject_categories:
            subjects = prerequisite_analysis.get(category, [])
            
            for subject in subjects:
                course_no = subject.get('course_no', '')
                
                # Skip if course already seen
                if course_no in seen_rows:
                    continue
                
                # Special handling for no-grade courses
                if category == 'no_grade_course':
                    subject_year_level = str(subject.get('year_level', ''))
                    
                    # Check if the current selection has specific no-grade course restrictions
                    if selected_year_semester in no_grade_semester_mapping:
                        allowed_semesters = no_grade_semester_mapping[selected_year_semester]
                        
                        # Check if the subject's year level is in the allowed semesters
                        if subject_year_level not in allowed_semesters or semester_no_grade_courses[subject_year_level]:
                            continue
                    
                    # Mark this semester's no-grade course as used
                    semester_no_grade_courses[subject_year_level].append(course_no)
                
                # Prepare subject data
                descriptive_title = textwrap.fill(subject.get('descriptive_title', ''), 40)
                units = subject.get('units', 0)
                faculty = ""

                data.append([course_no, descriptive_title, units, faculty])
                seen_rows.add(course_no)
                
                # Calculate units
                try:
                    unit = int(units)
                except (ValueError, TypeError):
                    unit = 0
                total_units += unit

        # Add total units row
        data.append(["Total ", "", total_units, ""])

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
        y -= h + 40

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

        # Save the PDF
        c.save()

        try:
            if os.name == 'nt':  # Windows
                chrome_path = r'c:/Program Files/Google/Chrome/Application/chrome.exe'
                if os.path.exists(chrome_path):
                    pdf_path = temp_pdf.name
                    if os.path.exists(pdf_path):
                        subprocess.run([chrome_path, pdf_path], shell=False)
                    else:
                        messagebox.showerror("Printing Error", "PDF file not found.")
                else:
                    chrome_path = r'c:/Program Files/Google/Chrome/Application/chrome.exe'
                    if os.path.exists(chrome_path):
                        pdf_path = temp_pdf.name
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

        # Close the print window
        print_window.destroy()


    def import_students(self):
        # Clear student list frame
        for widget in self.student_list_frame.winfo_children():
            widget.destroy()

        select_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/select.png")
        self.select_icon =ctk.CTkImage(light_image=select_icon, dark_image=select_icon, size=(20, 20))
        ctk.CTkLabel(self.student_list_frame, text="Select a file to import:", image=self.select_icon,compound="left",font=ctk.CTkFont(size=14)).pack(pady=10)

        # File selection frame
        file_frame = ctk.CTkFrame(self.student_list_frame, fg_color="transparent")
        file_frame.pack(fill="x", padx=20, pady=5)

        self.file_entry = ctk.CTkEntry(file_frame,width=400,height=32,placeholder_text="Select CSV file...")
        self.file_entry.pack(side="left", padx=(0, 10))

        browse_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/browse.png")
        self.browse_icon =ctk.CTkImage(light_image=browse_icon, dark_image=browse_icon, size=(20, 20))
        ctk.CTkButton(file_frame,text="Browse", image=self.browse_icon,command=self.browse_file, width=100, height=32).pack(side="left", padx=5)

        import_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/import.png")
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
  