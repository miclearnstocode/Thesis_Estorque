import os
import tempfile
import subprocess
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import textwrap, threading
import tkinter as tk
from tkinter import ttk
from rapidfuzz import fuzz
from database import DatabaseHandler
from tkinter import messagebox
from loginform import LoginForm  # For resource_path

class SplashScreen(tk.Toplevel):
    def __init__(self, parent, message="Generating PDF"):
        super().__init__(parent)
        self.title("Launching Rocket")
        width, height = 320, 420
        # Get screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        # Calculate position x, y to center the splash
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)
        self.canvas = tk.Canvas(self, width=200, height=250, bg="black", highlightthickness=0)
        self.canvas.pack(pady=(10,0))
        self.label = ttk.Label(self, text=message, font=("Arial", 13))
        self.label.pack(pady=5)
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=20, pady=5)
        self.progress.start(10)
        self.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close button

        # Draw rocket parts
        self.rocket_y = 200
        self.rocket_parts = self.draw_rocket(90, self.rocket_y)
        self._running = True
        self._dot_count = 0
        self.animate_message()
        self.animate_rocket()
        self.update()

    def draw_rocket(self, x, y):
        # Simple pixel rocket using rectangles and polygons
        body = self.canvas.create_rectangle(x, y, x+20, y+50, fill="white", outline="")
        nose = self.canvas.create_polygon(x, y, x+10, y-20, x+20, y, fill="red", outline="")
        left_fin = self.canvas.create_polygon(x, y+50, x-10, y+60, x, y+40, fill="orange", outline="")
        right_fin = self.canvas.create_polygon(x+20, y+50, x+30, y+60, x+20, y+40, fill="orange", outline="")
        flame = self.canvas.create_polygon(x+5, y+50, x+15, y+50, x+10, y+70, fill="yellow", outline="")
        return [body, nose, left_fin, right_fin, flame]

    def animate_rocket(self):
        if not self._running:
            return
        if self.rocket_y > 30:
            for part in self.rocket_parts:
                self.canvas.move(part, 0, -5)
            self.rocket_y -= 5
            self.after(40, self.animate_rocket)
        else:
            # Optional: show "Launched!" when done
            self.label.config(text="Rocket Launched! Generating PDF...")

    def animate_message(self):
        if not self._running:
            return
        dots = '.' * (self._dot_count % 4)
        self.label.config(text=f"Generating PDF{dots}")
        self._dot_count += 1
        self.after(400, self.animate_message)

    def destroy(self):
        self._running = False
        super().destroy()

