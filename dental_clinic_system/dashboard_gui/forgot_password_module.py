"""
Forgot Password Module - PyQt6
Solid white cards matching login style, real SMTP, safe QPainter
"""

import random
import re
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QGraphicsDropShadowEffect,
    QStackedWidget
)


# =============================================================================
# SAFE CUSTOM PAINTED ICON
# =============================================================================

class SafeIcon(QWidget):
    """Custom painted icon with safe paintEvent guards"""
    LOCK = 0
    SHIELD = 1
    PERSON = 2
    MAIL = 3
    PHONE = 4
    EYE_OPEN = 5
    EYE_CLOSED = 6
    CHECK_LARGE = 7
    KEY = 8
    CODE_HASH = 9

    def __init__(self, icon_id, size=48, color=None, bg_circle=False, parent=None):
        super().__init__(parent)
        self.icon_id = icon_id
        self._color = color if color else QColor('#64748B')
        self._bg = bg_circle
        self.setFixedSize(size, size)

    def set_icon(self, icon_id):
        self.icon_id = icon_id
        self.update()

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

        if self._bg:
            p.setBrush(QBrush(QColor('#F1F5F9')))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(cx, cy), 22 * s, 22 * s)

        pen = QPen(c, 2.2 * s)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        if self.icon_id == self.LOCK:
            self._draw_lock(p, cx, cy, s, c, pen)
        elif self.icon_id == self.SHIELD:
            self._draw_shield(p, cx, cy, s, c, pen)
        elif self.icon_id == self.PERSON:
            self._draw_person(p, cx, cy, s, c)
        elif self.icon_id == self.MAIL:
            self._draw_mail(p, cx, cy, s, c, pen)
        elif self.icon_id == self.PHONE:
            self._draw_phone(p, cx, cy, s, c, pen)
        elif self.icon_id == self.EYE_OPEN:
            self._draw_eye_open(p, cx, cy, s, c, pen)
        elif self.icon_id == self.EYE_CLOSED:
            self._draw_eye_closed(p, cx, cy, s, c, pen)
        elif self.icon_id == self.CHECK_LARGE:
            self._draw_check_large(p, cx, cy, s, c, pen)
        elif self.icon_id == self.KEY:
            self._draw_key(p, cx, cy, s, c, pen)
        elif self.icon_id == self.CODE_HASH:
            self._draw_code_hash(p, cx, cy, s, c, pen)

        p.end()

    def _draw_lock(self, p, cx, cy, s, c, pen):
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(QRectF(cx - 7*s, cy - 16*s, 14*s, 16*s), 0, 180*16)
        p.setBrush(QBrush(c))
        p.drawRoundedRect(QRectF(cx - 10*s, cy - 2*s, 20*s, 16*s), 3*s, 3*s)
        p.setBrush(QBrush(QColor('#F1F5F9')))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy + 3*s), 2.5*s, 2.5*s)
        p.drawRect(QRectF(cx - 1.2*s, cy + 4.5*s, 2.4*s, 5*s))

    def _draw_shield(self, p, cx, cy, s, c, pen):
        path = QPainterPath()
        path.moveTo(cx, cy - 18*s)
        path.cubicTo(cx + 14*s, cy - 16*s, cx + 16*s, cy - 4*s, cx + 16*s, cy)
        path.cubicTo(cx + 16*s, cy + 10*s, cx, cy + 20*s, cx, cy + 20*s)
        path.cubicTo(cx, cy + 20*s, cx - 16*s, cy + 10*s, cx - 16*s, cy)
        path.cubicTo(cx - 16*s, cy - 4*s, cx - 14*s, cy - 16*s, cx, cy - 18*s)
        path.closeSubpath()
        p.setPen(pen)
        p.setBrush(QBrush(QColor(c.red(), c.green(), c.blue(), 30)))
        p.drawPath(path)
        p.setPen(QPen(c, 2.5*s))
        p.setBrush(Qt.BrushStyle.NoBrush)
        chk = QPainterPath()
        chk.moveTo(cx - 6*s, cy)
        chk.lineTo(cx - 2*s, cy + 5*s)
        chk.lineTo(cx + 7*s, cy - 5*s)
        p.drawPath(chk)

    def _draw_person(self, p, cx, cy, s, c):
        p.setBrush(QBrush(c))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy - 8*s), 6*s, 6.5*s)
        body = QPainterPath()
        body.moveTo(cx - 16*s, cy + 16*s)
        body.cubicTo(cx - 16*s, cy + 2*s, cx - 8*s, cy - 1*s, cx, cy - 1*s)
        body.cubicTo(cx + 8*s, cy - 1*s, cx + 16*s, cy + 2*s, cx + 16*s, cy + 16*s)
        body.closeSubpath()
        p.drawPath(body)

    def _draw_mail(self, p, cx, cy, s, c, pen):
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(cx - 16*s, cy - 10*s, 32*s, 22*s), 3*s, 3*s)
        flap = QPainterPath()
        flap.moveTo(cx - 16*s, cy - 10*s)
        flap.lineTo(cx, cy + 2*s)
        flap.lineTo(cx + 16*s, cy - 10*s)
        p.drawPath(flap)

    def _draw_phone(self, p, cx, cy, s, c, pen):
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(cx - 9*s, cy - 16*s, 18*s, 32*s), 3*s, 3*s)
        p.setBrush(QBrush(QColor(c.red(), c.green(), c.blue(), 25)))
        p.drawRoundedRect(QRectF(cx - 6*s, cy - 11*s, 12*s, 20*s), 1.5*s, 1.5*s)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(QRectF(cx - 3*s, cy + 12*s, 6*s, 1.5*s))

    def _draw_eye_open(self, p, cx, cy, s, c, pen):
        p.setPen(pen)
        top = QPainterPath()
        top.moveTo(QPointF(cx - 16*s, cy))
        top.cubicTo(QPointF(cx - 10*s, cy - 12*s), QPointF(cx, cy - 12*s), QPointF(cx + 16*s, cy))
        p.drawPath(top)

        bot = QPainterPath()
        bot.moveTo(QPointF(cx - 16*s, cy))
        bot.cubicTo(QPointF(cx - 10*s, cy + 12*s), QPointF(cx, cy + 12*s), QPointF(cx + 16*s, cy))
        p.drawPath(bot)

        p.setBrush(QBrush(c))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), 5*s, 5*s)

    def _draw_eye_closed(self, p, cx, cy, s, c, pen):
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        arc = QPainterPath()
        arc.moveTo(QPointF(cx - 16*s, cy))
        arc.cubicTo(QPointF(cx - 8*s, cy - 8*s), QPointF(cx + 8*s, cy - 8*s), QPointF(cx + 16*s, cy))
        p.drawPath(arc)

        slash = QPainterPath()
        slash.moveTo(QPointF(cx - 10*s, cy + 8*s))
        slash.lineTo(QPointF(cx + 10*s, cy - 8*s))
        p.drawPath(slash)

    def _draw_check_large(self, p, cx, cy, s, c, pen):
        w = self.width()
        h = self.height()
        sc = min(w, h) / 80.0 if w > 4 else 1.0

        radius = 30 * sc
        p.setBrush(QBrush(QColor(c.red(), c.green(), c.blue(), 25)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), radius, radius)
        p.setPen(QPen(c, 2.5*sc))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), radius, radius)
        chk = QPainterPath()
        chk.moveTo(cx - 10*sc, cy + sc)
        chk.lineTo(cx - 3*sc, cy + 8*sc)
        chk.lineTo(cx + 11*sc, cy - 6*sc)
        pen2 = QPen(c, 3*sc)
        pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen2.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen2)
        p.drawPath(chk)

    def _draw_key(self, p, cx, cy, s, c, pen):
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx - 8*s, cy - 4*s), 7*s, 7*s)
        shaft = QPainterPath()
        shaft.moveTo(cx - s, cy - 4*s)
        shaft.lineTo(cx + 16*s, cy - 4*s)
        p.drawPath(shaft)
        t1 = QPainterPath()
        t1.moveTo(cx + 8*s, cy - 4*s)
        t1.lineTo(cx + 8*s, cy + 2*s)
        t1.lineTo(cx + 12*s, cy + 2*s)
        t1.lineTo(cx + 12*s, cy - 4*s)
        p.drawPath(t1)
        t2 = QPainterPath()
        t2.moveTo(cx + 14*s, cy - 4*s)
        t2.lineTo(cx + 14*s, cy + s)
        t2.lineTo(cx + 18*s, cy + s)
        t2.lineTo(cx + 18*s, cy - 4*s)
        p.drawPath(t2)

    def _draw_code_hash(self, p, cx, cy, s, c, pen):
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(cx - 10*s, cy - 10*s), QPointF(cx - 4*s, cy - 14*s))
        p.drawLine(QPointF(cx - 10*s, cy + 10*s), QPointF(cx - 4*s, cy + 14*s))
        p.drawLine(QPointF(cx + 10*s, cy - 10*s), QPointF(cx + 4*s, cy - 14*s))
        p.drawLine(QPointF(cx + 10*s, cy + 10*s), QPointF(cx + 4*s, cy + 14*s))
        p.drawLine(QPointF(cx - 12*s, cy), QPointF(cx + 12*s, cy))


