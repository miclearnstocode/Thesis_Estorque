import csv
import re
import functools
import import_functions as import_functions
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog , messagebox
from import_functions import database_grade, database_student, save_data, get_db_connection
from regular import process_data

def bind_method(cls):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Computer Science Department System")
        self.geometry("800x600")  # Set the window size
        self.bind('<Control-s>', lambda event: save_data)

        # Create a frame to hold the buttons
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=20)  # Add some padding around the frame

        # Create the buttons
        buttons = [
            ("Student", self.student_screen),
            ("Grade", self.grade_screen),
            ("Curriculum", self.curriculum_screen),
            ("Archive", self.archive_screen),
        ]

        for i, (text, command) in enumerate(buttons):
            button = ttk.Button(self.button_frame, text=text, command=command)
            button.grid(row=0, column=i, padx=10, pady=10)  # Arrange buttons in a row

        self.center_window()
        self.current_frame = self.button_frame
        # Variable to store the currently searched student details
        self.current_student = None

    def center_window(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        size = tuple(int(pos) for pos in self.geometry().split('+')[0].split('x'))
        x = (screen_width // 2) - (size[0] // 2)
        y = (screen_height // 2) - (size[1] // 2)
        self.geometry(f"{size[0]}x{size[1]}+{x}+{y}")

    def student_screen(self):
        if self.current_frame:
            self.current_frame.pack_forget()
            self.student_frame = tk.Frame(self)
            self.student_frame.pack(pady=20)

            tk.Label(self.student_frame, text="Student").pack()

        # Create a frame to hold the Regular/Irregular buttons
            self.regular_frame = tk.Frame(self.student_frame)
            self.regular_frame.pack(pady=10)

            ttk.Button(self.regular_frame, text="Regular", command=lambda: self.show_search_bar("Regular")).pack(side=tk.LEFT)
            ttk.Button(self.regular_frame, text="Irregular", command=lambda: self.show_search_bar("Irregular")).pack(side=tk.LEFT)

            # Create a frame to hold the search bar, buttons, and student list
            self.search_frame = tk.Frame(self.student_frame)
            self.search_frame.pack(pady=10)

            self.student_list_frame = tk.Frame(self.student_frame)
            self.student_list_frame.pack(pady=10)

            tab_frame = ttk.Frame(self.student_frame)
            tab_frame.pack(pady=20)

        # Create a frame to hold the year combobox and import button
            button_frame = tk.Frame(self.student_frame)
            button_frame.pack(pady=10)

            self.year_var = tk.StringVar()
            self.year_combox = ttk.Combobox(button_frame, textvariable=self.year_var)
            self.year_combox['values'] = ('1st yr', '2nd yr', '3rd yr', '4th yr')
            self.year_combox.current(0)
            self.year_combox.grid(row=356, column=238, padx=10)  # Use grid instead of pack

            import_button = ttk.Button(button_frame, text="Add student", command=lambda: self.import_students())
            import_button.grid(row=0, column=1, padx=5)  # Use grid instead of pack

            ttk.Button(self.student_frame, text="Back", command=self.show_main_menu).pack(pady=10)
            self.current_frame = self.student_frame

    def import_students(self):
    # Use file dialog to select the CSV file
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                with open(file_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    database_student_list = []
                
                    for row in reader:
                        # Clean and validate data
                        cleaned_row = {
                            'ID_NO': self.clean_id_no(row.get('ID_NO', '')),
                            'STUDENT_NAME': row.get('STUDENT_NAME', '').title(),
                            'AGE': self.validate_integer(row.get('AGE', '')),
                            'YEAR_LEVEL': self.validate_integer(row.get('YEAR_LEVEL', '')),
                            'SEX': row.get('SEX', '').strip().upper(),
                            'EMAIL_ADDRESS': row.get('EMAIL_ADDRESS', '').strip(),
                            'SHS': row.get('SHS', '').strip(),
                            'ADDRESS': row.get('ADDRESS', '').strip()
                        }

                        # Validate fields
                        if (cleaned_row['ID_NO'] is None or
                            not cleaned_row['SEX'] in ['M', 'F'] or
                            not self.validate_email(cleaned_row['EMAIL_ADDRESS'])):
                            messagebox.showerror("Invalid data", f"Invalid row data: {row}")
                            continue

                        # Add valid student data to the list
                        database_student_list.append(cleaned_row)

                # Insert valid student data into the database
                table_name = 'student_information'
                conn, cursor = get_db_connection()
                for student in database_student_list:
                    database_student(table_name, [student], cursor)
                conn.commit()
                conn.close()

                # Display the updated student data
                self.display_student_treeview(database_student_list)
            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import students: {str(e)}")

    def validate_integer(value):
        try:
            return int(value) if value.isdigit() else None
        except ValueError:
            return None
    def display_student_treeview(self, students):
        # Clear the current frame (if needed)
        for widget in self.student_list_frame.winfo_children():
            widget.destroy()

        # Create a treeview in the student frame
        student_treeview = ttk.Treeview(self.student_list_frame, columns=('ID_NO', 'STUDENT_NAME', 'YEAR_LEVEL', 'AGE', 'SEX', 'EMAIL_ADDRESS', 'SHS', 'ADDRESS'))
        student_treeview.pack(expand=True, fill='both', padx=20, pady=20)

        student_treeview.heading('#0', text='')
        student_treeview.heading('#1', text='ID_NO', anchor="w")
        student_treeview.heading('#2', text='STUDENT_NAME', anchor="w")
        student_treeview.heading('#3', text='YEAR_LEVEL', anchor="w")
        student_treeview.heading('#4', text='AGE', anchor="w")
        student_treeview.heading('#5', text='SEX', anchor="w")
        student_treeview.heading('#6', text='EMAIL_ADDRESS', anchor="w")
        student_treeview.heading('#7', text='SHS', anchor="w")
        student_treeview.heading('#8', text='ADDRESS', anchor="w")

        student_treeview.column('#0', width=0, stretch=tk.NO)
        student_treeview.column('#1', width=100, stretch=tk.NO)
        student_treeview.column('#2', width=200, stretch=tk.YES, minwidth=200)  # Make this column stretchable
        student_treeview.column('#3', width=100, stretch=tk.NO, minwidth=50)
        student_treeview.column('#4', width=50, stretch=tk.NO, minwidth=50)
        student_treeview.column('#5', width=100, stretch=tk.NO, minwidth=50)
        student_treeview.column('#6', width=150, stretch=tk.NO, minwidth=100)
        student_treeview.column('#7', width=100, stretch=tk.NO, minwidth=50)
        student_treeview.column('#8', width=200, stretch=tk.NO, minwidth=100)

        # Insert the student data into the treeview
        for student in students:
            student_treeview.insert('', 'end', values=list(student.values()))

    def _validate_student_data(self, student_dict):
        try:
            default_values = {'ID_NO': '0', 'STUDENT_NAME': '', 'AGE': 0, 'YEAR_LEVEL': 0, 'SEX': '', 'EMAIL_ADDRESS': '', 'SHS': '', 'ADDRESS': ''}

            for key, default_value in default_values.items():
                if key in student_dict:
                    value = student_dict[key]

                 # Ensure value is not None
                    if value is None:
                        value = default_value

                    # Handle ID_NO specifically
                    if key == 'ID_NO':
                        if isinstance(value, str):
                         # Remove non-digit characters
                            cleaned_value = ''.join(char for char in value if char.isdigit())
                            # Check if cleaned_value is valid
                            if cleaned_value:
                                student_dict[key] = cleaned_value
                            else:
                                messagebox.showerror("Invalid data", f"ID_NO should contain digits: {value}")
                                return None
                        else:
                            messagebox.showerror("Invalid data", f"ID_NO should be a string: {value}")
                            return None

                    elif key == 'STUDENT_NAME':
                        student_dict[key] = value.title()

                    elif key == 'SEX':
                        sex_value = value.strip().upper()
                        if sex_value not in ['M', 'F']:
                            messagebox.showerror("Invalid data", f"Invalid value for SEX: {sex_value}")
                            return None
                        student_dict[key] = sex_value

                    elif key == 'EMAIL_ADDRESS':
                        email_value = value.strip()
                        if not email_value or not self._validate_email(email_value):
                            messagebox.showerror("Invalid data", f"Invalid email address: {email_value}")
                            return None
                        student_dict[key] = email_value

                    elif key == 'SHS':
                        student_dict[key] = value.strip()

                    elif key == 'ADDRESS':
                        student_dict[key] = value.strip()

                    else:
                        # Ensure other fields are integers if possible
                        if isinstance(value, str) and value.isdigit():
                            student_dict[key] = int(value)
                        else:
                            # Use default value if conversion fails
                            student_dict[key] = default_value

                else:
                    student_dict[key] = default_value

            # Convert ID_NO to integer after validation
            if 'ID_NO' in student_dict:
                try:
                    student_dict['ID_NO'] = int(student_dict['ID_NO'])
                except ValueError:
                    messagebox.showerror("Invalid data", f"Invalid ID_NO: {student_dict['ID_NO']}")
                    return None

            return student_dict

        except Exception as e:
            messagebox.showerror("Invalid data", str(e))
            return None

    def clean_id_no(self, id_no):
        if isinstance(id_no, str):
            cleaned_value = ''.join(char for char in id_no if char.isdigit())
            return cleaned_value if cleaned_value else None
        return None
    def _validate_email(self, email):
        # Simple email validation using a regular expression
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.match(email_regex, email) is not None 
       
    def show_search_bar(self, status):
        # Clear the search frame before showing the search bar
        self.clear_frame(self.search_frame)
        self.clear_frame(self.student_list_frame)

        tk.Label(self.search_frame, text=f"Search {status} Students by ID:").pack(side=tk.LEFT, padx=5)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        search_button = ttk.Button(self.search_frame, text="Search", command=lambda: self.search_student(self.search_var.get(), status))
        search_button.pack(side=tk.LEFT, padx=5)

        info_button = ttk.Button(self.search_frame, text="Student Information", command=self.show_student_info)
        info_button.pack(side=tk.LEFT, padx=5)

        subject_button = ttk.Button(self.search_frame, text="Subject", command=self.show_subject_info)
        subject_button.pack(side=tk.LEFT, padx=5)

        # Bind the Enter key to trigger the search function
        self.search_entry.bind("<Return>", lambda event: self.search_student(self.search_var.get(), status))

    def search_student(self, ID_NO, status):
        # Clear only the student list frame before showing the search results
        self.clear_frame(self.student_list_frame)

        tk.Label(self.student_list_frame, text=f"Search Results for {status} Students with ID {ID_NO}:").pack(anchor='w')

        # Create a frame to display the student details
        student_details_frame = tk.Frame(self.student_list_frame)
        student_details_frame.pack(anchor='w', padx=10, pady=5)

        # Connect to the database
        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Query the database for the student with the given ID
        query = "SELECT * FROM students WHERE id = ?"
        cursor.execute(query, (ID_NO,))

        # Fetch the student data from the query result
        student = cursor.fetchone()

        if student:
            # Store the current student details for later use
            self.current_student = student

            student_info_text = f"ID: {student['ID']}\nName: {student['Name']}\nYear Level: {student['Year_Level']}\nAge: {student['Age']}\nSex: {student['Sex']}\nEmail: {student['Email']}\nSHS: {student['SHS']}\nAddress: {student['Address']}"
            tk.Label(student_details_frame, text=student_info_text, anchor='w').pack(anchor='w')

        else:
            tk.Label(student_details_frame, text="No student found with the given ID.").pack(anchor='w')

        conn.close()
        
    def show_student_info(self):
        if self.current_student:
            self.clear_frame(self.student_list_frame)
            student_info_frame = tk.Frame(self.student_list_frame)
            student_info_frame.pack(anchor='w', padx=10, pady=5)
            tk.Label(student_info_frame, text=f"Student Information for {self.current_student['name']}").pack(anchor='w')
            tk.Label(student_info_frame, text=f"Year Level: {self.current_student['year']}").pack(anchor='w')
            tk.Label(student_info_frame, text=f"ID Number: {self.current_student['id']}").pack(anchor='w')
            tk.Label(student_info_frame, text=f"Info: {self.current_student['info']}").pack(anchor='w')
        else:
            self.show_error("No student selected. Please search for a student first.")

    def show_subject_info(self):
        if self.current_student:
            self.clear_frame(self.student_list_frame)
            subject_info_frame = tk.Frame(self.student_list_frame)
            subject_info_frame.pack(anchor='w', padx=10, pady=5)
            tk.Label(subject_info_frame, text=f"Subject Information for {self.current_student['name']}").pack(anchor='w')
            for subject in self.current_student['subjects']:
                tk.Label(subject_info_frame, text=subject).pack(anchor='w')
        else:
            self.show_error("No student selected. Please search for a student first.")

    def show_error(self, message):
        error_window = tk.Toplevel(self)
        error_window.title("Error")
        tk.Label(error_window, text=message, padx=20, pady=20).pack()
        ttk.Button(error_window, text="OK", command=error_window.destroy).pack(pady=10)

    def grade_screen(self):
        if self.current_frame:
            self.current_frame.pack_forget()
        self.grade_frame = tk.Frame(self)
        self.grade_frame.pack(pady=20)

        tk.Label(self.grade_frame, text="Grade").pack()

        # Create buttons for each year level
        years = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        for year in years:
            year_frame = tk.Frame(self.grade_frame)
            year_frame.pack(pady=5)
            tk.Label(year_frame, text=f"{year} Grading Sheet:").pack(side=tk.LEFT)

            # Add semester selection
            semester_var = tk.StringVar()
            semester_var.set("1st Semester")  # default value
            semester_label = tk.Label(year_frame, text="Semester:")
            semester_label.pack(side=tk.LEFT)
            semester_option = ttk.OptionMenu(year_frame, semester_var, "1st Semester", "1st Semester", "2nd Semester")
            semester_option.pack(side=tk.LEFT, padx=5)

            import_button = ttk.Button(year_frame, text="Import", command=lambda year=year, semester=semester_var: self.import_grading_sheet(year, semester.get()))
            import_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(self.grade_frame, text="Back", command=self.show_main_menu).pack(pady=10)
        self.current_frame = self.grade_frame

    def import_grading_sheet(self, year, semester):
        title = f"Grading Sheet for {year} {semester}"
        grading_data = database_grade(title)
        if grading_data:
            print(f"Processed {year} {semester} grading sheet data")
            # Implement further processing or display of the grading data here

    def curriculum_screen(self):
        if self.current_frame:
            self.current_frame.pack_forget()
        self.curriculum_frame = tk.Frame(self)
        self.curriculum_frame.pack(pady=20)

        tk.Label(self.curriculum_frame, text="Curriculum").pack()

        # Frame to hold the import buttons
        import_frame = tk.Frame(self.curriculum_frame)
        import_frame.pack(pady=10)

        ttk.Button(import_frame, text="Existing Curriculum (CSV)", command= self.import_existing_curriculum).pack(side=tk.LEFT, padx=5)
        ttk.Button(import_frame, text="New Curriculum (CSV)", command=self.import_new_curriculum).pack(side=tk.LEFT, padx=5)

        ttk.Button(self.curriculum_frame, text="Back", command=self.show_main_menu).pack(pady=10)
        self.current_frame = self.curriculum_frame

    def load_and_process_file(self, title):
        file_path = filedialog.askopenfilename(title=title, filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                processed_data = process_data(file_path)
                self.display_processed_data(processed_data, self.curriculum_frame)
                messagebox.showinfo("Success", "Data processed successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
        return None
    def display_processed_data(self, processed_data, content_frame):
        # Clear existing widgets in the content frame
        for widget in content_frame.winfo_children():
            widget.destroy()

        # Notebook widget to handle multiple tabs (one for each year level and cluster)
        notebook = ttk.Notebook(content_frame)
        notebook.pack(expand=True, fill='both', padx=20, pady=20)
        self.treeviews = []

        # Iterate through each year level and cluster to create tabs
        for year_level in processed_data['Year Level'].unique():
            for cluster_id in processed_data['Cluster'].unique():
                tab_frame = ttk.Frame(notebook)
                notebook.add(tab_frame, text=f"{year_level}Y")

                # Treeview widget for the table
                tree = ttk.Treeview(tab_frame, height=10, columns=('Course No.', 'Descriptive Title', 'Year Level', 'Units', 'Lab', 'Lec', 'Prerequisite', 'Grades'))
                tree.pack(expand=True, fill='both', padx=20, pady=20)

                tree.heading('#0', text='')
                tree.heading('#1', text='Course No.')
                tree.heading('#2', text='Descriptive Title', anchor=tk.W)
                tree.heading('#3', text='Year Level')
                tree.heading('#4', text='Units')
                tree.heading('#5', text='Lab')
                tree.heading('#6', text='Lec')
                tree.heading('#7', text='Prerequisite')
                tree.heading('#8', text='Grades')

                tree.column('#0', width=0, stretch=tk.NO)
                tree.column('#1', width=70, stretch=tk.NO)
                tree.column('#2', width=300, stretch=tk.YES)
                tree.column('#3', width=70, stretch=tk.NO)  
                tree.column('#4', width=50, stretch=tk.NO)
                tree.column('#5', width=50, stretch=tk.NO)
                tree.column('#6', width=50, stretch=tk.NO)
                tree.column('#7', width=100, stretch=tk.YES)
                tree.column('#8', width=100, stretch=tk.NO)
                # Insert data into the Treeview
                filtered_data = processed_data[(processed_data['Year Level'] == year_level) & (processed_data['Cluster'] == cluster_id)]
                for _, row in filtered_data.iterrows():
                    tree.insert('', 'end', values=list(row))

                # Calculate and insert totals
                totals = filtered_data[['Units', 'Lab', 'Lec']].sum()
                tree.insert('', 'end', values=['Total', '', year_level, totals['Units'], totals['Lab'], totals['Lec'], ''])

                # Append Treeview to the list for saving later
                self.treeviews.append(tree)

        # Add Save and Back buttons
        save_button = ttk.Button(self.curriculum_frame, text="Save Data", command=lambda: save_data(self.treeviews))
        save_button.pack(pady=10)

        ttk.Button(self.curriculum_frame, text="Back", command=self.show_main_menu).pack(pady=10)

    def save_data_callback(self, cursor, treeviews):
            save_data(cursor, treeviews)
            cursor.commit()
            cursor.close()
            messagebox.showinfo("Success", "Data saved successfully!")

    def import_existing_curriculum(self):
        title = "Existing Curriculum (CSV)"
        curriculum_data = self.load_and_process_file(title)
        if curriculum_data is not None:
            print(f"Processed new curriculum data from {title}")
            # Clear the Treeview widget
            self.curriculum_treeview.delete(*self.curriculum_treeview.get_children())
            # Populate the Treeview widget with the imported data
            for course in curriculum_data:
                self.curriculum_treeview.insert("", tk.END, values=(course["Course No."], course["Descriptive Title"], course["Units"], course["Grades"]))  
        else:
            messagebox.showerror("Error", "No data Imported. ")
    def import_new_curriculum(self):
        title = "New Curriculum (CSV)"
        curriculum_data = self.load_and_process_file(title)
        if curriculum_data:
            print(f"Processed new curriculum data from {title}")
           
            self.curriculum_treeview.delete(*self.curriculum_treeview.get_children())
            # Populate the Treeview widget with the imported data
            for course in curriculum_data:
                self.curriculum_treeview.insert("", tk.END, values=(course["Course No."], course["Descriptive Title"], course["Units"], course["Grades"]))
        
            # Update the curriculum for 1st year students
            self.update_curriculum_for_year_level("1st Year", curriculum_data)   

    def update_curriculum_for_year_level(self, year_level, new_curriculum):
        
        for student in self.students:  
            if student["Year Level"] == year_level:
                if student["Year Level"] == "1st Year":  
                    student["Curriculum"] = new_curriculum  
                else:
                    
                    if student["Completed Courses"]:
                        
                        print(f"Student {student['Name']} has completed courses in the old curriculum. Leaving curriculum unchanged.")
                    else:
                        student["Curriculum"] = new_curriculum 
                print(f"Updated curriculum for {student['Name']} ({year_level})")
        # Check if any students have graduated and need to be archived
            for student in self.students:
                if student["Year Level"] == "4th Year" and student["Completed Courses"]:
                    # Add the old curriculum to the archive
                    self.archive_curriculum(student["Curriculum"], "Graduated Students")
                print(f"Archived curriculum for {student['Name']} (Graduated)")

    def archive_screen(self):
        if self.current_frame:
            self.current_frame.pack_forget()
            self.archive_frame = tk.Frame(self)
            self.archive_frame.pack(pady=20)

        tk.Label(self.archive_frame, text="Archive").pack()
        ttk.Button(self.archive_frame, text="Back", command=self.show_main_menu).pack()

        import_frame = tk.Frame(self.archive_frame)
        import_frame.pack(pady=10)

        ttk.Button(import_frame, text="Regular Archive", command=lambda: self.import_archive("Regular")).pack(side=tk.LEFT)
        ttk.Button(import_frame, text="Irregular Archive", command=lambda: self.import_archive("Irregular")).pack(side=tk.LEFT)

        self.current_frame = self.archive_frame

    def show_main_menu(self):
        self.student_frame.pack_forget()
        self.current_frame = self.button_frame
        self.button_frame.pack(pady=20)

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = Application()
    app.mainloop()
