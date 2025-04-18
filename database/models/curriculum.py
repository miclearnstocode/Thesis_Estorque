from tkinter import messagebox
import pandas as pd
import mysql.connector
import logging
import traceback


class CurriculumModel:
    def __init__(self, db_connection):
        self.db = db_connection

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
        """
        Retrieve the column names for the specified course table.
        """
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
