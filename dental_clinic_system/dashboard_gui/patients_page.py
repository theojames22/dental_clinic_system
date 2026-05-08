"""
LC Dental Care - Patients Page (PyQt6)
All data from the database.  No hardcoded patient rows.
Initials-only avatars, clean clinical white/blue design.
"""

from datetime import datetime, date
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QTimer, QPoint, QPointF
from PyQt6.QtGui import (
    QColor, QFont, QPainter, QBrush, QPen, QPainterPath,
    QLinearGradient, QAction,
)
from PyQt6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QScrollArea, QSizePolicy,
    QGraphicsDropShadowEffect, QMenu, QDialog, QFormLayout,
    QDialogButtonBox, QComboBox, QTextEdit, QMessageBox, QSpinBox,
)
from databasepy import *
from dashboard_gui.style import *
from dashboard_gui.dashboard_gui import DashboardGUI

# ── Theme tokens ────────────────────────────────────────────────────────
try:
    from dashboard_gui.dashboard_gui import (
        BG, CARD, PRIMARY, PRIMARY_CONTAINER, PRIMARY_DARK, PRIMARY_FIXED,
        SECONDARY, SECONDARY_FIXED, TERTIARY, TERTIARY_FIXED,
        TERTIARY_CONTAINER, TEXT, MUTED, SUBTLE, OUTLINE,
        SURFACE_HIGH, SURFACE_VARIANT, SUCCESS, WARNING, DANGER,
        ERROR_CONTAINER, FONT, add_shadow, IconWidget,
    )
    # Compatibility shims: some dashboards IconWidget enums don't include certain ids
    if not hasattr(IconWidget, "REFRESH") and hasattr(IconWidget, "SEARCH"):
        IconWidget.REFRESH = IconWidget.SEARCH
    if not hasattr(IconWidget, "PLUS"):
        if hasattr(IconWidget, "USER_PLUS"):
            IconWidget.PLUS = IconWidget.USER_PLUS
        elif hasattr(IconWidget, "CHECK"):
            IconWidget.PLUS = IconWidget.CHECK
