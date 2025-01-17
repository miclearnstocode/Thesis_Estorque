import sys
import threading
import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk
from flask import Flask, jsonify, render_template_string, request
import requests
from database import DatabaseHandler
from PIL import Image
from tkinter import TclError
import re


ctk.set_default_color_theme("green")    
class StudentApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Computer Studies Grades Kiosk")
        self.server_running = False
        self.db_handler = DatabaseHandler()
        self.show_login()
        
    def show_login(self):
        self.clear_frame()
        
        # Add a title label outside the login frame
        title_label = ctk.CTkLabel(self, text="COMPUTER STUDIES GRADES KIOSK", text_color="white",font=("Courier New", 40, "bold"))
        title_label.pack(padx=20,pady=20)

        # Add a label with the text ComScie@2025
        comscie_label = ctk.CTkLabel(self, text="ComScie@2025", text_color="white", font=("Helvetica", 16))
        comscie_label.place(x=10, y=90)

        # Create a frame for the login form
        login_frame = ctk.CTkFrame(self, fg_color="gainsboro", width=200, height=400)
        login_frame.pack(fill="both", expand=True, padx=10, pady=40)
        
        # Load and display the logo
        logo_image = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/Image/Capiz_State_University 2.png")
        logo_image = logo_image.resize((150, 150), Image.LANCZOS)
        logo_photo = ctk.CTkImage(light_image=logo_image, dark_image=logo_image, size=(150, 150))
        logo_label = ctk.CTkLabel(login_frame, image=logo_photo, text="")
        logo_label.pack(pady=30)

        def validate_student_id(event):
            try:
                new_value = self.student_id_entry.get()
                if len(new_value) > 11:
                    new_value = new_value[:11]
                if re.match(r'^[0-9-]*$', new_value):
                    self.student_id_entry.delete(0, 'end')
                    self.student_id_entry.insert(0, new_value)
                    return True
                else:
                    self.student_id_entry.delete(0, 'end')
                    self.student_id_entry.insert(0, re.sub(r'[^0-9-]', '', new_value))
                    return False
            except Exception as e:
                print(f"Validation error: {e}")
                return False
            
        self.student_id_entry = ctk.CTkEntry(login_frame, placeholder_text="Student ID", placeholder_text_color="grey", text_color="black", fg_color="white", width=200, height=39, corner_radius=30)
        self.student_id_entry.pack(pady=10)
        self.student_id_entry.bind('<KeyRelease>', validate_student_id)

        self.password_entry = ctk.CTkEntry(login_frame, placeholder_text="Password", placeholder_text_color="grey", text_color="black",show="*", fg_color="white", width=200, height=39, corner_radius=30)
        self.password_entry.pack(pady=10)

        # Function to toggle password visibility
        def toggle_password():
            if self.password_entry.cget('show') == '*':
                self.password_entry.configure(show='')
                show_password_button.configure(image=hide_icon)
            else:
                self.password_entry.configure(show='*')
                show_password_button.configure(image=show_icon)

        # Load the show/hide icons
        show_icon = ctk.CTkImage(Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/show_icon.png").resize((15, 15), Image.LANCZOS))
        hide_icon = ctk.CTkImage(Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/hide_icon.png").resize((15, 15), Image.LANCZOS))

        # Add a "Show Password" button with an icon
        show_password_button = ctk.CTkButton(login_frame, image=show_icon, text="", width=15, height=15, bg_color="white", fg_color="white",command=toggle_password)
        show_password_button.place(x=720, y=283)  # Adjust the position as needed

        # Bind the Enter key to navigate between the Entry widgets
        self.student_id_entry.bind("<Return>", lambda event: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda event: self.login())

        ctk.CTkButton(login_frame, text="Login", font=("Helvetica", 15, "bold") ,command=self.login, width=100, corner_radius=30).pack(pady=20)
        register_text = "Don't have an account? "
        register_label = ctk.CTkLabel(login_frame, text=register_text, fg_color="gainsboro", text_color="black")
        register_label.place(x=588, y=389)

        # Create a clickable and underlined "Register" label
        register_link = ctk.CTkLabel(login_frame, text="Register", fg_color="gainsboro", text_color="blue", font=("Helvetica", 12, "underline"))
        register_link.place(x=720, y=389)
        register_link.bind("<Button-1>", lambda e: self.show_register())
    
    def show_register(self):
        self.clear_frame()

        # Add a title label outside the login frame
        title_label = ctk.CTkLabel(self, text="COMPUTER STUDIES GRADES KIOSK", text_color="white",font=("Courier New", 40, "bold"))
        title_label.pack(padx=20,pady=20)

        # Create a frame for the registration form
        register_frame = ctk.CTkFrame(self, fg_color="gainsboro")
        register_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Load and display the logo
        logo_image = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/Image/Capiz_State_University 2.png")
        logo_image = logo_image.resize((150, 150), Image.LANCZOS)
        logo_photo = ctk.CTkImage(light_image=logo_image, dark_image=logo_image, size=(150, 150))
        logo_label = ctk.CTkLabel(register_frame, image=logo_photo, text="")
        logo_label.place(x=1150, y=10)

        def validate_student_id(event):
            try:
                new_value = self.student_id_entry.get()
                if len(new_value) > 11:
                    new_value = new_value[:11]
                if re.match(r'^[0-9-]*$', new_value):
                    self.student_id_entry.delete(0, 'end')
                    self.student_id_entry.insert(0, new_value)
                    return True
                else:
                    self.student_id_entry.delete(0, 'end')
                    self.student_id_entry.insert(0, re.sub(r'[^0-9-]', '', new_value))
                    return False
            except Exception as e:
                print(f"Validation error: {e}")
                return False
        def validate_name(event, entry):
            try:
                new_value = entry.get()
                if re.match(r'^[a-zA-Z]*$', new_value):
                    return True
                else:
                    entry.delete(0, 'end')
                    entry.insert(0, re.sub(r'[^a-zA-Z]', '', new_value))
                    return False
            except Exception as e:
                print(f"Validation error: {e}")
                return False

        self.student_id_entry = ctk.CTkEntry(register_frame, placeholder_text="Student ID", text_color="black", placeholder_text_color="black", fg_color="white", width=200, height=39, corner_radius=30)
        self.student_id_entry.pack(pady=10)
        self.student_id_entry.bind('<KeyRelease>', validate_student_id)

        self.last_name_entry = ctk.CTkEntry(register_frame, width=200, text_color="black",height=39,corner_radius=30, placeholder_text="Last Name", placeholder_text_color="black", fg_color="white")
        self.last_name_entry.pack(pady=10)
        self.last_name_entry.bind('<KeyRelease>', lambda event: validate_name(event, self.last_name_entry))
        
        self.middle_name_entry = ctk.CTkEntry(register_frame, width=200, text_color="black",corner_radius=30, height=39, placeholder_text="Middle Name", placeholder_text_color="black", fg_color="white")
        self.middle_name_entry.pack(pady=10)
        self.middle_name_entry.bind('<KeyRelease>', lambda event: validate_name(event, self.middle_name_entry))
        
        self.first_name_entry = ctk.CTkEntry(register_frame, width=200, text_color="black",corner_radius=30,height=39, placeholder_text="First Name", placeholder_text_color="black", fg_color="white")
        self.first_name_entry.pack(pady=10)
        self.first_name_entry.bind('<KeyRelease>', lambda event: validate_name(event, self.first_name_entry))

        self.password_entry = ctk.CTkEntry(register_frame, show="*", text_color="black",width=200, corner_radius=30, height=39, placeholder_text="Password", placeholder_text_color="black", fg_color="white")
        self.password_entry.pack(pady=10)
        
        self.confirm_password_entry = ctk.CTkEntry(register_frame, show="*", text_color="black",width=200, corner_radius=30, height=39, placeholder_text="Confirm Password", placeholder_text_color="black", fg_color="white")
        self.confirm_password_entry.pack(pady=10)
        
        # Function to toggle password visibility
        def toggle_password():
            if self.password_entry.cget('show') == '*':
                self.password_entry.configure(show='')
                password_button.configure(image=hide_icon)
            else:
                self.password_entry.configure(show='*')
                password_button.configure(image=show_icon)

        # Load the show/hide icons
        show_icon = ctk.CTkImage(Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/show_icon.png").resize((15, 15), Image.LANCZOS))
        hide_icon = ctk.CTkImage(Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/hide_icon.png").resize((15, 15), Image.LANCZOS))

        # Add a "Show Password" button with an icon
        password_button = ctk.CTkButton(register_frame, image=show_icon, text="", width=15, height=15, bg_color="white", fg_color="white",command=toggle_password)
        password_button.place(x=728, y=251)  # Adjust the position as needed

        # Function to toggle password visibility
        def toggle_password2():
            if self.confirm_password_entry.cget('show') == '*':
                self.confirm_password_entry.configure(show='')
                show_password_button.configure(image=hide_icon)
            else:
                self.confirm_password_entry.configure(show='*')
                show_password_button.configure(image=show_icon)

        # Load the show/hide icons
        show_icon = ctk.CTkImage(Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/show_icon.png").resize((15, 15), Image.LANCZOS))
        hide_icon = ctk.CTkImage(Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/hide_icon.png").resize((15, 15), Image.LANCZOS))

        # Add a "Show Password" button with an icon
        show_password_button = ctk.CTkButton(register_frame, image=show_icon, text="", width=15, height=15, bg_color="white", fg_color="white",command=toggle_password2)
        show_password_button.place(x=728, y=311)  # Adjust the position as needed

        # Bind the Enter key to navigate between the Entry widgets
        self.student_id_entry.bind("<Return>", lambda event: self.last_name_entry.focus_set())
        self.last_name_entry.bind("<Return>", lambda event: self.middle_name_entry.focus_set())
        self.middle_name_entry.bind("<Return>", lambda event: self.first_name_entry.focus_set())
        self.first_name_entry.bind("<Return>", lambda event: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda event: self.confirm_password_entry.focus_set())
        self.confirm_password_entry.bind("<Return>", lambda event: self.register())

        ctk.CTkButton(register_frame, text="Register", font=("Helvetica", 15, "bold"),command=self.register, width=100, corner_radius=30).pack(pady=20)
        already_text = "Already have an account? "
        already_label = ctk.CTkLabel(register_frame, text=already_text, fg_color="gainsboro", text_color="black", font=("Helvetica", 12))
        already_label.place(x=582, y=420)

        # Create a clickable and underlined "Login" label
        login_link = ctk.CTkLabel(register_frame, text="Login",fg_color="gainsboro", text_color="blue", font=("Helvetica", 12, "underline"))
        login_link.place(x=721, y=420)
        login_link.bind("<Button-1>", lambda e: self.show_login())

    def register(self):
        student_id = self.student_id_entry.get()
        last_name = self.last_name_entry.get()
        middle_name = self.middle_name_entry.get()
        first_name = self.first_name_entry.get()
        password = self.password_entry.get()

        if not student_id or not last_name or not middle_name or not first_name or not password:
            messagebox.showerror("Error", "All fields are required")
            return

        try:
            self.db_handler.register_student(student_id, last_name, middle_name, first_name, password)
            messagebox.showinfo("Success", "Registration successful")
            self.show_login()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def login(self):
        student_id = self.student_id_entry.get()
        password = self.password_entry.get()

        student = self.db_handler.get_student(student_id)
        if student and student[4] == password:  # Assuming PASSWORD is the 5th column
            self.show_grades(student_id)
        else:
            messagebox.showerror("Error", "Invalid student ID or password")

    def show_grades(self, student_id):
        self.clear_frame()
        self.state('zoomed')
        self.student_id = student_id

        # Fetch student details
        student = self.db_handler.get_student(student_id)
        last_name = student[1]
        middle_name = student[2]
        first_name = student[3]

        # Display student name and ID
        name_label = ctk.CTkLabel(self, text=f"{last_name}, {middle_name} {first_name}", font=("Helvetica", 20, "bold"), text_color="white")
        name_label.pack(anchor='w', pady=10)
        id_label = ctk.CTkLabel(self, text=f"Student ID: {student_id}", font=("Helvetica", 16), text_color="white")
        id_label.pack(anchor='w', pady=10)

        # Create a label for the school year
        self.school_year_label = ctk.CTkLabel(self, text="", font=("Helvetica", 16), text_color="white")
        self.school_year_label.pack(anchor='w', pady=10)

        # Add a logout button
        logout_button = ctk.CTkButton(self, text="Logout", corner_radius=30, command=self.logout, width=100)
        logout_button.pack(anchor='e', pady=10, padx=10)

        # Use ttk.Notebook instead of ctk.CTkTabview
        self.tabview = ttk.Notebook(self)
        self.tabview.pack(fill="both", expand=True)

        self.semesters = {
            '1.1': 'first_year_first_semester',
            '1.2': 'first_year_second_semester',
            '2.1': 'second_year_first_semester',
            '2.2': 'second_year_second_semester',
            '3.1': 'third_year_first_semester',
            '3.2': 'third_year_second_semester',
            '4.1': 'fourth_year_first_semester',
            '4.2': 'fourth_year_second_semester'
        }

        self.semester_descriptions = {
        '1.1': 'First Year - First Semester',
        '1.2': 'First Year - Second Semester',
        '2.1': 'Second Year - First Semester',
        '2.2': 'Second Year - Second Semester',
        '3.1': 'Third Year - First Semester',
        '3.2': 'Third Year - Second Semester',
        '4.1': 'Fourth Year - First Semester',
        '4.2': 'Fourth Year - Second Semester'
        }

        self.treeviews = {}

        for sem, sem_name in self.semesters.items():
            frame = ttk.Frame(self.tabview)
            self.tabview.add(frame, text=sem)  # Add a tab for each semester

            columns = ("Course", "Descriptive Title", "Grade")
            tree = ttk.Treeview(frame, columns=columns, show="headings")
            
            # Set font for the Treeview
            style = ttk.Style()
            style.theme_use("clam")
            style.configure("Treeview", font=("Helvetica", 12), rowheight=30)
            style.configure("Treeview.Heading", font=("Helvetica", 14, "bold"), background="#FFD700", foreground="black")

            for col in columns:
                tree.heading(col, text=col, anchor="center")
            
            # Configure column alignment for rows
            tree.column("Course", anchor="w", width=90)
            tree.column("Descriptive Title", anchor="w", width=320)
            tree.column("Grade", anchor="center", width=100)

            # Configure tags for alternating row colors
            tree.tag_configure('oddrow', background='lightgrey')
            tree.tag_configure('evenrow', background='white')

            tree.pack(fill="both", expand=True)

            self.treeviews[sem] = tree

        # Bind the tab change event to update the school year label
        self.tabview.bind("<<NotebookTabChanged>>", self.update_school_year_label)

        self.load_grades()

    def update_school_year_label(self, event):
        selected_tab = self.tabview.tab(self.tabview.select(), "text")
        #print(f"Selected tab: {selected_tab}")  # Debug print
        semester = self.semesters[selected_tab]
        #print(f"Mapped semester: {semester}")  # Debug print
        school_year = self.db_handler.school_year(self.student_id, selected_tab)
        #print(f"Fetched school year: {school_year}")  # Debug print
        description = self.semester_descriptions[selected_tab]  
        self.school_year_label.configure(text=f"{description} - School Year: {school_year}")

    def logout(self):
        self.show_login()

    def load_grades(self):
        grades = self.db_handler.get_grades(self.student_id)
        for index, grade in enumerate(grades):
            sem_key, course_no, grade_value = grade

            # Fetch the descriptive title from the curriculum_regular table
            descriptive_title = self.db_handler.get_descriptive_title(course_no)

            if sem_key in self.treeviews:
                tag = 'evenrow' if index % 2 == 0 else 'oddrow'
                self.treeviews[sem_key].insert("", "end", values=(course_no, descriptive_title, grade_value), tags=(tag,))
        
    def clear_frame(self):
        for widget in self.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = StudentApp()
    app.mainloop()
        