import logging
import threading
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import messagebox
from database import DatabaseHandler
from fuzzywuzzy import process  # Add this import at the top of the file
import pandas as pd

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PIL import Image
import time
from datetime import datetime, timedelta
import sys
import gc
import os

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_EMAIL = 'michaelestorque123@gmail.com'
SMTP_PASSWORD = 'ycxyqorukveyxiqs'

class GradeScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.cache_data = {}
        self.cache_timestamps = {}
        self.cache_size_limit = 100 * 1024 * 1024
        self.cache_ttl = timedelta(minutes=30)
        self.master = master
        
        # Create database handler instance
        self.db_handler = DatabaseHandler()
        self.data_frame = None

        # Set up the background
        try:
            # Load the background image
            bg_image = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/Image/Gradient.jpg")
            self.bg_image = ctk.CTkImage(
                light_image=bg_image,
                dark_image=bg_image,
                size=(self.master.winfo_width(), self.master.winfo_height())
            )
            
            # Create background label
            self.bg_label = ctk.CTkLabel(
                self,
                image=self.bg_image,
                text=""
            )
            self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
            
            # Bind resize event
            self.bind('<Configure>', self._resize_background)
            
        except Exception as e:
            print(f"Error loading background image: {e}")
            self.configure(fg_color="#FFFFFF")
    
        self.create_widgets()

    def _resize_background(self, event=None):
        """Update background image size when window is resized"""
        if hasattr(self, 'bg_image'):
            try:
                new_width = self.winfo_width()
                new_height = self.winfo_height()
                self.bg_image.configure(size=(new_width, new_height))
            except Exception as e:
                print(f"Error resizing background: {e}")

    def create_widgets(self):
        ctk.CTkLabel(self, text="   Grades  ", font=("Vivaldi", 30),fg_color="transparent", text_color="black").pack(pady=30)

        # Button style configuration
        button_style = {
            "fg_color": "transparent",    
            "hover_color": "#707070",     
            "text_color": "black",        
            "width": 120,                 
            "height": 32,                 
            "border_width": 1,            
            "border_color": "black"       
        }

        # Create a frame to hold the year and semester selectors
        selection_frame = ctk.CTkFrame(self)
        selection_frame.pack(pady=15)

        school_years = []
        for year in range(2020, 2100):
            school_years.append(f"{year}-{year+1}")

        # Add School Year dropdown
        self.school_year_var = ctk.StringVar()
        self.school_year_var.set("Select")  # Empty default value
        ctk.CTkLabel(selection_frame, text="School Year:", font=("Helvetica", 15)).pack(side=tk.LEFT, padx=5)
        school_year_option = ctk.CTkOptionMenu(
            selection_frame, 
            variable=self.school_year_var, 
            values=school_years,
            fg_color="white", 
            button_color="white", 
            button_hover_color="#707070", 
            text_color="black", 
            dropdown_fg_color="white", 
            dropdown_text_color="black", 
            dropdown_hover_color="#707070"
        )
        school_year_option.pack(side=tk.LEFT, padx=5)

        year_var = ctk.StringVar()
        year_var.set("Select")  
        ctk.CTkLabel(selection_frame, text="Year Level:", font=("Helvetica", 15)).pack(side=tk.LEFT, padx=5)
        year_option = ctk.CTkOptionMenu(selection_frame, variable=year_var, values=["1st Year", "2nd Year", "3rd Year", "4th Year"], fg_color="white", button_color="white", button_hover_color="#707070", text_color="black", dropdown_fg_color="white", dropdown_text_color="black", dropdown_hover_color="#707070")
        year_option.pack(side=tk.LEFT, padx=5)

        # Dropdown for selecting the semester with transparent style
        semester_var = ctk.StringVar()
        semester_var.set("Select")  
        ctk.CTkLabel(selection_frame, text="Semester:", font=("Helvetica", 15)).pack(side=tk.LEFT, padx=5)
        semester_option = ctk.CTkOptionMenu(selection_frame, variable=semester_var, values=["1st Semester", "2nd Semester"], fg_color="white", button_color="white", button_hover_color="#707070", text_color="black", dropdown_fg_color="white", dropdown_text_color="black", dropdown_hover_color="#707070")
        semester_option.pack(side=tk.LEFT, padx=5)

        import_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/import.png")
        self.import_icon = ctk.CTkImage(light_image=import_icon, dark_image=import_icon, size=(30, 30))

        # Add label for the import dropdown
        ctk.CTkLabel(selection_frame, text="Import:", font=("Helvetica", 15)).pack(side=tk.LEFT, padx=5)

        # Create the import dropdown
        self.import_var = ctk.StringVar(value="Select")
        import_dropdown = ctk.CTkOptionMenu(
            selection_frame,
            variable=self.import_var,
            values=["Regular", "Irregular"],
            fg_color="white",
            button_color="white",
            button_hover_color="#707070",
            text_color="black",
            dropdown_fg_color="white",
            dropdown_text_color="black",
            dropdown_hover_color="#707070",
            command=lambda choice: self.open_file_dialog(year_var.get(), semester_var.get(), choice)
        )
        import_dropdown.pack(side=tk.LEFT, padx=5)

        save_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/save.png")
        self.save_icon =ctk.CTkImage(light_image=save_icon, dark_image=save_icon, size=(30, 30))
        self.save_button = ctk.CTkButton(selection_frame, text="Save Grade", image=self.save_icon,state="disabled", command=self.on_save_button_click, **button_style)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # Create buttons frame with template download
        self.back_frame = ctk.CTkFrame(self)
        self.back_frame.place(x=11, y=70)

        # Template download dropdown style
        template_style = {
            "fg_color": "white",
            "button_color": "#F0F0F0",
            "button_hover_color": "#E0E0E0",
            "text_color": "black",
            "dropdown_fg_color": "white",
            "dropdown_text_color": "black",
            "dropdown_hover_color": "#E0E0E0",
            "width": 200,
            "corner_radius": 6
        }

        self.db_handler.cursor.execute("SELECT file_name FROM templates")
        templates = [row[0] for row in self.db_handler.cursor.fetchall()]

        # Add template download dropdown
        self.template_var = ctk.StringVar(value="Download Grading Sheet")
        template_dropdown = ctk.CTkOptionMenu(
            self.back_frame,
            variable=self.template_var,
            values=templates,
            command=self.download_template,
            **template_style
        )
        template_dropdown.pack(side=tk.RIGHT, padx=5)
        # Add upload template button
        upload_icon= Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/upload.png")
        self.upload_icon= ctk.CTkImage(light_image=upload_icon, dark_image=upload_icon, size=(30, 30))
        upload_button = ctk.CTkButton(
            self.back_frame, image=self.upload_icon,
            text="Upload Templates",
            command=self.upload_templates,
            **button_style
        )
        upload_button.pack(side=tk.RIGHT, padx=5)

        edit_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/edit.png")
        self.edit_icon = ctk.CTkImage(light_image=edit_icon, dark_image=edit_icon, size=(30, 30))
        view_edit_button = ctk.CTkButton(
            self.back_frame, 
            text="View and Edit", 
            image=self.edit_icon,
            command=self.open_view_edit_window, 
            **button_style
        )
        view_edit_button.pack(side=tk.RIGHT, padx=5)

        form_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/form.png")
        self.form_icon = ctk.CTkImage(light_image=form_icon, dark_image=form_icon, size=(30, 30))
        completion_button = ctk.CTkButton(
            self.back_frame, 
            text="Completion Form",
            image=self.form_icon, 
            command=self.open_completion_form, 
            **button_style
        )
        completion_button.pack(side=tk.RIGHT, padx=5)

        # Rest of your widgets remain the same
        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=200, mode="indeterminate", maximum=100)
        self.progress_bar.pack(pady=5)
        for i in range(101):
            self.progress_bar['value'] = i
            self.update_idletasks()
            time.sleep(0.07)
        self.progress_bar.pack_forget()
        back_button_style = {**button_style,"width": 32 }
        
        back_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/back.png")
        self.back_icon = ctk.CTkImage(light_image=back_icon, dark_image=back_icon, size=(20, 20))
        ctk.CTkButton(self.back_frame, text="Back", image=self.back_icon ,command=self.master.show_main_menu, **back_button_style).pack(side=tk.LEFT)

    def open_completion_form(self):
        # Create a new top-level window for the completion form
        self.completion_window = ctk.CTkToplevel(self)
        self.completion_window.title("Completion Form")
        self.completion_window.geometry("500x400")
        self.completion_window.grab_set()

        def fetch_student_details(event=None):
            """Function to fetch and auto-fill student details"""
            id_no = id_var.get().strip()
            if not id_no:
                return
            
            try:
                # First check if student exists in appraised_curriculum
                self.db_handler.cursor.execute("""
                    SELECT DISTINCT id_no, last_name, first_name, middle_name 
                    FROM appraised_curriculum 
                    WHERE id_no = %s
                    LIMIT 1
                """, (id_no,))
                appraised_student = self.db_handler.cursor.fetchone()
                
                # If found in appraised_curriculum, use those details
                if appraised_student:
                    self.current_student_source = 'appraised'
                    last_name_var.set(appraised_student[1])
                    first_name_var.set(appraised_student[2])
                    middle_name_var.set(appraised_student[3] if appraised_student[3] else '')
                    
                    # Get available courses for this student
                    self.db_handler.cursor.execute("""
                        SELECT course_no, grades 
                        FROM appraised_curriculum 
                        WHERE id_no = %s AND (grades IS NULL OR grades = '' OR grades = 'INC')
                    """, (id_no,))
                    
                    available_courses = self.db_handler.cursor.fetchall()
                    if not available_courses:
                        messagebox.showinfo("Info", 
                            "This student has no incomplete courses in appraised curriculum.")
                    
                    course_no_entry.focus()
                    return
                
                # If not in appraised_curriculum, check student_information
                self.db_handler.cursor.execute("""
                    SELECT ID_NO, LAST_NAME, FIRST_NAME, MIDDLE_NAME 
                    FROM student_information
                    WHERE ID_NO = %s
                """, (id_no,))
                student = self.db_handler.cursor.fetchone()
                
                if student:
                    self.current_student_source = 'regular'
                    last_name_var.set(student[1])
                    first_name_var.set(student[2])
                    middle_name_var.set(student[3] if student[3] else '')
                    course_no_entry.focus()
                else:
                    # If not found in student_information, check students table
                    self.db_handler.cursor.execute("""
                        SELECT ID_NO, LAST_NAME, FIRST_NAME, MIDDLE_NAME 
                        FROM students
                        WHERE ID_NO = %s
                    """, (id_no,))
                    student = self.db_handler.cursor.fetchone()
                    
                    if student:
                        # Even if found in students table, check if they exist in appraised_curriculum
                        self.db_handler.cursor.execute("""
                            SELECT id_no FROM appraised_curriculum WHERE id_no = %s LIMIT 1
                        """, (id_no,))
                        is_appraised = self.db_handler.cursor.fetchone() is not None
                        
                        if is_appraised:
                            self.current_student_source = 'appraised'
                            messagebox.showinfo("Info", 
                                "This student exists in appraised curriculum. Only existing incomplete courses can be updated.")
                        else:
                            self.current_student_source = 'regular'
                        
                        last_name_var.set(student[1])
                        first_name_var.set(student[2])
                        middle_name_var.set(student[3] if student[3] else '')
                        course_no_entry.focus()
                    else:
                        self.current_student_source = None
                        messagebox.showwarning("Warning", "No matching student found")
                        id_var.set('')  # Clear ID field
                        return
                    
            except Exception as e:
                print(f"Error fetching student details: {e}")
                messagebox.showerror("Error", "Failed to fetch student details")
                
        # Frame for input fields
        input_frame = ctk.CTkFrame(self.completion_window)
        input_frame.pack(pady=20)

        # Create StringVars
        id_var = ctk.StringVar()
        last_name_var = ctk.StringVar()
        first_name_var = ctk.StringVar()
        middle_name_var = ctk.StringVar()
        course_no_var = ctk.StringVar()
        grade_var = ctk.StringVar()
        def validate_id(new_value):
            # Allow only digits and hyphens
            return new_value == "" or all(char.isdigit() or char == '-' for char in new_value)

        # Labels and Entry fields
        ctk.CTkLabel(input_frame, text="ID No.").grid(row=0, column=0, padx=5, pady=5)
        id_entry = ctk.CTkEntry( input_frame,  width=200,  textvariable=id_var, validate="key",validatecommand=(input_frame.register(validate_id), '%P'))
        id_entry.grid(row=0, column=1, padx=5, pady=5)

        # Bind the fetch_student_details function to ID entry
        id_entry.bind('<FocusOut>', fetch_student_details)  # When focus leaves the field
        id_entry.bind('<Return>', fetch_student_details)    # When Enter is pressed

        # Last Name field (read-only)
        ctk.CTkLabel(input_frame, text="Last Name").grid(row=1, column=0, padx=5, pady=5)
        last_name_entry = ctk.CTkEntry(input_frame, width=200, textvariable=last_name_var, state="readonly")
        last_name_entry.grid(row=1, column=1, padx=5, pady=5)

        # First Name field (read-only)
        ctk.CTkLabel(input_frame, text="First Name").grid(row=2, column=0, padx=5, pady=5)
        first_name_entry = ctk.CTkEntry(input_frame, width=200, textvariable=first_name_var, state="readonly")
        first_name_entry.grid(row=2, column=1, padx=5, pady=5)

        # Middle Name field (read-only)
        ctk.CTkLabel(input_frame, text="Middle Name").grid(row=3, column=0, padx=5, pady=5)
        middle_name_entry = ctk.CTkEntry(input_frame, width=200, textvariable=middle_name_var, state="readonly")
        middle_name_entry.grid(row=3, column=1, padx=5, pady=5)
        

        def validate_course_no(new_value):
            # Allow only letters, numbers, and spaces
            return new_value == "" or all(char.isalnum() or char.isspace() for char in new_value)

        def suggest_courses(event=None):
            current_input = course_no_entry.get().strip().upper()
            id_no = id_var.get().strip()
            
            if not current_input:
                suggestion_listbox.place_forget()
                return

            try:
                # First check if student is in appraised_curriculum
                self.db_handler.cursor.execute("""
                    SELECT DISTINCT id_no FROM appraised_curriculum 
                    WHERE id_no = %s
                """, (id_no,))
                is_appraised = self.db_handler.cursor.fetchone() is not None

                if is_appraised:
                    # Get courses from appraised_curriculum for this student that have no grades
                    self.db_handler.cursor.execute("""
                        SELECT DISTINCT course_no 
                        FROM appraised_curriculum 
                        WHERE id_no = %s 
                        AND (grades IS NULL OR grades = '' OR grades = 'INC')
                    """, (id_no,))
                    available_courses = [row[0] for row in self.db_handler.cursor.fetchall()]
                else:
                    # Get courses from curriculum_regular for regular students
                    self.db_handler.cursor.execute("""
                        SELECT DISTINCT Course_No 
                        FROM curriculum_regular
                    """)
                    available_courses = [row[0] for row in self.db_handler.cursor.fetchall()]

                # Use fuzzy matching to find similar courses
                matches = process.extract(current_input, available_courses, limit=5)
                suggestions = [match[0] for match in matches if match[1] > 60]

                if suggestions:
                    suggestion_listbox.delete(0, tk.END)
                    for suggestion in suggestions:
                        suggestion_listbox.insert(tk.END, suggestion)
                    
                    # Position the suggestion listbox
                    entry_x = course_no_entry.winfo_rootx() - input_frame.winfo_rootx()
                    entry_y = course_no_entry.winfo_rooty() - input_frame.winfo_rooty()
                    
                    suggestion_listbox.lift()
                    suggestion_listbox.place(
                        x=entry_x, 
                        y=entry_y + course_no_entry.winfo_height(),
                        width=course_no_entry.winfo_width(),
                        relx=0,
                        rely=0
                    )
                else:
                    suggestion_listbox.place_forget()
                    
            except Exception as e:
                print(f"Error fetching course suggestions: {e}")
                suggestion_listbox.place_forget()
                
                # Create suggestion frame
        suggestion_frame = ctk.CTkFrame(
            input_frame,
            fg_color="white",
            border_width=1,
            border_color="grey",
            width=200  # Will be adjusted to match entry width
        )
        def handle_up_down_keys(event):
            if not suggestion_frame.winfo_ismapped():  # If suggestions are not visible
                return
            
            suggestions = suggestion_frame.winfo_children()
            if not suggestions:
                return

            # Update current index based on key press
            if event.keysym == 'Up':
                self.current_suggestion_index = (self.current_suggestion_index - 1) if self.current_suggestion_index > 0 else len(suggestions) - 1
            elif event.keysym == 'Down':
                self.current_suggestion_index = (self.current_suggestion_index + 1) if self.current_suggestion_index < len(suggestions) - 1 else 0

            # Update button appearances
            for i, button in enumerate(suggestions):
                if i == self.current_suggestion_index:
                    button.configure(fg_color="#0078D7", text_color="white")
                else:
                    button.configure(fg_color="transparent", text_color="black")

            # If Enter is pressed, select the highlighted suggestion
            if event.keysym == 'Return' and self.current_suggestion_index >= 0:
                selected_button = suggestions[self.current_suggestion_index]
                select_suggestion(selected_button.cget("text"))
                return "break" 
            
        def select_suggestion(selected_value):
            course_no_var.set(selected_value)
            suggestion_frame.place_forget()
            grade_entry.focus() 

        def use_suggestion(event):
            selection = suggestion_listbox.get(suggestion_listbox.curselection())
            course_no_var.set(selection)
            suggestion_listbox.place_forget()
            grade_entry.focus()  # Move focus to grade entry

        def hide_suggestions(event=None):
            # Delay hiding to allow for selection
            self.after(100, suggestion_listbox.place_forget)

        # Create suggestion listbox
        suggestion_listbox = tk.Listbox(
            input_frame,
            height=5,
            selectmode=tk.SINGLE,
            font=("Helvetica", 10),
            bg="white",
            fg="black"
        )
        suggestion_listbox.bind('<<ListboxSelect>>', use_suggestion)

        # Course No field
        ctk.CTkLabel(input_frame, text="Course No.").grid(row=4, column=0, padx=5, pady=5)
        course_no_entry = ctk.CTkEntry( input_frame,  width=200,  textvariable=course_no_var, validate="key", validatecommand=(input_frame.register(validate_course_no), '%P'))
        course_no_entry.grid(row=4, column=1, padx=5, pady=5)

        # Bind events to course number entry
        course_no_entry.bind('<Up>', handle_up_down_keys)
        course_no_entry.bind('<Down>', handle_up_down_keys)
        course_no_entry.bind('<KeyRelease-Return>', handle_up_down_keys)
        course_no_entry.bind('<KeyRelease>', suggest_courses)
        course_no_entry.bind('<FocusOut>', hide_suggestions)
        course_no_entry.bind('<Return>', lambda e: grade_entry.focus())
        
        def validate_grade(new_value):
            # List of valid grades
            valid_grades = ['1.00', '1.25', '1.50', '1.75', '2.00', '2.25', '2.50', '2.75', '3.00', '5.00', '']
            
            # Allow empty string (for backspace/delete) and only valid grades
            return new_value in valid_grades or any(valid.startswith(new_value) for valid in valid_grades)
        
        ctk.CTkLabel(input_frame, text="Grade").grid(row=5, column=0, padx=5, pady=5)
        grade_entry = ctk.CTkEntry(input_frame, width=200, textvariable=grade_var,validate="key",validatecommand=(input_frame.register(validate_grade), '%P'))
        grade_entry.grid(row=5, column=1, padx=5, pady=5)

        def on_grade_enter(event):
            grade_entry.configure(border_color="black")
            add_grade()
            # Reset focus to first entry and clear all fields
            id_entry.focus()
            id_entry.configure(border_color="blue")
            for var in [id_var, last_name_var, first_name_var, middle_name_var, course_no_var, grade_var]:
                var.set("")
            return "break"
        
        grade_entry.bind('<Return>', on_grade_enter)

        # Set initial focus and highlight
        id_entry.focus()
        id_entry.configure(border_color="blue")

        # Keep the Treeview as is
        columns = ("ID_NO", "Last Name", "First Name", "Middle Name", "Course No.", "Grade")
        self.grade_tree = ttk.Treeview(self.completion_window, columns=columns, show="headings")
        
        for col in columns:
            self.grade_tree.heading(col, text=col)
            self.grade_tree.column(col, anchor="center", width=100)
        
        self.grade_tree.pack(pady=20, padx=20, expand=True, fill="both")

        # Year-Semester dropdown
        year_levels = ["1.1", "1.2", "2.1", "2.2", "3.1", "3.2", "4.1", "4.2"]
        ctk.CTkLabel(input_frame, text="Year Level:").grid(row=6, column=0, padx=5, pady=5)
        year_level_var = ctk.StringVar(value=year_levels[0])
        year_level_dropdown = ctk.CTkOptionMenu(input_frame,variable=year_level_var, values=year_levels,fg_color="white",button_color="white",button_hover_color="#707070",text_color="black",dropdown_fg_color="white",dropdown_text_color="black",dropdown_hover_color="#707070")
        year_level_dropdown.grid(row=6, columns=3, padx=5, pady=5)
        
        # School Year dropdown (now below year level)
        school_years = []
        for year in range(2020, 2100):
            school_years.append(f"{year}-{year+1}")
        
        ctk.CTkLabel(input_frame, text="School Year:").grid(row=7, column=0, padx=5, pady=5)
        school_year_var = ctk.StringVar(value=school_years[0])
        school_year_dropdown = ctk.CTkOptionMenu(
            input_frame,
            variable=school_year_var,
            values=school_years,
            fg_color="white",
            button_color="white",
            button_hover_color="#707070",
            text_color="black",
            dropdown_fg_color="white",
            dropdown_text_color="black",
            dropdown_hover_color="#707070"
        )
        school_year_dropdown.grid(row=7, column=1, padx=5, pady=5)

        # Button frame
        button_frame = ctk.CTkFrame(self.completion_window, fg_color="transparent")
        button_frame.place(x=890,y=212)

        # Buttons with consistent styling
        button_style = {
            "fg_color": "transparent",
            "hover_color": "#707070",
            "text_color": "black",
            "width": 120,
            "height": 32,
            "border_width": 1,
            "border_color": "black"
        }

        # Keep all the original functions
        def add_grade():
            id_no = id_entry.get().strip()
            last_name = last_name_entry.get().strip()
            first_name = first_name_entry.get().strip()
            middle_name = middle_name_entry.get().strip()
            course_no = course_no_entry.get().strip().upper()
            grade = grade_entry.get().strip()

            if not hasattr(self, 'current_student_source') or not self.current_student_source:
                messagebox.showerror("Error", "Please enter a valid student ID first")
                return
                
            if self.current_student_source == 'appraised':
                # Verify course exists and is incomplete in appraised_curriculum
                course_no = course_no_entry.get().strip().upper()
                id_no = id_var.get().strip()
                
                self.db_handler.cursor.execute("""
                    SELECT grades FROM appraised_curriculum 
                    WHERE id_no = %s AND course_no = %s
                    AND (grades IS NULL OR grades = '' OR grades = 'INC')
                """, (id_no, course_no))
                
                if not self.db_handler.cursor.fetchone():
                    messagebox.showwarning("Warning", 
                        "This course either doesn't exist or already has a grade in appraised curriculum")
                    return

            if not all([id_no, last_name, first_name, course_no, grade]):
                messagebox.showerror("Error", "Please fill in all required fields")
                return

            # Insert with separate name fields
            self.grade_tree.insert("", "end", values=(id_no, last_name, first_name, middle_name, course_no, grade))

            # Clear entries after insertion
            for entry in [id_entry, last_name_entry, first_name_entry, middle_name_entry, course_no_entry, grade_entry]:
                entry.delete(0, 'end')

        def delete_grade():
            selected_item = self.grade_tree.selection()
            if not selected_item:
                messagebox.showwarning("Warning", "Please select a grade to delete")
                return
            
            self.grade_tree.delete(selected_item)

        def save_grades(event=None):
            """
            Save grades with comprehensive validation and multi-table checking
            """
            grades_data = []
            invalid_students = []
            appraised_updates = []

            # Collect grades data and validate student existence
            for item in self.grade_tree.get_children():
                values = self.grade_tree.item(item)['values']
                id_no = values[0]
                course_no = values[4]
                grade = values[5]
                
                # Check student existence and source
                student_source = self.db_handler.check_student_source(id_no)
                
                if student_source == 'not_found':
                    invalid_students.append(id_no)
                    continue
                
                # Handle students from appraised curriculum or students table (irregular)
                if student_source in ['appraised', 'students']:
                    try:
                        # Check if the course exists in appraised_curriculum for this student
                        self.db_handler.cursor.execute("""
                            SELECT id_no, course_no, grades FROM appraised_curriculum 
                            WHERE id_no = %s AND course_no = %s AND (grades IS NULL OR grades = '' OR grades = 'INC')
                        """, (id_no, course_no))
                        
                        incomplete_course = self.db_handler.cursor.fetchone()
                        
                        if incomplete_course:
                            # Add to appraised updates if course exists and has no grade
                            appraised_updates.append({
                                'id_no': id_no,
                                'course_no': course_no,
                                'grade': grade
                            })
                        else:
                            # Check if course exists with a grade
                            self.db_handler.cursor.execute("""
                                SELECT id_no FROM appraised_curriculum 
                                WHERE id_no = %s AND course_no = %s
                            """, (id_no, course_no))
                            exists_with_grade = self.db_handler.cursor.fetchone() is not None
                            if exists_with_grade:
                                messagebox.showwarning("Warning", 
                                    f"Course {course_no} for student {id_no} already has a grade in appraised curriculum.")
                                continue
                            else:
                                messagebox.showwarning("Warning", 
                                    f"Course {course_no} for student {id_no} does not exist in appraised curriculum.")
                                continue
                    except Exception as e:
                        print(f"Error checking appraised curriculum: {e}")
                        continue
                else:
                    # Regular student grades
                    grades_data.append({
                        'ID_NO': id_no,
                        'Last Name': values[1],
                        'First Name': values[2],
                        'Middle Name': values[3],
                        'Course No.': course_no,
                        'Grade': grade
                    })

            # Handle invalid students
            if invalid_students:
                error_message = f"The following student IDs are not found in any database:\n{', '.join(invalid_students)}"
                response = messagebox.askyesno(
                    "Invalid Students", 
                    f"{error_message}\n\nDo you want to proceed with saving only valid students?"
                )
                if not response:
                    return

            # Check if there are any valid grades to save
            if not grades_data and not appraised_updates:
                messagebox.showerror("Error", "No valid grades to save!")
                return

            # Get additional context
            year_level = year_level_var.get()
            school_year = school_year_var.get()

            # Attempt to save grades
            try:
                # Save regular grades
                if grades_data:
                    grades_df = pd.DataFrame(
                        grades_data, 
                        columns=["ID_NO", "Last Name", "First Name", "Middle Name", "Course No.", "Grade"]
                    )
                    self.db_handler.save_manual_grades(grades_df, year_level, school_year)

                # Update existing incomplete grades in appraised_curriculum
                if appraised_updates:
                    appraised_df = pd.DataFrame(
                        appraised_updates,
                        columns=["id_no", "course_no", "grade"]
                    )
                    self.db_handler.update_appraised_grades(appraised_df)

                # Clear the grade tree after successful save
                for item in self.grade_tree.get_children():
                    self.grade_tree.delete(item)

                # Show success message
                success_message = "Grades saved successfully!\n\n"
                if grades_data:
                    success_message += f"Regular grades: {len(grades_data)}\n"
                if appraised_updates:
                    success_message += f"Updated grades in appraised curriculum: {len(appraised_updates)}"

                messagebox.showinfo("Success", success_message)

            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save grades: {str(e)}")


        # Add buttons with the new style
        ctk.CTkButton(button_frame, text="Add Grade", command=add_grade, **button_style).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(button_frame,text="Delete Grade", command=delete_grade, **button_style).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(button_frame,text="Save Grades",command=save_grades,**button_style).pack(side=tk.LEFT, padx=5)

    def open_file_dialog(self, year, semester, choice):
        # Open a file dialog to select a CSV file
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            if choice == "Regular":
                self.import_grading_sheet(file_path, year, semester)
            elif choice == "Irregular":
                self.import_irregular_grading_sheet(file_path, year, semester)

    def import_grading_sheet(self, file_path, year, semester):
        if not self.school_year_var.get():
            messagebox.showerror("Error", "Please select a School Year")
            return False
        
        cache_key = f"grading_sheet_{year}_{semester}"
        
        try:
            # Check cache size before loading new data
            if self.get_cache_size() > self.cache_size_limit * 0.9:  # 90% of limit
                self.manage_cache_memory()

            grading_data = self.get_cached_data(cache_key, pd.read_csv, file_path)

            if not grading_data.empty:
                self.grading_data = grading_data
                self.year = year
                self.semester = semester
                self.school_year = self.school_year_var.get()  # Store school year
                self.display_grading_data(grading_data)
                self.save_button.configure(state="normal")

                threading.Thread(target=self.process_students, args=(grading_data, year, semester, self.school_year), daemon=True).start()
                
                return True
            
            return False

        except MemoryError:
            # Handle out of memory situation
            self.clear_cache()
            ctk.CTkMessageBox(title="Memory Error", message="Not enough memory. Cache has been cleared. Please try again.").pack()
            return False
        except Exception as e:
            ctk.CTkMessageBox(title="Error", message=f"Error loading file: {e}").pack()
            return False
        
    def import_irregular_grading_sheet(self, file_path, year, semester):
        if not self.school_year_var.get():
            messagebox.showerror("Error", "Please select a School Year")
            return False 

        try:
            grading_data = pd.read_csv(file_path)

            if not grading_data.empty:
                self.grading_data = grading_data
                self.year = year
                self.semester = semester
                self.school_year = self.school_year_var.get()  # Store school year
                self.display_grading_data(grading_data)
                self.save_button.configure(state="normal")

                return True

            return False

        except MemoryError:
            # Handle out of memory situation
            self.clear_cache()
            ctk.CTkMessageBox(title="Memory Error", message="Not enough memory. Cache has been cleared. Please try again.").pack()
            return False
        except Exception as e:
            ctk.CTkMessageBox(title="Error", message=f"Error loading file: {e}").pack()
            return False
        

    def get_cache_size(self):
        """Calculate current cache size in bytes"""
        return sys.getsizeof(self.cache_data)

    def is_cache_expired(self, key):
        """Check if cached item has expired"""
        if key not in self.cache_timestamps:
            return True
        return datetime.now() - self.cache_timestamps[key] > self.cache_ttl

    def manage_cache_memory(self):
        """Manage cache size and remove expired items"""
        current_size = self.get_cache_size()
        
        # Remove expired items first
        expired_keys = [
            key for key in list(self.cache_data.keys())
            if self.is_cache_expired(key)
        ]
        for key in expired_keys:
            self.remove_from_cache(key)

        # If still over limit, remove oldest items
        if self.get_cache_size() > self.cache_size_limit:
            sorted_items = sorted(
                self.cache_timestamps.items(),
                key=lambda x: x[1]
            )
            while self.get_cache_size() > self.cache_size_limit and sorted_items:
                oldest_key = sorted_items.pop(0)[0]
                self.remove_from_cache(oldest_key)

        # Force garbage collection
        gc.collect()

    def remove_from_cache(self, key):
        """Remove item from cache and timestamps"""
        if key in self.cache_data:
            del self.cache_data[key]
        if key in self.cache_timestamps:
            del self.cache_timestamps[key]

    def get_cached_data(self, key, fetch_function, *args):
        """Get data from cache with memory management"""
        try:
            # Check if data exists and is not expired
            if key in self.cache_data and not self.is_cache_expired(key):
                return self.cache_data[key]

            # Fetch new data
            data = fetch_function(*args)
            
            # Manage memory before adding new data
            self.manage_cache_memory()
            
            # Store data and timestamp
            self.cache_data[key] = data
            self.cache_timestamps[key] = datetime.now()
            
            return data
            
        except Exception as e:
            print(f"Cache error for key {key}: {e}")
            # If cache fails, fetch directly
            return fetch_function(*args)

    def get_student_info(self, student_id):
        """Get cached student information"""
        cache_key = f"student_info_{student_id}"
        return self.get_cached_data(
            cache_key,
            self.db_handler.get_student_info_by_id,
            student_id
        )

    def get_course_info(self, course_id):
        """Get cached course information"""
        cache_key = f"course_info_{course_id}"
        return self.get_cached_data(
            cache_key,
            self.db_handler.get_course_info,
            course_id
        )

    def process_students(self, grading_data, year, semester, school_year):
        cache_key = f"processed_students_{year}_{semester}"
        processed_results = []
        
        if cache_key in self.cache_data:
            return self.cache_data[cache_key]
        
        try:
            self.status_label.configure(text="Saving Grades and Updating Student Status...")
            self.progress_bar.pack()
            self.progress_bar.start()

            # Save grading data with school year
            success = self.db_handler.save_grading_data(
                grading_data=grading_data,
                year=year,
                semester=semester,
                school_year=school_year
            )

            if not success:
                messagebox.showerror("Error", "Failed to save grades to database")
                return []

            # Get and cache student information
            student_info = self.get_cached_data(
                "all_student_info",
                self.db_handler.get_student_info
            )

            total_students = len(grading_data)
            processed_students = 0

            # Define student info columns
            student_info_columns = ['ID_NO', 'LAST_NAME', 'FIRST_NAME', 'MIDDLE_NAME']
            
            # Get course columns (everything except student info)
            course_columns = [col for col in grading_data.columns if col not in student_info_columns]

            for index, row in grading_data.iterrows():
                student_id = row['ID_NO']
                last_name = row['LAST_NAME']
                first_name = row['FIRST_NAME']
                middle_name = row.get('MIDDLE_NAME', '')

                # Check and update student year level
                try:
                    new_yr = self.db_handler.update_student_yr(student_id)
                    if new_yr:
                        print(f"Student {student_id} ({last_name}, {first_name}) promoted to Year {new_yr}")
                except Exception as e:
                    print(f"Error updating year level for student {student_id}: {e}")

                incomplete_courses = []

                # Check each course grade
                for course_code in course_columns:
                    grade = str(row[course_code]).strip().upper() if pd.notna(row[course_code]) else ''
                    
                    # Check if grade is incomplete or missing
                    if pd.isna(row[course_code]) or grade == '' or grade == 'INC':
                        incomplete_courses.append({
                            'course_code': course_code,
                            'grade': grade
                        })

                if incomplete_courses:
                    student_data = student_info[student_info['ID_NO'] == student_id]
                    if not student_data.empty:
                        student_email = student_data['EMAIL_ADDRESS'].values[0]
                        if student_email:
                            # Extract just the course codes for the email
                            course_list = [course['course_code'] for course in incomplete_courses]
                            
                            self.send_email(
                                student_email=student_email,
                                last_name=last_name,
                                first_name=first_name,
                                middle_name=middle_name,
                                student_id=student_id,
                                missing_courses=course_list,
                                notification_type="Not Complete"
                            )

                processed_students += 1
                self.update_status(f"Processed {processed_students}/{total_students} students")
                
                # Cache individual student results with year update info
                processed_results.append({
                    'student_id': student_id,
                    'last_name': last_name,
                    'first_name': first_name,
                    'middle_name': middle_name,
                    'incomplete_courses': incomplete_courses,
                    'year_updated': new_yr if 'new_yr' in locals() else None
                })

            self.cache_data[cache_key] = processed_results
            self.update_status("All students processed and year levels updated!", final=True)

        except Exception as e:
            print(f"Error in process_students: {e}")
            messagebox.showerror("Error", f"An error occurred while processing students: {e}")
        finally:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()

        return processed_results

    def clear_cache(self):
        """Clear cache and force garbage collection"""
        self.cache_data.clear()
        self.cache_timestamps.clear()
        gc.collect()

    def monitor_memory_usage(self):
        """Monitor memory usage and manage cache if needed"""
        try:
            if self.get_cache_size() > self.cache_size_limit * 0.8:  # 80% threshold
                self.manage_cache_memory()
        except Exception as e:
            print(f"Memory monitoring error: {e}")

    def refresh_data(self):
        """Force refresh of cached data with memory management"""
        self.monitor_memory_usage()
        self.clear_cache()
        if hasattr(self, 'year') and hasattr(self, 'semester'):
            return self.import_grading_sheet(
                self.current_file_path,
                self.year,
                self.semester
            )

    def send_email(self, student_email, last_name, first_name, middle_name, student_id, missing_courses, notification_type):
        try:
            # Format name for display only when needed
            display_name = f"{last_name} {first_name}"
            if middle_name:
                display_name += f" {middle_name}"

            subject = f"Notification: Incomplete Grades for {display_name} (ID: {student_id})"
            body = f"Dear {display_name},\n\nThis is regarding your grades for the following courses:\n\n"

            if notification_type == "Not Complete":
                body += "You have incomplete grades for the following courses:\n\n"
            elif notification_type == "Failed":
                body += "You have failed grades for the following courses:\n\n"
            
            for course in missing_courses:
                body += f"- {course}\n"

            body += "\nPlease contact your professor/instructor to complete the requirements.\n\nRegards,\nComputer Studies Department"

            msg = MIMEMultipart()
            msg['From'] = SMTP_EMAIL
            msg['To'] = student_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.set_debuglevel(1)
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(SMTP_EMAIL, student_email, text)
            server.quit()

            # Use display_name only for messages
            messagebox.showinfo("Email Sent", f"Email has been successfully sent to {display_name} (ID: {student_id}).")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send email to {student_email}. Error: {e}")
            return False

    def update_status(self, message, final=False):
        self.status_label.configure(text=message)
        if final:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
        self.master.update_idletasks()

    def on_save_button_click(self):
        try:
            if not self.school_year_var.get():
                messagebox.showerror("Error", "Please select a School Year")
                return
            
            import_choice = self.import_var.get()  # Get the import choice
            
            if not hasattr(self, 'grading_data'):
                messagebox.showerror("Error", "No grading data loaded")
                return

            # Clean the DataFrame before saving
            clean_data = self.grading_data.copy()
            
            # Clean column names
            clean_data.columns = clean_data.columns.str.strip()
            
            # Clean data values and trim spaces
            for col in clean_data.columns:
                clean_data[col] = clean_data[col].apply(
                    lambda x: str(x).strip().upper() if pd.notna(x) else ''
                )
                # Trim spaces for grades specifically
                if col in ['Grade']:
                    clean_data[col] = clean_data[col].str.replace(r'\s+', '', regex=True)
            
            # Determine if the data is for regular or irregular students
            import_choice = self.import_var.get()
            if import_choice == "Select":
                messagebox.showerror("Error", "Please select an import type (Regular or Irregular)")
                return

            if import_choice == "Regular":
                success = self.db_handler.save_grading_data(
                    grading_data=clean_data, 
                    year=self.year, 
                    semester=self.semester,
                    school_year=self.school_year_var.get().strip()
                )

            elif import_choice == "Irregular":
                # Prepare grade data for irregular students
                grade_data = clean_data.copy()
                
                # Add school year to the DataFrame
                grade_data['school_year'] = self.school_year_var.get().strip()

                # Identify course columns (exclude ID column and other columns)
                id_column = 'id_no'
                exclude_columns = ['id_no', 'last_name', 'first_name', 'middle_name']
                course_columns = [col for col in grade_data.columns if col not in exclude_columns]

                # Melt the DataFrame to create a long format
                melted_data = grade_data.melt(
                    id_vars=['id_no', 'school_year'],
                    value_vars=course_columns, 
                    var_name='course_no', 
                    value_name='grades'
                )

                # Replace empty grades with 'INC'
                melted_data['grades'] = melted_data['grades'].apply(lambda x: 'INC' if x == '' or pd.isna(x) else x)

                # Save or update grades for irregular students
                success = self.db_handler.save_irregular_grading_data(
                    melted_data, 
                    year=self.year, 
                    semester=self.semester
                )
            
            if success:
                messagebox.showinfo("Success", "Grades have been successfully saved to the database.")
            else:
                messagebox.showerror("Error", "Failed to save to the database")

        except Exception as e:
            print(f"Error in on_save_button_click: {e}")  # Debug print
            messagebox.showerror("Error", f"Failed to save grades: {e}")
                            
    def display_grading_data(self, grading_data, is_irregular=False):
        if self.data_frame:
            self.data_frame.destroy()

        # Make a copy and clean the data
        clean_data = grading_data.copy()
        
        # Clean up column names by removing any leading/trailing spaces
        clean_data.columns = clean_data.columns.str.strip()
        
        # Remove specific columns if irregular
        if is_irregular:
            columns_to_remove = ['ID_NO', 'LAST_NAME', 'FIRST_NAME', 'MIDDLE_NAME']
            clean_data = clean_data.drop(columns=columns_to_remove, errors='ignore')
        
        # Clean up data values
        for col in clean_data.columns:
            clean_data[col] = clean_data[col].apply(
                lambda x: str(x).strip().upper() if pd.notna(x) else ''
            )
        
        self.data_frame = tk.Frame(self, bg="#008080")
        self.data_frame.pack(expand=True, fill='both', padx=10, pady=10)

        # Get columns directly from the cleaned DataFrame
        columns = list(clean_data.columns)

        # Configure Treeview style for row height
        style = ttk.Style()
        style.configure("Treeview", rowheight=35, font=("Helvetica", 12)) 
        style.configure("Treeview.Heading", font=("Helvetica", 12))

        # Create frame for Treeview and scrollbars
        tree_frame = ctk.CTkFrame(self.data_frame)
        tree_frame.pack(expand=True, fill='both')

        # Create Treeview
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

        # Create vertical scrollbar
        vsb = ctk.CTkScrollbar(tree_frame, orientation="vertical", command=tree.yview)
        vsb.pack(side='right', fill='y')

        # Create horizontal scrollbar
        hsb = ctk.CTkScrollbar(tree_frame, orientation="horizontal", command=tree.xview)
        hsb.pack(side='bottom', fill='x')

        # Configure the Treeview to use both scrollbars
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.pack(expand=True, fill='both')

        # Configure columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor='center', width=100)

        tree.tag_configure('oddrow', background='lightgrey')
        tree.tag_configure('evenrow', background='white')
    
        for index, (_, row) in enumerate(clean_data.iterrows()):
            tag = 'oddrow' if index % 2 == 0 else 'evenrow'
            tree.insert("", "end", values=list(row), tags=(tag,))

        self.grading_data = clean_data  # Store the cleaned DataFrame
        
    def destroy(self):
        """Override destroy method to handle cleanup"""
        try:
            # Clean up all possible windows
            windows_to_cleanup = [
                'view_edit_window',
                'completion_window'  # Added completion window
            ]
            
            for window_name in windows_to_cleanup:
                if hasattr(self, window_name) and getattr(self, window_name) is not None:
                    window = getattr(self, window_name)
                    try:
                        # Destroy all children first
                        for widget in window.winfo_children():
                            try:
                                # Clear any variables
                                if hasattr(widget, '_variable'):
                                    widget._variable = None
                                # Destroy the widget
                                if widget.winfo_exists():
                                    widget.destroy()
                            except:
                                pass
                        
                        # Destroy the window if it still exists
                        if window.winfo_exists():
                            window.destroy()
                    except:
                        pass
                    finally:
                        # Clear the reference
                        setattr(self, window_name, None)
            
            # Clean up variables
            vars_to_cleanup = [
                'year_semester_var',
                'school_year_var',
                'sex_var'
            ]
            
            for var_name in vars_to_cleanup:
                if hasattr(self, var_name):
                    delattr(self, var_name)
            
            # Clear cached data
            if hasattr(self, 'cache_data'):
                self.cache_data.clear()
            if hasattr(self, 'cache_timestamps'):
                self.cache_timestamps.clear()
            
            # Clean up main window widgets
            try:
                for widget in self.winfo_children():
                    if widget.winfo_exists():
                        if hasattr(widget, '_variable'):
                            widget._variable = None
                        widget.destroy()
            except:
                pass
            
            # Finally destroy self
            if self.winfo_exists():
                super().destroy()
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
            try:
                if self.winfo_exists():
                    super().destroy()
            except:
                pass

    def cleanup_view_edit_window(self):
        """Clean up resources when view/edit window is closed"""
        try:
            windows_to_cleanup = [
                'view_edit_window',
                'completion_window'
            ]
            
            for window_name in windows_to_cleanup:
                if hasattr(self, window_name) and getattr(self, window_name) is not None:
                    window = getattr(self, window_name)
                    try:
                        if window.winfo_exists():
                            window.destroy()
                    except:
                        pass
                    finally:
                        setattr(self, window_name, None)
                    
        except Exception as e:
            print(f"Error during window cleanup: {e}")

    def open_view_edit_window(self):
        """Create window for viewing and editing grades"""
        # Create a new top-level window for viewing and editing
        self.view_edit_window = ctk.CTkToplevel(self)
        self.view_edit_window.title("View and Edit Grades")
        self.view_edit_window.geometry("800x600")
        self.view_edit_window.grab_set()
        
        # Create filter frame
        filter_frame = ctk.CTkFrame(self.view_edit_window,bg_color="transparent")
        filter_frame.pack(pady=10, padx=10, fill="x")
        

        # Year Level dropdown
        ctk.CTkLabel(filter_frame, text="Year Level:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        self.year_semester_var = ctk.StringVar(value="Select")
        year_levels = ["1.1", "1.2", "2.1", "2.2", "3.1", "3.2", "4.1", "4.2"]
        year_semester_dropdown = ctk.CTkComboBox(filter_frame,variable=self.year_semester_var,values=year_levels,command=self.update_school_years,state="readonly",text_color="black",bg_color="ghost white",width=120)
        year_semester_dropdown.pack(side=tk.LEFT, padx=5)

        # School Year dropdown
        ctk.CTkLabel(filter_frame, text="School Year:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        self.school_year_var = ctk.StringVar(value="Select")
        self.school_year_dropdown = ctk.CTkComboBox(filter_frame,variable=self.school_year_var,values=["Select Year Level First"],command=self.load_grades,state="readonly",bg_color="ghost white",width=120,text_color="black")
        self.school_year_dropdown.pack(side=tk.LEFT, padx=5)

        # Sex Filter dropdown
        ctk.CTkLabel(filter_frame, text="Sex:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        self.sex_var = ctk.StringVar(value="Select")  # Default to select sexz
        sex_dropdown = ctk.CTkComboBox(filter_frame,variable=self.sex_var,values=["M", "F"],command=self.load_grades,state="readonly",width=80,text_color="black",bg_color="ghost white")
        sex_dropdown.pack(side=tk.LEFT, padx=5)       
        # Add instruction label with some styling
        instruction_label = ctk.CTkLabel(filter_frame,text="(Double Click to Edit Student Grade)",font=("Helvetica", 12, "italic"),text_color="gray40")
        instruction_label.pack(side=tk.LEFT, padx=(10, 5))

        # Create Treeview frame
        self.tree_frame = ctk.CTkFrame(self.view_edit_window)
        self.tree_frame.pack(pady=10, padx=10, fill="both", expand=True)

    def update_school_years(self, selected_year_level):
        """Update school year dropdown based on selected year level"""
        try:
            school_years = self.db_handler.get_available_school_years(selected_year_level)
            self.school_year_dropdown.configure(values=school_years)
            self.school_year_var.set(school_years[0])
        except Exception as e:
            messagebox.showerror("Error", f"Error loading school years: {e}")

    def load_grades(self, selected_school_year=None):
        try:
            year_level = self.year_semester_var.get()
            school_year = self.school_year_var.get()
            sex_filter = self.sex_var.get()
            
            if "Select" in year_level or "Select" in school_year or "No data" in school_year:
                return
            
            # Get all grades data
            grades_info = self.db_handler.get_grades_by_semester(year_level, school_year, sex_filter)
            
            # Create new treeview with dynamic columns
            for widget in self.tree_frame.winfo_children():
                widget.destroy()
            style = ttk.Style()
            style.configure("Treeview", font=("Helvetica", 12),  rowheight=35, background="white", fieldbackground="white", foreground="black") 
            style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"), background="white", foreground="black")
            self.grade_tree = ttk.Treeview(
                self.tree_frame,
                columns=grades_info['columns'],
                show="headings")
            
            # Configure tag colors for alternating rows
            self.grade_tree.tag_configure('oddrow', background='#E8E8E8')  # Light grey
            self.grade_tree.tag_configure('evenrow', background='white')
            
            # Configure columns
            column_widths = {
                "ID_NO": 100,
                "SEX": 50,
                "Student_Name": 200
            }
            
            for col in grades_info['columns']:
                display_name = col.replace('_', ' ').upper()
                self.grade_tree.heading(col, text=display_name)
                self.grade_tree.column(col, width=column_widths.get(col, 100), anchor='center')
            
            # Insert data with alternating row colors
            for i, row in enumerate(grades_info['data']):
                values = [row[col] for col in grades_info['columns']]
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.grade_tree.insert("", "end", values=values, tags=(tag,))
            
            # Add scrollbars
            y_scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.grade_tree.yview)
            x_scrollbar = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.grade_tree.xview)
            self.grade_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
            
            # Pack everything
            y_scrollbar.pack(side="right", fill="y")
            x_scrollbar.pack(side="bottom", fill="x")
            self.grade_tree.pack(side="left", fill="both", expand=True)
            
            # Set up grade editing
            self.setup_grade_editing()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading grades: {e}")

    def setup_grade_editing(self):
        # Bind double-click event to the treeview
        self.grade_tree.bind('<Double-1>', self.on_double_click)
    
    def on_double_click(self, event):
        """Handle double-click event on treeview"""
        # Get the clicked item and column
        region = self.grade_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        
        column = self.grade_tree.identify_column(event.x)
        item = self.grade_tree.identify_row(event.y)
        
        # Only allow editing grade columns (not ID or Name)
        if column in ("#1", "#2"):  # ID_NO and Student_Name columns
            return
        
        # Get column name and current value
        column_name = self.grade_tree["columns"][int(column.replace("#", "")) - 1]
        current_value = self.grade_tree.item(item)['values'][int(column.replace("#", "")) - 1]
        
        # Create popup for editing
        self.create_edit_popup(item, column, column_name, current_value)

    def create_edit_popup(self, item, column, column_name, current_value):
        """Create a popup window for grade editing"""
        popup = ctk.CTkToplevel(self.view_edit_window)
        popup.title("Edit Grade")
        popup.geometry("300x200")
        
        # Center the popup
        popup.geometry(f"+{self.view_edit_window.winfo_x() + 200}+{self.view_edit_window.winfo_y() + 200}")
        
        # Make popup modal
        popup.grab_set()
        
        # Get student info
        values = self.grade_tree.item(item)['values']
        student_id = values[0]
        student_name = values[1]
        
        # Create labels and entry
        ctk.CTkLabel(popup, text=f"Student: {student_name}").pack(pady=5)
        ctk.CTkLabel(popup, text=f"Course: {column_name}").pack(pady=5)
        ctk.CTkLabel(popup, text="Grade Update ").pack(pady=5)
        
        grade_var = ctk.StringVar(value=str(current_value) if current_value else "")
        grade_entry = ctk.CTkEntry(popup, textvariable=grade_var)
        grade_entry.pack(pady=10)
        
        # Create buttons frame
        button_frame = ctk.CTkFrame(popup)
        button_frame.pack(pady=10)
        
        def validate_grade(grade_str):
            """Validate if the grade is in the correct format and range"""
            try:
                grade = float(grade_str)
                valid_grades = [1.00, 1.25, 1.50, 1.75, 2.00, 2.25, 2.50, 2.75, 3.00]
                
                if grade not in valid_grades:
                    messagebox.showerror("Error", 
                        "Invalid grade. Please enter a valid grade:\n"
                        "1.00, 1.25, 1.50, 1.75, 2.00, 2.25, 2.50, 2.75, 3.00")
                    return False
                return True
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
                return False
        
        def save_grade(event=None):
            """Save the grade if it's valid"""
            grade_str = grade_var.get().strip()
            
            # Handle empty grade (if allowed)
            if not grade_str:
                msg = CTkMessagebox(
                    title="Confirm",
                    message="Are you sure you want to clear this grade?",
                    icon="question",
                    option_1="Yes",
                    option_2="No"
                )
                response = msg.ask()
                if response:
                    new_grade = None
                else:
                    return
            else:
                # Validate non-empty grade
                if not validate_grade(grade_str):
                    return
                new_grade = float(grade_str)
            
            try:
                # Update database
                year_level = self.year_semester_var.get()
                school_year = self.school_year_var.get()
                
                success = self.db_handler.update_grade(
                    student_id, 
                    column_name, 
                    new_grade, 
                    year_level, 
                    school_year
                )
                
                if success:
                    # Update treeview
                    values = list(self.grade_tree.item(item)['values'])
                    col_idx = int(column.replace("#", "")) - 1
                    values[col_idx] = new_grade if new_grade is not None else ""
                    self.grade_tree.item(item, values=values)
                    popup.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save grade: {e}")
        
        def cancel(event=None):
            popup.destroy()
        
        # Add Save and Cancel buttons
        save_button = ctk.CTkButton(button_frame, text="Save", command=save_grade)
        save_button.pack(side=tk.LEFT, padx=5)
        
        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=cancel)
        cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to save_grade function
        popup.bind('<Return>', save_grade)
        grade_entry.bind('<Return>', save_grade)
        
        # Bind Escape key to cancel
        popup.bind('<Escape>', cancel)
        
        # Focus the entry widget
        grade_entry.focus_set()

    def download_template(self, choice):
        try:
            # Get the selected template
            template_name = self.template_var.get()

            # Get the file path from the database
            self.db_handler.cursor.execute("SELECT file_data FROM templates WHERE file_name = %s", (template_name,))
            file_data = self.db_handler.cursor.fetchone()

            if file_data:
                # Ask the user to save the file with a custom name
                file_path = filedialog.asksaveasfilename(
                    title="Save Template",
                    defaultextension=".csv",
                    filetypes=[("CSV Files", "*.csv")]
                )

                if file_path:
                    # Save the file to the local file system
                    with open(file_path, 'w') as file:
                        file.write(file_data[0])

                    # Show a success message
                    CTkMessagebox(title="Success", message="Template downloaded successfully!")
                else:
                    # Show a message if the user cancels the save operation
                    CTkMessagebox(title="Info", message="Save operation cancelled.")
            else:
                # Show an error message if the file is not found
                CTkMessagebox(title="Error", message="Failed to download template: Cannot find file path")

        except Exception as e:
            # Log the error and show an error message
            print(f"Error downloading template: {e}")
            CTkMessagebox(title="Error", message="Failed to download template: Unknown error")

    def upload_templates(self):

        # Open file dialog to select multiple CSV files
        file_paths = filedialog.askopenfilenames(
            title="Select CSV Files",
            filetypes=[("CSV Files", "*.csv")]
        )
        
        if file_paths:
            # Call the function in database.py to save the files
            self.db_handler.save_templates_to_database(file_paths)

            CTkMessagebox(title="Success", message="Templates have been uploaded successfully!")