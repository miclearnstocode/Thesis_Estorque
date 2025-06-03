import customtkinter as ctk
import tkinter as tk
from PIL import Image

class BaseSearchBar(ctk.CTkFrame):
    def __init__(self, parent, search_frame, student_list_frame):
        super().__init__(search_frame)
        self.parent = parent
        self.student_list_frame = student_list_frame

    def load_icon(self, path, size=(30, 30)):
        icon = Image.open(path)
        return ctk.CTkImage(light_image=icon, dark_image=icon, size=size)

class RegularSearchBar(BaseSearchBar):
    def __init__(self, parent, search_frame, student_list_frame):
        super().__init__(parent, search_frame, student_list_frame)
        self.build_search_ui()

    def build_search_ui(self):
        ctk.CTkLabel(self, text="Regular Students ID NO:", font=ctk.CTkFont(size=14)).pack(side="left", padx=5)

        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(self, corner_radius=20, textvariable=self.search_var, width=200, height=32,
                                    placeholder_text="e.g., 2021-322048")
        search_entry.pack(side="left", padx=5)

        search_icon = self.load_icon("icons/searchs.png")
        ctk.CTkButton(self, text="Search", image=search_icon, text_color="black", fg_color="transparent",
                      border_width=1, width=100, height=32, command=self.search_student).pack(side="left", padx=(0, 5))

        search_entry.bind("<Return>", lambda event: self.search_student())

    def search_student(self):
        id_no = self.search_var.get().strip()
        if not id_no:
            tk.messagebox.showerror("Input Error", "Please enter a valid ID_NO.")
            return
        # TODO: Call search logic from service layer and display in self.student_list_frame
        print(f"Searching for regular student: {id_no}")

class IrregularSearchBar(BaseSearchBar):
    def __init__(self, parent, search_frame, student_list_frame):
        super().__init__(parent, search_frame, student_list_frame)
        self.build_search_ui()

    def build_search_ui(self):
        ctk.CTkLabel(self, text="Irregular Students ID NO:", font=ctk.CTkFont(size=14)).pack(side="left", padx=5)

        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(self, corner_radius=20, textvariable=self.search_var, width=200, height=32,
                                    placeholder_text="Enter ID")
        search_entry.pack(side="left", padx=5)

        search_icon = self.load_icon("icons/searchs.png")
        ctk.CTkButton(self, text="Search", image=search_icon, text_color="black", fg_color="transparent",
                      hover_color="grey70", border_width=1, width=100, height=32,
                      command=self.search_student_irregular).pack(side="left", padx=(0, 5))

        search_entry.bind("<Return>", lambda event: self.search_student_irregular())

    def search_student_irregular(self):
        id_no = self.search_var.get().strip()
        if not id_no:
            tk.messagebox.showerror("Input Error", "Please enter a valid ID_NO.")
            return
        # TODO: Call irregular search logic from service layer and display in self.student_list_frame
        print(f"Searching for irregular student: {id_no}")
