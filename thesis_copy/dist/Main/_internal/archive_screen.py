
import os, subprocess, tempfile
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import CTkMessagebox
import customtkinter as ctk
from PIL import Image
from database import DatabaseHandler
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle, Spacer
from reportlab.platypus import Image
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from loginform import LoginForm

class ArchiveScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.db_handler = DatabaseHandler()
        self.create_widgets()
        # Load and set up the background
        try:
            bg_image = Image.open(LoginForm.resource_path("Image/Gradient.jpg"))
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
        ctk.CTkLabel(self, text="Archive", font=("Times New Roman", 30)).place(x=500, y=30)

        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.place(x=30, y=150)

        # Regular Archive button
        ctk.CTkButton(search_frame, text="Alumni", command=lambda: self.import_archive("Regular"),**regular_button_style, corner_radius=20).pack(side=tk.RIGHT, padx=5)
        # Irregular Archive button
        ctk.CTkButton(search_frame, text="Drop/Stop", command=lambda: self.import_archive("Irregular"),**regular_button_style, corner_radius=20).pack(side=tk.RIGHT, padx=5)

        # Back button frame
        back_frame = ctk.CTkFrame(self, fg_color="transparent")
        back_frame.place(x=30, y=108)

        back_icon = Image.open(LoginForm.resource_path("icons/back.png"))
        self.back_icon = ctk.CTkImage(light_image=back_icon, dark_image=back_icon, size=(20, 20))
        ctk.CTkButton(back_frame, text="Back", image=self.back_icon,command=self.master.show_main_menu,**back_button_style).pack(side=tk.LEFT)

        # Search entry
        self.search_entry = ctk.CTkEntry(search_frame,  placeholder_text="Search by ID, Name, or Year", width=300, corner_radius=30)
        self.search_entry.pack(side="left", padx=(0, 10))

        # Search button
        search_icons = Image.open(LoginForm.resource_path("icons/searchs.png"))
        self.search_icons = ctk.CTkImage(light_image=search_icons, dark_image=search_icons,size=(30,30))
        search_button = ctk.CTkButton(search_frame, text="Search", image=self.search_icons, command=self.perform_search,width=120, **button_style, corner_radius=20)
        search_button.pack(side="left")
        search_button.bind("<Return>", lambda event: self.perform_search())
        # Students table frame
        self.table_frame = ctk.CTkScrollableFrame(self, height=400, width=1000)
        self.table_frame.place(x=30, y=200)

        # Table headers
        headers = ["ID NO", "Full Name", "Year", "Enrolled Year", "Year Graduated"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(self.table_frame, 
                text=header, width=150, height=30, font=("Helvetica", 12, "bold"),
                fg_color="#C9E4CA", corner_radius=5, text_color="black")
            if header in ["Year", "Enrolled Year", "Year Graduated"]:
                label.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            else:
                label.grid(row=0, column=i, padx=5, pady=5, sticky="w")
            self.table_frame.grid_columnconfigure(i, weight=1, minsize=150)

    def load_students(self, students=None):
        # Clear existing entries
        for widget in self.table_frame.winfo_children()[5:]:  # Assuming 5 header labels now
            widget.destroy()

        # If no students provided, fetch all
        if students is None:
            students = self.db_handler.get_students_list()

        self.selected_students = []

        # Populate table
        for row, student in enumerate(students, 1):
            # Check if student is a tuple or dictionary
            if isinstance(student, tuple):
                # If tuple, use index-based access
                student_data = {
                    'ID_NO': student[0],
                    'FULL_NAME': student[1],
                    'YR': student[2],  # Current year (e.g., 1, 2, 3, 4)
                    'ENROLLED_YEAR': student[3],  # Year the student enrolled
                    'YEAR_GRADUATED': "N/A"  # Default value
                }
            else:
                # If dictionary, use key-based access
                student_data = student

            # Calculate Year Graduated
            current_year = student_data.get('YR', 1)  # Default to 1 if not provided
            enrolled_year = student_data.get('ENROLLED_YEAR', 2020)  # Default to 2020 if not provided

            # If the student is in their fourth year, second semester, they are graduating this year
            if current_year == 4:  # Fourth year
                student_data['YEAR_GRADUATED'] = enrolled_year + 4  # Graduation year
            else:
                # If not in fourth year, set to "N/A" or calculate expected graduation year
                student_data['YEAR_GRADUATED'] = enrolled_year + 4  # Expected graduation year

            # Map 'SCHOOL_YEAR' to 'YEAR_GRADUATED' (if needed)
            if 'SCHOOL_YEAR' in student_data:
                student_data['YEAR_GRADUATED'] = student_data['SCHOOL_YEAR']

            # Create clickable buttons for each student field
            for col, key in enumerate(['ID_NO', 'FULL_NAME', 'YR', 'ENROLLED_YEAR', 'YEAR_GRADUATED']):
                btn = ctk.CTkButton(
                    self.table_frame,
                    text=str(student_data.get(key, "N/A")),  # Use "N/A" if key is missing
                    fg_color="transparent",  # Make it look like a label
                    hover_color="#707070",   # Add hover effect
                    text_color="black",      # Match label text color
                    command=lambda s=student_data: self.on_student_click(s)  # Bind click event
                )
                btn.grid(row=row, column=col, padx=5, pady=2, sticky="w" if col < 2 else "ew")
    styles = getSampleStyleSheet()   
    # Register Times New Roman font
    pdfmetrics.registerFont(TTFont('TimesNewRoman', 'C:\\Windows\\Fonts\\times.ttf'))
    pdfmetrics.registerFont(TTFont('TimesNewRomanBold', 'C:\\Windows\\Fonts\\timesbd.ttf'))


    def on_student_click(self, student_data):
        def add_header_footer(canvas, doc):
            canvas.saveState()

            page_number = canvas.getPageNumber()
            page_width = doc.pagesize[0]
            page_height = doc.pagesize[1]

            # Header image on every page
            header_image_path = "Image/Header.jpg"
            canvas.drawImage(header_image_path, x=0, y=page_height - 70, width=595.27, height=70)

            # Header text only on first page
            if page_number == 1:
                canvas.setFont("TimesNewRomanBold", 16)
                text = "BACHELOR OF SCIENCE IN COMPUTER SCIENCE"
                text_width = canvas.stringWidth(text, "Helvetica-Bold", 14)
                x_centered = (page_width - text_width) / 2
                canvas.drawString(x_centered, page_height - 120, text)

            # Footer image on every page
            footer_image_path = "Image/Footer.jpg"
            canvas.drawImage(footer_image_path, x=0, y=0, width=595.27, height=70)
            
            # Non-official logo (watermark effect)
            logo_path = "icons/non_official.jpg"
            
            # Load logo with transparency
            logo = ImageReader(logo_path)
            
            # Get logo dimensions
            logo_width, logo_height = logo.getSize()
            
            # Scale logo (adjust as needed)
            scale_factor = 0.5  # Adjust this to resize logo
            scaled_width = logo_width * scale_factor
            scaled_height = logo_height * scale_factor
            
            # Calculate center position
            x_centered = (page_width - scaled_width) / 2
            y_centered = (page_height - scaled_height) / 2

            # Prepare for tilted, transparent logo
            canvas.saveState()
            
            # Translate to the center of the page
            canvas.translate(page_width/2, page_height/2)
            
            # Rotate the canvas (adjust angle as needed)
            canvas.rotate(30)  # 30-degree tilt
            
            # Translate back
            canvas.translate(-page_width/2, -page_height/2)

            # Set low opacity for watermark effect
            canvas.setFillColorRGB(0, 0, 0, 0.2)  # Very light, almost transparent
            
            # Draw logo behind text (send backward)
            canvas.drawImage(
                logo_path, 
                x=x_centered, 
                y=y_centered, 
                width=scaled_width, 
                height=scaled_height, 
                mask='auto',  # Preserves transparency
                preserveAspectRatio=True)
            canvas.restoreState()

        try:
            temp_pdf =tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            pdf_filename = temp_pdf.name
            temp_pdf.close()
            # Adjust page layout to account for header and footer
            def page_layout(canvas, doc):
                add_header_footer(canvas, doc)

            # Create document with adjusted margins
            doc = BaseDocTemplate(pdf_filename, pagesize=A4)

            # Create frames that account for header and footer
            frame = Frame(
                doc.leftMargin, 
                doc.bottomMargin + 100,  # Add space for footer
                doc.width, 
                doc.height - 200,  # Reduce height for header and footer
                id='normal'
            )

            # Create page template
            template = PageTemplate(id='TestTemplate', frames=frame, onPage=page_layout)
            doc.addPageTemplates([template])

            # Define styles
            styles = getSampleStyleSheet()
            # Create a custom style with Times New Roman
            times_normal_style = ParagraphStyle(
                'TimesNormalStyle',
                parent=styles['Normal'],
                fontName='TimesNewRoman',
                fontSize=12
            )
            # Create a bold Times New Roman style
            times_bold_style = ParagraphStyle(
                'TimesBoldStyle',
                parent=styles['Normal'],
                fontName='TimesNewRomanBold',
                fontSize=12
            )

            # Create a list to hold the PDF content
            content = []

            # Add student information as paragraphs
            student_info = [
                ("ID Number", student_data.get('ID_NO', 'N/A')),
                ("Full Name", student_data.get('FULL_NAME', 'N/A')),
                ("Year", student_data.get('YR', 'N/A')),
                ("Enrolled Year", student_data.get('ENROLLED_YEAR', '')),
                ("Year Graduated", student_data.get('YEAR_GRADUATED', 'N/A'))
            ]

            for label, value in student_info:
                content.append(Paragraph(f"<b>{label}:</b> {value}", times_normal_style))
                content.append(Spacer(1, 12))
            # Add an extra space after "Year Graduated"
            content.append(Spacer(1, 36))
            # Fetch curriculum data
            curriculum_columns, curriculum_data = self.db_handler.get_curriculum_regular()

            # Fetch student's grades
            student_id = student_data.get('ID_NO', '')
            # Add comprehensive debugging
            print("Student Data:", student_data)
            print("Student ID:", student_id)
            course_data = self.db_handler.get_course_data(student_id) or {}
            # Debugging course data
            """print("Retrieved Course Data:")
            for table, courses in course_data.items():
                print(f"{table}: {courses}")"""


            # Define the custom style for year semester
            year_level_style = ParagraphStyle(
                'YearLevelStyle',
                parent=styles['Normal'],  # Use Normal as the base style
                fontSize=12,              # Set font size to 12
                fontName='TimesNewRomanBold',
                spaceAfter=5
            )
            # Prepare combined course data for table
            combined_course_data = {}

            # Normalize curriculum data to dictionaries
            if curriculum_data and isinstance(curriculum_data[0], (tuple, list)):
                curriculum_data = [
                    dict(zip(curriculum_columns, course)) 
                    for course in curriculum_data
                ]
                
                # Group courses by year and semester
                for curriculum_course in curriculum_data:
                    def safe_get(course, key, default=''):
                        return course.get(key, default) if isinstance(course, dict) else default

                    year_level = safe_get(curriculum_course, 'YEAR_LEVEL')
                    #print(f"Processing year level: {year_level}")  # Debugging output
                    course_no = safe_get(curriculum_course, 'COURSE_NO')
                    descriptive_title = safe_get(curriculum_course, 'DESCRIPTIVE_TITLE')
                    units = safe_get(curriculum_course, 'UNITS')
                    lec = safe_get(curriculum_course, 'LEC')
                    lab = safe_get(curriculum_course, 'LAB')
                    prerequisite = safe_get(curriculum_course, 'PREREQUISITE')

                    grade = 'N/A'

                    for table_name, courses in course_data.items():
                        for course_item in courses:
                            if isinstance(course_item, list) and len(course_item) >= 2 and course_item[0] == course_no:
                                grade = course_item[1]
                                break
                            elif isinstance(course_item, dict) and course_item.get('course_code') == course_no:
                                grade = course_item.get('grade', 'N/A')
                                break

                        if grade != 'N/A':
                            break

                    # Use the updated year level titles
                    year_semester = self.get_year_level_title(year_level)

                    if year_semester not in combined_course_data:
                        combined_course_data[year_semester] = []

                    combined_course_data[year_semester].append([
                        Paragraph(course_no, times_normal_style),
                        Paragraph(descriptive_title, times_normal_style),
                        units,
                        lec,
                        lab,
                        Paragraph(prerequisite, times_normal_style),
                        grade
                    ])

            for year_semester, course_data in combined_course_data.items():
                if course_data:
                    course_table = Table(
                        [["Course No.", "Descriptive Title", "Units", "Lec", "Lab", "Prerequisite", "Grade"]] + course_data,
                        colWidths=[60, 200, 40, 40, 40, 80, 40]
                    )
                    course_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'TimesNewRomanBold'),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.transparent),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('FONTNAME', (0, 1), (-1, -1), 'TimesNewRoman')
                    ]))
                    content.append(Paragraph("&nbsp;&nbsp;" + year_semester, year_level_style))
                    content.append(course_table)
                    content.append(Spacer(1, 42))

            doc.build(content)

            if os.name == 'nt':
                chrome_path = r'C:/Program Files/Google/Chrome/Application/chrome.exe'
                if os.path.exists(chrome_path):
                    subprocess.run([chrome_path, pdf_filename], shell=False)
                else:
                    messagebox.showerror("Printing Error", "Google Chrome executable not found.")
            else:
                messagebox.showerror("Printing Error", "Printing is only supported on Windows.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Printing Error", f"An error occurred while printing: {str(e)}")


    def get_year_level_title(self, year_level):
        """Simple mapping of year levels to descriptive titles"""
        return {
            "1.1": "First Year First Semester",
            "1.2": "First Year Second Semester",
            "2.1": "Second Year First Semester",
            "2.2": "Second Year Second Semester",
            "3.1": "Third Year First Semester",
            "3.2": "Third Year Second Semester",
            "4.1": "Fourth Year First Semester",
            "4.2": "Fourth Year Second Semester"}.get(str(year_level), year_level)

    def perform_search(self):
        search_term = self.search_entry.get()
        if search_term:
            students = self.db_handler.search_students(search_term)
            self.load_students(students)
        else:
            # If search is empty, reload all students
            self.load_students()


    def import_archive(self, archive_type):
        # Create a new toplevel window for archive import
        import_window = ctk.CTkToplevel(self)
        import_window.title(f"{archive_type} Archive Import")
        import_window.geometry("600x400")

        # Base style for labels and buttons
        label_style = {"fg_color": "white","text_color": "black","corner_radius": 10,"width": 300,"height": 40}

        button_style = {"fg_color": "#4CAF50","hover_color": "#45a049","text_color": "white","width": 100,"height": 30}

        # Frame to hold archive import components
        import_frame = ctk.CTkFrame(import_window, fg_color="transparent")
        import_frame.place(x=150, y=50)

        # Graduates Label with Import Button
        graduates_label = ctk.CTkLabel(import_frame, text="Graduates", **label_style)
        graduates_label.pack(pady=10)

        graduates_import_btn = ctk.CTkButton(import_frame, text="Import", command=self.import_graduates,**button_style)
        graduates_import_btn.pack(pady=5)

        # Curriculum Label with Import Button
        curriculum_label = ctk.CTkLabel(import_frame, text="Curriculum", **label_style)
        curriculum_label.pack(pady=10)

        curriculum_import_btn = ctk.CTkButton(import_frame, text="Import", command=self.import_curriculum,**button_style)
        curriculum_import_btn.pack(pady=5)

    def import_graduates(self):
        """
        Method to import graduates data with CustomTkinter components
        """
        try:
            # Open file dialog to select graduates file
            file_path = filedialog.askopenfilename(
                title="Select Graduates File",
                filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")])

            if not file_path:
                return  # User cancelled file selection

            # Create progress window
            progress_window = ctk.CTkToplevel(self)
            progress_window.title("Importing Graduates")
            progress_window.geometry("400x200")
            progress_window.resizable(False, False)

            # Progress frame
            progress_frame = ctk.CTkFrame(progress_window, fg_color="transparent")
            progress_frame.pack(expand=True, fill="both", padx=20, pady=20)

            # Status label
            status_label = ctk.CTkLabel(progress_frame, text="Importing Graduates...",  font=("Arial", 16))
            status_label.pack(pady=(0, 10))

            # Progress bar
            progress_bar = ctk.CTkProgressBar(progress_frame,width=300, height=20)
            progress_bar.pack(pady=(0, 10))
            progress_bar.set(0)

            # Detailed status label
            detail_label = ctk.CTkLabel(progress_frame, text="", font=("Arial", 12))
            detail_label.pack(pady=(0, 10))

            # Determine file type and import accordingly
            file_extension = os.path.splitext(file_path)[1].lower()

            def perform_import():
                try:
                    # Simulate import process
                    for i in range(1, 11):
                        progress_bar.set(i/10)
                        detail_label.configure(text=f"Processing... {i*10}%")
                        progress_window.update()
                        self.after(200)  # Simulate processing time

                    # Actual import based on file type
                    if file_extension == '.csv':
                        self.import_csv_graduates(file_path)
                    elif file_extension in ['.xlsx', '.xls']:
                        self.import_excel_graduates(file_path)
                    else:
                        raise ValueError("Unsupported file format")

                    # Success dialog
                    success_dialog = ctk.CTkToplevel(progress_window)
                    success_dialog.title("Import Successful")
                    success_dialog.geometry("300x150")
                    success_dialog.resizable(False, False)

                    success_label = ctk.CTkLabel(success_dialog, text="Graduates data\nimported successfully!",  font=("Arial", 14), text_color="green")
                    success_label.pack(expand=True, pady=10)

                    close_btn = ctk.CTkButton(success_dialog, text="Close",  command=success_dialog.destroy,width=100)
                    close_btn.pack(pady=10)

                    # Close progress window
                    progress_window.destroy()

                except Exception as e:
                    # Error dialog
                    error_dialog = ctk.CTkToplevel(progress_window)
                    error_dialog.title("Import Error")
                    error_dialog.geometry("300x150")
                    error_dialog.resizable(False, False)

                    error_label = ctk.CTkLabel(error_dialog, text=f"Import failed:\n{str(e)}", font=("Arial", 12), text_color="red")
                    error_label.pack(expand=True, pady=10)

                    close_btn = ctk.CTkButton(error_dialog,text="Close", command=error_dialog.destroy,width=100,fg_color="red",hover_color="darkred")
                    close_btn.pack(pady=10)

                    # Close progress window
                    progress_window.destroy()

            # Start import in a separate thread or after method
            progress_window.after(500, perform_import)

        except Exception as e:
            # Fallback error handling
            CTkMessagebox(title="Critical Error", message=str(e), icon="cancel")

    def import_curriculum(self):
        """
        Method to import curriculum data with CustomTkinter components
        Similar implementation to import_graduates
        """
        try:
            # Open file dialog to select curriculum file
            file_path = filedialog.askopenfilename(
                title="Select Curriculum File",
                filetypes=[("CSV files", "*.csv"),("Excel files", "*.xlsx"),("All files", "*.*")])

            if not file_path:
                return  # User cancelled file selection

            # Create progress window
            progress_window = ctk.CTkToplevel(self)
            progress_window.title("Importing Curriculum")
            progress_window.geometry("400x200")
            progress_window.resizable(False, False)

            # Progress frame
            progress_frame = ctk.CTkFrame(progress_window, fg_color="transparent")
            progress_frame.pack(expand=True, fill="both", padx=20, pady=20)

            # Status label
            status_label = ctk.CTkLabel(progress_frame, text="Importing Curriculum...", font=("Arial", 16))
            status_label.pack(pady=(0, 10))

            # Progress bar
            progress_bar = ctk.CTkProgressBar(progress_frame, width=300, height=20)
            progress_bar.pack(pady=(0, 10))
            progress_bar.set(0)

            # Detailed status label
            detail_label = ctk.CTkLabel(progress_frame, text="", font=("Arial", 12))
            detail_label.pack(pady=(0, 10))

            # Determine file type and import accordingly
            file_extension = os.path.splitext(file_path)[1].lower()

            def perform_import():
                try:
                    # Simulate import process
                    for i in range(1, 11):
                        progress_bar.set(i/10)
                        detail_label.configure(text=f"Processing... {i*10}%")
                        progress_window.update()
                        self.after(200)  # Simulate processing time

                    # Actual import based on file type
                    if file_extension == '.csv':
                        self.import_csv_curriculum(file_path)
                    elif file_extension in ['.xlsx', '.xls']:
                        self.import_excel_curriculum(file_path)
                    else:
                        raise ValueError("Unsupported file format")

                    # Success dialog
                    success_dialog = ctk.CTkToplevel(progress_window)
                    success_dialog.title("Import Successful")
                    success_dialog.geometry("300x150")
                    success_dialog.resizable(False, False)

                    success_label = ctk.CTkLabel(success_dialog,text="Curriculum data\nimported successfully!", font=("Arial", 14),text_color="green")
                    success_label.pack(expand=True, pady=10)

                    close_btn = ctk.CTkButton(success_dialog, text="Close", command=success_dialog.destroy, width=100)
                    close_btn.pack(pady=10)

                    # Close progress window
                    progress_window.destroy()

                except Exception as e:
                    # Error dialog
                    error_dialog = ctk.CTkToplevel(progress_window)
                    error_dialog.title("Import Error")
                    error_dialog.geometry("300x150")
                    error_dialog.resizable(False, False)

                    error_label = ctk.CTkLabel(error_dialog, text=f"Import failed:\n{str(e)}", font=("Arial", 12), text_color="red")
                    error_label.pack(expand=True, pady=10)

                    close_btn = ctk.CTkButton(error_dialog, text="Close", command=error_dialog.destroy, width=100, fg_color="red", hover_color="darkred")
                    close_btn.pack(pady=10)

                    # Close progress window
                    progress_window.destroy()

            # Start import in a separate thread or after method
            progress_window.after(500, perform_import)

        except Exception as e:
            # Fallback error handling
            CTkMessagebox(title="Critical Error", message=str(e), icon="cancel")