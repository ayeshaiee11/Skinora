"""FormaFace analysis engine — shared core extracted from malemodel."""

import base64
import math
from pathlib import Path
from urllib.parse import quote

import cv2
import mediapipe as mp
import numpy as np

DATASET_ROOT = Path(__file__).resolve().parent.parent / "dataset"

UNDERTONE_INFO = {
    "cool": dict(
        label="Cool / Light",
        undertone="Cool · Pink-Red",
        swatch="#F2C9A8",
        best=["#E8D5C4", "#6A5ACD", "#708090", "#C71585", "#2F4F4F", "#B8860B"],
    ),
    "light": dict(
        label="Light / Fair",
        undertone="Neutral · Balanced",
        swatch="#FDDBB4",
        best=["#DEB887", "#228B22", "#8B0000", "#4169E1", "#DAA520", "#800080"],
    ),
    "medium": dict(
        label="Light-Medium / Warm",
        undertone="Warm · Golden-Olive",
        swatch="#D2956A",
        best=["#8B6914", "#556B2F", "#8B3A3A", "#1C3A5E", "#A0522D", "#6B3A6B"],
    ),
    "warm": dict(
        label="Medium / Deep",
        undertone="Warm · Rich Mahogany",
        swatch="#A0674A",
        best=["#5C3317", "#2D5016", "#7B2D00", "#1A2744", "#704214", "#4A1942"],
    ),
}

FACE_TIPS = {
    "oval": dict(
        desc=["Balanced Proportions", "Slightly Narrow Chin", "Wider Forehead"],
        hair="Ivy league, classic side part or messy medium – most styles suit oval.",
        beard="Most beard styles work – full beard, goatee or light stubble all complement.",
        outfit="Slim-fit shirts, structured jackets and minimal patterns.",
        color="Earth tones, navy and warm neutrals look best on you.",
    ),
    "round": dict(
        desc=["Full Cheeks", "Soft Jawline", "Similar Width & Length"],
        hair="High fade, pompadour or quiff – add height to elongate the face.",
        beard="Angular beard with defined lines to add length and definition.",
        outfit="Vertical stripes, V-necks and slim-fit silhouettes.",
        color="Deep, cool tones and dark shades create definition.",
    ),
    "heart": dict(
        desc=["Wide Forehead", "High Cheekbones", "Narrow Chin"],
        hair="Side-swept, textured crop or ivy league to reduce forehead width.",
        beard="Fuller beard on the chin to balance the wide forehead.",
        outfit="Wider collars, horizontal chest detail, layered tops.",
        color="Soft pastels and warm neutrals flatter the complexion.",
    ),
    "square": dict(
        desc=["Strong Angular Jaw", "Broad Forehead", "Defined Features"],
        hair="Curly top, slick back or longer top to soften angular features.",
        beard="Short stubble or rounded beard to soften the strong jawline.",
        outfit="Round-neck tees, bomber jackets and soft fabrics.",
        color="Soft warm hues and dusty tones complement squared features.",
    ),
    "rectangle": dict(
        desc=["Long Face", "Strong Jaw", "High Forehead"],
        hair="French crop, textured fringe or curtain bangs to add horizontal width.",
        beard="Full beard or wide-set stubble to add width to the face.",
        outfit="Horizontal stripes, wide lapels, layered looks.",
        color="Rich warm tones and warm neutrals work beautifully.",
    ),
    "diamond": dict(
        desc=["Narrow Forehead & Chin", "Wide Cheekbones", "Angular"],
        hair="Curtain bangs, side parts and volume on top add forehead width.",
        beard="Goatee or chin-strap to add definition to the narrow chin.",
        outfit="Off-shoulder, boat necks and statement necklines.",
        color="Jewel tones and rich earthy hues suit diamond faces.",
    ),
    "triangle": dict(
        desc=["Wide Jaw", "Narrow Forehead", "Strong Chin"],
        hair="Pompadour, quiff or volume at crown to widen the forehead.",
        beard="Light stubble only – heavy beard emphasises the wide jaw.",
        outfit="Detailed tops, shoulder emphasis, peplum-style layering.",
        color="Light tones on top, darker tones on bottom balance the shape.",
    ),
}

