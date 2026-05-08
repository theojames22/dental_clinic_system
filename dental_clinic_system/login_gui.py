"""
PyQt6 conversion of login_gui.py
Preserves original logic, method names, and behavior. Only the UI framework changed
from customtkinter to PyQt6. Visual layout matches the provided screenshot.
"""

import re
import sys
import json
import os
from PyQt6.QtCore import Qt, QTimer, QSettings
from PyQt6.QtGui import QIcon, QPixmap, QFont, QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QLineEdit, QPushButton,
    QCheckBox, QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QGraphicsDropShadowEffect,
    QScrollArea, QSizePolicy, QStackedWidget, QRadioButton
)
from databasepy import *
from dashboard_gui.style import *
from dashboard_gui.dashboard_gui import DashboardGUI
from buttons.password_toggle_button import PasswordToggleButton
from buttons.custom_checkbox import CustomCheckbox
from dashboard_gui.forgot_password_module import ForgotPasswordFlow
from dashboard_gui.forgot_password_module import *





class RoleIcon(QWidget):
    """Clean painted icons for role selection buttons"""
    ADMIN = 100
    RECEPTIONIST = 101
    DENTIST = 102

    def __init__(self, icon_type, size=36, color=None, parent=None):
        super().__init__(parent)
        self.icon_type = icon_type
        self._color = color if color else QColor('#64748B')
        self.setFixedSize(size, size)

    def set_color(self, color):
        self._color = color
        self.update()

    def paintEvent(self, event):
        w = self.width()
        h = self.height()
        if w < 4 or h < 4:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = w / 2.0
        cy = h / 2.0
        s = min(w, h) / 48.0
        c = self._color
        pen = QPen(c, 2.2 * s)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        if self.icon_type == self.ADMIN:
            self._draw_admin(p, cx, cy, s, c, pen)
        elif self.icon_type == self.RECEPTIONIST:
            self._draw_receptionist(p, cx, cy, s, c, pen)
        elif self.icon_type == self.DENTIST:
            self._draw_dentist(p, cx, cy, s, c, pen)
        p.end()

    def _draw_admin(self, p, cx, cy, s, c, pen):
        path = QPainterPath()
        path.moveTo(cx, cy - 18 * s)
        path.cubicTo(QPointF(cx + 14*s, cy - 16*s), QPointF(cx + 16*s, cy - 4*s), QPointF(cx + 16*s, cy))
        path.cubicTo(QPointF(cx + 16*s, cy + 10*s), QPointF(cx, cy + 20*s), QPointF(cx, cy + 20*s))
        path.cubicTo(QPointF(cx, cy + 20*s), QPointF(cx - 16*s, cy + 10*s), QPointF(cx - 16*s, cy))
        path.cubicTo(QPointF(cx - 16*s, cy - 4*s), QPointF(cx - 14*s, cy - 16*s), QPointF(cx, cy - 18*s))
        path.closeSubpath()
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        p.setBrush(QBrush(c))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), 2.5 * s, 2.5 * s)

    def _draw_receptionist(self, p, cx, cy, s, c, pen):
        p.setBrush(QBrush(c))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy - 12 * s), 5 * s, 5.5 * s)
        body = QPainterPath()
        body.moveTo(cx - 14 * s, cy + 8 * s)
        body.cubicTo(QPointF(cx - 14*s, cy - 2*s), QPointF(cx - 7*s, cy - 5*s), QPointF(cx, cy - 5*s))
        body.cubicTo(QPointF(cx + 7*s, cy - 5*s), QPointF(cx + 14*s, cy - 2*s), QPointF(cx + 14*s, cy + 8*s))
        body.closeSubpath()
        p.drawPath(body)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(QPointF(cx - 18 * s, cy + 13 * s), QPointF(cx + 18 * s, cy + 13 * s))

    def _draw_dentist(self, p, cx, cy, s, c, pen):
        path = QPainterPath()
        path.moveTo(cx - 10 * s, cy - 2 * s)
        path.lineTo(cx - 10 * s, cy + 8 * s)
        path.cubicTo(QPointF(cx - 10*s, cy + 16*s), QPointF(cx + 10*s, cy + 16*s), QPointF(cx + 10*s, cy + 8*s))
        path.lineTo(cx + 10 * s, cy - 2 * s)
        path.cubicTo(QPointF(cx + 10*s, cy - 14*s), QPointF(cx + 2*s, cy - 14*s), QPointF(cx + 2*s, cy - 6*s))
        path.lineTo(cx, cy - 3 * s)
        path.lineTo(cx - 2 * s, cy - 6 * s)
        path.cubicTo(QPointF(cx - 2*s, cy - 14*s), QPointF(cx - 10*s, cy - 14*s), QPointF(cx - 10*s, cy - 2*s))
        path.closeSubpath()
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)


