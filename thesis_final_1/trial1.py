import logging
import pandas as pd
from tkinter import messagebox
import mysql.connector

class DatabaseHandler:
    def __init__(self):
        self.conn, self.cursor = self.get_db_connection()
    def get_db_connection(self):
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # Update with actual password if necessary
            database='department'
        )
        cursor = conn.cursor()
        return conn, cursor

    def close_db_connection(self):
        self.conn.close()

    def saving_curriculum_data(self, processed_data):
        # Check if the DataFrame is empty
        if processed_data.empty:
            messagebox.showerror("Error", "No data to save!")
            return  # Exit the function if there's no data

        query = """INSERT INTO curriculum_regular 
                (Course_No, Descriptive_Title, Year_Level, Units, Lab, Lec, Prerequisite, Grades)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

        try:
            # Print processed data for debugging purposes
            print("Processed data:")
            print(processed_data.head())  # Print the first few rows

        # Convert DataFrame to list of tuples, replacing NaN values with None for all relevant fields
            values = [
                (
                    row.Course_No,
                    row.Descriptive_Title,
                    row.Year_Level,
                    '' if pd.isna(row.Units) else row.Units,  # Replace NaN with empty string
                    '' if pd.isna(row.Lab) else row.Lab,  # Replace NaN with empty string
                    '' if pd.isna(row.Lec) else row.Lec,  # Replace NaN with empty string
                    '' if pd.isna(row.Prerequisite) else row.Prerequisite,  # Replace NaN with empty string
                    '' if pd.isna(row.Grades) else row.Grades  # Replace NaN with empty string            
                    )   
            for _, row in processed_data.iterrows()
        ]

            # Ensure the database connection is open
            if self.conn.is_connected():
                self.cursor.executemany(query, values)
                self.conn.commit()
                
            else:
                raise mysql.connector.Error("Database connection lost.")
        except mysql.connector.Error as err:
            # Rollback in case of error and display error message
            print("Error encountered:", err)
            if self.conn.is_connected():
                self.conn.rollback()
            messagebox.showerror("Error", f"Error saving data to database: {err}")

        finally:
        # Close the cursor and connection only if connected
            if self.conn.is_connected():
                self.cursor.close()
                self.conn.close()
    def saving_student(self, student_name, data, table_name=None):
        try:
            # Create the table if it doesn't exist
            create_table_query = f"""
                CREATE TABLE IF NOT EXISTS students (
                    ID_NO VARCHAR(255),
                    `STUDENT_NAME` VARCHAR(255),
                    YR VARCHAR(255),
                    AGE INT,
                    SEX CHAR(25),
                    `EMAIL_ADDRESS` VARCHAR(255),
                    `SHS` VARCHAR(255),
                    `ADDRESS` VARCHAR(255),
                    STATUS VARCHAR(255)
                )
            """
            self.cursor.execute(create_table_query)

            # Insert data into the table
            insert_query = f"""
                INSERT INTO students (
                      ID_NO, `STUDENT_NAME`, YR, AGE, SEX, `EMAIL_ADDRESS`, `SHS`, `ADDRESS`, STATUS
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.executemany(insert_query, data)

            if table_name:
                # Create the table if it doesn't exist
                create_table_query = f"""
                    CREATE TABLE IF NOT EXISTS `{table_name}` (
                        Course_No VARCHAR(255),
                        `Descriptive_Title` VARCHAR(255),
                        Year_Level DECIMAL(3, 1),
                        Units INT,
                        Lab INT,
                        Lec INT,
                        Prerequisite VARCHAR(255),
                        Grades_x DECIMAL(5, 2)
                    )
                """
                self.cursor.execute(create_table_query)

                # Insert data into the table
                insert_query = f"""
                    INSERT INTO `{table_name}` (
                        Course_No,
                        `Descriptive_Title`,
                        Year_Level,
                        Units,
                        Lab,
                        Lec,
                        Prerequisite,
                        Grades_x
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                self.cursor.executemany(insert_query, data)

            # Commit the changes
            self.conn.commit()
            messagebox.showinfo(f"Data saved to {table_name if table_name else student_name} table successfully.")

        except mysql.connector.Error as e:
            messagebox.showerror(f"Error saving data: {e}")
            logging.error(f"Error saving data: {e}")

        finally:
            # Close the cursor and connection only if connected
            if self.conn.is_connected():
                self.cursor.close()
                self.conn.close()

    def save_appraised_data(self, appraised_id, id_no, student_name, year, sex, age, email_address, matched_subjects):
        try:
            # Create a new table for the student if it doesn't exist
            table_name = "appraised_curriculum"
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    appraised_id VARCHAR(20),
                    id_no  VARCHAR(50),
                    student_name VARCHAR(100),
                    year INT,
                    sex VARCHAR(10),
                    age INT,
                    email_address VARCHAR(100),
                    course_no VARCHAR(100),
                    descriptive_title VARCHAR(100),
                    year_level DECIMAL(3,1),
                    units INT,
                    lec INT,
                    lab INT,
                    prerequisite VARCHAR(100),
                    grades DECIMAL(5,2)
                )
            """)

            # Save basic info
            self.cursor.execute("""
                INSERT INTO students (id_no, student_name, year, sex, age, email_address)
                VALUES ( %s, %s, %s, %s, %s, %s)
            """, (
                id_no, 
                student_name, 
                year if not pd.isna(year) else None, 
                sex, 
                age, 
                email_address
            ))
            self.conn.commit()

            # Save matched subjects
            for _, row in matched_subjects.iterrows():
                self.cursor.execute(f"""
                    INSERT INTO {table_name} (appraised_id, id_no, student_name, year, sex, age, email_address, course_no, descriptive_title, year_level, units, lec, lab, prerequisite, grades)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    appraised_id,
                    id_no, 
                    student_name, 
                    year,
                    sex,
                    age,
                    email_address,
                    row['Course_No'] if not pd.isna(row['Course_No']) else '', 
                    row['Descriptive_Title'] if not pd.isna(row['Descriptive_Title']) else '', 
                    row['Year_Level'] if not pd.isna(row['Year_Level']) else '', 
                    row['Units'] if not pd.isna(row['Units']) else 0, 
                    row['Lec'] if not pd.isna(row['Lec']) else '', 
                    row['Lab'] if not pd.isna(row['Lab']) else '',
                    row['Prerequisite'] if not pd.isna(row['Prerequisite']) else '',
                    row['Grades'] if not pd.isna(row['Grades']) else ''
                )) #fix that the prerequisite is also save
            self.conn.commit()

            messagebox.showinfo("Success", "Appraised data saved to the database successfully!")
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Failed to save data to the database: {e}")

    def check_and_fetch_entries(self, id_no, current_year_level):
        try:
            # Helper function to determine the previous year level
            def get_previous_year_level(year_level):
                parts = year_level.split('.')
                if len(parts) == 2:
                    year = int(parts[0])
                    semester = int(parts[1])
                    if semester == 1:
                        return f"{year - 1}.2"  # Previous year, second semester
                    else:
                        return f"{year}.1"  # Same year, first semester
                return year_level  # Default to current if parsing fails

            # Determine the previous year level
            prev_year_level = get_previous_year_level(current_year_level)

            # Query to fetch entries with no grades from the previous year level
            no_grades_query = """
                SELECT course_no, descriptive_title, units
                FROM appraised_curriculum
                WHERE id_no = %s AND year_level = %s AND (grades IS NULL OR grades = '')
            """
            no_grades_results = self.execute_query(no_grades_query, (id_no, prev_year_level))

            # Query to check curriculum status for the current year level
            status_query = """
                SELECT COUNT(*) as entry_count, 
                SUM(CASE WHEN grades IS NOT NULL AND grades != '' THEN 1 ELSE 0 END) as graded_count
                FROM appraised_curriculum
                WHERE id_no = %s AND year_level = %s
            """
            status_results = self.execute_query(status_query, (id_no, current_year_level))

            # Determine status from the results
            if status_results and len(status_results) > 0:
                status_result = status_results[0]
                entry_count = status_result['entry_count']
                graded_count = status_result['graded_count']

                curriculum_status = {
                    "has_entries": entry_count > 0,
                    "has_grades": graded_count > 0
                }
            else:
                curriculum_status = {
                    "has_entries": False,
                    "has_grades": False
                }

            # Determine if any course without grades from the previous year level should be added
            missing_grades = no_grades_results

            return {
                "curriculum_status": curriculum_status,
                "missing_grades": missing_grades
            }
        except Exception as e:
            raise Exception(f"An error occurred while fetching entries: {str(e)}")

    def insert_students(self, table_name, data):
        if not data:
            messagebox.showerror("Error", "No data to insert!")
            return  # Exit the function if there's no data

        for row in data:
            required_keys = ['ID_NO', 'STUDENT_NAME', 'YR', 'AGE ', 'SEX']
            if not all(key in row for key in required_keys):
                print(f"Error: Missing required key in row: {row}")
                continue
            self.cursor.execute(f'''INSERT INTO {table_name} 
                               (ID_NO, STUDENT_NAME, YR, AGE, SEX, EMAIL_ADDRESS, SHS, ADDRESS)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''', 
                               (row['ID_NO'], row['STUDENT_NAME'], row['YR'], row['AGE '], row['SEX'], row.get('EMAIL_ADDRESS', ''), row.get('SHS', ''), row.get('ADDRESS', '')))

        self.conn.commit()

    def fetch_irregular_students(self, id_no, year_level):
        query = """
        SELECT appraised_id, id_no, student_name, year, sex, age, email_address,
               course_no, descriptive_title, year_level, units, lec, lab, prerequisite, grades
        FROM appraised_curriculum
        WHERE id_no = %s AND year_level = %s
        """
        params = (id_no, year_level)
        return self.execute_query(query, params)
    
    def fetch_student_data(self, id_no, year_level):
        logging.debug(f"Fetching data for ID_NO: {id_no}, Year Level: {year_level}")
        curriculum_query = """
            SELECT 
                si.ID_NO, 
                si.STUDENT_NAME,
                si.YR, 
                si.AGE, 
                si.SEX, 
                si.EMAIL_ADDRESS,
                cr.Course_No, 
                cr.Descriptive_Title, 
                cr.Year_Level, 
                cr.Units, 
                cr.Lec, 
                cr.Lab, 
                cr.Prerequisite
            FROM
                student_information si
            LEFT JOIN
                curriculum_regular cr ON cr.Year_Level = %s
            WHERE
                si.ID_NO = %s
        """
        curriculum_params = (year_level, id_no)

        try:
            curriculum_results = self.execute_query(curriculum_query, curriculum_params)
            if not curriculum_results:
                logging.warning(f"No curriculum data found for ID_NO: {id_no}, Year Level: {year_level}")
        except mysql.connector.Error as err:
            logging.error(f"An error occurred while fetching student data: {err.msg}")
            raise RuntimeError(f"An error occurred while fetching student data: {err.msg}")

        table_mapping = {
            '1.1': 'first_year_first_semester',
            '1.2': 'first_year_second_semester',
            '2.1': 'second_year_first_semester',
            '2.2': 'second_year_second_semester',
            '3.1': 'third_year_first_semester',
            '3.2': 'third_year_second_semester',
            '4.1': 'fourth_year_first_semester',
            '4.2': 'fourth_year_second_semester'
        }

        table_name = table_mapping.get(year_level)
        table_exists = False
        has_grades = False
        grades_data = {}
        enrollment_status = ""

        if table_name:
            table_check_query = "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = %s"
            try:
                table_exists_result = self.execute_query(table_check_query, (table_name,))
                table_exists = table_exists_result[0]['COUNT(*)'] == 1

                if table_exists:
                    # Check if student has grades for any course
                    grades_query = f"SELECT COURSE_NO, GRADE FROM {table_name} WHERE ID_NO = %s"
                    grades_results = self.execute_query(grades_query, (id_no,))
                    has_grades = len(grades_results) > 0

                    if has_grades:
                        enrollment_status = "Student has grades for this semester."
                        grades_data = {row['COURSE_NO']: row['GRADE'] for row in grades_results}
                    else:
                        enrollment_status = f"No grades yet for {year_level}"
                else:
                    # Table does not exist
                    enrollment_status = f"No grades yet for {year_level}"

            except mysql.connector.Error as err:
                logging.error(f"Error checking {table_name}: {err.msg}")
                enrollment_status = f"Error checking enrollment status for {year_level}"
        else:
            enrollment_status = f"Invalid year level: {year_level}"
                        # Update curriculum results with grades
        for curriculum in curriculum_results:
            course_no = curriculum['Course_No']
            curriculum['Grade'] = grades_data.get(course_no, "No grade available")
            
        logging.debug(f"Grades data: {grades_data}")
        logging.debug(f"Curriculum data with grades: {curriculum_results}")

        # Return curriculum results, enrollment status, and table existence/grade information
        return {
            "curriculum_data": curriculum_results,
            "curriculum_regular_data": self.execute_query("SELECT * FROM curriculum_regular"),
            "enrollment_status": enrollment_status,
            "table_exists": table_exists,
            "has_grades": has_grades,
            "grades_data": grades_data
        }
        
    def fetch_curriculum(self, year_level, id_no):
        logging.debug(f"Fetching curriculum data for Year Level: {year_level}, ID_NO: {id_no}")

        curriculum_query = """
            SELECT
                si.ID_NO, 
                si.STUDENT_NAME,
                si.YR, 
                si.AGE, 
                si.SEX, 
                si.EMAIL_ADDRESS,
                cr.Course_No, 
                cr.Descriptive_Title, 
                cr.Year_Level, 
                cr.Units, 
                cr.Lec, 
                cr.Lab, 
                cr.Prerequisite
            FROM
                student_information si
            LEFT JOIN
                curriculum_regular cr ON cr.Year_Level = %s
            WHERE
                si.ID_NO = %s
        """
        curriculum_params = (year_level, id_no)

        try:
            curriculum_results = self.execute_query(curriculum_query, curriculum_params)
            if not curriculum_results:
                logging.warning(f"No curriculum data found for Year Level: {year_level}, ID_NO: {id_no}")
        except mysql.connector.Error as err:
            logging.error(f"An error occurred while fetching curriculum data: {err.msg}")
            raise RuntimeError(f"An error occurred while fetching curriculum data: {err.msg}")

        return curriculum_results
    
    def execute_query(self, query, params=None):
        logging.debug(f"Executing query: {query} with params: {params}")
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, params)
                if query.strip().lower().startswith("select"):
                    results = cursor.fetchall()
                    logging.debug(f"Fetched {len(results)} records.")
                    return results
                else:
                    self.conn.commit()
                    logging.debug("Query executed and changes committed.")
        except mysql.connector.Error as e:
            logging.error(f"Error executing query: {e}")
            self.conn.rollback()
            raise

    def save_grading_data(self, grading_data, year, semester):
        year_mapping = {
            "1st Year": "first_year",
            "2nd Year": "second_year",
            "3rd Year": "third_year",
            "4th Year": "fourth_year"
        }

        semester_mapping = {
            "1st Semester": "first_semester",
            "2nd Semester": "second_semester"
        }

        # Get the corresponding table name based on year and semester
        table_name = f"{year_mapping[year]}_{semester_mapping[semester]}"

        # SQL to create the table if it doesn't exist
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            ID_NO VARCHAR(50),
            STUDENT_NAME VARCHAR(100),
            COURSE_NO VARCHAR(50),
            GRADE VARCHAR(10),
            PRIMARY KEY (ID_NO, COURSE_NO)
        )
        """
        self.execute_query(create_table_query)

        insert_query = f"""
        INSERT INTO {table_name} (ID_NO, STUDENT_NAME, COURSE_NO, GRADE)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE GRADE = VALUES(GRADE)
        """

        course_columns = [col for col in grading_data.columns if col not in ['ID_NO', 'STUDENT_NAME']]

        for index, row in grading_data.iterrows():
            student_id = row['ID_NO']
            student_name = row['STUDENT_NAME']

            for course in course_columns:
                grade = row[course]
                if pd.notna(grade):
                    params = (student_id, student_name, course, grade)
                    self.execute_query(insert_query, params)

        return True

    def get_student_info(self):
        try:
            query = "SELECT `ID_NO`, STUDENT_NAME, EMAIL_ADDRESS FROM student_information"
            cursor = self.conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return pd.DataFrame(result, columns=columns)
        except mysql.connector.Error as e:
            messagebox.showerror(f"Error getting student_information info: {e}")
            return pd.DataFrame()

    def get_missing_grades(self, year, semester):
        try:
            query = """
                SELECT student_id, course_no
                FROM grades
                WHERE year = %s AND semester = %s AND grade IS NULL
            """
            cursor = self.conn.cursor()
            cursor.execute(query, (year, semester))
            result = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return pd.DataFrame(result, columns=columns)
        except mysql.connector.Error as e:
            messagebox.showerror(f"Error getting missing grades: {e}")
            return pd.DataFrame()
        

        def search_student(self):
    id_no = self.search_entry.get()
    year_level = self.year_level_var.get()
    
    student_data = self.db.fetch_student_data(id_no, year_level)
    print("Full student data:", student_data)  # Debug print
    
    # Clear existing data
    for item in self.curriculum_tree.get_children():
        self.curriculum_tree.delete(item)
    
    if student_data["curriculum_data"]:
        for i, row in enumerate(student_data["curriculum_data"]):
            course_no = row.get('Course_No', '').strip()  # Strip whitespace
            descriptive_title = row.get('Descriptive_Title', '')
            year_level = row.get('Year_Level', '')
            units = row.get('Units', '')
            lec = row.get('Lec', '')
            lab = row.get('Lab', '')
            prerequisite = row.get('Prerequisite', '')
            
            # Get the grade from all_grades_data
            grade = "N/A"
            for table, grades in student_data["grades_data"].items():
                # Check for exact match first
                if course_no in grades:
                    grade = grades[course_no]
                    break
                # If no exact match, try matching without leading/trailing spaces
                for grade_course, grade_value in grades.items():
                    if course_no.strip() == grade_course.strip():
                        grade = grade_value
                        break
                if grade != "N/A":
                    break
            
            values = [course_no, descriptive_title, year_level, units, lec, lab, prerequisite, grade]
            
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.curriculum_tree.insert("", "end", values=values, tags=(tag,))
            
            # Debug print for each row
            print(f"Course: {course_no}, Grade: {grade}")
    else:
        print("No data")
    
    # Configure tag colors
    self.curriculum_tree.tag_configure('oddrow', background='#E8E8E8')
    self.curriculum_tree.tag_configure('evenrow', background='#FFFFFF')
    
    # Update status label
    self.status_label.config(text=student_data["enrollment_status"])
    
    # Store the retrieved student ID for later use in printing
    self.selected_id_no = id_no
    
    print("Received grades data:", student_data["grades_data"])

    # Additional debugging: print all course numbers from curriculum and grades
    curriculum_courses = set(row.get('Course_No', '').strip() for row in student_data["curriculum_data"])
    grades_courses = set()
    for table, grades in student_data["grades_data"].items():
        grades_courses.update(grade.strip() for grade in grades.keys())
    
    print("Curriculum courses:", curriculum_courses)
    print("Grades courses:", grades_courses)
    print("Courses in curriculum but not in grades:", curriculum_courses - grades_courses)
    print("Courses in grades but not in curriculum:", grades_courses - curriculum_courses)