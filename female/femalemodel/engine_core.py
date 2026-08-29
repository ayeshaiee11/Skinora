"""Shared OpenCV + MediaPipe face analysis engine for FormaFace."""

import math
from pathlib import Path

import cv2
import numpy as np
import mediapipe as mp

DATASET_ROOT = Path(__file__).parent / "dataset" / "female"

UNDERTONE_INFO = {
    "cool":   dict(label="Cool / Light",        undertone="Cool · Pink-Red",
                   swatch="#F2C9A8",
                   best=["#E8D5C4","#6A5ACD","#708090","#C71585","#2F4F4F","#B8860B"]),
    "light":  dict(label="Light / Fair",         undertone="Neutral · Balanced",
                   swatch="#FDDBB4",
                   best=["#DEB887","#228B22","#8B0000","#4169E1","#DAA520","#800080"]),
    "medium": dict(label="Light-Medium / Warm",  undertone="Warm · Golden-Olive",
                   swatch="#D2956A",
                   best=["#8B6914","#556B2F","#8B3A3A","#1C3A5E","#A0522D","#6B3A6B"]),
    "warm":   dict(label="Medium / Deep",        undertone="Warm · Rich Mahogany",
                   swatch="#A0674A",
                   best=["#5C3317","#2D5016","#7B2D00","#1A2744","#704214","#4A1942"]),
}

FACE_TIPS = {
    "oval":      dict(desc=["Balanced Proportions","Slightly Narrow Chin","Wider Forehead"],
                      specs="Most frames suit oval faces – aviators, wayfarers or cat-eye.",
                      hair="Soft layers, waves or loose updos suit you best.",
                      hijab="Draped, layered or side-pinned styles complement your face.",
                      outfit="Flowy silhouettes, structured blazers and minimal patterns.",
                      color="Earth tones, muted colors and warm shades look best on you."),
    "round":     dict(desc=["Full Cheeks","Soft Jawline","Similar Width & Length"],
                      specs="Angular, rectangular or geometric frames add definition.",
                      hair="Long layers, high ponytails, side parts lengthen the face.",
                      hijab="Tall styles, volume on top, avoid wide side draping.",
                      outfit="Vertical lines, V-necks and structured silhouettes.",
                      color="Cool, muted tones and deep shades create definition."),
    "heart":     dict(desc=["Wide Forehead","High Cheekbones","Narrow Chin"],
                      specs="Bottom-heavy or round frames balance a wide forehead.",
                      hair="Low ponytails, medium waves and chin-length bobs balance width.",
                      hijab="Wider at the bottom, side drapes to balance the forehead.",
                      outfit="A-line skirts, wide-leg trousers, detail at the hips.",
                      color="Soft pastels and warm neutrals flatter the complexion."),
    "square":    dict(desc=["Strong Angular Jaw","Broad Forehead","Defined Features"],
                      specs="Round or oval frames soften angular features.",
                      hair="Soft curls, layered cuts and side parts soften the jaw.",
                      hijab="Soft drapes, rounded styles to balance angular jaw.",
                      outfit="Wrap dresses, soft fabrics, curved necklines.",
                      color="Soft, warm hues and dusty tones complement squared features."),
    "rectangle": dict(desc=["Long Face","Strong Jaw","High Forehead"],
                      specs="Oversized or wide frames shorten the face's appearance.",
                      hair="Chin bobs, curtain bangs and waves add horizontal fullness.",
                      hijab="Side sweeps and wide draped styles add width.",
                      outfit="Horizontal stripes, wide belts, layered tops.",
                      color="Rich warm tones and warm neutrals work beautifully."),
    "diamond":   dict(desc=["Narrow Forehead & Chin","Wide Cheekbones","Angular"],
                      specs="Oval or rimless frames complement diamond faces.",
                      hair="Curtain bangs, side parts and volume on top add width.",
                      hijab="Jersey wrap or tied-back styles add forehead width.",
                      outfit="Off-shoulder, boat necks and statement necklines.",
                      color="Jewel tones and rich earthy hues suit diamond faces."),
    "triangle":  dict(desc=["Wide Jaw","Narrow Forehead","Strong Chin"],
                      specs="Cat-eye or top-heavy frames widen the upper face.",
                      hair="Volume at crown, curtain bangs to widen the forehead.",
                      hijab="Bonnet wraps or Malaysian shayla add forehead width.",
                      outfit="Detailed tops, peplum, shoulder emphasis.",
                      color="Light tones on top, darker tones on bottom balance shape."),
}

