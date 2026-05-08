from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QLineEdit, QFormLayout, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt

class InventoryPage(QWidget):
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
        
        title = QLabel("Inventory Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1F2937;")
        layout.addWidget(title)
        
        filter_layout = QHBoxLayout()
        
        self.alert_filter = QCheckBox("Show low stock items only")
        self.alert_filter.toggled.connect(self.load_inventory)
        filter_layout.addWidget(self.alert_filter)
        filter_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_inventory)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Item Name", "Quantity", "Price", "Reorder Level", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        self.load_inventory()
    
    def load_inventory(self):
        if self.alert_filter.isChecked():
            items = self.db.get_low_stock_items()
        else:
            items = self.db.get_all_inventory()
        
        self.table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('item_id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(item.get('item_name', 'Unknown')))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get('quantity', 0))))
            self.table.setItem(row, 3, QTableWidgetItem(f"${item.get('price', 0):.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(str(item.get('reorder_level', 0))))
            
            qty = item.get('quantity', 0)
            reorder = item.get('reorder_level', 0)
            if qty <= reorder:
                status = "⚠️ Low Stock"
                status_item = QTableWidgetItem(status)
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status = "✓ In Stock"
                status_item = QTableWidgetItem(status)
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            
            self.table.setItem(row, 5, status_item)
    
    def refresh(self):
        self.load_inventory()