except Exception:
    BG              = "#F9F9FF"
    CARD            = "#FFFFFF"
    PRIMARY         = "#003F87"
    PRIMARY_CONTAINER = "#0056B3"
    PRIMARY_DARK    = "#002A5C"
    PRIMARY_FIXED   = "#D7E2FF"
    SECONDARY       = "#555F6B"
    SECONDARY_FIXED = "#D9E3F1"
    TERTIARY        = "#722B00"
    TERTIARY_FIXED  = "#FFDBCC"
    TERTIARY_CONTAINER = "#983C00"
    TEXT            = "#191C21"
    MUTED           = "#555F6B"
    SUBTLE          = "#727784"
    OUTLINE         = "#C2C6D4"
    SURFACE_HIGH    = "#E7E8F0"
    SURFACE_VARIANT = "#E1E2EA"
    SUCCESS         = "#1E8449"
    WARNING         = "#D68910"
    DANGER          = "#BA1A1A"
    ERROR_CONTAINER = "#FFDAD6"
    FONT            = "Inter"

    def add_shadow(w, blur=18, offset_y=4, alpha=12):
        e = QGraphicsDropShadowEffect(w)
        e.setBlurRadius(blur); e.setOffset(0, offset_y)
        e.setColor(QColor(0, 0, 0, alpha)); w.setGraphicsEffect(e)

    class IconWidget(QWidget):
        """Minimal fallback icon widget."""
        SEARCH=0; PLUS=1; REFRESH=2; SETTINGS=3; FILTER=4
        PERSON=5; CALENDAR=6; CHECK=7; EDIT=8; CLOSE=9
        USERS=10; TRENDING=11; MEDICAL=12; USER_PLUS=13
        CLOCK=14; SHIELD=15; WARNING=16; LIST=17; SAVE=18

        def __init__(self, icon_id, size=20, color=None, filled=False, parent=None):
            super().__init__(parent)
            self.icon_id = icon_id
            self._color = color or QColor(MUTED)
            self._filled = filled
            self.setFixedSize(size, size)

        def set_color(self, c): self._color = c; self.update()
        def set_filled(self, f): self._filled = f; self.update()

        def paintEvent(self, event):
            w, h = self.width(), self.height()
            if w < 4: return
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            c = self._color; s = min(w, h) / 24.0
            cx, cy = w / 2.0, h / 2.0
            pen = QPen(c, 1.7, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.setBrush(QBrush(c) if self._filled else Qt.BrushStyle.NoBrush)
            i = self.icon_id
            if i == self.SEARCH:
                p.drawEllipse(QPointF(cx - 1*s, cy - 1*s), 6*s, 6*s)
                p.drawLine(QPointF(cx + 3*s, cy + 3*s), QPointF(cx + 8*s, cy + 8*s))
            elif i == self.PLUS:
                p.drawLine(QPointF(cx - 7*s, cy), QPointF(cx + 7*s, cy))
                p.drawLine(QPointF(cx, cy - 7*s), QPointF(cx, cy + 7*s))
            elif i == self.REFRESH:
                p.drawArc(QRectF(cx - 8*s, cy - 8*s, 16*s, 16*s), 0, 270*16)
                p.drawLine(QPointF(cx + 5*s, cy - 6*s), QPointF(cx + 8*s, cy - 2*s))
                p.drawLine(QPointF(cx + 4*s, cy - 2*s), QPointF(cx + 8*s, cy - 2*s))
            elif i == self.SETTINGS:
                p.drawEllipse(QPointF(cx, cy), 3.5*s, 3.5*s)
                for a in range(0, 360, 45):
                    r = math.radians(a)
                    p.drawLine(QPointF(cx+math.cos(r)*6*s, cy+math.sin(r)*6*s),
                               QPointF(cx+math.cos(r)*9*s, cy+math.sin(r)*9*s))
            elif i == self.FILTER or i == self.LIST:
                p.drawLine(QPointF(cx-8*s, cy-6*s), QPointF(cx+8*s, cy-6*s))
                p.drawLine(QPointF(cx-5*s, cy), QPointF(cx+5*s, cy))
                p.drawLine(QPointF(cx-2*s, cy+6*s), QPointF(cx+2*s, cy+6*s))
            elif i in (self.PERSON, self.USER_PLUS):
                p.drawEllipse(QPointF(cx, cy - 4*s), 4.5*s, 4.5*s)
                pa = QPainterPath(); pa.moveTo(cx-8*s, cy+9*s)
                pa.cubicTo(QPointF(cx-8*s, cy+1*s), QPointF(cx+8*s, cy+1*s),
                           QPointF(cx+8*s, cy+9*s))
                p.drawPath(pa)
                if i == self.USER_PLUS:
                    p.drawLine(QPointF(cx+5*s, cy-2*s), QPointF(cx+9*s, cy-2*s))
                    p.drawLine(QPointF(cx+7*s, cy-4*s), QPointF(cx+7*s, cy))
            elif i in (self.CALENDAR, self.CLOCK):
                if i == self.CLOCK:
                    p.drawEllipse(QPointF(cx, cy), 9*s, 9*s)
                    p.drawLine(QPointF(cx, cy), QPointF(cx, cy-5*s))
                    p.drawLine(QPointF(cx, cy), QPointF(cx+4*s, cy+2*s))
                else:
                    p.drawRoundedRect(QRectF(cx-8*s, cy-8*s, 16*s, 16*s), 2, 2)
                    p.drawLine(QPointF(cx-8*s, cy-3*s), QPointF(cx+8*s, cy-3*s))
            elif i == self.CHECK:
                p.drawLine(QPointF(cx-6*s, cy), QPointF(cx-2*s, cy+5*s))
                p.drawLine(QPointF(cx-2*s, cy+5*s), QPointF(cx+7*s, cy-5*s))
            elif i == self.EDIT:
                p.drawRoundedRect(QRectF(cx-8*s, cy-8*s, 14*s, 16*s), 2, 2)
                p.drawLine(QPointF(cx-4*s, cy-3*s), QPointF(cx+2*s, cy-3*s))
                p.drawLine(QPointF(cx-4*s, cy+1*s), QPointF(cx+4*s, cy+1*s))
            elif i == self.CLOSE:
                p.drawLine(QPointF(cx-5*s, cy-5*s), QPointF(cx+5*s, cy+5*s))
                p.drawLine(QPointF(cx+5*s, cy-5*s), QPointF(cx-5*s, cy+5*s))
            elif i == self.USERS:
                p.drawEllipse(QPointF(cx-4*s, cy-4*s), 3.5*s, 3.5*s)
                p.drawEllipse(QPointF(cx+4*s, cy-4*s), 3.5*s, 3.5*s)
                p.drawArc(QRectF(cx-9*s, cy, 18*s, 12*s), 0, 180*16)
            elif i == IconWidget.TRENDING:
                p.drawLine(QPointF(cx-8*s, cy+4*s), QPointF(cx-2*s, cy-2*s))
                p.drawLine(QPointF(cx-2*s, cy-2*s), QPointF(cx+2*s, cy+2*s))
                p.drawLine(QPointF(cx+2*s, cy+2*s), QPointF(cx+8*s, cy-4*s))
                p.drawLine(QPointF(cx+8*s, cy-4*s), QPointF(cx+4*s, cy-4*s))
                p.drawLine(QPointF(cx+8*s, cy-4*s), QPointF(cx+8*s, cy))
            elif i == self.MEDICAL:
                p.drawRoundedRect(QRectF(cx-9*s, cy-5*s, 18*s, 13*s), 2, 2)
                p2 = QPen(c, 2.0); p.setPen(p2)
                p.drawLine(QPointF(cx, cy-1*s), QPointF(cx, cy+5*s))
                p.drawLine(QPointF(cx-3*s, cy+2*s), QPointF(cx+3*s, cy+2*s))
            elif i == self.SHIELD:
                pa = QPainterPath(); pa.moveTo(cx, cy-10*s)
                pa.lineTo(cx+9*s, cy-4*s); pa.lineTo(cx+9*s, cy+2*s)
                pa.cubicTo(QPointF(cx+9*s, cy+8*s), QPointF(cx, cy+12*s),
                           QPointF(cx, cy+12*s))
                pa.cubicTo(QPointF(cx, cy+12*s), QPointF(cx-9*s, cy+8*s),
                           QPointF(cx-9*s, cy+2*s))
                pa.lineTo(cx-9*s, cy-4*s); pa.closeSubpath()
                p.drawPath(pa)
            elif i == self.WARNING:
                pa = QPainterPath(); pa.moveTo(cx, cy-9*s)
                pa.lineTo(cx+10*s, cy+8*s); pa.lineTo(cx-10*s, cy+8*s)
                pa.closeSubpath(); p.drawPath(pa)
            elif i == self.SAVE:
                p.drawRoundedRect(QRectF(cx-8*s, cy-9*s, 16*s, 18*s), 2, 2)
                p.drawLine(QPointF(cx-8*s, cy-3*s), QPointF(cx+8*s, cy-3*s))
                p.drawRoundedRect(QRectF(cx-4*s, cy-8*s, 8*s, 5*s), 1, 1)
            else:
                p.drawEllipse(QPointF(cx, cy), 8*s, 8*s)
            p.end()


# ── Helpers ─────────────────────────────────────────────────────────────
import math

def _initials(name: str) -> str:
    if not name: return "?"
    parts = [p for p in str(name).strip().split() if p]
    if not parts: return "?"
    if len(parts) == 1: return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()

_AVATAR_PALETTE = [
    ("#D7E2FF", "#003F87"), ("#FFDBCC", "#722B00"),
    ("#D9E3F1", "#1B3F66"), ("#FFE7B0", "#7A4F00"),
    ("#CCE8DA", "#1E5E3A"), ("#E1E2EA", "#3E4756"),
    ("#F0E6FF", "#6B21A8"), ("#CCF2FF", "#0E7490"),
]

def _avatar_colors(name: str):
    if not name: return _AVATAR_PALETTE[0]
    h = sum(ord(c) for c in str(name))
    return _AVATAR_PALETTE[h % len(_AVATAR_PALETTE)]

def _fmt_date(value) -> str:
    if not value: return "No visit"
    if isinstance(value, (datetime, date)):
        return value.strftime("%b %d, %Y")
    s = str(value)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"):
        try: return datetime.strptime(s.split(".")[0], fmt).strftime("%b %d, %Y")
        except: continue
    return s

def _derive_status(appointment_status) -> str:
    """Derive patient status from latest appointment status."""
    if not appointment_status: return "Pending"
    s = str(appointment_status).strip().lower()
    if s in ('scheduled', 'walk-in'): return "Active"
    if s == 'completed': return "Active"
    if s == 'cancelled': return "Inactive"
    return "Active"

STATUS_STYLES = {
    "active":   ("#CCE8DA", "#1E5E3A"),
    "pending":  ("#FFE7B0", "#7A4F00"),
    "inactive": ("#E1E2EA", "#3E4756"),
}

def _status_chip(text: str) -> QLabel:
    key = (text or "").strip().lower()
    bg, fg = STATUS_STYLES.get(key, ("#E1E2EA", "#3E4756"))
    chip = QLabel((text or "--").upper())
    chip.setFont(QFont(FONT, 9, QFont.Weight.Bold))
    chip.setStyleSheet(
        f"background:{bg};color:{fg};border-radius:10px;"
        f"padding:4px 12px;border:none;")
    chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
    chip.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
    return chip

SCROLLBAR_CSS = (
    "QScrollArea{background:transparent;border:none;}"
    f"QScrollBar:vertical{{background:transparent;width:8px;}}"
    f"QScrollBar::handle:vertical{{background:{OUTLINE};border-radius:4px;min-height:30px;}}"
    "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
)


# ═══════════════════════════════════════════════════════════════════════
# INITIALS AVATAR — circular, initials only, no images
# ═══════════════════════════════════════════════════════════════════════
class InitialsAvatar(QWidget):
    def __init__(self, name: str, size: int = 40, parent=None):
        super().__init__(parent)
        self._name = name or ""; self._size = size
        self.setFixedSize(size, size)

    def set_name(self, name: str):
        self._name = name or ""; self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg, fg = _avatar_colors(self._name)
        p.setBrush(QBrush(QColor(bg))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, self._size, self._size)
        p.setPen(QColor(fg))
        f = QFont(FONT, max(9, int(self._size * 0.36)), QFont.Weight.Bold)
        p.setFont(f)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, _initials(self._name))


