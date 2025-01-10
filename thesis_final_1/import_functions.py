import csv
import json
import mysql.connector
from tkinter import filedialog, messagebox

def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',  # Update with actual password if necessary
        database='department'
    )
    cursor = conn.cursor()
    return conn, cursor

def close_db_connection(conn):
    conn.close()

# Save curriculum data
def save_data(treeviews):
    conn, cursor = get_db_connection()

    query = """INSERT INTO curriculum_regular (`Course No.`, `Descriptive Title`, `Year Level`, Units, Lab, Lec, Prerequisite, Grades)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""" 
    for tree in treeviews:
        for child in tree.get_children():
            row_data = tree.item(child, 'values')
            cursor.execute(query, row_data)

    conn.commit()
    cursor.close()
    conn.close()

    messagebox.showinfo("Success", "Data saved successfully!")

# Process and store grading data
def database_grade(grading_data_file, num_subjects, num_midterms):
    grading_table = []
    with open(grading_data_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            subjects = [row[f'Subject{i+1}'] for i in range(num_subjects)]
            midterms = [row[f'Midterm-{i+1}'] for i in range(num_midterms)]
            finals = [row[f'Final-{i+1}'] for i in range(num_midterms)]

            # Convert midterms and finals to integers, default to 0 if empty
            midterms = [int(midterm) if midterm else 0 for midterm in midterms]
            finals = [int(final) if final else 0 for final in finals]

            # Calculate totals and average
            total_score = sum([int(subject) if subject else 0 for subject in subjects]) + sum(midterms) + sum(finals)
            average = total_score / (num_subjects + num_midterms * 2)

            remark = 'Excellent' if average >= 80 else 'Good' if average >= 70 else 'Fair' if average >= 60 else 'Satisfactory' if average >= 50 else 'Poor'

            grading_table.append({
                'ID_NO': row['ID NO.'],
                'STUDENT_NAME': row['STUDENT NAME'],
                **{f'Subject{i+1}': subject for i, subject in enumerate(subjects)},
                **{f'Midterm-{i+1}': midterm for i, midterm in enumerate(midterms)},
                **{f'Final-{i+1}': final for i, final in enumerate(finals)},
                'Average': average,
                'Remark': remark
            })
    return grading_table

# Insert students into database
def database_student(table_name, data, cursor):    
    for row in data:
        age = int(row['AGE']) if 'AGE' in row and row['AGE'].isdigit() else 0
        cursor.execute(f'''INSERT INTO {table_name} 
                           (ID_NO, STUDENT_NAME, YEAR_LEVEL, AGE, SEX, EMAIL_ADDRESS, SHS, ADDRESS)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''', 
                           (row['ID_NO'], row['STUDENT_NAME'], row['YEAR_LEVEL'], age, row['SEX'], row.get('EMAIL_ADDRESS', ''), row.get('SHS', ''), row.get('ADDRESS', '')))

# Fetch and join grading and curriculum data
def fetch_data():
    conn, cursor = get_db_connection()

    # Fetch curriculum data
    cursor.execute("SELECT * FROM curriculum_regular")
    curriculum_data = cursor.fetchall()

    # Fetch grading data
    cursor.execute("SELECT * FROM database_grade")
    database_grade_data = cursor.fetchall()

    # Join the data
    joined_data = []
    for curriculum_row in curriculum_data:
        for database_grade_row in database_grade_data:
            if curriculum_row[0] == database_grade_row[0]:  # Match by ID_NO
                joined_row = {
                    "ID_NO": database_grade_row[0],
                    "STUDENT_NAME": database_grade_row[1],
                    "COURSE_NO": curriculum_row[0],
                    "DESCRIPTIVE_TITLE": curriculum_row[1],
                    "YEAR_LEVEL": curriculum_row[2],
                    "UNITS": curriculum_row[3],
                    "GRADES": database_grade_row[2],  # Adjust as needed
                    "REMARK": database_grade_row[15]  # Adjust the index for remark
                }
                joined_data.append(joined_row)

    conn.close()

    return joined_data
