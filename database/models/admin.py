import mysql.connector
from configparser import Error
import datetime, logging

class AdminModel:
    def __init__(self, db_connection):
        self.db = db_connection

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
