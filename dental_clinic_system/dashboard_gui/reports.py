from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDateEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime

class ReportsPage(QWidget):
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
        
        title = QLabel("Reports")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1F2937;")
        layout.addWidget(title)
        
        self.tab_widget = QTabWidget()
        
        self.appointments_tab = QWidget()
        self.setup_appointments_tab()
        self.tab_widget.addTab(self.appointments_tab, "Appointments")
        
        self.billing_tab = QWidget()
        self.setup_billing_tab()
        self.tab_widget.addTab(self.billing_tab, "Billing")
        
        self.inventory_tab = QWidget()
        self.setup_inventory_tab()
        self.tab_widget.addTab(self.inventory_tab, "Inventory")
        
        layout.addWidget(self.tab_widget)
    
    def setup_appointments_tab(self):
        layout = QVBoxLayout(self.appointments_tab)
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Status:"))
        self.apt_status_filter = QComboBox()
        self.apt_status_filter.addItems(["All", "scheduled", "confirmed", "completed", "cancelled"])
        self.apt_status_filter.currentTextChanged.connect(self.load_appointment_report)
        filter_layout.addWidget(self.apt_status_filter)
        
        filter_layout.addStretch()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_appointment_report)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        self.appointment_table = QTableWidget()
        self.appointment_table.setAlternatingRowColors(True)
        layout.addWidget(self.appointment_table)
        
        self.load_appointment_report()
    
    def setup_billing_tab(self):
        layout = QVBoxLayout(self.billing_tab)
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Status:"))
        self.bill_status_filter = QComboBox()
        self.bill_status_filter.addItems(["All", "Pending", "Paid", "Partial"])
        self.bill_status_filter.currentTextChanged.connect(self.load_billing_report)
        filter_layout.addWidget(self.bill_status_filter)
        
        filter_layout.addStretch()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_billing_report)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        self.billing_table = QTableWidget()
        self.billing_table.setAlternatingRowColors(True)
        layout.addWidget(self.billing_table)
        
        self.load_billing_report()
    
    def setup_inventory_tab(self):
        layout = QVBoxLayout(self.inventory_tab)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_inventory_report)
        layout.addWidget(refresh_btn)
        
        self.inventory_table = QTableWidget()
        self.inventory_table.setAlternatingRowColors(True)
        layout.addWidget(self.inventory_table)
        
        self.load_inventory_report()
    
    def load_appointment_report(self):
        status = self.apt_status_filter.currentText()
        if status == "All":
            status = None
        reports = self.db.get_filtered_appointment_report(status=status)
        
        if reports:
            self.appointment_table.setColumnCount(6)
            self.appointment_table.setHorizontalHeaderLabels(["Date", "Patient", "Doctor", "Treatment", "Status", "Amount"])
            
            self.appointment_table.setRowCount(len(reports))
            for row, report in enumerate(reports):
                apt_date = report.get('appointment_date')
                date_str = apt_date.strftime("%Y-%m-%d %H:%M") if hasattr(apt_date, 'strftime') else str(apt_date)
                self.appointment_table.setItem(row, 0, QTableWidgetItem(date_str))
                self.appointment_table.setItem(row, 1, QTableWidgetItem(str(report.get('patient_name', ''))))
                self.appointment_table.setItem(row, 2, QTableWidgetItem(str(report.get('doctor_name', ''))))
                self.appointment_table.setItem(row, 3, QTableWidgetItem(str(report.get('treatment_name', ''))))
                self.appointment_table.setItem(row, 4, QTableWidgetItem(str(report.get('status', ''))))
                self.appointment_table.setItem(row, 5, QTableWidgetItem(f"${float(report.get('amount', 0)):.2f}"))
    
    def load_billing_report(self):
        status = self.bill_status_filter.currentText()
        if status == "All":
            status = None
        reports = self.db.get_filtered_billing_report(status=status)
        
        if reports:
            self.billing_table.setColumnCount(5)
            self.billing_table.setHorizontalHeaderLabels(["Bill ID", "Patient", "Amount", "Status", "Payment Date"])
            
            self.billing_table.setRowCount(len(reports))
            for row, report in enumerate(reports):
                self.billing_table.setItem(row, 0, QTableWidgetItem(str(report.get('bill_id', ''))))
                self.billing_table.setItem(row, 1, QTableWidgetItem(str(report.get('patient_name', ''))))
                self.billing_table.setItem(row, 2, QTableWidgetItem(f"${float(report.get('amount', 0)):.2f}"))
                self.billing_table.setItem(row, 3, QTableWidgetItem(str(report.get('status', ''))))
                pay_date = report.get('payment_date')
                date_str = pay_date.strftime("%Y-%m-%d") if pay_date and hasattr(pay_date, 'strftime') else "-"
                self.billing_table.setItem(row, 4, QTableWidgetItem(date_str))
    
    def load_inventory_report(self):
        reports = self.db.get_inventory_report()
        
        if reports:
            self.inventory_table.setColumnCount(6)
            self.inventory_table.setHorizontalHeaderLabels(["ID", "Item Name", "Quantity", "Price", "Reorder Level", "Status"])
            
            self.inventory_table.setRowCount(len(reports))
            for row, report in enumerate(reports):
                self.inventory_table.setItem(row, 0, QTableWidgetItem(str(report.get('item_id', ''))))
                self.inventory_table.setItem(row, 1, QTableWidgetItem(str(report.get('item_name', ''))))
                self.inventory_table.setItem(row, 2, QTableWidgetItem(str(report.get('quantity', 0))))
                self.inventory_table.setItem(row, 3, QTableWidgetItem(f"${float(report.get('price', 0)):.2f}"))
                self.inventory_table.setItem(row, 4, QTableWidgetItem(str(report.get('reorder_level', 0))))
                self.inventory_table.setItem(row, 5, QTableWidgetItem(str(report.get('alert_status', 'Normal'))))