GROOMING_TIPS = {
    "cool": "Daily moisturiser with SPF. Use a gentle face wash and toner for oily zones.",
    "light": "Hydrate & protect. SPF daily, gentle exfoliation weekly. Hyaluronic acid serum.",
    "medium": "Niacinamide for even tone. Retinol at night. Mineral SPF 50+ essential.",
    "warm": "Antioxidant serums, glycolic acid & rich moisturisers. SPF every day.",
}

STYLE_TIPS = {
    "cool": "Monochrome outfits, clean tailoring and cool-toned accessories suit you.",
    "light": "Neutral palettes, earthy tones and well-fitted basics elevate your look.",
    "medium": "Warm earthy tones, structured casual wear and leather accessories.",
    "warm": "Deep jewel tones, rich fabrics and bold accessories define your style.",
}


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

        if len(tl) <= 12 and " " not in tl:
            best = max(children, key=lambda c: similarity(c.name, tl), default=None)
            if best and similarity(best.name, tl) >= max(3, len(tl) - 2):
                return best
        return None

    def _resolve(self, *parts):
        p = self.root
        for part in parts:
            if part is None:
                return None
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
            [
                f
                for f in folder.iterdir()
                if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg")
            ],
            key=lambda x: x.name,
        )
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


class FaceEngine:
    def __init__(self):
        self.fm = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
        )

    def _pt(self, lms, i, w, h):
        l = lms[i]
        return (int(l.x * w), int(l.y * h))

    def _d(self, a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def _face_shape(self, lms, w, h):
        jaw_l = self._pt(lms, 234, w, h)
        jaw_r = self._pt(lms, 454, w, h)
        top = self._pt(lms, 10, w, h)
        bot = self._pt(lms, 152, w, h)
        ch_l = self._pt(lms, 93, w, h)
        ch_r = self._pt(lms, 323, w, h)
        fore_l = self._pt(lms, 54, w, h)
        fore_r = self._pt(lms, 284, w, h)
        chin_l = self._pt(lms, 172, w, h)
        chin_r = self._pt(lms, 397, w, h)
        jaw_w = self._d(jaw_l, jaw_r)
        face_h = self._d(top, bot)
        cheek_w = self._d(ch_l, ch_r)
        fore_w = self._d(fore_l, fore_r)
        chin_w = self._d(chin_l, chin_r)
        ratio = face_h / max(jaw_w, 1)
        if ratio > 1.80:
            return "rectangle"
        if cheek_w > jaw_w * 1.20 and ratio < 1.5:
            return "diamond"
        if chin_w > fore_w * 1.10:
            return "triangle"
        if ratio < 1.20:
            return "round"
        if fore_w > chin_w * 1.20:
            return "heart"
        if 1.30 < ratio < 1.65:
            return "oval"
        return "square"

    def _eye_shape(self, lms, w, h):
        li = self._pt(lms, 133, w, h)
        lo = self._pt(lms, 33, w, h)
        lt = self._pt(lms, 159, w, h)
        lb = self._pt(lms, 145, w, h)
        ew = self._d(li, lo)
        eh = self._d(lt, lb)
        ratio = eh / max(ew, 1)
        tilt = lo[1] - li[1]
        if ratio > 0.36:
            return "round"
        if tilt > 4:
            return "downturned"
        if tilt < -4:
            return "upturned"
        if ew < 55:
            return "monolid"
        crease = self._pt(lms, 160, w, h)
        if abs(crease[1] - lt[1]) < 4:
            return "hooded"
        return "almond"

    def _undertone(self, bgr, lms, w, h):
        pts = [self._pt(lms, i, w, h) for i in [205, 425, 234, 454]]
        vals = []
        for (x, y) in pts:
            roi = bgr[max(0, y - 12) : y + 12, max(0, x - 12) : x + 12]
            if roi.size:
                vals.append(roi.reshape(-1, 3).mean(0))
        if not vals:
            return "medium"
        r, g, b = np.mean(vals, axis=0)[[2, 1, 0]]
        bright = (r + g + b) / 3
        warm_idx = r - b
        if bright > 195:
            return "cool" if warm_idx < 20 else "light"
        if bright > 155:
            return "light" if warm_idx < 30 else "medium"
        if bright > 115:
            return "medium"
        return "warm"

    def _contrast(self, bgr, lms, w, h):
        s = self._pt(lms, 234, w, h)
        e = self._pt(lms, 33, w, h)
        sr = cv2.cvtColor(
            bgr[max(0, s[1] - 10) : s[1] + 10, max(0, s[0] - 10) : s[0] + 10],
            cv2.COLOR_BGR2GRAY,
        )
        er = cv2.cvtColor(
            bgr[max(0, e[1] - 6) : e[1] + 6, max(0, e[0] - 6) : e[0] + 6],
            cv2.COLOR_BGR2GRAY,
        )
        if not sr.size or not er.size:
            return "medium"
        d = abs(float(sr.mean()) - float(er.mean()))
        return "high" if d > 55 else ("medium" if d > 25 else "low")

    def _overlay(self, bgr, lms, w, h):
        out = bgr.copy()
        jaw = [
            10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379,
            378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234,
            127, 162, 21, 54, 103, 67, 109, 10,
        ]
        for i in range(len(jaw) - 1):
            cv2.line(
                out,
                self._pt(lms, jaw[i], w, h),
                self._pt(lms, jaw[i + 1], w, h),
                (0, 212, 255),
                1,
            )
        for idx in [10, 152, 234, 454, 93, 323, 33, 133, 159, 145, 362, 263, 386, 374, 1, 61, 291, 17]:
            cv2.circle(out, self._pt(lms, idx, w, h), 3, (0, 212, 255), -1)
        return out

    def analyse_bgr(self, bgr):
        if bgr is None:
            return {"error": "Cannot read image."}
        h, w = bgr.shape[:2]
        res = self.fm.process(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        if not res.multi_face_landmarks:
            return {"error": "No face detected – please use a clear front-facing photo."}
        lms = res.multi_face_landmarks[0].landmark
        return dict(
            face_shape=self._face_shape(lms, w, h),
            eye_shape=self._eye_shape(lms, w, h),
            undertone=self._undertone(bgr, lms, w, h),
            contrast=self._contrast(bgr, lms, w, h),
            annotated=self._overlay(bgr, lms, w, h),
            error=None,
        )

    def analyse_bytes(self, data: bytes):
        arr = np.frombuffer(data, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return self.analyse_bgr(bgr)

    def analyse(self, path):
        bgr = cv2.imread(str(path))
        return self.analyse_bgr(bgr)


def bgr_to_base64_jpeg(bgr, quality=85):
    ok, buf = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        return None
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")


def path_to_url(path: Path, dataset_root: Path) -> str:
    rel = path.relative_to(dataset_root).as_posix()
    parts = rel.split("/")
    return "/dataset/" + "/".join(quote(p) for p in parts)


def build_recommendations(loader: DatasetLoader, face_shape: str, undertone: str):
    return dict(
        hairstyles=[path_to_url(p, loader.root) for p in loader.hairstyles(face_shape, 3)],
        beard=[path_to_url(p, loader.root) for p in loader.beard(face_shape, 3)],
        outfit_style=[path_to_url(p, loader.root) for p in loader.outfit_styles(face_shape, undertone, 3)],
        colours=[path_to_url(p, loader.root) for p in loader.colours(face_shape, undertone, 3)],
        accessories=[path_to_url(p, loader.root) for p in loader.accessories(face_shape, 2)],
    )


def build_analysis_response(engine: FaceEngine, loader: DatasetLoader, data: bytes):
    result = engine.analyse_bytes(data)
    if result.get("error"):
        return {"ok": False, "error": result["error"]}

    fs = result["face_shape"]
    ut = result["undertone"]
    annotated = result.pop("annotated")

    face_info = FACE_TIPS.get(fs, {})
    undertone_info = UNDERTONE_INFO.get(ut, {})

    return {
        "ok": True,
        "face_shape": fs,
        "eye_shape": result["eye_shape"],
        "undertone": ut,
        "contrast": result["contrast"],
        "annotated_image": bgr_to_base64_jpeg(annotated),
        "undertone_info": undertone_info,
        "tips": {
            "traits": face_info.get("desc", []),
            "hair": face_info.get("hair", ""),
            "beard": face_info.get("beard", ""),
            "outfit": face_info.get("outfit", ""),
            "color": face_info.get("color", ""),
            "grooming": GROOMING_TIPS.get(ut, ""),
            "style": STYLE_TIPS.get(ut, ""),
        },
        "recommendations": build_recommendations(loader, fs, ut),
    }
