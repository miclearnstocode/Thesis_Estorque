import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
from ui.components.search_bar import RegularSearchBar, IrregularSearchBar
from ui.components.summary_dialog import SummaryDialog

class StudentScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.search_bar = None
        self.curriculum_tree = None

        self.setup_ui()

    def setup_ui(self):
        self.columns = ('ID_NO', 'STUDENT_NAME', 'YEAR_LEVEL', 'AGE', 'SEX', 'EMAIL_ADDRESS', 'SHS', 'ADDRESS')
        self.id_no = None

        # Load background
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        self.bg_image = Image.open("Image/student.JPG").resize((screen_width, screen_height), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        tk.Label(self, image=self.bg_photo).place(x=0, y=0, relwidth=1, relheight=1)

        # Title
        ctk.CTkLabel(self, text="Student", font=("Vivaldi", 40, "bold"), text_color="black", fg_color="transparent").pack(pady=30)

        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)

        self.add_mode_buttons(button_frame)
        self.search_frame = tk.Frame(self, bg="ghost white")
        self.search_frame.place(x=10, y=190)

        self.student_list_frame = tk.Frame(self)
        self.student_list_frame.place(x=30, y=250)

    def add_mode_buttons(self, frame):
        from PIL import Image
        button_style = {
            "fg_color": "transparent",
            "hover_color": "#707070",
            "text_color": "black",
            "height": 32,
            "border_width": 1,
            "border_color": "black",
            "corner_radius": 20
        }
        
        regular_icon = Image.open("icons/regulars.png")
        irreg_icon = Image.open("icons/irregulars.png")
        regular_img = ctk.CTkImage(light_image=regular_icon, dark_image=regular_icon, size=(30, 30))
        irreg_img = ctk.CTkImage(light_image=irreg_icon, dark_image=irreg_icon, size=(30, 30))

        ctk.CTkButton(frame, text="Regular", image=regular_img, **button_style,
                      font=('Helvetica', 14, 'bold'), command=self.show_regular_search).pack(side=tk.RIGHT, padx=10)
        ctk.CTkButton(frame, text="Irregular", image=irreg_img, **button_style,
                      font=('Helvetica', 14, 'bold'), command=self.show_irregular_search).pack(side=tk.RIGHT, padx=10)

    def show_regular_search(self):
        self.clear_frames()
        self.search_bar = RegularSearchBar(self, self.search_frame, self.student_list_frame)
        self.search_bar.pack()

    def show_irregular_search(self):
        self.clear_frames()
        self.search_bar = IrregularSearchBar(self, self.search_frame, self.student_list_frame)
        self.search_bar.pack()

    def show_summary(self):
        self.clear_frames()
        SummaryDialog(self)

    def clear_frames(self):
        for widget in self.search_frame.winfo_children():
            widget.destroy()
        for widget in self.student_list_frame.winfo_children():
            widget.destroy()
