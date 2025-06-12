from configparser import Error
import logging
from CTkMessagebox import CTkMessagebox
import pandas as pd
from tkinter import messagebox
import mysql.connector
from datetime import datetime
import time, os
import traceback
import logging

class DatabaseHandler:
    def __init__(self):
        self.conn, self.cursor = self.get_db_connection()
    def get_db_connection(self):
        conn = mysql.connector.connect(
            host='localhost', #192.168.254.125
            user='root',
            password='', 
            database='department',
            port=3306,
            allow_local_infile=True)
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
                (Course_No, Descriptive_Title, Year_Level, Units, Lab, Lec, Prerequisite, Grades, sy_revision)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""

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
                    '' if pd.isna(row.Units) else row.Units,
                    '' if pd.isna(row.Lab) else row.Lab,
                    '' if pd.isna(row.Lec) else row.Lec,
                    '' if pd.isna(row.Prerequisite) else row.Prerequisite,
                    '' if pd.isna(row.Grades) else row.Grades,
                    '' if pd.isna(row.SY_Revision) else row.SY_Revision  # Fixed column name
                )   
                for _, row in processed_data.iterrows()
            ]

            # Ensure the database connection is open
            if self.conn.is_connected():
                self.cursor.executemany(query, values)
                self.conn.commit()
                messagebox.showinfo("Success", "Data saved successfully!")
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

    # ini sa pag add student           
    def saving_student(self, last_name, first_name, middle_name, data, enrolled_year, bday, to_be_enrolled_years, table_name=None):
        try:
            # Ensure the student_information table exists with the correct structure
            create_table_query = """
                CREATE TABLE IF NOT EXISTS student_information (
                    ID_NO VARCHAR(255) PRIMARY KEY,
                    LAST_NAME VARCHAR(100) NOT NULL,
                    FIRST_NAME VARCHAR(100) NOT NULL,
                    MIDDLE_NAME VARCHAR(100),
                    YR VARCHAR(255),
                    AGE INT,
                    BDAY DATE,
                    SEX CHAR(25),
                    EMAIL_ADDRESS VARCHAR(255),
                    SHS VARCHAR(255),
                    ADDRESS VARCHAR(255),
                    ENROLLED_YEAR YEAR,
                    TO_BE_ENROLLED_YEAR VARCHAR(255) DEFAULT NULL
                )
            """
            self.cursor.execute(create_table_query)

            # Generate a default academic year if none is provided
            if not to_be_enrolled_years:
                current_year = datetime.now().year
                to_be_enrolled_years = f"{current_year}-{current_year + 1}"  # Example: "2025-2026"

            # Process the student data
            processed_data = []
            for row in data:
                processed_row = (
                    row[0],        # ID_NO
                    last_name,     # LAST_NAME
                    first_name,    # FIRST_NAME
                    middle_name,   # MIDDLE_NAME
                    row[2],        # YR
                    row[3],        # AGE
                    bday,          # BDAY from the function parameter
                    row[4],        # SEX
                    row[5],        # EMAIL_ADDRESS
                    row[6],        # SHS
                    row[7],        # ADDRESS
                    enrolled_year, # ENROLLED_YEAR from selection
                    to_be_enrolled_years  # Ensure a value is always inserted
                )
                processed_data.append(processed_row)

            # Check if the student already exists to prevent duplicates
            for row in processed_data:
                id_no = row[0]
                self.cursor.execute("SELECT COUNT(*) FROM student_information WHERE ID_NO = %s", (id_no,))
                exists = self.cursor.fetchone()[0]

                if exists:
                    # Update existing student record
                    update_query = """
                        UPDATE student_information
                        SET LAST_NAME = %s, FIRST_NAME = %s, MIDDLE_NAME = %s,
                            YR = %s, AGE = %s, BDAY = %s, SEX = %s, EMAIL_ADDRESS = %s, 
                            SHS = %s, ADDRESS = %s, ENROLLED_YEAR = %s, TO_BE_ENROLLED_YEAR = %s
                        WHERE ID_NO = %s
                    """
                    self.cursor.execute(update_query, (*row[1:], id_no))
                else:
                    # Insert new student record
                    insert_query = """
                        INSERT INTO student_information (
                            ID_NO, LAST_NAME, FIRST_NAME, MIDDLE_NAME, YR, AGE, BDAY, SEX, 
                            EMAIL_ADDRESS, SHS, ADDRESS, ENROLLED_YEAR, TO_BE_ENROLLED_YEAR
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    self.cursor.execute(insert_query, row)

            # Commit changes
            self.conn.commit()
            messagebox.showinfo("Success", "Student information saved successfully.")

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to save data: {err}")
            self.conn.rollback()

    # ni hu sa appraised curriculum
    def save_appraised_data(self, appraised_id, id_no, last_name, first_name, middle_name, year, sex, age, email_address, matched_subjects, school_year):
        try:
            if not school_year:
                raise ValueError("School year is required")
            # Create a new table for the student if it doesn't exist
            table_name = "appraised_curriculum"
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    appraised_id VARCHAR(20),
                    id_no VARCHAR(50),
                    last_name VARCHAR(110),
                    first_name VARCHAR(100),
                    middle_name VARCHAR(100),
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
                    grades DECIMAL(5,2),
                    school_year VARCHAR(20)
                )
            """)

            # Save basic info
            self.cursor.execute("""
                INSERT INTO students (id_no, last_name, first_name, middle_name, year, sex, age, email_address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                id_no, 
                last_name,
                first_name,
                middle_name,
                year if not pd.isna(year) else None, 
                sex, 
                age, 
                email_address
            ))
            self.conn.commit()

            # Save matched subjects
            for _, row in matched_subjects.iterrows():
                self.cursor.execute(f"""
                    INSERT INTO {table_name} (appraised_id, id_no, last_name, first_name, middle_name, year, sex, age, email_address, course_no, descriptive_title, year_level, units, lec, lab, prerequisite, grades, school_year)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    appraised_id,
                    id_no, 
                    last_name,
                    first_name,
                    middle_name,
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
                    row['Grades'] if not pd.isna(row['Grades']) else '',
                    school_year
                )) #fix that the prerequisite is also save
            self.conn.commit()

            messagebox.showinfo("Success", "Appraised data saved to the database successfully!")
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Failed to save data to the database: {e}")
   
    def fetch_available_fallback_subjects(self, id_no):
        logging.debug(f"Fetching available fallback subjects for ID_NO: {id_no}")
        query = """
            SELECT 
                ac.course_no,
                ac.descriptive_title,
                ac.units
            FROM
                appraised_curriculum ac
            WHERE
                ac.id_no = %s AND
                (ac.grades IS NULL OR ac.grades = '0.00')  -- Assuming '0.00' indicates no grade
        """
        params = (id_no,)

        try:
            results = self.execute_query(query, params)

            if not results:
                logging.warning(f"No available fallback subjects found for ID_NO: {id_no}")
                return []

            logging.info(f"Found {len(results)} available fallback subjects for ID_NO: {id_no}")
            return results

        except mysql.connector.Error as err:
            logging.error(f"An error occurred while fetching fallback subjects: {err.msg}")
            return []

    # pag display sa irregular studnt baga
    def fetch_irregular_students(self, id_no): 
        logging.debug(f"Fetching irregular student data for ID_NO: {id_no}")
        appraised_query = """
            SELECT 
                ac.appraised_id,
                ac.id_no, 
                ac.last_name,
                ac.first_name,
                ac.middle_name,
                ac.year, 
                ac.age, 
                ac.sex, 
                ac.email_address,
                ac.course_no, 
                ac.descriptive_title, 
                ac.year_level, 
                ac.units, 
                ac.lec, 
                ac.lab, 
                ac.prerequisite,
                ac.grades
            FROM
                appraised_curriculum ac
            WHERE
                ac.id_no = %s
        """

        appraised_params = (id_no,)

        try:
            appraised_results = self.execute_query(appraised_query, appraised_params)

            if not appraised_results:
                logging.warning(f"No appraised curriculum data found for ID_NO: {id_no}")
                return []

            # Semester progression mapping
            semester_progression = {
                '1.1': '1.2', '1.2': '2.1', 
                '2.1': '2.2', '2.2': '3.1', 
                '3.1': '3.2', '3.2': '4.1', 
                '4.1': '4.2', '4.2': 'Graduate'
            }

            # Group courses by year level
            year_level_courses = {}
            for record in appraised_results:
                year_level = str(record['year_level'])
                if year_level not in year_level_courses:
                    year_level_courses[year_level] = []
                year_level_courses[year_level].append(record)

            # Determine the current and next semester
            current_semester = None
            next_semester = None

            # Sort year levels to ensure progression
            sorted_year_levels = sorted(year_level_courses.keys(), 
                                        key=lambda x: (int(x.split('.')[0]), int(x.split('.')[1])))

            for year_level in sorted_year_levels:
                courses = year_level_courses[year_level]
                
                # Check if all courses in this year level have passing grades
                all_passed = all(
                    str(course['grades']).strip() not in ['', '0.00'] and 
                    float(course['grades']) >= 1.0  # Assuming passing grade is 1.0 or above
                    for course in courses
                )

                if all_passed:
                    # If all courses are passed, move to the next semester
                    current_semester = year_level
                    next_semester = semester_progression.get(year_level)
                    
                    logging.info(f"All courses in {year_level} are passed")
                    logging.info(f"Current Semester: {current_semester}")
                    logging.info(f"Next Semester: {next_semester}")
                    
                    break

            # If no progression found, use the lowest semester
            if not current_semester:
                current_semester = sorted_year_levels[0]
                next_semester = semester_progression.get(current_semester, '1.2')

            # Prepare results with semester information
            for record in appraised_results:
                record['current_sem'] = current_semester
                record['next_sem'] = next_semester

            return appraised_results

        except Exception as err:
            logging.error(f"An error occurred while fetching irregular student data: {err}")
            return []
                                    
    def update_student_yr(self, id_no): # para kat update ng year level ng student
        try:
            # Get all grades for the student
            all_grades = self.check_all_tables_for_grades(id_no)
            completed_semesters = set(all_grades.keys())
            print(f"\nChecking year level update for student ID: {id_no}")
            print(f"Completed semesters: {completed_semesters}")

            # Check for empty grades in each semester
            for semester, grades in all_grades.items():
                for course, grade in grades.items():
                    # Skip non-grade columns
                    if course in ['ID_NO', 'LAST_NAME', 'FIRST_NAME', 'MIDDLE_NAME', 'SCHOOL_YEAR']:
                        continue
                    
                    # Check for empty, None, or INC grades
                    if grade is None or str(grade).strip() == '' or str(grade).upper() == 'INC':
                        print(f"Found incomplete grade in {semester} for course {course}")
                        return None  # Don't update year if any empty grades found

            # Define semester requirements for each year
            year_requirements = {
                '2': {'first_year_first_semester', 'first_year_second_semester'},
                '3': {'second_year_first_semester', 'second_year_second_semester'},
                '4': {'third_year_first_semester', 'third_year_second_semester'},
                'Graduate': {'fourth_year_first_semester', 'fourth_year_second_semester'}
            }

            # Get current year level
            query = "SELECT YR FROM student_information WHERE ID_NO = %s"
            self.cursor.execute(query, (id_no,))
            result = self.cursor.fetchone()
            
            if not result:
                print(f"WARNING: No student found with ID: {id_no}")
                return None

            current_yr = result[0]
            print(f"Current year level: {current_yr}")

            # Determine new year level based on completed semesters
            new_yr = None
            for year, required_semesters in year_requirements.items():
                if required_semesters.issubset(completed_semesters):
                    if current_yr != 'Graduate':  # Don't update if already graduated
                        new_yr = year
                        print(f"Requirements met for year {year}")

            # Update if new year level is determined and all grades are complete
            if new_yr and new_yr != current_yr:
                print(f"Updating year level from {current_yr} to {new_yr}")
                update_query = "UPDATE student_information SET YR = %s WHERE ID_NO = %s"
                self.cursor.execute(update_query, (new_yr, id_no))
                self.conn.commit()
                print(f"Successfully updated student {id_no} year level to {new_yr}")
                return new_yr
            else:
                print("No year level update needed")
                return None

        except mysql.connector.Error as err:
            print(f"DATABASE ERROR: {err}")
            self.conn.rollback()
            return None
        except Exception as e:
            print(f"UNEXPECTED ERROR: {e}")
            return None
        
    def insert_students(self, table_name, data):
        try:
            # Insert data
            insert_query = """
                INSERT INTO student_information (
                    ID_NO, LAST_NAME, FIRST_NAME, MIDDLE_NAME,
                    YR, AGE, SEX, EMAIL_ADDRESS, SHS, ADDRESS, ENROLLED_YEAR
                ) VALUES (%(ID_NO)s, %(LAST_NAME)s, %(FIRST_NAME)s, %(MIDDLE_NAME)s,
                        %(YR)s, %(AGE)s, %(SEX)s, %(EMAIL_ADDRESS)s, %(SHS)s, 
                        %(ADDRESS)s, %(ENROLLED_YEAR)s)
            """
            self.cursor.executemany(insert_query, data)
            self.conn.commit()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to insert data: {err}")
            self.conn.rollback()

    # ini ya hu sa regular student na display 
    def fetch_student_data(self, id_no, year_level):
        logging.debug(f"Fetching data for ID_NO: {id_no}, Year Level: {year_level}")        
        curriculum_query = """
            SELECT 
                si.ID_NO, 
                si.LAST_NAME,
                si.FIRST_NAME,
                si.MIDDLE_NAME,
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
                curriculum_regular cr ON cr.YEAR_LEVEL = si.YR
            WHERE
                si.ID_NO = %s AND cr.YEAR_LEVEL = %s
        """
        curriculum_params = (id_no, year_level)

        try:
            curriculum_results = self.execute_query(curriculum_query, curriculum_params)
            if not curriculum_results:
                logging.warning(f"No curriculum data found for ID_NO: {id_no}, Year Level: {year_level}")
            else:
                # Update student name format in results
                for result in curriculum_results:
                    result['STUDENT_NAME'] = f"{result['LAST_NAME']}, {result['FIRST_NAME']} {result['MIDDLE_NAME']}".strip()
                    # Remove individual name fields if not needed
                    del result['LAST_NAME']
                    del result['FIRST_NAME']
                    del result['MIDDLE_NAME']

        except mysql.connector.Error as err:
            logging.error(f"An error occurred while fetching student data: {err.msg}")
            raise RuntimeError(f"An error occurred while fetching student data: {err.msg}")

        # Rest of the method remains the same
        table_mapping = {
            '1.1': 'first_year_first_semester',
            '1.2': 'first_year_second_semester',
            '2.1': 'second_year_first_semester',
            '2.2': 'second_year_second_semester',
            '3.1': 'third_year_first_semester',
            '3.2': 'third_year_second_semester',
            '4.1': 'fourth_year_first_semester',
            '4.2': 'fourth_year_second_semester'}

        all_grades_data = self.check_all_tables_for_grades(id_no)
        
        current_table = table_mapping.get(year_level)
        if current_table:
            if current_table in all_grades_data:
                enrollment_status = f"Student has grades for {year_level}"
            else:
                enrollment_status = f"No grades yet for {year_level}"
        else:
            enrollment_status = f"Invalid year level: {year_level}"

        # Update curriculum results with grades from all tables
        for curriculum in curriculum_results:
            course_no = curriculum['Course_No']
            for table, grades in all_grades_data.items():
                if course_no in grades:
                    curriculum[f'Grade_{table}'] = grades[course_no]

        logging.debug(f"All grades data: {all_grades_data}")
        logging.debug(f"Curriculum data with grades: {curriculum_results}")

        return {
            "curriculum_data": curriculum_results,
            "curriculum_regular_data": self.execute_query("SELECT * FROM curriculum_regular"),
            "enrollment_status": enrollment_status,
            "table_exists": current_table in all_grades_data,
            "has_grades": bool(all_grades_data.get(current_table)),
            "grades_data": all_grades_data}
    
        # pag check ng grade sa regular student
    def check_all_tables_for_grades(self, id_no):
        table_names = [
            'first_year_first_semester',
            'first_year_second_semester',
            'second_year_first_semester',
            'second_year_second_semester',
            'third_year_first_semester',
            'third_year_second_semester',
            'fourth_year_first_semester',
            'fourth_year_second_semester']

        all_grades_data = {}

        for table in table_names:
            try:
                # First check if table exists
                table_check_query = """
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = %s 
                    AND COLUMN_NAME NOT IN ('ID_NO', 'LAST_NAME', 'FIRST_NAME', 'MIDDLE_NAME', 'SCHOOL_YEAR')
                """
                course_columns = self.execute_query(table_check_query, (table,))
                
                if course_columns:
                    # Build dynamic SELECT query using the course columns
                    course_cols = [col['COLUMN_NAME'] for col in course_columns]
                    select_query = f"""
                        SELECT 
                            {', '.join(f'`{col}`' for col in course_cols)}
                        FROM {table}
                        WHERE ID_NO = %s
                    """
                    
                    grades_result = self.execute_query(select_query, (id_no,))
                    
                    if grades_result:
                        grades_data = {}
                        # First row contains all the grades
                        grade_row = grades_result[0]
                        
                        # Add each non-empty grade to the dictionary
                        for course_col in course_cols:
                            if grade_row[course_col] and str(grade_row[course_col]).strip():
                                grades_data[course_col] = grade_row[course_col]
                        
                        if grades_data:  # Only add if there are actual grades
                            all_grades_data[table] = grades_data
                            logging.debug(f"Found grades in {table}: {grades_data}")
                
            except mysql.connector.Error as err:
                logging.error(f"Error checking {table}: {err}")
                continue

        return all_grades_data
        
    def get_latest_school_year(self, id_no):
        """Get the latest school year from student information and then from student's grades"""
        try:
            # First, check the school year in student information table
            student_info_query = """
                SELECT ENROLLED_YEAR, YR 
                FROM student_information 
                WHERE ID_NO = %s 
            """
            
            student_info_result = self.execute_query(student_info_query, (id_no,))
            
            # If school year found in student information, process and return it
            if student_info_result and student_info_result[0]['YR']== '1':
                latest_school_year = student_info_result[0]['ENROLLED_YEAR']
                try:
                    # Ensure latest_school_year is treated as a string for formatting
                    if isinstance(latest_school_year, int): 
                        start_year = str(latest_school_year)
                        current_year = f"{start_year}-{int(start_year) + 1}"
                        return current_year
                    elif isinstance(latest_school_year, str):
                        return latest_school_year
                except (ValueError, IndexError):
                    return None
            
            # Determine which tables to check based on student's year
            table_mapping = {
                '1': [
                    'first_year_first_semester',
                    'first_year_second_semester'
                ],
                '2': [
                    'second_year_first_semester',
                    'second_year_second_semester'
                ],
                '3': [
                    'third_year_first_semester',
                    'third_year_second_semester'
                ],
                '4': [
                    'fourth_year_first_semester',
                    'fourth_year_second_semester'
                ]
            }
            
            # Determine the year level to check (use from student info if available)
            year_level = student_info_result[0]['YR'] if student_info_result else None
            
            # If year level is not found in student info, use a comprehensive search
            tables_to_check = table_mapping.get(year_level, [
                'first_year_first_semester',
                'first_year_second_semester',
                'second_year_first_semester',
                'second_year_second_semester',
                'third_year_first_semester',
                'third_year_second_semester',
                'fourth_year_first_semester',
                'fourth_year_second_semester'])
            
            latest_school_year = None
            
            for table in tables_to_check:
                query = f"""
                    SELECT SCHOOL_YEAR 
                    FROM {table} 
                    WHERE ID_NO = %s 
                    AND SCHOOL_YEAR IS NOT NULL 
                    AND SCHOOL_YEAR != ''
                    ORDER BY SCHOOL_YEAR DESC 
                    LIMIT 1
                """
                
                result = self.execute_query(query, (id_no,))
                if result and result[0]['SCHOOL_YEAR']:
                    latest_school_year = result[0]['SCHOOL_YEAR']
                    break  # Stop after finding the first valid school year
            
            if latest_school_year:
                try:
                    # Reuse the parsing logic
                    def parse_school_year(year_str):
                        if '-' in year_str:
                            return year_str
                        
                        elif '/' in year_str:
                            return year_str
                        
                        else:
                            # If it's a single year, generate year range
                            try:
                                start_year = int(year_str)
                                return f"{start_year}-{start_year + 1}"
                            except ValueError:
                                return year_str
                    
                    return parse_school_year(latest_school_year)
                
                except (ValueError, IndexError):
                    return None
            
            return None
        
        except Exception as e:
            print(f"Error getting latest school year: {e}")
            return None
                    
    def get_latest_school_year_irregular(self, id_no):
        """Get the latest school year from appraised curriculum for irregular students"""
        try:
            query = """
                SELECT school_year
                FROM appraised_curriculum
                WHERE id_no = %s 
                AND school_year IS NOT NULL 
                AND school_year != ''
                ORDER BY school_year DESC 
                LIMIT 1
            """
            
            result = self.execute_query(query, (id_no,))
            
            if result and result[0]['school_year']:
                latest_school_year = result[0]['school_year']
                
                # Parse the last school year and increment for current
                try:
                    # Handle different possible formats
                    if '-' in latest_school_year:
                        # If already in format 2023-2024, return as is
                        if len(latest_school_year.split('-')) == 2:
                            return latest_school_year
                        
                        start_year = int(latest_school_year.split('-')[0])
                        current_school_year = f"{start_year}-{start_year + 1}"
                    
                    elif '/' in latest_school_year:
                        # If already in format 2023/2024, return as is
                        if len(latest_school_year.split('/')) == 2:
                            return latest_school_year
                        
                        start_year = int(latest_school_year.split('/')[0])
                        current_school_year = f"{start_year}/{start_year + 1}"
                    
                    else:
                        # If it's a single year
                        start_year = int(latest_school_year)
                        current_school_year = f"{start_year}-{start_year + 1}"
                    
                    return current_school_year
                
                except (ValueError, IndexError):
                    return None
            
            return None
            
        except Exception as e:
            print(f"Error getting latest school year for irregular student: {e}")
            return None
        
    # pag display sa curriculum data hatag also copy sa each ka student 
    def fetch_curriculum(self, year_level, id_no):
        logging.debug(f"Fetching curriculum data for Year Level: {year_level}, ID_NO: {id_no}")

        curriculum_query = """
            SELECT
                si.ID_NO, 
                si.LAST_NAME,
                si.FIRST_NAME,
                si.MIDDLE_NAME,
                si.YR, 
                si.AGE, 
                si.SEX, 
                si.EMAIL_ADDRESS,
                si.SHS,
                si.ADDRESS,
                cr.COURSE_NO, 
                cr.DESCRIPTIVE_TITLE, 
                cr.YEAR_LEVEL, 
                cr.UNITS, 
                cr.LEC, 
                cr.LAB, 
                cr.PREREQUISITE
            FROM
                student_information si
            LEFT JOIN
                curriculum_regular cr ON cr.YEAR_LEVEL = %s
            WHERE
                si.ID_NO = %s
        """
        curriculum_params = (year_level, id_no)

        try:
            curriculum_results = self.execute_query(curriculum_query, curriculum_params)
            if not curriculum_results:
                logging.warning(f"No curriculum data found for Year Level: {year_level}, ID_NO: {id_no}")
            else:
                # Format student name and update results
                for result in curriculum_results:
                    result['STUDENT_NAME'] = f"{result['LAST_NAME']}, {result['FIRST_NAME']} {result['MIDDLE_NAME']}".strip()
                    # Remove individual name fields if not needed
                    del result['LAST_NAME']
                    del result['FIRST_NAME']
                    del result['MIDDLE_NAME']

        except mysql.connector.Error as err:
            logging.error(f"An error occurred while fetching curriculum data: {err.msg}")
            raise RuntimeError(f"An error occurred while fetching curriculum data: {err.msg}")

        return curriculum_results
    
    #old execute query method
    """def execute_query(self, query, params=None):
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
            raise"""
       #new execute query method jan 8 2025 
    def execute_query(self, query, params=None):
        logging.debug(f"Executing query: {query} with params: {params}")
        cursor = None
        try:
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
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
        finally:
            if cursor:
                cursor.close()

    def execute_query_with_retry(self, query, params=None, retries=3, delay=5):
        for attempt in range(retries):
            try:
                if not self.conn.is_connected():
                    self.conn.reconnect()
                cursor = self.conn.cursor(dictionary=True)
                cursor.execute(query, params or ())
                if query.strip().lower().startswith("select"):
                    results = cursor.fetchall()
                    return results
                else:
                    self.conn.commit()
                    return None
            except mysql.connector.Error as e:
                if attempt == retries - 1:
                    self.conn.rollback()
                    raise
                time.sleep(delay)
            finally:
                if cursor:
                    cursor.close()

    def get_existing_courses(self):
        self.cursor.execute("SELECT COURSE_NO FROM curriculum_regular")
        return set(row[0].strip().upper() for row in self.cursor.fetchall())

    def save_grading_data(self, grading_data, year, semester, school_year):
        try:
            # Clean DataFrame column names
            grading_data = grading_data.copy()
            grading_data.columns = grading_data.columns.str.strip()

            # Mappings for table name
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
            
            table_name = f"{year_mapping[year]}_{semester_mapping[semester]}"

            # Identify student info columns and course columns
            student_info_columns = ['ID_NO', 'LAST_NAME', 'FIRST_NAME', 'MIDDLE_NAME']
            course_columns = [col for col in grading_data.columns if col not in student_info_columns]

            # Create table with the correct structure
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                `ID_NO` VARCHAR(255),
                `LAST_NAME` VARCHAR(100),
                `FIRST_NAME` VARCHAR(100),
                `MIDDLE_NAME` VARCHAR(100),
                `SCHOOL_YEAR` VARCHAR(20),
                `COURSE_NO` VARCHAR(30),
                `GRADES` DECIMAL(5,2),
                PRIMARY KEY (`ID_NO`, `COURSE_NO`, `SCHOOL_YEAR`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            self.execute_query_with_retry(create_table_query)

            # Insert query
            insert_query = f"""
            INSERT INTO `{table_name}` 
                (`ID_NO`, `LAST_NAME`, `FIRST_NAME`, `MIDDLE_NAME`, `SCHOOL_YEAR`, `COURSE_NO`, `GRADES`)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE `GRADES` = VALUES(`GRADES`)
            """

            # Process each student's grades
            values_list = []
            for _, row in grading_data.iterrows():
                student_info = [
                    str(row['ID_NO']).strip(),
                    str(row['LAST_NAME']).strip(),
                    str(row['FIRST_NAME']).strip(),
                    str(row.get('MIDDLE_NAME', '')).strip(),
                    school_year.strip()
                ]
                
                # For each course column (like GE101, CS101, etc.)
                for course in course_columns:
                    grade = row[course]
                    if pd.notna(grade) and str(grade).strip() != "":
                        try:
                            # Create a record with the course code as COURSE_NO and its value as GRADES
                            values = student_info + [course, float(grade)]
                            values_list.append(tuple(values))
                        except ValueError:
                            print(f"Invalid grade value for {course}: {grade}")
                            continue

            # Execute batch insert
            if values_list:
                self.cursor.executemany(insert_query, values_list)
                self.conn.commit()
                return True

            return False

        except mysql.connector.Error as err:
            CTkMessagebox(title="Database", message=f"Database Error: {err}")
            self.conn.rollback()
            return False
        except Exception as e:
            CTkMessagebox(title="Database", message=f"Error saving grades: {e}")
            self.conn.rollback()
            return False
            
    def save_irregular_grading_data(self, grading_data, year, semester):
        try:
            # Define the table name
            table_name = "appraised_curriculum"
            
            # Comprehensive year level conversion function
            def convert_year_level(year_text):
                # Mapping dictionaries with multiple variations
                year_map = {
                    '1ST YEAR': 1, '1ST': 1, '1': 1,
                    '2ND YEAR': 2, '2ND': 2, '2': 2,
                    '3RD YEAR': 3, '3RD': 3, '3': 3,
                    '4TH YEAR': 4, '4TH': 4, '4': 4
                }
                
                semester_map = {
                    '1ST SEMESTER': 1, '1ST': 1, '1': 1,
                    '2ND SEMESTER': 2, '2ND': 2, '2': 2
                }
                
                # Normalize input
                normalized = str(year_text).upper().replace(' ', '')
                
                try:
                    # Direct numeric conversion
                    return float(normalized)
                except (ValueError, TypeError):
                    pass
                
                # Handle text-based input
                try:
                    # Check if input is in predefined maps
                    if normalized in year_map:
                        return float(year_map[normalized])
                    
                    # Parse Year and Semester text
                    if 'YEAR' in normalized and 'SEMESTER' in normalized:
                        # Extract year part
                        year_part = normalized.split('YEAR')[0]
                        # Extract semester part
                        semester_part = normalized.split('SEMESTER')[0].split('.')[-1]
                        
                        # Convert year and semester
                        year_numeric = year_map.get(year_part, year_part)
                        semester_numeric = semester_map.get(semester_part, semester_part)
                        
                        # Ensure numeric conversion
                        return float(f"{year_numeric}.{semester_numeric}")
                    
                    # Try dot-separated format
                    parts = normalized.split('.')
                    if len(parts) == 2:
                        year_numeric = year_map.get(parts[0], parts[0])
                        semester_numeric = semester_map.get(parts[1], parts[1])
                        return float(f"{year_numeric}.{semester_numeric}")
                    
                    # Fallback
                    raise ValueError(f"Cannot convert {year_text} to year level")
                
                except Exception as e:
                    print(f"Error converting year level: {year_text}, Error: {e}")
                    return None

            # Combine year and semester to create year_level
            current_year_level = convert_year_level(f"{year} Year.{semester} Semester")
            
            # Validate year_level
            if current_year_level is None:
                raise ValueError(f"Invalid year level conversion for {year} Year.{semester} Semester")
            
            # Comprehensive search query to find all matching courses for the specific student
            comprehensive_search_query = f"""
            SELECT 
                id_no, 
                course_no, 
                year_level, 
                grades,
                school_year
            FROM `{table_name}`
            WHERE 
                id_no = %s AND 
                course_no = %s
            ORDER BY ABS(year_level - %s)  # Sort by closest year level
            """
            
            # Update query that ensures update only for the specific student and course
            update_query = f"""
            UPDATE `{table_name}`
            SET grades = %s, school_year = %s
            WHERE 
                id_no = %s AND 
                course_no = %s AND 
                year_level = %s
            """
            
            # Handle both DataFrame and list of dictionaries
            if isinstance(grading_data, pd.DataFrame):
                # If it's a DataFrame, iterate through rows
                for _, row in grading_data.iterrows():
                    try:
                        # First, try to update at the current year level
                        self.cursor.execute(update_query, (
                            row['grades'], 
                            row['school_year'], 
                            row['id_no'], 
                            row['course_no'], 
                            current_year_level
                        ))
                        
                        # If no update occurred, search for alternative year levels
                        if self.cursor.rowcount == 0:
                            # Find all matching courses for this student, sorted by closest year level
                            self.cursor.execute(comprehensive_search_query, (
                                row['id_no'], 
                                row['course_no'], 
                                current_year_level
                            ))
                            existing_courses = self.cursor.fetchall()
                            
                            if existing_courses:
                                # Log matching courses
                                print(f"Fallback search for student {row['id_no']}:")
                                for course in existing_courses:
                                    print(f"Course: {course[1]}, Year Level: {course[2]}, Current Grade: {course[3]}")
                                
                                # Try to update the closest year level record
                                closest_year_level = existing_courses[0][2]
                                self.cursor.execute(update_query, (
                                    row['grades'], 
                                    row['school_year'], 
                                    row['id_no'], 
                                    row['course_no'], 
                                    closest_year_level
                                ))
                                
                                # Log the update
                                print(f"Updated grade for course {row['course_no']} at fallback year level {closest_year_level}")
                            else:
                                print(f"No record found for course {row['course_no']} for student {row['id_no']}")
                    
                    except Exception as row_error:
                        print(f"Error processing row: {row_error}")
                        continue

            elif isinstance(grading_data, list):
                # Similar logic for list of dictionaries
                for entry in grading_data:
                    try:
                        # First, try to update at the current year level
                        self.cursor.execute(update_query, (
                            entry['grades'], 
                            entry['school_year'], 
                            entry['id_no'], 
                            entry['course_no'], 
                            current_year_level
                        ))
                        
                        # If no update occurred, search for alternative year levels
                        if self.cursor.rowcount == 0:
                            # Find all matching courses for this student, sorted by closest year level
                            self.cursor.execute(comprehensive_search_query, (
                                entry['id_no'], 
                                entry['course_no'], 
                                current_year_level
                            ))
                            existing_courses = self.cursor.fetchall()
                            
                            if existing_courses:
                                # Log matching courses
                                print(f"Fallback search for student {entry['id_no']}:")
                                for course in existing_courses:
                                    print(f"Course: {course[1]}, Year Level: {course[2]}, Current Grade: {course[3]}")
                                
                                # Try to update the closest year level record
                                closest_year_level = existing_courses[0][2]
                                self.cursor.execute(update_query, (
                                    entry['grades'], 
                                    entry['school_year'], 
                                    entry['id_no'], 
                                    entry['course_no'], 
                                    closest_year_level
                                ))
                                
                                # Log the update
                                print(f"Updated grade for course {entry['course_no']} at fallback year level {closest_year_level}")
                            else:
                                print(f"No record found for course {entry['course_no']} for student {entry['id_no']}")
                    
                    except Exception as entry_error:
                        print(f"Error processing entry: {entry_error}")
                        continue
            
            else:
                # Unsupported input type
                raise ValueError("Invalid input type for grading_data. Expected DataFrame or list of dictionaries.")
            
            self.conn. commit()
            return True
        
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            self.conn.rollback()
            return False
        except Exception as e:
            print(f"Error saving grades: {e}")
            self.conn.rollback()
            return False
                                        
    def get_student_id(self, search_term=None):
        try:
            # Ensure we have a valid connection
            if not hasattr(self, 'conn') or not self.conn.is_connected():
                print("Reconnecting to database...")
                self.conn = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
                )
            
            # Create a dictionary cursor
            dict_cursor = self.conn.cursor(dictionary=True)
            
            try:
                if search_term:
                    query = """
                        SELECT DISTINCT 
                            ID_NO, 
                            LAST_NAME,
                            FIRST_NAME,
                            MIDDLE_NAME
                        FROM student_information 
                        WHERE (LAST_NAME LIKE %s 
                            OR FIRST_NAME LIKE %s 
                            OR MIDDLE_NAME LIKE %s)
                        ORDER BY LAST_NAME, FIRST_NAME, MIDDLE_NAME
                    """
                    dict_cursor.execute(query, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
                else:
                    query = """
                        SELECT DISTINCT 
                            ID_NO, 
                            LAST_NAME,
                            FIRST_NAME,
                            MIDDLE_NAME
                        FROM student_information 
                        ORDER BY LAST_NAME, FIRST_NAME, MIDDLE_NAME
                    """
                    dict_cursor.execute(query)
                
                results = dict_cursor.fetchall()
                print(f"Query results: {results}")  # Debug print
                
                # Format names for display
                formatted_names = []
                for row in results:
                    name = f"{row['LAST_NAME']} {row['FIRST_NAME']}"
                    if row['MIDDLE_NAME']:
                        name += f" {row['MIDDLE_NAME']}"
                    formatted_names.append(name)
                
                return {
                    'full_data': results if results else [],
                    'names': formatted_names if results else []
                }
                
            finally:
                dict_cursor.close()
                
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            return {'full_data': [], 'names': []}
        except Exception as e:
            print(f"Error getting student data: {e}")
            return {'full_data': [], 'names': []}
        
    def get_student_by_id(self, id_no):
        """Fetch a single student's details by ID number"""
        try:
            query = """
                SELECT 
                    ID_NO,
                    LAST_NAME,
                    FIRST_NAME,
                    MIDDLE_NAME
                FROM student_information
                WHERE ID_NO = %s
            """
            self.cursor.execute(query, (id_no,))
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'ID_NO': result[0],
                    'LAST_NAME': result[1],
                    'FIRST_NAME': result[2],
                    'MIDDLE_NAME': result[3]
                }
            return None
            
        except mysql.connector.Error as e:
            print(f"Database error fetching student: {e}")
            return None
        except Exception as e:
            print(f"Error fetching student: {e}")
            return None
        
    def check_student_existence(self, id_no):
        """
        Check if student exists in multiple tables
        
        Args:
            id_no (str): Student ID number to check
        
        Returns:
            bool: True if student exists in any table, False otherwise
        """
        try:
            # Check in student_information table
            query_student_info = """
            SELECT COUNT(*) FROM student_information 
            WHERE ID_NO = %s
            """
            self.cursor.execute(query_student_info, (id_no,))
            student_info_count = self.cursor.fetchone()[0]
            
            if student_info_count > 0:
                return True
            
            # Check in students table
            query_students = """
            SELECT COUNT(*) FROM students 
            WHERE ID_NO = %s
            """
            self.cursor.execute(query_students, (id_no,))
            students_count = self.cursor.fetchone()[0]
            
            if students_count > 0:
                return True
            
            # Check in appraised_curriculum table
            query_appraised = """
            SELECT COUNT(*) FROM appraised_curriculum 
            WHERE ID_NO = %s
            """
            self.cursor.execute(query_appraised, (id_no,))
            appraised_count = self.cursor.fetchone()[0]
            
            return appraised_count > 0
        
        except Exception as e:
            print(f"Error checking student existence: {e}")
            return False
        
    def verify_record_exists(self, id_no, course_no):
        """Verify if a record exists in appraised_curriculum
        Args:
            id_no (str): Student ID number
            course_no (str): Course number
        Returns:
            bool: True if record exists, False otherwise
        """
        try:
            query = """
            SELECT COUNT(*) 
            FROM appraised_curriculum 
            WHERE id_no = %s AND course_no = %s
            """
            self.cursor.execute(query, (id_no, course_no))
            count = self.cursor.fetchone()[0]
            
            return count > 0
        
        except Exception as e:
            print(f"Error verifying record existence: {e}")
            return False
            
    def update_appraised_grades(self, grades_df):
        """Update only grades column in appraised_curriculum table for existing records"""
        try:
            for _, row in grades_df.iterrows():
                # Only update the grades column, using other columns to identify the correct row
                update_query = """
                    UPDATE appraised_curriculum 
                    SET grades = %s
                    WHERE id_no = %s 
                    AND course_no = %s
                    AND year_level = %s
                    AND school_year = %s
                    AND (grades IS NULL OR grades = '' OR grades = 'INC')
                """
                self.cursor.execute(
                    update_query, 
                    (
                        row['grade'],      # New grade value to set
                        row['id_no'],      # Identifier
                        row['course_no'],   # Identifier
                        row['year_level'],  # Identifier
                        row['school_year']  # Identifier
                    )
                )
                
                if self.cursor.rowcount == 0:
                    print(f"No update performed for student {row['id_no']}, course {row['course_no']} - record might not exist or already has a grade")
                else:
                    print(f"Successfully updated grade for student {row['id_no']}, course {row['course_no']}")
                    
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Error updating appraised grades: {e}")
            raise
                

    def save_manual_grades(self, grading_data, year_level, school_year):
        try:
            # Map year levels to table names (now each table should have columns: ID_NO, LAST_NAME, FIRST_NAME, MIDDLE_NAME, SCHOOL_YEAR, COURSE_NO, GRADES)
            year_mapping = {
                "1.1": "first_year_first_semester",
                "1.2": "first_year_second_semester",
                "2.1": "second_year_first_semester",
                "2.2": "second_year_second_semester",
                "3.1": "third_year_first_semester",
                "3.2": "third_year_second_semester",
                "4.1": "fourth_year_first_semester",
                "4.2": "fourth_year_second_semester"}

            table_name = year_mapping.get(year_level)
            if not table_name:
                raise ValueError(f"Invalid year level: {year_level}")

            # Ensure the table has the correct structure
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                `ID_NO` VARCHAR(255),
                `LAST_NAME` VARCHAR(100),
                `FIRST_NAME` VARCHAR(100),
                `MIDDLE_NAME` VARCHAR(100),
                `SCHOOL_YEAR` VARCHAR(20),
                `COURSE_NO` VARCHAR(30),
                `GRADES` DECIMAL(5,2),
                PRIMARY KEY (`ID_NO`, `COURSE_NO`, `SCHOOL_YEAR`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            self.cursor.execute(create_table_query)

            # Define valid grades
            valid_grades = {1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 5.0}

            # Process each row in the grading data
            for _, row in grading_data.iterrows():
                try:
                    course_no = row['Course No.'].strip()
                    # Convert grade to decimal and validate
                    try:
                        grade = float(row['Grade'])
                        if grade not in valid_grades:
                            raise ValueError(
                                f"Invalid grade {grade} for course {course_no}. "
                                f"Valid grades are: {', '.join(map(str, valid_grades))}"
                            )
                    except ValueError as ve:
                        if "could not convert string to float" in str(ve):
                            raise ValueError(f"Invalid grade format for course {course_no}: {row['Grade']}")
                        raise ve

                    # Check if the record already exists
                    check_query = f"""
                        SELECT COUNT(*) FROM `{table_name}`
                        WHERE ID_NO = %s AND COURSE_NO = %s AND SCHOOL_YEAR = %s
                    """
                    self.cursor.execute(check_query, (
                        row['ID_NO'].strip(),
                        course_no,
                        school_year.strip()
                    ))
                    exists = self.cursor.fetchone()[0]

                    if exists:
                        # Do not update, just show message and skip
                        messagebox.showwarning(
                            "Duplicate Entry",
                            f"Grade for student {row['ID_NO']} in course {course_no} for {school_year} already exists. Double entry detected."
                        )
                        continue

                    # Insert the grade for this student, course, and school year
                    insert_query = f"""
                    INSERT INTO `{table_name}` 
                        (`ID_NO`, `LAST_NAME`, `FIRST_NAME`, `MIDDLE_NAME`, `SCHOOL_YEAR`, `COURSE_NO`, `GRADES`)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        row['ID_NO'].strip(),
                        row['Last Name'].strip(),
                        row['First Name'].strip(),
                        row['Middle Name'].strip(),
                        school_year.strip(),
                        course_no,
                        grade
                    )
                    self.cursor.execute(insert_query, values)

                except ValueError as ve:
                    messagebox.showerror("Validation Error", str(ve))
                    self.conn.rollback()
                    return False

            self.conn.commit()
            return True

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error saving grades: {err}")
            return False
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            return False

            
    def check_student_source(self, id_no):
        """Check if a student exists in student_information or appraised curriculum.
        Args:
            id_no (str): Student ID number to check.
        Returns:
            str: 'appraised' if found in appraised curriculum, 
                'regular' if found in student_information,
                'not_found' otherwise."""
        try:
            # First check appraised curriculum
            query_appraised = """
                SELECT COUNT(*) FROM appraised_curriculum 
                WHERE id_no = %s
            """
            self.cursor.execute(query_appraised, (id_no,))
            appraised_count = self.cursor.fetchone()[0]

            if appraised_count > 0:
                return 'appraised'  # Found in appraised curriculum

            # Check student_information table
            query_student_info = """
                SELECT COUNT(*) FROM student_information 
                WHERE ID_NO = %s
            """
            self.cursor.execute(query_student_info, (id_no,))
            student_info_count = self.cursor.fetchone()[0]

            if student_info_count > 0:
                return 'regular'  # Found in student_information

            return 'not_found'  # Not found in any table

        except Exception as e:
            print(f"Error checking student source: {e}")
            return 'not_found'  # Return not found on error

    def get_student_info(self):
        try:
            query = """
                SELECT 
                    ID_NO,
                    LAST_NAME,
                    FIRST_NAME,
                    MIDDLE_NAME,
                    YR,
                    AGE,
                    SEX,
                    EMAIL_ADDRESS,
                    SHS,
                    ADDRESS
                FROM student_information
                ORDER BY LAST_NAME, FIRST_NAME, MIDDLE_NAME
            """
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            columns = ['ID_NO', 'LAST_NAME', 'FIRST_NAME', 'MIDDLE_NAME', 'YR', 'AGE', 
                      'SEX', 'EMAIL_ADDRESS', 'SHS', 'ADDRESS']
            return pd.DataFrame(result, columns=columns)
        except mysql.connector.Error as e:
            messagebox.showerror(f"Error getting student information: {e}")
            return pd.DataFrame()

    def get_missing_grades(self, year_level):
        try:
            table_mapping = {
                "1.1": "first_year_first_semester",
                "1.2": "first_year_second_semester",
                "2.1": "second_year_first_semester",
                "2.2": "second_year_second_semester",
                "3.1": "third_year_first_semester",
                "3.2": "third_year_second_semester",
                "4.1": "fourth_year_first_semester",
                "4.2": "fourth_year_second_semester"
            }

            table_name = table_mapping.get(year_level)
            if not table_name:
                raise ValueError(f"Invalid year level: {year_level}")

            # Get courses for the specific year level from curriculum_regular
            year_decimal = float(year_level)
            self.cursor.execute("""
                SELECT COURSE_NO 
                FROM curriculum_regular 
                WHERE YEAR_LEVEL = %s
            """, (year_decimal,))
            
            curriculum_courses = [row[0] for row in self.cursor.fetchall()]
            
            if not curriculum_courses:
                print(f"No courses found for year level {year_level}")
                return pd.DataFrame()

            # Modified query to use curriculum courses
            query = f"""
                SELECT DISTINCT 
                    si.ID_NO,
                    CONCAT(
                        si.LAST_NAME, ', ',
                        si.FIRST_NAME,
                        CASE 
                            WHEN si.MIDDLE_NAME IS NOT NULL AND si.MIDDLE_NAME != '' 
                            THEN CONCAT(' ', si.MIDDLE_NAME) 
                            ELSE '' 
                        END
                    ) as STUDENT_NAME,
                    cr.COURSE_NO
                FROM 
                    student_information si
                    CROSS JOIN curriculum_regular cr
                    LEFT JOIN `{table_name}` g 
                        ON si.ID_NO = g.ID_NO 
                WHERE 
                    cr.YEAR_LEVEL = %s
                    AND cr.COURSE_NO IN ({', '.join(['%s'] * len(curriculum_courses))})
                    AND (g.ID_NO IS NULL OR g.`{curriculum_courses[0]}` IS NULL)
                ORDER BY 
                    si.LAST_NAME, si.FIRST_NAME, si.MIDDLE_NAME, cr.COURSE_NO
            """
            
            # Create parameter tuple with year_level and course list
            params = (year_decimal,) + tuple(curriculum_courses)
            
            print(f"Executing query: {query}")  # Debug print
            print(f"Parameters: {params}")  # Debug print
            print(f"Curriculum courses: {curriculum_courses}")  # Debug print
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            columns = ['ID_NO', 'STUDENT_NAME', 'COURSE_NO']
            df = pd.DataFrame(results, columns=columns)
            return df
        
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error: {e}")
            return pd.DataFrame()

    def check_existing_grade(self, student_id, course_no, year, semester, school_year):
        """Check if a grade already exists for a student in a specific course and semester. 
        Args:
            student_id (str): Student's ID number
            course_no (str): Course number/code
            year (str): Year level (e.g., "1st Year")
            semester (str): Semester (e.g., "1st Semester")
            school_year (str): School year (e.g., "2024-2025")
            
        Returns:
            bool: True if grade exists, False otherwise
        """
        try:
            # Map the year and semester to table name
            year_mapping = {"1st Year": "first_year", "2nd Year": "second_year", "3rd Year": "third_year", "4th Year": "fourth_year"}
            semester_mapping = {"1st Semester": "first_semester", "2nd Semester": "second_semester"}
            
            table_name = f"{year_mapping[year]}_{semester_mapping[semester]}"

            # Check if grade exists
            query = f"""
                SELECT COUNT(*) 
                FROM `{table_name}` 
                WHERE ID_NO = %s 
                AND COURSE_NO = %s 
                AND SCHOOL_YEAR = %s
                AND GRADES IS NOT NULL
            """
            
            self.cursor.execute(query, (student_id, course_no, school_year))
            count = self.cursor.fetchone()[0]
            
            return count > 0

        except mysql.connector.Error as err:
            print(f"Database Error in check_existing_grade: {err}")
            return False
        except Exception as e:
            print(f"Error in check_existing_grade: {e}")
            return False
            
    def create_users_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS admin_management (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            salt VARCHAR(255) NOT NULL,
            role VARCHAR(50) DEFAULT 'user',
            is_active BOOLEAN DEFAULT FALSE,
            last_login DATETIME,
            registration_date DATETIME NOT NULL
        )
        """
        try:
            self.cursor.execute(create_table_query)
            self.conn.commit()
        except Error as e:
            print(f"Error creating admin_management table: {e}")
            raise

    def save_user(self, id, email, hashed_password, salt, username):
        try:
            # Validate input
            if not all([id, email, hashed_password, salt, username]):
                raise ValueError("All fields are required")

            # Email validation
            import re
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                raise ValueError("Invalid email format")

            # Username validation
            if len(username) < 3:
                raise ValueError("Username must be at least 3 characters long")

            # Check for existing email
            check_query = "SELECT * FROM admin_management WHERE email = %s"
            self.cursor.execute(check_query, (email,))
            existing_user = self.cursor.fetchone()
            
            if existing_user:
                raise ValueError("Email already registered")

            # Check for existing username
            check_username_query = "SELECT * FROM admin_management WHERE username = %s"
            self.cursor.execute(check_username_query, (username,))
            existing_username = self.cursor.fetchone()
            
            if existing_username:
                raise ValueError("Username already taken")

            # Prepare insert query
            insert_query = """
                INSERT INTO admin_management 
                    (id, username, email, password, salt, role, is_active, registration_date, last_login) 
                VALUES 
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Get current timestamp
            current_time = datetime.now()
            
            # Execute insert
            self.cursor.execute(insert_query, (
                id,               # New id field
                username, 
                email, 
                hashed_password, 
                salt,
                'user',           # Default role
                False,            # Default is_active status
                current_time,     # Registration date
                current_time      # Set last_login to current time
            ))
            
            # Commit transaction
            self.conn.commit()
            
            # Log successful registration
            logging.info(f"New user registered: {username} ({email}) with ID: {id}")
            
            return True
        
        except mysql.connector.Error as db_error:
            # Specific database-related error handling
            print(f"Database Error: {db_error}")
            self.conn.rollback()
            
            # Check for specific MySQL error codes
            if db_error.errno == mysql.connector.errorcode.ER_DUP_ENTRY:
                raise ValueError("A user with this ID, email, or username already exists")
            
            raise RuntimeError(f"Database error occurred: {db_error}")
        
        except ValueError as ve:
            # Validation error handling
            print(f"Validation Error: {ve}")
            self.conn.rollback()
            raise
        
        except Exception as e:
            # Catch-all for any other unexpected errors
            print(f"Unexpected Error in save_user: {e}")
            self.conn.rollback()
            raise RuntimeError(f"An unexpected error occurred: {e}")
                
    def get_next_user_id(self):
        self.cursor.execute("SELECT MAX(id) FROM admin_management")  # Adjust the table name as necessary
        result = self.cursor.fetchone()
        return (result[0] + 1) if result[0] is not None else 0  # Start from 0 if no users exist

    def get_user_by_email(self, email):
        try:
            if not email:
                return None
            
            query = """
                SELECT id, username, email, password, salt, role, is_active, last_login 
                FROM admin_management 
                WHERE email = %s
            """
            self.cursor.execute(query, (email,))
            user = self.cursor.fetchone()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'password': user[3],
                    'salt': user[4],
                    'role': user[5],
                    'is_active': user[6],
                    'last_login': user[7]
                }
            return None
        
        except Error as e:
            print(f"Error retrieving user: {e}")
            return None

    def __del__(self):
        """Cleanup method for database connection"""
        try:
            # Only close if explicitly requested or program is truly ending
            if hasattr(self, '_closing') and self._closing:
                if self.conn.is_connected():
                    self.cursor.close()
                    self.conn.close()
                    print("MySQL connection explicitly closed")
        except:
            pass
    def close(self):
        """Method to explicitly close the connection when needed"""
        self._closing = True
        try:
            if self.conn.is_connected():
                self.cursor.close()
                self.conn.close()
                print("MySQL connection explicitly closed")
        except Exception as e:
            print(f"Error closing connection: {e}")
            
    def create_templates_table(self):
        """
        Creates the 'templates' table if it does not already exist.
        """
        query = """
        CREATE TABLE IF NOT EXISTS templates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            file_name VARCHAR(255) NOT NULL,
            file_data LONGTEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            self.cursor.execute(query)
            self.conn.commit()
            print("Table 'templates' created or already exists.")
        except Exception as e:
            print(f"Error creating table: {e}")
            self.conn.rollback()

    def save_templates_to_database(self, file_paths):
        """
        Saves multiple CSV files to the 'templates' table in the database.
        """
        try:
            for file_path in file_paths:
                # Extract file name
                file_name = os.path.basename(file_path)

                # Read the CSV file
                with open(file_path, 'r') as file:
                    csv_data = file.read()

                # Insert the file into the database
                query = "INSERT INTO templates (file_name, file_data) VALUES (%s, %s)"
                self.cursor.execute(query, (file_name, csv_data))

            # Commit the transaction
            self.conn.commit()
            print(f"{len(file_paths)} files saved to the database.")

        except Exception as e:
            print(f"Error saving files to the database: {e}")
            self.conn.rollback()

        finally:
            # Close the cursor and connection
            self.cursor.close()
            self.conn.close()

    def preload_grade_data(self):
        """Preload grade data for all semesters"""
        try:
            grade_data = {}
            semesters = [
                "1.1", "1.2", "2.1", "2.2",
                "3.1", "3.2", "4.1", "4.2"
            ]
            
            for semester in semesters:
                grade_data[semester] = self.get_grades_by_semester(semester, "2023-2024", "All")
            
            return grade_data
            
        except Exception as e:
            print(f"Error preloading grade data: {e}")
            return {}
        
    def get_grades_by_semester(self, year_level, school_year, sex_filter):
        try:
            table_mapping = {
                "1.1": "first_year_first_semester",
                "1.2": "first_year_second_semester",
                "2.1": "second_year_first_semester",
                "2.2": "second_year_second_semester",
                "3.1": "third_year_first_semester",
                "3.2": "third_year_second_semester",
                "4.1": "fourth_year_first_semester",
                "4.2": "fourth_year_second_semester"
            }
            
            table_name = table_mapping.get(year_level)
            if not table_name:
                raise ValueError(f"Invalid year level: {year_level}")
            
            # Get course columns for this semester
            columns_query = f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = %s 
            AND COLUMN_NAME NOT IN ('ID_NO', 'LAST_NAME', 'FIRST_NAME', 'MIDDLE_NAME', 'SCHOOL_YEAR')
            ORDER BY ORDINAL_POSITION
            """
            self.cursor.execute(columns_query, (table_name,))
            course_columns = [row[0] for row in self.cursor.fetchall()]
            
            # Get all grades data
            grades_query = f"""
            SELECT 
                si.ID_NO,
                si.SEX,
                CONCAT(
                    si.LAST_NAME, ', ', 
                    si.FIRST_NAME,
                    CASE 
                        WHEN si.MIDDLE_NAME IS NOT NULL AND si.MIDDLE_NAME != '' 
                        THEN CONCAT(' ', si.MIDDLE_NAME)
                        ELSE '' 
                    END
                ) as Student_Name,
                {', '.join(f'g.`{col}`' for col in course_columns)}
            FROM 
                student_information si
                LEFT JOIN {table_name} g ON si.ID_NO COLLATE utf8mb4_unicode_ci = g.ID_NO
            WHERE 
                g.SCHOOL_YEAR = %s
                AND si.SEX = %s
            ORDER BY 
                si.LAST_NAME, 
                si.FIRST_NAME, 
                si.MIDDLE_NAME
            """
            
            self.cursor.execute(grades_query, (school_year, sex_filter))
            
            # Convert results to pandas DataFrame
            df = pd.DataFrame(self.cursor.fetchall(), columns=['ID_NO', 'SEX', 'Student_Name'] + course_columns)
            
            return {
                'columns': df.columns.tolist(),
                'data': df.to_dict('records')  # Convert DataFrame to list of dictionaries
            }
            
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            raise
        except Exception as e:
            print(f"Error loading grades: {e}")
            raise

    def get_available_school_years(self, year_level):
        """
        Get available school years for a specific semester
        """
        try:
            table_mapping = {
                "1.1": "first_year_first_semester",
                "1.2": "first_year_second_semester",
                "2.1": "second_year_first_semester",
                "2.2": "second_year_second_semester",
                "3.1": "third_year_first_semester",
                "3.2": "third_year_second_semester",
                "4.1": "fourth_year_first_semester",
                "4.2": "fourth_year_second_semester"
            }
            
            table_name = table_mapping.get(year_level)
            if not table_name:
                raise ValueError(f"Invalid year level: {year_level}")
            
            # Get available school years for this semester
            query = f"""
            SELECT DISTINCT SCHOOL_YEAR 
            FROM {table_name}
            WHERE SCHOOL_YEAR IS NOT NULL
            ORDER BY SCHOOL_YEAR DESC
            """
            self.cursor.execute(query)
            school_years = [year[0] for year in self.cursor.fetchall()]
            
            return school_years if school_years else ["No data available"]
            
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            raise
        except Exception as e:
            print(f"Error getting school years: {e}")
            raise

    def update_grade(self, student_id, course_no, new_grade, year_level, school_year):
        """Update a student's grade in the database"""
        try:
            table_mapping = {
                "1.1": "first_year_first_semester",
                "1.2": "first_year_second_semester",
                "2.1": "second_year_first_semester",
                "2.2": "second_year_second_semester",
                "3.1": "third_year_first_semester",
                "3.2": "third_year_second_semester",
                "4.1": "fourth_year_first_semester",
                "4.2": "fourth_year_second_semester"
            }
            
            table_name = table_mapping.get(year_level)
            if not table_name:
                raise ValueError(f"Invalid year level: {year_level}")
            
            # Update the grade
            update_query = f"""
            UPDATE {table_name}
            SET `{course_no}` = %s
            WHERE ID_NO = %s AND SCHOOL_YEAR = %s
            """
            
            self.cursor.execute(update_query, (new_grade, student_id, school_year))
            self.conn.commit()
            
            return True
            
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            messagebox.showerror("Error", f"Failed to update grade: {err}")
            return False
        except Exception as e:
            print(f"Error: {e}")
            messagebox.showerror("Error", f"An error occurred: {e}")
            return False

    def get_all_users(self):
        """Fetch all users with their status and last login"""
        try:
            query = """
                SELECT id, username, role, last_login, is_active 
                FROM Admin_management 
                ORDER BY username
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []

    def update_user_status(self, user_id, new_status):
        """Update user's active status with comprehensive checks"""
        cursor = None
        try:
            # Create a new cursor for this operation
            cursor = self.conn.cursor(buffered=True)
            
            # Verify the user exists before updating
            check_query = "UPDATE admin_management SET is_active = %s, last_updated = NOW() WHERE id = %s"
            cursor.execute(check_query, (user_id,))
            
            # Fetch the result to ensure there are no unread results
            existing_user = cursor.fetchone()
            
            if not existing_user:
                print(f"No user found with ID {user_id}")
                return False
            
            # Proceed with update if user exists
            query = "UPDATE admin_management SET is_active = %s WHERE id = %s"
            cursor.execute(query, (new_status, user_id))
            
            rows_affected = cursor.rowcount
            if rows_affected == 0:
                print(f"Failed to update status for user ID {user_id}")
                return False
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error updating user status: {e}")
            self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
                

     #this is for the student grades.py           
    def register_student(self, student_id, last_name, middle_name, first_name, password):
        self.cursor.execute("""
            INSERT INTO studgrade_pass (ID_NO, LAST_NAME, MIDDLE_NAME, FIRST_NAME, PASSWORD)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_id, last_name, middle_name, first_name, password))
        self.conn.commit()

    def get_student(self, student_id):
        self.cursor.execute("SELECT * FROM studgrade_pass WHERE ID_NO = %s", (student_id,))
        return self.cursor.fetchone()

    def get_grades(self, student_id):
        table_names = {
            'first_year_first_semester': '1.1',
            'first_year_second_semester': '1.2',
            'second_year_first_semester': '2.1',
            'second_year_second_semester': '2.2',
            'third_year_first_semester': '3.1',
            'third_year_second_semester': '3.2',
            'fourth_year_first_semester': '4.1',
            'fourth_year_second_semester': '4.2'
        }
        grades = []

        for table, sem_key in table_names.items():
            try:
                # Fetch column names for the table
                cursor = self.conn.cursor()
                cursor.execute(f"SHOW COLUMNS FROM `{table}`")
                columns = [col[0] for col in cursor.fetchall() if col[0] not in ('ID_NO', 'LAST_NAME', 'FIRST_NAME', 'MIDDLE_NAME', 'SCHOOL_YEAR')]
                cursor.close()  # Close the cursor after fetching column names

                if columns:
                    # Fetch grades for the student
                    cursor = self.conn.cursor()
                    query = f"SELECT {', '.join([f'`{col}`' for col in columns])} FROM `{table}` WHERE ID_NO = %s"
                    cursor.execute(query, (student_id,))
                    result = cursor.fetchone()
                    cursor.fetchall()  # Consume any remaining results to avoid "Unread result found" error
                    cursor.close()  # Close the cursor after fetching grades

                    if result:
                        for course_no, grade_value in zip(columns, result):
                            grades.append((sem_key, course_no, grade_value))
                    else:
                        # If no grades, append empty grades
                        for course_no in columns:
                            grades.append((sem_key, course_no, ""))
            except mysql.connector.Error as e:
                print(f"Error processing table {table}: {e}")
            finally:
                # Ensure the cursor is closed explicitly
                if cursor:
                    cursor.close()

        return grades

    def school_year(self, student_id, semester):
        table_names = {
            '1.1': 'first_year_first_semester',
            '1.2': 'first_year_second_semester',
            '2.1': 'second_year_first_semester',
            '2.2': 'second_year_second_semester',
            '3.1': 'third_year_first_semester',
            '3.2': 'third_year_second_semester',
            '4.1': 'fourth_year_first_semester',
            '4.2': 'fourth_year_second_semester'
        }
        table = table_names.get(semester)
        if not table:
            print(f"Invalid semester identifier: {semester}")  # Debug print
            return "N/A"

        try:
            cursor = self.conn.cursor()
            query = f"SELECT SCHOOL_YEAR FROM `{table}` WHERE ID_NO = %s"
            print(f"Executing query: {query} with student_id: {student_id}")  # Debug print
            cursor.execute(query, (student_id,))
            result = cursor.fetchone()
            cursor.fetchall()  # Consume any remaining results to avoid "Unread result found" error
            print(f"Query result: {result}")  # Debug print
            return result[0] if result else "N/A"
        except mysql.connector.Error as e:
            print(f"Error fetching school year for {table}: {e}")
            return "N/A"
        finally:
            cursor.close()
            
    def get_descriptive_title(self, course_no):
        cursor = self.conn.cursor()
        try:
            query = "SELECT DESCRIPTIVE_TITLE FROM curriculum_regular WHERE COURSE_NO = %s"
            cursor.execute(query, (course_no,))
            result = cursor.fetchone()
            cursor.fetchall()  # Consume any remaining results to avoid "Unread result found" error
            return result[0] if result else "Unknown"
        finally:
            cursor.close()

    def get_students_list(self):
        """Retrieve list of students for display purposes"""
        try:
            # Ensure connection is active
            if not self.conn or not self.conn.is_connected():
                self.conn, self.cursor = self.get_db_connection()

            # Query to get basic student information
            query = """
            SELECT 
                ID_NO, 
                CONCAT(LAST_NAME, ', ', FIRST_NAME, ' ', COALESCE(MIDDLE_NAME, '')) AS FULL_NAME,
                YR,
                ENROLLED_YEAR
            FROM student_information
            ORDER BY LAST_NAME, FIRST_NAME
            """
            
            self.cursor.execute(query)
            students = self.cursor.fetchall()

            return students

        except mysql.connector.Error as e:
            messagebox.showerror("Retrieval Error", f"Failed to retrieve students: {e}")
            return []

    def search_students(self, search_term):
        """Search students by ID, Name, or Year"""
        try:
            # Ensure connection is active
            if not self.conn or not self.conn.is_connected():
                self.conn, self.cursor = self.get_db_connection()

            # Comprehensive search query
            search_query = """
            SELECT 
                ID_NO, 
                CONCAT(LAST_NAME, ', ', FIRST_NAME, ' ', COALESCE(MIDDLE_NAME, '')) AS FULL_NAME,
                YR,
                ENROLLED_YEAR
            FROM student_information 
            WHERE ID_NO LIKE %s OR 
                  CONCAT(LAST_NAME, ' ', FIRST_NAME, ' ', COALESCE(MIDDLE_NAME, '')) LIKE %s OR
                  YR = %s
            ORDER BY LAST_NAME, FIRST_NAME
            """
            
            # Prepare search parameters
            search_param = f"%{search_term}%"
            
            # Try to convert search term to year if possible
            try:
                year_param = int(search_term)
            except ValueError:
                year_param = 0
            
            # Execute search
            self.cursor.execute(search_query, (search_param, search_param, year_param))
            students = self.cursor.fetchall()

            return students

        except mysql.connector.Error as e:
            messagebox.showerror("Search Error", f"Failed to search students: {e}")
            return []
        
    def get_students_list(self):
        """Retrieve list of students for display purposes, filtered by year value of 4, and include SCHOOL_YEAR."""
        try:
            # Ensure connection is active
            if not self.conn or not self.conn.is_connected():
                self.conn, self.cursor = self.get_db_connection()

            # Query to get basic student information, filtered by YR = 4
            query = """
            SELECT 
                ID_NO, 
                CONCAT(LAST_NAME, ', ', FIRST_NAME, ' ', COALESCE(MIDDLE_NAME, '')) AS FULL_NAME,
                YR,
                ENROLLED_YEAR
            FROM student_information
            WHERE YR = 4
            ORDER BY LAST_NAME, FIRST_NAME
            """
            
            self.cursor.execute(query)
            students = self.cursor.fetchall()

            # Convert to list of dictionaries if not already
            if students and isinstance(students[0], dict):
                students_list = students
            elif students:
                # Convert tuple results to dictionary
                column_names = ['ID_NO', 'FULL_NAME', 'YR', 'ENROLLED_YEAR']
                students_list = [dict(zip(column_names, student)) for student in students]
            else:
                return []

            # Add SCHOOL_YEAR to each student's data
            for student in students_list:
                id_no = student['ID_NO']
                school_year = self.get_school_year(id_no)  # Retrieve SCHOOL_YEAR
                student['SCHOOL_YEAR'] = school_year

            return students_list

        except mysql.connector.Error as e:
            messagebox.showerror("Retrieval Error", f"Failed to retrieve students: {e}")
            return []
        
    def get_school_year(self, id_no):
        """
        Retrieve the SCHOOL_YEAR for a specific student from the fourth_year_second_semester table.
        """
        try:
            # Ensure connection is active
            if not self.conn or not self.conn.is_connected():
                self.conn, self.cursor = self.get_db_connection()

            # Query to get SCHOOL_YEAR for the given ID_NO
            query = """
            SELECT SCHOOL_YEAR 
            FROM fourth_year_second_semester 
            WHERE ID_NO = %s
            """
            self.cursor.execute(query, (id_no,))
            result = self.cursor.fetchone()

            # Return SCHOOL_YEAR if found, otherwise return "N/A"
            return result[0] if result else "N/A"

        except mysql.connector.Error as e:
            messagebox.showerror("Retrieval Error", f"Failed to retrieve SCHOOL_YEAR for ID {id_no}: {e}")
            return "N/A"
                
    def search_students(self, search_term):
        """
        Search students by ID, Name, or Year
        """
        try:
            # Ensure connection is active
            if not self.conn or not self.conn.is_connected():
                self.conn, self.cursor = self.get_db_connection()

            # Comprehensive search query
            search_query = """
            SELECT 
                ID_NO, 
                CONCAT(LAST_NAME, ', ', FIRST_NAME, ' ', COALESCE(MIDDLE_NAME, '')) AS FULL_NAME,
                YR,
                ENROLLED_YEAR
            FROM student_information 
            WHERE ID_NO LIKE %s OR 
                  CONCAT(LAST_NAME, ' ', FIRST_NAME, ' ', COALESCE(MIDDLE_NAME, '')) LIKE %s OR
                  YR = %s
            ORDER BY LAST_NAME, FIRST_NAME
            """
            
            # Prepare search parameters
            search_param = f"%{search_term}%"
            
            # Try to convert search term to year if possible
            try:
                year_param = int(search_term)
            except ValueError:
                year_param = 0
            
            # Execute search
            self.cursor.execute(search_query, (search_param, search_param, year_param))
            students = self.cursor.fetchall()

            # Convert to list of dictionaries if not already
            if students and isinstance(students[0], dict):
                return students
            elif students:
                # Convert tuple results to dictionary
                column_names = ['ID_NO', 'FULL_NAME', 'YR', 'ENROLLED_YEAR']
                return [dict(zip(column_names, student)) for student in students]
            
            return []

        except mysql.connector.Error as e:
            messagebox.showerror("Search Error", f"Failed to search students: {e}")
            return []
        
    def get_course_data(self, student_id):
        course_data = {}

        try:
            #Use dictionary cursor correctly
            cursor = self.conn.cursor(dictionary=True)

            # List of table names
            table_names = [
                'first_year_first_semester',
                'first_year_second_semester',
                'second_year_first_semester',
                'second_year_second_semester',
                'third_year_first_semester',
                'third_year_second_semester',
                'fourth_year_first_semester',
                'fourth_year_second_semester'
            ]

            # Loop over table names to retrieve grades for each table
            for table_name in table_names:
                # Fix: Use the correct cursor reference
                columns_query = f"""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = %s 
                    AND COLUMN_NAME NOT IN ('ID_NO', 'LAST_NAME', 'FIRST_NAME', 'MIDDLE_NAME', 'SCHOOL_YEAR', 'YR')
                """
                cursor.execute(columns_query, (table_name,))
                course_columns = [col['COLUMN_NAME'] for col in cursor.fetchall() if isinstance(col, dict)]

                # Debugging: Print columns
                print(f"Columns for {table_name}: {course_columns}")

                # If no columns found, skip to next table
                if not course_columns:
                    continue

                # Escape column names with spaces
                escaped_columns = [f"`{col}`" for col in course_columns]
                select_columns = ', '.join(escaped_columns)

                # Construct dynamic query with escaped column names
                grade_query = f"""
                    SELECT ID_NO, {select_columns}
                    FROM `{table_name}`
                    WHERE ID_NO = %s
                """

                try:
                    #Fix: Use the correct cursor reference
                    cursor.execute(grade_query, (student_id,))
                    results = cursor.fetchall()

                    # Process results
                    table_grades = []
                    for row in results:
                        for col in course_columns:
                            grade = row.get(col)

                            #Fix: Handle valid grades properly
                            if grade is not None and str(grade).strip().upper() not in ['', 'N/A', '0', 'NULL']:
                                if [col, grade] not in table_grades:
                                    table_grades.append([col, grade])

                    # Add non-empty grades to course data
                    if table_grades:
                        course_data[table_name] = table_grades
                        print(f"Grades found in {table_name}: {table_grades}")

                except Exception as query_error:
                    print(f"Error in {table_name}: {query_error}")
                    continue

            #Fix: Remove duplicate entries across tables
            unique_course_data = {}
            for table, grades in course_data.items():
                for grade_entry in grades:
                    if grade_entry[0] not in [existing[0] for existing in unique_course_data.get(table, [])]:
                        if table not in unique_course_data:
                            unique_course_data[table] = []
                        unique_course_data[table].append(grade_entry)

            # Comprehensive debugging
            print("Final Course Data:")
            for table, courses in unique_course_data.items():
                print(f"{table}: {courses}")

            return unique_course_data

        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            return None
        finally:
            #Fix: Ensure cursor is closed properly
            if 'cursor' in locals() and cursor is not None:
                cursor.close()
                        
    def get_course_columns(self, table_name):
        """Retrieve the column names for the specified course table."""
        try:
            # Ensure connection is active
            if not self.conn.is_connected():
                self.conn, self.cursor = self.get_db_connection()

            query = f"SHOW COLUMNS FROM {table_name}"
            self.cursor.execute(query)
            return [column['Field'] for column in self.cursor.fetchall()]
        except mysql.connector.Error as err:
            print(f"Error retrieving columns: {err}")
            return []
                            

    def get_curriculum_regular(self):
        try:
            # Ensure connection is active
            if not self.conn.is_connected():
                self.conn, self.cursor = self.get_db_connection()

            query = """
                SELECT 
                    COURSE_NO, 
                    DESCRIPTIVE_TITLE, 
                    YEAR_LEVEL, 
                    UNITS, 
                    LEC, 
                    LAB, 
                    PREREQUISITE, 
                    GRADES
                FROM 
                    curriculum_regular
            """
            
            # Execute the query
            self.cursor.execute(query)
            
            # Fetch results
            results = self.cursor.fetchall()
            
            # Check if results are empty
            if not results:
                logging.warning("No curriculum data found")
                return [], []

            # Extract column names
            column_names = [desc[0] for desc in self.cursor.description]
            
            # Log successful retrieval
            logging.info(f"Retrieved {len(results)} curriculum records")
            
            return column_names, results

        except mysql.connector.Error as err:
            # Detailed MySQL error logging
            logging.error(f"MySQL Database error: {err}")
            print(f"MySQL Database error: {err}")
            
            # Additional detailed error tracking
            traceback.print_exc()
            return [], []

    def get_unenrolled_students(self, year_level, current_sy):
        """Fetch students of a given year level who are not yet enrolled in both first and second semester.
        :param year_level: The year level of students (1, 2, 3, or 4).
        :param current_sy: The current school year (e.g., "2024-2025").
        :return: List of dictionaries containing student details.
        """
        # Map numeric year_level to its word equivalent for table names
        year_word_map = {
            "1": "first",
            "2": "second",
            "3": "third",
            "4": "fourth",
            1: "first",
            2: "second",
            3: "third",
            4: "fourth"
        }
        year_word = year_word_map.get(year_level)
        if not year_word:
            print(f"Invalid year_level: {year_level}")
            return []

        try:
            query = f"""
                SELECT s.ID_NO, s.LAST_NAME, s.FIRST_NAME, s.MIDDLE_NAME, s.YR, s.ENROLLED_YEAR
                FROM student_information s
                LEFT JOIN {year_word}_year_first_semester fyfs ON s.ID_NO = fyfs.ID_NO AND fyfs.SCHOOL_YEAR = %s
                LEFT JOIN {year_word}_year_second_semester fyss ON s.ID_NO = fyss.ID_NO AND fyss.SCHOOL_YEAR = %s
                WHERE s.YR = %s  
                AND fyfs.ID_NO IS NULL AND fyss.ID_NO IS NULL;
            """

            # Debugging: Print query before executing
            print(f"Executing query for {year_level}-year students: {query} with {current_sy}")

            self.cursor.execute(query, (current_sy, current_sy, year_level))
            students = self.cursor.fetchall()

            # Debugging: Print fetched students
            print(f"Fetched {year_level}-year students: {students}")

            if not students:
                print(f"No {year_level}-year students found.")
                return []

            #Now using the format_students function to structure the data
            return self.format_students(students)

        except mysql.connector.Error as err:
            print(f"{year_level} year Database error: {err}")
            return []

    def format_students(self, students):
        """
        Helper function to format student data into a list of dictionaries.
        """
        student_list = []
        for row in students:
            student_list.append({
                "ID_NO": row[0],
                "LAST_NAME": row[1],
                "FIRST_NAME": row[2],
                "MIDDLE_NAME": row[3] if row[3] else "",
                "YEAR_LEVEL": row[4],
                "ENROLLMENT_STATUS": "Not Enrolled"
            })
        return student_list
