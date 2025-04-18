import mysql.connector
import logging
import time

class DBConnection:
    def __init__(self):
        self.conn, self.cursor = self.get_db_connection()

    def get_db_connection(self):
        conn = mysql.connector.connect(
            host='localhost', #192.168.254.125
            user='root',
            password='', 
            database='department',
            port=3306,
            allow_local_infile=True
        )
        cursor = conn.cursor()
        return conn, cursor
    
    def close_db_connection(self):
        self.conn.close()
        
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