# ═══════════════════════════════════════════════════════════════════════
# CLINICAL PERFORMANCE CARD (blue gradient)
# ═══════════════════════════════════════════════════════════════════════
class ClinicalPerformanceCard(QFrame):
    def __init__(self, satisfaction="--", retention="--", note="", parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self._sat = satisfaction; self._ret = retention; self._note = note
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(28, 22, 28, 22); lay.setSpacing(8)
        title = QLabel("Clinical Performance")
        title.setStyleSheet("color:white;background:transparent;border:none;")
        title.setFont(QFont(FONT, 18, QFont.Weight.Bold)); lay.addWidget(title)

        sub = QLabel(self._note or "Quarterly directory audit is 94% complete.")
        sub.setWordWrap(True)
        sub.setStyleSheet("color:rgba(255,255,255,0.85);background:transparent;border:none;")
        sub.setFont(QFont(FONT, 10)); lay.addWidget(sub)

        row = QHBoxLayout(); row.setSpacing(40)
        for label, value in (("PATIENT SATISFACTION", self._sat),
                             ("RETENTION RATE", self._ret)):
            col = QVBoxLayout(); col.setSpacing(2)
            l1 = QLabel(label); l1.setFont(QFont(FONT, 9, QFont.Weight.Bold))
            l1.setStyleSheet(
                "color:rgba(255,255,255,0.85);background:transparent;"
                "border:none;letter-spacing:1px;")
            l2 = QLabel(str(value)); l2.setFont(QFont(FONT, 22, QFont.Weight.Bold))
            l2.setStyleSheet("color:white;background:transparent;border:none;")
            col.addWidget(l1); col.addWidget(l2); row.addLayout(col)
        row.addStretch(1); lay.addLayout(row); lay.addStretch(1)

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        grad = QLinearGradient(0, 0, rect.width(), rect.height())
        grad.setColorAt(0, QColor(PRIMARY))
        grad.setColorAt(1, QColor(PRIMARY_CONTAINER))
        p.setBrush(QBrush(grad)); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(0, 0, rect.width(), rect.height()), 14, 14)

    def update_metrics(self, satisfaction, retention, note=""):
        self._sat = satisfaction; self._ret = retention; self._note = note
        # Rebuild
        while self.layout().count():
            it = self.layout().takeAt(0)
            if it.widget(): it.widget().deleteLater()
            elif it.layout():
                while it.layout().count():
                    si = it.layout().takeAt(0)
                    if si.widget(): si.widget().deleteLater()
        self._build()


