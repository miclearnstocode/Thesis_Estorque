# database/controllers/admin_controller.py

class AdminController:
    def __init__(self, admin_model):
        self.model = admin_model

    def create_users_table(self):
        return self.model.create_users_table()

    def save_user(self, id, email, hashed_password, salt, username):
        return self.model.save_user(id, email, hashed_password, salt, username)