class BulkStudentPrinter:
    def __init__(self, parent, not_enrolled_ids, year_level):
        """
        parent: Tkinter parent window
        not_enrolled_ids: list of student IDs to print
        year_level: year/semester string to print for all students
        """
        self.parent = parent
        self.not_enrolled_ids = not_enrolled_ids
        self.year_level = year_level
        self.db_handler = DatabaseHandler()

    def print_all(self):
        # Show splash screen
        splash = SplashScreen(self.parent, "Generating PDF...")
        self.parent.update_idletasks()
        def generate_and_open_pdf():
            try:
                # Prepare PDF
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_filename = f"NotEnrolled_Students_{timestamp}.pdf"
                temp_dir = tempfile.gettempdir()
                pdf_path = os.path.join(temp_dir, pdf_filename)
                c = canvas.Canvas(pdf_path, pagesize=A4)
                c.setTitle(pdf_filename)
                width, height = A4

                pdfmetrics.registerFont(TTFont('TimesNewRoman', 'C://Windows//Fonts//times.ttf'))
                pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', 'timesbd.ttf'))

                for idx, student_id in enumerate(self.not_enrolled_ids):
                    # Fetch student data
                    try:
                        student_data = self.db_handler.fetch_student_data(student_id, self.year_level)
                        curriculum_data = student_data.get("curriculum_data", [])
                        if not curriculum_data:
                            continue
                        student_details = curriculum_data[0]
                        student_name = student_details.get("STUDENT_NAME", "")
                        year = student_details.get("YR", "")
                        sex = student_details.get("SEX", "")
                        age = student_details.get("AGE", "")
                        address = student_details.get("ADDRESS", "")
                    except Exception as e:
                        print(f"Error fetching data for {student_id}: {e}")
                        continue

                    # Header image
                    image_path = LoginForm.resource_path("Image/Header.jpg")
                    header_height = 80
                    c.drawImage(image_path, 0, height - header_height, width=width, height=header_height)

                    y = height - 100
                    c.setFont("TimesNewRoman-Bold", 14)
                    c.drawCentredString(width / 2, y, "COMPUTER STUDIES DEPARTMENT")
                    y -= 20
                    c.drawCentredString(width / 2, y, "PRE-REGISTRATION FORM")
                    y -= 30
                    current_school_year = self.db_handler.get_latest_school_year(student_id)
                    if current_school_year and len(str(current_school_year)) == 4 and str(current_school_year).isdigit():
                        next_year = str(int(current_school_year) + 1)
                        ay_string = f"{current_school_year}-{next_year}"
                    else:
                        ay_string = current_school_year or '______'
                    c.drawCentredString(width / 2, y, f"A.Y. {ay_string}")
                    y -= 20
                    # Map year number to ordinal string
                    year_map = {"1": "1st Year", "2": "2nd Year", "3": "3rd Year", "4": "4th Year"}
                    year_str = year_map.get(str(year).strip()[0], f"{year} Year") if year else "Year Level"
                    c.drawCentredString(width / 2, y, year_str)
                    y -= 30
                    c.setFont("TimesNewRoman", 14)
                    c.drawString(40, y, f"Name: {student_name}")
                    c.drawString(285, y, f"Sex: {sex}")
                    c.drawString(450, y, f"Age: {age}")
                    y -= 20
                    c.drawString(40, y, f"Course/Year Level: {year}")
                    y -= 20
                    c.drawString(40, y, f"Address: {address}")
                    y -= 20
                    c.drawString(40, y, "Parent/Guardian:______________________")
                    y -= 20
                    c.drawString(40, y, "Contact No:__________________________")
                    y -= 20

                    # Table
                    table_columns = ["Course Number", "Course Title", "Unit Credit", "Faculty"]
                    data = [table_columns]
                    total_units = 0
                    seen_rows = set()
                    prerequisite_analysis = self.check_prerequisites(student_data, self.year_level)

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

                    data.append(["Total ", "", total_units, ""])

                    # Row heights
                    row_heights = []
                    for row in data:
                        max_lines = max(len(str(cell).split('\n')) for cell in row)
                        row_heights.append(max(20, max_lines * 15))

                    t = Table(data, colWidths=[1.5*72, 3.5*72, 1*72, 1.5*72], rowHeights=row_heights)
                    t.setStyle(TableStyle([
                        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
                        ('FONTNAME', (0,0), (-1,-1), 'TimesNewRoman'),
                        ('FONTSIZE', (0,0), (-1,-1), 12),
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('FONTNAME', (0,0), (-1,0), 'TimesNewRoman-Bold'),
                        ('FONTSIZE', (0,0), (-1,0), 12),
                        ('FONTNAME', (0,1), (0,-1), 'TimesNewRoman-Bold'),
                        ('FONTNAME', (2,-1), (2,-1), 'TimesNewRoman-Bold'),
                    ]))
                    w, h = t.wrapOn(c, width, height)
                    t.drawOn(c, 30, y - h)
                    y -= h + 40

                    # Certification and signature area
                    c.drawString(50, y, f"This is to certify that the student indicated above is qualified to enroll this A.Y. {current_school_year or '_______________'}")
                    y -= + 50
                    c.drawString(390, y, "__________________________")
                    y -= 20
                    c.drawString(400, y, "Name and Signature of Student")
                    y -= 50
                    start_y = y
                    c.drawString(40, start_y, "Noted:")
                    y = start_y - 30
                    c.drawString(40, y, "MAREVIC P. NAVA, MSCS")
                    y -= 20
                    c.drawString(40, y, "Program Chair, BSCS")
                    y = start_y
                    c.drawRightString(410, y, "Received:")
                    y -= 30
                    c.drawRightString(515, y, "MARIA JONACEL B. SAZON")
                    y -= 20
                    c.drawRightString(462, y, "College Registrar")
                    # Footer image
                    footer_image_path = LoginForm.resource_path("Image/Footer.jpg")
                    footer_height = 50
                    c.drawImage(footer_image_path, 0, 0, width=width, height=footer_height)

                    # Add new page if not last student
                    if idx < len(self.not_enrolled_ids) - 1:
                        c.showPage()
                c.save()

                # Open the PDF
                try:
                    if os.name == 'nt':
                        chrome_path = r'c:/Program Files/Google/Chrome/Application/chrome.exe'
                        if os.path.exists(chrome_path) and os.path.exists(pdf_path):
                            subprocess.run([chrome_path, pdf_path], shell=False)
                        else:
                            os.startfile(pdf_path)
                    else:
                        messagebox.showinfo("PDF Created", f"PDF saved at: {pdf_path}")
                except Exception as e:
                    messagebox.showerror("Printing Error", f"An error occurred while opening PDF: {str(e)}")
            finally:
                # Hide splash screen when done
                splash.destroy()
        threading.Thread(target=generate_and_open_pdf, daemon=True).start()

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
            grade = [1.00, 1.50, 1.75, 2.00, 2.25, 2.50, 2.75, 3.00]


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
                        fuzz.ratio(s.get('COURSE_NO', '').strip().lower(), prereq.lower()) >= 100),None)
                    
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
    