class RoleCard(QFrame):
    """Clickable role selection card with painted icon"""
    def __init__(self, role_id, icon_type, title, color, parent=None):
        super().__init__(parent)
        self.role_id = role_id
        self._color = color
        self._selected = False
        self.on_click = None
        
        # Ensure _text exists before _apply_style() touches it
        self._text = None
        self._icon = None

        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(10)

        self._icon = RoleIcon(icon_type, size=32, color=QColor(color))
        layout.addWidget(self._icon)

        self._text = QLabel(title)
        self._text.setStyleSheet(
            f"color: {color}; font-size: 13px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self._text)
        layout.addStretch()

    def _apply_style(self):
        if self._selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._color};
                    border: 2px solid {self._color};
                    border-radius: 12px;
                }}
            """)
            if self._text is not None:
                self._text.setStyleSheet(
                    f"color: #FFFFFF; font-size: 13px; font-weight: 700; "
                    f"background: transparent; border: none;"
                )
            if self._icon is not None:
                self._icon.set_color(QColor('#FFFFFF'))
        else:
            # Parse hex color to RGB for hover effect
            hex_color = self._color.name() if isinstance(self._color, QColor) else self._color
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: #FFFFFF;
                    border: 2px solid {self._color.name() if isinstance(self._color, QColor) else self._color};
                    border-radius: 12px;
                }}
                QFrame:hover {{
                    background-color: rgba({r}, {g}, {b}, 50);
                }}
            """)
            if self._text is not None:
                self._text.setStyleSheet(
                    f"color: {self._color}; font-size: 13px; font-weight: 700; "
                    f"background: transparent; border: none;"
                )
            if self._icon is not None:
                self._icon.set_color(QColor(self._color))



    def set_selected(self, selected):
        self._selected = selected
        self._apply_style()

    def mousePressEvent(self, event):
        if self.on_click:
            self.on_click()
        super().mousePressEvent(event)
