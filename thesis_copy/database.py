from configparser import Error
import logging
import pandas as pd
from tkinter import messagebox
import mysql.connector
from datetime import datetime
import re

class DatabaseHandler:
    def __init__(self):
        self.conn, self.cursor = self.get_db_connection()
    def get_db_connection(self):
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='', 
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
    def saving_student(self, last_name, first_name, middle_name, data, enrolled_year, table_name=None):
        try:
            # Create table with separate name fields and ENROLLED_YEAR using YEAR type
            create_table_query = """
                CREATE TABLE IF NOT EXISTS student_information (
                    ID_NO VARCHAR(255) PRIMARY KEY,
                    LAST_NAME VARCHAR(100) NOT NULL,
                    FIRST_NAME VARCHAR(100) NOT NULL,
                    MIDDLE_NAME VARCHAR(100),
                    YR VARCHAR(255),
                    AGE INT,
                    SEX CHAR(25),
                    EMAIL_ADDRESS VARCHAR(255),
                    SHS VARCHAR(255),
                    ADDRESS VARCHAR(255),
                    ENROLLED_YEAR YEAR
                )
            """
            self.cursor.execute(create_table_query)

            # Process the data with separate name fields and ENROLLED_YEAR
            processed_data = []
            for row in data:
                processed_row = (
                    row[0],        # ID_NO
                    last_name,     # LAST_NAME
                    first_name,    # FIRST_NAME
                    middle_name,   # MIDDLE_NAME
                    row[2],        # YR
                    row[3],        # AGE
                    row[4],        # SEX
                    row[5],        # EMAIL_ADDRESS
                    row[6],        # SHS
                    row[7],        # ADDRESS
                    enrolled_year  # ENROLLED_YEAR from selection
                )
                processed_data.append(processed_row)

            # Insert data
            insert_query = """
                INSERT INTO student_information (
                    ID_NO, LAST_NAME, FIRST_NAME, MIDDLE_NAME,
                    YR, AGE, SEX, EMAIL_ADDRESS, SHS, ADDRESS, ENROLLED_YEAR
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.executemany(insert_query, processed_data)

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


    # pag display sa irregular studnt baga
    def fetch_irregular_students(self, id_no): #sa irregular student ni sa 
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

                logging.info(f"Found {len(appraised_results)} records for ID_NO: {id_no}")
                return appraised_results

            except mysql.connector.Error as err:
                logging.error(f"An error occurred while fetching irregular student data: {err.msg}")
                return []        
        
    def update_student_yr(self, id_no): # para kat update ng year level ng student
        """
        Automatically updates student's year level based on completed semesters.
        Prohibits update if there are any empty grades.
        Args:
            id_no (str): Student ID number
        Returns:
            str: New year level if updated, None if no update needed
        """
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
                curriculum_regular cr ON cr.Year_Level = %s
            WHERE
                si.ID_NO = %s
        """
        curriculum_params = (year_level, id_no)

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
            '4.2': 'fourth_year_second_semester'
        }

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
            "grades_data": all_grades_data
        }
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
            'fourth_year_second_semester'
        ]

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
                'fourth_year_second_semester'
            ])
            
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

   # pag savve ng grading shetyt
    def save_grading_data(self, grading_data, year, semester, school_year):
        try:
            # Clean DataFrame column names
            grading_data = grading_data.copy()
            grading_data.columns = grading_data.columns.str.strip()

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

            # Get student info columns and course columns
            student_info_columns = ['ID_NO', 'LAST_NAME', 'FIRST_NAME', 'MIDDLE_NAME']
            course_columns = [col for col in grading_data.columns if col not in student_info_columns]

            # Create table if it doesn't exist
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                `ID_NO` VARCHAR(255),
                `LAST_NAME` VARCHAR(100),
                `FIRST_NAME` VARCHAR(100),
                `MIDDLE_NAME` VARCHAR(100),
                `SCHOOL_YEAR` VARCHAR(20),
                {', '.join(f'`{col}` VARCHAR(10)' for col in course_columns)},
                PRIMARY KEY (`ID_NO`, `SCHOOL_YEAR`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """

            print(f"Creating table with query: {create_table_query}")
            self.cursor.execute(create_table_query)
            self.conn.commit()

            # Verify table exists
            self.cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            if not self.cursor.fetchone():
                raise Exception(f"Failed to create table {table_name}")

            # Insert data
            columns = student_info_columns + ['SCHOOL_YEAR'] + course_columns
            placeholders = ', '.join(['%s'] * len(columns))
            insert_query = f"""
            INSERT INTO `{table_name}` 
            (`{'`, `'.join(columns)}`)
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE
            {', '.join(f'`{col}` = VALUES(`{col}`)' for col in columns if col != 'ID_NO')}
            """

            # Process each row
            for _, row in grading_data.iterrows():
                values = [
                    str(row['ID_NO']).strip(),
                    str(row['LAST_NAME']).strip(),
                    str(row['FIRST_NAME']).strip(),
                    str(row.get('MIDDLE_NAME', '')).strip(),
                    school_year.strip()
                ]
                
                # Add grades for each course
                for course in course_columns:
                    grade = str(row[course]).strip().upper() if pd.notna(row[course]) else ''
                    values.append(grade)

                try:
                    self.cursor.execute(insert_query, tuple(values))
                except mysql.connector.Error as err:
                    print(f"Error inserting row: {err}")
                    print(f"Values: {values}")
                    raise

            self.conn.commit()
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
        """
        Fetch a single student's details by ID number
        """
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

    def save_manual_grades(self, grading_data, year_level, school_year):
        try:
            # Map year levels to table names
            year_mapping = {
                "1.1": "first_year_first_semester",
                "1.2": "first_year_second_semester",
                "2.1": "second_year_first_semester",
                "2.2": "second_year_second_semester",
                "3.1": "third_year_first_semester",
                "3.2": "third_year_second_semester",
                "4.1": "fourth_year_first_semester",
                "4.2": "fourth_year_second_semester"
            }

            table_name = year_mapping.get(year_level)
            if not table_name:
                raise ValueError(f"Invalid year level: {year_level}")

            # Get the table structure to know available course columns
            self.cursor.execute(f"DESCRIBE {table_name}")
            table_columns = [row[0] for row in self.cursor.fetchall()]
            course_columns = [col for col in table_columns if col not in 
                             ['ID_NO', 'LAST_NAME', 'FIRST_NAME', 'MIDDLE_NAME', 'SCHOOL_YEAR']]
            
            print("Available course columns:", course_columns)  # Debug print

            # Define valid grades
            valid_grades = {1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0}

            # Process each row in the grading data
            for _, row in grading_data.iterrows():
                try:
                    course_no = row['Course No.'].strip()
                    if course_no not in course_columns:
                        raise ValueError(f"Invalid course: {course_no} for this semester")

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

                    # Check if student record exists
                    check_query = f"""
                        SELECT * FROM {table_name} 
                        WHERE ID_NO = %s AND SCHOOL_YEAR = %s
                    """
                    self.cursor.execute(check_query, (row['ID_NO'].strip(), school_year))
                    existing_record = self.cursor.fetchone()

                    if existing_record:
                        # Update existing record with the new grade for the specific course
                        update_query = f"""
                        UPDATE {table_name}
                        SET `{course_no}` = %s,
                            LAST_NAME = %s,
                            FIRST_NAME = %s,
                            MIDDLE_NAME = %s
                        WHERE ID_NO = %s AND SCHOOL_YEAR = %s
                        """
                        values = (
                            str(grade),
                            row['Last Name'].strip(),
                            row['First Name'].strip(),
                            row['Middle Name'].strip(),
                            row['ID_NO'].strip(),
                            school_year
                        )
                        self.cursor.execute(update_query, values)
                    else:
                        # Create a new record with NULL for all courses except the current one
                        columns = ['ID_NO', 'LAST_NAME', 'FIRST_NAME', 'MIDDLE_NAME', 'SCHOOL_YEAR']
                        values = [
                            row['ID_NO'].strip(),
                            row['Last Name'].strip(),
                            row['First Name'].strip(),
                            row['Middle Name'].strip(),
                            school_year
                        ]
                        
                        # Add all course columns
                        for col in course_columns:
                            columns.append(f"`{col}`")
                            values.append(str(grade) if col == course_no else None)

                        placeholders = ', '.join(['%s'] * len(columns))
                        insert_query = f"""
                        INSERT INTO {table_name}
                        ({', '.join(columns)})
                        VALUES ({placeholders})
                        """
                        self.cursor.execute(insert_query, values)

                except ValueError as ve:
                    messagebox.showerror("Validation Error", str(ve))
                    self.conn.rollback()
                    return False

            self.conn.commit()
            return True

        except mysql.connector.Error as err:
            print(f"MySQL Error: {err}")
            messagebox.showerror("Database Error", f"Error saving grades: {err}")
            return False
        except Exception as e:
            print(f"Unexpected Error: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            return False

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

    def get_school_year(self, student_id, semester):
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