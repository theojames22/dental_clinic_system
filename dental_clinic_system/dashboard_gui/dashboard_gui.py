"""
LC Dental Care - Dashboard (PyQt6)
FIX: Dashboard no longer disappears after switching to Profile and back.
  - All pages created once, added to QStackedWidget once.
  - Refresh methods update widgets IN PLACE, never deleteLater on layout children.
  - PatientStatsCard.update_pct() updates the label text only.
  - AppointmentSplitCard.update_segments() rebuilds only the legend container.
  - Safe refresh methods with RuntimeError guards.
"""

import os
import math
from datetime import datetime, timedelta
from PyQt6.QtCore import (
    Qt, QTimer, QRectF, QPointF, QPropertyAnimation, QEasingCurve, pyqtProperty,
)
from PyQt6.QtGui import (
    QColor, QFont, QPainter, QPen, QBrush, QLinearGradient, QPixmap,
    QPainterPath, QImage,
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QStackedWidget, QLineEdit,
    QGraphicsDropShadowEffect, QButtonGroup, QComboBox, QFileDialog,
    QSizePolicy, QGridLayout, QCheckBox, QSpacerItem,
)
from dashboard_gui.style import Config

# ═════════════════════════════════════════════════════════════════════════
# THEME
# ═════════════════════════════════════════════════════════════════════════
BG                = "#F9F9FF"
CARD              = "#FFFFFF"
SIDEBAR_BG        = "#F2F3FC"
SIDEBAR_BORDER    = "#C2C6D4"
SIDEBAR_ACTIVE_BG = "#D9E3F1"
PRIMARY           = "#003F87"
PRIMARY_CONTAINER = "#0056B3"
PRIMARY_DARK      = "#002A5C"
PRIMARY_FIXED     = "#D7E2FF"
SECONDARY         = "#555F6B"
SECONDARY_FIXED   = "#D9E3F1"
TERTIARY          = "#722B00"
TERTIARY_FIXED    = "#FFDBCC"
TERTIARY_CONTAINER= "#983C00"
ERROR             = "#BA1A1A"
ERROR_CONTAINER   = "#FFDAD6"
TEXT              = "#191C21"
MUTED             = "#555F6B"
SUBTLE            = "#727784"
OUTLINE           = "#C2C6D4"
SURFACE_HIGH      = "#E7E8F0"
SURFACE_VARIANT   = "#E1E2EA"
DANGER            = ERROR
WARNING           = "#D68910"
SUCCESS           = "#1E8449"
FONT              = "Inter"

SPLIT_PALETTE = [
    "#003F87", "#0056B3", "#1E40AF", "#3B82F6",
    "#722B00", "#983C00", "#D68910", "#1E8449",
    "#555F6B", "#BA1A1A", "#7C3AED", "#0891B2",
]


def add_shadow(widget, blur=18, offset_y=4, alpha=12):
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur); effect.setOffset(0, offset_y)
    effect.setColor(QColor(0, 0, 0, alpha)); widget.setGraphicsEffect(effect)


def get_nice_ticks(max_val, num_ticks=5):
    if max_val <= 0: return [0]*(num_ticks+1), 1
    rough = max_val/num_ticks; mag = 10**math.floor(math.log10(rough))
    res = rough/mag
    if res <= 1.5:   step = mag
    elif res <= 3:   step = 2*mag
    elif res <= 7:   step = 5*mag
    else:            step = 10*mag
    mx = math.ceil(max_val/step)*step
    return [int(i*step) for i in range(num_ticks+1)], mx


REVENUE_TICKS = [0, 1000, 3000, 5000, 8000, 10000, 20000]


def map_revenue_to_fraction(value):
    ticks = REVENUE_TICKS; n = len(ticks)-1
    if value <= ticks[0]:  return 0.0
    if value >= ticks[-1]: return 1.0
    for i in range(n):
        a, b = ticks[i], ticks[i+1]
        if a <= value <= b:
            return (i + ((value-a)/(b-a) if b != a else 0)) / n
    return 1.0


# ═════════════════════════════════════════════════════════════════════════
# PROFILE IMAGE LOADER
# ═════════════════════════════════════════════════════════════════════════
def load_profile_pixmap(profile_image, size=40):
    if profile_image is None:
        return None
    if isinstance(profile_image, bytes):
        pm = QPixmap()
        if pm.loadFromData(profile_image):
            return pm.scaled(size, size,
                             Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                             Qt.TransformationMode.SmoothTransformation)
        return None
    if isinstance(profile_image, str) and profile_image.strip():
        if os.path.exists(profile_image):
            pm = QPixmap(profile_image)
            if not pm.isNull():
                return pm.scaled(size, size,
                                 Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                 Qt.TransformationMode.SmoothTransformation)
        return None
    return None


# ═════════════════════════════════════════════════════════════════════════
# USER DATA - fully DB-backed
# ═════════════════════════════════════════════════════════════════════════
class UserData:
    def __init__(self, db, current_user: dict):
        self.db = db
        self.user_id         = current_user.get("user_id")
        self.user_name       = current_user.get("username", "")
        self.user_role       = current_user.get("role", "")
        self.staff_full_name = current_user.get("name", "")
        self.email           = None
        self.phone           = None
        self.profile_image   = None
        self._load_from_db()

    def _load_from_db(self):
        if not self.db or not self.user_id: return
        try:
            p = self.db.get_logged_in_user_profile(self.user_id)
            if not p: return
            self.staff_full_name = p.get("staff_name") or self.staff_full_name or ""
            self.user_name       = p.get("username")   or self.user_name
            self.user_role       = p.get("role")       or self.user_role
            self.email           = p.get("email")
            self.phone           = p.get("phone")
            self.profile_image   = p.get("profile_image")
        except Exception as e:
            print(f"[UserData] DB error: {e}")

    def reload(self): self._load_from_db()

    @property
    def first_name(self):
        n = (self.staff_full_name or self.user_name or "").strip()
        return n.split()[0] if n else "N/A"

    @property
    def display_role(self):
        r = (self.user_role or "").strip()
        return r.title() if r else "N/A"

    @property
    def display_email(self):
        return self.email or "N/A"

    @property
    def display_phone(self):
        return self.phone or "N/A"

    @property
    def initial(self):
        s = self.staff_full_name or self.user_name or ""
        return s[0].upper() if s else "?"