# ═══════════════════════════════════════════════════════════════════════
# METRIC CARD (Active Records / Patient Growth)
# ═══════════════════════════════════════════════════════════════════════
class MetricCard(QFrame):
    def __init__(self, title, value, badge_text="", badge_bg=None,
                 badge_fg=None, icon_id=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"MetricCard{{background:{CARD};border-radius:14px;"
            f"border:1px solid {OUTLINE};}}")
        self.setMinimumHeight(150)
        add_shadow(self, blur=18, offset_y=4, alpha=14)
        lay = QVBoxLayout(self); lay.setContentsMargins(20, 18, 20, 18); lay.setSpacing(8)

        head = QHBoxLayout(); head.setSpacing(8)
        if icon_id is not None:
            ico = IconWidget(icon_id, 20, QColor(MUTED))
            head.addWidget(ico)
        ttl = QLabel(title); ttl.setFont(QFont(FONT, 11, QFont.Weight.DemiBold))
        ttl.setStyleSheet(f"color:{MUTED};background:transparent;border:none;")
        head.addWidget(ttl); head.addStretch(1); lay.addLayout(head)

        self._value_label = QLabel(str(value))
        self._value_label.setFont(QFont(FONT, 26, QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        lay.addWidget(self._value_label)

        if badge_text:
            b = QLabel(badge_text)
            bbg = badge_bg or PRIMARY_FIXED; bfg = badge_fg or PRIMARY
            b.setStyleSheet(
                f"background:{bbg};color:{bfg};border-radius:8px;"
                f"padding:4px 10px;border:none;")
            b.setFont(QFont(FONT, 9, QFont.Weight.DemiBold))
            b.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
            lay.addWidget(b)
        lay.addStretch(1)

    def set_value(self, v, badge_text="", badge_bg=None, badge_fg=None):
        self._value_label.setText(str(v))
        # Update badge if provided
        for child in self.findChildren(QLabel):
            if child is not self._value_label and child.text().startswith(("+", "Above", "Below")):
                if badge_text:
                    child.setText(badge_text)
                    if badge_bg:
                        child.setStyleSheet(
                            f"background:{badge_bg};color:{badge_fg or PRIMARY};"
                            f"border-radius:8px;padding:4px 10px;border:none;")
                else:
                    child.setText("")
                break


# ═══════════════════════════════════════════════════════════════════════
# SEARCH / ACTION BAR
# ═══════════════════════════════════════════════════════════════════════
class SearchBar(QFrame):
    search_changed = pyqtSignal(str)
    filter_clicked = pyqtSignal()
    add_clicked    = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"background:{CARD};border-radius:12px;border:1px solid {OUTLINE};")
        add_shadow(self, blur=14, offset_y=2, alpha=10)
        self.setFixedHeight(64)
        lay = QHBoxLayout(self); lay.setContentsMargins(14, 10, 14, 10); lay.setSpacing(10)

        # Search icon + input
        search_frame = QFrame()
        search_frame.setStyleSheet(
            f"QFrame{{background:{BG};border:1px solid {OUTLINE};border-radius:8px;}}")
        sf_lay = QHBoxLayout(search_frame); sf_lay.setContentsMargins(10, 4, 10, 4)
        sf_lay.setSpacing(8)
        sf_lay.addWidget(IconWidget(IconWidget.SEARCH, 16, QColor(SUBTLE)))
        self.search = QLineEdit(); self.search.setPlaceholderText("Search by name...")
        self.search.setStyleSheet(
            f"QLineEdit{{background:transparent;border:none;color:{TEXT};font-size:13px;}}"
            f"QLineEdit::placeholder{{color:{SUBTLE};}}")
        self.search.textChanged.connect(self.search_changed.emit)
        sf_lay.addWidget(self.search, 1)
        self.search.setMinimumWidth(260)
        lay.addWidget(search_frame, 1)

        # Filter button
        self.filter_btn = QPushButton("Filter")
        self.filter_btn.setFixedHeight(40)
        self.filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.filter_btn.setStyleSheet(
            f"QPushButton{{background:{CARD};color:{TEXT};border:1px solid {OUTLINE};"
            f"border-radius:8px;padding:0 16px;font-weight:600;font-size:12px;}}"
            f"QPushButton:hover{{background:{SURFACE_HIGH};}}")
        self.filter_btn.clicked.connect(self.filter_clicked.emit)
        # Add filter icon
        fl = QHBoxLayout(self.filter_btn); fl.setContentsMargins(0,0,0,0)
        # We'll just use text since QPushButton with icon needs setIcon
        lay.addWidget(self.filter_btn)

        lay.addStretch(1)

        # Add Patient button
        self.add_btn = QPushButton("Add Patient")
        self.add_btn.setFixedHeight(40)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet(
            f"QPushButton{{background:{PRIMARY};color:white;border:none;"
            f"border-radius:8px;padding:0 18px;font-weight:700;font-size:12px;}}"
            f"QPushButton:hover{{background:{PRIMARY_DARK};}}")
        self.add_btn.clicked.connect(self.add_clicked.emit)
        lay.addWidget(self.add_btn)


# ═══════════════════════════════════════════════════════════════════════
# PATIENT ROW
# ═══════════════════════════════════════════════════════════════════════
COL_WEIGHTS = [3, 2, 2, 2, 2, 2, 1]
HEADERS = ["PATIENT NAME", "RECORD ID", "LAST VISIT",
           "PRIMARY DR.", "TREATMENT", "STATUS", "ACTIONS"]

def _safe_get(d, *keys, default=None):
    if d is None: return default
    if isinstance(d, dict):
        for k in keys:
            if k in d and d[k] not in (None, ""): return d[k]
        return default
    return default


class PatientRow(QFrame):
    manage_clicked = pyqtSignal(dict)

    def __init__(self, patient: dict, alt: bool = False, parent=None):
        super().__init__(parent)
        self.patient = patient
        bg = "#F6F8FD" if alt else CARD
        self.setStyleSheet(
            f"PatientRow{{background:{bg};border:none;"
            f"border-bottom:1px solid {SURFACE_VARIANT};}}"
            f"PatientRow:hover{{background:#EEF3FB;}}")
        self.setMinimumHeight(64)
        lay = QHBoxLayout(self); lay.setContentsMargins(20, 8, 20, 8); lay.setSpacing(12)

        # Patient Name + initials avatar + age/gender
        name = _safe_get(patient, "patient_name", "name", default="Unknown")
        age = _safe_get(patient, "age", default=None)
        gender = _safe_get(patient, "gender", default=None)
        sub_parts = [x for x in [f"{age} yrs" if age else None, gender] if x]
        sub = " - ".join(sub_parts) if sub_parts else ""

        name_box = QWidget()
        nb = QHBoxLayout(name_box); nb.setContentsMargins(0,0,0,0); nb.setSpacing(12)
        nb.addWidget(InitialsAvatar(name, 40))
        col = QVBoxLayout(); col.setSpacing(0); col.setContentsMargins(0,0,0,0)
        n = QLabel(str(name)); n.setFont(QFont(FONT, 11, QFont.Weight.Bold))
        n.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        col.addWidget(n)
        if sub:
            s = QLabel(sub); s.setFont(QFont(FONT, 9))
            s.setStyleSheet(f"color:{SUBTLE};background:transparent;border:none;")
            col.addWidget(s)
        nb.addLayout(col); nb.addStretch(1)
        self._add_cell(lay, name_box, COL_WEIGHTS[0])

        # Record ID
        pid = _safe_get(patient, "patient_id", "id", default=0)
        rec_id = f"#RE-{int(pid):05d}" if pid else "--"
        self._add_text(lay, rec_id, COL_WEIGHTS[1], muted=True)

        # Last Visit
        lv = _safe_get(patient, "last_visit", default=None)
        self._add_text(lay, _fmt_date(lv), COL_WEIGHTS[2], muted=True)

        # Primary Dr.
        dr = _safe_get(patient, "doctor_name", "staff_name", default=None)
        dr_box = QWidget(); dl = QHBoxLayout(dr_box)
        dl.setContentsMargins(0,0,0,0); dl.setSpacing(8)
        dot = QLabel(); dot.setFixedSize(8, 8)
        dc = PRIMARY
        if dr:
            h = sum(ord(c) for c in str(dr)) % 4
            dc = [PRIMARY, TERTIARY_CONTAINER, SUCCESS, WARNING][h]
        dot.setStyleSheet(f"background:{dc};border-radius:4px;")
        dl.addWidget(dot)
        dn = QLabel(str(dr) if dr else "Not assigned")
        dn.setFont(QFont(FONT, 10))
        dn.setStyleSheet(
            f"color:{TEXT if dr else MUTED};background:transparent;border:none;")
        dl.addWidget(dn); dl.addStretch(1)
        self._add_cell(lay, dr_box, COL_WEIGHTS[3])

        # Treatment
        tr = _safe_get(patient, "treatment_name", "treatment", default=None)
        self._add_text(lay, str(tr) if tr else "No treatment", COL_WEIGHTS[4],
                       muted=not tr)

        # Status
        appt_status = _safe_get(patient, "appointment_status", "status", default=None)
        st = _derive_status(appt_status)
        st_box = QWidget(); sl = QHBoxLayout(st_box)
        sl.setContentsMargins(0,0,0,0); sl.setSpacing(0)
        sl.addWidget(_status_chip(st)); sl.addStretch(1)
        self._add_cell(lay, st_box, COL_WEIGHTS[5])

        # Manage button
        btn = QPushButton("Manage"); btn.setFixedHeight(32)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton{{background:{CARD};color:{TEXT};border:1px solid {OUTLINE};"
            f"border-radius:8px;padding:0 16px;font-weight:600;font-size:11px;}}"
            f"QPushButton:hover{{background:{PRIMARY};color:white;border-color:{PRIMARY};}}")
        btn.clicked.connect(lambda: self.manage_clicked.emit(self.patient))
        bb = QWidget(); bl = QHBoxLayout(bb)
        bl.setContentsMargins(0,0,0,0); bl.addStretch(1); bl.addWidget(btn)
        self._add_cell(lay, bb, COL_WEIGHTS[6])

    def _add_text(self, lay, text, stretch, muted=False):
        l = QLabel(str(text)); l.setFont(QFont(FONT, 10))
        col = MUTED if muted else TEXT
        l.setStyleSheet(f"color:{col};background:transparent;border:none;")
        self._add_cell(lay, l, stretch)

    def _add_cell(self, lay, w, stretch):
        lay.addWidget(w, stretch)


# ═══════════════════════════════════════════════════════════════════════
# ADD PATIENT DIALOG
# ═══════════════════════════════════════════════════════════════════════
class AddPatientDialog(QDialog):
    def __init__(self, db=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Add Patient")
        self.setMinimumWidth(480)
        self.setStyleSheet(f"QDialog{{background:{CARD};}}")

        lay = QVBoxLayout(self); lay.setContentsMargins(28, 24, 28, 24); lay.setSpacing(16)

        # Header
        hdr = QHBoxLayout(); hdr.setSpacing(10)
        hdr.addWidget(IconWidget(IconWidget.USER_PLUS, 22, QColor(PRIMARY), filled=True))
        t = QLabel("Add New Patient"); t.setFont(QFont(FONT, 16, QFont.Weight.Bold))
        t.setStyleSheet(f"color:{PRIMARY};background:transparent;border:none;")
        hdr.addWidget(t); hdr.addStretch(); lay.addLayout(hdr)

        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{OUTLINE};"); lay.addWidget(sep)

        # Form
        form = QGridLayout(); form.setHorizontalSpacing(16); form.setVerticalSpacing(12)

        self.name_edit = QLineEdit(); self.name_edit.setPlaceholderText("Full name")
        self.age_edit = QSpinBox(); self.age_edit.setRange(0, 150); self.age_edit.setSuffix(" years")
        self.gender_combo = QComboBox(); self.gender_combo.addItems(["Male", "Female", "Other"])
        self.contact_edit = QLineEdit(); self.contact_edit.setPlaceholderText("Phone / contact number")
        self.address_edit = QLineEdit(); self.address_edit.setPlaceholderText("Address")
        self.history_edit = QTextEdit(); self.history_edit.setPlaceholderText("Medical history (optional)")
        self.history_edit.setFixedHeight(80)

        input_style = (
            f"QLineEdit{{border:1px solid {OUTLINE};border-radius:8px;padding:0 12px;"
            f"font-size:13px;color:{TEXT};background:{CARD};}}"
            f"QLineEdit:focus{{border:2px solid {PRIMARY};}}")
        combo_style = (
            f"QComboBox{{border:1px solid {OUTLINE};border-radius:8px;padding:0 12px;"
            f"font-size:13px;color:{TEXT};background:{CARD};}}"
            f"QComboBox QAbstractItemView{{background:{CARD};border:1px solid {OUTLINE};padding:4px;}}")
        spin_style = (
            f"QSpinBox{{border:1px solid {OUTLINE};border-radius:8px;padding:0 12px;"
            f"font-size:13px;color:{TEXT};background:{CARD};}}")
        text_style = (
            f"QTextEdit{{border:1px solid {OUTLINE};border-radius:8px;padding:8px;"
            f"font-size:13px;color:{TEXT};background:{CARD};}}")

        for w, s in [(self.name_edit, input_style), (self.age_edit, spin_style),
                     (self.gender_combo, combo_style), (self.contact_edit, input_style),
                     (self.address_edit, input_style), (self.history_edit, text_style)]:
            w.setStyleSheet(s)
            w.setFixedHeight(40) if not isinstance(w, QTextEdit) else None

        label_style = f"color:{MUTED};background:transparent;border:none;font-weight:600;font-size:11px;"
        labels = ["Patient Name", "Age", "Gender", "Contact", "Address", "Medical History"]
        widgets = [self.name_edit, self.age_edit, self.gender_combo,
                   self.contact_edit, self.address_edit, self.history_edit]
        for i, (lbl, w) in enumerate(zip(labels, widgets)):
            l = QLabel(lbl); l.setStyleSheet(label_style)
            form.addWidget(l, i, 0); form.addWidget(w, i, 1)

        lay.addLayout(form)

        # Buttons
        btn_row = QHBoxLayout(); btn_row.addStretch()
        cancel = QPushButton("Cancel"); cancel.setFixedHeight(40)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet(
            f"QPushButton{{background:{SURFACE_HIGH};color:{TEXT};border:1px solid {OUTLINE};"
            f"border-radius:8px;padding:0 20px;font-weight:600;}}"
            f"QPushButton:hover{{background:{SURFACE_VARIANT};}}")
        cancel.clicked.connect(self.reject); btn_row.addWidget(cancel)

        save = QPushButton("Add Patient"); save.setFixedHeight(40)
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.setStyleSheet(
            f"QPushButton{{background:{PRIMARY};color:white;border:none;"
            f"border-radius:8px;padding:0 24px;font-weight:700;}}"
            f"QPushButton:hover{{background:{PRIMARY_DARK};}}")
        save.clicked.connect(self._save); btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Required", "Patient name is required.")
            return
        age = self.age_edit.value() or None
        gender = self.gender_combo.currentText()
        contact = self.contact_edit.text().strip() or None
        address = self.address_edit.text().strip() or None
        history = self.history_edit.toPlainText().strip() or None

        if self.db:
            try:
                result = self.db.add_patient_directory(
                    name, age, gender, contact, address, history)
                if result:
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error",
                                         "Failed to add patient. Check database connection.")
            except Exception as e:
                QMessageBox.critical(self, "Database Error", str(e))
        else:
            self.accept()


# ═══════════════════════════════════════════════════════════════════════
# PATIENT DETAIL / EDIT DIALOG
# ═══════════════════════════════════════════════════════════════════════
class PatientDetailDialog(QDialog):
    def __init__(self, db, patient: dict, parent=None):
        super().__init__(parent)
        self.db = db; self.patient = patient
        self.setWindowTitle(f"Patient - {patient.get('patient_name', 'Details')}")
        self.setMinimumWidth(520)
        self.setStyleSheet(f"QDialog{{background:{CARD};}}")

        lay = QVBoxLayout(self); lay.setContentsMargins(28, 24, 28, 24); lay.setSpacing(16)

        # Header with avatar
        hdr = QHBoxLayout(); hdr.setSpacing(14)
        name = patient.get("patient_name", "Unknown")
        hdr.addWidget(InitialsAvatar(name, 48))
        col = QVBoxLayout(); col.setSpacing(2)
        n = QLabel(name); n.setFont(QFont(FONT, 16, QFont.Weight.Bold))
        n.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        col.addWidget(n)
        pid = patient.get("patient_id", 0)
        rid = QLabel(f"Record #RE-{int(pid):05d}")
        rid.setStyleSheet(f"color:{MUTED};background:transparent;border:none;")
        rid.setFont(QFont(FONT, 10)); col.addWidget(rid)
        hdr.addLayout(col); hdr.addStretch(); lay.addLayout(hdr)

        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{OUTLINE};"); lay.addWidget(sep)

        # Editable form
        form = QGridLayout(); form.setHorizontalSpacing(16); form.setVerticalSpacing(12)
        input_style = (
            f"QLineEdit{{border:1px solid {OUTLINE};border-radius:8px;padding:0 12px;"
            f"font-size:13px;color:{TEXT};background:{CARD};height:36px;}}"
            f"QLineEdit:focus{{border:2px solid {PRIMARY};}}")
        combo_style = (
            f"QComboBox{{border:1px solid {OUTLINE};border-radius:8px;padding:0 12px;"
            f"font-size:13px;color:{TEXT};background:{CARD};height:36px;}}"
            f"QComboBox QAbstractItemView{{background:{CARD};border:1px solid {OUTLINE};padding:4px;}}")
        text_style = (
            f"QTextEdit{{border:1px solid {OUTLINE};border-radius:8px;padding:8px;"
            f"font-size:13px;color:{TEXT};background:{CARD};}}")
        label_style = f"color:{MUTED};background:transparent;border:none;font-weight:600;font-size:11px;"

        self.name_edit = QLineEdit(patient.get("patient_name") or "")
        self.age_edit = QLineEdit(str(patient.get("age") or ""))
        self.age_edit.setValidator(None)  # allow any for simplicity
        self.gender_combo = QComboBox(); self.gender_combo.addItems(["Male", "Female", "Other"])
        idx = self.gender_combo.findText(patient.get("gender") or "Male")
        if idx >= 0: self.gender_combo.setCurrentIndex(idx)
        self.contact_edit = QLineEdit(patient.get("contact") or "")
        self.address_edit = QLineEdit(patient.get("address") or "")
        self.history_edit = QTextEdit()
        self.history_edit.setPlainText(patient.get("medical_history") or "")
        self.history_edit.setFixedHeight(80)

        for w, s in [(self.name_edit, input_style), (self.age_edit, input_style),
                     (self.gender_combo, combo_style), (self.contact_edit, input_style),
                     (self.address_edit, input_style), (self.history_edit, text_style)]:
            w.setStyleSheet(s)

        labels = ["Patient Name", "Age", "Gender", "Contact", "Address", "Medical History"]
        widgets = [self.name_edit, self.age_edit, self.gender_combo,
                   self.contact_edit, self.address_edit, self.history_edit]
        for i, (lbl, w) in enumerate(zip(labels, widgets)):
            l = QLabel(lbl); l.setStyleSheet(label_style)
            form.addWidget(l, i, 0); form.addWidget(w, i, 1)
        lay.addLayout(form)

        # Info section (read-only)
        sep2 = QFrame(); sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background:{OUTLINE};"); lay.addWidget(sep2)

        info_lay = QHBoxLayout(); info_lay.setSpacing(24)
        for lbl, val in [("Registered", _fmt_date(patient.get("registration_date"))),
                         ("Last Visit", _fmt_date(patient.get("last_visit"))),
                         ("Doctor", patient.get("doctor_name") or "Not assigned")]:
            c = QVBoxLayout(); c.setSpacing(2)
            l = QLabel(lbl); l.setStyleSheet(label_style); c.addWidget(l)
            v = QLabel(str(val)); v.setFont(QFont(FONT, 11))
            v.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
            c.addWidget(v); info_lay.addLayout(c)
        info_lay.addStretch(); lay.addLayout(info_lay)

        # Buttons
        btn_row = QHBoxLayout()

        delete_btn = QPushButton("Delete Patient"); delete_btn.setFixedHeight(38)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet(
            f"QPushButton{{background:{ERROR_CONTAINER};color:{DANGER};border:1px solid {DANGER};"
            f"border-radius:8px;padding:0 16px;font-weight:600;}}"
            f"QPushButton:hover{{background:{DANGER};color:white;}}")
        delete_btn.clicked.connect(self._delete)
        btn_row.addWidget(delete_btn)

        btn_row.addStretch()

        cancel = QPushButton("Cancel"); cancel.setFixedHeight(38)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet(
            f"QPushButton{{background:{SURFACE_HIGH};color:{TEXT};border:1px solid {OUTLINE};"
            f"border-radius:8px;padding:0 16px;font-weight:600;}}"
            f"QPushButton:hover{{background:{SURFACE_VARIANT};}}")
        cancel.clicked.connect(self.reject); btn_row.addWidget(cancel)

        save = QPushButton("Save Changes"); save.setFixedHeight(38)
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.setStyleSheet(
            f"QPushButton{{background:{PRIMARY};color:white;border:none;"
            f"border-radius:8px;padding:0 20px;font-weight:700;}}"
            f"QPushButton:hover{{background:{PRIMARY_DARK};}}")
        save.clicked.connect(self._save)
        btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Required", "Patient name is required.")
            return
        age = self.age_edit.text().strip() or None
        gender = self.gender_combo.currentText()
        contact = self.contact_edit.text().strip() or None
        address = self.address_edit.text().strip() or None
        history = self.history_edit.toPlainText().strip() or None
        if self.db:
            try:
                self.db.update_patient_directory(
                    self.patient.get("patient_id"), name, age, gender,
                    contact, address, history)
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
        else:
            self.accept()

    def _delete(self):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete patient {self.patient.get('patient_name', '')}?\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes and self.db:
            try:
                self.db.delete_patient(self.patient.get("patient_id"))
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))