EYE_EYELINER = {
    "almond":    "Classic Wing – extend liner slightly past the outer corner for elongation.",
    "round":     "Elongated Cat-Eye – makes round eyes appear more almond-shaped.",
    "hooded":    "Thin Floated Wing – applied on upper lash line only, avoids heavy lower liner.",
    "monolid":   "Smudged Gradient – creates depth and dimension on monolid eyes.",
    "downturned":"Lifted Wing – outer corner wing visually lifts downturned eyes.",
    "upturned":  "Soft Cat-Eye – balances upturned eyes with a gentle lower wing.",
}

MAKEUP_TIPS = {
    "cool":   "Cool-toned pinks, berry lips, silver highlights & rosy blush.",
    "light":  "Warm neutrals, peachy blush, defined brows and nude lips.",
    "medium": "Bronze highlights, terracotta blush, warm nudes & copper shadow.",
    "warm":   "Rich bronzers, deep berries, golden highlights & warm browns.",
}

SKIN_TIPS = {
    "cool":   "Brightening Vitamin C serum. SPF 30+ daily. Focus on hydration & barrier care.",
    "light":  "Hydrate & protect. SPF daily, gentle exfoliation weekly. Hyaluronic acid serum.",
    "medium": "Niacinamide for even tone. Retinol at night. Mineral SPF 50+ essential.",
    "warm":   "Antioxidant serums, glycolic acid & rich moisturisers. SPF every day.",
}


class DatasetLoader:
    UNDERTONES = ["cool", "light", "medium", "warm"]

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
            length_diff = abs(len(a) - len(b))
            return matches - length_diff

        if len(tl) <= 12 and ' ' not in tl:
            best = max(children, key=lambda c: similarity(c.name, tl), default=None)
            if best and similarity(best.name, tl) >= max(3, len(tl) - 2):
                return best
        return None

    def _resolve(self, *parts):
        p = self.root
        for part in parts:
            if part is None:
                return None
            tl = part.lower().strip()
            try:
                children = [c for c in p.iterdir() if c.is_dir()]
            except Exception:
                return None
            match = next((c for c in children if c.name.lower() == tl), None)
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
            key=lambda x: x.name
        )
        return imgs if count is None else imgs[:count]

    def accessories(self, face_shape, count=2):
        return self._images(self._resolve("accessories", face_shape), count)

    def colours(self, face_shape, undertone, count=3):
        return self._images(self._resolve("colours", face_shape, undertone), count)

    def eye_shape_imgs(self, eye_shape, count=3):
        return self._images(self._resolve("eye shapes", eye_shape), count)

    def eyeliner(self, eye_shape, count=1):
        return self._images(self._resolve("eyeliner", eye_shape), count)

    def face_shape_imgs(self, face_shape, count=2):
        return self._images(self._resolve("face shapes", face_shape), count)

    def hairstyles(self, face_shape, count=3):
        return self._images(self._resolve("hairstyles", face_shape), count)

    def hijaab(self, face_shape, count=3):
        return self._images(self._resolve("hijaab style", face_shape), count)

    def outfit_styles(self, face_shape, undertone, count=3):
        return self._images(self._resolve("outfit styles", face_shape, undertone), count)

    def debug_paths(self, face_shape, undertone, eye_shape):
        checks = [
            ("accessories",   self._resolve("accessories",   face_shape)),
            ("colours",       self._resolve("colours",       face_shape, undertone)),
            ("eye shapes",    self._resolve("eye shapes",    eye_shape)),
            ("eyeliner",      self._resolve("eyeliner",      eye_shape)),
            ("face shapes",   self._resolve("face shapes",   face_shape)),
            ("hairstyles",    self._resolve("hairstyles",    face_shape)),
            ("hijaab style",  self._resolve("hijaab style",  face_shape)),
            ("outfit styles", self._resolve("outfit styles", face_shape, undertone)),
        ]
        for name, path in checks:
            status = "✓" if path and path.exists() else "✗ NOT FOUND"
            print(f"  {status}  {name:20s}  →  {path}")


