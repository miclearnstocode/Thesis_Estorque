import mysql.connector
import pandas as pd
from tkinter import messagebox

class GradeModel:
    def __init__(self, db_connection):
        self.db = db_connection
        
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
            self.execute_query_with_retry(create_table_query)

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

            # Prepare values for batch insertion
            values_list = []
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

                values_list.append(tuple(values))

            # Execute batch insert
            try:
                self.cursor.executemany(insert_query, values_list)
            except mysql.connector.Error as err:
                print(f"Error inserting rows: {err}")
                print(f"Values: {values_list}")
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
                