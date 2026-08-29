"""
╔══════════════════════════════════════════════════════════════╗
║          AI STYLE RECOMMENDER  –  Complete Python App        ║
║  OpenCV + MediaPipe  |  PyQt5 UI  |  Female Dataset          ║
╚══════════════════════════════════════════════════════════════╝

HOW TO RUN:
    pip install opencv-python mediapipe PyQt5 numpy Pillow
    python ai_style_recommender.py

DATASET ROOT:  Set DATASET_ROOT below to your actual path.
               Default assumes  dataset/female/  is next to this script.
"""

import sys, os, math, random, colorsys
from pathlib import Path

import cv2
import numpy as np
import mediapipe as mp

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea, QFrame,
    QFileDialog, QSizePolicy, QGraphicsDropShadowEffect, QProgressBar,
    QSpacerItem
)
from PyQt5.QtCore  import Qt, QThread, pyqtSignal, QSize, QRect, QPoint
from PyQt5.QtGui   import (
    QPixmap, QImage, QColor, QFont, QPainter, QPen, QBrush,
    QLinearGradient, QPainterPath, QFontMetrics
)

from engine_core import (
    DATASET_ROOT, UNDERTONE_INFO, FACE_TIPS, EYE_EYELINER,
    MAKEUP_TIPS, SKIN_TIPS, DatasetLoader, FaceEngine,
)

# ══════════════════════════════════════════════════════════════
#  COLOUR THEME
# ══════════════════════════════════════════════════════════════
BG       = "#0D0D14"
BG2      = "#13131E"
BG3      = "#1C1C2E"
CARD     = "#181826"
BORDER   = "#2E2E48"
ACCENT   = "#00D4FF"
ACCENT2  = "#7B61FF"
ACCENT3  = "#FF6B9D"
SUCCESS  = "#00FF9F"
WARN     = "#FFB347"
TEXT     = "#E8E8F4"
TEXTD    = "#6B6B8A"
TEXTM    = "#A0A0C0"

# ══════════════════════════════════════════════════════════════
#  WORKER THREAD
# ══════════════════════════════════════════════════════════════
class Worker(QThread):
    progress = pyqtSignal(int, str)
    done     = pyqtSignal(dict, dict)
    failed   = pyqtSignal(str)

    def __init__(self, path, engine, loader):
        super().__init__()
        self.path   = path
        self.engine = engine
        self.loader = loader

    def run(self):
        self.progress.emit(15,"Detecting face…")
        res = self.engine.analyse(self.path)
        if res.get("error"):
            self.failed.emit(res["error"]); return

        self.progress.emit(45,"Classifying face shape…")
        self.progress.emit(65,"Analysing skin undertone…")
        self.progress.emit(80,"Gathering recommendations…")

        fs = res["face_shape"]; es = res["eye_shape"]; ut = res["undertone"]

        # ── debug: print resolved paths to terminal ──
        print(f"\n{'─'*60}")
        print(f"  Face Shape : {fs}  |  Eye Shape : {es}  |  Undertone : {ut}")
        print(f"  Dataset root : {self.loader.root}")
        print(f"  Exists       : {self.loader.root.exists()}")
        print("  Path checks  :")
        self.loader.debug_paths(fs, ut, es)
        print(f"{'─'*60}\n")

        recs = dict(
            hairstyles   = self.loader.hairstyles(fs,3),
            hijaab       = self.loader.hijaab(fs,3),
            outfit_style = self.loader.outfit_styles(fs,ut,3),
            colours      = self.loader.colours(fs,ut,4),
            accessories  = self.loader.accessories(fs,2),
            eyeliner     = self.loader.eyeliner(es,1),
            face_shape_i = self.loader.face_shape_imgs(fs,1),
            eye_shape_i  = self.loader.eye_shape_imgs(es,1),
        )
        self.progress.emit(100,"Done!")
        self.done.emit(res, recs)



# ══════════════════════════════════════════════════════════════
#  UI HELPERS
# ══════════════════════════════════════════════════════════════
def cv2px(bgr):
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w, c = rgb.shape
    return QPixmap.fromImage(QImage(rgb.data, w, h, c * w, QImage.Format_RGB888))


