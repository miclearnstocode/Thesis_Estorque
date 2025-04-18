# database/controllers/student_controller.py

class StudentController:
    def __init__(self, student_model):
        self.model = student_model

    def saving_student(self, last_name, first_name, middle_name, data, enrolled_year, bday, to_be_enrolled_years, table_name=None):
        return self.model.saving_student(last_name, first_name, middle_name, data, enrolled_year, bday, to_be_enrolled_years, table_name)

    def fetch_student_data(self, id_no, year_level):
        return self.model.fetch_student_data(id_no, year_level)