# -----------------------------------------------------------------------------
# LoginGUI (PyQt6)
# -----------------------------------------------------------------------------
class LoginGUI(QMainWindow):
    def __init__(self, root=None, db=None):
        super().__init__()
        self.root = root  # kept for API parity; not used in Qt
        self.db = db
        self.login_attempts = {}
        self.reset_codes = {}
        
        # Setup QSettings for persistent storage
        self.settings = QSettings("LC Dental Care", "DentalClinicSystem")
        
        # Load saved credentials
        self.saved_credentials = self.load_saved_credentials()
        
        self.signup_strength_indicator = None
        self.signup_strength_label = None
        self.password_visible = False
        self.selected_recovery_method = None
        self.recovery_username = None
        self.verification_code = None

        self.setWindowTitle("DentalCare - Login")
        self.setMinimumSize(1024, 768)

        # Top-right exit (X) button
        self.exit_btn = QPushButton("X", self)
        self.exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exit_btn.setFixedSize(45, 45)
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background: rgba(220, 53, 69, 200);
                color: white;
                border: 2px solid #DC3545;
                border-radius: 10px;
                font-weight: 700;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(220, 53, 69, 255);
            }
        """)
        self.exit_btn.clicked.connect(self.exit)

        self.showFullScreen()
        
        # Position button at top-right after window is shown
        QTimer.singleShot(100, self._position_exit_button)

    def load_saved_credentials(self):
        """Load saved credentials from QSettings"""
        try:
            username = self.settings.value("saved_username", "", type=str)
            remember = self.settings.value("remember_me", False, type=bool)
            return {"username": username, "remember": remember}
        except Exception as e:
            print(f"Error loading saved credentials: {e}")
            return {"username": "", "remember": False}

    def save_credentials(self, username, remember):
        """Save credentials to QSettings"""
        try:
            if remember:
                self.settings.setValue("saved_username", username)
                self.settings.setValue("remember_me", True)
            else:
                self.settings.remove("saved_username")
                self.settings.setValue("remember_me", False)
        except Exception as e:
            print(f"Error saving credentials: {e}")

    # -------------------------------------------------------------------------
    def _position_exit_button(self):
        """Position exit button at top-right corner"""
        self.exit_btn.move(self.width() - 60, 15)
        self.exit_btn.raise_()

    # -------------------------------------------------------------------------
    def _make_input(self, placeholder, icon="", password=False):
        """Create a rounded input field with leading icon and optional eye toggle."""
        frame = QFrame()
        frame.setFixedHeight(52)
        frame.setStyleSheet("""
            QFrame {
                background-color:#F3F4F6;
                border:1px solid #E5E7EB;
                border-radius:10px;
            }
        """)
        h = QHBoxLayout(frame)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(10)
        
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("color:#9CA3AF;font-size:16px;background:transparent;border:none;")
        h.addWidget(icon_lbl)
        
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setStyleSheet("""
            QLineEdit {
                background:transparent;
                border:none;
                color:#1F2937;
                font-size:14px;
            }
        """)
        if password:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
        h.addWidget(edit, 1)
        
        if password:
            eye = PasswordToggleButton(parent=frame, on_text="🙈", off_text="👁")
            eye.set_state(is_on=False)  # password hidden => show eye
            eye.clicked.connect(lambda: self.toggle_password(edit, eye))
            h.addWidget(eye)

        
        return {"frame": frame, "edit": edit}
    
    # -------------------------------------------------------------------------
    def toggle_password(self, edit, eye_button):
        """Toggle password visibility"""
        if edit.echoMode() == QLineEdit.EchoMode.Password:
            edit.setEchoMode(QLineEdit.EchoMode.Normal)
            eye_button.set_state(True)
        else:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
            eye_button.set_state(False)

    # -------------------------------------------------------------------------
    def show(self):
        self.clear_window()

        # Create central widget with background
        central = QWidget()
        self.setCentralWidget(central)
        
        # Use QStackedLayout or simple grid to overlay content on background
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Set background using stylesheet (no backslashes in f-strings)
        image_path = "D:/dental_clinic_system/image/background.png"
        # Check if background image exists, if not use a gradient
        if os.path.exists(image_path):
            central.setStyleSheet(f"""
                QWidget {{
                    background-image: url("{image_path}");
                    background-position: center;
                    background-repeat: no-repeat;
                }}
            """)
        else:
            central.setStyleSheet("""
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #E8F0FE, stop:1 #F0F4F8);
                }
            """)
        
        # Create login card container
        login_container = QWidget(central)
        login_container.setStyleSheet("background: transparent;")
        
        container_layout = QVBoxLayout(login_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addStretch()
        
        card_row = QHBoxLayout()
        card_row.addStretch()
        
        # Create login card
        login_card = QFrame()
        login_card.setObjectName("loginCard")
        login_card.setFixedSize(580, 720)
        login_card.setStyleSheet("""
            #loginCard {
                background-color: white;
                border-radius: 20px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(login_card)
        shadow.setBlurRadius(50)
        shadow.setOffset(0, 15)
        shadow.setColor(QColor(0, 0, 0, 80))
        login_card.setGraphicsEffect(shadow)
        
        content = QVBoxLayout(login_card)
        content.setContentsMargins(55, 55, 55, 45)
        content.setSpacing(0)
        
        # Header
        title = QLabel("Welcome to LC Dental Care!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color:#1F2937;font-size:32px;font-weight:700;background:transparent;")
        content.addWidget(title)
        content.addSpacing(12)
        
        subtitle = QLabel("Please enter your clinical credentials to access the dashboard.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color:#6B7280;font-size:14px;background:transparent;")
        content.addWidget(subtitle)
        content.addSpacing(35)
        
        # Username
        u_lbl = QLabel("Username or Clinical Email")
        u_lbl.setStyleSheet("color:#1F2937;font-size:14px;font-weight:700;background:transparent;")
        content.addWidget(u_lbl)
        content.addSpacing(10)
        
        self.username_entry = self._make_input("Enter your Username")
        content.addWidget(self.username_entry["frame"])
        content.addSpacing(25)
        
        # Password
        p_lbl = QLabel("Password")
        p_lbl.setStyleSheet("color:#1F2937;font-size:14px;font-weight:700;background:transparent;")
        content.addWidget(p_lbl)
        content.addSpacing(10)
        
        self.password_entry = self._make_input("Enter your password", password=True)
        content.addWidget(self.password_entry["frame"])
        content.addSpacing(22)
        
        # Options row
        opt_row = QHBoxLayout()
        self.remember_cb = CustomCheckbox(parent=None, text="Remember me")
        self.remember_cb.setChecked(self.saved_credentials.get("remember", False))

        opt_row.addWidget(self.remember_cb)
        opt_row.addStretch()
        self.forgot_btn = QPushButton("Forgot password?")
        self.forgot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.forgot_btn.setFlat(True)
        self.forgot_btn.setStyleSheet("""
            QPushButton {
                color:#1E40AF;
                font-size:13px;
                font-weight:700;
                border:none;
                background:transparent;
            }
            QPushButton:hover {
                color:#1E3A8A;
            }
        """)
        self.forgot_btn.clicked.connect(self.forgot_password)
        opt_row.addWidget(self.forgot_btn)
        content.addLayout(opt_row)
        content.addSpacing(28)
        
        # Login button
        self.login_btn = QPushButton("Secure Login")
        self.login_btn.setFixedHeight(52)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color:#1E3A8A;
                color:white;
                font-size:15px;
                font-weight:700;
                border-radius:10px;
                border: none;
            }
            QPushButton:hover { background-color:#1E40AF; }
            QPushButton:disabled { background-color:#94A3B8; }
        """)
        self.login_btn.clicked.connect(self.do_login)
        content.addWidget(self.login_btn)
        content.addSpacing(25)
        
        # Sign up row
        sign_row = QHBoxLayout()
        sign_row.addStretch()
        sign_lbl = QLabel("New to DentalCare?")
        sign_lbl.setStyleSheet("color:#6B7280;font-size:13px;background:transparent;")
        sign_row.addWidget(sign_lbl)
        self.signup_link = QPushButton("Create an Account")
        self.signup_link.setFlat(True)
        self.signup_link.setCursor(Qt.CursorShape.PointingHandCursor)
        self.signup_link.setStyleSheet("""
            QPushButton {
                color:#1E40AF;
                font-size:13px;
                font-weight:700;
                border:none;
                background:transparent;
            }
            QPushButton:hover {
                color:#1E3A8A;
            }
        """)
        self.signup_link.clicked.connect(self.show_signup)
        sign_row.addWidget(self.signup_link)
        sign_row.addStretch()
        content.addLayout(sign_row)
        content.addStretch()
        
        footer = QLabel("Need staff access? Contact Administrator")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color:#9CA3AF;font-size:12px;background:transparent;")
        content.addWidget(footer)
        
        card_row.addWidget(login_card)
        card_row.addStretch()
        container_layout.addLayout(card_row)
        container_layout.addStretch()
        
        # Add both background and container to main layout
        main_layout.addWidget(login_container)
        
        # Pre-fill saved credentials
        saved_username = self.saved_credentials.get("username", "")
        if saved_username:
            self.username_entry["edit"].setText(saved_username)
            # If username is filled, focus on password field
            self.password_entry["edit"].setFocus()
        else:
            # Set initial focus
            self.username_entry["edit"].setFocus()
        
        super().show()
        QTimer.singleShot(50, self._position_exit_button)
    
    # -------------------------------------------------------------------------
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
        elif event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.do_login()
        else:
            super().keyPressEvent(event)
    
    # -------------------------------------------------------------------------
    def do_login(self):
        # Check if login widgets exist (they may have been deleted by clear_window)
        if not hasattr(self, 'username_entry') or not self.username_entry:
            return
        if not hasattr(self, 'password_entry') or not self.password_entry:
            return
        if not self.username_entry.get("edit") or not self.password_entry.get("edit"):
            return
        
        # Check if the widgets are still valid (not deleted)
        try:
            username = self.username_entry["edit"].text().strip()
            password = self.password_entry["edit"].text()
        except RuntimeError:
            return  # Widget has been deleted
        
        if not username:
            self.show_error_notification("Please enter your username")
            return
        if not password:
            self.show_error_notification("Please enter your password")
            return
        
        self.login_btn.setText("⏳ Verifying...")
        self.login_btn.setDisabled(True)
        QTimer.singleShot(500, lambda: self.validate_login(username, password))
    
    def validate_login(self, username, password):
        roles = ["admin", "receptionist", "dentist"]
        user = None
        selected_role = None
        for role in roles:
            user = self.db.authenticate_user(username, password, role)
            if user:
                selected_role = role
                break
        
        if user:
            current_user = {
                "role": selected_role,
                "name": user.get("staff_name", username),
                "username": username,
                "user_id": user["user_id"],
            }
            
            # Save credentials if remember me is checked
            if self.remember_cb.isChecked():
                self.save_credentials(username, True)
            else:
                self.save_credentials("", False)
            
            self.show_success_notification(f"Welcome back, {current_user['name']}!")
            QTimer.singleShot(500, lambda: self.show_dashboard(current_user))
        else:
            self.login_btn.setText("Secure Login")
            self.login_btn.setDisabled(False)
            self.show_error_notification("Invalid username or password")
    
    # -------------------------------------------------------------------------
    def forgot_password(self):
        """Show forgot password recovery flow"""
        self.show_forgot_password_page()

    def show_forgot_password_page(self):
        """Show the forgot password recovery page with QStackedWidget flow"""
        self.clear_window()

        central = QWidget()
        self.setCentralWidget(central)

        import os
        image_path = "D:/dental_clinic_system/image/background.png"
        if os.path.exists(image_path):
            central.setStyleSheet(f"""
                QWidget {{
                    background-image: url("{image_path}");
                    background-position: center;
                    background-repeat: no-repeat;
                }}
            """)
        else:
            central.setStyleSheet("""
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #E8F0FE, stop:1 #F0F4F8);
                }
            """)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addStretch()

        row = QHBoxLayout()
        row.addStretch()

        from dashboard_gui.forgot_password_module import ForgotPasswordFlow
        self.forgot_password_flow = ForgotPasswordFlow(self.db)
        self.forgot_password_flow.backToLogin = self.show

        row.addWidget(self.forgot_password_flow)
        row.addStretch()
        main_layout.addLayout(row)
        main_layout.addStretch()

        super().show()
        QTimer.singleShot(50, self._position_exit_button)


    def show_signup(self):
        self.clear_window()

        central = QWidget()
        self.setCentralWidget(central)

        image_path = "D:/dental_clinic_system/image/background.png"
        if os.path.exists(image_path):
            central.setStyleSheet(f"""
                QWidget {{
                    background-image: url("{image_path}");
                    background-position: center;
                    background-repeat: no-repeat;
                }}
            """)
        else:
            central.setStyleSheet("""
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #E8F0FE, stop:1 #F0F4F8);
                }
            """)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addStretch()

        row = QHBoxLayout()
        row.addStretch()

        signup_card = QFrame()
        signup_card.setFixedSize(600, 750)
        signup_card.setObjectName("signupCard")
        signup_card.setStyleSheet("""
            #signupCard {
                background-color: white;
                border-radius: 20px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(signup_card)
        shadow.setBlurRadius(50)
        shadow.setOffset(0, 15)
        shadow.setColor(QColor(0, 0, 0, 80))
        signup_card.setGraphicsEffect(shadow)

        outer = QVBoxLayout(signup_card)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        outer.addWidget(scroll)

        scroll_inner = QWidget()
        scroll_inner.setStyleSheet("background: white; border: none;")
        scroll.setWidget(scroll_inner)

        content = QVBoxLayout(scroll_inner)
        content.setContentsMargins(40, 36, 40, 36)
        content.setSpacing(0)

        # Title
        title = QLabel("Create Account")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color:#1F2937;font-size:28px;font-weight:700;background:transparent;border:none;")
        content.addWidget(title)
        content.addSpacing(6)

        sub = QLabel("Join LC Dental Clinic and start managing your practice")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color:#6B7280;font-size:14px;background:transparent;border:none;")
        content.addWidget(sub)
        content.addSpacing(24)

        # Role selection label
        role_label = QLabel("Select Your Role")
        role_label.setStyleSheet("color:#374151;font-size:14px;font-weight:700;background:transparent;border:none;")
        content.addWidget(role_label)
        content.addSpacing(10)

        # Role cards row
        role_row = QHBoxLayout()
        role_row.setSpacing(12)

        self.selected_signup_role = None
        self.signup_role_cards = []

        roles = [
            ("Administrator", "admin", Config.COLORS["primary"], RoleIcon.ADMIN),
            ("Receptionist", "receptionist", Config.COLORS["secondary"], RoleIcon.RECEPTIONIST),
            ("Dentist", "dentist", Config.COLORS["info"], RoleIcon.DENTIST),
        ]

        for text, role, color, icon_id in roles:
            card = RoleCard(role, icon_id, text, color)
            card.on_click = lambda r=role, c=card: self.select_signup_role(r, c)
            role_row.addWidget(card)
            self.signup_role_cards.append({"card": card, "role": role, "color": color})

        content.addLayout(role_row)
        content.addSpacing(22)

        # Form fields
        fields = [
            ("Full Name", "signup_name_entry"),
            ("Username", "signup_username_entry"),
            ("Email Address", "signup_email_entry"),
            ("Phone Number", "signup_phone_entry"),
            ("Password", "signup_password_entry"),
            ("Confirm Password", "signup_confirm_entry"),
        ]

        for i, (label_text, attr_name) in enumerate(fields):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color:#374151;font-size:13px;font-weight:700;background:transparent;border:none;")
            content.addWidget(lbl)
            content.addSpacing(8)

            entry = QLineEdit()
            entry.setPlaceholderText(f"Enter {label_text.lower()}")
            entry.setFixedHeight(46)
            entry.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #E5E7EB;
                    border-radius: 10px;
                    padding: 0 14px;
                    font-size: 14px;
                    color: #1F2937;
                    background: #FFFFFF;
                }
                QLineEdit:focus {
                    border: 2px solid #1E3A8A;
                }
                QLineEdit::placeholder {
                    color: #9CA3AF;
                }
            """)
            if label_text == "Password" or label_text == "Confirm Password":
                entry.setEchoMode(QLineEdit.EchoMode.Password)
            content.addWidget(entry)
            setattr(self, attr_name, entry)

            # Password strength meter below Password field
            if label_text == "Password":
                content.addSpacing(6)
                self.signup_strength_meter = QFrame()
                self.signup_strength_meter.setFixedHeight(6)
                self.signup_strength_meter.setStyleSheet("background:#E5E7EB;border-radius:3px;border:none;")
                content.addWidget(self.signup_strength_meter)
                content.addSpacing(3)

                self.signup_strength_label = QLabel("")
                self.signup_strength_label.setStyleSheet("color:#9CA3AF;font-size:11px;background:transparent;border:none;")
                content.addWidget(self.signup_strength_label)
                entry.textChanged.connect(self.update_signup_password_strength)
            else:
                content.addSpacing(14)

        content.addSpacing(10)

        # Terms checkbox
        self.terms_check = CustomCheckbox(parent=None, text="I agree to the Terms and Conditions")
        content.addWidget(self.terms_check)
        content.addSpacing(18)

        # Create Account button
        signup_btn = QPushButton("Create Account")
        signup_btn.setFixedHeight(52)
        signup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        signup_btn.setStyleSheet("""
            QPushButton {
                background: #1E3A8A;
                color: white;
                font-size: 15px;
                font-weight: 700;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover {
                background: #1E40AF;
            }
        """)
        signup_btn.clicked.connect(self.do_signup)
        content.addWidget(signup_btn)
        content.addSpacing(14)

        # Login link
        login_row = QHBoxLayout()
        login_row.addStretch()
        already = QLabel("Already have an account?")
        already.setStyleSheet("color:#6B7280;font-size:13px;background:transparent;border:none;")
        login_row.addWidget(already)
        login_link = QPushButton("Sign In")
        login_link.setFlat(True)
        login_link.setCursor(Qt.CursorShape.PointingHandCursor)
        login_link.setStyleSheet("""
            QPushButton {
                color: #1E40AF;
                font-size: 13px;
                font-weight: 700;
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                color: #1E3A8A;
            }
        """)
        login_link.clicked.connect(self.show)
        login_row.addWidget(login_link)
        login_row.addStretch()
        content.addLayout(login_row)

        row.addWidget(signup_card)
        row.addStretch()
        main_layout.addLayout(row)
        main_layout.addStretch()

        super().show()
        QTimer.singleShot(50, self._position_exit_button)

    def select_signup_role(self, role, card):
        self.selected_signup_role = role
        for item in getattr(self, "signup_role_cards", []):
            if "card" in item and "button" in item:
                item["button"].set_selected(item["card"] is card)

    def hide_signup_fields(self):
        pass


    def update_signup_password_strength(self, *_):
        password = self.signup_password_entry.text()
        strength = 0
        criteria = []
        if len(password) >= 8:
            strength += 1
            criteria.append("8+ characters")
        if re.search(r'[A-Z]', password):
            strength += 1
            criteria.append("Uppercase")
        if re.search(r'[0-9]', password):
            strength += 1
            criteria.append("Number")
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            strength += 1
            criteria.append("Special char")

        colors = {0: '#E5E7EB', 1: '#EF4444', 2: '#F97316', 3: '#EAB308', 4: '#22C55E'}
        names = {0: '', 1: 'Weak', 2: 'Fair', 3: 'Good', 4: 'Strong'}

        self.signup_strength_meter.setStyleSheet(
            f"background:{colors[strength]};border-radius:3px;border:none;"
        )
        if password:
            text = names[strength]
            if criteria:
                text += f"  ({', '.join(criteria)})"
            self.signup_strength_label.setText(text)
            self.signup_strength_label.setStyleSheet(
                f"color:{colors[strength]};font-size:11px;background:transparent;border:none;"
            )
        else:
            self.signup_strength_label.setText("")
            self.signup_strength_label.setStyleSheet("color:#9CA3AF;font-size:11px;background:transparent;border:none;")
            self.signup_strength_meter.setStyleSheet("background:#E5E7EB;border-radius:3px;border:none;")

    def do_signup(self):
        name = self.signup_name_entry.text().strip()
        username = self.signup_username_entry.text().strip()
        email = self.signup_email_entry.text().strip()
        phone = self.signup_phone_entry.text().strip()
        password = self.signup_password_entry.text()
        confirm = self.signup_confirm_entry.text()

        # Validation
        if not self.selected_signup_role:
            from dashboard_gui.styled_dialog import StyledDialog
            StyledDialog.show_message(self, "Error", "Please select a role.", "error")
            return
        if not name:
            from dashboard_gui.styled_dialog import StyledDialog
            StyledDialog.show_message(self, "Error", "Please enter your full name.", "error")
            return
        if not username:
            from dashboard_gui.styled_dialog import StyledDialog
            StyledDialog.show_message(self, "Error", "Please enter a username.", "error")
            return
        if len(username) < 3:
            from dashboard_gui.styled_dialog import StyledDialog
            StyledDialog.show_message(self, "Error", "Username must be at least 3 characters.", "error")
            return
        if not email or '@' not in email:
            from dashboard_gui.styled_dialog import StyledDialog
            StyledDialog.show_message(self, "Error", "Please enter a valid email address.", "error")
            return
        if not phone:
            from dashboard_gui.styled_dialog import StyledDialog
            StyledDialog.show_message(self, "Error", "Please enter a phone number.", "error")
            return
        # Phone number validation: must be exactly 11 digits, no letters
        phone_clean = phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        if not phone_clean.isdigit():
            from dashboard_gui.styled_dialog import StyledDialog
            StyledDialog.show_message(self, "Error", "Phone number cannot contain letters. Please enter digits only.", "error")
            return
        if len(phone_clean) != 11:
            from dashboard_gui.styled_dialog import StyledDialog
            StyledDialog.show_message(self, "Error", "Phone number must be exactly 11 digits.", "error")
            return
        if not password:
            from dashboard_gui.styled_dialog import StyledDialog
            StyledDialog.show_message(self, "Error", "Please enter a password.", "error")
            return
        if len(password) < 8:
            from dashboard_gui.styled_dialog import StyledDialog
            StyledDialog.show_message(self, "Error", "Password must be at least 8 characters.", "error")
            return
        if password != confirm:
            from dashboard_gui.styled_dialog import StyledDialog
            StyledDialog.show_message(self, "Error", "Passwords do not match.", "error")
            return
        if not self.terms_check.isChecked():
            from dashboard_gui.styled_dialog import StyledDialog
            StyledDialog.show_message(self, "Error", "Please agree to the Terms and Conditions.", "error")
            return

        # Check if username exists
        if self.db.check_username_exists(username):
            from dashboard_gui.styled_dialog import StyledDialog
            StyledDialog.show_message(self, "Error", "Username already exists. Please choose a different one.", "error")
            return

        # Check if email exists
        if self.db.email_exists(email):
            from dashboard_gui.styled_dialog import StyledDialog
            StyledDialog.show_message(self, "Error", "An account with this email already exists.", "error")
            return

        # Create user
        user_id = self.db.create_user(username, password, self.selected_signup_role, email, name)

        if user_id:
            # Save phone number if column exists
            try:
                self.db.execute_query(
                    "UPDATE users SET phone = %s WHERE user_id = %s",
                    (phone, user_id)
                )
            except Exception:
                pass

            from dashboard_gui.styled_dialog import StyledDialog
            StyledDialog.show_message(
                self,
                "Account Created",
                "Your account has been created successfully.\nYou can now log in with your credentials.",
                "success"
            )
            self.show()
        else:
            from dashboard_gui.styled_dialog import StyledDialog
            StyledDialog.show_message(self, "Error", "Failed to create account. Please try again.", "error")
    
    # -------------------------------------------------------------------------
    def update_signup_password_strength(self, *_):
        password = self.signup_password_entry.text()
        strength = 0
        criteria = []
        if len(password) >= 8:
            strength += 25
            criteria.append("✓ 8+ characters")
        if re.search(r'[A-Z]', password):
            strength += 25
            criteria.append("✓ Uppercase")
        if re.search(r'[0-9]', password):
            strength += 25
            criteria.append("✓ Number")
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            strength += 25
            criteria.append("✓ Special")
        
        if strength <= 0:
            self.signup_strength_label.setText("")
            self.signup_strength_meter.setStyleSheet("background:#E5E7EB;border-radius:3px;")
            return
        
        if strength <= 25:
            color, text = "#DC3545", "Weak"
        elif strength <= 50:
            color, text = "#FFC107", "Fair"
        elif strength <= 75:
            color, text = "#17A2B8", "Good"
        else:
            color, text = "#28A745", "Strong"
        
        self.signup_strength_meter.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {color}, stop:{strength/100} {color}, "
            f"stop:{strength/100 + 0.001} #E5E7EB, stop:1 #E5E7EB);"
            f"border-radius:3px;"
        )
        criteria_text = " • ".join(criteria) if criteria else ""
        self.signup_strength_label.setText(f"{text} - {criteria_text}")
        self.signup_strength_label.setStyleSheet(f"color:{color};font-size:11px;background:transparent;")
    
    # -------------------------------------------------------------------------
    def select_signup_role(self, role, card):
        """Handle role selection in signup form"""
        self.selected_signup_role = role
        for item in getattr(self, "signup_role_cards", []):
            if "card" in item:
                item["card"].set_selected(item["card"] is card)
    
    # -------------------------------------------------------------------------
    def do_signup(self):
        if not getattr(self, "selected_signup_role", None):
            self.show_error_notification("Please select a role first")
            return
        name = self.signup_name_entry.text().strip()
        username = self.signup_username_entry.text().strip()
        password = self.signup_password_entry.text()
        confirm = self.signup_confirm_entry.text()
        email = self.signup_email_entry.text().strip()
        
        if not all([name, username, password]):
            self.show_error_notification("Please fill in all required fields")
            return
        if password != confirm:
            self.show_error_notification("Passwords do not match")
            return
        if len(password) < 8:
            self.show_error_notification("Password must be at least 8 characters")
            return
        if not self.terms_check.isChecked():
            self.show_error_notification("Please agree to the Terms and Conditions")
            return
        if self.db.check_username_exists(username):
            self.show_error_notification("Username already exists")
            return
        
        user_id = self.db.create_user(
            username, password, self.selected_signup_role, email, name
        )
        if user_id:
            self.show_success_notification(f"Account created successfully! Welcome, {name}!")
            QTimer.singleShot(1500, self.show)
        else:
            self.show_error_notification("Failed to create account. Please try again.")
    
    # -------------------------------------------------------------------------
    def _toast(self, title, message, bg):
        toast = QWidget(self, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        toast.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        toast.setStyleSheet(f"background:{bg};border-radius:8px;")
        toast.setFixedSize(360, 80)
        
        v = QVBoxLayout(toast)
        v.setContentsMargins(15, 8, 15, 8)
        t = QLabel(title)
        t.setStyleSheet("color:white;font-size:12px;font-weight:700;background:transparent;")
        m = QLabel(message)
        m.setWordWrap(True)
        m.setStyleSheet("color:white;font-size:11px;background:transparent;")
        v.addWidget(t)
        v.addWidget(m)
        
        geo = self.geometry()
        toast.move(geo.x() + geo.width() - 380, geo.y() + 20)
        toast.show()
        QTimer.singleShot(3000, toast.close)
    
    def show_error_notification(self, message):
        self._toast("❌ Error", message, Config.COLORS.get("danger", "#DC3545"))
    
    def show_success_notification(self, message):
        self._toast("✓ Success", message, Config.COLORS.get("success", "#28A745"))
    
    # -------------------------------------------------------------------------
    def show_dashboard(self, current_user):
        self.showNormal()
        self.hide()
        self.dashboard = DashboardGUI(self.db, current_user)
        self.dashboard.show()
    
    def exit(self):
        if self.db:
            self.db.close()
        QApplication.quit()
    
    def clear_window(self):
        old = self.centralWidget()
        if old is not None:
            old.deleteLater()