def mk_label(text, size=11, bold=False, color=None, align=Qt.AlignLeft, wrap=False):
    l = QLabel(text)
    c = color or TEXT
    l.setStyleSheet(
        f"color:{c};font-size:{size}px;"
        f"font-weight:{'700' if bold else '400'};"
        f"background:transparent;letter-spacing:0.2px;")
    l.setAlignment(align)
    if wrap:
        l.setWordWrap(True)
    return l


def section_label(text, color=ACCENT):
    """Small all-caps colored category label like in the reference."""
    l = QLabel(text.upper())
    l.setStyleSheet(
        f"color:{color};font-size:8px;font-weight:800;"
        f"letter-spacing:2.5px;background:transparent;")
    return l


def divider():
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background:{BORDER};border:none;")
    return f


# ══════════════════════════════════════════════════════════════
#  ROUNDED IMAGE  –  custom painted, clipped to rounded rect
# ══════════════════════════════════════════════════════════════
class RoundImg(QLabel):
    def __init__(self, path=None, w=104, h=120, radius=8):
        super().__init__()
        self.setFixedSize(w, h)
        self._r = radius
        self.setStyleSheet("background:transparent;")
        self._pm = None
        if path and Path(str(path)).exists():
            self._pm = QPixmap(str(path)).scaled(
                w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        clip = QPainterPath()
        clip.addRoundedRect(0, 0, self.width(), self.height(), self._r, self._r)
        p.setClipPath(clip)
        if self._pm:
            sw, sh = self._pm.width(), self._pm.height()
            ox = (sw - self.width()) // 2
            oy = (sh - self.height()) // 2
            p.drawPixmap(0, 0, self._pm, ox, oy, self.width(), self.height())
        else:
            p.fillRect(0, 0, self.width(), self.height(), QColor(BG3))
            p.setPen(QColor(BORDER))
            # dashed placeholder border
            pen = QPen(QColor(BORDER), 1, Qt.DashLine)
            p.setPen(pen)
            p.drawRoundedRect(1, 1, self.width()-2, self.height()-2, self._r, self._r)
            p.setPen(QColor(TEXTD))
            font = QFont(); font.setPixelSize(9)
            p.setFont(font)
            p.drawText(self.rect(), Qt.AlignCenter, "No image")


# ══════════════════════════════════════════════════════════════
#  SWATCH DOT
# ══════════════════════════════════════════════════════════════
class SwatchDot(QWidget):
    def __init__(self, hex_color, size=22):
        super().__init__()
        self.setFixedSize(size, size)
        self._c = QColor(hex_color)
        self.setStyleSheet("background:transparent;")

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(self._c))
        p.setPen(QPen(QColor(BORDER), 1))
        r = self.width() // 2
        p.drawEllipse(self.rect().adjusted(1, 1, -1, -1))


# ══════════════════════════════════════════════════════════════
#  CIRCULAR SCORE RING
# ══════════════════════════════════════════════════════════════
class ScoreRing(QWidget):
    def __init__(self, score=92, size=70):
        super().__init__()
        self._score = score
        self._size = size
        self.setFixedSize(size, size)
        self.setStyleSheet("background:transparent;")

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        margin = 7
        thick = 7
        rect = QRect(margin, margin, self._size - 2*margin, self._size - 2*margin)
        # track
        pen = QPen(QColor(BORDER), thick, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, 0, 360 * 16)
        # arc
        pen2 = QPen(QColor(SUCCESS), thick, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen2)
        span = int(self._score / 100 * 360 * 16)
        p.drawArc(rect, 90 * 16, -span)
        # text
        p.setPen(QColor(SUCCESS))
        f = QFont(); f.setPixelSize(15); f.setBold(True)
        p.setFont(f)
        p.drawText(rect, Qt.AlignCenter, f"{self._score}%")


