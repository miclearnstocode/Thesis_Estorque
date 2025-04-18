# database/controllers/appraisal_controller.py

class AppraisalController:
    def __init__(self, appraisal_model):
        self.model = appraisal_model

    def save_appraised_data(self, appraised_id, id_no, last_name, first_name, middle_name, year, sex, age, email_address, matched_subjects, school_year):
        return self.model.save_appraised_data(appraised_id, id_no, last_name, first_name, middle_name, year, sex, age, email_address, matched_subjects, school_year)

    def update_appraised_grades(self, grades_df):
        return self.model.update_appraised_grades(grades_df)