# =============================================================================
# RADIO INDICATOR - Safe custom painted widget
# =============================================================================

class RadioIndicator(QWidget):
    """Custom painted radio/check indicator with its own paintEvent"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self._checked = False
        self._disabled = False

    def set_state(self, checked, disabled):
        self._checked = checked
        self._disabled = disabled
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
        r = 9

        if self._checked:
            p.setBrush(QBrush(QColor('#1E3A8A')))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(cx, cy), r, r)
            pen = QPen(QColor('#FFFFFF'), 2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            path = QPainterPath()
            path.moveTo(cx - 4, cy)
            path.lineTo(cx - 1, cy + 3)
            path.lineTo(cx + 5, cy - 3)
            p.drawPath(path)
        else:
            color = QColor('#E2E8F0') if self._disabled else QColor('#CBD5E1')
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(color, 2))
            p.drawEllipse(QPointF(cx, cy), r, r)

        p.end()


# =============================================================================
# OTP INPUT BOX
# =============================================================================

class OTPLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(56, 65)
        self.setMaxLength(1)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_empty()

    def _apply_empty(self):
        self.setStyleSheet("""
            QLineEdit {
                background-color: #F8FAFC;
                border: 2px solid #E2E8F0;
                border-radius: 12px;
                font-size: 26px;
                font-weight: 700;
                color: #1E293B;
            }
            QLineEdit:focus {
                border-color: #1E3A8A;
                background-color: #FFFFFF;
            }
        """)

    def _apply_filled(self):
        self.setStyleSheet("""
            QLineEdit {
                background-color: #EFF6FF;
                border: 2px solid #1E3A8A;
                border-radius: 12px;
                font-size: 26px;
                font-weight: 700;
                color: #1E3A8A;
            }
            QLineEdit:focus {
                border-color: #1E40AF;
                background-color: #FFFFFF;
            }
        """)

    def _apply_error(self):
        self.setStyleSheet("""
            QLineEdit {
                background-color: #FEF2F2;
                border: 2px solid #EF4444;
                border-radius: 12px;
                font-size: 26px;
                font-weight: 700;
                color: #EF4444;
            }
        """)

    def reset_style(self):
        if self.text():
            self._apply_filled()
        else:
            self._apply_empty()


# =============================================================================
# PASSWORD STRENGTH BAR
# =============================================================================

class PasswordStrengthBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(8)
        self._strength = 0

    def set_strength(self, val):
        self._strength = max(0, min(4, val))
        self.update()

    def paintEvent(self, event):
        if self.width() < 2 or self.height() < 2:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor('#E2E8F0')))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect(), 4, 4)
        if self._strength > 0:
            colors = ['#EF4444', '#F97316', '#EAB308', '#22C55E']
            widths = [0.25, 0.50, 0.75, 1.0]
            p.setBrush(QBrush(QColor(colors[self._strength - 1])))
            bar_w = int(self.width() * widths[self._strength - 1])
            p.drawRoundedRect(0, 0, bar_w, self.height(), 4, 4)
        p.end()


# =============================================================================
# RECOVERY METHOD CARD
# =============================================================================

class RecoveryMethodCard(QFrame):
    clicked = None

    def __init__(self, method_id, icon_id, title, subtitle, tag="", disabled=False, parent=None):
        super().__init__(parent)
        self.method_id = method_id
        self._selected = False
        self._disabled = disabled

        self.setFixedHeight(90)
        if self._disabled:
            self.setCursor(Qt.CursorShape.ForbiddenCursor)
        else:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(15)

        icon = SafeIcon(icon_id, size=50, bg_circle=True)
        if self._disabled:
            icon.set_color(QColor('#CBD5E1'))
        layout.addWidget(icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        text_col.setContentsMargins(0, 0, 0, 0)

        if tag:
            t = QLabel(tag)
            t.setStyleSheet("color:#10B981;font-size:10px;font-weight:700;letter-spacing:0.5px;background:transparent;border:none;")
            text_col.addWidget(t)

        t2 = QLabel(title)
        if self._disabled:
            t2.setStyleSheet("color:#94A3B8;font-size:15px;font-weight:700;background:transparent;border:none;")
        else:
            t2.setStyleSheet("color:#1E293B;font-size:15px;font-weight:700;background:transparent;border:none;")
        text_col.addWidget(t2)

        t3 = QLabel(subtitle)
        if self._disabled:
            t3.setStyleSheet("color:#94A3B8;font-size:13px;font-style:italic;background:transparent;border:none;")
        else:
            t3.setStyleSheet("color:#64748B;font-size:13px;background:transparent;border:none;")
        text_col.addWidget(t3)

        layout.addLayout(text_col)
        layout.addStretch()

        self.indicator = RadioIndicator()
        self.indicator.set_state(False, self._disabled)
        layout.addWidget(self.indicator)

    def _apply_style(self):
        if self._disabled:
            self.setStyleSheet("""
                QFrame {
                    background-color: #F8FAFC;
                    border: 2px solid #E2E8F0;
                    border-radius: 14px;
                }
            """)
        elif self._selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #EFF6FF;
                    border: 2px solid #1E3A8A;
                    border-radius: 14px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border: 2px solid #E2E8F0;
                    border-radius: 14px;
                }
                QFrame:hover {
                    border-color: #94A3B8;
                    background-color: #F8FAFC;
                }
            """)

    def set_selected(self, selected):
        if self._disabled:
            return
        self._selected = selected
        self._apply_style()
        self.indicator.set_state(selected, False)

    def mousePressEvent(self, event):
        if self.clicked and not self._disabled:
            self.clicked()
        super().mousePressEvent(event)