# ══════════════════════════════════════════════════════════════
#  PANEL CARD  –  dark card with optional accent-color header band
# ══════════════════════════════════════════════════════════════
class PanelCard(QFrame):
    """A dark card. Pass header_text+header_color to get a colored title band."""
    def __init__(self, header_text=None, header_color=None, bg=None, border=None):
        super().__init__()
        bg = bg or BG3
        border = border or BORDER
        self.setStyleSheet(
            f"QFrame#panelCard{{background:{bg};border:1px solid {border};"
            f"border-radius:12px;}}")
        self.setObjectName("panelCard")

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._outer.setSpacing(0)

        if header_text:
            hdr = QWidget()
            hdr.setStyleSheet(
                f"background:{header_color or ACCENT2};"
                f"border-radius:12px 12px 0 0;")
            hdr.setFixedHeight(32)
            hl = QHBoxLayout(hdr)
            hl.setContentsMargins(12, 0, 12, 0)
            lh = QLabel(header_text.upper())
            lh.setStyleSheet(
                "color:#fff;font-size:9px;font-weight:800;"
                "letter-spacing:2px;background:transparent;")
            hl.addWidget(lh)
            self._outer.addWidget(hdr)

        self.body = QWidget()
        self.body.setStyleSheet("background:transparent;")
        self._body_layout = QVBoxLayout(self.body)
        self._body_layout.setContentsMargins(14, 12, 14, 12)
        self._body_layout.setSpacing(8)
        self._outer.addWidget(self.body, 1)

    def layout_(self):
        return self._body_layout

    def add(self, widget):
        self._body_layout.addWidget(widget)

    def add_layout(self, layout):
        self._body_layout.addLayout(layout)


# ══════════════════════════════════════════════════════════════
#  REC BLOCK  –  one recommendation tile (hairstyle, hijab…)
# ══════════════════════════════════════════════════════════════
class RecBlock(QFrame):
    def __init__(self, title, paths, caption, accent, img_w=100, img_h=118, show=3):
        super().__init__()
        self.setStyleSheet(
            f"QFrame{{background:{BG3};border:1px solid {BORDER};border-radius:12px;}}")
        v = QVBoxLayout(self)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(8)

        v.addWidget(section_label(title, accent))

        row = QHBoxLayout(); row.setSpacing(6); row.setContentsMargins(0, 0, 0, 0)
        for i, p in enumerate(paths[:show]):
            row.addWidget(RoundImg(p, img_w, img_h, 8))
        for _ in range(show - min(show, len(paths))):
            row.addWidget(RoundImg(None, img_w, img_h, 8))
        row.addStretch()
        v.addLayout(row)

        cap = QLabel(caption)
        cap.setWordWrap(True)
        cap.setStyleSheet(
            f"color:{TEXTM};font-size:10px;background:transparent;"
            f"line-height:16px;")
        v.addWidget(cap)


