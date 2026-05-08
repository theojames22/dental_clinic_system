from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QLineEdit, QComboBox, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QDialogButtonBox, QFormLayout, QDateEdit, QTimeEdit
)
from PyQt6.QtCore import Qt, QDate, QTime, QDateTime
from PyQt6.QtGui import QFont
from datetime import datetime

class AppointmentsPage(QWidget):
    def __init__(self, db, current_user, dashboard):
        super().__init__()
        self.db = db
        self.current_user = current_user
        self.dashboard = dashboard
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        header_layout = QHBoxLayout()
        title = QLabel("Appointment Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1F2937;")
        header_layout.addWidget(title)
        
        book_btn = QPushButton("+ Book Appointment")
        book_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        book_btn.clicked.connect(self.book_appointment)
        header_layout.addWidget(book_btn)
        
        layout.addLayout(header_layout)
        
        filter_layout = QHBoxLayout()
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "scheduled", "confirmed", "completed", "cancelled", "walk-in"])
        self.status_filter.currentTextChanged.connect(self.load_appointments)
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.status_filter)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search by patient, doctor, or treatment...")
        self.search_input.textChanged.connect(self.load_appointments)
        filter_layout.addWidget(self.search_input)
        
        layout.addLayout(filter_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Date/Time", "Patient", "Doctor", "Treatment", "Status", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #E5E7EB;
            }
            QTableWidget::item {
                padding: 10px;
            }
        """)
        layout.addWidget(self.table)
        
        self.load_appointments()
    
    def load_appointments(self):
        appointments = self.db.get_all_appointments_with_details()
        
        status_filter = self.status_filter.currentText()
        if status_filter != "All":
            appointments = [a for a in appointments if a.get('status', '').lower() == status_filter.lower()]
        
        search_term = self.search_input.text().strip().lower()
        if search_term:
            filtered = []
            for a in appointments:
                if (search_term in a.get('patient_name', '').lower() or
                    search_term in a.get('doctor_name', '').lower() or
                    search_term in a.get('treatment_name', '').lower()):
                    filtered.append(a)
            appointments = filtered
        
        self.table.setRowCount(len(appointments))
        
        for row, apt in enumerate(appointments):
            date_str = ""
            if apt.get('appointment_date'):
                if hasattr(apt['appointment_date'], 'strftime'):
                    date_str = apt['appointment_date'].strftime("%b %d, %Y\n%I:%M %p")
                else:
                    date_str = str(apt['appointment_date'])[:16]
            
            self.table.setItem(row, 0, QTableWidgetItem(date_str))
            self.table.setItem(row, 1, QTableWidgetItem(apt.get('patient_name', 'Unknown')))
            self.table.setItem(row, 2, QTableWidgetItem(apt.get('doctor_name', 'Not Assigned')))
            self.table.setItem(row, 3, QTableWidgetItem(apt.get('treatment_name', 'Consultation')))
            
            status = apt.get('status', 'pending')
            status_item = QTableWidgetItem(status.capitalize())
            status_colors = {
                'completed': '#10B981',
                'confirmed': '#3B82F6',
                'scheduled': '#6B7280',
                'cancelled': '#EF4444',
                'walk-in': '#8B5CF6'
            }
            status_item.setForeground(Qt.GlobalColor.black)
            self.table.setItem(row, 4, status_item)
            
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 5, 5, 5)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet("background-color: #3B82F6; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
            edit_btn.clicked.connect(lambda checked, a=apt: self.edit_appointment(a))
            action_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("background-color: #EF4444; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
            delete_btn.clicked.connect(lambda checked, a=apt: self.delete_appointment(a))
            action_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 5, action_widget)
    
    def book_appointment(self):
        QMessageBox.information(self, "Book Appointment", "This feature will be implemented in the next update.")
    
    def edit_appointment(self, appointment):
        QMessageBox.information(self, "Edit Appointment", f"Editing appointment #{appointment.get('appointment_id')}")
    
    def delete_appointment(self, appointment):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete appointment for {appointment.get('patient_name')}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            result = self.db.delete_appointment(appointment.get('appointment_id'))
            if result:
                QMessageBox.information(self, "Success", "Appointment deleted successfully!")
                self.load_appointments()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete appointment")
    
    def refresh(self):
        self.load_appointments()