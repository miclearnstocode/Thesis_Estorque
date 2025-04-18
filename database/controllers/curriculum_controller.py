# database/controllers/curriculum_controller.py

class CurriculumController:
    def __init__(self, curriculum_model):
        self.model = curriculum_model

    def saving_curriculum_data(self, processed_data):
        return self.model.saving_curriculum_data(processed_data)

    def fetch_curriculum(self, year_level, id_no):
        return self.model.fetch_curriculum(year_level, id_no)