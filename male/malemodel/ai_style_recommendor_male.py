"""
╔══════════════════════════════════════════════════════════════╗
║       AI STYLE RECOMMENDER  –  MALE  |  Complete App        ║
║  OpenCV + MediaPipe  |  PyQt5 UI  |  Male Dataset           ║
╚══════════════════════════════════════════════════════════════╝

HOW TO RUN:
    pip install opencv-python mediapipe PyQt5 numpy Pillow
    python ai_style_recommendor_male.py

DATASET ROOT:  Set DATASET_ROOT below to your actual path.
               Default assumes  dataset/  is next to this script.
"""

import sys, os, math, random, colorsys
from pathlib import Path

import cv2
import numpy as np
import mediapipe as mp

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea, QFrame,
    QFileDialog, QSizePolicy, QProgressBar,
)
from PyQt5.QtCore  import Qt, QThread, pyqtSignal, QRect
from PyQt5.QtGui   import (
    QPixmap, QImage, QColor, QFont, QPainter, QPen, QBrush,
    QPainterPath
)

# ──────────────────────────────────────────────────────────────
#  ★  EDIT THIS PATH to point at your MALEMODEL/dataset folder ★
# ──────────────────────────────────────────────────────────────
DATASET_ROOT = Path(__file__).parent / "dataset"

# ══════════════════════════════════════════════════════════════
#  COLOUR THEME
# ══════════════════════════════════════════════════════════════
BG      = "#0A0A12"
BG2     = "#111119"
BG3     = "#181825"
BORDER  = "#252538"
ACCENT  = "#00C8F0"
ACCENT2 = "#6C4FE8"
ACCENT3 = "#E8557A"
SUCCESS = "#00E896"
WARN    = "#E8A030"
TEXT    = "#EEEEF8"
TEXTD   = "#55557A"
TEXTM   = "#9090B8"

# ══════════════════════════════════════════════════════════════
#  KNOWLEDGE BASE
# ══════════════════════════════════════════════════════════════
UNDERTONE_INFO = {
    "cool":   dict(label="Cool / Light",       undertone="Cool · Pink-Red",
                   swatch="#F2C9A8",
                   best=["#E8D5C4","#6A5ACD","#708090","#C71585","#2F4F4F","#B8860B"]),
    "light":  dict(label="Light / Fair",        undertone="Neutral · Balanced",
                   swatch="#FDDBB4",
                   best=["#DEB887","#228B22","#8B0000","#4169E1","#DAA520","#800080"]),
    "medium": dict(label="Light-Medium / Warm", undertone="Warm · Golden-Olive",
                   swatch="#D2956A",
                   best=["#8B6914","#556B2F","#8B3A3A","#1C3A5E","#A0522D","#6B3A6B"]),
    "warm":   dict(label="Medium / Deep",       undertone="Warm · Rich Mahogany",
                   swatch="#A0674A",
                   best=["#5C3317","#2D5016","#7B2D00","#1A2744","#704214","#4A1942"]),
}

FACE_TIPS = {
    "oval":      dict(
        desc=["Balanced Proportions","Slightly Narrow Chin","Wider Forehead"],
        hair="Ivy league, classic side part or messy medium – most styles suit oval.",
        beard="Most beard styles work – full beard, goatee or light stubble all complement.",
        outfit="Slim-fit shirts, structured jackets and minimal patterns.",
        color="Earth tones, navy and warm neutrals look best on you."),
    "round":     dict(
        desc=["Full Cheeks","Soft Jawline","Similar Width & Length"],
        hair="High fade, pompadour or quiff – add height to elongate the face.",
        beard="Angular beard with defined lines to add length and definition.",
        outfit="Vertical stripes, V-necks and slim-fit silhouettes.",
        color="Deep, cool tones and dark shades create definition."),
    "heart":     dict(
        desc=["Wide Forehead","High Cheekbones","Narrow Chin"],
        hair="Side-swept, textured crop or ivy league to reduce forehead width.",
        beard="Fuller beard on the chin to balance the wide forehead.",
        outfit="Wider collars, horizontal chest detail, layered tops.",
        color="Soft pastels and warm neutrals flatter the complexion."),
    "square":    dict(
        desc=["Strong Angular Jaw","Broad Forehead","Defined Features"],
        hair="Curly top, slick back or longer top to soften angular features.",
        beard="Short stubble or rounded beard to soften the strong jawline.",
        outfit="Round-neck tees, bomber jackets and soft fabrics.",
        color="Soft warm hues and dusty tones complement squared features."),
    "rectangle": dict(
        desc=["Long Face","Strong Jaw","High Forehead"],
        hair="French crop, textured fringe or curtain bangs to add horizontal width.",
        beard="Full beard or wide-set stubble to add width to the face.",
        outfit="Horizontal stripes, wide lapels, layered looks.",
        color="Rich warm tones and warm neutrals work beautifully."),
    "diamond":   dict(
        desc=["Narrow Forehead & Chin","Wide Cheekbones","Angular"],
        hair="Curtain bangs, side parts and volume on top add forehead width.",
        beard="Goatee or chin-strap to add definition to the narrow chin.",
        outfit="Off-shoulder, boat necks and statement necklines.",
        color="Jewel tones and rich earthy hues suit diamond faces."),
    "triangle":  dict(
        desc=["Wide Jaw","Narrow Forehead","Strong Chin"],
        hair="Pompadour, quiff or volume at crown to widen the forehead.",
        beard="Light stubble only – heavy beard emphasises the wide jaw.",
        outfit="Detailed tops, shoulder emphasis, peplum-style layering.",
        color="Light tones on top, darker tones on bottom balance the shape."),
}

