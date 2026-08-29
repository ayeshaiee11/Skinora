"""
Skinora — Standalone Webcam App
================================
Run: python skinora_webcam.py

Requirements:
    pip install opencv-python numpy scipy

Controls:
    SPACE  — Capture & analyse current frame
    R      — Reset / clear results
    Q      — Quit
"""

import math
import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Colour / analysis data
# ---------------------------------------------------------------------------

ITA_SKIN_TYPES = [
    (55,  "Very Light",  (180, 219, 253)),   # BGR tuples for OpenCV drawing
    (41,  "Light",       (138, 193, 245)),
    (28,  "Intermediate",(107, 147, 212)),
    (10,  "Tan",         ( 74, 120, 192)),
    (-30, "Brown",       ( 36,  85, 141)),
    (-90, "Dark",        ( 18,  41,  74)),
]

UNDERTONE_PALETTE = {
    "Warm":    ["Golden/Amber", "Bronze", "Terracotta", "Peach", "Copper"],
    "Cool":    ["Rose", "Mauve", "Lilac", "Berry", "Burgundy"],
    "Neutral": ["Nude", "Taupe", "Warm Beige", "Dusty Rose", "Caramel"],
}

EYELINER_STYLES = {
    "Almond":    ("Classic Wing",        "Thin flick along lash line, small wing."),
    "Round":     ("Tight-line + Wing",   "Line upper waterline; short wing lifts."),
    "Monolid":   ("Bold Graphic",        "Thick line; skip inner corner."),
    "Hooded":    ("Invisible Liner",     "Line only the lash line; no flick."),
    "Upturned":  ("Extended Cat Eye",    "Exaggerate the natural lift."),
    "Downturned":("Lifted Wing",         "Wing upward to counterbalance droop."),
    "Unknown":   ("Soft Pencil Line",    "Gentle smudged pencil for any shape."),
}

MAKEUP_TIPS = {
    "Very Light":   "Use cool-toned blush (rose, mauve) and light-coverage foundation.",
    "Light":        "Peachy blush and golden highlighter flatter your tone.",
    "Intermediate": "Warm bronzers and terracotta lip colours are your best friends.",
    "Tan":          "Rich berry lips and copper eyeshadow make your skin glow.",
    "Brown":        "Deep plums, burnt oranges, and gold shimmer enhance your depth.",
    "Dark":         "Bold jewel tones and metallic highlighters look stunning.",
}

HAIRSTYLE_TIPS = {
    "Oval":    ["Suits almost any style", "Try beach waves or a sleek bun"],
    "Round":   ["Add height on top", "Long layers elongate the face"],
    "Square":  ["Soft waves soften angles", "Side parts work well"],
    "Heart":   ["Volume at jaw level", "Chin-length bobs balance forehead"],
    "Oblong":  ["Wide/side-swept bangs add width", "Avoid extra-long straight hair"],
}

FRAMES_TIPS = {
    "Oval":    "Aviators, wayfarers — most shapes work.",
    "Round":   "Angular or rectangular frames add definition.",
    "Square":  "Round or oval frames soften the jaw.",
    "Heart":   "Bottom-heavy frames balance a wide forehead.",
    "Oblong":  "Oversized or wide frames add width.",
}

# ---------------------------------------------------------------------------
# OpenCV cascades
# ---------------------------------------------------------------------------

FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
EYE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_eye.xml"
)

# ---------------------------------------------------------------------------
# Colour maths
# ---------------------------------------------------------------------------