# ═══════════════════════════════════════════════════════════════════════
# TOAST NOTIFICATION
# ═══════════════════════════════════════════════════════════════════════
class ToastNotification(QFrame):
    def __init__(self, message, bg_color=SUCCESS, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(
            f"background:{bg_color};border-radius:10px;border:none;")
        self.setFixedSize(340, 56)
        lay = QHBoxLayout(self); lay.setContentsMargins(16, 8, 16, 8)
        icon = IconWidget(IconWidget.CHECK, 20, QColor("#FFFFFF"), filled=True)
        lay.addWidget(icon)
        lbl = QLabel(message); lbl.setWordWrap(True)
        lbl.setStyleSheet("color:white;font-size:12px;font-weight:600;"
                          "background:transparent;border:none;")
        lbl.setFont(QFont(FONT, 12, QFont.Weight.Bold))
        lay.addWidget(lbl, 1)

    def show_at(self, parent_widget):
        if parent_widget:
            geo = parent_widget.geometry()
            self.move(geo.x() + geo.width() - 360, geo.y() + 20)
        self.show()
        QTimer.singleShot(3000, self.close)


# ═══════════════════════════════════════════════════════════════════════
# FLOATING ACTION BUTTON (FAB)
# ═══════════════════════════════════════════════════════════════════════
class FAB(QPushButton):
    """Circular floating action button at bottom-right."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(52, 52)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QPushButton{{background:{PRIMARY};color:white;border:none;"
            f"border-radius:26px;font-size:22px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{PRIMARY_DARK};}}")
        # Plus icon inside
        lay = QHBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(IconWidget(IconWidget.PLUS, 22, QColor("#FFFFFF"), filled=True))

    def reposition(self, parent_rect):
        self.move(parent_rect.width() - 72, parent_rect.height() - 72)


# ═══════════════════════════════════════════════════════════════════════
# PATIENTS PAGE — main widget
# ═══════════════════════════════════════════════════════════════════════
class PatientsPage(QWidget):
    """
    Patients directory page connected to the real database.
    Drop-in for the QStackedWidget in DashboardGUI.
    """

    def __init__(self, db=None, parent=None):
        super().__init__(parent)
        self.db = db
        self._all_patients = []
        self._filter_status = None
        self._filter_doctor = None
        self._filter_treatment = None
        self.setStyleSheet(f"background:{BG};")
        self._build()
        QTimer.singleShot(0, self.refresh)

    # ── UI CONSTRUCTION ──────────────────────────────────────────────
    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(SCROLLBAR_CSS)

        host = QWidget(); host.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(host)
        lay.setContentsMargins(28, 24, 28, 28); lay.setSpacing(20)

        # ── Top metrics row ──
        metrics_row = QHBoxLayout(); metrics_row.setSpacing(20)

        self.perf_card = ClinicalPerformanceCard()
        metrics_row.addWidget(self.perf_card, 5)

        self.active_card = MetricCard(
            "Active Records", "--",
            icon_id=IconWidget.USERS)
        metrics_row.addWidget(self.active_card, 3)

        self.growth_card = MetricCard(
            "Patient Growth", "--",
            icon_id=IconWidget.TRENDING_UP)
        metrics_row.addWidget(self.growth_card, 3)

        lay.addLayout(metrics_row)

        # ── Search / action bar ──
        self.search_bar = SearchBar()
        self.search_bar.search_changed.connect(self._on_search)
        self.search_bar.filter_clicked.connect(self._show_filter_menu)
        self.search_bar.add_clicked.connect(self._open_add_dialog)
        lay.addWidget(self.search_bar)

        # ── Patient Directory card ──
        self.directory = QFrame()
        self.directory.setStyleSheet(
            f"background:{CARD};border-radius:14px;border:1px solid {OUTLINE};")
        add_shadow(self.directory, blur=20, offset_y=4, alpha=14)
        d_lay = QVBoxLayout(self.directory)
        d_lay.setContentsMargins(0, 0, 0, 0); d_lay.setSpacing(0)

        # Header bar
        head = QFrame(); head.setStyleSheet("background:transparent;border:none;")
        hl = QHBoxLayout(head); hl.setContentsMargins(20, 16, 20, 16); hl.setSpacing(8)
        title = QLabel("Patient Directory")
        title.setFont(QFont(FONT, 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{PRIMARY};background:transparent;border:none;")
        hl.addWidget(title); hl.addStretch(1)

        refresh_btn = QPushButton(); refresh_btn.setFixedSize(32, 32)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet(
            f"QPushButton{{background:transparent;color:{MUTED};border:none;}}"
            f"QPushButton:hover{{color:{PRIMARY};}}")
        rl = QVBoxLayout(refresh_btn); rl.setContentsMargins(0,0,0,0)
        rl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rl.addWidget(IconWidget(IconWidget.REFRESH, 16, QColor(MUTED)))
        refresh_btn.clicked.connect(self.refresh)
        hl.addWidget(refresh_btn)

        settings_btn = QPushButton(); settings_btn.setFixedSize(32, 32)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setStyleSheet(refresh_btn.styleSheet())
        sl2 = QVBoxLayout(settings_btn); sl2.setContentsMargins(0,0,0,0)
        sl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sl2.addWidget(IconWidget(IconWidget.SETTINGS, 16, QColor(MUTED)))
        hl.addWidget(settings_btn)

        d_lay.addWidget(head)

        # Column headers
        col_head = QFrame()
        col_head.setStyleSheet(
            f"background:{BG};border:none;"
            f"border-top:1px solid {SURFACE_VARIANT};"
            f"border-bottom:1px solid {SURFACE_VARIANT};")
        col_head.setFixedHeight(40)
        chl = QHBoxLayout(col_head); chl.setContentsMargins(20, 0, 20, 0)
        chl.setSpacing(12)
        for h, w in zip(HEADERS, COL_WEIGHTS):
            l = QLabel(h); l.setFont(QFont(FONT, 9, QFont.Weight.Bold))
            l.setStyleSheet(
                f"color:{SUBTLE};background:transparent;border:none;letter-spacing:1px;")
            chl.addWidget(l, w)
        d_lay.addWidget(col_head)

        # Rows container (scrollable)
        self.rows_scroll = QScrollArea(); self.rows_scroll.setWidgetResizable(True)
        self.rows_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.rows_scroll.setMinimumHeight(300)
        self.rows_scroll.setStyleSheet(SCROLLBAR_CSS)

        self.rows_host = QWidget(); self.rows_host.setStyleSheet(f"background:{CARD};")
        self.rows_lay = QVBoxLayout(self.rows_host)
        self.rows_lay.setContentsMargins(0, 0, 0, 0); self.rows_lay.setSpacing(0)
        self.rows_lay.addStretch()
        self.rows_scroll.setWidget(self.rows_host)
        d_lay.addWidget(self.rows_scroll, 1)

        # Empty state
        self.empty = QLabel("No patients found")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setFont(QFont(FONT, 13))
        self.empty.setStyleSheet(
            f"color:{SUBTLE};padding:60px;background:transparent;border:none;")
        self.empty.hide(); d_lay.addWidget(self.empty)

        lay.addWidget(self.directory, 1)

        scroll.setWidget(host); outer.addWidget(scroll)

        # FAB
        self.fab = FAB(self)
        self.fab.clicked.connect(self._open_add_dialog)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fab.reposition(self.rect())

    # ── DATA LOADING ─────────────────────────────────────────────────
    def refresh(self):
        self._all_patients = self._load_patients()
        self._update_metrics()
        self._render_rows(self._apply_filters(self._all_patients))

    def _load_patients(self):
        if not self.db: return []
        try:
            data = self.db.get_patient_directory_data()
            return list(data or [])
        except Exception as e:
            print(f"[PatientsPage] load error: {e}")
            # Fallback: try simple query
            try:
                data = self.db.get_all_patients()
                return list(data or [])
            except Exception as e2:
                print(f"[PatientsPage] fallback error: {e2}")
                return []

    def _update_metrics(self):
        if not self.db: return
        try:
            m = self.db.get_patient_metrics() or {}
            sat = m.get("satisfaction", 0)
            ret = m.get("retention", 0)
            active = m.get("active_records", 0)
            weekly = m.get("weekly_new", 0)
            growth = m.get("growth_pct", 0)

            self.perf_card.update_metrics(
                satisfaction=f"{sat}/5.0" if sat else "--",
                retention=f"{ret}%" if ret else "--",
                note=f"Based on {active} active patient records" if active else
                     "No patient data available")

            self.active_card.set_value(
                f"{active:,}" if active else "0",
                badge_text=f"+{weekly} this week" if weekly else "",
                badge_bg=PRIMARY_FIXED, badge_fg=PRIMARY)

            sign = "+" if growth >= 0 else ""
            self.growth_card.set_value(
                f"{sign}{growth}%" if growth else "0%",
                badge_text="Above monthly target" if growth and growth > 0 else
                           "Below monthly target" if growth and growth < 0 else "",
                badge_bg="#CCE8DA" if growth and growth > 0 else
                         ERROR_CONTAINER if growth and growth < 0 else PRIMARY_FIXED,
                badge_fg=SUCCESS if growth and growth > 0 else
                         DANGER if growth and growth < 0 else PRIMARY)
        except Exception as e:
            print(f"[PatientsPage] metrics error: {e}")

    # ── RENDERING ────────────────────────────────────────────────────
    def _clear_rows(self):
        while self.rows_lay.count():
            it = self.rows_lay.takeAt(0)
            if it and it.widget(): it.widget().deleteLater()

    def _render_rows(self, patients):
        self._clear_rows()
        if not patients:
            self.empty.show(); self.rows_host.hide(); return
        self.empty.hide(); self.rows_host.show()
        for i, p in enumerate(patients):
            row = PatientRow(p, alt=(i % 2 == 1))
            row.manage_clicked.connect(self._open_manage)
            self.rows_lay.addWidget(row)
        self.rows_lay.addStretch(1)

    # ── FILTERING ────────────────────────────────────────────────────
    def _apply_filters(self, patients):
        out = patients
        q = (self.search_bar.search.text() or "").strip().lower()
        if q:
            out = [p for p in out
                   if q in str(_safe_get(p, "patient_name", "name", default="")).lower()
                   or q in str(_safe_get(p, "contact", default="")).lower()
                   or q in str(_safe_get(p, "patient_id", default="")).lower()]
        if self._filter_status:
            out = [p for p in out
                   if _derive_status(
                       _safe_get(p, "appointment_status", "status", default=None)
                   ).lower() == self._filter_status.lower()]
        if self._filter_doctor:
            out = [p for p in out
                   if str(_safe_get(p, "doctor_name", default="") or "").lower()
                   == self._filter_doctor.lower()]
        if self._filter_treatment:
            out = [p for p in out
                   if str(_safe_get(p, "treatment_name", default="") or "").lower()
                   == self._filter_treatment.lower()]
        return out

    def _on_search(self, _text):
        self._render_rows(self._apply_filters(self._all_patients))

    def _show_filter_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu{{background:{CARD};border:1px solid {OUTLINE};"
            f"border-radius:10px;padding:6px;}}"
            f"QMenu::item{{padding:8px 24px;color:{TEXT};border-radius:6px;}}"
            f"QMenu::item:selected{{background:{SURFACE_HIGH};}}"
            f"QMenu::separator{{height:1px;background:{OUTLINE};margin:4px 12px;}}")

        # Status section
        status_header = menu.addAction("Status"); status_header.setEnabled(False)
        for label, key in (("All Statuses", None), ("Active", "active"),
                           ("Pending", "pending"), ("Inactive", "inactive")):
            act = menu.addAction(label)
            if self._filter_status == key:
                act.setText(label + "  *")
            act.triggered.connect(lambda _, k=key: self._set_filter_status(k))

        menu.addSeparator()

        # Doctor section
        if self.db:
            try:
                options = self.db.get_filter_options() or {}
                doctors = options.get("doctors", [])
                if doctors:
                    doc_header = menu.addAction("Doctor"); doc_header.setEnabled(False)
                    all_docs = menu.addAction("All Doctors")
                    all_docs.triggered.connect(lambda: self._set_filter_doctor(None))
                    for d in doctors[:8]:
                        dn = d.get("staff_name", "")
                        act = menu.addAction(dn)
                        if self._filter_doctor and self._filter_doctor.lower() == dn.lower():
                            act.setText(dn + "  *")
                        act.triggered.connect(lambda _, n=dn: self._set_filter_doctor(n))
                    menu.addSeparator()

                treatments = options.get("treatments", [])
                if treatments:
                    trt_header = menu.addAction("Treatment"); trt_header.setEnabled(False)
                    all_trt = menu.addAction("All Treatments")
                    all_trt.triggered.connect(lambda: self._set_filter_treatment(None))
                    for t in treatments[:8]:
                        tn = t.get("treatment_name", "")
                        act = menu.addAction(tn)
                        if self._filter_treatment and self._filter_treatment.lower() == tn.lower():
                            act.setText(tn + "  *")
                        act.triggered.connect(lambda _, n=tn: self._set_filter_treatment(n))
            except Exception as e:
                print(f"[PatientsPage] filter options error: {e}")

        menu.addSeparator()
        clear = menu.addAction("Clear All Filters")
        clear.triggered.connect(self._clear_filters)

        menu.exec(self.search_bar.filter_btn.mapToGlobal(
            self.search_bar.filter_btn.rect().bottomLeft()))

    def _set_filter_status(self, key):
        self._filter_status = key
        self._render_rows(self._apply_filters(self._all_patients))

    def _set_filter_doctor(self, name):
        self._filter_doctor = name
        self._render_rows(self._apply_filters(self._all_patients))

    def _set_filter_treatment(self, name):
        self._filter_treatment = name
        self._render_rows(self._apply_filters(self._all_patients))

    def _clear_filters(self):
        self._filter_status = None
        self._filter_doctor = None
        self._filter_treatment = None
        self.search_bar.search.clear()
        self._render_rows(self._apply_filters(self._all_patients))

    # ── ACTIONS ──────────────────────────────────────────────────────
    def _open_add_dialog(self):
        dlg = AddPatientDialog(self.db, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()
            self._show_toast("Patient added successfully")

    def _open_manage(self, patient: dict):
        # Reload fresh data for this patient
        if self.db:
            try:
                fresh = self.db.get_patient_details(patient.get("patient_id"))
                if fresh:
                    # Merge with directory data
                    fresh.update({k: v for k, v in patient.items()
                                  if k not in fresh or fresh[k] is None})
                    patient = fresh
            except: pass

        dlg = PatientDetailDialog(self.db, patient, self)
        result = dlg.exec()
        if result == QDialog.DialogCode.Accepted:
            self.refresh()
            self._show_toast("Patient updated successfully")

    def _show_toast(self, message):
        toast = ToastNotification(message, SUCCESS, self.window())
        toast.show_at(self.window())