GROOMING_TIPS = {
    "cool":   "Daily moisturiser with SPF. Use a gentle face wash and toner for oily zones.",
    "light":  "Hydrate & protect. SPF daily, gentle exfoliation weekly. Hyaluronic acid serum.",
    "medium": "Niacinamide for even tone. Retinol at night. Mineral SPF 50+ essential.",
    "warm":   "Antioxidant serums, glycolic acid & rich moisturisers. SPF every day.",
}
STYLE_TIPS = {
    "cool":   "Monochrome outfits, clean tailoring and cool-toned accessories suit you.",
    "light":  "Neutral palettes, earthy tones and well-fitted basics elevate your look.",
    "medium": "Warm earthy tones, structured casual wear and leather accessories.",
    "warm":   "Deep jewel tones, rich fabrics and bold accessories define your style.",
}

# ══════════════════════════════════════════════════════════════
#  DATASET LOADER
# ══════════════════════════════════════════════════════════════
class DatasetLoader:
    def __init__(self, root: Path):
        self.root = root

    @staticmethod
    def _match_folder(children, target):
        tl = target.lower().strip()
        for c in children:
            if c.name.lower() == tl:
                return c
        def similarity(a, b):
            a, b = a.lower(), b.lower()
            matches = sum(1 for x, y in zip(sorted(a), sorted(b)) if x == y)
            return matches - abs(len(a) - len(b))
        if len(tl) <= 12 and ' ' not in tl:
            best = max(children, key=lambda c: similarity(c.name, tl), default=None)
            if best and similarity(best.name, tl) >= max(3, len(tl) - 2):
                return best
        return None

    def _resolve(self, *parts):
        p = self.root
        for part in parts:
            if part is None: return None
            try:
                children = [c for c in p.iterdir() if c.is_dir()]
            except Exception:
                return None
            match = next((c for c in children if c.name.lower() == part.lower().strip()), None)
            if match is None:
                match = self._match_folder(children, part)
            if match is None:
                return None
            p = match
        return p

    def _images(self, folder, count=None):
        if folder is None or not folder.exists():
            return []
        imgs = sorted(
            [f for f in folder.iterdir()
             if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg")],
            key=lambda x: x.name)
        return imgs if count is None else imgs[:count]

    def hairstyles(self, face_shape, count=3):
        return self._images(self._resolve("hairstyle", face_shape), count)

    def beard(self, face_shape, count=3):
        return self._images(self._resolve("beard", face_shape), count)

    def colours(self, face_shape, undertone, count=3):
        return self._images(self._resolve("colours", face_shape, undertone), count)

    def outfit_styles(self, face_shape, undertone, count=3):
        return self._images(self._resolve("outfit styles", face_shape, undertone), count)

    def accessories(self, face_shape, count=2):
        return self._images(self._resolve("accessories", face_shape), count)

    def debug_paths(self, face_shape, undertone):
        checks = [
            ("hairstyle",     self._resolve("hairstyle",     face_shape)),
            ("beard",         self._resolve("beard",          face_shape)),
            ("colours",       self._resolve("colours",        face_shape, undertone)),
            ("outfit styles", self._resolve("outfit styles",  face_shape, undertone)),
            ("accessories",   self._resolve("accessories",    face_shape)),
        ]
        for name, path in checks:
            status = "✓" if path and path.exists() else "✗ NOT FOUND"
            print(f"  {status}  {name:20s}  →  {path}")


# ══════════════════════════════════════════════════════════════
#  FACE ANALYSIS ENGINE
# ══════════════════════════════════════════════════════════════
class FaceEngine:
    def __init__(self):
        self.fm = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True, max_num_faces=1,
            refine_landmarks=True, min_detection_confidence=0.5)

    def _pt(self, lms, i, w, h):
        l = lms[i]; return (int(l.x*w), int(l.y*h))

    def _d(self, a, b):
        return math.hypot(a[0]-b[0], a[1]-b[1])

    def _face_shape(self, lms, w, h):
        jaw_l  = self._pt(lms,234,w,h); jaw_r  = self._pt(lms,454,w,h)
        top    = self._pt(lms,10, w,h); bot    = self._pt(lms,152,w,h)
        ch_l   = self._pt(lms,93, w,h); ch_r   = self._pt(lms,323,w,h)
        fore_l = self._pt(lms,54, w,h); fore_r = self._pt(lms,284,w,h)
        chin_l = self._pt(lms,172,w,h); chin_r = self._pt(lms,397,w,h)
        jaw_w   = self._d(jaw_l,jaw_r)
        face_h  = self._d(top,bot)
        cheek_w = self._d(ch_l,ch_r)
        fore_w  = self._d(fore_l,fore_r)
        chin_w  = self._d(chin_l,chin_r)
        ratio   = face_h / max(jaw_w,1)
        if ratio   > 1.80:                       return "rectangle"
        if cheek_w > jaw_w*1.20 and ratio < 1.5: return "diamond"
        if chin_w  > fore_w*1.10:                return "triangle"
        if ratio   < 1.20:                       return "round"
        if fore_w  > chin_w*1.20:                return "heart"
        if 1.30    < ratio < 1.65:               return "oval"
        return "square"

    def _eye_shape(self, lms, w, h):
        li = self._pt(lms,133,w,h); lo = self._pt(lms,33, w,h)
        lt = self._pt(lms,159,w,h); lb = self._pt(lms,145,w,h)
        ew = self._d(li,lo); eh = self._d(lt,lb)
        ratio = eh / max(ew,1)
        tilt  = lo[1] - li[1]
        if ratio > 0.36: return "round"
        if tilt  >  4:   return "downturned"
        if tilt  < -4:   return "upturned"
        if ew    < 55:   return "monolid"
        crease = self._pt(lms,160,w,h)
        if abs(crease[1]-lt[1]) < 4: return "hooded"
        return "almond"

    def _undertone(self, bgr, lms, w, h):
        pts  = [self._pt(lms,i,w,h) for i in [205,425,234,454]]
        vals = []
        for (x,y) in pts:
            roi = bgr[max(0,y-12):y+12, max(0,x-12):x+12]
            if roi.size: vals.append(roi.reshape(-1,3).mean(0))
        if not vals: return "medium"
        r,g,b = np.mean(vals, axis=0)[[2,1,0]]
        bright = (r+g+b)/3
        warm_idx = r - b
        if   bright > 195: return "cool"   if warm_idx <  20 else "light"
        elif bright > 155: return "light"  if warm_idx <  30 else "medium"
        elif bright > 115: return "medium"
        else:              return "warm"

    def _contrast(self, bgr, lms, w, h):
        s = self._pt(lms,234,w,h)
        e = self._pt(lms,33, w,h)
        sr = cv2.cvtColor(bgr[max(0,s[1]-10):s[1]+10, max(0,s[0]-10):s[0]+10], cv2.COLOR_BGR2GRAY)
        er = cv2.cvtColor(bgr[max(0,e[1]-6): e[1]+6,  max(0,e[0]-6): e[0]+6],  cv2.COLOR_BGR2GRAY)
        if not sr.size or not er.size: return "medium"
        d = abs(float(sr.mean()) - float(er.mean()))
        return "high" if d>55 else ("medium" if d>25 else "low")

    def _overlay(self, bgr, lms, w, h):
        out = bgr.copy()
        jaw = [10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,
               378,400,377,152,148,176,149,150,136,172,58,132,93,234,
               127,162,21,54,103,67,109,10]
        for i in range(len(jaw)-1):
            cv2.line(out, self._pt(lms,jaw[i],w,h),
                         self._pt(lms,jaw[i+1],w,h), (0,212,255), 1)
        for idx in [10,152,234,454,93,323,33,133,159,145,362,263,386,374,1,61,291,17]:
            cv2.circle(out, self._pt(lms,idx,w,h), 3, (0,212,255), -1)
        return out

    def analyse(self, path):
        bgr = cv2.imread(str(path))
        if bgr is None:
            return {"error":"Cannot read image."}
        h, w = bgr.shape[:2]
        res  = self.fm.process(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        if not res.multi_face_landmarks:
            return {"error":"No face detected – please use a clear front-facing photo."}
        lms = res.multi_face_landmarks[0].landmark
        return dict(
            face_shape = self._face_shape(lms,w,h),
            eye_shape  = self._eye_shape (lms,w,h),
            undertone  = self._undertone (bgr,lms,w,h),
            contrast   = self._contrast  (bgr,lms,w,h),
            annotated  = self._overlay   (bgr,lms,w,h),
            error      = None
        )


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

        fs = res["face_shape"]; ut = res["undertone"]

        print(f"\n{'─'*60}")
        print(f"  Face Shape : {fs}  |  Undertone : {ut}")
        print(f"  Dataset root : {self.loader.root}  |  Exists: {self.loader.root.exists()}")
        self.loader.debug_paths(fs, ut)
        print(f"{'─'*60}\n")

        recs = dict(
            hairstyles   = self.loader.hairstyles(fs, 3),
            beard        = self.loader.beard(fs, 3),
            outfit_style = self.loader.outfit_styles(fs, ut, 3),
            colours      = self.loader.colours(fs, ut, 3),
            accessories  = self.loader.accessories(fs, 2),
        )
        self.progress.emit(100,"Done!")
        self.done.emit(res, recs)


# ══════════════════════════════════════════════════════════════
#  UI HELPERS
# ══════════════════════════════════════════════════════════════
def cv2px(bgr):
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w, c = rgb.shape
    return QPixmap.fromImage(QImage(rgb.data, w, h, c*w, QImage.Format_RGB888))


def mk_label(text, size=11, bold=False, color=None, align=Qt.AlignLeft, wrap=False):
    l = QLabel(text)
    c = color or TEXT
    l.setStyleSheet(
        f"color:{c};font-size:{size}px;"
        f"font-weight:{'700' if bold else '400'};"
        f"background:transparent;letter-spacing:0.2px;")
    l.setAlignment(align)
    if wrap: l.setWordWrap(True)
    return l


def section_label(text, color=ACCENT):
    l = QLabel(text.upper())
    l.setStyleSheet(
        f"color:{color};font-size:8px;font-weight:800;"
        f"letter-spacing:2.5px;background:transparent;")
    return l


# ══════════════════════════════════════════════════════════════
#  ROUNDED IMAGE
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
            ox = (sw - self.width())  // 2
            oy = (sh - self.height()) // 2
            p.drawPixmap(0, 0, self._pm, ox, oy, self.width(), self.height())
        else:
            p.fillRect(0, 0, self.width(), self.height(), QColor(BG3))
            pen = QPen(QColor(BORDER), 1, Qt.DashLine)
            p.setPen(pen)
            p.drawRoundedRect(1, 1, self.width()-2, self.height()-2, self._r, self._r)
            p.setPen(QColor(TEXTD))
            f = QFont(); f.setPixelSize(9); p.setFont(f)
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
        p.drawEllipse(self.rect().adjusted(1,1,-1,-1))


# ══════════════════════════════════════════════════════════════
#  CIRCULAR SCORE RING
# ══════════════════════════════════════════════════════════════
class ScoreRing(QWidget):
    def __init__(self, score=90, size=70):
        super().__init__()
        self._score = score
        self._size  = size
        self.setFixedSize(size, size)
        self.setStyleSheet("background:transparent;")

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        margin, thick = 7, 7
        rect = QRect(margin, margin, self._size-2*margin, self._size-2*margin)
        p.setPen(QPen(QColor(BORDER), thick, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 0, 360*16)
        p.setPen(QPen(QColor(SUCCESS), thick, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 90*16, -int(self._score/100*360*16))
        p.setPen(QColor(SUCCESS))
        f = QFont(); f.setPixelSize(15); f.setBold(True); p.setFont(f)
        p.drawText(rect, Qt.AlignCenter, f"{self._score}%")


# ══════════════════════════════════════════════════════════════
#  REC BLOCK
# ══════════════════════════════════════════════════════════════
class RecBlock(QFrame):
    def __init__(self, title, paths, caption, accent, img_w=100, img_h=118, show=3):
        super().__init__()
        self.setStyleSheet(
            f"QFrame{{background:{BG3};border:1px solid {BORDER};border-radius:12px;}}")
        v = QVBoxLayout(self)
        v.setContentsMargins(12,12,12,12); v.setSpacing(8)
        v.addWidget(section_label(title, accent))
        row = QHBoxLayout(); row.setSpacing(6); row.setContentsMargins(0,0,0,0)
        for p in paths[:show]: row.addWidget(RoundImg(p, img_w, img_h, 8))
        for _ in range(show - min(show, len(paths))):
            row.addWidget(RoundImg(None, img_w, img_h, 8))
        row.addStretch()
        v.addLayout(row)
        cap = QLabel(caption); cap.setWordWrap(True)
        cap.setStyleSheet(f"color:{TEXTM};font-size:10px;background:transparent;")
        v.addWidget(cap)


# ══════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════
class Header(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(68)
        self.setStyleSheet(
            f"QFrame{{background:{BG2};border:none;"
            f"border-bottom:1px solid {BORDER};border-radius:0;}}")
        h = QHBoxLayout(self); h.setContentsMargins(24,0,24,0); h.setSpacing(0)

        logo_col = QVBoxLayout(); logo_col.setSpacing(3)
        title = QLabel("AI STYLE RECOMMENDER  –  MALE")
        title.setStyleSheet(
            f"color:{ACCENT};font-size:19px;font-weight:900;"
            f"letter-spacing:3px;background:transparent;")
        sub = QLabel("Scan. Analyze. Recommend.")
        sub.setStyleSheet(
            f"color:{TEXTD};font-size:10px;letter-spacing:1.5px;background:transparent;")
        logo_col.addWidget(title); logo_col.addWidget(sub)
        h.addLayout(logo_col); h.addStretch()

        for i, (icon, label) in enumerate([
            ("⬡","1. Scan Face"),("⬡","2. Analyze\nOpenCV + ML"),
            ("☆","3. Recommend"),("✓","4. Results")]):
            if i > 0:
                arr = QLabel("→")
                arr.setStyleSheet(
                    f"color:{BORDER};font-size:16px;background:transparent;padding:0 14px;")
                h.addWidget(arr)
            col = QVBoxLayout(); col.setSpacing(2); col.setAlignment(Qt.AlignCenter)
            ic = QLabel(icon); ic.setAlignment(Qt.AlignCenter)
            ic.setStyleSheet(f"color:{ACCENT2};font-size:18px;background:transparent;")
            lb = QLabel(label); lb.setAlignment(Qt.AlignCenter)
            lb.setStyleSheet(
                f"color:{TEXTD};font-size:8px;letter-spacing:0.5px;background:transparent;")
            col.addWidget(ic, 0, Qt.AlignHCenter); col.addWidget(lb)
            h.addLayout(col)


# ══════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════
class Footer(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(36)
        self.setStyleSheet(
            f"QFrame{{background:{BG2};border:none;"
            f"border-top:1px solid {BORDER};border-radius:0;}}")
        h = QHBoxLayout(self); h.setContentsMargins(24,0,24,0); h.setSpacing(10)
        tag = QLabel("TECHNOLOGY BEHIND")
        tag.setStyleSheet(
            f"color:{TEXTD};font-size:8px;font-weight:800;"
            f"letter-spacing:2px;background:transparent;")
        h.addWidget(tag)
        sep = QFrame(); sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color:{BORDER};background:{BORDER};max-width:1px;")
        h.addWidget(sep)
        for t in ["OpenCV","Face Detection","Landmark Detection",
                  "Skin Tone Classification","Face Shape Prediction","Recommendation Engine"]:
            chip = QLabel(t)
            chip.setStyleSheet(
                f"background:{BG3};color:{TEXTM};border-radius:4px;"
                f"border:1px solid {BORDER};font-size:9px;padding:2px 8px;")
            h.addWidget(chip)
        h.addStretch()


# ══════════════════════════════════════════════════════════════
#  LEFT PANEL  –  SCAN
# ══════════════════════════════════════════════════════════════
class ScanPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(320)
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(10)

        tc = QFrame()
        tc.setStyleSheet(
            f"QFrame{{background:{BG2};border:1px solid {BORDER};border-radius:10px;}}")
        tv = QVBoxLayout(tc); tv.setContentsMargins(14,10,14,10); tv.setSpacing(2)
        tv.addWidget(mk_label("1.  SCAN YOUR FACE", 12, bold=True))
        root.addWidget(tc)

        face_frame = QFrame()
        face_frame.setStyleSheet(
            f"QFrame{{background:{BG3};border:1px solid {BORDER};border-radius:12px;}}")
        fv = QVBoxLayout(face_frame); fv.setContentsMargins(8,8,8,8); fv.setSpacing(0)
        self.face_lbl = QLabel()
        self.face_lbl.setFixedSize(300,330); self.face_lbl.setAlignment(Qt.AlignCenter)
        self.face_lbl.setStyleSheet(
            f"background:{BG3};border-radius:8px;color:{TEXTD};font-size:12px;border:none;")
        self.face_lbl.setText("Drop or select\na photo here")
        fv.addWidget(self.face_lbl)
        root.addWidget(face_frame)

        self.btn_up = self._mk_btn("⬆  UPLOAD PHOTO", ACCENT2, ACCENT)
        self.btn_an = self._mk_btn("◉  ANALYSE FACE",  ACCENT3, ACCENT2)
        self.btn_an.setEnabled(False)
        root.addWidget(self.btn_up); root.addWidget(self.btn_an)

        self.prog = QProgressBar()
        self.prog.setFixedHeight(5); self.prog.setRange(0,100)
        self.prog.setValue(0); self.prog.setTextVisible(False)
        self.prog.setStyleSheet(f"""
            QProgressBar{{background:{BORDER};border-radius:2px;border:none;}}
            QProgressBar::chunk{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {ACCENT2},stop:1 {ACCENT});border-radius:2px;}}""")
        root.addWidget(self.prog)
        self.prog_lbl = mk_label("Ready", 10, color=TEXTD)
        root.addWidget(self.prog_lbl)
        root.addWidget(self._build_status())
        root.addStretch()

    def _mk_btn(self, text, c1, c2):
        b = QPushButton(text); b.setFixedHeight(42); b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet(f"""
            QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {c1},stop:1 {c2});
                color:#fff;border:none;border-radius:10px;
                font-size:11px;font-weight:800;letter-spacing:1.5px;}}
            QPushButton:disabled{{background:{BG3};color:{TEXTD};border:1px solid {BORDER};}}""")
        return b

    def _build_status(self):
        card = QFrame()
        card.setStyleSheet(
            f"QFrame{{background:{BG3};border:1px solid {BORDER};border-radius:10px;}}")
        v = QVBoxLayout(card); v.setContentsMargins(14,12,14,12); v.setSpacing(10)
        hdr = QLabel("DETECTION STATUS")
        hdr.setStyleSheet(
            f"color:{TEXTD};font-size:8px;font-weight:800;"
            f"letter-spacing:2px;background:transparent;")
        v.addWidget(hdr)
        self._dots = {}
        for k in ["Face Detected","Landmarks Detected","Skin Analysed","Face Shape Identified"]:
            row = QHBoxLayout(); row.setSpacing(10)
            dot = QLabel("○"); dot.setFixedWidth(18); dot.setAlignment(Qt.AlignCenter)
            dot.setStyleSheet(f"color:{TEXTD};font-size:15px;background:transparent;")
            txt = mk_label(k, 11, color=TEXTD)
            row.addWidget(dot); row.addWidget(txt); row.addStretch()
            v.addLayout(row)
            self._dots[k] = (dot, txt)
        return card

    def tick(self, key):
        if key in self._dots:
            dot, txt = self._dots[key]
            dot.setText("●")
            dot.setStyleSheet(f"color:{SUCCESS};font-size:15px;background:transparent;")
            txt.setStyleSheet(f"color:{TEXT};font-size:11px;font-weight:600;background:transparent;")

    def reset(self):
        for k,(dot,txt) in self._dots.items():
            dot.setText("○")
            dot.setStyleSheet(f"color:{TEXTD};font-size:15px;background:transparent;")
            txt.setStyleSheet(f"color:{TEXTD};font-size:11px;background:transparent;")
        self.prog.setValue(0); self.prog_lbl.setText("Ready")

    def show_img(self, pm):
        scaled = pm.scaled(300,330,Qt.KeepAspectRatio,Qt.SmoothTransformation)
        self.face_lbl.setPixmap(scaled); self.face_lbl.setAlignment(Qt.AlignCenter)

    def enable_scan(self, on):
        self.btn_an.setEnabled(on)


# ══════════════════════════════════════════════════════════════
#  MIDDLE PANEL  –  ANALYSIS RESULTS
# ══════════════════════════════════════════════════════════════
class AnalysisPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(260)
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(10)

        tc = QFrame()
        tc.setStyleSheet(
            f"QFrame{{background:{BG2};border:1px solid {BORDER};border-radius:10px;}}")
        tv = QVBoxLayout(tc); tv.setContentsMargins(14,10,14,10); tv.setSpacing(2)
        tv.addWidget(mk_label("2.  ANALYSIS RESULTS", 12, bold=True))
        root.addWidget(tc)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea{background:transparent;border:none;}
            QScrollBar:vertical{background:#111119;width:4px;border-radius:2px;}
            QScrollBar::handle:vertical{background:#252538;border-radius:2px;min-height:20px;}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}
        """)
        self.inner = QWidget(); self.inner.setStyleSheet("background:transparent;")
        self.cards_layout = QVBoxLayout(self.inner)
        self.cards_layout.setContentsMargins(0,0,4,0); self.cards_layout.setSpacing(10)
        self._placeholder = mk_label("Upload a photo\nto see results.",
            12, color=TEXTD, align=Qt.AlignCenter, wrap=True)
        self.cards_layout.addWidget(self._placeholder)
        self.cards_layout.addStretch()
        scroll.setWidget(self.inner)
        root.addWidget(scroll, 1)

    def _clear(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def _card(self, accent=ACCENT):
        f = QFrame()
        f.setStyleSheet(
            f"QFrame{{background:{BG3};"
            f"border:1px solid {BORDER};"
            f"border-left:3px solid {accent};"
            f"border-radius:10px;}}")
        v = QVBoxLayout(f); v.setContentsMargins(12,10,12,10); v.setSpacing(6)
        return f, v

    def populate(self, res):
        self._clear()
        ut  = res["undertone"];  uti = UNDERTONE_INFO[ut]
        fs  = res["face_shape"]; fst = FACE_TIPS.get(fs, {})
        es  = res["eye_shape"]
        con = res["contrast"]

        # SKIN TONE
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

        # FACE SHAPE
        c2, v2 = self._card(ACCENT2)
        v2.addWidget(section_label("Face Shape", ACCENT2))
        v2.addWidget(mk_label(fs.capitalize(), 13, bold=True))
        for d in fst.get("desc", []):
            row2 = QHBoxLayout(); row2.setSpacing(6)
            dot2 = QLabel("•"); dot2.setStyleSheet(
                f"color:{ACCENT2};font-size:12px;background:transparent;")
            row2.addWidget(dot2); row2.addWidget(mk_label(d, 10, color=TEXTD))
            row2.addStretch(); v2.addLayout(row2)
        self.cards_layout.addWidget(c2)

        # FEATURES
        c3, v3 = self._card(ACCENT3)
        v3.addWidget(section_label("Features", ACCENT3))
        for k, val in [("Eye Shape", es.capitalize()),
                       ("Jaw",       "Defined"),
                       ("Nose",      "Straight"),
                       ("Lips",      "Medium")]:
            row3 = QHBoxLayout(); row3.setSpacing(0)
            row3.addWidget(mk_label(k + ":", 10, color=TEXTD))
            row3.addSpacing(6)
            row3.addWidget(mk_label(val, 10, bold=True))
            row3.addStretch(); v3.addLayout(row3)
        self.cards_layout.addWidget(c3)

        # COLOR ANALYSIS
        c4, v4 = self._card(WARN)
        v4.addWidget(section_label("Color Analysis", WARN))
        v4.addWidget(mk_label("Best Colors", 10, color=TEXTD))
        sr = QHBoxLayout(); sr.setSpacing(6)
        for hx in uti["best"]: sr.addWidget(SwatchDot(hx, 22))
        sr.addStretch(); v4.addLayout(sr)
        self.cards_layout.addWidget(c4)

        # CONTRAST LEVEL
        c5, v5 = self._card(ACCENT)
        v5.addWidget(section_label("Contrast Level", ACCENT))
        v5.addWidget(mk_label(con.capitalize(), 11, bold=True))
        pb = QProgressBar(); pb.setFixedHeight(7)
        pb.setRange(0,3); pb.setValue({"low":1,"medium":2,"high":3}.get(con,2))
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
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(10)

        tc = QFrame()
        tc.setStyleSheet(
            f"QFrame{{background:{BG2};border:1px solid {BORDER};border-radius:10px;}}")
        tv = QVBoxLayout(tc); tv.setContentsMargins(14,10,14,10); tv.setSpacing(2)
        tv.addWidget(mk_label("3.  RECOMMENDATIONS", 12, bold=True))
        root.addWidget(tc)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea{background:transparent;border:none;}
            QScrollBar:vertical{background:#111119;width:4px;border-radius:2px;}
            QScrollBar::handle:vertical{background:#252538;border-radius:2px;min-height:20px;}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}
        """)
        self.inner = QWidget(); self.inner.setStyleSheet("background:transparent;")
        self.grid = QGridLayout(self.inner)
        self.grid.setContentsMargins(0,0,6,6); self.grid.setSpacing(10)
        self.grid.setColumnStretch(0,1); self.grid.setColumnStretch(1,1)
        self._ph = mk_label("Recommendations will appear\nafter analysis.",
            12, color=TEXTD, align=Qt.AlignCenter, wrap=True)
        self.grid.addWidget(self._ph, 0, 0, 1, 2, Qt.AlignCenter)
        scroll.setWidget(self.inner)
        root.addWidget(scroll, 1)

    def _clear(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def populate(self, res, recs):
        self._clear()
        fs = res["face_shape"]; ut = res["undertone"]
        ft = FACE_TIPS.get(fs, {})

        blocks = [
            ("Hairstyle",    recs["hairstyles"],   ft.get("hair",""),   ACCENT,  100, 118, 3),
            ("Beard Style",  recs["beard"],         ft.get("beard",""),  ACCENT2, 100, 118, 3),
            ("Outfit Colors",recs["colours"],       ft.get("color",""),  WARN,    100, 110, 3),
            ("Outfit Style", recs["outfit_style"],  ft.get("outfit",""), ACCENT3, 100, 110, 3),
            ("Accessories",  recs["accessories"],   "Minimal accessories – watch, ring, bracelet.", SUCCESS, 100, 100, 2),
        ]

        for i, (title, paths, caption, accent, iw, ih, show) in enumerate(blocks):
            r, col = divmod(i, 2)
            self.grid.addWidget(RecBlock(title, paths, caption, accent, iw, ih, show), r, col)

        # bottom strip
        bot = QFrame()
        bot.setStyleSheet(
            f"QFrame{{background:{BG3};border:1px solid {BORDER};border-radius:12px;}}")
        bh = QHBoxLayout(bot); bh.setContentsMargins(14,14,14,14); bh.setSpacing(14)

        for heading, tip in [
            ("Grooming Tips", GROOMING_TIPS.get(ut,"")),
            ("Style Tips",    STYLE_TIPS.get(ut,"")),
        ]:
            tf = QFrame()
            tf.setStyleSheet(
                f"QFrame{{background:{BG2};border:1px solid {BORDER};border-radius:8px;}}")
            tv = QVBoxLayout(tf); tv.setContentsMargins(12,10,12,10); tv.setSpacing(5)
            tv.addWidget(section_label(heading, TEXTM))
            tl = QLabel(tip); tl.setWordWrap(True)
            tl.setStyleSheet(f"color:{TEXTM};font-size:10px;background:transparent;")
            tv.addWidget(tl)
            bh.addWidget(tf, 1)

        sf = QFrame()
        sf.setStyleSheet(
            f"QFrame{{background:{BG2};border:1px solid {ACCENT2};border-radius:8px;}}")
        sv = QVBoxLayout(sf); sv.setContentsMargins(12,12,12,12); sv.setSpacing(6)
        sv.addWidget(section_label("Your Style Score", ACCENT2))
        sv.addWidget(ScoreRing(90, 70), 0, Qt.AlignHCenter)
        sv.addWidget(mk_label("Sharp, confident style!\nFollow the recommendations.",
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
        self.setWindowTitle("AI Style Recommender – Male")
        self.setMinimumSize(1200,800); self.resize(1440,900)
        self._img_path = None
        self._engine   = FaceEngine()
        self._loader   = DatasetLoader(DATASET_ROOT)
        self._apply_style(); self._build()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QMainWindow,QWidget{{
                background:{BG};color:{TEXT};
                font-family:'Segoe UI','Inter','Helvetica Neue',Arial,sans-serif;}}
            QScrollBar:vertical{{background:{BG2};width:4px;border-radius:2px;margin:0;}}
            QScrollBar::handle:vertical{{background:{BORDER};border-radius:2px;min-height:20px;}}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;border:none;}}
        """)

    def _build(self):
        cw = QWidget(); self.setCentralWidget(cw)
        rv = QVBoxLayout(cw); rv.setContentsMargins(0,0,0,0); rv.setSpacing(0)
        rv.addWidget(Header())
        body = QWidget()
        bh = QHBoxLayout(body); bh.setContentsMargins(14,14,14,14); bh.setSpacing(12)
        self.sp = ScanPanel()
        self.ap = AnalysisPanel()
        self.rp = RecPanel()
        self.sp.btn_up.clicked.connect(self._upload)
        self.sp.btn_an.clicked.connect(self._analyse)
        bh.addWidget(self.sp); bh.addWidget(self.ap); bh.addWidget(self.rp, 1)
        rv.addWidget(body, 1)
        rv.addWidget(Footer())

    def _upload(self):
        path, _ = QFileDialog.getOpenFileName(
            self,"Select Photo","","Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if not path: return
        self._img_path = path
        self.sp.show_img(QPixmap(path))
        self.sp.enable_scan(True); self.sp.reset()
        self.sp.prog_lbl.setText("Photo loaded – ready to analyse.")

    def _analyse(self):
        if not self._img_path: return
        self.sp.btn_an.setEnabled(False); self.sp.btn_up.setEnabled(False)
        self.sp.reset()
        self._worker = Worker(self._img_path, self._engine, self._loader)
        self._worker.progress.connect(self._on_prog)
        self._worker.done.connect(self._on_done)
        self._worker.failed.connect(self._on_err)
        self._worker.start()

    def _on_prog(self, val, msg):
        self.sp.prog.setValue(val); self.sp.prog_lbl.setText(msg)
        if val >= 15: self.sp.tick("Face Detected")
        if val >= 45: self.sp.tick("Landmarks Detected")
        if val >= 65: self.sp.tick("Skin Analysed")
        if val >= 80: self.sp.tick("Face Shape Identified")

    def _on_done(self, res, recs):
        self.sp.prog.setValue(100); self.sp.prog_lbl.setText("✓  Analysis complete!")
        for k in ["Face Detected","Landmarks Detected","Skin Analysed","Face Shape Identified"]:
            self.sp.tick(k)
        self.sp.show_img(cv2px(res["annotated"]))
        self.ap.populate(res); self.rp.populate(res, recs)
        self.sp.btn_an.setEnabled(True); self.sp.btn_up.setEnabled(True)
        self.sp.enable_scan(True)

    def _on_err(self, msg):
        self.sp.prog_lbl.setText(f"⚠  {msg}")
        self.sp.prog.setValue(0)
        self.sp.btn_an.setEnabled(True); self.sp.btn_up.setEnabled(True)
        self.sp.enable_scan(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("AI Style Recommender – Male")
    w = MainWindow(); w.show()
    sys.exit(app.exec_())