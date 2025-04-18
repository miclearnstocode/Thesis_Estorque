import mysql.connector
import pandas as pd
from tkinter import messagebox

class AppraisalModel:
    def __init__(self, db_connection):
        self.db = db_connection
    
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
                