# =============================================================================
# MAIN FORGOT PASSWORD FLOW
# =============================================================================

class ForgotPasswordFlow(QWidget):
    backToLogin = None

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_username = None
        self.selected_method = None
        self.verification_code = None
        self.user_real_email = None
        self.user_real_phone = None
        self.resend_timer = QTimer(self)
        self.resend_seconds = 0
        self._setup()

    # ------------------------------------------------------------------ setup
    def _setup(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card = QFrame()
        self.card.setFixedSize(580, 720)
        self.card.setObjectName("fpCard")
        self.card.setStyleSheet("""
            #fpCard {
                background-color: white;
                border-radius: 20px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(50)
        shadow.setOffset(0, 15)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.card.setGraphicsEffect(shadow)

        card_lay = QVBoxLayout(self.card)
        card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color:white;")
        card_lay.addWidget(self.stack)

        self.stack.addWidget(self._page_username())
        self.stack.addWidget(self._page_method())
        self.stack.addWidget(self._page_code())
        self.stack.addWidget(self._page_reset())
        self.stack.addWidget(self._page_success())

        outer.addWidget(self.card)

        if self.db and self.db.is_connected():
            self.db.setup_recovery_columns()

    # -------------------------------------------------------------- helpers
    def _btn_primary(self, text):
        b = QPushButton(text)
        b.setFixedHeight(52)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet("""
            QPushButton {
                background-color: #1E3A8A;
                color: white;
                font-size: 15px;
                font-weight: 700;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #1E40AF;
            }
            QPushButton:pressed {
                background-color: #1E3A8A;
            }
            QPushButton:disabled {
                background-color: #94A3B8;
                color: #CBD5E1;
            }
        """)
        return b

    def _btn_back(self, text="Back to Login"):
        b = QPushButton(text)
        b.setFlat(True)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet("""
            QPushButton {
                color: #64748B;
                font-size: 13px;
                font-weight: 700;
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                color: #1E3A8A;
            }
        """)
        return b

    def _input(self, placeholder, icon_id=None, password=False):
        frame = QFrame()
        frame.setFixedHeight(52)
        frame.setObjectName("fpInput")
        frame.setStyleSheet("""
            #fpInput {
                background-color: #F3F4F6;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
            }
        """)
        h = QHBoxLayout(frame)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(10)

        if icon_id is not None:
            ic = SafeIcon(icon_id, size=22)
            ic.setStyleSheet("background:transparent;border:none;")
            h.addWidget(ic)

        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #1F2937;
                font-size: 14px;
            }
        """)

        eye = None
        if password:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
            eye = SafeIcon(SafeIcon.EYE_CLOSED, size=22)
            eye.setCursor(Qt.CursorShape.PointingHandCursor)
            eye.setStyleSheet("background:transparent;border:none;")
            vis = [False]

            def toggle(e=eye, le=edit, v=vis):
                if v[0]:
                    le.setEchoMode(QLineEdit.EchoMode.Password)
                    e.set_icon(SafeIcon.EYE_CLOSED)
                    e.set_color(QColor('#64748B'))
                    v[0] = False
                else:
                    le.setEchoMode(QLineEdit.EchoMode.Normal)
                    e.set_icon(SafeIcon.EYE_OPEN)
                    e.set_color(QColor('#1E3A8A'))
                    v[0] = True

            eye.mousePressEvent = lambda ev: toggle()
            h.addWidget(eye)

        h.addWidget(edit)
        return frame, edit

    def _header(self, icon_id, title, subtitle):
        w = QWidget()
        w.setStyleSheet("background:white;border:none;")
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(12)

        ic = SafeIcon(icon_id, size=64, bg_circle=True)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(ic)
        row.addStretch()
        v.addLayout(row)

        t = QLabel(title)
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setWordWrap(True)
        t.setStyleSheet("color:#1F2937;font-size:28px;font-weight:700;background:transparent;border:none;")
        v.addWidget(t)

        s = QLabel(subtitle)
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s.setWordWrap(True)
        s.setMaximumWidth(420)
        s.setStyleSheet("color:#6B7280;font-size:14px;background:transparent;border:none;")
        v.addWidget(s)
        return w

    # --------------------------------------------------------- PAGE 1: USERNAME
    def _page_username(self):
        page = QWidget()
        page.setStyleSheet("background:white;border:none;")
        v = QVBoxLayout(page)
        v.setContentsMargins(55, 55, 55, 45)
        v.setSpacing(0)

        v.addWidget(self._header(SafeIcon.LOCK, "Forgot Password?",
                                "No worries! Enter your username to begin the recovery process."))
        v.addSpacing(35)

        lbl = QLabel("Username")
        lbl.setStyleSheet("color:#1F2937;font-size:14px;font-weight:700;background:transparent;border:none;")
        v.addWidget(lbl)
        v.addSpacing(10)

        self.fp_username_frame, self.fp_username_edit = self._input("Enter your username", SafeIcon.PERSON)
        v.addWidget(self.fp_username_frame)
        v.addSpacing(10)

        self.fp_username_err = QLabel("")
        self.fp_username_err.setStyleSheet("color:#EF4444;font-size:13px;background:transparent;border:none;")
        self.fp_username_err.setVisible(False)
        v.addWidget(self.fp_username_err)

        v.addStretch()

        btn = self._btn_primary("Continue")
        btn.clicked.connect(self._on_continue)
        v.addWidget(btn)
        v.addSpacing(25)

        back = self._btn_back("Back to Login")
        back.clicked.connect(lambda: self.backToLogin() if self.backToLogin else None)
        v.addWidget(back)

        self.fp_username_edit.returnPressed.connect(self._on_continue)
        return page

    # ------------------------------------------------- PAGE 2: RECOVERY METHOD
    def _page_method(self):
        page = QWidget()
        page.setStyleSheet("background:white;border:none;")
        v = QVBoxLayout(page)
        v.setContentsMargins(55, 55, 55, 45)
        v.setSpacing(0)

        v.addWidget(self._header(SafeIcon.SHIELD, "Verify Your Identity",
                                "Choose how you would like to receive your recovery code."))
        v.addSpacing(30)

        self.fp_method_box = QVBoxLayout()
        self.fp_method_box.setSpacing(12)
        self.fp_method_box.setContentsMargins(0, 0, 0, 0)
        v.addLayout(self.fp_method_box)

        v.addStretch()

        self.fp_send_btn = self._btn_primary("Send Recovery Code")
        self.fp_send_btn.setEnabled(False)
        self.fp_send_btn.clicked.connect(self._on_send_code)
        v.addWidget(self.fp_send_btn)
        v.addSpacing(25)

        back = self._btn_back("Back")
        back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        v.addWidget(back)

        info = QLabel("This recovery step ensures your patient records remain confidential. The code expires in 15 minutes.")
        info.setWordWrap(True)
        info.setStyleSheet("color:#6B7280;font-size:12px;background:#F3F4F6;padding:15px;border-radius:10px;border:1px solid #E5E7EB;")
        v.addWidget(info)

        return page

    # --------------------------------------------------- PAGE 3: ENTER CODE
    def _page_code(self):
        page = QWidget()
        page.setStyleSheet("background:white;border:none;")
        v = QVBoxLayout(page)
        v.setContentsMargins(55, 55, 55, 45)
        v.setSpacing(0)

        self.fp_code_header = self._header(SafeIcon.CODE_HASH, "Enter Recovery Code",
                                           "We've sent a 6-digit code to your registered email address.")
        v.addWidget(self.fp_code_header)
        v.addSpacing(35)

        otp_row = QHBoxLayout()
        otp_row.setSpacing(10)
        otp_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.fp_otp_boxes = []
        for i in range(6):
            box = OTPLineEdit()
            box.textChanged.connect(lambda txt, idx=i: self._otp_changed(txt, idx))
            box.keyPressEvent = lambda ev, idx=i: self._otp_key(ev, idx)
            otp_row.addWidget(box)
            self.fp_otp_boxes.append(box)
        v.addLayout(otp_row)
        v.addSpacing(10)

        self.fp_code_err = QLabel("")
        self.fp_code_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fp_code_err.setStyleSheet("color:#EF4444;font-size:13px;background:transparent;border:none;")
        self.fp_code_err.setVisible(False)
        v.addWidget(self.fp_code_err)

        v.addStretch()

        self.fp_verify_btn = self._btn_primary("Verify Code")
        self.fp_verify_btn.clicked.connect(self._on_verify)
        v.addWidget(self.fp_verify_btn)
        v.addSpacing(20)

        rr = QHBoxLayout()
        rr.addStretch()
        rr.addWidget(QLabel("Didn't receive the code?"))
        rr.itemAt(rr.count()-1).widget().setStyleSheet("color:#6B7280;font-size:13px;background:transparent;border:none;")

        self.fp_resend_btn = self._btn_back("Resend Code")
        self.fp_resend_btn.setStyleSheet("""
            QPushButton {
                color: #1E3A8A;
                font-size: 13px;
                font-weight: 700;
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                color: #1E40AF;
            }
            QPushButton:disabled {
                color: #94A3B8;
            }
        """)
        self.fp_resend_btn.clicked.connect(self._on_resend)
        rr.addWidget(self.fp_resend_btn)
        rr.addStretch()
        v.addLayout(rr)
        v.addStretch()

        back = self._btn_back("Back")
        back.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        v.addWidget(back)

        self.resend_timer.timeout.connect(self._tick_resend)
        return page

    # ------------------------------------------------- PAGE 4: RESET PASSWORD
    def _page_reset(self):
        page = QWidget()
        page.setStyleSheet("background:white;border:none;")
        v = QVBoxLayout(page)
        v.setContentsMargins(55, 55, 55, 45)
        v.setSpacing(0)

        v.addWidget(self._header(SafeIcon.KEY, "Reset Your Password",
                                "Please create a new secure password for your account."))
        v.addSpacing(35)

        v.addWidget(QLabel("New Password"))
        v.itemAt(v.count()-1).widget().setStyleSheet("color:#1F2937;font-size:14px;font-weight:700;background:transparent;border:none;")
        v.addSpacing(10)

        self.fp_new_frame, self.fp_new_edit = self._input("Enter new password", SafeIcon.LOCK, password=True)
        v.addWidget(self.fp_new_frame)
        v.addSpacing(5)

        hint = QLabel("Must be at least 8 characters long.")
        hint.setStyleSheet("color:#9CA3AF;font-size:12px;background:transparent;border:none;")
        v.addWidget(hint)
        v.addSpacing(5)

        self.fp_str_bar = PasswordStrengthBar()
        v.addWidget(self.fp_str_bar)
        v.addSpacing(3)

        self.fp_str_lbl = QLabel("")
        self.fp_str_lbl.setStyleSheet("color:#6B7280;font-size:12px;background:transparent;border:none;")
        v.addWidget(self.fp_str_lbl)
        v.addSpacing(20)

        v.addWidget(QLabel("Confirm New Password"))
        v.itemAt(v.count()-1).widget().setStyleSheet("color:#1F2937;font-size:14px;font-weight:700;background:transparent;border:none;")
        v.addSpacing(10)

        self.fp_conf_frame, self.fp_conf_edit = self._input("Confirm new password", SafeIcon.LOCK, password=True)
        v.addWidget(self.fp_conf_frame)
        v.addSpacing(5)

        self.fp_match_lbl = QLabel("")
        self.fp_match_lbl.setStyleSheet("color:#6B7280;font-size:12px;background:transparent;border:none;")
        self.fp_match_lbl.setVisible(False)
        v.addWidget(self.fp_match_lbl)

        v.addStretch()

        self.fp_reset_btn = self._btn_primary("Reset Password")
        self.fp_reset_btn.clicked.connect(self._on_reset)
        v.addWidget(self.fp_reset_btn)
        v.addSpacing(25)

        back = self._btn_back("Back to Login")
        back.clicked.connect(lambda: self.backToLogin() if self.backToLogin else None)
        v.addWidget(back)

        self.fp_new_edit.textChanged.connect(self._pw_changed)
        self.fp_conf_edit.textChanged.connect(self._conf_changed)
        return page

    # --------------------------------------------------- PAGE 5: SUCCESS
    def _page_success(self):
        page = QWidget()
        page.setStyleSheet("background:white;border:none;")
        v = QVBoxLayout(page)
        v.setContentsMargins(55, 80, 55, 55)
        v.setSpacing(0)

        ic = SafeIcon(SafeIcon.CHECK_LARGE, size=96, color=QColor('#22C55E'))
        r = QHBoxLayout()
        r.addStretch()
        r.addWidget(ic)
        r.addStretch()
        v.addLayout(r)
        v.addSpacing(24)

        t = QLabel("Password Reset Successful!")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet("color:#1F2937;font-size:26px;font-weight:700;background:transparent;border:none;")
        v.addWidget(t)
        v.addSpacing(12)

        m = QLabel("Your password has been successfully reset. You can now login with your new password.")
        m.setAlignment(Qt.AlignmentFlag.AlignCenter)
        m.setWordWrap(True)
        m.setMaximumWidth(400)
        m.setStyleSheet("color:#6B7280;font-size:15px;background:transparent;border:none;")
        v.addWidget(m)

        v.addStretch()

        btn = self._btn_primary("Continue to Login")
        btn.clicked.connect(lambda: self.backToLogin() if self.backToLogin else None)
        v.addWidget(btn)
        return page

    # ============================================================ LOGIC

    def _on_continue(self):
        uname = self.fp_username_edit.text().strip()
        self.fp_username_err.setVisible(False)

        if not uname:
            self.fp_username_err.setText("Please enter your username")
            self.fp_username_err.setVisible(True)
            return

        if not self.db or not self.db.is_connected():
            self.fp_username_err.setText("Database connection error.")
            self.fp_username_err.setVisible(True)
            return

        if not self.db.check_username_exists(uname):
            self.fp_username_err.setText("Username not found. Please check and try again.")
            self.fp_username_err.setVisible(True)
            return

        self.current_username = uname
        self._build_methods()
        self.stack.setCurrentIndex(1)

    def _mask_email(self, email):
        if not email or '@' not in email:
            return email
        name, domain = email.split('@', 1)
        if len(name) <= 2:
            masked = name[0] + '*' * len(name)
        else:
            masked = name[:2] + '*' * (len(name) - 2)
        return f"{masked}@{domain}"

    def _mask_phone(self, phone):
        if not phone:
            return phone
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) <= 4:
            return phone
        masked = digits[:3] + '*' * (len(digits) - 5) + digits[-2:]
        return f"+{masked}" if phone.startswith('+') else masked

    def _build_methods(self):
        while self.fp_method_box.count():
            item = self.fp_method_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.selected_method = None
        self.fp_send_btn.setEnabled(False)
        self.user_real_email = None
        self.user_real_phone = None

        user = self.db.get_user_by_username(self.current_username)
        if not user:
            return

        email = user.get('email')
        phone = self.db.get_user_phone(self.current_username)

        has_email = bool(email and email.strip())
        has_phone = bool(phone and phone.strip())

        # Email card
        if has_email:
            self.user_real_email = email.strip()
            card = RecoveryMethodCard(
                "email", SafeIcon.MAIL, "Recovery via Email",
                self._mask_email(email.strip()), "RECOMMENDED", disabled=False
            )
            card.clicked = lambda: self._pick_method("email")
            self.fp_method_box.addWidget(card)
        else:
            card = RecoveryMethodCard(
                "email", SafeIcon.MAIL, "Recovery via Email",
                "Not available", "", disabled=True
            )
            self.fp_method_box.addWidget(card)

        # SMS card
        if has_phone:
            self.user_real_phone = phone.strip()
            card = RecoveryMethodCard(
                "sms", SafeIcon.PHONE, "Recovery via SMS",
                self._mask_phone(phone.strip()) + "  (Coming soon)", "", disabled=True
            )
            self.fp_method_box.addWidget(card)
        else:
            card = RecoveryMethodCard(
                "sms", SafeIcon.PHONE, "Recovery via SMS",
                "Not available", "", disabled=True
            )
            self.fp_method_box.addWidget(card)

        if not has_email and not has_phone:
            lbl = QLabel("No recovery methods available for this account.\nPlease contact the administrator.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color:#EF4444;font-size:14px;background:#FEF2F2;padding:20px;border-radius:10px;border:1px solid #FCA5A5;")
            self.fp_method_box.addWidget(lbl)

    def _pick_method(self, method_id):
        self.selected_method = method_id
        self.fp_send_btn.setEnabled(True)
        for i in range(self.fp_method_box.count()):
            w = self.fp_method_box.itemAt(i).widget()
            if isinstance(w, RecoveryMethodCard):
                w.set_selected(w.method_id == method_id)

    def _on_send_code(self):
        if not self.selected_method or not self.current_username:
            return

        if self.selected_method == "email":
            if not self.user_real_email:
                self._err("No email address is saved for this account.\nPlease contact the administrator.")
                return

            code = f"{random.randint(100000, 999999)}"
            self.verification_code = code

            if not self.db.save_reset_code(self.current_username, code):
                self._err("Failed to save recovery code. Please try again.")
                return

            sent = self.db.send_recovery_email(self.user_real_email, self.current_username, code)
            if not sent:
                self.db.clear_reset_code(self.current_username)
                self._err("Failed to send the recovery email.\nPlease try again later or contact the administrator.")
                return

        elif self.selected_method == "sms":
            self._err("SMS recovery is not configured yet.\nPlease use email recovery or contact the administrator.")
            return
        else:
            return

        # Update header subtitle
        for child in self.fp_code_header.findChildren(QLabel):
            txt = child.text().lower()
            if "sent" in txt:
                if self.selected_method == "email":
                    child.setText("We've sent a 6-digit code to your registered email address.")
                else:
                    child.setText("We've sent a 6-digit code to your registered phone number.")
                break

        for box in self.fp_otp_boxes:
            box.clear()
            box.reset_style()
        self.fp_code_err.setVisible(False)

        self.resend_seconds = 30
        self.fp_resend_btn.setEnabled(False)
        self.fp_resend_btn.setText(f"Resend Code ({self.resend_seconds}s)")
        self.resend_timer.start(1000)

        self.stack.setCurrentIndex(2)
        QTimer.singleShot(100, lambda: self.fp_otp_boxes[0].setFocus())

    def _on_resend(self):
        if self.resend_seconds > 0:
            return
        self._on_send_code()

    def _tick_resend(self):
        self.resend_seconds -= 1
        if self.resend_seconds <= 0:
            self.resend_timer.stop()
            self.fp_resend_btn.setEnabled(True)
            self.fp_resend_btn.setText("Resend Code")
        else:
            self.fp_resend_btn.setText(f"Resend Code ({self.resend_seconds}s)")

    def _otp_changed(self, text, idx):
        if text:
            self.fp_otp_boxes[idx]._apply_filled()
            if idx < 5 and not self.fp_otp_boxes[idx + 1].text():
                QTimer.singleShot(50, lambda: self.fp_otp_boxes[idx + 1].setFocus())
        else:
            self.fp_otp_boxes[idx]._apply_empty()
            if idx > 0:
                QTimer.singleShot(50, lambda: self.fp_otp_boxes[idx - 1].setFocus())

    def _otp_key(self, event, idx):
        if event.key() == Qt.Key.Key_Backspace:
            if not self.fp_otp_boxes[idx].text() and idx > 0:
                self.fp_otp_boxes[idx - 1].setFocus()
                self.fp_otp_boxes[idx - 1].setText("")
        elif event.key() == Qt.Key.Key_Left and idx > 0:
            self.fp_otp_boxes[idx - 1].setFocus()
        elif event.key() == Qt.Key.Key_Right and idx < 5:
            self.fp_otp_boxes[idx + 1].setFocus()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._on_verify()
        else:
            QLineEdit.keyPressEvent(self.fp_otp_boxes[idx], event)

    def _on_verify(self):
        code = ''.join(b.text() for b in self.fp_otp_boxes)
        self.fp_code_err.setVisible(False)

        if len(code) != 6:
            self.fp_code_err.setText("Please enter all 6 digits")
            self.fp_code_err.setVisible(True)
            return

        if not code.isdigit():
            self.fp_code_err.setText("Code must contain only numbers")
            self.fp_code_err.setVisible(True)
            return

        if not self.db.validate_reset_code(self.current_username, code):
            self.fp_code_err.setText("Invalid or expired code. Please try again.")
            self.fp_code_err.setVisible(True)
            for b in self.fp_otp_boxes:
                b._apply_error()
            QTimer.singleShot(1000, self._fix_otp_styles)
            return

        self.resend_timer.stop()
        self._ok("Code verified successfully!")
        QTimer.singleShot(500, lambda: self.stack.setCurrentIndex(3))

    def _fix_otp_styles(self):
        for b in self.fp_otp_boxes:
            b.reset_style()

    def _pw_changed(self, pw):
        st = 0
        tags = []
        if len(pw) >= 8:
            st += 1; tags.append("8+ chars")
        if re.search(r'[A-Z]', pw):
            st += 1; tags.append("Uppercase")
        if re.search(r'[0-9]', pw):
            st += 1; tags.append("Number")
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', pw):
            st += 1; tags.append("Special")
        self.fp_str_bar.set_strength(st)
        names = ["", "Weak", "Fair", "Good", "Strong"]
        cols = ["", "#EF4444", "#F97316", "#EAB308", "#22C55E"]
        if pw:
            self.fp_str_lbl.setText(f"Password strength: {names[st]} ({', '.join(tags)})")
            self.fp_str_lbl.setStyleSheet(f"color:{cols[st]};font-size:12px;background:transparent;border:none;")
        else:
            self.fp_str_lbl.setText("")
        self._check_match()

    def _conf_changed(self, _):
        self._check_match()

    def _check_match(self):
        nw = self.fp_new_edit.text()
        cf = self.fp_conf_edit.text()
        if not cf:
            self.fp_match_lbl.setVisible(False)
            return
        self.fp_match_lbl.setVisible(True)
        if nw == cf:
            self.fp_match_lbl.setText("Passwords match")
            self.fp_match_lbl.setStyleSheet("color:#22C55E;font-size:12px;font-weight:600;background:transparent;border:none;")
        else:
            self.fp_match_lbl.setText("Passwords do not match")
            self.fp_match_lbl.setStyleSheet("color:#EF4444;font-size:12px;font-weight:600;background:transparent;border:none;")

    def _on_reset(self):
        nw = self.fp_new_edit.text()
        cf = self.fp_conf_edit.text()
        if not nw or not cf:
            self._err("Please fill in both password fields.")
            return
        if len(nw) < 8:
            self._err("Password must be at least 8 characters long.")
            return
        if nw != cf:
            self._err("Passwords do not match.")
            return

        ok = self.db.update_user_password_by_username(self.current_username, nw)
        if not ok:
            self._err("Failed to reset password. Please try again.")
            return

        self.db.clear_reset_code(self.current_username)
        self._ok("Password reset successfully!")
        QTimer.singleShot(800, lambda: self.stack.setCurrentIndex(4))

    # ------------------------------------------------------------ messages
    def _err(self, msg):
        from dashboard_gui.styled_dialog import StyledDialog
        StyledDialog.show_message(self, "Error", msg, "error")

    def _ok(self, msg):
        from dashboard_gui.styled_dialog import StyledDialog
        StyledDialog.show_message(self, "Success", msg, "success")
    # ------------------------------------------------------------ reset
    def reset_flow(self):
        self.current_username = None
        self.selected_method = None
        self.verification_code = None
        self.user_real_email = None
        self.user_real_phone = None

        self.fp_username_edit.clear()
        self.fp_username_err.setVisible(False)

        for b in self.fp_otp_boxes:
            b.clear()
            b.reset_style()
        self.fp_code_err.setVisible(False)

        self.fp_new_edit.clear()
        self.fp_conf_edit.clear()
        self.fp_str_bar.set_strength(0)
        self.fp_str_lbl.setText("")
        self.fp_match_lbl.setVisible(False)

        self.resend_timer.stop()
        self.fp_resend_btn.setEnabled(True)
        self.fp_resend_btn.setText("Resend Code")

        self.stack.setCurrentIndex(0)
        self.fp_username_edit.setFocus()

    def showEvent(self, event):
        super().showEvent(event)
        self.reset_flow()