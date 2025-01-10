import csv
import functools
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from import_functions import database_grade, save_data
from regular import process_data

# Decorator to bind methods
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
        self.bind('<Control-s>', lambda event: save_data())

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

        # Create a frame to hold the year combobox and import button
        self.button_frame = ttk.Frame(self.student_frame)
        self.button_frame.pack(pady=10)

        self.year_var = tk.StringVar()
        self.year_combox = ttk.Combobox(self.button_frame, textvariable=self.year_var)
        self.year_combox['values'] = ('1st yr', '2nd yr', '3rd yr', '4th yr')
        self.year_combox.current(0)
        self.year_combox.pack(side=tk.LEFT, padx=10)

        self.import_button = ttk.Button(self.button_frame, text="Add Student", command=self.import_students)
        self.import_button.pack(side=tk.LEFT, padx=10)

        # Add a Back button to return to the main menu
        ttk.Button(self.student_frame, text="Back", command=self.show_main_menu).pack(pady=10)
        self.current_frame = self.student_frame

    def display_student_treeview(self):
        tab_frame = ttk.Frame(self.student_frame)
        tab_frame.pack(pady=20)
        self.student_treeview = ttk.Treeview(tab_frame, columns=('ID No.', 'Student Name', 'Year Level', 'Age', 'Sex', 'Email Address', 'SHS', 'Address'), show="headings")
        self.student_treeview.pack(expand=True, fill='both', padx=20, pady=20)

        # Define the column headings
        self.student_treeview.heading("ID No.", text="ID No.", anchor="w")
        self.student_treeview.heading("Student Name", text="Student Name", anchor="w")
        self.student_treeview.heading("Year Level", text="Year Level", anchor="w")
        self.student_treeview.heading("Age", text="Age", anchor="w")
        self.student_treeview.heading("Sex", text="Sex", anchor="w")
        self.student_treeview.heading("Email Address", text="Email Address", anchor="w")
        self.student_treeview.heading("SHS", text="SHS", anchor="w")
        self.student_treeview.heading("Address", text="Address", anchor="w")

        # Set the column widths
        self.student_treeview.column("ID No.", width=100, stretch=tk.NO, minwidth=100)
        self.student_treeview.column("Student Name", width=200, stretch=tk.YES, minwidth=200)  # Make this column stretchable
        self.student_treeview.column("Year Level", width=100, stretch=tk.NO, minwidth=50)
        self.student_treeview.column("Age", width=50, stretch=tk.NO, minwidth=50)
        self.student_treeview.column("Sex", width=100, stretch=tk.NO, minwidth=50)
        self.student_treeview.column("Email Address", width=150, stretch=tk.NO, minwidth=100)
        self.student_treeview.column("SHS", width=100, stretch=tk.NO, minwidth=50)
        self.student_treeview.column("Address", width=200, stretch=tk.NO, minwidth=100)

    def import_students(self):
        # Load the CSV file
        if self.load_csv_file():
            self.display_student_treeview()

    def _validate_student_data(self, student_dict):
        """
        Validate and clean the student data.
        """
        if 'ID NO.' in student_dict:
            id_no = student_dict['ID NO.'].replace('-', '')
            try:
                student_dict['ID NO.'] = int(id_no)
            except ValueError:
                messagebox.showerror("Invalid ID NO.", "The ID NO. must be an integer.")
                return None
        else:
            student_dict['ID NO.'] = 0

        if 'STUDENT NAME' in student_dict:
            student_dict['STUDENT NAME'] = student_dict['STUDENT NAME'].title()
        else:
            student_dict['STUDENT NAME'] = ''

        if 'AGE' in student_dict:
            try:
                student_dict['AGE'] = int(student_dict['AGE'])
            except ValueError:
                messagebox.showerror("Invalid AGE", "The AGE must be an integer.")
                return None
        else:
            student_dict['AGE'] = 0

        if 'YEAR_LEVEL' in student_dict:
            try:
                student_dict['YEAR_LEVEL'] = int(student_dict['YEAR_LEVEL'])
            except ValueError:
                messagebox.showerror("Invalid YEAR_LEVEL", "The YEAR_LEVEL must be an integer.")
                return None
        else:
            student_dict['YEAR_LEVEL'] = 0

        return student_dict

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

    def search_student(self, student_id, status):
        # Clear only the student list frame before showing the search results
        self.clear_frame(self.student_list_frame)

        tk.Label(self.student_list_frame, text=f"Search Results for {status} Students with ID {student_id}:").pack(anchor='w')

        # Create a frame to display the student details
        student_details_frame = tk.Frame(self.student_list_frame)
        student_details_frame.pack(anchor='w', padx=10, pady=5)

        # Connect to the database
        conn = self.open_database_connection()
        cursor = conn.cursor()

        # Query the database for the student with the given ID
        query = "SELECT * FROM students WHERE id = ?"
        cursor.execute(query, (student_id,))

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

    def open_database_connection(self):
        # Add code here to connect to your database (e.g., MySQL, SQLite)
        # This is just a placeholder to avoid errors in this example.
        pass

    def show_student_info(self):
        if self.current_student:
            messagebox.showinfo("Student Info", f"ID: {self.current_student['ID']}\nName: {self.current_student['Name']}")
        else:
            messagebox.showerror("No student selected", "Please search for a student first.")

    def show_subject_info(self):
        if self.current_student:
            messagebox.showinfo("Subject Info", f"Displaying subjects for {self.current_student['Name']}")
        else:
            messagebox.showerror("No student selected", "Please search for a student first.")

    def curriculum_screen(self):
        pass

    def grade_screen(self):
        pass

    def archive_screen(self):
        pass

    def show_main_menu(self):
        self.student_frame.pack_forget()
        self.current_frame = self.button_frame
        self.button_frame.pack(pady=20)

    def load_csv_file(self):
        file_path = filedialog.askopenfilename(title="Open CSV File", filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return False

        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    student_dict = self._validate_student_data(row)
                    if student_dict:
                        # Insert into the Treeview
                        self.student_treeview.insert('', tk.END, values=(
                            student_dict.get('ID NO.', ''),
                            student_dict.get('STUDENT NAME', ''),
                            student_dict.get('YEAR_LEVEL', ''),
                            student_dict.get('AGE', ''),
                            student_dict.get('Sex', ''),
                            student_dict.get('EMAIL_ADDRESS', ''),
                            student_dict.get('SHS', ''),
                            student_dict.get('Address', '')
                        ))
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV file: {e}")
            return False

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = Application()
    app.mainloop()