class FaceEngine:
    def __init__(self):
        self.fm = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True, max_num_faces=1,
            refine_landmarks=True, min_detection_confidence=0.5)

    def _pt(self, lms, i, w, h):
        l = lms[i]
        return (int(l.x * w), int(l.y * h))

    def _d(self, a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def _face_shape(self, lms, w, h):
        jaw_l   = self._pt(lms, 234, w, h); jaw_r  = self._pt(lms, 454, w, h)
        top     = self._pt(lms, 10, w, h);  bot    = self._pt(lms, 152, w, h)
        ch_l    = self._pt(lms, 93, w, h);  ch_r   = self._pt(lms, 323, w, h)
        fore_l  = self._pt(lms, 54, w, h);  fore_r = self._pt(lms, 284, w, h)
        chin_l  = self._pt(lms, 172, w, h); chin_r = self._pt(lms, 397, w, h)

        jaw_w   = self._d(jaw_l, jaw_r)
        face_h  = self._d(top, bot)
        cheek_w = self._d(ch_l, ch_r)
        fore_w  = self._d(fore_l, fore_r)
        chin_w  = self._d(chin_l, chin_r)

        ratio = face_h / max(jaw_w, 1)

        if ratio > 1.80:                        return "rectangle"
        if cheek_w > jaw_w * 1.20 and ratio < 1.5: return "diamond"
        if chin_w  > fore_w * 1.10:              return "triangle"
        if ratio   < 1.20:                      return "round"
        if fore_w  > chin_w * 1.20:              return "heart"
        if 1.30    < ratio < 1.65:              return "oval"
        return "square"

    def _eye_shape(self, lms, w, h):
        li = self._pt(lms, 133, w, h); lo = self._pt(lms, 33, w, h)
        lt = self._pt(lms, 159, w, h); lb = self._pt(lms, 145, w, h)
        ew = self._d(li, lo); eh = self._d(lt, lb)
        ratio = eh / max(ew, 1)
        tilt  = lo[1] - li[1]
        if ratio > 0.36:               return "round"
        if tilt  >  4:                 return "downturned"
        if tilt  < -4:                 return "upturned"
        if ew    < 55:                 return "monolid"
        crease = self._pt(lms, 160, w, h)
        if abs(crease[1] - lt[1]) < 4: return "hooded"
        return "almond"

    def _undertone(self, bgr, lms, w, h):
        pts  = [self._pt(lms, i, w, h) for i in [205, 425, 234, 454]]
        vals = []
        for (x, y) in pts:
            roi = bgr[max(0, y - 12):y + 12, max(0, x - 12):x + 12]
            if roi.size:
                vals.append(roi.reshape(-1, 3).mean(0))
        if not vals:
            return "medium"
        r, g, b = np.mean(vals, axis=0)[[2, 1, 0]]
        bright = (r + g + b) / 3
        warm_idx = r - b

        if   bright > 195: return "cool"   if warm_idx <  20 else "light"
        elif bright > 155: return "light"  if warm_idx <  30 else "medium"
        elif bright > 115: return "medium"
        else:               return "warm"

    def _contrast(self, bgr, lms, w, h):
        s  = self._pt(lms, 234, w, h)
        e  = self._pt(lms, 33, w, h)
        sr = cv2.cvtColor(bgr[max(0, s[1] - 10):s[1] + 10, max(0, s[0] - 10):s[0] + 10], cv2.COLOR_BGR2GRAY)
        er = cv2.cvtColor(bgr[max(0, e[1] - 6): e[1] + 6,  max(0, e[0] - 6): e[0] + 6],  cv2.COLOR_BGR2GRAY)
        if not sr.size or not er.size:
            return "medium"
        d = abs(float(sr.mean()) - float(er.mean()))
        return "high" if d > 55 else ("medium" if d > 25 else "low")

    def _overlay(self, bgr, lms, w, h):
        out = bgr.copy()
        jaw = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379,
               378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234,
               127, 162, 21, 54, 103, 67, 109, 10]
        for i in range(len(jaw) - 1):
            cv2.line(out, self._pt(lms, jaw[i], w, h),
                         self._pt(lms, jaw[i + 1], w, h), (0, 212, 255), 1)
        for idx in [10, 152, 234, 454, 93, 323, 33, 133, 159, 145,
                    362, 263, 386, 374, 1, 61, 291, 17]:
            cv2.circle(out, self._pt(lms, idx, w, h), 3, (0, 212, 255), -1)
        return out

    def analyse(self, path):
        bgr = cv2.imread(str(path))
        if bgr is None:
            return {"error": "Cannot read image."}
        h, w = bgr.shape[:2]
        res  = self.fm.process(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        if not res.multi_face_landmarks:
            return {"error": "No face detected – please use a clear front-facing photo."}
        lms = res.multi_face_landmarks[0].landmark
        return dict(
            face_shape=self._face_shape(lms, w, h),
            eye_shape=self._eye_shape(lms, w, h),
            undertone=self._undertone(bgr, lms, w, h),
            contrast=self._contrast(bgr, lms, w, h),
            annotated=self._overlay(bgr, lms, w, h),
            error=None
        )
