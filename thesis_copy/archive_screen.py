import tkinter as tk
import customtkinter as ctk
from PIL import Image

class ArchiveScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        
        # Load and set up the background
        try:
            bg_image = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/Image/Gradient.jpg")
            self.bg_image = ctk.CTkImage(light_image=bg_image,dark_image=bg_image,size=(self.master.winfo_width(), self.master.winfo_height()))
            
            self.bg_label = ctk.CTkLabel(self,image=self.bg_image,text="")
            self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
            
            # Bind resize event
            self.bind('<Configure>', self.resize_background)
            
        except Exception as e:
            print(f"Error loading background image: {e}")
            self.configure(bg="white")

        self.create_widgets()

    def resize_background(self, event):
        """Update background image size when window is resized"""
        if hasattr(self, 'bg_image'):
            try:
                new_width = self.winfo_width()
                new_height = self.winfo_height()
                self.bg_image.configure(size=(new_width, new_height))
            except Exception as e:
                print(f"Error resizing background: {e}")

    def create_widgets(self):
        # Base button style configuration
        button_style = {
            "fg_color": "transparent",    
            "hover_color": "#707070",     
            "text_color": "black",        
            "height": 32,                 
            "border_width": 1,            
            "border_color": "black"       
        }

        # Additional styles for different button types
        regular_button_style = {**button_style, "width": 120}

        back_button_style = {**button_style, "width": 32}

        # Title label
        ctk.CTkLabel(self, text="Archive", font=("Times New Roman", 30)).pack(pady=30)

        # Import buttons frame
        import_frame = ctk.CTkFrame(self, fg_color="transparent")
        import_frame.pack(pady=10)

        # Regular Archive button
        ctk.CTkButton(import_frame, text="Regular Archive", command=lambda: self.import_archive("Regular"),**regular_button_style).pack(side=tk.LEFT, padx=5)

        # Irregular Archive button
        ctk.CTkButton(import_frame, text="Irregular Archive", command=lambda: self.import_archive("Irregular"),**regular_button_style).pack(side=tk.LEFT, padx=5)

        # Back button frame
        back_frame = ctk.CTkFrame(self, fg_color="transparent")
        back_frame.place(x=30, y=108)

        back_icon = Image.open("C:/Users/Admin/Documents/Thesis_Estorque/icons/back.png")
        self.back_icon = ctk.CTkImage(light_image=back_icon, dark_image=back_icon, size=(20, 20))
        ctk.CTkButton(back_frame, text="Back", image=self.back_icon,command=self.master.show_main_menu,**back_button_style).pack(side=tk.LEFT)

    def import_archive(self, archive_type):
        print(f"Importing {archive_type} archive...")