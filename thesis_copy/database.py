# database.py
import logging
import re
import pandas as pd
from tkinter import messagebox
import psycopg2
import psycopg2.extras
from datetime import datetime
import time, os, logging
from psycopg2.extras import RealDictCursor
from config_manager import config_manager
from postgres_manager import PostgresManager

class DatabaseHandler:
    def __init__(self):
        try:
            #comscie@2025
            # Initialize PostgreSQL manager and ensure it's running
            self.postgres_manager = PostgresManager()
            postgres_config = config_manager.get_postgres_config()
            
            if postgres_config.get('auto_start', True):
                if not self.postgres_manager.ensure_postgres_running():
                    logging.error("Failed to start PostgreSQL server")
                    self.show_connection_error("Failed to start PostgreSQL server")
                    return
            
            # Get configuration from config manager
            db_config = config_manager.get_database_config()
            
            self.host = db_config['host']
            self.user = db_config['user']
            self.password = db_config['password']
            self.database = db_config['database']
            self.port = db_config['port']
            
            logging.info(f"Database config loaded: {self.host}, {self.user}, {self.database}")
            self.conn = None
            self.cursor = None
            
            # Get initial connection
            self.conn, self.cursor = self.get_db_connection()
        except Exception as e:
            logging.error(f"DatabaseHandler initialization failed: {e}")
            self.show_config_error(e)
            
    def get_db_connection(self):
        try:
            conn = psycopg2.connect(host=self.host, user=self.user, password=self.password, dbname=self.database, port=self.port)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            logging.info("PostgreSQL connection established successfully")
            return conn, cursor

        except psycopg2.OperationalError as err:
            # Handle common PostgreSQL connection issues with clear messages
            message = str(err)

            if "password authentication failed" in message:
                user_message = "Access denied — check your username and password."
            elif "could not connect to server" in message:
                user_message = ("Cannot connect to PostgreSQL server. Please ensure:\n"
                    "• PostgreSQL service is running\n"
                    "• Host and port are correct\n"
                    "• Firewall is not blocking the connection")
            elif "does not exist" in message:
                user_message = "Database does not exist — please create it first."
            elif "could not translate host name" in message:
                user_message = "Unknown PostgreSQL host — check the hostname in your configuration."
            else:
                user_message = f"Database connection error: {message}"

            logging.error(f"PostgreSQL connection failed: {user_message}")
            print(f"Database connection failed: {user_message}")
            raise Exception(user_message)

        except psycopg2.Error as err:
            # Catch-all for other psycopg2 errors
            logging.error(f"Unexpected PostgreSQL error: {err}")
            raise Exception(f"Unexpected PostgreSQL error: {err}")

        
    def show_config_error(self, error):
        """Show configuration error to user"""
        print("Configuration Error",error)
        
    def show_connection_error(self, error):
        """Show connection error to user"""
        error_messages = {1045: "Access denied - Check username and password",
            1049: "Database 'department' does not exist", 
            2003: "Cannot connect to PostgreSQL server - Make sure PostgreSQL is running",
            2005: "Unknown PostgreSQL server host - Check host address"}
        
        user_message = error_messages.get(error.errno, f"Database error: {error}")
        print("Database Connection Failed", user_message)
        
    def close_db_connection(self):
        self.conn.close()
    
    def saving_curriculum_data(self, processed_data):
        if processed_data.empty:
            messagebox.showerror("Error", "No data to save!")
            return
        try:
            effective_sy = processed_data['SY_Revision'].iloc[0]
            curriculum_name = f"Curriculum {effective_sy}"  # Optional: replace with GUI input if needed

            # Ensure the connection is valid
            if self.conn.closed != 0:
                raise psycopg2.Error("Database connection lost.")

            cursor = self.conn.cursor()

            # Step 1: Check if curriculum_version exists by effective_sy
            cursor.execute("SELECT curriculum_id FROM curriculum_version WHERE effective_sy = %s", (effective_sy,))
            result = cursor.fetchone()

            if result:
                curriculum_id = result[0]
            else:
                # PostgreSQL: use RETURNING to get the inserted ID
                cursor.execute("INSERT INTO curriculum_version (effective_sy, name) VALUES (%s, %s) RETURNING curriculum_id",
                    (effective_sy, curriculum_name))
                curriculum_id = cursor.fetchone()[0]

            # Step 2: Insert into curriculum_regular
            query = """
                INSERT INTO curriculum_regular 
                    (Course_No, Descriptive_Title, Year_Level, Units, Lab, Lec, Prerequisite, Grades, sy_revision, curriculum_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = [( row.Course_No, row.Descriptive_Title, row.Year_Level, None if pd.isna(row.Units) else row.Units, None if pd.isna(row.Lab) else row.Lab, None if pd.isna(row.Lec) else row.Lec, None if pd.isna(row.Prerequisite) else row.Prerequisite, None if pd.isna(row.Grades) else row.Grades, effective_sy, curriculum_id) for _, row in processed_data.iterrows()]

            cursor.executemany(query, values)
            self.conn.commit()
            messagebox.showinfo("Success", "Curriculum data saved successfully!")

        except psycopg2.Error as err:
            print("Error encountered:", err)
            if self.conn and self.conn.closed == 0:
                self.conn.rollback()
            messagebox.showerror("Error", f"Database error: {err}")

        finally:
            if self.conn and self.conn.closed == 0:
                cursor.close()
                self.conn.close()

    # ini sa pag add student           
    def saving_student_data(self, data):
        if not data:
            messagebox.showerror("Error", "No student data provided.")
            return

        try:
            # PostgreSQL connection check
            if not self.conn or self.conn.closed != 0:
                raise psycopg2.Error("Database connection lost.")
            
            self.cursor = self.conn.cursor()

            # Helper to get curriculum_id based on ENROLLED_YEAR
            def get_curriculum_id_for_year(enrolled_year):
                self.cursor.execute("""SELECT curriculum_id 
                    FROM curriculum_version 
                    WHERE effective_sy <= %s 
                    ORDER BY effective_sy DESC 
                    LIMIT 1
                """, (enrolled_year,))
                result = self.cursor.fetchone()
                return result[0] if result else None

            processed_data = []
            for row in data:
                # Split full name into LAST, FIRST, MIDDLE
                full_name = row[1]
                parts = full_name.strip().split(",")
                last_name = parts[0].strip()
                first_middle = parts[1].strip().split(" ") if len(parts) > 1 else [""]
                first_name = first_middle[0]
                middle_name = " ".join(first_middle[1:]) if len(first_middle) > 1 else ""

                # Convert BIRTHDAY safely
                try:
                    bday = pd.to_datetime(row[6], errors='coerce').date() if row[6] else None
                except Exception:
                    bday = None

                # Handle enrolled year and curriculum
                enrolled_year = row[12]
                to_be_enrolled_years = row[13] if len(row) > 13 else None
                curriculum_id = get_curriculum_id_for_year(enrolled_year)

                processed_row = (
                    row[0],         # id_no
                    last_name,      # LAST_NAME
                    first_name,     # FIRST_NAME
                    middle_name,    # MIDDLE_NAME
                    row[2],         # YR
                    row[3],         # AGE
                    bday,           # BDAY
                    row[4],         # SEX
                    row[5],         # PARENT_GUARDIAN
                    row[7],         # PHONE_NUMBER
                    row[8],         # EMAIL_ADDRESS
                    row[9],         # SHS
                    row[10],        # ADDRESS
                    enrolled_year,  # ENROLLED_YEAR
                    to_be_enrolled_years, curriculum_id)
                processed_data.append(processed_row)

            # INSERT or UPDATE logic using PostgreSQL-safe code
            for row in processed_data:
                self.cursor.execute("SELECT COUNT(*) FROM student_information WHERE id_no = %s", (row[0],))
                exists = self.cursor.fetchone()[0] > 0

                if exists:
                    update_query = """
                        UPDATE student_information
                        SET LAST_NAME=%s, FIRST_NAME=%s, MIDDLE_NAME=%s, YR=%s, AGE=%s, BDAY=%s, 
                            SEX=%s, PARENT_GUARDIAN=%s, PHONE_NUMBER=%s, EMAIL_ADDRESS=%s, SHS=%s,
                            ADDRESS=%s, ENROLLED_YEAR=%s, TO_BE_ENROLLED_YEAR=%s, curriculum_id=%s
                        WHERE id_no=%s
                    """
                    self.cursor.execute(update_query, (*row[1:], row[0]))
                else:
                    insert_query = """
                        INSERT INTO student_information (
                            id_no, LAST_NAME, FIRST_NAME, MIDDLE_NAME, YR, AGE, BDAY, SEX,
                            PARENT_GUARDIAN, PHONE_NUMBER, EMAIL_ADDRESS, SHS, ADDRESS,
                            ENROLLED_YEAR, TO_BE_ENROLLED_YEAR, curriculum_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    self.cursor.execute(insert_query, row)

            self.conn.commit()
            messagebox.showinfo("Success", "Student data saved successfully!")

        except psycopg2.Error as err:
            if self.conn and self.conn.closed == 0:
                self.conn.rollback()
            logging.error(f"PostgreSQL error: {err}")
            messagebox.showerror("Database Error", f"PostgreSQL error: {err}")

        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn and self.conn.closed == 0:
                self.conn.close()

    # ni hu sa appraised curriculum
    def save_appraised_data(self, appraised_id, id_no, last_name, first_name, middle_name, year, sex, age, birthday, contact_number, email_address, address, parent_guardian, matched_subjects, school_year):
        try:
            if not school_year:
                raise ValueError("School year is required")

            if not self.conn or self.conn.closed != 0:
                raise psycopg2.Error("Database connection lost.")

            self.cursor = self.conn.cursor()

            # ✅ Create the table if it doesn't exist (PostgreSQL syntax) with all columns
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
                    birthday DATE,
                    contact_number VARCHAR(15), 
                    email_address VARCHAR(100), 
                    address VARCHAR(255),
                    parent_guardian VARCHAR(100), 
                    course_no VARCHAR(100), 
                    descriptive_title VARCHAR(100),
                    year_level NUMERIC(3,1), 
                    units INT, 
                    lec INT, 
                    lab INT, 
                    prerequisite VARCHAR(100), 
                    grades NUMERIC(5,2),
                    school_year VARCHAR(20), 
                    PRIMARY KEY (appraised_id, id_no, course_no)
                )
            """)

            # Insert matched subjects
            insert_query = f"""
                INSERT INTO {table_name} (
                    appraised_id, id_no, last_name, first_name, middle_name,
                    year, sex, age, birthday, contact_number, email_address,
                    address, parent_guardian, course_no, descriptive_title,
                    year_level, units, lec, lab, prerequisite, grades, school_year)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (appraised_id, id_no, course_no)
                DO UPDATE SET
                    last_name = EXCLUDED.last_name,
                    first_name = EXCLUDED.first_name,
                    middle_name = EXCLUDED.middle_name,
                    year = EXCLUDED.year,
                    sex = EXCLUDED.sex,
                    age = EXCLUDED.age,
                    birthday = EXCLUDED.birthday,
                    contact_number = EXCLUDED.contact_number,
                    email_address = EXCLUDED.email_address,
                    address = EXCLUDED.address,
                    parent_guardian = EXCLUDED.parent_guardian,
                    descriptive_title = EXCLUDED.descriptive_title,
                    year_level = EXCLUDED.year_level,
                    units = EXCLUDED.units,
                    lec = EXCLUDED.lec,
                    lab = EXCLUDED.lab,
                    prerequisite = EXCLUDED.prerequisite,
                    grades = EXCLUDED.grades,
                    school_year = EXCLUDED.school_year
            """

            for _, row in matched_subjects.iterrows():
                # Convert birthday to proper date format
                birthday_date = None
                if birthday and not pd.isna(birthday):
                    try:
                        if isinstance(birthday, str):
                            birthday_date = pd.to_datetime(birthday, errors='coerce').date()
                        else:
                            birthday_date = pd.to_datetime(birthday, errors='coerce').date()
                    except Exception:
                        birthday_date = None
                
                # Clean contact number
                clean_contact_number = None
                if contact_number and not pd.isna(contact_number):
                    clean_contact_number = str(contact_number).strip()
                    # Remove any non-digit characters except +
                    clean_contact_number = ''.join(filter(lambda x: x.isdigit() or x == '+', clean_contact_number))
                
                self.cursor.execute(insert_query, (
                    appraised_id, id_no, last_name, first_name,
                    middle_name, year, sex, age, birthday_date,
                    clean_contact_number,  # Use cleaned contact number
                    email_address if not pd.isna(email_address) else None,
                    address if not pd.isna(address) else None, 
                    parent_guardian if not pd.isna(parent_guardian) else None,
                    row.get('Course_No', None), 
                    row.get('Descriptive_Title', None), 
                    row.get('Year_Level', None),
                    0 if pd.isna(row.get('Units')) else row['Units'], 
                    0 if pd.isna(row.get('Lec')) else row['Lec'],
                    0 if pd.isna(row.get('Lab')) else row['Lab'], 
                    row.get('Prerequisite', None), 
                    0 if pd.isna(row.get('Grades')) else row['Grades'], 
                    school_year
                ))

            self.conn.commit()
            messagebox.showinfo("Success", "Appraised data saved to the database successfully!")

        except (psycopg2.Error, Exception) as e:
            if self.conn and self.conn.closed == 0:
                self.conn.rollback()
            logging.error(f"Failed to save data to PostgreSQL: {e}")
            messagebox.showerror("Error", f"Failed to save data to the database:\n{e}")

        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn and self.conn.closed == 0:
                self.conn.close()
            
    def fetch_available_fallback_subjects(self, id_no):
        logging.debug(f"Fetching available fallback subjects for id_no: {id_no}")

        query = """
            SELECT 
                ac.course_no,
                ac.descriptive_title,
                ac.units
            FROM
                appraised_curriculum ac
            WHERE
                ac.id_no = %s
                AND (ac.grades IS NULL OR ac.grades = 0.00)
        """
        params = (id_no,)

        try:
            # Ensure the connection is active
            if not self.conn or self.conn.closed != 0:
                raise psycopg2.Error("Database connection lost.")

            # Create a fresh cursor with RealDictCursor to return dict-like results
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()

            if not results:
                logging.warning(f"No available fallback subjects found for id_no: {id_no}")
                return []

            logging.info(f"Found {len(results)} available fallback subjects for id_no: {id_no}")
            return results

        except psycopg2.Error as err:
            logging.error(f"Error fetching fallback subjects: {err}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error while fetching fallback subjects: {e}")
            return []

    # pag display sa irregular studnt baga
    def fetch_irregular_students(self, id_no):
        logging.debug(f"Fetching irregular student data for id_no: {id_no}")

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
                ac.birthday,
                ac.contact_number,
                ac.email_address,
                ac.address,
                ac.parent_guardian,
                ac.course_no, 
                ac.descriptive_title, 
                ac.year_level, 
                ac.units, 
                ac.lec, 
                ac.lab, 
                ac.prerequisite,
                ac.grades
            FROM appraised_curriculum ac
            WHERE ac.id_no = %s
        """
        appraised_params = (id_no,)

        try:
            # Ensure PostgreSQL connection is alive
            if not self.conn or self.conn.closed != 0:
                raise psycopg2.Error("Database connection lost.")

            # Use psycopg2 cursor safely
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(appraised_query, appraised_params)
                appraised_results = cursor.fetchall()

            if not appraised_results:
                logging.warning(f"No appraised curriculum data found for id_no: {id_no}")
                return []

            # Semester progression mapping
            semester_progression = {'1.1': '1.2', '1.2': '2.1','2.1': '2.2', '2.2': '3.1','3.1': '3.2', '3.2': '4.1','4.1': '4.2', '4.2': 'Graduate'}

            # Group courses by year level
            year_level_courses = {}
            for record in appraised_results:
                year_level = str(record.get('year_level', '')).strip()
                if not year_level:
                    continue
                if year_level not in year_level_courses:
                    year_level_courses[year_level] = []
                year_level_courses[year_level].append(record)

            if not year_level_courses:
                logging.warning(f"No valid year levels found for id_no: {id_no}")
                return appraised_results

            #Sort year levels for logical progression
            def parse_level(level):
                try:
                    parts = level.split('.')
                    return int(parts[0]), int(parts[1])
                except Exception:
                    return (99, 99)  # Put malformed values at the end

            sorted_year_levels = sorted(year_level_courses.keys(), key=parse_level)

            current_semester = None
            next_semester = None

            #Determine current and next semester based on grades
            for year_level in sorted_year_levels:
                courses = year_level_courses[year_level]
                all_passed = all(course.get('grades') is not None and str(course['grades']).strip() not in ['', '0.00'] and
                    float(course['grades']) >= 1.0  # Assuming passing grade ≥ 1.0
                    for course in courses)

                if all_passed:
                    current_semester = year_level
                    next_semester = semester_progression.get(year_level)
                    logging.info(f"All courses in {year_level} are passed")
                    logging.info(f"Current Semester: {current_semester}")
                    logging.info(f"Next Semester: {next_semester}")
                    break

            #Default fallback if no semester progression found
            if not current_semester:
                current_semester = sorted_year_levels[0]
                next_semester = semester_progression.get(current_semester, '1.2')

            #Add semester info to all records
            for record in appraised_results:
                record['current_sem'] = current_semester
                record['next_sem'] = next_semester
            return appraised_results
        except psycopg2.Error as err:
            logging.error(f"PostgreSQL error while fetching irregular student data: {err}")
            return []
        except Exception as err:
            logging.error(f"Unexpected error while fetching irregular student data: {err}")
            return []

    def update_student_yr(self, id_no):  # para kat update ng year level ng student
        try:
            #Ensure PostgreSQL connection is alive
            if not self.conn or self.conn.closed != 0:
                raise psycopg2.Error("Database connection lost.")

            print(f"\nChecking year level update for student ID: {id_no}")

            # Get all grades for the student
            all_grades = self.check_all_tables_for_grades(id_no)
            completed_semesters = set(all_grades.keys())
            print(f"Completed semesters: {completed_semesters}")

            # Check for incomplete or invalid grades
            for semester, grades in all_grades.items():
                for course, grade in grades.items():
                    if course in ['id_no', 'LAST_NAME', 'FIRST_NAME', 'MIDDLE_NAME', 'SCHOOL_YEAR']:
                        continue
                    if grade is None or str(grade).strip() == '' or str(grade).upper() == 'INC':
                        print(f"Found incomplete grade in {semester} for course {course}")
                        return None  # Stop if incomplete grades exist

            #Define semester requirements for each year level
            year_requirements = { '2': {'first_year_first_semester', 'first_year_second_semester'},'3': {'second_year_first_semester', 'second_year_second_semester'},'4': {'third_year_first_semester', 'third_year_second_semester'},'Graduate': {'fourth_year_first_semester', 'fourth_year_second_semester'}}

            # Fetch current year level safely
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT YR FROM student_information WHERE id_no = %s", (id_no,))
                result = cursor.fetchone()

            if not result:
                print(f"WARNING: No student found with ID: {id_no}")
                return None

            current_yr = str(result[0])
            print(f"Current year level: {current_yr}")

            # Determine new year level based on completed semesters
            new_yr = None
            for year, required_semesters in year_requirements.items():
                if required_semesters.issubset(completed_semesters):
                    if current_yr != 'Graduate':
                        new_yr = year
                        print(f"Requirements met for year {year}")

            # Perform update only if applicable
            if new_yr and new_yr != current_yr:
                print(f"Updating year level from {current_yr} to {new_yr}")
                with self.conn.cursor() as cursor:
                    cursor.execute("UPDATE student_information SET YR = %s WHERE id_no = %s", (new_yr, id_no))
                self.conn.commit()
                print(f"Successfully updated student {id_no} year level to {new_yr}")
                return new_yr
            else:
                print("No year level update needed")
                return None
        except psycopg2.Error as err:
            print(f"DATABASE ERROR: {err}")
            if self.conn and self.conn.closed == 0:
                self.conn.rollback()
            return None
        except Exception as e:
            print(f"UNEXPECTED ERROR: {e}")
            return None

    def insert_students(self, table_name, data):
        try:
            # Ensure PostgreSQL connection is alive
            if not self.conn or self.conn.closed != 0:
                raise psycopg2.Error("Database connection lost.")

            # ---  Phone number validation ---
            for row in data:
                phone = str(row.get('PHONE_NUMBER', '')).strip()
                phone_digits = ''.join(filter(str.isdigit, phone))

                if len(phone_digits) > 10:
                    messagebox.showerror("Validation Error", f"Phone number '{phone}' exceeds 10 digits.")
                    return  # Stop the insert if any phone number is invalid

                row['PHONE_NUMBER'] = phone_digits  # keep only numeric digits

            # Use parameterized PostgreSQL insert query
            insert_query = f"""
                INSERT INTO {table_name} (
                    id_no, LAST_NAME, FIRST_NAME, MIDDLE_NAME,
                    YR, AGE, BIRTHDAY, SEX, PARENT_GUARDIAN, PHONE_NUMBER,
                    EMAIL_ADDRESS, SHS, ADDRESS, ENROLLED_YEAR
                )
                VALUES (
                    %(id_no)s, %(LAST_NAME)s, %(FIRST_NAME)s, %(MIDDLE_NAME)s,
                    %(YR)s, %(AGE)s, %(BIRTHDAY)s, %(SEX)s, %(PARENT_GUARDIAN)s, %(PHONE_NUMBER)s,
                    %(EMAIL_ADDRESS)s, %(SHS)s, %(ADDRESS)s, %(ENROLLED_YEAR)s
                )
                ON CONFLICT (id_no)
                DO UPDATE SET
                    LAST_NAME = EXCLUDED.LAST_NAME,
                    FIRST_NAME = EXCLUDED.FIRST_NAME,
                    MIDDLE_NAME = EXCLUDED.MIDDLE_NAME,
                    YR = EXCLUDED.YR,
                    AGE = EXCLUDED.AGE,
                    BIRTHDAY = EXCLUDED.BIRTHDAY,
                    SEX = EXCLUDED.SEX,
                    PARENT_GUARDIAN = EXCLUDED.PARENT_GUARDIAN,
                    PHONE_NUMBER = EXCLUDED.PHONE_NUMBER,
                    EMAIL_ADDRESS = EXCLUDED.EMAIL_ADDRESS,
                    SHS = EXCLUDED.SHS,
                    ADDRESS = EXCLUDED.ADDRESS,
                    ENROLLED_YEAR = EXCLUDED.ENROLLED_YEAR
            """

            # Execute in bulk safely
            with self.conn.cursor() as cursor:
                cursor.executemany(insert_query, data)

            self.conn.commit()
            messagebox.showinfo("Success", "Students inserted or updated successfully!")

        except psycopg2.Error as err:
            logging.error(f"PostgreSQL insert error: {err}")
            if self.conn and self.conn.closed == 0:
                self.conn.rollback()
            messagebox.showerror("Database Error", f"Failed to insert data:\n{err}")

        except Exception as e:
            logging.error(f"Unexpected error during insert: {e}")
            if self.conn and self.conn.closed == 0:
                self.conn.rollback()
            messagebox.showerror("Error", f"Unexpected error occurred:\n{e}")

    # ini ya hu sa regular student na display 
    def fetch_student_data(self, id_no, year_level):
        logging.debug(f"Fetching data for id_no: {id_no}, Year Level: {year_level}")

        # First, verify the student exists and get basic info
        student_query = """
            SELECT 
                id_no, last_name, first_name, middle_name, yr, age,
                birthday, sex, parent_guardian, phone_number, 
                email_address, address, curriculum_id
            FROM student_information 
            WHERE id_no = %s
        """

        # Then get curriculum data based on curriculum_id
        curriculum_query = """
            SELECT 
                cr.course_no, 
                cr.descriptive_title, 
                cr.year_level, 
                cr.units, 
                cr.lec, 
                cr.lab, 
                cr.prerequisite,
                cr.grades
            FROM curriculum_regular cr
            WHERE cr.curriculum_id = %s
            AND (%s IS NULL OR cr.year_level::TEXT LIKE %s)
            ORDER BY cr.year_level, cr.course_no
        """

        try:
            # Ensure PostgreSQL connection is active
            if not self.conn or self.conn.closed != 0:
                logging.warning("Connection closed, reconnecting...")
                self.conn, self.cursor = self.get_db_connection()

            curriculum_results = []
            student_info = None

            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # First get student basic information
                cursor.execute(student_query, (id_no,))
                student_result = cursor.fetchone()
                
                if not student_result:
                    logging.warning(f"No student found for id_no: {id_no}")
                    return {
                        "curriculum_data": [],
                        "curriculum_regular_data": [],
                        "enrollment_status": "Student not found",
                        "table_exists": False,
                        "has_grades": False,
                        "grades_data": {},
                        "student_info": None}
                
                student_info = dict(student_result)
                
                # Format student name - use lowercase column names
                try:
                    last_name = student_info.get('last_name', '') or ''
                    first_name = student_info.get('first_name', '') or ''
                    middle = student_info.get('middle_name', '') or ''
                    middle_initial = f"{middle[0]}." if middle else ""
                    student_info['STUDENT_NAME'] = f"{last_name}, {first_name} {middle_initial}".strip()
                except (KeyError, IndexError, TypeError) as e:
                    logging.warning(f"Error formatting student name: {e}")
                    student_info['STUDENT_NAME'] = "Unknown Student"

                # Then get curriculum data based on curriculum_id
                curriculum_id = student_info.get('curriculum_id')
                if curriculum_id:
                    # Build LIKE pattern for year level filtering
                    if year_level and year_level != "Select":
                        year_pattern = f"{year_level.split('.')[0]}.%"
                    else:
                        year_pattern = f"{student_info.get('yr', '1')}.%"
                    
                    cursor.execute(curriculum_query, (curriculum_id, year_level, year_pattern))
                    curriculum_results = cursor.fetchall()
                    
                    # Combine student info with each curriculum record
                    combined_results = []
                    for curriculum in curriculum_results:
                        combined_record = student_info.copy()
                        combined_record.update(curriculum)
                        
                        # Ensure all required fields are present with proper keys
                        combined_record['COURSE_NO'] = curriculum.get('course_no', '')
                        combined_record['DESCRIPTIVE_TITLE'] = curriculum.get('descriptive_title', '')
                        combined_record['YEAR_LEVEL'] = curriculum.get('year_level', '')
                        combined_record['UNITS'] = curriculum.get('units', 0)
                        combined_record['LEC'] = curriculum.get('lec', 0)
                        combined_record['LAB'] = curriculum.get('lab', 0)
                        combined_record['PREREQUISITE'] = curriculum.get('prerequisite', '')
                        combined_record['GRADES'] = curriculum.get('grades', 0.00)
                        
                        combined_results.append(combined_record)
                    
                    curriculum_results = combined_results
                else:
                    logging.warning(f"No curriculum_id found for student {id_no}")

        except psycopg2.Error as err:
            logging.error(f"Database error while fetching student data: {err}")
            raise RuntimeError(f"Database error while fetching student data: {err}")

        # Map year levels to semester tables
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

        # Fetch all grades with error handling
        all_grades_data = {}
        try:
            all_grades_data = self.check_all_tables_for_grades(id_no)
        except Exception as e:
            logging.warning(f"Error fetching grades data: {e}")

        # Determine enrollment status
        current_table = table_mapping.get(year_level) if year_level and year_level != "Select" else None
        if current_table:
            if current_table in all_grades_data:
                enrollment_status = f"Student has grades for {year_level}"
            else:
                enrollment_status = f"No grades yet for {year_level}"
        else:
            enrollment_status = "Student found" if student_info else "Student not found"

        # Merge grade data into curriculum results with error handling
        for curriculum in curriculum_results:
            course_no = curriculum.get('course_no') or curriculum.get('COURSE_NO')
            if course_no:
                for table, grades in all_grades_data.items():
                    if course_no in grades:
                        curriculum[f'Grade_{table}'] = grades[course_no]
                        # Also update the main GRADES field
                        curriculum['GRADES'] = grades[course_no]

        logging.debug(f"Curriculum data with grades: {len(curriculum_results)} records")

        # Safely fetch all curriculum_regular rows
        curriculum_regular_data = []
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM curriculum_regular")
                curriculum_regular_data = cursor.fetchall()
        except Exception as e:
            logging.warning(f"Error fetching curriculum regular data: {e}")

        return {
            "curriculum_data": curriculum_results, 
            "curriculum_regular_data": curriculum_regular_data,
            "enrollment_status": enrollment_status, 
            "table_exists": current_table in all_grades_data if current_table else False,
            "has_grades": bool(all_grades_data.get(current_table)) if current_table else False,
            "grades_data": all_grades_data,
            "student_info": student_info  # Include student info separately
        }
        
    # pag check ng grade sa regular student
    def check_all_tables_for_grades(self, id_no):
        table_names = [
            'first_year_first_semester', 'first_year_second_semester',
            'second_year_first_semester', 'second_year_second_semester', 
            'third_year_first_semester', 'third_year_second_semester',
            'fourth_year_first_semester', 'fourth_year_second_semester'
        ]

        all_grades_data = {}

        # Loop through all semester tables
        for table in table_names:
            try:
                query = f"""
                    SELECT course_no, grades
                    FROM {table}
                    WHERE id_no = %s
                """

                # Ensure PostgreSQL connection is active
                if not self.conn or self.conn.closed != 0:
                    raise psycopg2.Error("Database connection lost.")

                # Use psycopg2 cursor safely
                with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute(query, (id_no,))
                    results = cursor.fetchall()

                if results:
                    grades_data = {}
                    for row in results:
                        course_no = row.get('course_no')
                        grade = row.get('grades')
                        if course_no and grade is not None and str(grade).strip() != '':
                            grades_data[course_no] = grade

                    if grades_data:
                        all_grades_data[table] = grades_data
                        logging.debug(f"Found grades in {table}: {grades_data}")

            except psycopg2.errors.UndefinedTable:
                # Table might not exist — skip silently
                logging.warning(f"Table '{table}' does not exist. Skipping.")
                continue
            except psycopg2.Error as err:
                logging.error(f"PostgreSQL error checking {table}: {err}")
                continue
            except Exception as e:
                logging.error(f"Unexpected error checking {table}: {e}")
                continue
        
        return all_grades_data

    def get_latest_school_year(self, id_no):
        """Get the latest school year from student information and then from student's grades"""
        try:
            #Ensure PostgreSQL connection is active
            if not self.conn or self.conn.closed != 0:
                raise psycopg2.Error("Database connection lost.")

            # Step 1: Check the school year in student_information
            student_info_query = """
                SELECT enrolled_year, yr
                FROM student_information
                WHERE id_no = %s
            """

            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(student_info_query, (id_no,))
                student_info_result = cursor.fetchall()

            #If a record is found and the student is in first year
            if student_info_result and student_info_result[0]['yr'] == '1':
                latest_school_year = student_info_result[0]['enrolled_year']
                try:
                    # Normalize the format of school year
                    if isinstance(latest_school_year, int):
                        start_year = str(latest_school_year)
                        formatted_year = f"{start_year}-{int(start_year) + 1}"
                        return formatted_year
                    elif isinstance(latest_school_year, str):
                        return latest_school_year.strip()
                except (ValueError, IndexError):
                    return None

            #Step 2: Determine which grade tables to check
            table_mapping = {'1': ['first_year_first_semester', 'first_year_second_semester'], '2': ['second_year_first_semester', 'second_year_second_semester'],'3': ['third_year_first_semester', 'third_year_second_semester'],'4': ['fourth_year_first_semester', 'fourth_year_second_semester']}

            year_level = student_info_result[0]['yr'] if student_info_result else None
            tables_to_check = table_mapping.get(year_level, ['first_year_first_semester', 'first_year_second_semester',
                'second_year_first_semester', 'second_year_second_semester', 'third_year_first_semester', 'third_year_second_semester', 'fourth_year_first_semester', 'fourth_year_second_semester'])

            latest_school_year = None

            # Step 3: Search for the latest non-empty SCHOOL_YEAR from grade tables
            for table in tables_to_check:
                query = f"""
                    SELECT school_year
                    FROM {table}
                    WHERE id_no = %s
                    AND school_year IS NOT NULL
                    AND TRIM(school_year) <> ''
                    ORDER BY school_year DESC
                    LIMIT 1
                """
                try:
                    with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                        cursor.execute(query, (id_no,))
                        result = cursor.fetchall()

                    if result and result[0]['school_year']:
                        latest_school_year = result[0]['school_year']
                        break  # Stop once a valid school year is found

                except psycopg2.errors.UndefinedTable:
                    logging.warning(f"Table '{table}' does not exist, skipping...")
                    continue
                except psycopg2.Error as err:
                    logging.error(f"Database error while checking {table}: {err}")
                    continue

            #Step 4: Normalize and return formatted school year
            if latest_school_year:
                def parse_school_year(year_str):
                    year_str = str(year_str).strip()
                    if '-' in year_str or '/' in year_str:
                        return year_str
                    try:
                        start_year = int(year_str)
                        return f"{start_year}-{start_year + 1}"
                    except ValueError:
                        return year_str

                return parse_school_year(latest_school_year)

            return None

        except psycopg2.Error as err:
            logging.error(f"PostgreSQL error in get_latest_school_year: {err}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in get_latest_school_year: {e}")
            return None

    def get_latest_school_year_irregular(self, id_no):
        """Get the latest school year from appraised_curriculum for irregular students (PostgreSQL version)."""
        try:
            #Ensure PostgreSQL connection is alive
            if not self.conn or self.conn.closed != 0:
                raise psycopg2.Error("Database connection lost.")

            query = """
                SELECT school_year
                FROM appraised_curriculum
                WHERE id_no = %s
                AND school_year IS NOT NULL
                AND TRIM(school_year) <> ''
                ORDER BY school_year DESC
                LIMIT 1
            """

            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, (id_no,))
                result = cursor.fetchall()

            if result and result[0]['school_year']:
                latest_school_year = result[0]['school_year'].strip()

                try:
                    # Handle common formats cleanly
                    if '-' in latest_school_year:
                        parts = latest_school_year.split('-')
                        if len(parts) == 2 and all(p.isdigit() for p in parts):
                            return latest_school_year
                        start_year = int(parts[0])
                        return f"{start_year}-{start_year + 1}"

                    elif '/' in latest_school_year:
                        parts = latest_school_year.split('/')
                        if len(parts) == 2 and all(p.isdigit() for p in parts):
                            return latest_school_year
                        start_year = int(parts[0])
                        return f"{start_year}/{start_year + 1}"

                    else:
                        #Single year → Convert to range (e.g. "2025" → "2025-2026")
                        start_year = int(latest_school_year)
                        return f"{start_year}-{start_year + 1}"

                except (ValueError, IndexError):
                    logging.warning(f"Unrecognized school year format for ID {id_no}: {latest_school_year}")
                    return None

            else:
                logging.info(f"No school year found in appraised_curriculum for ID {id_no}")
                return None

        except psycopg2.Error as err:
            logging.error(f"PostgreSQL error in get_latest_school_year_irregular: {err}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in get_latest_school_year_irregular: {e}")
            return None

    # pag display sa curriculum data hatag also copy sa each ka student 
    def fetch_curriculum(self, year_level, id_no):
        logging.debug(f"Fetching curriculum data for Year Level: {year_level}, id_no: {id_no}")

        curriculum_query = """
            SELECT
                si.id_no,  si.last_name, si.first_name,
                si.middle_name, si.yr, si.age, 
                si.sex,  si.email_address, si.shs,
                si.address, cr.course_no, cr.descriptive_title, 
                cr.year_level, cr.units, cr.lec, cr.lab, cr.prerequisite
            FROM
                student_information si
            LEFT JOIN
                curriculum_regular cr ON (cr.year_level::TEXT LIKE si.yr::TEXT || '.%' OR cr.year_level = %s)
            WHERE
                si.id_no = %s
        """

        curriculum_params = (year_level, id_no)
        try:
            #Ensure PostgreSQL connection is alive
            if not self.conn or self.conn.closed != 0:
                raise psycopg2.Error("Database connection lost.")

            #Use RealDictCursor so results are dictionaries (not tuples)
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(curriculum_query, curriculum_params)
                curriculum_results = cursor.fetchall()

            if not curriculum_results:
                logging.warning(f"No curriculum data found for Year Level: {year_level}, id_no: {id_no}")
                return []

            #Format student name and clean result keys
            for result in curriculum_results:
                last_name = result.get('last_name', '') or ''
                first_name = result.get('first_name', '') or ''
                middle_name = result.get('middle_name', '') or ''
                middle_initial = f"{middle_name[0]}." if middle_name else ''
                result['student_name'] = f"{last_name}, {first_name} {middle_initial}".strip()

                # Optionally remove raw fields
                for field in ['last_name', 'first_name', 'middle_name']:
                    result.pop(field, None)

            logging.info(f"Fetched {len(curriculum_results)} curriculum records for {id_no}")

            return curriculum_results

        except psycopg2.Error as err:
            logging.error(f"PostgreSQL error while fetching curriculum data: {err}")
            raise RuntimeError(f"Database error while fetching curriculum data: {err}")

        except Exception as e:
            logging.error(f"Unexpected error while fetching curriculum data: {e}")
            raise RuntimeError(f"Unexpected error while fetching curriculum data: {e}")

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
        except psycopg2.Error as e:
            logging.error(f"Error executing query: {e}")
            self.conn.rollback()
            raise"""
       #new execute query method jan 8 2025 
    def execute_query(self, query, params=None):
        logging.debug(f"Executing query: {query} with params: {params}")

        try:
            #Ensure connection is active
            if not self.conn or self.conn.closed != 0:
                raise psycopg2.Error("Database connection lost.")

            #Use RealDictCursor to get results as dictionaries
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params or ())

                #If SELECT query, fetch all records
                if query.strip().lower().startswith("select"):
                    results = cursor.fetchall()
                    logging.debug(f"Fetched {len(results)} records.")
                    return results
                else:
                    #Commit any INSERT/UPDATE/DELETE automatically
                    self.conn.commit()
                    logging.debug("Query executed successfully and committed.")

        except psycopg2.Error as e:
            #Rollback on any SQL error
            if self.conn and self.conn.closed == 0:
                self.conn.rollback()
            logging.error(f"PostgreSQL error executing query: {e}")
            raise RuntimeError(f"Database error: {e}")

        except Exception as e:
            logging.error(f"Unexpected error executing query: {e}")
            raise RuntimeError(f"Unexpected error: {e}")

    def execute_query_with_retry(self, query, params=None, retries=3, delay=5):
        """
        Execute a PostgreSQL query with automatic reconnection and retry logic.
        - Retries a few times if connection is lost or query fails.
        - Returns results (list of dicts) for SELECT queries.
        - Commits automatically for non-SELECT queries.
        """
        for attempt in range(1, retries + 1):
            cursor = None
            try:
                #  Ensure connection is active
                if not self.conn or self.conn.closed != 0:
                    logging.warning("PostgreSQL connection lost. Reconnecting...")
                    self.conn = psycopg2.connect(host=self.host, user=self.user, password=self.password, dbname=self.database, port=self.port)
                    logging.info("PostgreSQL connection re-established.")

                # Use RealDictCursor to get dict results
                cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute(query, params or ())

                #If SELECT, fetch results
                if query.strip().lower().startswith("select"):
                    results = cursor.fetchall()
                    logging.debug(f"Fetched {len(results)} records (attempt {attempt}/{retries}).")
                    return results
                else:
                    self.conn.commit()
                    logging.debug(f"Query executed successfully and committed (attempt {attempt}/{retries}).")
                    return None

            except psycopg2.Error as e:
                logging.error(f"PostgreSQL error on attempt {attempt}: {e}")

                # Rollback to clear the connection state
                if self.conn and self.conn.closed == 0:
                    self.conn.rollback()

                # Retry after delay (unless last attempt)
                if attempt < retries:
                    logging.warning(f"Retrying query in {delay} seconds... ({attempt}/{retries})")
                    time.sleep(delay)
                else:
                    logging.critical("All retry attempts failed.")
                    raise RuntimeError(f"Query failed after {retries} retries: {e}")

            except Exception as e:
                logging.error(f"Unexpected error during query (attempt {attempt}): {e}")
                raise

            finally:
                if cursor:
                    cursor.close()
                
    def get_existing_courses(self):
        """Fetch all existing course numbers from curriculum_regular (PostgreSQL-safe)."""
        try:
            # Ensure connection is active
            if not self.conn or self.conn.closed != 0:
                self.ensure_connection()  # Optional helper if you have one

            query = "SELECT course_no FROM curriculum_regular"

            # Use RealDictCursor for consistent dict-style results
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query)
                results = cursor.fetchall()

            # Convert results to uppercase, stripped set
            return {row['course_no'].strip().upper() for row in results if row['course_no']}

        except psycopg2.Error as e:
            logging.error(f"Database error fetching existing courses: {e}")
            if self.conn and self.conn.closed == 0:
                self.conn.rollback()
            return set()

        except Exception as e:
            logging.error(f"Unexpected error fetching existing courses: {e}")
            return set()

    def save_grading_data(self, grading_data, year, semester, school_year):
        """Save grading data to the appropriate table in PostgreSQL. Performs UPSERT (insert or update) on conflict."""
        try:
            # Clean DataFrame column names and normalize to lowercase
            grading_data = grading_data.copy()
            grading_data.columns = grading_data.columns.str.strip()
            
            # Normalize column names to handle case sensitivity
            column_mapping = {}
            for col in grading_data.columns:
                col_lower = col.lower()
                if col_lower in ['id_no', 'last_name', 'first_name', 'middle_name']:
                    column_mapping[col] = col_lower
                else:
                    column_mapping[col] = col  # Keep course columns as-is

            # Map year & semester to table name
            year_mapping = {"1st Year": "first_year", "2nd Year": "second_year", "3rd Year": "third_year", "4th Year": "fourth_year"}
            semester_mapping = {"1st Semester": "first_semester", "2nd Semester": "second_semester"}

            table_name = f"{year_mapping[year]}_{semester_mapping[semester]}"

            # Ensure connection is active
            if not self.conn or self.conn.closed != 0:
                self.ensure_connection()

            # Use normalized column names
            student_info_columns = ['id_no', 'last_name', 'first_name', 'middle_name']
            course_columns = [col for col in grading_data.columns if col.lower() not in [info_col.lower() for info_col in student_info_columns]]

            # PostgreSQL UPSERT (ON CONFLICT)
            insert_query = f"""
            INSERT INTO {table_name} 
                (id_no, last_name, first_name, middle_name, school_year, course_no, grades)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id_no, course_no, school_year)
            DO UPDATE SET grades = EXCLUDED.grades
            """

            values_list = []
            for _, row in grading_data.iterrows():
                # Handle case-insensitive column access
                student_id = str(row.get('ID_NO') or row.get('id_no', '')).strip()
                last_name = str(row.get('LAST_NAME') or row.get('last_name', '')).strip()
                first_name = str(row.get('FIRST_NAME') or row.get('first_name', '')).strip()
                middle_name = str(row.get('MIDDLE_NAME') or row.get('middle_name', '')).strip()

                student_info = [student_id, last_name, first_name, middle_name, school_year.strip()]

                # Iterate through all course columns
                for course in course_columns:
                    grade = row[course]
                    if pd.notna(grade) and str(grade).strip() != "":
                        try:
                            values = student_info + [course.strip(), float(grade)]
                            values_list.append(tuple(values))
                        except ValueError:
                            logging.warning(f"Invalid grade value for {course}: {grade}")
                            continue

            if values_list:
                with self.conn.cursor() as cursor:
                    cursor.executemany(insert_query, values_list)
                self.conn.commit()
                logging.info(f"Saved {len(values_list)} grade records into {table_name}")
                return True

            logging.info("No valid grading data to save.")
            return False

        except psycopg2.Error as err:
            if self.conn and self.conn.closed == 0:
                self.conn.rollback()
            logging.error(f"Database error while saving grades: {err}")
            print("Database Error save_grading_data", err)
            return False

        except Exception as e:
            if self.conn and self.conn.closed == 0:
                self.conn.rollback()
            logging.error(f"Unexpected error while saving grades: {e}")
            print("Error save_grading_data", e)
            return False
        
    def save_irregular_grading_data(self, grading_data, year, semester):
        """Save irregular grading data for a student into the appraised_curriculum table (PostgreSQL version). Updates existing records by matching id_no + course_no + year_level. """
        try:
            table_name = "appraised_curriculum"

            #Convert "year" + "semester" → numeric year_level (e.g., 2.1)
            def convert_year_level(year_text, semester_text):
                year_map = {'1ST YEAR': 1, '1ST': 1, '1': 1,
                            '2ND YEAR': 2, '2ND': 2, '2': 2,
                            '3RD YEAR': 3, '3RD': 3, '3': 3,
                            '4TH YEAR': 4, '4TH': 4, '4': 4}

                semester_map = {'1ST SEMESTER': 1, '1ST': 1, '1': 1,
                                '2ND SEMESTER': 2, '2ND': 2, '2': 2}

                y = year_map.get(str(year_text).upper().strip(), None)
                s = semester_map.get(str(semester_text).upper().strip(), None)
                return float(f"{y}.{s}") if y and s else None

            current_year_level = convert_year_level(year, semester)
            if current_year_level is None:
                raise ValueError(f"Invalid year/semester input: {year} {semester}")

            #Queries updated to PostgreSQL syntax
            comprehensive_search_query = f"""
                SELECT 
                    id_no, 
                    course_no, 
                    year_level, 
                    grades,
                    school_year
                FROM {table_name}
                WHERE 
                    id_no = %s AND 
                    course_no = %s
                ORDER BY ABS(year_level - %s)
            """

            update_query = f"""
                UPDATE {table_name}
                SET grades = %s, school_year = %s
                WHERE 
                    id_no = %s AND 
                    course_no = %s AND 
                    year_level = %s """

            # Use context-managed cursor for safety
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:

                # Normalize DataFrame to list if needed
                if isinstance(grading_data, pd.DataFrame):
                    grading_iterable = grading_data.to_dict(orient='records')
                elif isinstance(grading_data, list):
                    grading_iterable = grading_data
                else:
                    raise ValueError("grading_data must be a DataFrame or list of dicts")

                for entry in grading_iterable:
                    try:
                        # Normalize keys (case-insensitive)
                        id_no = entry.get('id_no') or entry.get('id_no')
                        course_no = entry.get('course_no') or entry.get('COURSE_NO')
                        grades = entry.get('grades') or entry.get('GRADES')
                        school_year = entry.get('school_year') or entry.get('SCHOOL_YEAR')

                        if not (id_no and course_no):
                            logging.warning(f"Skipping invalid record: {entry}")
                            continue

                        # Try update at current level first
                        cursor.execute(update_query, (grades, school_year, id_no, course_no, current_year_level))

                        if cursor.rowcount == 0:
                            # Fallback: find closest year_level record
                            cursor.execute(comprehensive_search_query, (id_no, course_no, current_year_level))
                            existing = cursor.fetchall()

                            if existing:
                                closest_year_level = existing[0]['year_level']
                                cursor.execute(update_query, (grades, school_year, id_no, course_no, closest_year_level))
                                logging.info(f"Updated fallback course {course_no} for {id_no} at year {closest_year_level}")
                            else:
                                logging.warning(f"No match found for course {course_no} (student {id_no})")

                    except Exception as inner_err:
                        logging.error(f"Error processing entry {entry}: {inner_err}")
                        continue

            self.conn.commit()
            logging.info("Irregular grading data saved successfully.")
            return True

        except psycopg2.Error as err:
            if self.conn and self.conn.closed == 0:
                self.conn.rollback()
            logging.error(f"Database error while saving irregular grades: {err}")
            print(f"Database Error: {err}")
            return False

        except Exception as e:
            if self.conn and self.conn.closed == 0:
                self.conn.rollback()
            logging.error(f"Unexpected error saving irregular grades: {e}")
            print(f"Error saving grades: {e}")
            return False

    def get_student_id(self, search_term=None):
        """Fetch student IDs and names from the student_information table. Compatible with PostgreSQL (psycopg2).
        """
        try:
            # Ensure connection is alive
            if not hasattr(self, 'conn') or not self.conn or self.conn.closed != 0:
                logging.warning("Reconnecting to PostgreSQL database...")
                self.conn = psycopg2.connect(host=self.host, user=self.user, password=self.password, dbname=self.database, port=self.port)
                logging.info("Database connection re-established.")

            #Use RealDictCursor for dictionary-style rows
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:

                if search_term:
                    query = """
                        SELECT DISTINCT 
                            id_no, 
                            last_name,
                            first_name,
                            middle_name
                        FROM student_information 
                        WHERE (
                            last_name ILIKE %s 
                            OR first_name ILIKE %s 
                            OR middle_name ILIKE %s
                        )
                        ORDER BY last_name, first_name, middle_name
                    """
                    params = (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")
                    cursor.execute(query, params)
                else:
                    query = """
                        SELECT DISTINCT 
                            id_no, 
                            last_name,
                            first_name,
                            middle_name
                        FROM student_information 
                        ORDER BY last_name, first_name, middle_name
                    """
                    cursor.execute(query)

                results = cursor.fetchall()
                logging.debug(f"Fetched {len(results)} students from database.")

                #Format names for display
                formatted_names = []
                for row in results:
                    name_parts = [row['last_name'], row['first_name']]
                    if row.get('middle_name'):
                        name_parts.append(row['middle_name'])
                    formatted_names.append(" ".join(name_parts))

                return {'full_data': results, 'names': formatted_names}

        except psycopg2.Error as err:
            logging.error(f"PostgreSQL error while fetching student data: {err}")
            if self.conn and self.conn.closed == 0:
                self.conn.rollback()
            return {'full_data': [], 'names': []}

        except Exception as e:
            logging.error(f"Unexpected error while fetching student data: {e}")
            return {'full_data': [], 'names': []}

    def get_student_by_id(self, id_no):
        """Fetch a single student's details by ID number (PostgreSQL version)."""
        try:
            #Ensure connection is active
            if not hasattr(self, 'conn') or not self.conn or self.conn.closed != 0:
                logging.warning("PostgreSQL connection lost. Reconnecting...")
                self.conn = psycopg2.connect(host=self.host,user=self.user,password=self.password,dbname=self.database,port=self.port)
                logging.info("Database connection re-established.")

            query = """
                SELECT 
                    id_no,
                    last_name,
                    first_name,
                    middle_name
                FROM student_information
                WHERE id_no = %s
                LIMIT 1
            """

            #  Use context manager to auto-close cursor
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, (id_no,))
                result = cursor.fetchone()

            # Return dictionary result directly (keys match column names)
            if result:
                return {'id_no': result['id_no'],'LAST_NAME': result['last_name'],'FIRST_NAME': result['first_name'],'MIDDLE_NAME': result['middle_name']}

            logging.info(f"No student found with id_no: {id_no}")
            return None

        except psycopg2.Error as e:
            if self.conn and self.conn.closed == 0:
                self.conn.rollback()
            logging.error(f"PostgreSQL error fetching student by ID: {e}")
            print(f"Database error fetching student: {e}")
            return None

        except Exception as e:
            logging.error(f"Unexpected error fetching student by ID: {e}")
            print(f"Error fetching student: {e}")
            return None

    def check_student_existence(self, id_no):
        """Check if student exists in multiple tables.
        Args:
            id_no (str): Student ID number to check.
        Returns:
            bool: True if student exists in any table, False otherwise.
        """
        try:
            # Ensure connection is alive
            if not self.conn or self.conn.closed != 0:
                self.conn, self.cursor = self.get_db_connection()

            with self.conn.cursor() as cursor:
                # Check in student_information
                cursor.execute("SELECT COUNT(*) FROM student_information WHERE id_no = %s", (id_no,))
                if cursor.fetchone()[0] > 0:
                    return True

                # Check in students
                cursor.execute("SELECT COUNT(*) FROM students WHERE id_no = %s", (id_no,))
                if cursor.fetchone()[0] > 0:
                    return True

                # Check in appraised_curriculum
                cursor.execute("SELECT COUNT(*) FROM appraised_curriculum WHERE id_no = %s", (id_no,))
                if cursor.fetchone()[0] > 0:
                    return True

            return False

        except psycopg2.Error as err:
            print(f"Database error checking student existence: {err}")
            if self.conn:
                self.conn.rollback()
            return False
        except Exception as e:
            print(f"Unexpected error checking student existence: {e}")
            return False

    def verify_record_exists(self, id_no, course_no):
        """
        Verify if a record exists in appraised_curriculum.

        Args:
            id_no (str): Student ID number
            course_no (str): Course number

        Returns:
            bool: True if record exists, False otherwise
        """
        try:
            # Ensure the connection is still alive
            if not self.conn or self.conn.closed != 0:
                self.conn, self.cursor = self.get_db_connection()

            with self.conn.cursor() as cursor:
                query = """
                    SELECT 1
                    FROM appraised_curriculum
                    WHERE id_no = %s AND course_no = %s
                    LIMIT 1
                """
                cursor.execute(query, (id_no, course_no))
                return cursor.fetchone() is not None

        except psycopg2.Error as err:
            print(f"Database error verifying record existence: {err}")
            if self.conn:
                self.conn.rollback()
            return False
        except Exception as e:
            print(f"Unexpected error verifying record existence: {e}")
            return False

    def update_appraised_grades(self, grades_df):
        """Update only the grades column in appraised_curriculum for existing records."""
        try:
            # Ensure the connection is alive
            if not self.conn or self.conn.closed != 0:
                self.conn, self.cursor = self.get_db_connection()

            with self.conn.cursor() as cursor:
                for _, row in grades_df.iterrows():
                    update_query = """
                        UPDATE appraised_curriculum
                        SET grades = %s
                        WHERE id_no = %s
                        AND course_no = %s
                        AND year_level = %s
                        AND school_year = %s
                        AND (grades IS NULL OR grades = '' OR grades = 'INC')
                    """

                    cursor.execute(update_query,(row['grade'], row['id_no'], row['course_no'],row['year_level'], row['school_year']))

                    if cursor.rowcount == 0:
                        print(f"No update for student {row['id_no']}, " f"course {row['course_no']} — record missing or already has grade.")
                    else:
                        print(f"Updated grade for student {row['id_no']} " f"({row['course_no']}) to {row['grade']}")

                self.conn.commit()
                return True

        except psycopg2.Error as err:
            print(f"❌ Database error while updating grades: {err}")
            if self.conn:
                self.conn.rollback()
            return False

        except Exception as e:
            print(f"❌ Unexpected error updating appraised grades: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def save_manual_grades(self, grading_data, year_level, school_year):
        """Save manually entered grades for a given year and semester into PostgreSQL. Automatically creates the semester table if it doesn't exist."""
        try:
            # Map year-levels to PostgreSQL table names
            year_mapping = {"1.1": "first_year_first_semester", "1.2": "first_year_second_semester",
                "2.1": "second_year_first_semester", "2.2": "second_year_second_semester",
                "3.1": "third_year_first_semester", "3.2": "third_year_second_semester",
                "4.1": "fourth_year_first_semester", "4.2": "fourth_year_second_semester"}

            table_name = year_mapping.get(year_level)
            if not table_name:
                raise ValueError(f"Invalid year level: {year_level}")

            # Create table if it doesn’t exist (PostgreSQL syntax)
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id_no VARCHAR(255),
                last_name VARCHAR(100),
                first_name VARCHAR(100),
                middle_name VARCHAR(100),
                school_year VARCHAR(20),
                course_no VARCHAR(30),
                grades NUMERIC(5,2),
                PRIMARY KEY (id_no, course_no, school_year))
            """
            self.cursor.execute(create_table_query)

            # Valid grade list
            valid_grades = {1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 5.0}

            # Process and insert each record
            for _, row in grading_data.iterrows():
                try:
                    course_no = str(row['Course No.']).strip()
                    # Validate grade
                    try:
                        grade = float(row['Grade'])
                        if grade not in valid_grades:
                            raise ValueError(
                                f"Invalid grade {grade} for course {course_no}. "
                                f"Valid grades are: {', '.join(map(str, valid_grades))}"
                            )
                    except ValueError as ve:
                        if "could not convert" in str(ve):
                            raise ValueError(f"Invalid grade format for course {course_no}: {row['Grade']}")
                        raise ve

                    # Check if record already exists
                    check_query = f"""
                        SELECT COUNT(*) 
                        FROM {table_name}
                        WHERE id_no = %s AND course_no = %s AND school_year = %s
                    """
                    self.cursor.execute(check_query, (row['id_no'].strip(), course_no, school_year.strip()))
                    exists = self.cursor.fetchone()[0]

                    if exists:
                        messagebox.showwarning("Duplicate Entry", f"Grade for student {row['id_no']} in course {course_no} for {school_year} already exists.")
                        continue

                    # Insert new record
                    insert_query = f"""
                        INSERT INTO {table_name} (
                            id_no, last_name, first_name, middle_name, school_year, course_no, grades)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (row['id_no'].strip(),row['Last Name'].strip(),row['First Name'].strip(), row['Middle Name'].strip(),school_year.strip(),course_no, grade)
                    self.cursor.execute(insert_query, values)

                except ValueError as ve:
                    messagebox.showerror("Validation Error", str(ve))
                    self.conn.rollback()
                    return False

            self.conn.commit()
            return True

        except psycopg2.Error as err:
            messagebox.showerror("Database Error", f"Error saving grades: {err}")
            self.conn.rollback()
            return False

        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")
            self.conn.rollback()
            return False

    def check_student_source(self, id_no):
        """
        Check if a student exists in student_information or appraised_curriculum.
        Args:
            id_no (str): Student ID number to check.
        Returns:
            str:  'appraised'  → Found in appraised_curriculum
                'regular'    → Found in student_information
                'not_found'  → Not found in either"""
        try:
            # Ensure connection is active
            if self.conn.closed:
                self.conn = psycopg2.connect(host=self.host,user=self.user,password=self.password,dbname=self.database,port=self.port)
            cursor = self.conn.cursor()

            # Check in appraised_curriculum
            query_appraised = """
                SELECT COUNT(*) 
                FROM appraised_curriculum 
                WHERE id_no = %s
            """
            cursor.execute(query_appraised, (id_no,))
            appraised_count = cursor.fetchone()[0]

            if appraised_count > 0:
                cursor.close()
                return 'appraised'

            # Check in student_information
            query_student_info = """
                SELECT COUNT(*) 
                FROM student_information 
                WHERE id_no = %s
            """
            cursor.execute(query_student_info, (id_no,))
            student_info_count = cursor.fetchone()[0]

            cursor.close()
            if student_info_count > 0:
                return 'regular'
            return 'not_found'

        except psycopg2.Error as err:
            print(f"[Database Error] Error checking student source: {err}")
            return 'not_found'

        except Exception as e:
            print(f"[Error] Unexpected error checking student source: {e}")
            return 'not_found'

    def get_student_info(self):
        """Fetch all student information from the student_information table."""
        try:
            # Ensure connection is active
            if not hasattr(self, 'conn') or self.conn.closed != 0:
                self.conn, self.cursor = self.get_db_connection()

            query = """
                SELECT 
                    id_no,
                    last_name,
                    first_name,
                    middle_name,
                    yr,
                    age,
                    sex,
                    email_address,
                    shs,
                    address
                FROM student_information
                ORDER BY last_name, first_name, middle_name
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()

            # Define column names (must match query order)
            columns = ['id_no', 'last_name', 'first_name', 'middle_name','yr', 'age', 'sex', 'email_address', 'shs', 'address']

            # Convert result list of tuples → DataFrame
            return pd.DataFrame(result, columns=columns)

        except psycopg2.Error as err:
            messagebox.showerror("Database Error", f"Error getting student information: {err}")
            return pd.DataFrame()

        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")
            return pd.DataFrame()

    def get_missing_grades(self, year_level):
        """Fetch students missing grades for all subjects in a given year level. Returns a DataFrame with id_no, STUDENT_NAME, COURSE_NO.
        """
        try:
            # Map year_level string to semester table name
            table_mapping = {"1.1": "first_year_first_semester", "1.2": "first_year_second_semester",
                "2.1": "second_year_first_semester", "2.2": "second_year_second_semester",
                "3.1": "third_year_first_semester", "3.2": "third_year_second_semester",
                "4.1": "fourth_year_first_semester", "4.2": "fourth_year_second_semester"}

            table_name = table_mapping.get(year_level)
            if not table_name:
                raise ValueError(f"Invalid year level: {year_level}")

            # Ensure connection is alive
            if not hasattr(self, 'conn') or self.conn.closed != 0:
                self.conn, self.cursor = self.get_db_connection()

            # Step 1️⃣: Get all course codes for this year level
            year_decimal = float(year_level)
            self.cursor.execute("SELECT course_no FROM curriculum_regular WHERE year_level = %s", (year_decimal,))
            curriculum_courses = [row[0] for row in self.cursor.fetchall()]

            if not curriculum_courses:
                print(f"No curriculum courses found for year level {year_level}")
                return pd.DataFrame()

            # Step 2️⃣: Find students who do not have grades recorded for these courses
            # PostgreSQL uses || for string concatenation, not CONCAT()
            placeholders = ", ".join(["%s"] * len(curriculum_courses))
            query = f"""
                SELECT DISTINCT 
                    si.id_no,
                    si.last_name || ', ' || si.first_name ||
                    CASE 
                        WHEN si.middle_name IS NOT NULL AND si.middle_name <> '' 
                        THEN ' ' || si.middle_name 
                        ELSE '' 
                    END AS student_name,
                    cr.course_no
                FROM 
                    student_information si
                CROSS JOIN curriculum_regular cr
                LEFT JOIN {table_name} g 
                    ON si.id_no = g.id_no 
                    AND cr.course_no = g.course_no 
                WHERE 
                    cr.year_level = %s
                    AND cr.course_no IN ({placeholders})
                    AND (g.grades IS NULL OR g.grades = '')
                ORDER BY 
                    si.last_name, si.first_name, si.middle_name, cr.course_no
            """

            params = (year_decimal, *curriculum_courses)
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()

            columns = ['id_no', 'student_name', 'course_no']
            df = pd.DataFrame(results, columns=columns)

            return df

        except psycopg2.Error as err:
            print(f"❌ Database Error: {err}")
            return pd.DataFrame()

        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
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
            # Year/Semester → Table mapping
            year_mapping = {"1st Year": "first_year", "2nd Year": "second_year", "3rd Year": "third_year", "4th Year": "fourth_year"}
            semester_mapping = {"1st Semester": "first_semester", "2nd Semester": "second_semester"}

            table_name = f"{year_mapping.get(year)}_{semester_mapping.get(semester)}"
            if not table_name:
                print(f"Invalid year/semester combination: {year}, {semester}")
                return False

            # Ensure connection is active
            if not hasattr(self, 'conn') or self.conn.closed != 0:
                self.conn, self.cursor = self.get_db_connection()

            query = f"""
                SELECT COUNT(*) 
                FROM {table_name}
                WHERE id_no = %s 
                AND course_no = %s 
                AND school_year = %s
                AND grades IS NOT NULL
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query, (student_id, course_no, school_year))
                count = cursor.fetchone()[0]
                return count > 0

        except psycopg2.Error as err:
            print(f"❌ Database Error in check_existing_grade: {err}")
            return False

        except Exception as e:
            print(f"❌ Unexpected Error in check_existing_grade: {e}")
            return False

    def get_next_user_id(self):
        """
        Get the next user ID from the admin_management table.
        For PostgreSQL, the SERIAL column automatically increments,
        but this function provides the next value for display or manual insert.
        """
        try:
            # Ensure connection is active
            if not hasattr(self, 'conn') or self.conn.closed != 0:
                self.conn, self.cursor = self.get_db_connection()

            # PostgreSQL way to get the next sequence value
            query = """ 
                SELECT COALESCE(MAX(id), 0) + 1 AS next_id 
                FROM admin_management 
            """
            self.cursor.execute(query)
            result = self.cursor.fetchone()

            # Return the next available ID (ensure it's at least 1)
            next_id = result[0] if result and result[0] is not None else 1
            print(f"Next user ID: {next_id}")
            return next_id

        except psycopg2.Error as err:
            print(f"❌ Database Error in get_next_user_id: {err}")
            # Fallback to 1 if there's an error
            return 1
        except Exception as e:
            print(f"❌ Unexpected Error in get_next_user_id: {e}")
            # Fallback to 1 if there's an unexpected error
            return 1

    def save_user(self, id, email, hashed_password, salt, username):
        """
        Save a new user into the admin_management table.
        Includes full validation and PostgreSQL-safe execution.
        """
        try:
            # --- Input validation ---
            if not all([id, email, hashed_password, salt, username]):
                raise ValueError("All fields are required")

            # Email format validation
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                raise ValueError("Invalid email format")

            # Username validation
            if len(username.strip()) < 3:
                raise ValueError("Username must be at least 3 characters long")

            # Ensure connection is active - recreate if needed
            if not hasattr(self, 'conn') or self.conn is None or self.conn.closed != 0:
                print("Re-establishing database connection...")
                self.conn, self.cursor = self.get_db_connection()

            # --- Check if email already exists ---
            check_query_email = "SELECT 1 FROM admin_management WHERE email = %s"
            self.cursor.execute(check_query_email, (email,))
            if self.cursor.fetchone():
                raise ValueError("Email already registered")

            # --- Check if username already exists ---
            check_query_username = "SELECT 1 FROM admin_management WHERE username = %s"
            self.cursor.execute(check_query_username, (username,))
            if self.cursor.fetchone():
                raise ValueError("Username already taken")

            # --- Insert new user ---
            insert_query = """
                INSERT INTO admin_management 
                    (id, username, email, password, salt, role, is_active, registration_date, last_login)
                VALUES 
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            current_time = datetime.now()

            self.cursor.execute(
                insert_query,(id, username.strip(), email.strip(), hashed_password, salt,
                    'user',               # Default role
                    True,                 # Default active (changed from False to True)
                    current_time,         # Registration date
                    current_time          # Last login initialized to now
                ))
            self.conn.commit()
            print(f"✅ New user registered: {username} ({email}) with ID {id}")
            return True

        except psycopg2.Error as db_error:
            if hasattr(self, 'conn') and self.conn and self.conn.closed == 0:
                self.conn.rollback()
            print(f"❌ Database Error in save_user: {db_error}")
            return False
        except ValueError as ve:
            if hasattr(self, 'conn') and self.conn and self.conn.closed == 0:
                self.conn.rollback()
            print(f"⚠️ Validation Error in save_user: {ve}")
            return False
        except Exception as e:
            if hasattr(self, 'conn') and self.conn and self.conn.closed == 0:
                self.conn.rollback()
            print(f"❌ Unexpected Error in save_user: {e}")
            return False

    def create_users_table(self):
        """
        Create the admin_management table in PostgreSQL if it doesn't already exist.
        """
        create_table_query = """
        CREATE TABLE IF NOT EXISTS admin_management (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            salt VARCHAR(255) NOT NULL,
            role VARCHAR(50) DEFAULT 'user',
            is_active BOOLEAN DEFAULT TRUE,
            last_login TIMESTAMP,
            registration_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        try:
            # Ensure connection is active
            if not hasattr(self, 'conn') or self.conn.closed != 0:
                self.conn, self.cursor = self.get_db_connection()

            with self.conn.cursor() as cursor:
                cursor.execute(create_table_query)
                self.conn.commit()

            print("✅ admin_management table ensured successfully.")
            return True

        except psycopg2.Error as e:
            print(f"❌ Database error creating admin_management table: {e}")
            if hasattr(self, 'conn') and self.conn and self.conn.closed == 0:
                self.conn.rollback()
            return False
        except Exception as e:
            print(f"❌ Unexpected error creating admin_management table: {e}")
            if hasattr(self, 'conn') and self.conn and self.conn.closed == 0:
                self.conn.rollback()
            return False
        
    def get_user_by_email(self, email):
        """
        Retrieve a user record by email from the admin_management table.
        Returns a dictionary if found, otherwise None.
        """
        try:
            if not email:
                return None

            # Ensure connection is active
            if not hasattr(self, 'conn') or self.conn.closed != 0:
                self.conn, self.cursor = self.get_db_connection()

            query = """
                SELECT 
                    id, username, email, password, salt, role, is_active, last_login
                FROM admin_management 
                WHERE email = %s
            """

            with self.conn.cursor() as cursor:
                cursor.execute(query, (email,))
                user = cursor.fetchone()

            if user:
                return {'id': user[0], 'username': user[1], 'email': user[2], 'password': user[3], 'salt': user[4], 'role': user[5], 'is_active': user[6], 'last_login': user[7]}
            return None

        except psycopg2.Error as db_error:
            print(f"❌ Database Error in get_user_by_email: {db_error}")
            return None

        except Exception as e:
            print(f"❌ Unexpected Error in get_user_by_email: {e}")
            return None
        
    def __del__(self):
        """Cleanup method for PostgreSQL database connection."""
        try:
            # Only close if explicitly marked for cleanup
            if getattr(self, '_closing', False):
                # Check if connection exists and is open
                if hasattr(self, 'conn') and self.conn and self.conn.closed == 0:
                    if hasattr(self, 'cursor') and self.cursor:
                        self.cursor.close()
                    self.conn.close()
                    print("✅ PostgreSQL connection explicitly closed.")
        except Exception as e:
            print(f"⚠️ Error while closing PostgreSQL connection: {e}")

    def close(self):
        """Method to explicitly close the PostgreSQL connection when needed"""
        self._closing = True
        try:
            # psycopg2 / psycopg connections do not have is_connected()
            if self.conn is not None and not self.conn.closed:
                self.cursor.close()
                self.conn.close()
                print("PostgreSQL Connection explicitly closed.")
        except Exception as e:
            print("PostgreSQL Connection Error",e)

    def create_templates_table(self):
        """
        Creates the 'templates' table if it does not already exist (PostgreSQL version).
        """
        query = """ CREATE TABLE IF NOT EXISTS templates (
            id SERIAL PRIMARY KEY,
            file_name VARCHAR(255) NOT NULL,
            file_data TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"""
        try:
            self.cursor.execute(query)
            self.conn.commit()
            print("Database Templates Table", "Table 'templates' created or already exists.")
        except Exception as e:
            print("Database Templates Table Error",e)
            self.conn.rollback()

    def save_templates_to_database(self, file_paths):
        """
        Saves multiple CSV files to the 'templates' table in PostgreSQL.
        """
        try:
            for file_path in file_paths:
                # Extract file name
                file_name = os.path.basename(file_path)

                # Read the CSV file
                with open(file_path, 'r', encoding='utf-8') as file:
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
            # Optional: do not close connection here if you plan to reuse it
            if self.cursor:
                self.cursor.close()
            if self.conn and not self.conn.closed:
                self.conn.close()

    def preload_grade_data(self):
        """Preload grade data for all semesters"""
        try:
            # Get a fresh database connection
            conn, cursor = self.get_db_connection()
            grade_data = {}
            semesters = ["1.1", "1.2", "2.1", "2.2","3.1", "3.2", "4.1", "4.2"]

            for semester in semesters:
                # Make sure get_grades_by_semester returns list/dict compatible with PostgreSQL queries
                grade_data[semester] = self.get_grades_by_semester(semester=semester, school_year="2023-2024",
                    student_id="All") # adjust if your PostgreSQL query needs NULL or '%' instead of 'All'
            # Close the connection when done
            cursor.close()
            conn.close()
            return grade_data

        except Exception as e:
            print("Database Error Preload of Grade",e)
            return {}
        
    def get_grades_by_semester(self, year_level, school_year, sex_filter):
        try:
            table_mapping = {"1.1": "first_year_first_semester", "1.2": "first_year_second_semester",
                "2.1": "second_year_first_semester", "2.2": "second_year_second_semester",
                "3.1": "third_year_first_semester", "3.2": "third_year_second_semester",
                "4.1": "fourth_year_first_semester", "4.2": "fourth_year_second_semester"}

            table_name = table_mapping.get(year_level)
            if not table_name:
                raise ValueError(f"Invalid year level: {year_level}")

            # Get course columns for this semester
            columns_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s
            AND column_name NOT IN ('id_no', 'last_name', 'first_name', 'middle_name', 'school_year')
            ORDER BY ordinal_position
            """
            self.cursor.execute(columns_query, (table_name,))
            course_columns = [row[0] for row in self.cursor.fetchall()]

            # Build dynamic SELECT statement
            grades_query = f"""
                SELECT 
                    si.id_no,
                    si.sex,
                    si.last_name || ', ' || si.first_name || 
                    CASE 
                        WHEN si.middle_name IS NOT NULL AND si.middle_name != '' 
                        THEN ' ' || si.middle_name
                        ELSE ''
                    END AS student_name,
                    {', '.join(f'g.{col}' for col in course_columns)}
                FROM 
                    student_information si
                    LEFT JOIN {table_name} g ON si.id_no = g.id_no
                WHERE 
                    g.school_year = %s
                    AND si.sex = %s
                ORDER BY 
                    si.last_name, si.first_name, si.middle_name
                """

            self.cursor.execute(grades_query, (school_year, sex_filter))

            # Convert results to pandas DataFrame
            df = pd.DataFrame(self.cursor.fetchall(), columns=['id_no', 'SEX', 'Student_Name'] + course_columns)

            return {'columns': df.columns.tolist(), 'data': df.to_dict('records')}

        except psycopg2.Error as err:
            print("Database Error",err)
            print(f"Database Error: {err}")
            raise
        except Exception as e:
            print(f"Error loading grades: {e}")
            raise

    def get_available_school_years(self, year_level):
        """
        Get available school years for a specific semester (PostgreSQL version)
        """
        try:
            table_mapping = {"1.1": "first_year_first_semester", "1.2": "first_year_second_semester",
                "2.1": "second_year_first_semester", "2.2": "second_year_second_semester",
                "3.1": "third_year_first_semester", "3.2": "third_year_second_semester",
                "4.1": "fourth_year_first_semester", "4.2": "fourth_year_second_semester"}

            table_name = table_mapping.get(year_level)
            if not table_name:
                raise ValueError(f"Invalid year level: {year_level}")

            # Get available school years for this semester
            query = f"""
            SELECT DISTINCT school_year
            FROM {table_name}
            WHERE school_year IS NOT NULL
            ORDER BY school_year DESC
            """
            self.cursor.execute(query)
            school_years = [year[0] for year in self.cursor.fetchall()]

            return school_years if school_years else ["No data available"]

        except psycopg2.Error as err:
            print(f"Database Error: {err}")
            raise
        except Exception as e:
            print(f"Error getting school years: {e}")
            raise

    def update_grade(self, student_id, course_no, new_grade, year_level, school_year):
        """Update a student's grade in the PostgreSQL database"""
        try:
            table_mapping = {"1.1": "first_year_first_semester","1.2": "first_year_second_semester",
                "2.1": "second_year_first_semester","2.2": "second_year_second_semester",
                "3.1": "third_year_first_semester","3.2": "third_year_second_semester",
                "4.1": "fourth_year_first_semester","4.2": "fourth_year_second_semester"}

            table_name = table_mapping.get(year_level)
            if not table_name:
                raise ValueError(f"Invalid year level: {year_level}")

            # Update the grade using double quotes for dynamic column
            update_query = f"""
            UPDATE {table_name}
            SET {course_no} = %s
            WHERE id_no = %s AND school_year = %s
            """

            self.cursor.execute(update_query, (new_grade, student_id, school_year))
            self.conn.commit()
            return True

        except psycopg2.Error as err:
            print(f"Database Error: {err}")
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False

    def get_all_users(self):
        """Fetch all users with their status and last login (PostgreSQL version)"""
        try:
            query = """
                SELECT id, username, role, last_login, is_active
                FROM admin_management
                ORDER BY username
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except psycopg2.Error as err:
            print(f"Database Error fetching users: {err}")
            return []
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []

    def update_user_status(self, user_id, new_status):
        """Update user's active status in PostgreSQL"""
        cursor = None
        try:
            cursor = self.conn.cursor()

            # Update user's status and last_updated timestamp
            query = """
                UPDATE admin_management
                SET is_active = %s,
                    last_updated = NOW()
                WHERE id = %s
                RETURNING id
            """
            cursor.execute(query, (new_status, user_id))
            
            updated_user = cursor.fetchone()
            if not updated_user:
                print(f"No user found with ID {user_id}")
                return False

            self.conn.commit()
            return True

        except psycopg2.Error as err:
            print(f"Database Error updating user status: {err}")
            self.conn.rollback()
            return False
        except Exception as e:
            print(f"Error updating user status: {e}")
            self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

     #this is for the student grades.py           
    
    def register_student(self, student_id, last_name, middle_name, first_name, password):
        """Register a new student in PostgreSQL"""
        try:
            query = """
                INSERT INTO studgrade_pass (id_no, last_name, middle_name, first_name, password)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (student_id, last_name, middle_name, first_name, password))
            self.conn.commit()
            print(f"Student {student_id} registered successfully.")
        except psycopg2.Error as err:
            print(f"Database Error registering student: {err}")
            self.conn.rollback()
        except Exception as e:
            print(f"Error registering student: {e}")
            self.conn.rollback()

    def get_student(self, student_id):
        """Fetch a single student record from PostgreSQL"""
        try:
            query = "SELECT * FROM studgrade_pass WHERE id_no = %s"
            self.cursor.execute(query, (student_id,))
            return self.cursor.fetchone()
        except psycopg2.Error as err:
            print(f"Database Error fetching student: {err}")
            return None
        except Exception as e:
            print(f"Error fetching student: {e}")
            return None


    def get_grades(self, student_id):
        """
        Get grades for a student across all semesters in PostgreSQL.

        Args:
            student_id (str): The student's ID number

        Returns:
            list: List of tuples containing (semester_key, course_no, grade)
        """
        table_names = {'first_year_first_semester': '1.1', 'first_year_second_semester': '1.2',
            'second_year_first_semester': '2.1', 'second_year_second_semester': '2.2',
            'third_year_first_semester': '3.1','third_year_second_semester': '3.2',
            'fourth_year_first_semester': '4.1', 'fourth_year_second_semester': '4.2'}
        grades = []

        for table, sem_key in table_names.items():
            cursor = None
            try:
                # Use RealDictCursor to get dictionary-like rows
                cursor = self.conn.cursor(cursor_factory=RealDictCursor)

                query = f"""
                    SELECT course_no, grades
                    FROM {table}
                    WHERE id_no = %s
                    ORDER BY course_no
                """
                cursor.execute(query, (student_id,))
                results = cursor.fetchall()

                if results:
                    for row in results:
                        course = row.get('course_no')
                        grade = row.get('grades')
                        if course and grade:
                            grades.append((sem_key, course, grade))
                else:
                    print(f"No grades found in {table} for student {student_id}")

            except psycopg2.Error as e:
                print(f"Error processing table {table}: {e}")
            finally:
                if cursor:
                    cursor.close()

        return grades

    def school_year(self, student_id, semester):
        """
        Get the school year for a student in a specific semester (PostgreSQL version)
        """
        table_names = {'1.1': 'first_year_first_semester', '1.2': 'first_year_second_semester',
            '2.1': 'second_year_first_semester', '2.2': 'second_year_second_semester',
            '3.1': 'third_year_first_semester', '3.2': 'third_year_second_semester',
            '4.1': 'fourth_year_first_semester', '4.2': 'fourth_year_second_semester'}
        table = table_names.get(semester)
        if not table:
            print(f"Invalid semester identifier: {semester}")  # Debug print
            return "N/A"

        cursor = None
        try:
            cursor = self.conn.cursor()
            query = f"SELECT school_year FROM {table} WHERE id_no = %s"
            print(f"Executing query: {query} with student_id: {student_id}")  # Debug print
            cursor.execute(query, (student_id,))
            result = cursor.fetchone()
            print(f"Query result: {result}")  # Debug print
            return result[0] if result else "N/A"

        except psycopg2.Error as e:
            print(f"Error fetching school year for {table}: {e}")
            return "N/A"

        finally:
            if cursor:
                cursor.close()

    def get_descriptive_title(self, course_no):
        """
        Get the descriptive title of a course (PostgreSQL version)
        """
        cursor = None
        try:
            cursor = self.conn.cursor()
            query = "SELECT descriptive_title FROM curriculum_regular WHERE course_no = %s"
            cursor.execute(query, (course_no,))
            result = cursor.fetchone()
            return result[0] if result else "Unknown"

        except psycopg2.Error as e:
            print(f"Database error fetching descriptive title for {course_no}: {e}")
            return "Unknown"
        except Exception as e:
            print(f"Error fetching descriptive title: {e}")
            return "Unknown"
        finally:
            if cursor:
                cursor.close()

    def get_students_list(self):
        """Retrieve list of students for display purposes (PostgreSQL version)"""
        cursor = None
        try:
            # Ensure connection is active
            if not self.conn or self.conn.closed:
                self.conn, _ = self.get_db_connection()

            cursor = self.conn.cursor()
            query = """
                SELECT 
                    id_no, 
                    last_name || ', ' || first_name || ' ' || COALESCE(middle_name, '') AS full_name,
                    yr,
                    enrolled_year
                FROM student_information
                ORDER BY last_name, first_name
            """
            cursor.execute(query)
            students = cursor.fetchall()

            return students

        except psycopg2.Error as e:
            print("Retrieval Error",e)
            return []
        finally:
            if cursor:
                cursor.close()

    def search_students(self, search_term):
        """Search students by ID, Name, or Year (PostgreSQL version)"""
        cursor = None
        try:
            # Ensure connection is active
            if not self.conn or self.conn.closed:
                self.conn, _ = self.get_db_connection()

            cursor = self.conn.cursor()
            search_query = """
                SELECT 
                    id_no, 
                    last_name || ', ' || first_name || ' ' || COALESCE(middle_name, '') AS full_name,
                    yr,
                    enrolled_year
                FROM student_information 
                WHERE id_no LIKE %s OR 
                    (last_name || ' ' || first_name || ' ' || COALESCE(middle_name, '')) LIKE %s OR
                    yr = %s
                ORDER BY last_name, first_name
            """

            # Prepare search parameters
            search_param = f"%{search_term}%"

            # Convert search term to year if possible
            try:
                year_param = int(search_term)
            except ValueError:
                year_param = 0

            cursor.execute(search_query, (search_param, search_param, year_param))
            students = cursor.fetchall()

            return students

        except psycopg2.Error as e:
            print("Search Error",e)
            return []
        except Exception as e:
            print("Search Error",e)
            return []
        finally:
            if cursor:
                cursor.close()

    def get_students_list(self):
        """
        Retrieve list of students for display purposes, filtered by YR = 4, 
        and include SCHOOL_YEAR (PostgreSQL version)
        """
        cursor = None
        try:
            # Ensure connection is active
            if not self.conn or self.conn.closed:
                self.conn, _ = self.get_db_connection()

            cursor = self.conn.cursor()
            query = """
                SELECT 
                    id_no, 
                    last_name || ', ' || first_name || ' ' || COALESCE(middle_name, '') AS full_name,
                    yr,
                    enrolled_year
                FROM student_information
                WHERE yr = 4
                ORDER BY last_name, first_name
            """
            cursor.execute(query)
            students = cursor.fetchall()

            # Convert tuple results to dictionary
            if students:
                column_names = ['id_no', 'full_name', 'yr', 'enrolled_year']
                students_list = [dict(zip(column_names, student)) for student in students]
            else:
                return []

            # Add SCHOOL_YEAR to each student
            for student in students_list:
                id_no = student['id_no']
                student['school_year'] = self.get_school_year(id_no)

            return students_list

        except psycopg2.Error as e:
            print("Retrieval Error")
            return []
        except Exception as e:
            print("Retrieval Error",e)
            return []
        finally:
            if cursor:
                cursor.close()

    def get_school_year(self, id_no):
        """
        Retrieve the school_year for a specific student from the fourth_year_second_semester table (PostgreSQL version).
        """
        cursor = None
        try:
            # Ensure connection is active
            if not self.conn or self.conn.closed:
                self.conn, _ = self.get_db_connection()

            cursor = self.conn.cursor()
            query = """
                SELECT school_year
                FROM fourth_year_second_semester
                WHERE id_no = %s
            """
            cursor.execute(query, (id_no,))
            result = cursor.fetchone()

            return result[0] if result else "N/A"

        except psycopg2.Error as e:
            print(e)
            return "N/A"
        except Exception as e:
            print(e)
            return "N/A"
        finally:
            if cursor:
                cursor.close()

    def search_students(self, search_term):
        """
        Search students by ID, Name, or Year (PostgreSQL version)
        """
        cursor = None
        try:
            # Ensure connection is active
            if not self.conn or self.conn.closed:
                self.conn, _ = self.get_db_connection()

            cursor = self.conn.cursor()
            search_query = """
                SELECT 
                    id_no, 
                    last_name || ', ' || first_name || ' ' || COALESCE(middle_name, '') AS full_name,
                    yr,
                    enrolled_year
                FROM student_information 
                WHERE id_no LIKE %s OR 
                    (last_name || ' ' || first_name || ' ' || COALESCE(middle_name, '')) LIKE %s OR
                    yr = %s
                ORDER BY last_name, first_name
            """

            search_param = f"%{search_term}%"

            # Convert search term to year if possible
            try:
                year_param = int(search_term)
            except ValueError:
                year_param = 0

            cursor.execute(search_query, (search_param, search_param, year_param))
            students = cursor.fetchall()

            # Convert tuple results to dictionary
            if students:
                column_names = ['id_no', 'full_name', 'yr', 'enrolled_year']
                return [dict(zip(column_names, student)) for student in students]

            return []

        except psycopg2.Error as e:
            print(e)
            return []
        except Exception as e:
            print(e)
            return []
        finally:
            if cursor:
                cursor.close()

    def get_course_data(self, student_id):
        """
        Retrieve all course grades for a student across all semesters (PostgreSQL version)
        """
        course_data = {}
        cursor = None

        try:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            table_names = ['first_year_first_semester', 'first_year_second_semester',
                'second_year_first_semester', 'second_year_second_semester',
                'third_year_first_semester','third_year_second_semester',
                'fourth_year_first_semester', 'fourth_year_second_semester']

            for table_name in table_names:
                # Get column names excluding meta columns
                columns_query = """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = %s
                    AND column_name NOT IN ('id_no', 'last_name', 'first_name', 'middle_name', 'school_year', 'yr')
                    ORDER BY ordinal_position
                """
                cursor.execute(columns_query, (table_name,))
                course_columns = [col['column_name'] for col in cursor.fetchall()]

                if not course_columns:
                    continue

                # Escape column names for PostgreSQL
                select_columns = ', '.join(course_columns)

                grade_query = f"""
                    SELECT id_no, {select_columns}
                    FROM {table_name}
                    WHERE id_no = %s
                """
                cursor.execute(grade_query, (student_id,))
                results = cursor.fetchall()

                table_grades = []
                for row in results:
                    for col in course_columns:
                        grade = row.get(col)
                        if grade is not None and str(grade).strip().upper() not in ['', 'N/A', '0', 'NULL']:
                            table_grades.append([col, grade])

                if table_grades:
                    course_data[table_name] = table_grades

            # Remove duplicate entries per table (just in case)
            unique_course_data = {}
            for table, grades in course_data.items():
                seen_cols = set()
                unique_grades = []
                for col, grade in grades:
                    if col not in seen_cols:
                        unique_grades.append([col, grade])
                        seen_cols.add(col)
                unique_course_data[table] = unique_grades

            # Optional debugging
            print("Final Course Data:")
            for table, grades in unique_course_data.items():
                print(f"{table}: {grades}")

            return unique_course_data

        except psycopg2.Error as err:
            print(f"Database error: {err}")
            return None
        finally:
            if cursor:
                cursor.close()
             
    def get_course_columns(self, table_name):
        """Retrieve the column names for the specified course table (PostgreSQL version)."""
        cursor = None
        try:
            # Ensure connection is active
            if not self.conn or self.conn.closed:
                self.conn, _ = self.get_db_connection()

            cursor = self.conn.cursor()
            query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """
            cursor.execute(query, (table_name,))
            columns = [row[0] for row in cursor.fetchall()]
            return columns

        except psycopg2.Error as err:
            print(f"Error retrieving columns for table {table_name}: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
           
    def get_curriculum_regular(self):
        """
        Retrieve all records from the curriculum_regular table (PostgreSQL version).
        Returns:
            tuple: (column_names, results)
        """
        cursor = None
        try:
            # Ensure connection is active
            if not self.conn or self.conn.closed:
                self.conn, _ = self.get_db_connection()

            cursor = self.conn.cursor()
            query = """
                SELECT 
                    course_no, 
                    descriptive_title, 
                    year_level, 
                    units, 
                    lec, 
                    lab, 
                    prerequisite, 
                    grades
                FROM curriculum_regular
            """
            cursor.execute(query)
            results = cursor.fetchall()

            if not results:
                logging.warning("No curriculum data found")
                return [], []

            # Extract column names
            column_names = [desc[0] for desc in cursor.description]

            logging.info(f"Retrieved {len(results)} curriculum records")
            return column_names, results

        except psycopg2.Error as err:
            logging.error(f"PostgreSQL Database error: {err}")
            print(err)
            return [], []
        except Exception as e:
            logging.error(f"Unexpected error retrieving curriculum: {e}")
            print(err)
            return [], []
        finally:
            if cursor:
                cursor.close()

    def get_unenrolled_students(self, year_level, current_sy):
        """
        Fetch students of a given year level who are not yet enrolled in both first and second semester.
        """
        year_word_map = {1: "first", 2: "second", 3: "third", 4: "fourth",
                        "1": "first", "2": "second", "3": "third", "4": "fourth"}
        year_word = year_word_map.get(year_level)
        if not year_word:
            print(f"Invalid year_level: {year_level}")
            return []

        cursor = None
        try:
            if not self.conn or self.conn.closed:
                self.conn, _ = self.get_db_connection()

            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            year_level_str = str(year_level)

            # Query with lowercase column names (no aliases needed)
            query = f"""
                SELECT s.id_no, s.last_name, s.first_name, s.middle_name, s.yr, s.enrolled_year
                FROM student_information s
                LEFT JOIN "{year_word}_year_first_semester" fyfs
                    ON s.id_no = fyfs.id_no AND fyfs.school_year = %s
                LEFT JOIN "{year_word}_year_second_semester" fyss
                    ON s.id_no = fyss.id_no AND fyss.school_year = %s
                WHERE s.yr = %s
                AND fyfs.id_no IS NULL AND fyss.id_no IS NULL
                ORDER BY s.last_name, s.first_name
            """

            print(f"Executing query for {year_level}-year students")
            print(f"Parameters: {current_sy}, {current_sy}, {year_level_str}")

            cursor.execute(query, (current_sy, current_sy, year_level_str))
            students = cursor.fetchall()

            print(f"Fetched {len(students)} students for year {year_level}")
            if students:
                print(f"Available columns in result: {list(students[0].keys())}")

            return self.format_students(students) if students else []

        except psycopg2.Error as err:
            print(f"{year_level}-year Database error: {err}")
            if self.conn and self.conn.closed == 0:
                self.conn.rollback()
            return []
        finally:
            if cursor:
                cursor.close()
                
    def get_next_semester(self, id_no):
        """
        Determine the next semester for a student based on completed grades.
        
        Args:
            id_no (str): Student ID.
            
        Returns:
            str: Next semester key (e.g., '1.2', '2.1') or 'Graduate' if all semesters completed.
        """
        semester_order = ['1.1', '1.2', '2.1', '2.2', '3.1', '3.2', '4.1', '4.2']

        # Retrieve all completed grades across all semesters
        all_grades = self.check_all_tables_for_grades(id_no)  # Should return a dict: {semester_key: grades_list}

        # Determine which semesters have grades recorded
        completed_semesters = [sem for sem in semester_order if sem in all_grades and all_grades[sem]]

        # If none completed, start at 1.1
        if not completed_semesters:
            return semester_order[0]

        # Find last completed semester
        last_completed = completed_semesters[-1]

        # Return the next semester in order, or "Graduate" if all completed
        last_index = semester_order.index(last_completed)
        if last_index + 1 < len(semester_order):
            return semester_order[last_index + 1]
        else:
            return "Graduate"

    def format_students(self, students):
        """
        Format student data into a list of dictionaries,
        fetching the latest enrollment STATUS and next semester.
        """
        def semester_number_to_word(semester_key):
            """
            Convert semester part of a key like '1.1' or '2.2' to '1st' or '2nd'.
            """
            if '.' in semester_key:
                sem_part = semester_key.split('.')[1]
                return "1st" if sem_part == '1' else "2nd" if sem_part == '2' else semester_key
            return semester_key

        # Ensure connection is active
        if not self.conn or self.conn.closed:
            self.conn, self.cursor = self.get_db_connection()

        student_list = []

        # Use a local cursor for PostgreSQL dictionary access
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            for row in students:
                # FIX: Use only lowercase column names that match PostgreSQL result
                id_no = row.get('id_no')
                last_name = row.get('last_name')
                first_name = row.get('first_name')
                middle_name = row.get('middle_name') or ''
                year_level = row.get('yr')
                enrolled_year = row.get('enrolled_year')  # Also get enrolled_year if needed

                # Check if we have all required fields
                if not all([id_no, last_name, first_name, year_level]):
                    print(f"Skipping incomplete student record: {row}")
                    print(f"Available columns: {list(row.keys())}")
                    continue

                # Fetch the latest enrollment status
                cursor.execute("""
                    SELECT status
                    FROM enrollment
                    WHERE id_no = %s
                    ORDER BY enrollment_date DESC, enrollment_id DESC
                    LIMIT 1
                """, (id_no,))
                status_result = cursor.fetchone()
                status = status_result['status'] if status_result else "Not Enrolled"

                # Determine next semester
                next_semester = self.get_next_semester(id_no)

                student_list.append({
                    "id_no": id_no, 
                    "LAST_NAME": last_name, 
                    "FIRST_NAME": first_name, 
                    "MIDDLE_NAME": middle_name, 
                    "YEAR_LEVEL": year_level, 
                    "ENROLLMENT_STATUS": status, 
                    "SEMESTER": semester_number_to_word(next_semester)
                })

            return student_list

        except psycopg2.Error as e:
            print(f"Database error while formatting students: {e}")
            return []
        except Exception as e:
            print(f"Error while formatting students: {e}")
            return []
        finally:
            cursor.close()
            
    def create_enrollment_table(self):
        """
        Create the 'enrollment' table in PostgreSQL if it does not exist.
        """
        create_table_query = """
            CREATE TABLE IF NOT EXISTS enrollment (
                enrollment_id SERIAL PRIMARY KEY,
                id_no VARCHAR(100) NOT NULL,
                school_year VARCHAR(20) NOT NULL,
                enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'Not Enrolled' CHECK (status IN ('Not Enrolled', 'Enrolled', 'Stopped', 'Returnee', 'Dropped')),
                CONSTRAINT fk_student FOREIGN KEY (id_no) REFERENCES student_information(id_no) ON DELETE CASCADE,
                CONSTRAINT unique_enrollment UNIQUE (id_no, school_year)
            );
        """
        try:
            self.cursor.execute(create_table_query)
            self.conn.commit()
            print("Enrollment table created or already exists.")
        except psycopg2.Error as e:
            print(f"Error creating enrollment table: {e}")
            self.conn.rollback()

    def save_enrollment(self, id_no, school_year, status="Enrolled"):
        """
        Update the enrollment status for a student for a given school year.
        If the record does not exist, insert it.
        Warn on duplicate insert but continue processing.
        """
        try:
            # Ensure connection is active
            if not self.conn or self.conn.closed:
                self.conn, self.cursor = self.get_db_connection()

            # Update existing enrollment
            update_query = """
                UPDATE enrollment
                SET status = %s, enrollment_date = CURRENT_TIMESTAMP
                WHERE id_no = %s AND school_year = %s
            """
            self.cursor.execute(update_query, (status, id_no, school_year))

            if self.cursor.rowcount == 0:
                # Insert if no existing record
                insert_query = """
                    INSERT INTO enrollment (id_no, school_year, enrollment_date, status)
                    VALUES (%s, %s, CURRENT_TIMESTAMP, %s)
                    ON CONFLICT (id_no, school_year) DO NOTHING
                """
                self.cursor.execute(insert_query, (id_no, school_year, status))
                if self.cursor.rowcount == 0:
                    messagebox.showwarning("Duplicate", f"Enrollment already exists for {id_no} in {school_year}.")

            self.conn.commit()

        except psycopg2.Error as err:
            self.conn.rollback()
            messagebox.showerror("Database Error", f"Failed to save enrollment: {err}")
            raise

    def update_enrollment_status_bulk(self, id_list, year_level, school_year, batch_size=100):
        """
        Set STATUS to 'Enrolled' for all students in id_list for the given year_level and school_year.
        Handles batches to avoid large query issues.
        """
        if not id_list:
            return

        try:
            # Ensure connection is active
            if not self.conn or self.conn.closed:
                self.conn, self.cursor = self.get_db_connection()

            for i in range(0, len(id_list), batch_size):
                batch = id_list[i:i + batch_size]
                placeholders = ','.join(['%s'] * len(batch))

                update_query = f"""
                    UPDATE enrollment
                    SET status = 'Enrolled', enrollment_date = CURRENT_TIMESTAMP
                    WHERE id_no IN ({placeholders}) AND school_year = %s
                """
                self.cursor.execute(update_query, (*batch, school_year))

            self.conn.commit()

        except psycopg2.Error as err:
            self.conn.rollback()
            print(f"Error updating enrollment status in bulk: {err}")
            raise
