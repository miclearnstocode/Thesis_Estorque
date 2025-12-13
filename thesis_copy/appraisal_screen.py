import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import pandas as pd
from rapidfuzz import fuzz, process
from database import DatabaseHandler
from PIL import Image
import re 
from loginform import LoginForm
from tkcalendar import DateEntry

class AppraisalScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.data_appraised = False
        self.matched_subjects = None 
        self.basic_info_entered = False
        # Detect screen size for responsive design
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        
        # Set responsive font sizes based on screen size
        if self.screen_width < 1366:  # Small laptop
            self.title_font_size = 28
            self.subtitle_font_size = 12
            self.field_font_size = 11
            self.entry_font_size = 12
        elif self.screen_width < 1920:  # Standard HD
            self.title_font_size = 32
            self.subtitle_font_size = 14
            self.field_font_size = 12
            self.entry_font_size = 13
        else:  # Large screens
            self.title_font_size = 36
            self.subtitle_font_size = 16
            self.field_font_size = 13
            self.entry_font_size = 14
        # Set modern colors
        self.primary_color = "#2E86AB"  # Modern blue
        self.secondary_color = "#A23B72"  # Modern purple
        self.accent_color = "#F18F01"  # Modern orange
        self.bg_color = "#F7F9FC"  # Light gray background
        self.card_color = "#FFFFFF"  # White for cards
        self.text_color = "#2C3E50"  # Dark text
        self.border_color = "#E1E8ED"  # Light border
        
        # Configure frame background
        self.configure(fg_color=self.bg_color)
        
        try:
            self.dept_bg = Image.open(LoginForm.resource_path("Image/Gradient.jpg"))
            self.bg_image_pil = self.dept_bg  
            
            # Create initial CTkImage with frame's size
            initial_width = self.winfo_width() or 736 
            initial_height = self.winfo_height() or 600  
            self.bg_image = ctk.CTkImage(light_image=self.bg_image_pil, dark_image=self.bg_image_pil, size=(initial_width, initial_height))

            self.bg_label = ctk.CTkLabel(self, image=self.bg_image, text="")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Bind resize event
            self.bind('<Configure>', self.resize_background)
            
        except Exception as e:
            print(f"Error loading background image: {e}")
        
        # Main title with modern styling
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=2, pady=(20, 10), sticky="ew")
        
        self.label = ctk.CTkLabel(title_frame, text="Appraisal", font=("Helvetica", 32, "bold"), fg_color="transparent",text_color=self.text_color)
        self.label.pack()
        
        subtitle = ctk.CTkLabel(title_frame,text="Student Information & Curriculum Matching",font=("Helvetica", 14),text_color="#7F8C8D",fg_color="transparent")
        subtitle.pack()
        
        # Keep original notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, padx=20, pady=10, sticky="nsew", columnspan=2)

        # Frames
        self.frame1 = ctk.CTkFrame(self.notebook, fg_color=self.bg_color)
        self.frame1.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.notebook.add(self.frame1, text="Basic Information")

        # Create a modern card for basic information
        self.info_card = ctk.CTkFrame(self.frame1, fg_color=self.card_color,corner_radius=12,border_width=1,border_color=self.border_color)
        self.info_card.pack(fill="both", expand=True, padx=20, pady=20)
        # Create a scrollable frame container
        self.scrollable_frame = ctk.CTkScrollableFrame(self.info_card,fg_color="transparent",scrollbar_button_color=self.border_color,scrollbar_button_hover_color=self.primary_color)
        self.scrollable_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Card header - place in scrollable frame
        card_header = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        card_header.pack(fill="x", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(card_header,text="📝 Basic Student Information",font=("Helvetica", 18, "bold"),text_color=self.text_color).pack(side="left")
        
        # Add a step indicator
        step_indicator = ctk.CTkLabel(card_header,text="Step 1 of 3",font=("Helvetica", 12),text_color=self.primary_color,fg_color="transparent")
        step_indicator.pack(side="right")
        
        # Year and Semester selection in a modern row
        date_selection_frame = ctk.CTkFrame(self.info_card, fg_color="transparent")
        date_selection_frame.pack(fill="x", padx=20, pady=(10, 15))
        
        # Year selection with icon
        year_container = ctk.CTkFrame(date_selection_frame, fg_color="transparent")
        year_container.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(year_container,text="🗓️ Academic Year",font=("Helvetica", 12, "bold"),text_color=self.text_color).pack(anchor="w")
        
        self.year_var = ctk.StringVar()
        self.year_dropdown = ctk.CTkComboBox(
            year_container,
            values=[str(year) for year in range(2023, 2030)],
            variable=self.year_var,
            state="readonly",
            width=180,
            height=38,
            font=("Helvetica", 13),
            dropdown_font=("Helvetica", 12),
            fg_color="white",
            text_color=self.text_color,
            border_color=self.border_color,
            border_width=1,
            corner_radius=8,
            button_color=self.primary_color,
            button_hover_color="#1E6A8C",
            command=self.auto_generate_appraised_id
        )
        self.year_dropdown.pack(pady=(5, 0))
        self.year_dropdown.set("Select Year")
        
        # Semester selection with icon
        semester_container = ctk.CTkFrame(date_selection_frame, fg_color="transparent")
        semester_container.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(semester_container,text="📚 Semester",font=("Helvetica", 12, "bold"),text_color=self.text_color).pack(anchor="w")
        
        self.semester_var = ctk.StringVar()
        self.semester_dropdown = ctk.CTkComboBox(
            semester_container,
            values=["1st Semester", "2nd Semester"],
            variable=self.semester_var,
            state="readonly",
            width=180,
            height=38,
            font=("Helvetica", 13),
            dropdown_font=("Helvetica", 12),
            fg_color="white",
            text_color=self.text_color,
            border_color=self.border_color,
            border_width=1,
            corner_radius=8,
            button_color=self.primary_color,
            button_hover_color="#1E6A8C",
            command=self.auto_generate_appraised_id
        )
        self.semester_dropdown.pack(pady=(5, 0))
        self.semester_dropdown.set("Select Semester")
        
        # Appraised ID display with modern styling
        appraised_id_container = ctk.CTkFrame(date_selection_frame, fg_color="transparent")
        appraised_id_container.pack(side="left")
        
        ctk.CTkLabel(
            appraised_id_container,
            text="🆔 Appraised ID",
            font=("Helvetica", 12, "bold"),
            text_color=self.text_color).pack(anchor="w")
        
        self.appraised_id_label = ctk.CTkLabel(
            appraised_id_container,
            text="Will appear here",
            font=("Helvetica", 13),
            text_color="#7F8C8D",
            fg_color="#F0F8FF",
            corner_radius=8,
            width=180,
            height=38
        )
        self.appraised_id_label.pack(pady=(5, 0))
        
        # Separator
        separator = ctk.CTkFrame(self.info_card, fg_color=self.border_color, height=1)
        separator.pack(fill="x", padx=20, pady=15)
        
        # Create entries in horizontal rows (3 columns per row)
        self.create_horizontal_entries()
        
        # Next button with modern styling
        button_container = ctk.CTkFrame(self.info_card, fg_color="transparent")
        button_container.pack(fill="x", padx=20, pady=(20, 15))
        
        # Button style configuration for modern design
        button_style = {
            "fg_color": self.primary_color, 
            "hover_color": "#1E6A8C",
            "text_color": "white", 
            "width": 120, 
            "height": 35, 
            "border_width": 0,
            "corner_radius": 8,
            "font": ("Helvetica", 12, "bold")
        }
        
        self.next_button = ctk.CTkButton(
            button_container,
            text="Continue →",
            command=self.check_basic_info,
            **button_style
        )
        self.next_button.pack(side="right")
        
        # Bind Enter key to the next button
        self.bind('<Return>', lambda e: self.check_basic_info())

        # Configure Treeview style
        style = ttk.Style()
        style.configure("Treeview", rowheight=35, font=("Helvetica", 12)) 
        style.configure("Treeview.Heading", font=("Helvetica", 12))
        
        # Keep original Treeview frames
        self.frame2 = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.frame2, text="Matched Subjects")

        self.tree1 = ttk.Treeview(self.frame2, columns=("Course_No", "Descriptive_Title", "Year_Level", "Units", "Lec", "Lab", "Prerequisite", "Grades"),show="headings", height=20)
        self.tree1.grid(row=0, column=0, sticky="nsew")

        self.tree1.heading("Course_No", text="Course No")
        self.tree1.heading("Descriptive_Title", text="Descriptive Title")
        self.tree1.heading("Year_Level", text="Year Level")
        self.tree1.heading("Units", text="Units")
        self.tree1.heading("Lec", text="Lec")
        self.tree1.heading("Lab", text="Lab")
        self.tree1.heading("Prerequisite", text="Prerequisite")
        self.tree1.heading("Grades", text="Grades")

        self.tree1.column("Course_No", width=50, anchor='center')
        self.tree1.column("Descriptive_Title", width=290, anchor='center')
        self.tree1.column("Year_Level", width=40, anchor='center')
        self.tree1.column("Units", width=25, anchor='center')
        self.tree1.column("Lec", width=25, anchor='center')
        self.tree1.column("Lab", width=25, anchor='center')
        self.tree1.column("Prerequisite", width=100, anchor='center')
        self.tree1.column("Grades", width=30, anchor='center')

        self.tree1.tag_configure('oddrow', background='lightgrey')
        self.tree1.tag_configure('evenrow', background='white')
        
        self.frame3 = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.frame3, text="Subject To Enroll")

        self.tree2 = ttk.Treeview(self.frame3, columns=("Course_No", "Descriptive_Title", "Year_Level", "Units", "Lec", "Lab", "Prerequisite","Grades"),show="headings", height=15)
        self.tree2.grid(row=0, column=0, sticky="nsew")

        self.tree2.heading("Course_No", text="Course No")
        self.tree2.heading("Descriptive_Title", text="Descriptive Title")
        self.tree2.heading("Year_Level", text="Year Level")
        self.tree2.heading("Units", text="Units")
        self.tree2.heading("Lec", text="Lec")
        self.tree2.heading("Lab", text="Lab")
        self.tree2.heading("Prerequisite", text="Prerequisite")
        self.tree2.heading("Grades", text="Grades")

        self.tree2.column("Course_No", width=50, anchor='center')
        self.tree2.column("Descriptive_Title", width=290, anchor='center')
        self.tree2.column("Year_Level", width=40, anchor='center')
        self.tree2.column("Units", width=25, anchor='center')
        self.tree2.column("Lec", width=25, anchor='center')
        self.tree2.column("Lab", width=25, anchor='center')
        self.tree2.column("Prerequisite", width=100, anchor='center')
        self.tree2.column("Grades", width=30, anchor='center')

        self.tree2.tag_configure('oddrow', background='lightgrey')
        self.tree2.tag_configure('evenrow', background='white')

        # Button frames - Modern design
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 20), padx=20, sticky="ew")

        appraise_icon = Image.open(LoginForm.resource_path("icons/appraisal.png"))
        self.appraise_icon = ctk.CTkImage(light_image=appraise_icon, dark_image=appraise_icon, size=(25, 25))
        self.appraise_button = ctk.CTkButton(
            button_frame, 
            text="Appraise", 
            image=self.appraise_icon,
            command=self.start_appraisal,
            fg_color=self.primary_color,
            hover_color="#1E6A8C",
            text_color="white",
            width=120,
            height=38,
            corner_radius=8,
            font=("Helvetica", 12, "bold")
        )
        self.appraise_button.pack(side="left", padx=5)
        
        save_icon = Image.open(LoginForm.resource_path("icons/save.png"))
        self.save_icon = ctk.CTkImage(light_image=save_icon, dark_image=save_icon, size=(25, 25))
        self.save_button = ctk.CTkButton(
            button_frame, 
            text="Save", 
            image=self.save_icon,
            command=self.save_to_database, 
            state="disabled",
            fg_color=self.secondary_color,
            hover_color="#8A2D5F",
            text_color="white",
            width=120,
            height=38,
            corner_radius=8,
            font=("Helvetica", 12, "bold")
        )
        self.save_button.pack(side="left", padx=5)

        self.note_label = ctk.CTkLabel(
            button_frame, 
            text="NOTE: Please select student curriculum first, then existing curriculum when appraising", 
            font=("Helvetica", 12, 'italic'), 
            text_color="#7F8C8D",
            fg_color="transparent"
        )
        self.note_label.pack(side="left", padx=20, expand=True, fill="x")

        back_icon = Image.open(LoginForm.resource_path("icons/back.png"))
        self.back_icon = ctk.CTkImage(light_image=back_icon, dark_image=back_icon, size=(25, 25))
        back_button = ctk.CTkButton(
            button_frame, 
            text="Back", 
            image=self.back_icon,
            command=self.master.show_main_menu,
            fg_color="transparent",
            hover_color="#F5F7FA",
            text_color=self.text_color,
            border_color=self.border_color,
            border_width=1,
            width=100,
            height=38,
            corner_radius=8,
            font=("Helvetica", 12)
        )
        back_button.pack(side="right", padx=5)

        # Configure grid weights to allow proper expansion
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.frame2.grid_rowconfigure(0, weight=1)
        self.frame2.grid_columnconfigure(0, weight=1)
        self.frame3.grid_rowconfigure(0, weight=1)
        self.frame3.grid_columnconfigure(0, weight=1)

    def create_horizontal_entries(self):
        """Create entries in a modern horizontal layout (3 columns per row)"""

        # Define entry fields with icons and validation rules
        field_configs = [
            # Row 1
            {
                "label": "👤 ID Number", 
                "key": "ID No:", 
                "row": 0, 
                "col": 0,
                "validation": self.validate_id_no,
                "placeholder": "e.g., 2023-00123"
            },
            {
                "label": "👤 Last Name", 
                "key": "Last Name:", 
                "row": 0, 
                "col": 1,
                "validation": self.validate_last_name,
                "placeholder": "Enter last name"
            },
            {
                "label": "👤 First Name", 
                "key": "First Name:", 
                "row": 0, 
                "col": 2,
                "validation": self.validate_first_name,
                "placeholder": "Enter first name"
            },
            # Row 2
            {
                "label": "👤 Middle Name", 
                "key": "Middle Name:", 
                "row": 1, 
                "col": 0,
                "validation": self.validate_middle_name,
                "placeholder": "Optional"
            },
            {
                "label": "🎓 Year Level", 
                "key": "Year Level:", 
                "row": 1, 
                "col": 1,
                "validation": self.validate_year_level,
                "placeholder": "1, 2, 3, or 4"
            },
            {
                "label": "⚤ Sex", 
                "key": "Sex:", 
                "row": 1, 
                "col": 2,
                "validation": self.validate_sex,
                "placeholder": "M or F"
            },
            # Row 3
            {
                "label": "🎂 Age", 
                "key": "Age:", 
                "row": 2, 
                "col": 0,
                "validation": self.validate_age,
                "placeholder": "e.g., 18"
            },
            {
                "label": "📅 Birthday", 
                "key": "Birthday:", 
                "row": 2, 
                "col": 1,
                "validation": None,
                "placeholder": "Click calendar icon"
            },
            {
                "label": "📱 Contact Number", 
                "key": "Contact Number:", 
                "row": 2, 
                "col": 2,
                "validation": self.validate_contact,
                "placeholder": "e.g., 912-3456789"
            },
            # Row 4
            {
                "label": "📧 Email Address", 
                "key": "Email Address:", 
                "row": 3, 
                "col": 0,
                "validation": self.validate_email,
                "placeholder": "name@example.com"
            },
            {
                "label": "🏠 Address", 
                "key": "Address:", 
                "row": 3, 
                "col": 1,
                "validation": self.validate_address,
                "placeholder": "Street, City, Province"
            },
            {
                "label": "👨‍👩‍👧‍👦 Parent/Guardian", 
                "key": "Parent/Guardian:", 
                "row": 3, 
                "col": 2,
                "validation": self.validate_parent_guardian,
                "placeholder": "Full name"
            }
        ]
        
        self.entries = {}
        
        # Create a grid frame for the entries INSIDE SCROLLABLE FRAME
        entries_grid = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        entries_grid.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Configure grid columns with equal weight AND MINIMUM WIDTH
        for i in range(3):
            entries_grid.grid_columnconfigure(i, weight=1, uniform="column", minsize=250)
        
        # Calculate row height based on screen size
        screen_height = self.winfo_screenheight()
        if screen_height < 768:  # Small screens
            row_height = 80
        elif screen_height < 1080:  # Medium screens
            row_height = 90
        else:  # Large screens
            row_height = 100
        
        # Create each field
        for i, config in enumerate(field_configs):
            field_frame = ctk.CTkFrame(entries_grid, fg_color="transparent")
            field_frame.grid(row=config["row"], column=config["col"], padx=10, pady=8, sticky="nsew")
            
            # Field label with icon
            label = ctk.CTkLabel(field_frame,text=config["label"],font=("Helvetica", 12, "bold"),text_color=self.text_color, fg_color="transparent",wraplength=200)  # Allow text wrapping on small screens
            
            label.pack(anchor="w", pady=(0, 5))
            
            if config["key"] == "Birthday:":
                # Special handling for birthday with calendar picker
                birthday_container = ctk.CTkFrame(field_frame, fg_color="transparent")
                birthday_container.pack(fill="x")
                
                # Create the enhanced date picker
                date_picker = self.create_enhanced_date_picker(birthday_container)
                self.entries[config["key"]] = date_picker
            else:
                # Regular entry field with responsive width
                entry_container = ctk.CTkFrame(field_frame, fg_color="transparent")
                entry_container.pack(fill="x")
                
                entry = ctk.CTkEntry(
                    entry_container,
                    placeholder_text=config["placeholder"],
                    font=("Helvetica", 13),
                    height=42,
                    border_width=1,
                    border_color=self.border_color,
                    fg_color="white",
                    text_color=self.text_color,
                    corner_radius=8,
                    validate="key" if config["validation"] else "none",
                    validatecommand=(self.register(config["validation"]), '%P') if config["validation"] else None)
                entry.pack(side="left", fill="x", expand=True)
                
                self.entries[config["key"]] = entry
                # Bind Enter and Tab keys for navigation
                entry.bind('<Return>', lambda e, current=i, total=len(field_configs): 
                          self.move_to_next_entry(e, current, total))
                entry.bind('<Tab>', lambda e, current=i, total=len(field_configs): 
                          self.move_to_next_entry(e, current, total))
            
        # Configure grid rows with responsive height
        for i in range(4):
            entries_grid.grid_rowconfigure(i, weight=0, minsize=row_height)
        
        # Add some padding at the bottom for better scrolling
        bottom_padding = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent", height=20)
        bottom_padding.pack(fill="x")
        self.setup_focusout_capitalization()
        
    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        return file_path

    def process_data(self, old_file_path, new_file_path):
        try:
            df_old = pd.read_csv(old_file_path)
            df_new = pd.read_csv(new_file_path)

            # Clean Descriptive_Title columns more thoroughly
            def clean_title(title):
                if pd.isna(title):
                    return ""
                # Convert to string and strip
                title = str(title).strip()
                # Normalize spaces around slashes
                title = re.sub(r'\s*/\s*', '/', title)
                # Remove extra spaces
                title = ' '.join(title.split())
                # Convert to lowercase for better matching
                return title.lower()
            
            df_old['Descriptive_Title_Clean'] = df_old['Descriptive_Title'].apply(clean_title)
            df_new['Descriptive_Title_Clean'] = df_new['Descriptive_Title'].apply(clean_title)

            # Clean column names
            df_old.columns = [col.strip() for col in df_old.columns]
            df_new.columns = [col.strip() for col in df_new.columns]

            # Check if 'Descriptive_Title' exists in both dataframes
            if 'Descriptive_Title' not in df_old.columns or 'Descriptive_Title' not in df_new.columns:
                messagebox.showerror("Error", "'Descriptive_Title' column is missing in one of the files.")
                return

            # Filter old curriculum to keep only rows where 'Grades' are not NaN
            filtered_old = df_old[df_old['Grades'].notna()]

            # Initialize a dictionary to store matched Descriptive_Titles and their corresponding grades
            matched_grades = {}

            # DEBUG: Print titles for comparison
            print("\n=== DEBUG: Title Matching ===")
            print(f"Old curriculum titles: {len(filtered_old)}")
            print(f"New curriculum titles: {len(df_new)}")
            
            # Perform fuzzy matching for each Descriptive_Title in the old curriculum
            for index, row in filtered_old.iterrows():
                old_title = row['Descriptive_Title_Clean']
                old_original = row['Descriptive_Title']
                old_grade = row['Grades']
                
                # Try multiple matching strategies
                
                # Strategy 1: Exact match after cleaning
                exact_matches = df_new[df_new['Descriptive_Title_Clean'] == old_title]
                if not exact_matches.empty:
                    new_title = exact_matches.iloc[0]['Descriptive_Title']
                    matched_grades[new_title] = old_grade
                    print(f"✓ Exact match: '{old_original}' -> '{new_title}' (Grade: {old_grade})")
                    continue
                
                # Strategy 2: Fuzzy matching with lower threshold
                match_result = process.extractOne(
                    old_title, 
                    df_new['Descriptive_Title_Clean'], 
                    scorer=fuzz.token_sort_ratio,
                    score_cutoff=77  # Lower threshold for better matching
                )

                if match_result:
                    new_title_clean, score, idx = match_result
                    new_title = df_new.iloc[idx]['Descriptive_Title']
                    matched_grades[new_title] = old_grade
                    print(f"✓ Fuzzy match ({score}%): '{old_original}' -> '{new_title}' (Grade: {old_grade})")
                    
                    # Also check for partial matches in course numbers
                    old_course = str(row.get('Course_No', '')).strip()
                    if old_course:
                        # Look for courses with similar course numbers
                        course_matches = df_new[
                            df_new['Course_No'].astype(str).str.contains(old_course.split()[0] if ' ' in old_course else old_course)
                        ]
                        if not course_matches.empty and new_title not in matched_grades:
                            matched_grades[new_title] = old_grade
                else:
                    print(f"✗ No match found for: '{old_original}'")

            print(f"\nTotal matches found: {len(matched_grades)}")
            print("Matched titles:", list(matched_grades.keys()))

            # Update grades in the new curriculum DataFrame based on matched titles
            df_new['Grades'] = df_new['Descriptive_Title'].map(matched_grades)

            # Also try to match by Course_No as a fallback
            course_no_grades = {}
            for _, row in filtered_old.iterrows():
                old_course_no = str(row.get('Course_No', '')).strip()
                old_grade = row['Grades']
                if old_course_no:
                    # Find matching course numbers in new curriculum
                    matching_courses = df_new[df_new['Course_No'].astype(str).str.contains(old_course_no, case=False, na=False)]
                    for _, new_row in matching_courses.iterrows():
                        course_no_grades[new_row['Descriptive_Title']] = old_grade
            
            # Update any missing grades from course number matching
            for idx, row in df_new.iterrows():
                if pd.isna(row['Grades']) and row['Descriptive_Title'] in course_no_grades:
                    df_new.at[idx, 'Grades'] = course_no_grades[row['Descriptive_Title']]
                    print(f"✓ Course number match: {row['Descriptive_Title']}")

            # Drop rows without valid 'Descriptive_Title' if necessary
            matched_subjects = df_new.dropna(subset=['Descriptive_Title'])

            # Sort the data by year (assuming you have a 'Year_Level' or equivalent column)
            if 'Year_Level' in matched_subjects.columns:
                matched_subjects = matched_subjects.sort_values(by=['Year_Level', 'Descriptive_Title'])

            # Print summary
            print(f"\n=== Summary ===")
            print(f"Total subjects in new curriculum: {len(matched_subjects)}")
            print(f"Subjects with grades: {matched_subjects['Grades'].notna().sum()}")
            print(f"Subjects without grades: {matched_subjects['Grades'].isna().sum()}")
            
            # Show which subjects didn't get grades
            missing_grades = matched_subjects[matched_subjects['Grades'].isna()]
            if not missing_grades.empty:
                print("\nSubjects without grades:")
                for _, row in missing_grades.iterrows():
                    print(f"  - {row['Course_No']}: {row['Descriptive_Title']}")

            return matched_subjects
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process data: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    def display_data(self, matched_subjects):
        # Clear existing data in the Treeview
        for child in self.tree1.get_children():
            self.tree1.delete(child)

        # Ensure required columns exist
        required_columns = ['Course_No', 'Descriptive_Title', 'Year_Level', 'Units', 'Lec', 'Lab', 'Prerequisite', 'Grades']
        for col in required_columns:
            if col not in matched_subjects.columns:
                print(f"Warning: Column {col} is missing")
                matched_subjects[col] = ''

        # Predefined order of year levels and semesters
        year_levels = ['1.1', '1.2', '2.1', '2.2', '3.1', '3.2', '4.1', '4.2']

        # Track overall total units, lec, and lab
        overall_total_units = 0
        overall_total_lec = 0
        overall_total_lab = 0

        # Iterate through predefined year levels and semesters
        for year_sem in year_levels:
            # Filter subjects for this specific year and semester
            group = matched_subjects[matched_subjects['Year_Level'].astype(str) == year_sem]
            
            # Skip if no subjects for this year and semester
            if group.empty:
                continue

            # Extract year and semester for title
            year, semester = map(int, year_sem.split('.'))

            # Insert title row for the year and semester
            title = f"{self.get_semester_title(year, semester)}"
            self.tree1.insert("", "end", values=["",title, "", "", "", "", "", "", ""], tags=('title_row',))
            
            # Track totals for this year level
            year_total_units = 0
            year_total_lec = 0
            year_total_lab = 0

            # Insert subjects for this year and semester
            row_index = 0
            for index, row in group.iterrows():
                # Prepare values for the treeview
                values = [row.get('Course_No', ''), row.get('Descriptive_Title', ''), row.get('Year_Level', ''), row.get('Units', ''), row.get('Lec', ''), row.get('Lab', ''), row.get('Prerequisite', ''), row.get('Grades', '')]
                
                    # Determine the tag for the row based on the explicit counter
                tag = 'oddrow' if row_index % 2 == 0 else 'evenrow'
                row_index += 1
                # Insert row into treeview with the appropriate tag
                self.tree1.insert("", "end", values=values, tags=(tag,))

                # Update totals
                year_total_units += float(row.get('Units', 0))
                year_total_lec += float(row.get('Lec', 0))
                year_total_lab += float(row.get('Lab', 0))

            # Insert year level total row
            year_total_values = ["","Total", "", f"{int(round(year_total_units))}", f"{int(round(year_total_lec))}", f"{int(round(year_total_lab))}",  "",  ""]
            self.tree1.insert("", "end", values=year_total_values, tags=('year_total_row',), )

            # Update overall totals
            overall_total_units += year_total_units
            overall_total_lec += year_total_lec
            overall_total_lab += year_total_lab

            # Insert a blank row for spacing
            self.tree1.insert("", "end", values=["", "", "", "", "", "", "", ""])

        # Add overall total row
        overall_total_values = ["","Overall Total", "", f"{int(round(overall_total_units))}", f"{int(round(overall_total_lec))}", f"{int(round(overall_total_lab))}", "", ""]
        self.tree1.insert("", "end", values=overall_total_values, tags=('overall_total_row',))

        # If no data was inserted, show a message
        if len(self.tree1.get_children()) <= 1:  # 1 for overall total row
            messagebox.showinfo("No Data", "No subjects found for the selected curriculum.")
        # Configure row styles with corrected colors
        self.tree1.tag_configure('oddrow', background='#E5E5E5', font=('Helvetica', 12))  # Light gray for odd rows
        self.tree1.tag_configure('evenrow', background='#FFFFFF', font=('Helvetica', 12))  # White for even rows
        self.tree1.tag_configure('year_total_row', background='#E6FFE6', font=('Helvetica', 12, 'bold'))  # Light green for totals
        self.tree1.tag_configure('title_row', background='#E6E6FF', font=('Helvetica', 12, 'bold'))  # Light blue for titles

    def get_semester_title(self, year, semester):
        year_titles = {1: 'First Year', 2: 'Second Year', 3: 'Third Year', 4: 'Fourth Year'}
        
        semester_titles = {1: 'First Semester', 2: 'Second Semester'}
        
        return f"{year_titles.get(year, 'Unknown Year')} - {semester_titles.get(semester, 'Unknown Semester')}"
        
    def display_rows_grades(self, matched_subjects):
        # Clear existing data in the Treeview
        for child in self.tree2.get_children():
            self.tree2.delete(child)

        # Configure treeview font and style
        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', 13), rowheight=35)
        style.configure("Treeview.Heading", font=('Helvetica', 13, 'bold'))

        # Filter rows with no grades
        rows_needing_grades = matched_subjects[matched_subjects['Grades'].isna()]

        # Initialize totals for different levels
        overall_totals = {'Units': 0, 'Lec': 0, 'Lab': 0}

        # Configure row tags
        self.tree2.tag_configure('oddrow', background='#E5E5E5', font=('Helvetica', 13))
        self.tree2.tag_configure('evenrow', background='#FFFFFF', font=('Helvetica', 13))
        self.tree2.tag_configure('title_row', background='#E6E6FF', font=('Helvetica', 13, 'bold'))
        self.tree2.tag_configure('total_row', background='#E6FFE6', font=('Helvetica', 13, 'bold'))

        # Initialize storage for year-level totals
        year_level_totals = {str(i): {'Units': 0, 'Lec': 0, 'Lab': 0} for i in range(1, 5)}

        # Group data by year levels
        grouped_by_year = rows_needing_grades.groupby(rows_needing_grades['Year_Level'].astype(str).str.split('.').str[0])

        for year, year_group in grouped_by_year:

            # Iterate through each semester of this year
            for semester in ['1', '2']:
                year_sem = f"{year}.{semester}"
                semester_group = year_group[year_group['Year_Level'].astype(str) == year_sem]

                # Skip if no subjects for this semester
                if semester_group.empty:
                    continue

                # Insert Semester Title Row
                semester_title = f"{self.get_semester_title(int(year), int(semester))}"
                self.tree2.insert("", "end", values=["", semester_title, "", "", "", "", "", "", ""], tags=('title_row',))

                # Initialize semester totals
                semester_totals = {'Units': 0, 'Lec': 0, 'Lab': 0}

                # Insert rows for this semester
                for idx, (_, row) in enumerate(semester_group.iterrows()):
                    # Determine row tag
                    tag = 'oddrow' if idx % 2 == 0 else 'evenrow'

                    # Prepare values for insertion
                    values = [row.get(col, "") if pd.notna(row.get(col, "")) else "" for col in self.tree2["columns"]]

                    # Insert row
                    self.tree2.insert("", "end", values=values, tags=(tag,))
                    def safe_convert(value, default=0):
                        """
                        Safely converts a value to a float or int. If the conversion fails,
                        the default value is returned.
                        """
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            return default

                    # Update totals
                    units = safe_convert(row.get('Units', 0))
                    lec = safe_convert(row.get('Lec', 0))
                    lab = safe_convert(row.get('Lab', 0))

                    semester_totals['Units'] += units
                    semester_totals['Lec'] += lec
                    semester_totals['Lab'] += lab

                    year_level_totals[year]['Units'] += units
                    year_level_totals[year]['Lec'] += lec
                    year_level_totals[year]['Lab'] += lab

                    overall_totals['Units'] += units
                    overall_totals['Lec'] += lec
                    overall_totals['Lab'] += lab

                # Insert Semester Total Row
                semester_total_values = ["", "Total", "",f"{int(semester_totals['Units'])}",f"{int(semester_totals['Lec'])}", f"{int(semester_totals['Lab'])}"] + [""] * (len(self.tree2["columns"]) - 4)
                self.tree2.insert("", "end", values=semester_total_values, tags=('total_row',))

                self.tree2.insert("", "end", values=[""] * len(self.tree2["columns"]))


        # Insert Overall Totals
        overall_total_values = ["", "Overall Totals", f"{int(overall_totals['Units'])}", f"{int(overall_totals['Lec'])}", f"{int(overall_totals['Lab'])}"] + [""] * (len(self.tree2["columns"]) - 4)
        self.tree2.insert("", "end", values=overall_total_values, tags=('total_row',))

        # Handle empty data scenario
        if len(self.tree2.get_children()) <= 1:
            messagebox.showinfo("No Data", "No subjects found for the selected curriculum.")

    def auto_generate_appraised_id(self, event=None):
        """Automatically generate appraised ID when year and semester are selected"""
        selected_year = self.year_var.get()
        selected_semester = self.semester_var.get()

        if selected_year and selected_semester:
            appraised_id = f"{selected_year}-{selected_semester}"
            self.appraised_id_label.configure(text=f"Appraised ID: {appraised_id}")
        else:
            self.appraised_id_label.configure(text="")

    def check_basic_info(self):
            if (self.entries["ID No:"].get() and self.entries["Last Name:"].get() and
                self.entries["First Name:"].get() and self.entries["Middle Name:"].get() and
                self.entries["Year Level:"].get() and self.entries["Sex:"].get() and 
                self.entries["Age:"].get() and self.entries["Birthday:"].get() and self.entries["Contact Number:"].get()
                 and self.entries["Email Address:"].get() and self.entries["Address:"].get() and self.entries["Parent/Guardian:"].get()):
                appraised_id_text = self.appraised_id_label.cget("text")
                if appraised_id_text and "Appraised ID:" in appraised_id_text:
                    self.basic_info_entered = True
                    self.notebook.select(self.frame2)
                    # Extract the appraised ID from the label text
                    appraised_id = appraised_id_text.replace("Appraised ID: ", "")
                    return (self.appraised_id_label.cget("text"),
                        self.entries["ID No:"].get(), self.entries["Last Name:"].get(),
                        self.entries["First Name:"].get(), self.entries["Middle Name:"].get(),
                        self.entries["Year Level:"].get(), self.entries["Sex:"].get(),
                        self.entries["Age:"].get(), self.entries["Birthday:"].get(),
                        self.entries["Contact Number:"].get(), self.entries["Email Address:"].get(),
                        self.entries["Address:"].get(),self.entries["Parent/Guardian:"].get())
                else:
                    messagebox.showwarning("Warning", "Please complete the Appraised ID first.")
            else:
                messagebox.showwarning("Warning", "Please enter all basic information.")
    
    def start_appraisal(self):
        if self.basic_info_entered:
            old_file_path = self.select_file()
            new_file_path = self.select_file()

            matched_subjects = self.process_data(old_file_path, new_file_path)

            if matched_subjects is not None:
                self.matched_subjects = matched_subjects
                self.display_data(matched_subjects)
                self.display_rows_grades(matched_subjects)
                self.save_button.configure(state=tk.NORMAL)
                self.data_appraised = True
        else:
            messagebox.showwarning("Warning", "Please enter basic information first.")

    def save_to_database(self):
        if self.matched_subjects is not None:
            db_handler = DatabaseHandler()
            try:
                if self.basic_info_entered:
                    school_year = self.year_var.get()
                    if not school_year:
                        messagebox.showwarning("Warning", "Please select a school year.")
                        return
                    # Get appraised ID from label
                    appraised_id_text = self.appraised_id_label.cget("text")
                    if not appraised_id_text:
                        messagebox.showwarning("Warning", "Appraised ID not generated. Please select Year and Semester.")
                        return
                    
                    appraised_id = appraised_id_text.replace("Appraised ID: ", "")
                    # Get basic info using check_basic_info
                    basic_info_result = self.check_basic_info()
                    if basic_info_result:
                        _, id_no, last_name, first_name, middle_name, year, sex, age, birthday, contact_number, email_address, address, parent_guardian = basic_info_result
                    db_handler.save_appraised_data(appraised_id, id_no, last_name, first_name, middle_name, year, sex, age, birthday, contact_number, email_address, address, parent_guardian, self.matched_subjects, school_year)

                    messagebox.showinfo("Success", "Appraised data saved to the database successfully!")
                else:
                    messagebox.showwarning("Warning", "Please enter all basic information.")
            except Exception as e:
                # Print full traceback for debugging
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", f"Failed to save appraised data to database: {e}")
        else:
            messagebox.showwarning("Warning", "No appraised data to save.")

    def resize_background(self, event=None):
        """Update background image size when window is resized"""
        if hasattr(self, 'bg_image'):
            try:
                new_width = self.winfo_width()
                new_height = self.winfo_height()
                self.bg_image.configure(size=(new_width, new_height))
            except Exception as e:
                print(f"Error resizing background: {e}")

    def create_enhanced_date_picker(self, parent):
        """Create an enhanced date picker with easy year selection"""
        from datetime import datetime
        import tkinter as tk
        
        # Create a container frame
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", expand=True)
        
        # Create a hidden DateEntry for the calendar popup
        date_entry = DateEntry(container,width=16,background='darkblue',foreground='white',borderwidth=2,
            date_pattern='yyyy-mm-dd',
            font=('Helvetica', 12),
            year=2000,  # Default to a common birth year
            show=False)  # Hide the default entry
        
        # Create a visible entry to display the date
        display_entry = ctk.CTkEntry(container,corner_radius=30,width=170,placeholder_text="YYYY-MM-DD")
        display_entry.pack(side="left", fill="x", expand=True)
        try:
            calendar_icon = Image.open(LoginForm.resource_path("icons/calendar.png"))
            calendar_image = ctk.CTkImage(light_image=calendar_icon, dark_image=calendar_icon, size=(20, 20))
        except FileNotFoundError:
            # Create a simple colored rectangle as fallback
            from PIL import ImageDraw
            calendar_icon = Image.new('RGB', (20, 20), color='blue')
            draw = ImageDraw.Draw(calendar_icon)
            draw.rectangle([2, 2, 18, 18], outline='white', width=1)
            draw.text((5, 5), "C", fill='white')
            calendar_image = ctk.CTkImage(light_image=calendar_icon, dark_image=calendar_icon, size=(20, 20))
        # Create a button to trigger year/month selection
        picker_btn = ctk.CTkButton(container,text="",width=30,height=30, image=calendar_image,fg_color="transparent",hover_color="gray70",command=lambda: self.show_enhanced_calendar(date_entry, display_entry))
        picker_btn.pack(side="right", padx=(5, 0))
        
        # Store reference to both widgets
        display_entry.date_picker = date_entry
        return display_entry

    def show_enhanced_calendar(self, date_entry, display_entry):
        """Show an enhanced calendar with easy year/month selection"""
        import tkinter as tk
        from datetime import datetime
        
        # Create popup window
        popup = ctk.CTkToplevel(self)
        popup.title("Select Date")
        popup.geometry("400x400")
        popup.transient(self)
        popup.grab_set()
        
        # Main container
        main_container = ctk.CTkFrame(popup)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Year-Month selection at the top
        selection_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        selection_frame.pack(fill="x", pady=(0, 10))
        
        # Year selection
        year_label = ctk.CTkLabel(selection_frame, text="Year:")
        year_label.grid(row=0, column=0, padx=(0, 5), sticky="w")
        
        year_var = ctk.StringVar()
        year_values = [str(y) for y in range(1991, datetime.now().year + 1)]
        year_combo = ctk.CTkComboBox(selection_frame, values=year_values, variable=year_var, width=100, command=lambda v: self.update_calendar_display(calendar_frame, int(v), month_var.get()))
        year_combo.set("2000")  # Default to a common birth year
        year_combo.grid(row=0, column=1, padx=(0, 20), sticky="w")
        
        # Month selection
        month_label = ctk.CTkLabel(selection_frame, text="Month:")
        month_label.grid(row=0, column=2, padx=(0, 5), sticky="w")
        
        month_var = ctk.StringVar()
        month_combo = ctk.CTkComboBox(
            selection_frame,
            values=["January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"],
            variable=month_var,
            width=120,
            command=lambda v: self.update_calendar_display(calendar_frame, int(year_var.get()), v))
        month_combo.set("June")  # Default month
        month_combo.grid(row=0, column=3, sticky="w")
        
        # Calendar display frame
        calendar_frame = ctk.CTkFrame(main_container)
        calendar_frame.pack(fill="both", expand=True)
        
        # Initialize calendar display
        self.update_calendar_display(calendar_frame, 2000, "June")
        
        # Button frame
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        def select_current_date():
            """Select today's date"""
            today = datetime.now()
            year_combo.set(str(today.year))
            month_combo.set(today.strftime("%B"))
            self.update_calendar_display(calendar_frame, today.year, today.strftime("%B"))
        
        def apply_date():
            """Apply the selected date"""
            year = int(year_var.get())
            month = self.month_name_to_number(month_var.get())
            # Get the selected day from the calendar
            selected_day = getattr(calendar_frame, '_selected_day', 1)
            
            # Format the date
            date_str = f"{year:04d}-{month:02d}-{selected_day:02d}"
            
            # Update the DateEntry
            date_entry.set_date(datetime(year, month, selected_day))
            
            # Update the display entry
            display_entry.delete(0, tk.END)
            display_entry.insert(0, date_str)
            
            popup.destroy()
        
        ctk.CTkButton(button_frame, text="Today", command=select_current_date).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Apply", command=apply_date).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=popup.destroy).pack(side="right", padx=5)

    def update_calendar_display(self, calendar_frame, year, month_name):
        """Update the calendar display with the selected year and month"""
        import calendar
        from datetime import datetime
        
        # Clear previous calendar
        for widget in calendar_frame.winfo_children():
            widget.destroy()
        
        # Convert month name to number
        month = self.month_name_to_number(month_name)
        
        # Get calendar for the month
        month_cal = calendar.monthcalendar(year, month)
        
        # Day headers
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for col, day in enumerate(days):
            label = ctk.CTkLabel(calendar_frame, text=day, width=40, height=30)
            label.grid(row=0, column=col, padx=2, pady=2)
        
        # Day buttons
        for week_num, week in enumerate(month_cal):
            for day_num, day in enumerate(week):
                if day != 0:
                    btn = ctk.CTkButton(
                        calendar_frame,
                        text=str(day),
                        width=40,
                        height=30,
                        fg_color="skyblue",
                        text_color="white",  # White text (for any text that might appear)
                        hover_color="blue",
                        command=lambda d=day: self.select_day(calendar_frame, d))
                    btn.grid(row=week_num + 1, column=day_num, padx=2, pady=2)
                    
                    # Highlight current day if applicable
                    today = datetime.now()
                    if year == today.year and month == today.month and day == today.day:
                        btn.configure(fg_color="lightblue")
        
        # Store current month and year for reference
        calendar_frame._current_year = year
        calendar_frame._current_month = month
        calendar_frame._selected_day = 1  # Default to first day

    def select_day(self, calendar_frame, day):
        """Select a day in the calendar"""
        # Reset all buttons to default color
        for child in calendar_frame.winfo_children():
            if isinstance(child, ctk.CTkButton):
                child.configure(fg_color="transparent")
        
        # Highlight selected button
        for child in calendar_frame.winfo_children():
            if isinstance(child, ctk.CTkButton) and child.cget("text") == str(day):
                child.configure(fg_color="lightgreen")
                break
        
        # Store selected day
        calendar_frame._selected_day = day

    def month_name_to_number(self, month_name):
        """Convert month name to number"""
        months = {
            "January": 1, "February": 2, "March": 3, "April": 4,
            "May": 5, "June": 6, "July": 7, "August": 8,
            "September": 9, "October": 10, "November": 11, "December": 12
        }
        return months.get(month_name, 1)

    def validate_id_no(self, new_value):
        # Allow only numbers and hyphens
        return re.match(r'^[0-9-]*$', new_value) is not None
    
    def validate_last_name(self, new_value):
        # Just validate, no auto-capitalization here
        pattern = r'^[a-zA-ZñÑ\s\'-]*$'
        return re.match(pattern, new_value) is not None

    def validate_first_name(self, new_value):
        # Just validate, no auto-capitalization here
        pattern = r'^[a-zA-ZñÑ\s\'-]*$'
        return re.match(pattern, new_value) is not None

    def validate_middle_name(self, new_value):
        # Just validate, no auto-capitalization here
        pattern = r'^[a-zA-ZñÑ\s\'-]*$'
        return re.match(pattern, new_value) is not None

    def setup_focusout_capitalization(self):
        """Set up auto-capitalization when user leaves the field"""
        name_fields = ["Last Name:", "First Name:", "Middle Name:"]
        
        for field_name in name_fields:
            entry = self.entries.get(field_name)
            if entry:
                # Bind to FocusOut event (when user leaves the field)
                entry.bind('<FocusOut>', 
                        lambda e, fn=field_name: self.capitalize_on_focus_out(fn))

    def capitalize_on_focus_out(self, field_name):
        """Capitalize the text when user leaves the field"""
        entry = self.entries.get(field_name)
        if not entry:
            return
        
        current_text = entry.get()
        
        # Only process if there's text
        if current_text.strip():
            # Capitalize first letter of each word
            words = current_text.split()
            capitalized_words = []
            
            for word in words:
                if word:  # Skip empty strings
                    capitalized_words.append(word.capitalize())
            
            capitalized_text = ' '.join(capitalized_words)
            
            # Only update if the text has actually changed
            if current_text != capitalized_text:
                entry.delete(0, tk.END)
                entry.insert(0, capitalized_text)

    def validate_year_level(self, new_value):
        # Allow empty string for backspace/delete
        if new_value == "":
            return True
        # Allow only numbers 1-4
        return re.match(r'^[1-4]$', new_value) is not None

    def validate_sex(self, new_value):
        # Allow only M or F (case-insensitive)
        return re.match(r'^[mMfF]?$', new_value) is not None

    def validate_age(self, new_value):
        # Allow only numbers, max 3 digits
        return re.match(r'^[0-9]{0,2}$', new_value) is not None

    def validate_contact(self, new_value):
        # Allow only digits and hyphens, and max length 11
        if not re.match(r'^[0-9-]*$', new_value) or len(new_value) > 11:
            return False
        
        # Auto-insert dash after 3rd digit
        digits = new_value.replace("-", "")
        result = ""

        for i, c in enumerate(digits):
            result += c
            if i == 3:
                result += "-"
        
        # Remove trailing dash if present
        if result.endswith("-") and len(result) > 1:
            result = result[:-1]

        # If the formatted value doesn't match the entry, update it
        entry = self.entries.get("Contact Number: ")
        if entry and new_value != result:
            entry.delete(0, tk.END)
            entry.insert(0, result)
            return False

    def validate_email(self, new_value):
        # Basic email validation
        return re.match(r'^[a-zA-Z0-9._%+-]*@?[a-zA-Z0-9.-]*\.?[a-zA-Z]*$', new_value) is not None
    def validate_address(self, new_value):
        # Allow letters, numbers, spaces, commas, periods, and hyphens
        if re.match(r'^[a-zA-Z0-9\s,.-]*$', new_value) is not None:
            # Remove multiple spaces and trailing spaces
            cleaned_address = ' '.join(word for word in new_value.split() if word)
            
            if cleaned_address or new_value == "":
                # Capitalize first letter of each word
                capitalized_address = ' '.join(word.capitalize() for word in cleaned_address.split())
                
                # Update entry with cleaned and capitalized address
                current_label = self.entries.get("Address:")  # No extra space
                if current_label:
                    current_label.delete(0, tk.END)
                    current_label.insert(0, capitalized_address)
                return True
        return False

    def validate_parent_guardian(self, new_value):
        # Allow letters, numbers, spaces, commas, periods, and hyphens
        if re.match(r'^[a-zA-Z0-9\s,.-]*$', new_value) is not None:
            # Remove multiple spaces and trailing spaces
            cleaned_name = ' '.join(word for word in new_value.split() if word)
            
            if cleaned_name or new_value == "":
                # Capitalize first letter of each word
                capitalized_name = ' '.join(word.capitalize() for word in cleaned_name.split())
                
                # Update entry with cleaned and capitalized name
                current_label = self.entries.get("Parent/Guardian:")  # No extra space
                if current_label:
                    current_label.delete(0, tk.END)
                    current_label.insert(0, capitalized_name)
                return True
        return False
    
    def move_to_next_entry(self, event, current_index, total_entries):
        # Define field order based on horizontal layout
        field_order = [
            "ID No:", "Last Name:", "First Name:", 
            "Middle Name:", "Year Level:", "Sex:", 
            "Age:", "Birthday:", "Contact Number:", 
            "Email Address:", "Address:", "Parent/Guardian:"
        ]
        
        if current_index < len(field_order) - 1:
            next_field = field_order[current_index + 1]
            if next_field in self.entries:
                self.entries[next_field].focus_set()
                return "break"
        
        return "break"