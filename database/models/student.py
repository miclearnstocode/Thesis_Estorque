import datetime
from tkinter import messagebox
import mysql.connector
import logging
import pandas as pd

class StudentModel:
    def __init__(self, db_connection):
        self.db = db_connection

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
    def check_student_source(self, id_no):
        """
        Check if a student exists in student_information or appraised curriculum.

        Args:
            id_no (str): Student ID number to check.

        Returns:
            str: 'appraised' if found in appraised curriculum, 
                'regular' if found in student_information,
                'not_found' otherwise.
        """
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

    def get_students_list(self):
        """
        Retrieve list of students for display purposes
        """
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

            return students

        except mysql.connector.Error as e:
            messagebox.showerror("Search Error", f"Failed to search students: {e}")
            return []

    def register_student(self, student_id, last_name, middle_name, first_name, password):
        self.cursor.execute("""
            INSERT INTO studgrade_pass (ID_NO, LAST_NAME, MIDDLE_NAME, FIRST_NAME, PASSWORD)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_id, last_name, middle_name, first_name, password))
        self.conn.commit()

    def get_student(self, student_id):
        self.cursor.execute("SELECT * FROM studgrade_pass WHERE ID_NO = %s", (student_id,))
        return self.cursor.fetchone()

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