def rgb_to_lab(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
    g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
    b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92
    X = r * 0.4124 + g * 0.3576 + b * 0.1805
    Y = r * 0.2126 + g * 0.7152 + b * 0.0722
    Z = r * 0.0193 + g * 0.1192 + b * 0.9505
    X, Y, Z = X / 0.95047, Y / 1.00000, Z / 1.08883
    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    L = 116 * f(Y) - 16
    a = 500 * (f(X) - f(Y))
    b_ = 200 * (f(Y) - f(Z))
    return L, a, b_


def ita_angle(L, b_):
    return math.degrees(math.atan((L - 50) / b_)) if b_ != 0 else 90.0


def skin_type_from_ita(angle):
    for threshold, name, bgr in ITA_SKIN_TYPES:
        if angle > threshold:
            return name, bgr
    return "Dark", (18, 41, 74)


def undertone_from_lab(a, b_):
    if a > 12 and b_ > 12:
        return "Warm"
    elif a < 8:
        return "Cool"
    return "Neutral"


# ---------------------------------------------------------------------------
# CV analysis helpers
# ---------------------------------------------------------------------------

def extract_skin_color(face_roi_bgr):
    h, w = face_roi_bgr.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.ellipse(mask, (w // 2, h // 6),      (w // 5, h // 8), 0, 0, 360, 255, -1)
    cv2.ellipse(mask, (w // 6, h // 2),      (w // 8, h // 8), 0, 0, 360, 255, -1)
    cv2.ellipse(mask, (5 * w // 6, h // 2),  (w // 8, h // 8), 0, 0, 360, 255, -1)
    pixels = face_roi_bgr[mask == 255].reshape(-1, 3).astype(np.float32)
    if len(pixels) == 0:
        return None
    k = min(3, len(pixels))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    dominant_idx = np.bincount(labels.flatten()).argmax()
    b, g, r = centers[dominant_idx]
    return int(b), int(g), int(r)


def estimate_face_shape(face_roi_gray):
    h, w = face_roi_gray.shape
    aspect = h / (w + 1e-6)
    if aspect > 1.6:
        return "Oblong", ["Long vertical length", "Narrow width", "Angular jaw"]
    elif aspect > 1.35:
        return "Oval",   ["Balanced proportions", "Slightly wider cheekbones", "Gentle jaw taper"]
    elif aspect > 1.1:
        return "Round",  ["Equal width and length", "Soft curves", "Full cheeks"]
    elif aspect > 0.95:
        return "Square", ["Strong jawline", "Wide forehead", "Equal proportions"]
    else:
        return "Heart",  ["Wide forehead", "Narrow chin", "High cheekbones"]


def estimate_eye_shape(face_roi_gray, face_w):
    eyes = EYE_CASCADE.detectMultiScale(face_roi_gray, scaleFactor=1.1, minNeighbors=5)
    if len(eyes) == 0:
        return "Unknown"
    eye_w_avg = np.mean([e[2] for e in eyes])
    ratio = eye_w_avg / (face_w + 1e-6)
    if ratio > 0.28:
        return "Round"
    elif ratio > 0.22:
        return "Almond"
    elif ratio > 0.16:
        return "Monolid"
    else:
        return "Hooded"


def analyze_frame(frame):
    """Returns a dict of results or None if no face found."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = FACE_CASCADE.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
    )
    if len(faces) == 0:
        return None

    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    x, y, w, h = faces[0]
    face_roi_bgr  = frame[y:y+h, x:x+w]
    face_roi_gray = gray[y:y+h, x:x+w]

    result = {"bbox": (x, y, w, h)}

    skin_bgr = extract_skin_color(face_roi_bgr)
    if skin_bgr:
        b, g, r = skin_bgr
        L, a, b_ = rgb_to_lab(r, g, b)
        angle = ita_angle(L, b_)
        skin_name, skin_color_bgr = skin_type_from_ita(angle)
        undertone = undertone_from_lab(a, b_)
        result["skin_name"]    = skin_name
        result["skin_bgr"]     = (b, g, r)          # extracted pixel colour
        result["skin_dot_bgr"] = skin_color_bgr      # ITA reference colour
        result["undertone"]    = undertone
        result["makeup_tip"]   = MAKEUP_TIPS.get(skin_name, "")
        result["palette"]      = UNDERTONE_PALETTE.get(undertone, [])
    else:
        result["skin_name"]    = "Unknown"
        result["undertone"]    = "Unknown"
        result["makeup_tip"]   = ""
        result["palette"]      = []

    shape, props = estimate_face_shape(face_roi_gray)
    result["face_shape"]  = shape
    result["face_props"]  = props
    result["hairstyle"]   = HAIRSTYLE_TIPS.get(shape, ["Consult a stylist for your shape"])
    result["frames"]      = FRAMES_TIPS.get(shape, "Choose frames that contrast your face shape.")

    eye_shape = estimate_eye_shape(face_roi_gray, w)
    result["eye_shape"] = eye_shape
    el = EYELINER_STYLES.get(eye_shape, EYELINER_STYLES["Unknown"])
    result["eyeliner_name"] = el[0]
    result["eyeliner_desc"] = el[1]

    return result


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

PANEL_W      = 440
FONT         = cv2.FONT_HERSHEY_SIMPLEX
FONT_SMALL   = 0.45
FONT_MED     = 0.55
FONT_LARGE   = 0.7
WHITE        = (255, 255, 255)
BLACK        = (0, 0, 0)
ACCENT       = (180, 130, 80)   # warm teal-ish brand colour
ACCENT2      = (100, 200, 160)
BG_DARK      = (30, 30, 30)
BG_MID       = (50, 50, 50)
BG_PANEL     = (40, 40, 40)


def put_text(img, text, pos, font_scale=FONT_SMALL, color=WHITE,
             thickness=1, line_type=cv2.LINE_AA):
    cv2.putText(img, text, pos, FONT, font_scale, color, thickness, line_type)


def wrap_text(img, text, x, y, max_w, font_scale=FONT_SMALL,
              color=WHITE, thickness=1, line_gap=18):
    """Simple word-wrap."""
    words = text.split()
    line = ""
    cy = y
    for word in words:
        test = (line + " " + word).strip()
        (tw, _), _ = cv2.getTextSize(test, FONT, font_scale, thickness)
        if tw > max_w and line:
            put_text(img, line, (x, cy), font_scale, color, thickness)
            cy += line_gap
            line = word
        else:
            line = test
    if line:
        put_text(img, line, (x, cy), font_scale, color, thickness)
    return cy + line_gap


def draw_swatch(img, bgr, cx, cy, r=14):
    cv2.circle(img, (cx, cy), r + 2, WHITE, -1)
    cv2.circle(img, (cx, cy), r,     bgr,   -1)


def draw_panel(canvas, results):
    """Draw results panel on the right side of canvas."""
    H, W = canvas.shape[:2]
    panel_x = W - PANEL_W

    # Panel background
    canvas[:, panel_x:] = BG_PANEL

    y = 20
    # Title
    put_text(canvas, "SKINORA", (panel_x + 10, y), FONT_LARGE, ACCENT, 2)
    y += 28
    put_text(canvas, "Skin & Face Analysis", (panel_x + 10, y), FONT_SMALL, (180, 180, 180))
    y += 22
    cv2.line(canvas, (panel_x + 8, y), (W - 8, y), ACCENT, 1)
    y += 14

    if results is None:
        put_text(canvas, "No face detected.", (panel_x + 10, y), FONT_MED, (100, 100, 200))
        put_text(canvas, "Press SPACE to capture.", (panel_x + 10, y + 24), FONT_SMALL, (160, 160, 160))
        return

    mw = PANEL_W - 20   # max text width

    # ---- Skin Tone ----
    put_text(canvas, "SKIN TONE", (panel_x + 10, y), FONT_SMALL, ACCENT2, 1)
    y += 18
    skin_bgr     = results.get("skin_bgr",     (180, 180, 180))
    skin_dot_bgr = results.get("skin_dot_bgr", (180, 180, 180))
    draw_swatch(canvas, skin_bgr,     panel_x + 24, y + 6)
    draw_swatch(canvas, skin_dot_bgr, panel_x + 60, y + 6)
    put_text(canvas, results.get("skin_name", "?"),
             (panel_x + 90, y + 10), FONT_MED, WHITE, 1)
    y += 36
    put_text(canvas, f"Undertone: {results.get('undertone','?')}",
             (panel_x + 10, y), FONT_SMALL, (200, 200, 160))
    y += 20

    # Colour palette labels
    palette = results.get("palette", [])
    if palette:
        put_text(canvas, "Palette:", (panel_x + 10, y), FONT_SMALL, (160, 160, 160))
        y += 18
        for i, name in enumerate(palette[:5]):
            put_text(canvas, f"• {name}", (panel_x + 14, y), 0.4, (220, 220, 220))
            y += 15
    y += 4
    cv2.line(canvas, (panel_x + 8, y), (W - 8, y), BG_MID, 1)
    y += 10

    # ---- Face Shape ----
    put_text(canvas, "FACE SHAPE", (panel_x + 10, y), FONT_SMALL, ACCENT2)
    y += 18
    put_text(canvas, results.get("face_shape", "?"),
             (panel_x + 10, y), FONT_MED, WHITE, 1)
    y += 20
    for prop in results.get("face_props", [])[:3]:
        put_text(canvas, f"• {prop}", (panel_x + 12, y), 0.4, (200, 200, 200))
        y += 14
    y += 4
    cv2.line(canvas, (panel_x + 8, y), (W - 8, y), BG_MID, 1)
    y += 10

    # ---- Eye Shape + Eyeliner ----
    put_text(canvas, "EYE SHAPE & LINER", (panel_x + 10, y), FONT_SMALL, ACCENT2)
    y += 18
    put_text(canvas, f"Shape: {results.get('eye_shape','?')}",
             (panel_x + 10, y), FONT_MED, WHITE)
    y += 20
    put_text(canvas, results.get("eyeliner_name", ""), (panel_x + 10, y), FONT_SMALL, ACCENT)
    y += 16
    y = wrap_text(canvas, results.get("eyeliner_desc", ""),
                  panel_x + 12, y, mw - 10, 0.4, (200, 200, 200), line_gap=15)
    cv2.line(canvas, (panel_x + 8, y), (W - 8, y), BG_MID, 1)
    y += 10

    # ---- Makeup tip ----
    put_text(canvas, "MAKEUP TIP", (panel_x + 10, y), FONT_SMALL, ACCENT2)
    y += 18
    y = wrap_text(canvas, results.get("makeup_tip", ""), panel_x + 10, y,
                  mw, 0.4, (220, 220, 180), line_gap=15)
    cv2.line(canvas, (panel_x + 8, y), (W - 8, y), BG_MID, 1)
    y += 10

    # ---- Hairstyle ----
    put_text(canvas, "HAIRSTYLE TIPS", (panel_x + 10, y), FONT_SMALL, ACCENT2)
    y += 18
    for tip in results.get("hairstyle", [])[:2]:
        y = wrap_text(canvas, f"• {tip}", panel_x + 12, y, mw - 10, 0.4, (200, 200, 200), 15)

    # ---- Glasses ----
    put_text(canvas, "FRAMES", (panel_x + 10, y), FONT_SMALL, ACCENT2)
    y += 18
    y = wrap_text(canvas, results.get("frames", ""), panel_x + 10, y,
                  mw, 0.4, (200, 200, 200), 15)

    # ---- Controls reminder ----
    cv2.line(canvas, (panel_x + 8, H - 55), (W - 8, H - 55), BG_MID, 1)
    put_text(canvas, "SPACE=capture  R=reset  Q=quit",
             (panel_x + 10, H - 38), 0.4, (130, 130, 130))


def draw_live_overlay(frame, gray):
    """Draw face detection box on live feed."""
    faces = FACE_CASCADE.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
    )
    for (x, y, w, h) in faces:
        # Corner brackets instead of full rectangle — cleaner look
        tl, lw = 16, 2
        c = ACCENT
        cv2.line(frame, (x, y),       (x + tl, y),       c, lw)
        cv2.line(frame, (x, y),       (x, y + tl),        c, lw)
        cv2.line(frame, (x+w, y),     (x+w-tl, y),       c, lw)
        cv2.line(frame, (x+w, y),     (x+w, y+tl),       c, lw)
        cv2.line(frame, (x, y+h),     (x+tl, y+h),       c, lw)
        cv2.line(frame, (x, y+h),     (x, y+h-tl),       c, lw)
        cv2.line(frame, (x+w, y+h),   (x+w-tl, y+h),     c, lw)
        cv2.line(frame, (x+w, y+h),   (x+w, y+h-tl),     c, lw)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open webcam. Check that a camera is connected.")
        return

    # Try to set a reasonable resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("Skinora webcam started.")
    print("  SPACE  — Capture & analyse")
    print("  R      — Reset results")
    print("  Q      — Quit")

    results   = None
    frozen    = None   # frozen frame shown after capture
    show_live = True

    while True:
        if show_live:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame.")
                break
            frame = cv2.flip(frame, 1)   # mirror
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            draw_live_overlay(frame, gray)
            display_frame = frame.copy()
        else:
            display_frame = frozen.copy()

        # Build canvas: cam feed | panel
        H, W = display_frame.shape[:2]
        canvas_w = W + PANEL_W
        canvas   = np.full((H, canvas_w, 3), BG_DARK, dtype=np.uint8)
        canvas[:, :W] = display_frame

        # Status bar (bottom of cam area)
        if show_live:
            status = "LIVE  |  Press SPACE to analyse"
        else:
            status = "CAPTURED  |  Press R to reset"
        put_text(canvas, status, (10, H - 10), 0.45, (140, 200, 140))

        draw_panel(canvas, results)

        cv2.imshow("Skinora", canvas)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q') or key == 27:       # Q or ESC
            break
        elif key == ord(' '):                  # SPACE — capture
            ret, frame = cap.read()
            if ret:
                frame   = cv2.flip(frame, 1)
                results = analyze_frame(frame)
                frozen  = frame.copy()
                show_live = False
                if results is None:
                    print("No face detected. Try again.")
                else:
                    print(f"  Skin: {results.get('skin_name')}  |  "
                          f"Undertone: {results.get('undertone')}  |  "
                          f"Face: {results.get('face_shape')}  |  "
                          f"Eyes: {results.get('eye_shape')}")
        elif key == ord('r'):                  # R — reset
            results   = None
            frozen    = None
            show_live = True

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()