# ═════════════════════════════════════════════════════════════════════════
# ICONS - clean line icons, no emojis
# ═════════════════════════════════════════════════════════════════════════
class IconWidget(QWidget):
    DASHBOARD=0;PATIENTS=1;APPOINTMENTS=2;SERVICES=3;BILLING=4
    INVENTORY=5;REPORTS=6;USERS=7;SETTINGS=8;LOGOUT=9
    BELL=10;SEARCH=11;CALENDAR=12;MONEY=13;ALERT=14
    PROFILE=15;TOOTH=16;CAMERA=17;SHIELD=18
    GROUPS=19;WALLET=20;WARNING=21;MEDICAL_BAG=22
    DIVERSITY=23;SCIENCE=24;CHAT=25;PAYMENTS=26
    MORE_HORIZ=27;TRENDING_UP=28;CLOCK=29;CHECK=30
    CANCEL=31;DOLLAR=32;BOX=33;USER_PLUS=34;LOCK=35
    NOTIFICATION=36;LANGUAGE=37;PALETTE=38;SAVE=39;PLUS=40

    def __init__(self, icon_id, size=20, color=None, filled=False, parent=None):
        super().__init__(parent)
        self.icon_id=icon_id; self._color=color or QColor(MUTED)
        self._filled=filled; self.setFixedSize(size,size)

    def set_color(self,c): self._color=c; self.update()
    def set_filled(self,f): self._filled=f; self.update()

    def paintEvent(self,event):
        w,h=self.width(),self.height()
        if w<4: return
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c=self._color; s=min(w,h)/24.0; cx,cy=w/2.0,h/2.0
        pen=QPen(c,1.7,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen); p.setBrush(QBrush(c) if self._filled else Qt.BrushStyle.NoBrush)
        i=self.icon_id
        if i==self.DASHBOARD:
            p.drawRoundedRect(QRectF(cx-9*s,cy-9*s,8*s,8*s),1.5,1.5)
            p.drawRoundedRect(QRectF(cx+1*s,cy-9*s,8*s,5*s),1.5,1.5)
            p.drawRoundedRect(QRectF(cx-9*s,cy+1*s,8*s,8*s),1.5,1.5)
            p.drawRoundedRect(QRectF(cx+1*s,cy-1*s,8*s,10*s),1.5,1.5)
        elif i in (self.PATIENTS,self.PROFILE):
            p.drawEllipse(QPointF(cx,cy-4*s),4.5*s,4.5*s)
            pa=QPainterPath();pa.moveTo(cx-8*s,cy+9*s)
            pa.cubicTo(QPointF(cx-8*s,cy+1*s),QPointF(cx+8*s,cy+1*s),QPointF(cx+8*s,cy+9*s))
            p.drawPath(pa)
        elif i==self.GROUPS:
            p.drawEllipse(QPointF(cx-5*s,cy-4*s),3*s,3*s)
            p.drawEllipse(QPointF(cx+5*s,cy-4*s),3*s,3*s)
            p.drawEllipse(QPointF(cx,cy-6*s),2.5*s,2.5*s)
            p.drawArc(QRectF(cx-10*s,cy,20*s,10*s),0,180*16)
        elif i in (self.APPOINTMENTS,self.CALENDAR):
            p.drawRoundedRect(QRectF(cx-8*s,cy-8*s,16*s,16*s),2,2)
            p.drawLine(QPointF(cx-8*s,cy-3*s),QPointF(cx+8*s,cy-3*s))
            p.drawLine(QPointF(cx-4*s,cy-11*s),QPointF(cx-4*s,cy-6*s))
            p.drawLine(QPointF(cx+4*s,cy-11*s),QPointF(cx+4*s,cy-6*s))
        elif i in (self.SERVICES,self.MEDICAL_BAG):
            p.drawRoundedRect(QRectF(cx-9*s,cy-5*s,18*s,13*s),2,2)
            p.drawLine(QPointF(cx-4*s,cy-5*s),QPointF(cx-4*s,cy-8*s))
            p.drawLine(QPointF(cx+4*s,cy-5*s),QPointF(cx+4*s,cy-8*s))
            p.drawLine(QPointF(cx-4*s,cy-8*s),QPointF(cx+4*s,cy-8*s))
            p2=QPen(c,2.0);p.setPen(p2)
            p.drawLine(QPointF(cx,cy-1*s),QPointF(cx,cy+5*s))
            p.drawLine(QPointF(cx-3*s,cy+2*s),QPointF(cx+3*s,cy+2*s))
        elif i in (self.BILLING,self.WALLET,self.DOLLAR):
            p.drawRoundedRect(QRectF(cx-9*s,cy-7*s,18*s,14*s),2,2)
            p.drawLine(QPointF(cx-9*s,cy-2*s),QPointF(cx+9*s,cy-2*s))
        elif i in (self.INVENTORY,self.BOX):
            p.drawRoundedRect(QRectF(cx-9*s,cy-8*s,18*s,16*s),2,2)
            p.drawLine(QPointF(cx-9*s,cy-3*s),QPointF(cx+9*s,cy-3*s))
            p.drawLine(QPointF(cx,cy-8*s),QPointF(cx,cy-3*s))
        elif i==self.REPORTS:
            p.drawLine(QPointF(cx-7*s,cy+8*s),QPointF(cx-7*s,cy+2*s))
            p.drawLine(QPointF(cx,cy+8*s),QPointF(cx,cy-4*s))
            p.drawLine(QPointF(cx+7*s,cy+8*s),QPointF(cx+7*s,cy-8*s))
        elif i==self.USERS:
            p.drawEllipse(QPointF(cx-4*s,cy-4*s),3.5*s,3.5*s)
            p.drawEllipse(QPointF(cx+4*s,cy-4*s),3.5*s,3.5*s)
            p.drawArc(QRectF(cx-9*s,cy,18*s,12*s),0,180*16)
        elif i==self.SETTINGS:
            p.drawEllipse(QPointF(cx,cy),3.5*s,3.5*s)
            for a in range(0,360,45):
                r=math.radians(a)
                p.drawLine(QPointF(cx+math.cos(r)*6*s,cy+math.sin(r)*6*s),
                           QPointF(cx+math.cos(r)*9*s,cy+math.sin(r)*9*s))
        elif i==self.LOGOUT:
            p.drawLine(QPointF(cx-8*s,cy-8*s),QPointF(cx-2*s,cy-8*s))
            p.drawLine(QPointF(cx-8*s,cy+8*s),QPointF(cx-2*s,cy+8*s))
            p.drawLine(QPointF(cx-8*s,cy-8*s),QPointF(cx-8*s,cy+8*s))
            p.drawLine(QPointF(cx,cy),QPointF(cx+9*s,cy))
            p.drawLine(QPointF(cx+5*s,cy-4*s),QPointF(cx+9*s,cy))
            p.drawLine(QPointF(cx+5*s,cy+4*s),QPointF(cx+9*s,cy))
        elif i==self.BELL:
            pa=QPainterPath();pa.moveTo(cx-7*s,cy+4*s)
            pa.lineTo(cx+7*s,cy+4*s);pa.lineTo(cx+5*s,cy+1*s)
            pa.lineTo(cx+5*s,cy-4*s)
            pa.cubicTo(QPointF(cx+5*s,cy-9*s),QPointF(cx-5*s,cy-9*s),QPointF(cx-5*s,cy-4*s))
            pa.lineTo(cx-5*s,cy+1*s);pa.closeSubpath();p.drawPath(pa)
            p.drawArc(QRectF(cx-2.5*s,cy+4*s,5*s,5*s),200*16,140*16)
        elif i==self.SEARCH:
            p.drawEllipse(QPointF(cx-1*s,cy-1*s),6*s,6*s)
            p.drawLine(QPointF(cx+3*s,cy+3*s),QPointF(cx+8*s,cy+8*s))
        elif i in (self.WARNING,self.ALERT):
            pa=QPainterPath();pa.moveTo(cx,cy-9*s)
            pa.lineTo(cx+10*s,cy+8*s);pa.lineTo(cx-10*s,cy+8*s);pa.closeSubpath()
            p.drawPath(pa);p2=QPen(c,2.2);p.setPen(p2)
            p.drawLine(QPointF(cx,cy-4*s),QPointF(cx,cy+2*s))
            p.setBrush(QBrush(c));p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(cx,cy+5*s),1.2,1.2)
        elif i==self.CLOCK:
            p.drawEllipse(QPointF(cx,cy),9*s,9*s)
            p.drawLine(QPointF(cx,cy),QPointF(cx,cy-5*s))
            p.drawLine(QPointF(cx,cy),QPointF(cx+4*s,cy+2*s))
        elif i==self.CHECK:
            p.drawLine(QPointF(cx-6*s,cy),QPointF(cx-2*s,cy+5*s))
            p.drawLine(QPointF(cx-2*s,cy+5*s),QPointF(cx+7*s,cy-5*s))
        elif i==self.CANCEL:
            p.drawLine(QPointF(cx-5*s,cy-5*s),QPointF(cx+5*s,cy+5*s))
            p.drawLine(QPointF(cx+5*s,cy-5*s),QPointF(cx-5*s,cy+5*s))
        elif i==self.USER_PLUS:
            p.drawEllipse(QPointF(cx-3*s,cy-5*s),3.5*s,3.5*s)
            pa=QPainterPath();pa.moveTo(cx-8*s,cy+6*s)
            pa.cubicTo(QPointF(cx-8*s,cy),QPointF(cx+2*s,cy),QPointF(cx+2*s,cy+6*s))
            p.drawPath(pa)
            p.drawLine(QPointF(cx+5*s,cy-2*s),QPointF(cx+9*s,cy-2*s))
            p.drawLine(QPointF(cx+7*s,cy-4*s),QPointF(cx+7*s,cy))
        elif i==self.TRENDING_UP:
            p.drawLine(QPointF(cx-8*s,cy+4*s),QPointF(cx-2*s,cy-2*s))
            p.drawLine(QPointF(cx-2*s,cy-2*s),QPointF(cx+2*s,cy+2*s))
            p.drawLine(QPointF(cx+2*s,cy+2*s),QPointF(cx+8*s,cy-4*s))
            p.drawLine(QPointF(cx+8*s,cy-4*s),QPointF(cx+4*s,cy-4*s))
            p.drawLine(QPointF(cx+8*s,cy-4*s),QPointF(cx+8*s,cy))
        elif i==self.CAMERA:
            p.drawRoundedRect(QRectF(cx-9*s,cy-5*s,18*s,12*s),2,2)
            p.drawEllipse(QPointF(cx,cy+1*s),3.5*s,3.5*s)
        elif i==self.LOCK:
            p.drawRoundedRect(QRectF(cx-6*s,cy,12*s,10*s),2,2)
            p.drawArc(QRectF(cx-4*s,cy-8*s,8*s,10*s),0,-180*16)
        elif i==self.NOTIFICATION:
            p.drawEllipse(QPointF(cx,cy-4*s),4.5*s,4.5*s)
            p.drawLine(QPointF(cx,cy+1*s),QPointF(cx,cy+6*s))
            p.drawLine(QPointF(cx-5*s,cy+8*s),QPointF(cx+5*s,cy+8*s))
        elif i==self.LANGUAGE:
            p.drawEllipse(QPointF(cx,cy),9*s,9*s)
            p.drawLine(QPointF(cx-9*s,cy),QPointF(cx+9*s,cy))
            p.drawArc(QRectF(cx-5*s,cy-9*s,10*s,18*s),0,180*16)
            p.drawArc(QRectF(cx-5*s,cy-9*s,10*s,18*s),180*16,180*16)
        elif i==self.PALETTE:
            p.drawEllipse(QPointF(cx,cy),9*s,9*s)
            for a in range(0,360,60):
                r=math.radians(a)
                p.setBrush(QBrush(c));p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(cx+math.cos(r)*5*s,cy+math.sin(r)*5*s),2*s,2*s)
            p.setPen(pen);p.setBrush(Qt.BrushStyle.NoBrush)
        elif i==self.SAVE:
            p.drawRoundedRect(QRectF(cx-8*s,cy-9*s,16*s,18*s),2,2)
            p.drawLine(QPointF(cx-8*s,cy-3*s),QPointF(cx+8*s,cy-3*s))
            p.drawRoundedRect(QRectF(cx-4*s,cy-8*s,8*s,5*s),1,1)
            p.drawRoundedRect(QRectF(cx-5*s,cy+1*s,10*s,6*s),1,1)
        elif i==self.PLUS:
            p.drawLine(QPointF(cx-7*s,cy),QPointF(cx+7*s,cy))
            p.drawLine(QPointF(cx,cy-7*s),QPointF(cx,cy+7*s))
        else:
            p.drawEllipse(QPointF(cx,cy),8*s,8*s)
        p.end()


# ═════════════════════════════════════════════════════════════════════════
# BRAND BLOCK
# ═════════════════════════════════════════════════════════════════════════
class BrandBlock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay=QHBoxLayout(self);lay.setContentsMargins(0,0,0,0);lay.setSpacing(12)
        icon_box=QFrame();icon_box.setFixedSize(40,40)
        icon_box.setStyleSheet(f"background:{PRIMARY_CONTAINER};border-radius:10px;")
        ib=QVBoxLayout(icon_box);ib.setContentsMargins(0,0,0,0)
        ib.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ib.addWidget(IconWidget(IconWidget.MEDICAL_BAG,22,QColor("#FFFFFF")))
        lay.addWidget(icon_box)
        col=QVBoxLayout();col.setSpacing(0)
        t=QLabel(getattr(Config,"APP_NAME","LC Dental Care"))
        t.setStyleSheet(f"color:{PRIMARY};background:transparent;border:none;")
        t.setFont(QFont(FONT,14,QFont.Weight.Bold))
        s=QLabel("Clinic Management")
        s.setStyleSheet(f"color:{SECONDARY};background:transparent;border:none;")
        s.setFont(QFont(FONT,9,QFont.Weight.Medium))
        col.addWidget(t);col.addWidget(s);lay.addLayout(col);lay.addStretch()


# ═════════════════════════════════════════════════════════════════════════
# SIDEBAR - no ghost text, exclusive group
# ═════════════════════════════════════════════════════════════════════════
class SidebarButton(QPushButton):
    def __init__(self, label, icon_id, parent=None):
        super().__init__(parent)
        self.setText("")  # no QPushButton text = no ghost
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(44)
        self._label_text = label
        lay=QHBoxLayout(self);lay.setContentsMargins(16,0,12,0);lay.setSpacing(14)
        self._icon=IconWidget(icon_id,22,QColor(SECONDARY));lay.addWidget(self._icon)
        self._text=QLabel(label);self._text.setFont(QFont(FONT,10,QFont.Weight.Medium))
        lay.addWidget(self._text);lay.addStretch()
        self._update_style()

    def _update_style(self):
        if self.isChecked():
            self.setStyleSheet(
                f"QPushButton{{text-align:left;border:none;background:{SIDEBAR_ACTIVE_BG};"
                f"border-left:4px solid {PRIMARY};border-top-right-radius:10px;"
                f"border-bottom-right-radius:10px;padding-left:0px;}}"
                f"QPushButton:hover{{background:{SIDEBAR_ACTIVE_BG};}}")
            self._text.setStyleSheet(f"color:{PRIMARY};background:transparent;border:none;font-weight:600;")
            self._icon.set_color(QColor(PRIMARY));self._icon.set_filled(True)
        else:
            self.setStyleSheet(
                f"QPushButton{{text-align:left;border:none;background:transparent;"
                f"border-radius:10px;padding-left:4px;}}"
                f"QPushButton:hover{{background:{SURFACE_HIGH};}}")
            self._text.setStyleSheet(f"color:{SECONDARY};background:transparent;border:none;")
            self._icon.set_color(QColor(SECONDARY));self._icon.set_filled(False)

    def checkStateSet(self): self._update_style()
    def nextCheckState(self): super().nextCheckState(); self._update_style()


