
        # Function to add grade to treeview
        def add_grade():
            name = name_entry.get().strip()
            course_no = course_no_entry.get().strip()
            course_title = course_title_entry.get().strip()
            grade = grade_combobox.get()

            # Validate input
            if not name:
                messagebox.showerror("Error", "Student Name is required")
                return
            if not course_no:
                messagebox.showerror("Error", "Course No. is required")
                return
            if not course_title:
                messagebox.showerror("Error", "Course Title is required")
                return
            if not grade:
                messagebox.showerror("Error", "Grade is required")
                return

            # Fuzzy match student name
            matches = process.extractBests(
                name,
                student_names,
                scorer=fuzz.token_sort_ratio,
                score_cutoff=100,
                limit=1
            )
            
            if matches:
                matched_name = matches[0][0]
                if matched_name != name:
                    response = messagebox.askyesno(
                        "Name Match",
                        f"Did you mean '{matched_name}'?\nClick Yes to use this name, No to keep '{name}'"
                    )
                    if response:
                        name = matched_name
                        name_entry.delete(0, tk.END)
                        name_entry.insert(0, matched_name)

            # Check for duplicate course number
            for item in grade_tree.get_children():
                values = grade_tree.item(item)['values']
                if values[1] == course_no:  # Course No. is the second column
                    response = messagebox.askyesno(
                        "Update Grade", 
                        f"Course {course_no} already exists for {values[0]}. Do you want to update its grade?"
                    )
                    if response:
                        grade_tree.item(item, values=(name, course_no, course_title, grade))
                    return

            # Insert into treeview
            grade_tree.insert("", "end", values=(name, course_no, course_title, grade))

            # Clear entries
            name_entry.delete(0, tk.END)
            course_no_entry.delete(0, tk.END)
            course_title_entry.delete(0, tk.END)
            grade_combobox.set('')

      # Function to delete selected grade
        def delete_grade():
            selected_item = grade_tree.selection()
            if not selected_item:
                messagebox.showwarning("Warning", "Please select a grade to delete")
                return
            grade_tree.delete(selected_item)
        def save_grades():
            if not year_sem_combobox.get():
                messagebox.showerror("Error", "Please select Year-Semester")
                return

            # Year-Semester mapping
            year_sem_mapping = {
                '1.1': ('1st Year', '1st Semester'),
                '1.2': ('1st Year', '2nd Semester'),
                '2.1': ('2nd Year', '1st Semester'),
                '2.2': ('2nd Year', '2nd Semester'),
                '3.1': ('3rd Year', '1st Semester'),
                '3.2': ('3rd Year', '2nd Semester'),
                '4.1': ('4th Year', '1st Semester'),
                '4.2': ('4th Year', '2nd Semester')
            }

            # Get the selected year-semester code (e.g., '1.1', '2.1', etc.)
            selected_year_sem = year_sem_combobox.get().split(' - ')[0]
            
            if selected_year_sem not in year_sem_mapping:
                messagebox.showerror("Error", "Invalid year-semester selection")
                return

            year, semester = year_sem_mapping[selected_year_sem]

            grades_data = []
            for item in grade_tree.get_children():
                values = grade_tree.item(item)['values']
                grades_data.append({
                    'Student Name': values[0],
                    'Course No.': values[1],
                    'Course Title': values[2],
                    'Grade': values[3]
                })

            if not grades_data:
                messagebox.showerror("Error", "No grades to save")
                return

            try:
                grades_df = pd.DataFrame(grades_data)
                if self.db_handler.save_manual_grades(grades_df, year, semester):
                    messagebox.showinfo("Success", "Grades saved successfully")
                    completion_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save grades: {str(e)}")

        