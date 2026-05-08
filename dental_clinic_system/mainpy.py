# In mainpy.py or wherever you initialize the app:

from PyQt6.QtWidgets import QApplication
from login_gui import LoginGUI
from databasepy import Database
from dashboard_gui.style import Config
import sys

class DentalClinicApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(Config.APP_NAME)
        self.app.setStyle('Fusion')
        
        # Initialize database
        self.db = Database()
        
        # Setup recovery columns on startup
        if self.db.is_connected():
            self.db.setup_recovery_columns()
        
        # Create login window
        self.login_gui = LoginGUI(None, self.db)
        
    def run(self):
        self.login_gui.show()
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = DentalClinicApp()
    app.run()