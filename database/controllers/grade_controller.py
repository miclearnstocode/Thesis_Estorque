# database/controllers/grades_controller.py

class GradesController:
    def __init__(self, grade_model):
        self.model = grade_model

    def save_grading_data(self, grading_data, year, semester, school_year):
        return self.model.save_grading_data(grading_data, year, semester, school_year)

    def get_grades(self, student_id):
        return self.model.get_grades(student_id)