class Sidebar(QFrame):
    ITEMS = [
        ("Dashboard",             IconWidget.DASHBOARD),
        ("Patients",              IconWidget.PATIENTS),
        ("Appointments",          IconWidget.APPOINTMENTS),
        ("Services & Treatments", IconWidget.SERVICES),
        ("Billing & Payments",    IconWidget.BILLING),
        ("Inventory",             IconWidget.INVENTORY),
        ("Reports",               IconWidget.REPORTS),
        ("Users",                 IconWidget.USERS),
        ("Settings",              IconWidget.SETTINGS),
        ("Profile",               IconWidget.PROFILE),
    ]
    def __init__(self, on_nav, on_logout=None, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self.setStyleSheet(f"background:{SIDEBAR_BG};border-right:1px solid {SIDEBAR_BORDER};")
        lay=QVBoxLayout(self);lay.setContentsMargins(16,24,8,24);lay.setSpacing(4)
        bw=QWidget();bwl=QVBoxLayout(bw);bwl.setContentsMargins(8,0,8,0)
        bwl.addWidget(BrandBlock());lay.addWidget(bw);lay.addSpacing(20)
        self.group=QButtonGroup(self);self.group.setExclusive(True)
        for i,(label,icon_id) in enumerate(self.ITEMS):
            btn=SidebarButton(label,icon_id)
            self.group.addButton(btn,i);lay.addWidget(btn)
            if i==0: btn.setChecked(True);btn._update_style()
        self.group.idClicked.connect(on_nav)
        lay.addStretch()
        sep=QFrame();sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{OUTLINE};margin:12px 8px;");lay.addWidget(sep)
        logout_btn=SidebarButton("Logout",IconWidget.LOGOUT)
        if on_logout: logout_btn.clicked.connect(on_logout)
        lay.addWidget(logout_btn)


# ═════════════════════════════════════════════════════════════════════════
# TOP BAR
# ═════════════════════════════════════════════════════════════════════════
class TopBar(QFrame):
    def __init__(self, user_data: UserData, on_search=None):
        super().__init__()
        self.setFixedHeight(64)
        self.setStyleSheet(f"background:{BG};border-bottom:1px solid {OUTLINE};")
        self._user_data = user_data
        lay=QHBoxLayout(self);lay.setContentsMargins(24,0,24,0);lay.setSpacing(16)

        sw=QFrame();sw.setFixedHeight(40);sw.setMinimumWidth(360);sw.setMaximumWidth(520)
        sw.setStyleSheet(f"background:{CARD};border:1px solid {OUTLINE};border-radius:20px;")
        sl=QHBoxLayout(sw);sl.setContentsMargins(14,0,14,0);sl.setSpacing(8)
        sl.addWidget(IconWidget(IconWidget.SEARCH,18,QColor(SUBTLE)))
        search=QLineEdit();search.setPlaceholderText("Search patients, records, or inventory...")
        search.setStyleSheet(f"QLineEdit{{background:transparent;border:none;color:{TEXT};font-size:13px;}}")
        if on_search: search.textChanged.connect(on_search)
        sl.addWidget(search,1);lay.addWidget(sw,1);lay.addStretch()

        bb=QPushButton();bb.setFixedSize(40,40);bb.setCursor(Qt.CursorShape.PointingHandCursor)
        bb.setStyleSheet("QPushButton{background:transparent;border:none;border-radius:20px;}"
                         f"QPushButton:hover{{background:{SURFACE_HIGH};}}")
        bl=QVBoxLayout(bb);bl.setContentsMargins(0,0,0,0);bl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.addWidget(IconWidget(IconWidget.BELL,22,QColor(MUTED)))
        bww=QWidget();bww_l=QVBoxLayout(bww);bww_l.setContentsMargins(0,0,0,0)
        bww.setFixedSize(44,44);bww_l.addWidget(bb)
        dot=QFrame(bww);dot.setFixedSize(8,8)
        dot.setStyleSheet(f"background:{ERROR};border:2px solid {BG};border-radius:4px;")
        dot.move(28,8);lay.addWidget(bww)

        dv=QFrame();dv.setFixedSize(1,28);dv.setStyleSheet(f"background:{OUTLINE};");lay.addWidget(dv)

        fn=self._user_data.first_name;rl=self._user_data.display_role
        self._name_label=QLabel(fn)
        self._name_label.setStyleSheet(f"color:{PRIMARY};background:transparent;border:none;font-weight:600;")
        self._name_label.setFont(QFont(FONT,11,QFont.Weight.Bold))
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._role_label=QLabel(rl)
        self._role_label.setStyleSheet(f"color:{SECONDARY};background:transparent;border:none;")
        self._role_label.setFont(QFont(FONT,9))
        self._role_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        ub=QVBoxLayout();ub.setSpacing(0);ub.setContentsMargins(0,0,0,0)
        ub.addWidget(self._name_label);ub.addWidget(self._role_label);lay.addLayout(ub)

        self._avatar=QLabel();self._avatar.setFixedSize(40,40)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_avatar();lay.addWidget(self._avatar)

    def _apply_avatar(self):
        pm=load_profile_pixmap(self._user_data.profile_image,40)
        if pm:
            self._avatar.setPixmap(pm)
            self._avatar.setStyleSheet(f"border:1px solid {OUTLINE};border-radius:20px;")
        else:
            self._avatar.setText(self._user_data.initial)
            self._avatar.setFont(QFont(FONT,14,QFont.Weight.Bold))
            self._avatar.setStyleSheet(f"background:{PRIMARY};color:white;border-radius:20px;")

    def refresh_avatar(self):
        """Safe refresh of topbar user info."""
        try:
            self._apply_avatar()
            self._name_label.setText(self._user_data.first_name)
            self._role_label.setText(self._user_data.display_role)
        except RuntimeError:
            pass  # Widget already deleted


# ═════════════════════════════════════════════════════════════════════════
# STAT CARD - NO hover
# ═════════════════════════════════════════════════════════════════════════
class StatCard(QFrame):
    def __init__(self, title, value, icon_id, icon_bg, icon_fg,
                 value_color=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"StatCard{{background:{CARD};border-radius:14px;"
            f"border:1px solid transparent;}}")
        add_shadow(self,blur=14,offset_y=4,alpha=12)
        self.setMinimumHeight(100)
        lay=QHBoxLayout(self);lay.setContentsMargins(20,16,20,16);lay.setSpacing(16)
        icon_frame=QFrame();icon_frame.setFixedSize(48,48)
        icon_frame.setStyleSheet(f"background:{icon_bg};border-radius:24px;")
        il=QVBoxLayout(icon_frame);il.setContentsMargins(0,0,0,0)
        il.setAlignment(Qt.AlignmentFlag.AlignCenter)
        il.addWidget(IconWidget(icon_id,24,QColor(icon_fg),filled=True))
        lay.addWidget(icon_frame)
        col=QVBoxLayout();col.setSpacing(2)
        t=QLabel(title);t.setWordWrap(True)
        t.setStyleSheet(f"color:{MUTED};background:transparent;border:none;")
        t.setFont(QFont(FONT,9,QFont.Weight.Medium));col.addWidget(t)
        self._value_label=QLabel(str(value))
        self._value_label.setStyleSheet(f"color:{value_color or PRIMARY};background:transparent;border:none;")
        self._value_label.setFont(QFont(FONT,20,QFont.Weight.Bold))
        col.addWidget(self._value_label)
        lay.addLayout(col);lay.addStretch()

    def set_value(self, v):
        try: self._value_label.setText(str(v))
        except RuntimeError: pass


# ═════════════════════════════════════════════════════════════════════════
# ANIMATED BAR CHART
# ═════════════════════════════════════════════════════════════════════════
class AnimatedBarChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._values=[];self._old_values=[];self._labels=[]
        self._color=QColor(PRIMARY_CONTAINER);self._progress=0.0
        self.setMinimumHeight(220);self._anim=None

    def set_data(self, values, labels, color=None):
        nv=[float(v) for v in (values or [])]
        nl=list(labels or [])
        if len(self._old_values)!=len(nv): self._old_values=[0.0]*len(nv)
        else:
            c=[]
            for i,v in enumerate(self._values):
                o=self._old_values[i] if i<len(self._old_values) else 0.0
                c.append(o+(v-o)*self._progress)
            self._old_values=c
        self._values=nv;self._labels=nl
        if color: self._color=QColor(color)
        self._progress=0.0
        if self._anim: self._anim.stop()
        self._anim=QPropertyAnimation(self,b"progress")
        self._anim.setDuration(700);self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.setStartValue(0.0);self._anim.setEndValue(1.0);self._anim.start()

    def get_progress(self): return self._progress
    def set_progress(self,v): self._progress=v;self.update()
    progress=pyqtProperty(float,get_progress,set_progress)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h=self.width(),self.height()
        pl,pr,pt,pb=56,8,8,36;cw=max(1,w-pl-pr);ch=max(1,h-pt-pb)
        p.setPen(QColor(SECONDARY));p.setFont(QFont(FONT,8,QFont.Weight.Medium))
        for i,val in enumerate(REVENUE_TICKS):
            f=i/(len(REVENUE_TICKS)-1);y=pt+ch-f*ch
            p.drawText(QRectF(0,y-8,pl-8,16),Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter,f"{val:,}")
            gp=QPen(QColor(SURFACE_VARIANT),0.6,Qt.PenStyle.DashLine);p.setPen(gp)
            p.drawLine(QPointF(pl,y),QPointF(pl+cw,y))
            p.setPen(QColor(SECONDARY));p.setFont(QFont(FONT,8,QFont.Weight.Medium))
        p.setPen(QPen(QColor(OUTLINE),1))
        p.drawLine(QPointF(pl,pt+ch),QPointF(pl+cw,pt+ch))
        if not self._values: p.end();return
        n=len(self._values);gap=max(4,int(cw/(n*6)));bw2=max(4,(cw-gap*(n-1))/n)
        for i,v in enumerate(self._values):
            o=self._old_values[i] if i<len(self._old_values) else 0.0
            cv=o+(v-o)*self._progress;frac=map_revenue_to_fraction(cv);bh=frac*ch
            x=pl+i*(bw2+gap);y=pt+ch-bh;r=min(4,bw2/3)
            color=self._color if cv>0 else QColor(SURFACE_VARIANT)
            g=QLinearGradient(0,y,0,y+max(1,bh))
            g.setColorAt(0,color);g.setColorAt(1,QColor(color.red(),color.green(),color.blue(),180))
            pa=QPainterPath();pa.addRoundedRect(QRectF(x,y,bw2,max(2,bh)),r,r)
            p.setPen(Qt.PenStyle.NoPen);p.setBrush(QBrush(g));p.drawPath(pa)
        p.setPen(QColor(SECONDARY));p.setFont(QFont(FONT,8,QFont.Weight.Medium))
        for i,l in enumerate(self._labels[:n]):
            x=pl+i*(bw2+gap)
            p.drawText(QRectF(x,pt+ch+6,bw2,18),Qt.AlignmentFlag.AlignCenter,str(l))
        p.end()


# ═════════════════════════════════════════════════════════════════════════
# ANIMATED LINE CHART
# ═════════════════════════════════════════════════════════════════════════
class AnimatedLineChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._values=[];self._old_values=[];self._labels=[]
        self._color=QColor(PRIMARY);self._y_max=10;self._progress=0.0
        self.setMinimumHeight(220);self._anim=None

    def set_data(self, values, labels, color=None, y_max=None):
        def tf(x):
            try: return float(x)
            except:
                if isinstance(x,(list,tuple)) and x:
                    try: return float(x[0])
                    except: return 0.0
                return 0.0
        nv=[tf(v) for v in (values or [])]
        if len(self._old_values)!=len(nv): self._old_values=[0.0]*len(nv)
        else:
            c=[]
            for i,v in enumerate(self._values):
                o=self._old_values[i] if i<len(self._old_values) else 0.0
                c.append(o+(v-o)*self._progress)
            self._old_values=c
        self._values=nv;self._labels=list(labels or [])
        if color: self._color=QColor(color)
        if y_max is None: y_max=max(nv)*1.25 if nv else 10
        self._y_max=max(y_max,1);self._progress=0.0
        if self._anim: self._anim.stop()
        self._anim=QPropertyAnimation(self,b"progress")
        self._anim.setDuration(700);self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.setStartValue(0.0);self._anim.setEndValue(1.0);self._anim.start()

    def get_progress(self): return self._progress
    def set_progress(self,v): self._progress=v;self.update()
    progress=pyqtProperty(float,get_progress,set_progress)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h=self.width(),self.height()
        pl,pr,pt,pb=44,8,8,36;cw=max(1,w-pl-pr);ch=max(1,h-pt-pb)
        ticks,mx=get_nice_ticks(self._y_max)
        if mx<=0: mx=1
        for i,val in enumerate(ticks):
            f=i/(len(ticks)-1) if len(ticks)>1 else 0;y=pt+ch-f*ch
            p.setPen(QColor(SECONDARY));p.setFont(QFont(FONT,8,QFont.Weight.Medium))
            p.drawText(QRectF(0,y-8,pl-6,16),Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter,str(val))
            gp=QPen(QColor(SURFACE_VARIANT),0.6,Qt.PenStyle.DashLine);p.setPen(gp)
            p.drawLine(QPointF(pl,y),QPointF(pl+cw,y))
        p.setPen(QPen(QColor(OUTLINE),1))
        p.drawLine(QPointF(pl,pt+ch),QPointF(pl+cw,pt+ch))
        if len(self._values)<1: p.end();return
        n=len(self._values);pts=[]
        for i,v in enumerate(self._values):
            o=self._old_values[i] if i<len(self._old_values) else 0.0
            cv=o+(v-o)*self._progress
            x=pl+(cw/max(1,n-1))*i if n>1 else pl+cw/2
            y=pt+ch-(cv/mx)*ch;pts.append(QPointF(x,y))
        pa=QPainterPath();pa.moveTo(pts[0])
        for i in range(len(pts)-1):
            a,b=pts[i],pts[i+1];m=(a.x()+b.x())/2
            pa.cubicTo(QPointF(m,a.y()),QPointF(m,b.y()),b)
        fill=QPainterPath(pa)
        fill.lineTo(pts[-1].x(),pt+ch);fill.lineTo(pts[0].x(),pt+ch);fill.closeSubpath()
        g=QLinearGradient(0,pt,0,pt+ch)
        g.setColorAt(0,QColor(self._color.red(),self._color.green(),self._color.blue(),60))
        g.setColorAt(1,QColor(self._color.red(),self._color.green(),self._color.blue(),0))
        p.setBrush(QBrush(g));p.setPen(Qt.PenStyle.NoPen);p.drawPath(fill)
        pen=QPen(self._color,2.5,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen);p.setBrush(Qt.BrushStyle.NoBrush);p.drawPath(pa)
        p.setBrush(self._color);p.setPen(Qt.PenStyle.NoPen)
        for pt2 in pts: p.drawEllipse(pt2,3.0,3.0)
        p.setPen(QColor(SECONDARY));p.setFont(QFont(FONT,8,QFont.Weight.Medium))
        for i,l in enumerate(self._labels[:n]):
            x=pl+(cw/max(1,n-1))*i if n>1 else pl+cw/2
            p.drawText(QRectF(x-24,pt+ch+6,48,18),Qt.AlignmentFlag.AlignCenter,str(l))
        p.end()


# ═════════════════════════════════════════════════════════════════════════
# DONUT CHART
# ═════════════════════════════════════════════════════════════════════════
class DonutChart(QWidget):
    def __init__(self, segments, parent=None):
        super().__init__(parent)
        self.segments=segments if segments else [];self.setMinimumSize(140,140)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        sz=min(self.width(),self.height())-20
        x=(self.width()-sz)/2;y=(self.height()-sz)/2;rect=QRectF(x,y,sz,sz)
        pen=QPen(QColor(SURFACE_VARIANT));pen.setWidth(14)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        p.setPen(pen);p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(rect.adjusted(8,8,-8,-8))
        if self.segments:
            start=90*16
            for _,pct,color in self.segments:
                span=-int(360*16*(pct/100.0))
                pen=QPen(QColor(color));pen.setWidth(14)
                pen.setCapStyle(Qt.PenCapStyle.FlatCap);p.setPen(pen)
                p.drawArc(rect.adjusted(8,8,-8,-8),start,span);start+=span
            total_pct=sum(pct for _,pct,_ in self.segments)
            p.setPen(QColor(PRIMARY));p.setFont(QFont(FONT,18,QFont.Weight.Bold))
            p.drawText(rect,Qt.AlignmentFlag.AlignCenter,f"{total_pct:.0f}%")
        else:
            p.setPen(QColor(MUTED));p.setFont(QFont(FONT,14,QFont.Weight.Bold))
            p.drawText(rect,Qt.AlignmentFlag.AlignCenter,"--")
        p.end()


# ═════════════════════════════════════════════════════════════════════════
# PATIENT STATS CARD - with update_pct() for IN-PLACE updates
# ═════════════════════════════════════════════════════════════════════════
class PatientStatsCard(QFrame):
    """Blue gradient card showing patient growth %.
    KEY FIX: has update_pct() so we NEVER delete/recreate this widget."""

    def __init__(self, pct, parent=None):
        super().__init__(parent)
        self._pct = pct
        self.setMinimumHeight(180)
        self.setStyleSheet(
            f"PatientStatsCard{{background:qlineargradient("
            f"x1:0,y1:0,x2:1,y2:1,stop:0 {PRIMARY_CONTAINER},stop:1 {PRIMARY});"
            f"border-radius:16px;}}")
        add_shadow(self,blur=18,offset_y=6,alpha=24)
        self._build_ui()

    def _build_ui(self):
        lay=QVBoxLayout(self);lay.setContentsMargins(24,22,24,22);lay.setSpacing(4)
        t=QLabel("Patient Statistics")
        t.setFont(QFont(FONT,16,QFont.Weight.Bold))
        t.setStyleSheet("color:white;background:transparent;border:none;")
        lay.addWidget(t)
        s=QLabel("Growth since last month")
        s.setStyleSheet("color:rgba(255,255,255,0.85);background:transparent;border:none;")
        s.setFont(QFont(FONT,10));lay.addWidget(s)
        lay.addStretch()
        row=QHBoxLayout();row.setSpacing(6);row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        try: pv=float(self._pct)
        except: pv=0.0
        sign="+" if pv>=0 else ""
        self._pct_label=QLabel(f"{sign}{pv:.1f}%")
        self._pct_label.setFont(QFont(FONT,30,QFont.Weight.Bold))
        self._pct_label.setStyleSheet("color:white;background:transparent;border:none;")
        row.addWidget(self._pct_label)
        row.addWidget(IconWidget(IconWidget.TRENDING_UP,18,QColor("#FFFFFF")),
                      0,Qt.AlignmentFlag.AlignBottom)
        row.addStretch()
        lay.addLayout(row)

    def update_pct(self, pct):
        """Update the percentage label IN PLACE - never destroys the widget."""
        self._pct = pct
        try:
            pv = float(pct)
        except:
            pv = 0.0
        sign = "+" if pv >= 0 else ""
        try:
            self._pct_label.setText(f"{sign}{pv:.1f}%")
        except RuntimeError:
            pass  # Widget already deleted

    def paintEvent(self, event):
        # Keep the gradient background on repaint
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        grad = QLinearGradient(0, 0, rect.width(), rect.height())
        grad.setColorAt(0, QColor(PRIMARY_CONTAINER))
        grad.setColorAt(1, QColor(PRIMARY))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(0, 0, rect.width(), rect.height()), 16, 16)
        p.end()
        # Let children paint
        super().paintEvent(event)


