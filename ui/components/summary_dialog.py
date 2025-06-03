import customtkinter as ctk
from tkinter import ttk, messagebox
from PIL import Image
from datetime import datetime

class SummaryDialog(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.place(x=60, y=200)
        self.configure(width=950, height=350, fg_color="gainsboro", corner_radius=30)

        ctk.CTkLabel(self, text="Enrollment Summary", font=("Vivaldi", 30, "bold")).pack(pady=20)
        self.build_ui()

    def build_ui(self):
        self.search_var = ctk.StringVar()

        # Search section
        search_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=20)
        search_frame.pack(fill="x", padx=20, pady=(10, 0))

        ctk.CTkLabel(search_frame, text="Search:", font=("Helvetica", 14)).pack(side="left", padx=10)
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=250, height=30,
                                    placeholder_text="Enter ID, Last Name, or First Name")
        search_entry.pack(side="left", padx=10)
        ctk.CTkButton(search_frame, text="Search", fg_color="blue", text_color="white",
                      corner_radius=10, command=self.filter_students).pack(side="left", padx=10)

        # Tabs for year levels
        self.notebook = ttk.Notebook(self, width=950, height=297)
        self.notebook.pack(pady=10, expand=True, fill='both')
        self.load_student_data()

    def load_student_data(self):
        db = DatabaseHandler()
        self.student_data = {}
        self.treeviews = {}

        current_year = datetime.now().year
        current_sy = f"{current_year}-{current_year + 1}"

        try:
            for year in range(1, 5):
                students = db.get_unenrolled_students(year, current_sy)
                label = f"{year}st Year" if year == 1 else f"{year}nd Year" if year == 2 else f"{year}rd Year" if year == 3 else f"{year}th Year"
                self.student_data[label] = students

            self.render_tabs()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to fetch student data: {str(e)}")

    def render_tabs(self):
        for year, students in self.student_data.items():
            tab = ctk.CTkFrame(self.notebook)
            self.notebook.add(tab, text=year)

            tree_frame = ctk.CTkFrame(tab)
            tree_frame.pack(pady=10, padx=10, fill="both", expand=True)

            columns = ("ID", "Name", "Year Level", "Status")
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
            tree.pack(side="left", fill="both", expand=True)

            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            scrollbar.pack(side="right", fill="y")
            tree.configure(yscrollcommand=scrollbar.set)

            for col in columns:
                tree.heading(col, text=col, anchor="center")
                tree.column(col, anchor="center", width=150)

            for i, student in enumerate(students):
                full_name = f"{student['LAST_NAME']}, {student['FIRST_NAME']} {student['MIDDLE_NAME']}"
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                tree.insert("", "end", values=(student["ID_NO"], full_name, student["YEAR_LEVEL"], student["ENROLLMENT_STATUS"]), tags=(tag,))

            tree.tag_configure("oddrow", background="#f0f0f0")
            tree.tag_configure("evenrow", background="#ffffff")

            self.treeviews[year] = tree

    def filter_students(self):
        term = self.search_var.get().strip().lower()
        if not term:
            messagebox.showwarning("Search Error", "Please enter a search term.")
            return

        for year, tree in self.treeviews.items():
            for item in tree.get_children():
                tree.delete(item)

            filtered = [s for s in self.student_data[year] if
                        term in s["ID_NO"].lower() or term in s["LAST_NAME"].lower() or term in s["FIRST_NAME"].lower()]

            for i, student in enumerate(filtered):
                full_name = f"{student['LAST_NAME']}, {student['FIRST_NAME']} {student['MIDDLE_NAME']}"
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                tree.insert("", "end", values=(student["ID_NO"], full_name, student["YEAR_LEVEL"], student["ENROLLMENT_STATUS"]), tags=(tag,))
