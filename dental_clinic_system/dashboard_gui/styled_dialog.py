"""
StyledDialog - PyQt6
Reusable solid white popup dialog.
Fixes transparency, unreadable text, and background bleeding issues.
"""

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect, QWidget
)


class StyledDialog(QDialog):
    """Solid white dialog that never inherits transparent parent backgrounds."""

    def __init__(self, parent=None, title="Message", message="", dialog_type="info"):
        """
        Args:
            parent: Parent widget (won't inherit its background).
            title: Dialog window title.
            message: Main message text.
            dialog_type: "info", "success", "error", or "warning".
        """
        # Pass None as parent to prevent inheriting transparent stylesheets.
        # We manually center it later.
        super().__init__(None)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setFixedSize(440, 240)
        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        # Force solid white background on the dialog itself
        self.setStyleSheet("background-color: #FFFFFF; border: none;")
        self._setup_ui(title, message, dialog_type)
        self._center_on_parent(parent)

    def _center_on_parent(self, parent):
        """Center this dialog over the parent widget."""
        if parent:
            parent_rect = parent.window().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

    def _setup_ui(self, title, message, dialog_type):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Inner card
        card = QFrame()
        card.setStyleSheet("background-color: #FFFFFF; border: none; border-radius: 16px;")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(0)

        # Icon row
        icon_row = QHBoxLayout()
        icon_row.setSpacing(16)

        icon_config = {
            "info":     ("#1E3A8A", "#EFF6FF", "?"),
            "success":  ("#15803D", "#DCFCE7", "!"),
            "error":    ("#DC2626", "#FEE2E2", "!"),
            "warning":  ("#D97706", "#FEF3C7", "!"),
        }
        border_color, bg_color, icon_text = icon_config.get(dialog_type, icon_config["info"])

        icon_frame = QFrame()
        icon_frame.setFixedSize(48, 48)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 14px;
            }}
        """)
        icon_label = QLabel(icon_text)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"""
            color: {border_color};
            font-size: 22px;
            font-weight: 800;
            background: transparent;
            border: none;
        """)
        icon_inner = QVBoxLayout(icon_frame)
        icon_inner.setContentsMargins(0, 0, 0, 0)
        icon_inner.addWidget(icon_label)
        icon_row.addWidget(icon_frame)

        # Title label
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: #1F2937;
            font-size: 17px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        title_row = QVBoxLayout()
        title_row.setSpacing(4)
        title_row.addWidget(title_label)
        icon_row.addLayout(title_row)
        icon_row.addStretch()
        card_layout.addLayout(icon_row)
        card_layout.addSpacing(20)

        # Message label
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setMinimumHeight(40)
        msg_label.setStyleSheet("""
            color: #4B5563;
            font-size: 14px;
            line-height: 1.5;
            background: transparent;
            border: none;
        """)
        card_layout.addWidget(msg_label)
        card_layout.addSpacing(28)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setFixedHeight(42)
        ok_btn.setFixedWidth(120)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setText("OK")
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {border_color};
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 700;
                border: none;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: {border_color};
            }}
            QPushButton:pressed {{
                background-color: {border_color};
            }}
        """)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)

        btn_row.addStretch()
        card_layout.addLayout(btn_row)

        main_layout.addWidget(card)

    def show_message(parent, title, message, dialog_type="info"):
        """Static helper to show a styled dialog."""
        dialog = StyledDialog(parent, title, message, dialog_type)
        dialog.exec()