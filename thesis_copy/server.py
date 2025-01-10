from flask import Flask, request, jsonify
from database import DatabaseHandler

app = Flask(__name__)
db_handler = DatabaseHandler()

@app.route('/get_student_grades', methods=['GET'])
def get_student_grades():
    id_no = request.args.get('id_no')
    semester = request.args.get('semester')
    
    if not id_no or not semester:
        return jsonify({'error': 'ID number and semester are required'}), 400
    
    try:
        grades = db_handler.get_student_grades(id_no, semester)
        if grades:
            return jsonify(grades), 200
        else:
            return jsonify({'message': 'No grades found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='192.168.254.125', port=5001)  # Updated port to avoid conflict with XAMPP