# ═════════════════════════════════════════════════════════════════════════
# APPOINTMENT SPLIT CARD - safe update_segments
# ═════════════════════════════════════════════════════════════════════════
class AppointmentSplitCard(QFrame):
    """KEY FIX: update_segments() only rebuilds the legend container,
    never the card itself or its top-level layout."""

    def __init__(self, segments, parent=None):
        super().__init__(parent)
        self.segments = segments or []
        self._legend_widgets = []
        self.setStyleSheet(
            f"AppointmentSplitCard{{background:{CARD};border-radius:16px;"
            f"border:1px solid {OUTLINE};}}")
        add_shadow(self,blur=14,offset_y=4,alpha=10)
        self._build()

    def _build(self):
        lay=QVBoxLayout(self);lay.setContentsMargins(20,20,20,20);lay.setSpacing(10)
        # Title - persistent
        t=QLabel("APPOINTMENT SPLIT")
        t.setStyleSheet(f"color:{SECONDARY};letter-spacing:1.5px;background:transparent;border:none;")
        t.setFont(QFont(FONT,9,QFont.Weight.Bold));lay.addWidget(t)
        # Donut - persistent
        self._donut=DonutChart(self.segments)
        dw=QHBoxLayout();dw.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dw.addWidget(self._donut);lay.addLayout(dw)
        # Legend container - rebuilt on update
        self._legend_container=QWidget()
        self._legend_container.setStyleSheet("background:transparent;border:none;")
        self._legend_lay=QVBoxLayout(self._legend_container)
        self._legend_lay.setContentsMargins(0,0,0,0);self._legend_lay.setSpacing(6)
        lay.addWidget(self._legend_container)
        self._build_legend()

    def _build_legend(self):
        # Remove old legend rows safely
        for w in self._legend_widgets:
            try:
                w.setParent(None)
                w.deleteLater()
            except RuntimeError:
                pass
        self._legend_widgets.clear()
        if self.segments:
            for label,pct,color in self.segments:
                row=self._make_legend_row(label,pct,color)
                self._legend_lay.addWidget(row)
                self._legend_widgets.append(row)
        else:
            e=QLabel("No appointment data yet")
            e.setAlignment(Qt.AlignmentFlag.AlignCenter)
            e.setStyleSheet(f"color:{MUTED};padding:12px;background:transparent;border:none;")
            e.setFont(QFont(FONT,10))
            self._legend_lay.addWidget(e)
            self._legend_widgets.append(e)

    def _make_legend_row(self, label, pct, color):
        row=QWidget();row.setStyleSheet("background:transparent;border:none;")
        h=QHBoxLayout(row);h.setContentsMargins(0,0,0,0);h.setSpacing(8)
        dot=QFrame();dot.setFixedSize(10,10)
        dot.setStyleSheet(f"background:{color};border-radius:5px;");h.addWidget(dot)
        n=QLabel(str(label));n.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        n.setFont(QFont(FONT,10));h.addWidget(n);h.addStretch()
        v=QLabel(f"{pct}%");v.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        v.setFont(QFont(FONT,10,QFont.Weight.Bold));h.addWidget(v)
        return row

    def update_segments(self, segments):
        """Safe update: only rebuild legend, never the card layout."""
        self.segments = segments or []
        try:
            self._donut.segments = self.segments
            self._donut.update()
            self._build_legend()
        except RuntimeError:
            pass  # Widgets already deleted


