"""
Custom PyQt6 3D flip checkbox widget
Converted from: https://uiverse.io by SharpTH
Features a 3D flip animation with checkmark on checked state
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty, QRect, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt6.QtCore import QTimer


class CustomCheckbox(QWidget):
    """
    Custom 3D flip checkbox with animation
    
    Usage:
        checkbox = CustomCheckbox(parent)
        checkbox.setChecked(True/False)
        checkbox.stateChanged.connect(callback)
    """
    
    def __init__(self, parent=None, text=""):
        super().__init__(parent)
        self.text = text
        self._is_checked = False
        self._rotation_y = 0  # 0 = front (unchecked), 180 = back (checked)
        self._hover = False
        
        # Set size based on whether text is provided
        if text:
            self.setFixedSize(250, 24)  # Larger for text
        else:
            self.setFixedSize(24, 24)  # Just checkbox
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")
        
        # Animation
        self.animation = QPropertyAnimation(self, b"rotationY")
        self.animation.setDuration(400)
        
    def setChecked(self, checked):
        """Set checkbox checked state with animation"""
        if checked != self._is_checked:
            self._is_checked = checked
            self.animate_flip()
    
    def isChecked(self):
        """Get checkbox checked state"""
        return self._is_checked
    
    def animate_flip(self):
        """Animate the 3D flip"""
        self.animation.stop()
        start = self._rotation_y
        end = 180 if self._is_checked else 0
        
        self.animation.setStartValue(start)
        self.animation.setEndValue(end)
        self.animation.start()
    
    def get_rotation_y(self):
        return self._rotation_y
    
    def set_rotation_y(self, value):
        self._rotation_y = value
        self.update()
    
    rotationY = pyqtProperty(float, get_rotation_y, set_rotation_y)
    
    def mousePressEvent(self, event):
        """Toggle checkbox on click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._is_checked)
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """Handle hover enter"""
        self._hover = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle hover leave"""
        self._hover = False
        self.update()
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        """Paint the 3D checkbox"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate perspective/3D effect
        progress = self._rotation_y / 180.0
        
        # Checkbox position
        checkbox_x = 0
        checkbox_y = 0
        checkbox_size = 20
        
        # Front face (unchecked) - visible when rotation_y < 90
        if self._rotation_y < 90:
            alpha = int(255 * (1 - progress * 2))  # Fade out as we rotate past 90
            if alpha > 0:
                self.draw_front_face(painter, checkbox_x, checkbox_y, checkbox_size, alpha)
        
        # Back face (checked) - visible when rotation_y > 90
        if self._rotation_y > 90:
            alpha = int(255 * ((progress * 2) - 1))  # Fade in after 90 degrees
            if alpha > 0:
                self.draw_back_face(painter, checkbox_x, checkbox_y, checkbox_size, alpha)
        
        # Draw text if provided
        if self.text:
            text_x = 28  # 20 (checkbox) + 8 (spacing)
            text_color = QColor("#1F2937")  # Dark gray-black
            painter.setPen(text_color)
            font = QFont()
            font.setPointSize(10)
            font.setFamily("Segoe UI")
            painter.setFont(font)
            painter.drawText(text_x, 2, 220, 20, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text)
    
    def draw_front_face(self, painter, x, y, size, alpha):
        """Draw the front face (unchecked state)"""
        # Outer box with gray border
        outer_color = QColor("#e8e8eb")
        outer_color.setAlpha(alpha)
        
        border_color = QColor("#0b76ef") if self._hover else QColor("#e8e8eb")
        border_color.setAlpha(alpha)
        
        # Outer gray background
        painter.fillRect(x, y, size, size, outer_color)
        painter.setPen(QPen(border_color, 2))
        painter.drawRect(x, y, size, size)
        
        # Inner white square
        inner_margin = 2
        inner_color = QColor("#ffffff")
        inner_color.setAlpha(alpha)
        painter.fillRect(x + inner_margin, y + inner_margin, size - 2*inner_margin, size - 2*inner_margin, inner_color)
    
    def draw_back_face(self, painter, x, y, size, alpha):
        """Draw the back face (checked state) with checkmark"""
        # Blue border
        border_color = QColor("#0b76ef")
        border_color.setAlpha(alpha)
        painter.setPen(QPen(border_color, 2))
        
        # Blue background
        bg_color = QColor("#0b76ef")
        bg_color.setAlpha(alpha)
        painter.fillRect(x, y, size, size, bg_color)
        painter.drawRect(x, y, size, size)
        
        # Draw checkmark
        self.draw_checkmark(painter, x, y, size, alpha)
    
    def draw_checkmark(self, painter, x, y, size, alpha):
        """Draw SVG checkmark (✓)"""
        checkmark_color = QColor("#ffffff")
        checkmark_color.setAlpha(alpha)
        
        painter.setPen(QPen(checkmark_color, 2.5))
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Checkmark proportions within the box
        # M19 5l-11 11-7-7 from 24x24 viewBox
        # Normalize to our checkbox size
        
        # Calculate scale
        scale = size / 24.0
        offset_x = x
        offset_y = y
        
        # Start point (top right)
        p1_x = offset_x + (19 * scale)
        p1_y = offset_y + (6 * scale)
        
        # Middle point (bottom middle)
        p2_x = offset_x + (8 * scale)
        p2_y = offset_y + (15 * scale)
        
        # End point (bottom left)
        p3_x = offset_x + (2 * scale)
        p3_y = offset_y + (9 * scale)
        
        # Draw checkmark lines
        painter.drawLine(int(p1_x), int(p1_y), int(p2_x), int(p2_y))
        painter.drawLine(int(p2_x), int(p2_y), int(p3_x), int(p3_y))