# ══════════════════════════════════════════════════════════════
#  HEADER BAR
# ══════════════════════════════════════════════════════════════
class Header(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(68)
        self.setStyleSheet(
            f"QFrame{{background:{BG2};border:none;"
            f"border-bottom:1px solid {BORDER};border-radius:0;}}")

        h = QHBoxLayout(self)
        h.setContentsMargins(24, 0, 24, 0)
        h.setSpacing(0)

        # logo block
        logo_col = QVBoxLayout(); logo_col.setSpacing(3)
        title = QLabel("AI STYLE RECOMMENDER")
        title.setStyleSheet(
            f"color:{ACCENT};font-size:20px;font-weight:900;"
            f"letter-spacing:3px;background:transparent;")
        sub = QLabel("Scan. Analyze. Recommend.")
        sub.setStyleSheet(
            f"color:{TEXTD};font-size:10px;letter-spacing:1.5px;background:transparent;")
        logo_col.addWidget(title)
        logo_col.addWidget(sub)
        h.addLayout(logo_col)
        h.addStretch()

        # step pipeline  1 → 2 → 3 → 4
        steps_data = [
            ("⬡", "1. Scan Face"),
            ("⬡", "2. Analyze\nOpenCV + ML"),
            ("☆", "3. Recommend"),
            ("✓", "4. Results"),
        ]
        for i, (icon, label) in enumerate(steps_data):
            if i > 0:
                arr = QLabel("→")
                arr.setStyleSheet(
                    f"color:{BORDER};font-size:16px;background:transparent;"
                    f"padding:0 14px;")
                h.addWidget(arr)
            col = QVBoxLayout(); col.setSpacing(2); col.setAlignment(Qt.AlignCenter)
            ic = QLabel(icon)
            ic.setAlignment(Qt.AlignCenter)
            ic.setStyleSheet(
                f"color:{ACCENT2};font-size:18px;background:transparent;")
            lb = QLabel(label)
            lb.setAlignment(Qt.AlignCenter)
            lb.setStyleSheet(
                f"color:{TEXTD};font-size:8px;letter-spacing:0.5px;"
                f"background:transparent;")
            col.addWidget(ic, 0, Qt.AlignHCenter)
            col.addWidget(lb)
            h.addLayout(col)


# ══════════════════════════════════════════════════════════════
#  FOOTER BAR
# ══════════════════════════════════════════════════════════════
class Footer(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(36)
        self.setStyleSheet(
            f"QFrame{{background:{BG2};border:none;"
            f"border-top:1px solid {BORDER};border-radius:0;}}")
        h = QHBoxLayout(self)
        h.setContentsMargins(24, 0, 24, 0)
        h.setSpacing(10)

        tag = QLabel("TECHNOLOGY BEHIND")
        tag.setStyleSheet(
            f"color:{TEXTD};font-size:8px;font-weight:800;"
            f"letter-spacing:2px;background:transparent;")
        h.addWidget(tag)

        sep = QFrame(); sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color:{BORDER};background:{BORDER};max-width:1px;")
        h.addWidget(sep)

        for t in ["OpenCV", "Face Detection", "Landmark Detection",
                  "Skin Tone Classification", "Face Shape Prediction",
                  "Recommendation Engine"]:
            chip = QLabel(t)
            chip.setStyleSheet(
                f"background:{BG3};color:{TEXTM};border-radius:4px;"
                f"border:1px solid {BORDER};font-size:9px;"
                f"padding:2px 8px;")
            h.addWidget(chip)
        h.addStretch()


# ══════════════════════════════════════════════════════════════
#  LEFT PANEL  –  SCAN YOUR FACE
# ══════════════════════════════════════════════════════════════
class ScanPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(320)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        # ── title strip ──
        tc = QFrame()
        tc.setStyleSheet(
            f"QFrame{{background:{BG2};border:1px solid {BORDER};border-radius:10px;}}")
        tv = QVBoxLayout(tc); tv.setContentsMargins(14, 10, 14, 10); tv.setSpacing(2)
        tv.addWidget(mk_label("1.  SCAN YOUR FACE", 12, bold=True))
        root.addWidget(tc)

        # ── face image display ──
        face_frame = QFrame()
        face_frame.setStyleSheet(
            f"QFrame{{background:{BG3};border:1px solid {BORDER};border-radius:12px;}}")
        fv = QVBoxLayout(face_frame)
        fv.setContentsMargins(8, 8, 8, 8); fv.setSpacing(0)

        self.face_lbl = QLabel()
        self.face_lbl.setFixedSize(300, 330)
        self.face_lbl.setAlignment(Qt.AlignCenter)
        self.face_lbl.setStyleSheet(
            f"background:{BG3};border-radius:8px;"
            f"color:{TEXTD};font-size:12px;border:none;")
        self.face_lbl.setText("Drop or select\na photo here")
        fv.addWidget(self.face_lbl)
        root.addWidget(face_frame)

        # ── buttons ──
        self.btn_up = self._mk_btn("⬆  UPLOAD PHOTO", ACCENT2, ACCENT)
        self.btn_an = self._mk_btn("◉  ANALYSE FACE", ACCENT3, ACCENT2)
        self.btn_an.setEnabled(False)
        root.addWidget(self.btn_up)
        root.addWidget(self.btn_an)

        # ── progress bar ──
        self.prog = QProgressBar()
        self.prog.setFixedHeight(5)
        self.prog.setRange(0, 100)
        self.prog.setValue(0)
        self.prog.setTextVisible(False)
        self.prog.setStyleSheet(f"""
            QProgressBar{{background:{BORDER};border-radius:2px;border:none;}}
            QProgressBar::chunk{{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {ACCENT2}, stop:1 {ACCENT});
                border-radius:2px;}}""")
        root.addWidget(self.prog)
        self.prog_lbl = mk_label("Ready", 10, color=TEXTD)
        root.addWidget(self.prog_lbl)

        # ── detection status card ──
        root.addWidget(self._build_status())
        root.addStretch()

    # ── helpers ──────────────────────────────────────────────
    def _mk_btn(self, text, c1, c2):
        b = QPushButton(text)
        b.setFixedHeight(42)
        b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet(f"""
            QPushButton{{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {c1}, stop:1 {c2});
                color:#fff;border:none;border-radius:10px;
                font-size:11px;font-weight:800;letter-spacing:1.5px;}}
            QPushButton:hover{{opacity:0.9;}}
            QPushButton:disabled{{
                background:{BG3};color:{TEXTD};
                border:1px solid {BORDER};}}""")
        return b

    def _build_status(self):
        card = QFrame()
        card.setStyleSheet(
            f"QFrame{{background:{BG3};border:1px solid {BORDER};border-radius:10px;}}")
        v = QVBoxLayout(card)
        v.setContentsMargins(14, 12, 14, 12)
        v.setSpacing(10)

        hdr = QLabel("DETECTION STATUS")
        hdr.setStyleSheet(
            f"color:{TEXTD};font-size:8px;font-weight:800;"
            f"letter-spacing:2px;background:transparent;")
        v.addWidget(hdr)

        self._dots = {}
        for k in ["Face Detected", "Landmarks Detected",
                  "Skin Analysed", "Face Shape Identified"]:
            row = QHBoxLayout(); row.setSpacing(10)
            dot = QLabel("○")
            dot.setFixedWidth(18)
            dot.setAlignment(Qt.AlignCenter)
            dot.setStyleSheet(
                f"color:{TEXTD};font-size:15px;background:transparent;")
            txt = mk_label(k, 11, color=TEXTD)
            row.addWidget(dot); row.addWidget(txt); row.addStretch()
            v.addLayout(row)
            self._dots[k] = (dot, txt)
        return card

    # ── public API ────────────────────────────────────────────
    def tick(self, key):
        if key in self._dots:
            dot, txt = self._dots[key]
            dot.setText("●")
            dot.setStyleSheet(
                f"color:{SUCCESS};font-size:15px;background:transparent;")
            txt.setStyleSheet(
                f"color:{TEXT};font-size:11px;font-weight:600;"
                f"background:transparent;")

    def reset(self):
        for k, (dot, txt) in self._dots.items():
            dot.setText("○")
            dot.setStyleSheet(
                f"color:{TEXTD};font-size:15px;background:transparent;")
            txt.setStyleSheet(
                f"color:{TEXTD};font-size:11px;background:transparent;")
        self.prog.setValue(0)
        self.prog_lbl.setText("Ready")

    def show_img(self, pm):
        scaled = pm.scaled(300, 330, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.face_lbl.setPixmap(scaled)
        self.face_lbl.setAlignment(Qt.AlignCenter)

    def enable_scan(self, on):
        self.btn_an.setEnabled(on)


# ══════════════════════════════════════════════════════════════
#  MIDDLE PANEL  –  ANALYSIS RESULTS
# ══════════════════════════════════════════════════════════════
class AnalysisPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(260)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        # title strip
        tc = QFrame()
        tc.setStyleSheet(
            f"QFrame{{background:{BG2};border:1px solid {BORDER};border-radius:10px;}}")
        tv = QVBoxLayout(tc); tv.setContentsMargins(14, 10, 14, 10); tv.setSpacing(2)
        tv.addWidget(mk_label("2.  ANALYSIS RESULTS", 12, bold=True))
        root.addWidget(tc)

        # scrollable cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea{background:transparent;border:none;}
            QScrollBar:vertical{background:#111119;width:4px;border-radius:2px;}
            QScrollBar::handle:vertical{background:#252538;border-radius:2px;min-height:20px;}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}
        """)

        self.inner = QWidget()
        self.inner.setStyleSheet("background:transparent;")
        self.cards_layout = QVBoxLayout(self.inner)
        self.cards_layout.setContentsMargins(0, 0, 4, 0)
        self.cards_layout.setSpacing(10)

        self._placeholder = mk_label(
            "Upload a photo\nto see results.",
            12, color=TEXTD, align=Qt.AlignCenter, wrap=True)
        self.cards_layout.addWidget(self._placeholder)
        self.cards_layout.addStretch()

        scroll.setWidget(self.inner)
        root.addWidget(scroll, 1)

    def _clear(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _card(self, accent=ACCENT):
        """Returns (frame, inner_vlayout)"""
        f = QFrame()
        f.setStyleSheet(
            f"QFrame{{background:{BG3};"
            f"border:1px solid {BORDER};"
            f"border-left:3px solid {accent};"
            f"border-radius:10px;}}")
        v = QVBoxLayout(f)
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(6)
        return f, v

    def populate(self, res):
        self._clear()
        ut  = res["undertone"];  uti = UNDERTONE_INFO[ut]
        fs  = res["face_shape"]; fst = FACE_TIPS.get(fs, {})
        es  = res["eye_shape"]
        con = res["contrast"]

        # ── SKIN TONE ──────────────────────────────
        c, v = self._card(ACCENT)
        v.addWidget(section_label("Skin Tone", ACCENT))
        row = QHBoxLayout(); row.setSpacing(10)
        sw = SwatchDot(uti["swatch"], 44)
        col = QVBoxLayout(); col.setSpacing(3)
        col.addWidget(mk_label(uti["label"], 12, bold=True))
        col.addWidget(mk_label(uti["undertone"], 10, color=TEXTD))
        row.addWidget(sw); row.addLayout(col); row.addStretch()
        v.addLayout(row)
        self.cards_layout.addWidget(c)

        # ── FACE SHAPE ─────────────────────────────
        c2, v2 = self._card(ACCENT2)
        v2.addWidget(section_label("Face Shape", ACCENT2))
        v2.addWidget(mk_label(fs.capitalize(), 13, bold=True))
        for d in fst.get("desc", []):
            row2 = QHBoxLayout(); row2.setSpacing(6)
            dot2 = QLabel("•"); dot2.setStyleSheet(
                f"color:{ACCENT2};font-size:12px;background:transparent;")
            row2.addWidget(dot2); row2.addWidget(mk_label(d, 10, color=TEXTD))
            row2.addStretch()
            v2.addLayout(row2)
        self.cards_layout.addWidget(c2)

        # ── FEATURES ───────────────────────────────
        c3, v3 = self._card(ACCENT3)
        v3.addWidget(section_label("Features", ACCENT3))
        for k, val in [("Eye Shape", es.capitalize()),
                       ("Eyebrow", "Soft Arch"),
                       ("Nose", "Straight"),
                       ("Lips", "Medium Full")]:
            row3 = QHBoxLayout(); row3.setSpacing(0)
            row3.addWidget(mk_label(k + ":", 10, color=TEXTD))
            row3.addSpacing(6)
            row3.addWidget(mk_label(val, 10, bold=True))
            row3.addStretch()
            v3.addLayout(row3)
        self.cards_layout.addWidget(c3)

        # ── COLOR ANALYSIS ─────────────────────────
        c4, v4 = self._card(WARN)
        v4.addWidget(section_label("Color Analysis", WARN))
        v4.addWidget(mk_label("Best Colors", 10, color=TEXTD))
        sr = QHBoxLayout(); sr.setSpacing(6)
        for hx in uti["best"]:
            sr.addWidget(SwatchDot(hx, 22))
        sr.addStretch()
        v4.addLayout(sr)
        self.cards_layout.addWidget(c4)

        # ── CONTRAST LEVEL ─────────────────────────
        c5, v5 = self._card(ACCENT)
        v5.addWidget(section_label("Contrast Level", ACCENT))
        v5.addWidget(mk_label(con.capitalize(), 11, bold=True))
        pb = QProgressBar()
        pb.setFixedHeight(7)
        pb.setRange(0, 3)
        pb.setValue({"low": 1, "medium": 2, "high": 3}.get(con, 2))
        pb.setTextVisible(False)
        pb.setStyleSheet(f"""
            QProgressBar{{background:{BORDER};border-radius:3px;border:none;}}
            QProgressBar::chunk{{background:{ACCENT};border-radius:3px;}}""")
        v5.addWidget(pb)
        self.cards_layout.addWidget(c5)

        self.cards_layout.addStretch()


# ══════════════════════════════════════════════════════════════
#  RIGHT PANEL  –  RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════
class RecPanel(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        # title strip
        tc = QFrame()
        tc.setStyleSheet(
            f"QFrame{{background:{BG2};border:1px solid {BORDER};border-radius:10px;}}")
        tv = QVBoxLayout(tc); tv.setContentsMargins(14, 10, 14, 10); tv.setSpacing(2)
        tv.addWidget(mk_label("3.  RECOMMENDATIONS", 12, bold=True))
        root.addWidget(tc)

        # scrollable 2-column grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea{background:transparent;border:none;}
            QScrollBar:vertical{background:#111119;width:4px;border-radius:2px;}
            QScrollBar::handle:vertical{background:#252538;border-radius:2px;min-height:20px;}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}
        """)

        self.inner = QWidget()
        self.inner.setStyleSheet("background:transparent;")
        self.grid = QGridLayout(self.inner)
        self.grid.setContentsMargins(0, 0, 6, 6)
        self.grid.setSpacing(10)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)

        self._ph = mk_label(
            "Recommendations will appear\nafter analysis.",
            12, color=TEXTD, align=Qt.AlignCenter, wrap=True)
        self.grid.addWidget(self._ph, 0, 0, 1, 2, Qt.AlignCenter)

        scroll.setWidget(self.inner)
        root.addWidget(scroll, 1)

    def _clear(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def populate(self, res, recs):
        self._clear()
        fs = res["face_shape"]
        es = res["eye_shape"]
        ut = res["undertone"]
        ft = FACE_TIPS.get(fs, {})

        blocks = [
            ("Hairstyle",     recs["hairstyles"],    ft.get("hair",""),   ACCENT,  100, 118, 3),
            ("Hijaab Style",  recs["hijaab"],         ft.get("hijab",""),  ACCENT2, 100, 118, 3),
            ("Outfit Colors", recs["colours"],        ft.get("color",""),  WARN,    100, 110, 3),
            ("Outfit Style",  recs["outfit_style"],   ft.get("outfit",""), ACCENT3, 100, 110, 3),
            ("Accessories",   recs["accessories"],    "Minimal gold jewelry and classic watches.", SUCCESS, 100, 100, 3),
        ]

        for i, (title, paths, caption, accent, iw, ih, show) in enumerate(blocks):
            r, col = divmod(i, 2)
            self.grid.addWidget(
                RecBlock(title, paths, caption, accent, iw, ih, show), r, col)

        # ── bottom strip: skincare / makeup / score ──
        bot = QFrame()
        bot.setStyleSheet(
            f"QFrame{{background:{BG3};border:1px solid {BORDER};border-radius:12px;}}")
        bh = QHBoxLayout(bot)
        bh.setContentsMargins(14, 14, 14, 14)
        bh.setSpacing(14)

        # skincare & makeup
        for heading, tip in [
            ("Skincare Tips", SKIN_TIPS.get(ut, "")),
            ("Makeup Tips",   MAKEUP_TIPS.get(ut, "")),
        ]:
            tf = QFrame()
            tf.setStyleSheet(
                f"QFrame{{background:{BG2};border:1px solid {BORDER};border-radius:8px;}}")
            tv = QVBoxLayout(tf); tv.setContentsMargins(12, 10, 12, 10); tv.setSpacing(5)
            tv.addWidget(section_label(heading, TEXTM))
            tip_lbl = QLabel(tip)
            tip_lbl.setWordWrap(True)
            tip_lbl.setStyleSheet(
                f"color:{TEXTM};font-size:10px;background:transparent;")
            tv.addWidget(tip_lbl)
            bh.addWidget(tf, 1)

        # style score
        sf = QFrame()
        sf.setStyleSheet(
            f"QFrame{{background:{BG2};border:1px solid {ACCENT2};border-radius:8px;}}")
        sv = QVBoxLayout(sf); sv.setContentsMargins(12, 12, 12, 12); sv.setSpacing(6)
        sv.addWidget(section_label("Your Style Score", ACCENT2))
        sv.addWidget(ScoreRing(92, 70), 0, Qt.AlignHCenter)
        sv.addWidget(mk_label(
            "You have a great sense of style!\nFollow the recommendations.",
            9, color=TEXTD, align=Qt.AlignCenter, wrap=True))
        bh.addWidget(sf)

        row_count = (len(blocks) + 1) // 2
        self.grid.addWidget(bot, row_count, 0, 1, 2)


# ══════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ══════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Style Recommender")
        self.setMinimumSize(1200, 800)
        self.resize(1440, 900)
        self._img_path = None
        self._engine   = FaceEngine()
        self._loader   = DatasetLoader(DATASET_ROOT)
        self._apply_style()
        self._build()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background:{BG};
                color:{TEXT};
                font-family:'Segoe UI','Inter','Helvetica Neue',Arial,sans-serif;
            }}
            QScrollBar:vertical{{
                background:{BG2};width:4px;border-radius:2px;margin:0;}}
            QScrollBar::handle:vertical{{
                background:{BORDER};border-radius:2px;min-height:20px;}}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical{{height:0;border:none;}}
        """)

    def _build(self):
        cw = QWidget(); self.setCentralWidget(cw)
        rv = QVBoxLayout(cw)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(0)

        rv.addWidget(Header())

        body = QWidget()
        bh = QHBoxLayout(body)
        bh.setContentsMargins(14, 14, 14, 14)
        bh.setSpacing(12)

        self.sp = ScanPanel()
        self.ap = AnalysisPanel()
        self.rp = RecPanel()

        self.sp.btn_up.clicked.connect(self._upload)
        self.sp.btn_an.clicked.connect(self._analyse)

        bh.addWidget(self.sp)
        bh.addWidget(self.ap)
        bh.addWidget(self.rp, 1)

        rv.addWidget(body, 1)
        rv.addWidget(Footer())

    # ── slots ────────────────────────────────────────────────
    def _upload(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Photo", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if not path:
            return
        self._img_path = path
        self.sp.show_img(QPixmap(path))
        self.sp.enable_scan(True)
        self.sp.reset()
        self.sp.prog_lbl.setText("Photo loaded – ready to analyse.")

    def _analyse(self):
        if not self._img_path:
            return
        self.sp.btn_an.setEnabled(False)
        self.sp.btn_up.setEnabled(False)
        self.sp.reset()
        self._worker = Worker(self._img_path, self._engine, self._loader)
        self._worker.progress.connect(self._on_prog)
        self._worker.done.connect(self._on_done)
        self._worker.failed.connect(self._on_err)
        self._worker.start()

    def _on_prog(self, val, msg):
        self.sp.prog.setValue(val)
        self.sp.prog_lbl.setText(msg)
        if val >= 15:  self.sp.tick("Face Detected")
        if val >= 45:  self.sp.tick("Landmarks Detected")
        if val >= 65:  self.sp.tick("Skin Analysed")
        if val >= 80:  self.sp.tick("Face Shape Identified")

    def _on_done(self, res, recs):
        self.sp.prog.setValue(100)
        self.sp.prog_lbl.setText("✓  Analysis complete!")
        for k in ["Face Detected", "Landmarks Detected",
                  "Skin Analysed", "Face Shape Identified"]:
            self.sp.tick(k)
        self.sp.show_img(cv2px(res["annotated"]))
        self.ap.populate(res)
        self.rp.populate(res, recs)
        self.sp.btn_an.setEnabled(True)
        self.sp.btn_up.setEnabled(True)
        self.sp.enable_scan(True)

    def _on_err(self, msg):
        self.sp.prog_lbl.setText(f"⚠  {msg}")
        self.sp.prog.setValue(0)
        self.sp.btn_an.setEnabled(True)
        self.sp.btn_up.setEnabled(True)
        self.sp.enable_scan(True)


# ══════════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("AI Style Recommender")
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())