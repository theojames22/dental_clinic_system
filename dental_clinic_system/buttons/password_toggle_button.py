from PyQt6.QtWidgets import QWidget, QCheckBox
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen

class EyeIcon(QWidget):
    def __init__(self, icon_type="eye", parent=None):
        super().__init__(parent)
        self.icon_type = icon_type
        self.setFixedSize(30, 30)
        self._scale = 1.0
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._scale, self._scale)
        painter.translate(-self.width() / 2, -self.height() / 2)
        
        color = QColor("#a5a5b0")
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        
        if self.icon_type == "eye":
            painter.drawEllipse(6, 12, 18, 10)
            painter.drawEllipse(13, 14, 4, 5)
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(14, 15, 2, 3)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(22, 14, 2, 4)
        else:
            painter.drawEllipse(6, 12, 18, 10)
            painter.drawEllipse(13, 14, 4, 5)
            painter.setPen(QPen(color, 2))
            painter.drawLine(5, 8, 25, 22)
        
        painter.end()
    
    def animate(self):
        self.animation = QPropertyAnimation(self, b"scale")
        self.animation.setDuration(500)
        self.animation.setStartValue(0.0)
        self.animation.setKeyValueAt(0.5, 1.2)
        self.animation.setEndValue(1.0)
        self.animation.start()
    
    def get_scale(self): return self._scale
    def set_scale(self, value): self._scale = value; self.update()
    scale = pyqtProperty(float, get_scale, set_scale)

class Container(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 30)
        
        self.checkbox = QCheckBox(self)
        self.checkbox.setFixedSize(0, 0)
        self.checkbox.setStyleSheet("opacity: 0; position: absolute;")
        
        self.eye = EyeIcon("eye", self)
        self.eye_slash = EyeIcon("eye-slash", self)
        self.eye_slash.hide()
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkbox.stateChanged.connect(self.on_toggle)
    
    def on_toggle(self, state):
        if state == Qt.CheckState.Checked.value:
            self.eye.hide()
            self.eye_slash.show()
            self.eye_slash.animate()
        else:
            self.eye.show()
            self.eye_slash.hide()
            self.eye.animate()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.checkbox.toggle()
        super().mousePressEvent(event)

class PasswordToggleButton(Container):
    """Toggle widget for password visibility.

    This class is used by `login_gui.py`.

    Expected API:
      - set_state(is_on: bool)
      - clicked.connect(fn)  (provided below)
    """

    class _SignalProxy:
        def __init__(self, container: "PasswordToggleButton"):
            self._container = container

        def connect(self, fn):
            # checkbox is the true state driver
            self._container.checkbox.stateChanged.connect(lambda _: fn())

    def __init__(self, parent=None, on_text="", off_text=""):
        super().__init__(parent)
        self._is_on = False
        # compatibility with login_gui.py expecting `.clicked.connect(...)`
        self.clicked = self._SignalProxy(self)

    def set_state(self, is_on):
        """Set the toggle state (True = password visible, False = password hidden)."""
        if is_on != self._is_on:
            self._is_on = bool(is_on)

        if self._is_on:
            # Password visible -> show eye-slash
            self.eye.hide()
            self.eye_slash.show()
        else:
            # Password hidden -> show eye
            self.eye.show()
            self.eye_slash.hide()

        # keep checkbox consistent with state
        self.checkbox.setChecked(self._is_on)

    def is_checked(self):
        return self.checkbox.isChecked()