# ═════════════════════════════════════════════════════════════════════════
# CHART CARD
# ═════════════════════════════════════════════════════════════════════════
class ChartCard(QFrame):
    PERIODS=[("Today",1),("Month",30),("Year",365)]

    def __init__(self, db, parent=None):
        super().__init__(parent);self.db=db
        self.setStyleSheet(f"ChartCard{{background:{CARD};border-radius:16px;border:1px solid {OUTLINE};}}")
        add_shadow(self,blur=16,offset_y=4,alpha=12)
        lay=QVBoxLayout(self);lay.setContentsMargins(24,24,24,24);lay.setSpacing(20)
        header=QHBoxLayout();col=QVBoxLayout();col.setSpacing(2)
        t=QLabel("Revenue & Appointments Analytics")
        t.setStyleSheet(f"color:{PRIMARY};background:transparent;border:none;")
        t.setFont(QFont(FONT,15,QFont.Weight.Bold));col.addWidget(t)
        s=QLabel("Comprehensive performance tracking across services")
        s.setStyleSheet(f"color:{SECONDARY};background:transparent;border:none;")
        s.setFont(QFont(FONT,10));col.addWidget(s)
        header.addLayout(col);header.addStretch()
        self.combo=QComboBox();self.combo.setFixedHeight(34);self.combo.setMinimumWidth(120)
        self.combo.setCursor(Qt.CursorShape.PointingHandCursor)
        for l,_ in self.PERIODS: self.combo.addItem(l)
        self.combo.setStyleSheet(
            f"QComboBox{{background:{SIDEBAR_BG};border:1px solid {OUTLINE};"
            f"border-radius:8px;padding:0 12px;color:{PRIMARY};font-size:12px;font-weight:600;}}"
            f"QComboBox::drop-down{{border:none;width:22px;}}"
            f"QComboBox QAbstractItemView{{background:{CARD};border:1px solid {OUTLINE};"
            f"selection-background-color:{SIDEBAR_ACTIVE_BG};selection-color:{PRIMARY};outline:0;padding:4px;}}")
        header.addWidget(self.combo);lay.addLayout(header)
        cr=QHBoxLayout();cr.setSpacing(24)
        bc=QVBoxLayout();bc.setSpacing(4)
        self.bar_chart=AnimatedBarChart();bc.addWidget(self.bar_chart,1)
        self.bar_cap=QLabel("Hourly Revenue");self.bar_cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bar_cap.setStyleSheet(f"color:{PRIMARY};background:transparent;border:none;")
        self.bar_cap.setFont(QFont(FONT,10,QFont.Weight.Bold));bc.addWidget(self.bar_cap)
        cr.addLayout(bc,1)
        lc=QVBoxLayout();lc.setSpacing(4)
        self.line_chart=AnimatedLineChart();lc.addWidget(self.line_chart,1)
        self.line_cap=QLabel("Appointment Distribution");self.line_cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.line_cap.setStyleSheet(f"color:{PRIMARY};background:transparent;border:none;")
        self.line_cap.setFont(QFont(FONT,10,QFont.Weight.Bold));lc.addWidget(self.line_cap)
        cr.addLayout(lc,1);lay.addLayout(cr)
        self.combo.currentIndexChanged.connect(self._update_charts)
        QTimer.singleShot(0,lambda:self._update_charts(0))

    @staticmethod
    def _hourly_labels(n):
        return [f"{(8+i)%12 or 12}{'am' if (8+i)<12 else 'pm'}" for i in range(n)]
    @staticmethod
    def _weekday_labels():
        return ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    @staticmethod
    def _monthly_labels():
        return ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    def _update_charts(self, idx):
        try: _,days=self.PERIODS[idx]
        except: days=1
        revenues,rev_labels,volumes,vol_labels=[],[],[],[]
        try:
            if self.db and self.db.is_connected():
                if days==30:
                    rev_labels=self._weekday_labels();vol_labels=self._weekday_labels()
                    rd=self.db.get_revenue_weekday_trends()
                    if isinstance(rd,tuple) and len(rd)==2: revenues,_=rd
                    vd=self.db.get_appointment_weekday_volume()
                    if isinstance(vd,tuple) and len(vd)==2: volumes,_=vd
                else:
                    rd=self.db.get_revenue_trends(days)
                    if isinstance(rd,tuple) and len(rd)==2: revenues,_=rd
                    vr=self.db.get_appointment_volume(days) or []
                    volumes=[int(v) if not isinstance(v,list) else (int(v[0]) if v else 0) for v in vr]
                    if days==1:
                        rev_labels=self._hourly_labels(len(revenues))
                        vol_labels=self._hourly_labels(len(volumes))
                    else:
                        rev_labels=self._monthly_labels()[:len(revenues)]
                        vol_labels=self._monthly_labels()[:len(volumes)]
        except Exception as e: print(f"[ChartCard] DB error: {e}")
        if not revenues:
            rev_labels=self._weekday_labels() if days==30 else (self._hourly_labels(10) if days==1 else self._monthly_labels())
            revenues=[0]*len(rev_labels)
        if not volumes:
            vol_labels=self._weekday_labels() if days==30 else (self._hourly_labels(10) if days==1 else self._monthly_labels())
            volumes=[0]*len(vol_labels)
        rc,vc=("Hourly Revenue","Hourly Appointments") if days==1 else \
              ("Weekly Revenue","Weekly Appointments") if days<=31 else \
              ("Monthly Revenue","Monthly Appointments")
        self.bar_cap.setText(rc);self.line_cap.setText(vc)
        self.bar_chart.set_data(revenues,rev_labels,color=QColor(PRIMARY_CONTAINER))
        self.line_chart.set_data(volumes,vol_labels,color=QColor(PRIMARY))


# ═════════════════════════════════════════════════════════════════════════
# UPCOMING APPOINTMENTS CARD
# ═════════════════════════════════════════════════════════════════════════
def _avatar_color_for(name):
    palette=[(SECONDARY_FIXED,PRIMARY),(TERTIARY_FIXED,TERTIARY_CONTAINER),
             (PRIMARY_FIXED,PRIMARY),(SIDEBAR_ACTIVE_BG,PRIMARY)]
    h=sum(ord(c) for c in (name or ""))%len(palette);return palette[h]

class UpcomingAppointmentsCard(QFrame):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"UpcomingAppointmentsCard{{background:{CARD};border-radius:16px;border:1px solid {OUTLINE};}}")
        add_shadow(self,blur=14,offset_y=4,alpha=10)
        lay=QVBoxLayout(self);lay.setContentsMargins(0,0,0,0);lay.setSpacing(0)
        header=QHBoxLayout();header.setContentsMargins(24,20,24,16)
        t=QLabel("Upcoming Appointments")
        t.setStyleSheet(f"color:{PRIMARY};background:transparent;border:none;")
        t.setFont(QFont(FONT,14,QFont.Weight.Bold));header.addWidget(t);header.addStretch()
        lay.addLayout(header)
        sep=QFrame();sep.setFixedHeight(1);sep.setStyleSheet(f"background:{OUTLINE};");lay.addWidget(sep)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMinimumHeight(180);scroll.setMaximumHeight(340)
        scroll.setStyleSheet(
            "QScrollArea{background:transparent;border:none;}"
            f"QScrollBar:vertical{{background:transparent;width:6px;}}"
            f"QScrollBar::handle:vertical{{background:{OUTLINE};border-radius:3px;min-height:28px;}}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        sc=QWidget();sc.setStyleSheet("background:transparent;")
        sl=QVBoxLayout(sc);sl.setContentsMargins(16,12,16,12);sl.setSpacing(0)
        if not items:
            e=QLabel("No upcoming appointments");e.setAlignment(Qt.AlignmentFlag.AlignCenter)
            e.setStyleSheet(f"color:{MUTED};padding:40px;background:transparent;border:none;")
            e.setFont(QFont(FONT,12));sl.addWidget(e)
        else:
            for idx,ap in enumerate(items):
                sl.addWidget(self._make_row(ap,alt=(idx%2==1)))
        sl.addStretch();scroll.setWidget(sc);lay.addWidget(scroll,1)

    def _make_row(self, ap, alt=False):
        rw=QFrame();bg="#F6F8FD" if alt else CARD
        rw.setStyleSheet(f"QFrame{{background:{bg};border:none;border-radius:8px;padding:4px;}}")
        h=QHBoxLayout(rw);h.setContentsMargins(12,10,12,10);h.setSpacing(12)
        pn=ap.get("patient_name","Unknown");bgc,fgc=_avatar_color_for(pn)
        av=QLabel();av.setFixedSize(40,40);av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ini="".join(w[0].upper() for w in pn.split()[:2]) if pn else "?"
        av.setText(ini);av.setFont(QFont(FONT,12,QFont.Weight.Bold))
        av.setStyleSheet(f"background:{bgc};color:{fgc};border-radius:20px;");h.addWidget(av)
        col=QVBoxLayout();col.setSpacing(1)
        n=QLabel(pn);n.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        n.setFont(QFont(FONT,11,QFont.Weight.Bold));col.addWidget(n)
        ad=ap.get("appointment_date","")
        ts=ad.strftime("%I:%M %p - %b %d") if isinstance(ad,datetime) else str(ad)
        tl=QLabel(ts);tl.setStyleSheet(f"color:{MUTED};background:transparent;border:none;")
        tl.setFont(QFont(FONT,9));col.addWidget(tl);h.addLayout(col,1)
        tr=ap.get("treatment_name","") or ap.get("treatment","")
        if tr:
            ch=QLabel(tr);ch.setStyleSheet(f"background:{PRIMARY_FIXED};color:{PRIMARY};border-radius:10px;padding:4px 12px;border:none;font-weight:600;")
            ch.setFont(QFont(FONT,9));ch.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Maximum)
            h.addWidget(ch)
        st=ap.get("status","")
        sc_map={"scheduled":(PRIMARY_FIXED,PRIMARY),"completed":("#CCE8DA",SUCCESS),
                "walk-in":("#FFE7B0",WARNING),"cancelled":(ERROR_CONTAINER,DANGER)}
        sbg,sfg=sc_map.get(st,(SURFACE_VARIANT,MUTED))
        sch=QLabel(st.title() if st else "--");sch.setStyleSheet(f"background:{sbg};color:{sfg};border-radius:10px;padding:4px 10px;border:none;font-weight:600;")
        sch.setFont(QFont(FONT,9));sch.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Maximum)
        h.addWidget(sch);return rw


