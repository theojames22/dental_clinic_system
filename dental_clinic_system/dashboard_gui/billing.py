from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QFrame, QFormLayout
)
from PyQt6.QtCore import Qt

class BillingPage(QWidget):
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
        
        title = QLabel("Billing Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1F2937;")
        layout.addWidget(title)
        
        filter_layout = QHBoxLayout()
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Pending", "Paid", "Partial"])
        self.status_filter.currentTextChanged.connect(self.load_bills)
        filter_layout.addWidget(QLabel("Filter by status:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_bills)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Bill ID", "Patient", "Amount", "Status", "Payment Date"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        self.load_bills()
    
    def load_bills(self):
        status_filter = self.status_filter.currentText()
        if status_filter == "All":
            bills = self.db.get_all_bills()
        else:
            bills = self.db.get_bills_by_status(status_filter)
        
        self.table.setRowCount(len(bills))
        
        for row, bill in enumerate(bills):
            self.table.setItem(row, 0, QTableWidgetItem(str(bill.get('bill_id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(bill.get('patient_name', 'Unknown')))
            self.table.setItem(row, 2, QTableWidgetItem(f"${bill.get('amount', 0):.2f}"))
            
            status = bill.get('status', 'Pending')
            status_item = QTableWidgetItem(status)
            if status == "Paid":
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif status == "Pending":
                status_item.setForeground(Qt.GlobalColor.darkYellow)
            self.table.setItem(row, 3, status_item)
            
            payment_date = bill.get('payment_date')
            date_str = payment_date.strftime("%Y-%m-%d") if payment_date and hasattr(payment_date, 'strftime') else "-"
            self.table.setItem(row, 4, QTableWidgetItem(date_str))
    
    def refresh(self):
        self.load_bills()