# ═════════════════════════════════════════════════════════════════════════
# RECENT ACTIVITY CARD
# ═════════════════════════════════════════════════════════════════════════
class RecentActivityCard(QFrame):
    def __init__(self, db, parent=None):
        super().__init__(parent);self.db=db
        self.setStyleSheet(f"RecentActivityCard{{background:{CARD};border-radius:16px;border:1px solid {OUTLINE};}}")
        add_shadow(self,blur=14,offset_y=4,alpha=10)
        lay=QVBoxLayout(self);lay.setContentsMargins(0,0,0,0);lay.setSpacing(0)
        header=QHBoxLayout();header.setContentsMargins(24,20,24,16)
        t=QLabel("Recent Activity")
        t.setStyleSheet(f"color:{PRIMARY};background:transparent;border:none;")
        t.setFont(QFont(FONT,14,QFont.Weight.Bold));header.addWidget(t);header.addStretch()
        lay.addLayout(header)
        sep=QFrame();sep.setFixedHeight(1);sep.setStyleSheet(f"background:{OUTLINE};");lay.addWidget(sep)
        self.scroll=QScrollArea();self.scroll.setWidgetResizable(True);self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setMinimumHeight(180);self.scroll.setMaximumHeight(340)
        self.scroll.setStyleSheet(
            "QScrollArea{background:transparent;border:none;}"
            f"QScrollBar:vertical{{background:transparent;width:6px;}}"
            f"QScrollBar::handle:vertical{{background:{OUTLINE};border-radius:3px;min-height:28px;}}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        self._content=QWidget();self._content.setStyleSheet("background:transparent;")
        self._cl=QVBoxLayout(self._content);self._cl.setContentsMargins(16,12,16,12)
        self._cl.setSpacing(0);self._cl.addStretch()
        self.scroll.setWidget(self._content);lay.addWidget(self.scroll,1)
        QTimer.singleShot(100,self.refresh)

    def refresh(self):
        # Guard against deleted widgets
        try:
            _ = self._content.isVisible()
        except RuntimeError:
            return
        while self._cl.count():
            it=self._cl.takeAt(0)
            if it and it.widget():
                try: it.widget().deleteLater()
                except RuntimeError: pass
        acts=self._load()
        if not acts:
            e=QLabel("No recent activity");e.setAlignment(Qt.AlignmentFlag.AlignCenter)
            e.setFont(QFont(FONT,12));e.setStyleSheet(f"color:{MUTED};padding:40px;background:transparent;border:none;")
            self._cl.addWidget(e)
        else:
            for i,a in enumerate(acts): self._cl.addWidget(self._row(a,alt=(i%2==1)))
        self._cl.addStretch()

    def _load(self):
        items=[]
        try:
            a=self.db.get_recent_activities(limit=8) if self.db else []
            items.extend(a or [])
        except: pass
        try:
            b=self.db.execute_query(
                "SELECT b.bill_id,b.amount,b.status,b.payment_date,p.patient_name "
                "FROM billing b JOIN appointments a ON b.appointment_id=a.appointment_id "
                "JOIN patient p ON a.patient_id=p.patient_id "
                "ORDER BY COALESCE(b.payment_date,NOW()) DESC LIMIT 5") if self.db else []
            for x in (b or []):
                act=f"Bill ${float(x.get('amount',0)):,.0f} - {x.get('status','')}"
                if x.get('patient_name'): act+=f" ({x['patient_name']})"
                items.append({"action":act,"time":str(x.get("payment_date",""))[:16] or "--","user":"Billing"})
        except: pass
        try:
            lo=self.db.get_low_stock_items() if self.db else []
            for x in (lo or [])[:3]:
                items.append({"action":f"Low stock: {x.get('item_name','Item')} ({x.get('quantity',0)} left)","time":"Alert","user":"Inventory"})
        except: pass
        try:
            np=self.db.execute_query(
                "SELECT patient_name,registration_date FROM patient ORDER BY registration_date DESC LIMIT 3") if self.db else []
            for x in (np or []):
                items.append({"action":f"New patient: {x.get('patient_name','')}","time":str(x.get("registration_date",""))[:16] or "--","user":"Reception"})
        except: pass
        items.sort(key=lambda x:str(x.get("time","")),reverse=True)
        return items[:10]

    def _row(self, act, alt=False):
        rw=QFrame();bg="#F6F8FD" if alt else CARD
        rw.setStyleSheet(f"QFrame{{background:{bg};border:none;border-radius:8px;}}")
        h=QHBoxLayout(rw);h.setContentsMargins(12,10,12,10);h.setSpacing(12)
        al=act.get("action","").lower()
        if "low stock" in al or "inventory" in al: iid,ibg,ifg=IconWidget.ALERT,ERROR_CONTAINER,DANGER
        elif "bill" in al or "payment" in al or "paid" in al: iid,ibg,ifg=IconWidget.DOLLAR,PRIMARY_FIXED,PRIMARY
        elif "patient" in al or "new" in al: iid,ibg,ifg=IconWidget.USER_PLUS,"#CCE8DA",SUCCESS
        elif "cancel" in al: iid,ibg,ifg=IconWidget.CANCEL,ERROR_CONTAINER,DANGER
        elif "complet" in al: iid,ibg,ifg=IconWidget.CHECK,"#CCE8DA",SUCCESS
        else: iid,ibg,ifg=IconWidget.CALENDAR,SECONDARY_FIXED,SECONDARY
        ifr=QFrame();ifr.setFixedSize(34,34);ifr.setStyleSheet(f"background:{ibg};border-radius:17px;")
        il=QVBoxLayout(ifr);il.setContentsMargins(0,0,0,0);il.setAlignment(Qt.AlignmentFlag.AlignCenter)
        il.addWidget(IconWidget(iid,16,QColor(ifg),filled=True));h.addWidget(ifr)
        col=QVBoxLayout();col.setSpacing(1)
        a=QLabel(act.get("action",""));a.setWordWrap(True)
        a.setStyleSheet(f"color:{TEXT};background:transparent;border:none;");a.setFont(QFont(FONT,10));col.addWidget(a)
        m=QLabel(act.get("user","")+"  -  "+str(act.get("time","")))
        m.setStyleSheet(f"color:{MUTED};background:transparent;border:none;");m.setFont(QFont(FONT,8));col.addWidget(m)
        h.addLayout(col,1);return rw


# ═════════════════════════════════════════════════════════════════════════
# TOGGLE SWITCH
# ═════════════════════════════════════════════════════════════════════════
class ToggleSwitch(QCheckBox):
    def __init__(self, parent=None, checked=False):
        super().__init__(parent)
        self.setChecked(checked);self.setFixedSize(44,24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        track_rect=QRectF(0,0,44,24)
        if self.isChecked(): p.setBrush(QBrush(QColor(PRIMARY)))
        else: p.setBrush(QBrush(QColor(OUTLINE)))
        p.setPen(Qt.PenStyle.NoPen);p.drawRoundedRect(track_rect,12,12)
        kx=22 if self.isChecked() else 2
        p.setBrush(QBrush(QColor(CARD)));p.drawEllipse(QRectF(kx,2,20,20))
        p.end()


# ═════════════════════════════════════════════════════════════════════════
# DASHBOARD PAGE - safe refresh, never deletes top-level layout widgets
# ═════════════════════════════════════════════════════════════════════════
class DashboardPage(QWidget):
    def __init__(self, db, user_data: UserData, parent=None):
        super().__init__(parent)
        self.db=db;self.user_data=user_data
        self.setStyleSheet(f"background:{BG};")
        self._build();QTimer.singleShot(100,self.refresh_stats)

    def _build(self):
        outer=QVBoxLayout(self);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea{{background:{BG};border:none;}}"
            f"QScrollBar:vertical{{background:transparent;width:8px;}}"
            f"QScrollBar::handle:vertical{{background:{OUTLINE};border-radius:4px;min-height:30px;}}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        host=QWidget();host.setStyleSheet(f"background:{BG};")
        lay=QVBoxLayout(host);lay.setContentsMargins(28,24,28,28);lay.setSpacing(20)

        # Stat cards
        sr=QHBoxLayout();sr.setSpacing(16)
        self.card_today=StatCard("Today's Appointments","--",IconWidget.CALENDAR,PRIMARY_FIXED,PRIMARY)
        self.card_patients=StatCard("Total Patients","--",IconWidget.GROUPS,SECONDARY_FIXED,SECONDARY)
        self.card_pending=StatCard("Pending Bills","--",IconWidget.DOLLAR,TERTIARY_FIXED,TERTIARY_CONTAINER)
        self.card_stock=StatCard("Low Stock Alerts","--",IconWidget.ALERT,ERROR_CONTAINER,DANGER)
        for c in (self.card_today,self.card_patients,self.card_pending,self.card_stock):
            sr.addWidget(c,1)
        lay.addLayout(sr)

        # Chart
        self.chart_card=ChartCard(self.db);lay.addWidget(self.chart_card)

        # Patient stats + Appointment split
        mr=QHBoxLayout();mr.setSpacing(20)
        self.psc=PatientStatsCard(0);mr.addWidget(self.psc,3)
        segs=self._load_split()
        self.split_card=AppointmentSplitCard(segs);mr.addWidget(self.split_card,3)
        lay.addLayout(mr)

        # Upcoming + Recent
        br=QHBoxLayout();br.setSpacing(20)
        self.upcoming=UpcomingAppointmentsCard(self._load_upcoming());br.addWidget(self.upcoming,1)
        self.recent=RecentActivityCard(self.db);br.addWidget(self.recent,1)
        lay.addLayout(br);lay.addStretch()
        scroll.setWidget(host);outer.addWidget(scroll)

    def refresh_stats(self):
        """Safe refresh - updates widgets IN PLACE, never deletes them."""
        # Guard: if this page's widgets have been destroyed, bail out
        try:
            _ = self.card_today.isVisible()
        except RuntimeError:
            return

        if not self.db or not self.db.is_connected(): return
        try:
            st=self.db.get_dashboard_stats()
            self.card_today.set_value(str(st.get("today_appointments",0)))
            self.card_patients.set_value(str(st.get("total_patients",0)))
            pa=st.get("pending_amount",0)
            pb=st.get("pending_bills",0)
            self.card_pending.set_value(f"${pa:,.0f}" if pa else str(pb))
            self.card_stock.set_value(str(st.get("low_stock",0)))

            # KEY FIX: update PatientStatsCard IN PLACE instead of delete/recreate
            self.psc.update_pct(st.get("patient_growth",0))

            # KEY FIX: update AppointmentSplitCard IN PLACE
            segs=self._load_split()
            self.split_card.update_segments(segs)
        except RuntimeError:
            pass  # Widget already deleted
        except Exception as e:
            print(f"[DashboardPage] refresh error: {e}")

    def _load_split(self):
        segs=[]
        try:
            data=self.db.get_treatment_type_split() if self.db else []
            for j,item in enumerate(data or []):
                name=item.get("treatment_name","Other")
                pct=item.get("pct",0);color=SPLIT_PALETTE[j%len(SPLIT_PALETTE)]
                segs.append((name,pct,color))
        except: pass
        return segs

    def _load_upcoming(self):
        try:
            if self.db: return self.db.get_upcoming_appointments(limit=8) or []
        except: pass
        return []


# ═════════════════════════════════════════════════════════════════════════
# PROFILE PAGE - safe save
# ═════════════════════════════════════════════════════════════════════════
class ProfilePage(QWidget):
    def __init__(self, db, user_data: UserData, parent=None):
        super().__init__(parent)
        self.db=db;self.user_data=user_data
        self.setStyleSheet(f"background:{BG};")
        self._build()

    def _build(self):
        outer=QVBoxLayout(self);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea{{background:{BG};border:none;}}"
            f"QScrollBar:vertical{{background:transparent;width:8px;}}"
            f"QScrollBar::handle:vertical{{background:{OUTLINE};border-radius:4px;min-height:30px;}}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        host=QWidget();host.setStyleSheet(f"background:{BG};")
        lay=QVBoxLayout(host);lay.setContentsMargins(40,32,40,32);lay.setSpacing(20)

        hl=QVBoxLayout();hl.setSpacing(4)
        t=QLabel("Profile Settings");t.setFont(QFont(FONT,22,QFont.Weight.Bold))
        t.setStyleSheet(f"color:{PRIMARY};background:transparent;border:none;");hl.addWidget(t)
        s=QLabel("Manage your professional information, security, and clinic preferences.")
        s.setWordWrap(True);s.setStyleSheet(f"color:{MUTED};background:transparent;border:none;")
        s.setFont(QFont(FONT,11));hl.addWidget(s);lay.addLayout(hl)

        # Personal Information
        pi_card=QFrame()
        pi_card.setStyleSheet(f"background:{CARD};border-radius:16px;border:1px solid {OUTLINE};")
        add_shadow(pi_card,blur=16,offset_y=4,alpha=12)
        pi_lay=QVBoxLayout(pi_card);pi_lay.setContentsMargins(28,24,28,24);pi_lay.setSpacing(18)
        pi_hdr=QHBoxLayout()
        pi_hdr.addWidget(IconWidget(IconWidget.PROFILE,20,QColor(PRIMARY),filled=True))
        pi_t=QLabel("Personal Information");pi_t.setFont(QFont(FONT,14,QFont.Weight.Bold))
        pi_t.setStyleSheet(f"color:{PRIMARY};background:transparent;border:none;")
        pi_hdr.addWidget(pi_t);pi_hdr.addStretch();pi_lay.addLayout(pi_hdr)

        av_row=QHBoxLayout();av_row.setSpacing(16)
        self._avatar=QLabel();self._avatar.setFixedSize(72,72)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter);self._apply_avatar()
        av_row.addWidget(self._avatar)
        av_col=QVBoxLayout();av_col.setSpacing(6)
        self._profile_name=QLabel(self.user_data.staff_full_name or self.user_data.user_name or "N/A")
        self._profile_name.setFont(QFont(FONT,16,QFont.Weight.Bold))
        self._profile_name.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        av_col.addWidget(self._profile_name)
        self._profile_role=QLabel(self.user_data.display_role)
        self._profile_role.setStyleSheet(f"color:{MUTED};background:transparent;border:none;")
        self._profile_role.setFont(QFont(FONT,11));av_col.addWidget(self._profile_role)
        photo_btn=QPushButton("Change Photo");photo_btn.setFixedHeight(32)
        photo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        photo_btn.setStyleSheet(
            f"QPushButton{{background:{SURFACE_HIGH};color:{PRIMARY};border:1px solid {OUTLINE};"
            f"border-radius:8px;padding:0 14px;font-weight:600;font-size:11px;}}"
            f"QPushButton:hover{{background:{SIDEBAR_ACTIVE_BG};}}")
        photo_btn.clicked.connect(self._change_photo);av_col.addWidget(photo_btn)
        av_row.addLayout(av_col,1);pi_lay.addLayout(av_row)
        sep1=QFrame();sep1.setFixedHeight(1);sep1.setStyleSheet(f"background:{OUTLINE};");pi_lay.addWidget(sep1)

        form_grid=QGridLayout();form_grid.setHorizontalSpacing(16);form_grid.setVerticalSpacing(14)
        self._fields={}
        field_defs=[
            ("Full Name","staff_name",self.user_data.staff_full_name or ""),
            ("Username","username",self.user_data.user_name or ""),
            ("Email Address","email",self.user_data.email or ""),
            ("Phone Number","phone",self.user_data.phone or ""),
            ("Role / Job Title","role",self.user_data.user_role or ""),
        ]
        input_ss=(f"QLineEdit{{border:1px solid {OUTLINE};border-radius:8px;padding:0 12px;"
                  f"font-size:13px;color:{TEXT};background:{CARD};}}QLineEdit:focus{{border:2px solid {PRIMARY};}}")
        readonly_ss=(f"QLineEdit{{border:1px solid {OUTLINE};border-radius:8px;padding:0 12px;"
                     f"font-size:13px;color:{MUTED};background:{SURFACE_HIGH};}}")
        for row,(label,key,default) in enumerate(field_defs):
            l=QLabel(label);l.setFont(QFont(FONT,10,QFont.Weight.Bold))
            l.setStyleSheet(f"color:{MUTED};background:transparent;border:none;")
            form_grid.addWidget(l,row,0)
            edit=QLineEdit(default);edit.setFixedHeight(38)
            if key in ("username","role"):
                edit.setReadOnly(True);edit.setStyleSheet(readonly_ss)
            else:
                edit.setStyleSheet(input_ss)
            self._fields[key]=edit;form_grid.addWidget(edit,row,1)
        pi_lay.addLayout(form_grid);lay.addWidget(pi_card)

        # Display Settings
        ds_card=QFrame()
        ds_card.setStyleSheet(f"background:{CARD};border-radius:16px;border:1px solid {OUTLINE};")
        add_shadow(ds_card,blur=16,offset_y=4,alpha=12)
        ds_lay=QVBoxLayout(ds_card);ds_lay.setContentsMargins(28,24,28,24);ds_lay.setSpacing(16)
        ds_hdr=QHBoxLayout()
        ds_hdr.addWidget(IconWidget(IconWidget.PALETTE,20,QColor(PRIMARY),filled=True))
        ds_t=QLabel("Display Settings");ds_t.setFont(QFont(FONT,14,QFont.Weight.Bold))
        ds_t.setStyleSheet(f"color:{PRIMARY};background:transparent;border:none;")
        ds_hdr.addWidget(ds_t);ds_hdr.addStretch();ds_lay.addLayout(ds_hdr)
        combo_ss=(f"QComboBox{{border:1px solid {OUTLINE};border-radius:8px;padding:0 12px;"
                  f"color:{TEXT};font-size:12px;background:{CARD};}}QComboBox::drop-down{{border:none;width:22px;}}"
                  f"QComboBox QAbstractItemView{{background:{CARD};border:1px solid {OUTLINE};padding:4px;}}")
        lang_row=QHBoxLayout();lang_row.setSpacing(12)
        lang_l=QLabel("Language");lang_l.setFont(QFont(FONT,11))
        lang_l.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        lang_row.addWidget(lang_l);lang_row.addStretch()
        self._lang_combo=QComboBox();self._lang_combo.setFixedHeight(34);self._lang_combo.setMinimumWidth(180)
        self._lang_combo.addItems(["English (United States)","Filipino","Spanish","French"])
        self._lang_combo.setStyleSheet(combo_ss);lang_row.addWidget(self._lang_combo)
        ds_lay.addLayout(lang_row)
        theme_row=QHBoxLayout();theme_row.setSpacing(12)
        theme_l=QLabel("Theme");theme_l.setFont(QFont(FONT,11))
        theme_l.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        theme_row.addWidget(theme_l);theme_row.addStretch()
        self._theme_combo=QComboBox();self._theme_combo.setFixedHeight(34);self._theme_combo.setMinimumWidth(180)
        self._theme_combo.addItems(["Light","Dark"]);self._theme_combo.setStyleSheet(combo_ss)
        self._theme_combo.setCurrentIndex(0);theme_row.addWidget(self._theme_combo)
        ds_lay.addLayout(theme_row);lay.addWidget(ds_card)

        # Security & Password
        sp_card=QFrame()
        sp_card.setStyleSheet(f"background:{CARD};border-radius:16px;border:1px solid {OUTLINE};")
        add_shadow(sp_card,blur=16,offset_y=4,alpha=12)
        sp_lay=QVBoxLayout(sp_card);sp_lay.setContentsMargins(28,24,28,24);sp_lay.setSpacing(16)
        sp_hdr=QHBoxLayout()
        sp_hdr.addWidget(IconWidget(IconWidget.LOCK,20,QColor(PRIMARY),filled=True))
        sp_t=QLabel("Security & Password");sp_t.setFont(QFont(FONT,14,QFont.Weight.Bold))
        sp_t.setStyleSheet(f"color:{PRIMARY};background:transparent;border:none;")
        sp_hdr.addWidget(sp_t);sp_hdr.addStretch();sp_lay.addLayout(sp_hdr)
        pw_fields=QGridLayout();pw_fields.setHorizontalSpacing(16);pw_fields.setVerticalSpacing(12)
        pw_ss=(f"QLineEdit{{border:1px solid {OUTLINE};border-radius:8px;padding:0 12px;"
               f"font-size:13px;color:{TEXT};background:{CARD};}}QLineEdit:focus{{border:2px solid {PRIMARY};}}")
        self._old_pw=QLineEdit();self._old_pw.setPlaceholderText("Current password")
        self._old_pw.setEchoMode(QLineEdit.EchoMode.Password);self._old_pw.setFixedHeight(38)
        self._old_pw.setStyleSheet(pw_ss)
        self._new_pw=QLineEdit();self._new_pw.setPlaceholderText("New password")
        self._new_pw.setEchoMode(QLineEdit.EchoMode.Password);self._new_pw.setFixedHeight(38)
        self._new_pw.setStyleSheet(pw_ss)
        self._conf_pw=QLineEdit();self._conf_pw.setPlaceholderText("Confirm new password")
        self._conf_pw.setEchoMode(QLineEdit.EchoMode.Password);self._conf_pw.setFixedHeight(38)
        self._conf_pw.setStyleSheet(pw_ss)
        lbl_ss=f"color:{MUTED};background:transparent;border:none;font-weight:600;font-size:11px;"
        ol=QLabel("Current Password");ol.setStyleSheet(lbl_ss)
        nl=QLabel("New Password");nl.setStyleSheet(lbl_ss)
        cl=QLabel("Confirm Password");cl.setStyleSheet(lbl_ss)
        pw_fields.addWidget(ol,0,0);pw_fields.addWidget(self._old_pw,0,1)
        pw_fields.addWidget(nl,1,0);pw_fields.addWidget(self._new_pw,1,1)
        pw_fields.addWidget(cl,2,0);pw_fields.addWidget(self._conf_pw,2,1)
        sp_lay.addLayout(pw_fields)
        self._pw_msg=QLabel("");self._pw_msg.setFont(QFont(FONT,10))
        self._pw_msg.setStyleSheet("background:transparent;border:none;");sp_lay.addWidget(self._pw_msg)
        lay.addWidget(sp_card)

        # Notification Preferences
        np_card=QFrame()
        np_card.setStyleSheet(f"background:{CARD};border-radius:16px;border:1px solid {OUTLINE};")
        add_shadow(np_card,blur=16,offset_y=4,alpha=12)
        np_lay=QVBoxLayout(np_card);np_lay.setContentsMargins(28,24,28,24);np_lay.setSpacing(14)
        np_hdr=QHBoxLayout()
        np_hdr.addWidget(IconWidget(IconWidget.NOTIFICATION,20,QColor(PRIMARY),filled=True))
        np_t=QLabel("Notification Preferences");np_t.setFont(QFont(FONT,14,QFont.Weight.Bold))
        np_t.setStyleSheet(f"color:{PRIMARY};background:transparent;border:none;")
        np_hdr.addWidget(np_t);np_hdr.addStretch();np_lay.addLayout(np_hdr)
        notif_items=[("New Appointments",True),("Appointment Reminders",True),
                     ("Patient Messages",True),("Billing Alerts",True),("Inventory Alerts",False)]
        self._notif_toggles={}
        for label,checked in notif_items:
            row=QHBoxLayout();row.setSpacing(12)
            l=QLabel(label);l.setFont(QFont(FONT,11))
            l.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
            row.addWidget(l);row.addStretch()
            ts=ToggleSwitch(checked=checked);row.addWidget(ts)
            self._notif_toggles[label]=ts;np_lay.addLayout(row)
        lay.addWidget(np_card)

        # Save button
        save_btn=QPushButton("Save Profile Settings");save_btn.setFixedHeight(48)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(
            f"QPushButton{{background:{PRIMARY};color:white;border:none;border-radius:10px;"
            f"font-weight:700;font-size:14px;}}QPushButton:hover{{background:{PRIMARY_DARK};}}")
        save_btn.clicked.connect(self._save_profile);lay.addWidget(save_btn)
        lay.addStretch()
        scroll.setWidget(host);outer.addWidget(scroll)

    def _apply_avatar(self):
        pm=load_profile_pixmap(self.user_data.profile_image,72)
        if pm:
            self._avatar.setPixmap(pm)
            self._avatar.setStyleSheet(f"border:2px solid {OUTLINE};border-radius:36px;")
        else:
            self._avatar.setText(self.user_data.initial)
            self._avatar.setFont(QFont(FONT,24,QFont.Weight.Bold))
            self._avatar.setStyleSheet(f"background:{PRIMARY};color:white;border-radius:36px;")

    def _change_photo(self):
        path,_=QFileDialog.getOpenFileName(self,"Select Profile Photo","",
                                           "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path and self.db and self.user_data.user_id:
            try:
                self.db.update_profile_image(self.user_data.user_id,path)
                self.user_data.profile_image=path;self._apply_avatar()
            except Exception as e: print(f"[ProfilePage] photo error: {e}")

    def _save_profile(self):
        if not self.db or not self.user_data.user_id: return
        staff_name=self._fields["staff_name"].text().strip()
        email=self._fields["email"].text().strip()
        phone=self._fields["phone"].text().strip()
        ok=self.db.update_staff_profile(self.user_data.user_id,staff_name,email,phone)
        if ok:
            self.user_data.staff_full_name=staff_name
            self.user_data.email=email;self.user_data.phone=phone
        old=self._old_pw.text();new=self._new_pw.text();conf=self._conf_pw.text()
        if old or new or conf:
            if not old or not new or not conf:
                self._pw_msg.setText("All password fields are required.")
                self._pw_msg.setStyleSheet(f"color:{DANGER};background:transparent;border:none;");return
            if new!=conf:
                self._pw_msg.setText("New passwords do not match.")
                self._pw_msg.setStyleSheet(f"color:{DANGER};background:transparent;border:none;");return
            if len(new)<8:
                self._pw_msg.setText("Password must be at least 8 characters.")
                self._pw_msg.setStyleSheet(f"color:{DANGER};background:transparent;border:none;");return
            try:
                pw_ok=self.db.update_user_password_secure(self.user_data.user_id,old,new)
                if pw_ok:
                    self._old_pw.clear();self._new_pw.clear();self._conf_pw.clear()
                    self._pw_msg.setText("Password updated.")
                    self._pw_msg.setStyleSheet(f"color:{SUCCESS};background:transparent;border:none;")
                else:
                    self._pw_msg.setText("Current password is incorrect.")
                    self._pw_msg.setStyleSheet(f"color:{DANGER};background:transparent;border:none;");return
            except Exception as e:
                self._pw_msg.setText(f"Error: {e}")
                self._pw_msg.setStyleSheet(f"color:{DANGER};background:transparent;border:none;");return
        self.user_data.reload()
        self.refresh_profile_page()
        # Tell the main window to refresh its topbar
        main_window = self.window()
        if hasattr(main_window, 'refresh_top_profile'):
            main_window.refresh_top_profile()
        # Show success popup
        msg=QMessageBox(self);msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Profile Saved");msg.setText("Your profile settings have been saved successfully.")
        msg.setStyleSheet(
            f"QMessageBox{{background:{CARD};}}QLabel{{color:{TEXT};font-size:13px;}}"
            f"QPushButton{{background:{PRIMARY};color:white;border:none;border-radius:6px;padding:6px 20px;font-weight:600;}}")
        msg.exec()

    def refresh_profile_page(self):
        """Safe refresh of profile page fields from user_data."""
        try:
            self._fields["staff_name"].setText(self.user_data.staff_full_name or "")
            self._fields["email"].setText(self.user_data.email or "")
            self._fields["phone"].setText(self.user_data.phone or "")
            self._fields["role"].setText(self.user_data.user_role or "")
            self._profile_name.setText(self.user_data.staff_full_name or self.user_data.user_name or "N/A")
            self._profile_role.setText(self.user_data.display_role)
            self._apply_avatar()
        except RuntimeError:
            pass  # Widget already deleted


# ═════════════════════════════════════════════════════════════════════════
# MAIN DASHBOARD WINDOW
# KEY FIX: pages created once, switched with setCurrentWidget / setCurrentIndex.
# Safe refresh methods with RuntimeError guards. Never destroys pages.
# ═════════════════════════════════════════════════════════════════════════
class DashboardGUI(QMainWindow):
    def __init__(self, db, current_user: dict):
        super().__init__()
        self.db = db
        self.user_data = UserData(db, current_user)
        self.setWindowTitle(f"{getattr(Config,'APP_NAME','LC Dental Care')} - Dashboard")
        self.setMinimumSize(1280, 800)
        self.showMaximized()

        central=QWidget();self.setCentralWidget(central)
        main_lay=QHBoxLayout(central);main_lay.setContentsMargins(0,0,0,0);main_lay.setSpacing(0)

        # Sidebar - persistent
        self.sidebar=Sidebar(on_nav=self._on_nav,on_logout=self._logout)
        main_lay.addWidget(self.sidebar)

        # Right column - persistent
        right=QWidget();right.setStyleSheet(f"background:{BG};")
        right_lay=QVBoxLayout(right);right_lay.setContentsMargins(0,0,0,0);right_lay.setSpacing(0)

        # TopBar - persistent
        self.topbar=TopBar(self.user_data)
        right_lay.addWidget(self.topbar)

        # Stacked widget - all pages added once, never removed
        self.stack=QStackedWidget()
        right_lay.addWidget(self.stack,1)

        # ── Create all pages ONCE ──
        # Page 0: Dashboard
        self.dashboard_page=DashboardPage(db,self.user_data)
        self.stack.addWidget(self.dashboard_page)

        # Page 1: Patients (real page)
        try:
            from dashboard_gui.patients_page import PatientsPage
            self.patients_page=PatientsPage(db)
        except ImportError:
            self.patients_page=None
        self.stack.addWidget(self.patients_page if self.patients_page else QWidget())

        # Pages 2-8: Placeholders
        self._placeholder_idx={}
        for label in ["Appointments","Services & Treatments",
                      "Billing & Payments","Inventory","Reports","Users","Settings"]:
            ph=QWidget();ph.setStyleSheet(f"background:{BG};")
            pl=QVBoxLayout(ph);pl.setContentsMargins(40,32,40,32)
            t=QLabel(label);t.setFont(QFont(FONT,24,QFont.Weight.Bold))
            t.setStyleSheet(f"color:{PRIMARY};background:transparent;border:none;")
            pl.addWidget(t);pl.addStretch()
            self._placeholder_idx[label]=self.stack.addWidget(ph)

        # Page 9: Profile
        self.profile_page=ProfilePage(db,self.user_data)
        self._profile_idx=self.stack.addWidget(self.profile_page)

        main_lay.addWidget(right,1)

        # Auto-refresh timer
        self._timer=QTimer(self)
        self._timer.timeout.connect(self._periodic_refresh)
        self._timer.start(60000)

    # ── SAFE NAVIGATION ─────────────────────────────────────────────
    def _on_nav(self, btn_id):
        """Switch pages using setCurrentWidget / setCurrentIndex.
        Never destroys or recreates any page."""
        try:
            if btn_id==0:  # Dashboard
                self.stack.setCurrentWidget(self.dashboard_page)
                self.refresh_dashboard_data()
            elif btn_id==1:  # Patients
                if self.patients_page:
                    try: self.patients_page.refresh()
                    except RuntimeError: pass
                    self.stack.setCurrentWidget(self.patients_page)
            elif btn_id==9:  # Profile
                self.refresh_profile_page()
                self.stack.setCurrentIndex(self._profile_idx)
                self.refresh_top_profile()
            elif 2<=btn_id<=8:
                labels={2:"Appointments",3:"Services & Treatments",
                        4:"Billing & Payments",5:"Inventory",
                        6:"Reports",7:"Users",8:"Settings"}
                label=labels.get(btn_id,"")
                if label in self._placeholder_idx:
                    self.stack.setCurrentIndex(self._placeholder_idx[label])
        except RuntimeError:
            pass  # A widget was deleted unexpectedly

    def _logout(self):
        self.close()
        from login_gui import LoginGUI
        self.login=LoginGUI(None,self.db);self.login.show()

    # ── SAFE REFRESH METHODS ────────────────────────────────────────
    def refresh_dashboard_data(self):
        """Refresh dashboard data only - never destroys widgets."""
        try:
            if self.dashboard_page and self.dashboard_page.isVisible():
                self.dashboard_page.refresh_stats()
        except RuntimeError:
            pass

    def refresh_profile_page(self):
        """Refresh profile page fields from DB."""
        try:
            self.user_data.reload()
            if self.profile_page:
                self.profile_page.refresh_profile_page()
        except RuntimeError:
            pass

    def refresh_top_profile(self):
        """Refresh topbar avatar and user info."""
        try:
            self.topbar._user_data = self.user_data
            self.topbar.refresh_avatar()
        except RuntimeError:
            pass

    def _periodic_refresh(self):
        """Auto-refresh dashboard every 60 seconds if visible."""
        try:
            if self.stack.currentWidget() is self.dashboard_page:
                self.refresh_dashboard_data()
                if self.dashboard_page.recent:
                    self.dashboard_page.recent.refresh()
                if self.dashboard_page.chart_card:
                    self.dashboard_page.chart_card._update_charts(
                        self.dashboard_page.chart_card.combo.currentIndex())
        except RuntimeError:
            pass