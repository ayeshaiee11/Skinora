"""
FormaFace API — Flask server for the Skinora dashboard.

Run:
    pip install -r requirements.txt
    python formaface_server.py

The femaledash FormaFace section calls http://localhost:5000/api/analyze
"""

import base64
import tempfile
from pathlib import Path

import cv2
from flask import Flask, abort, jsonify, request, send_file
from flask_cors import CORS

from engine_core import (
    DATASET_ROOT,
    EYE_EYELINER,
    FACE_TIPS,
    MAKEUP_TIPS,
    SKIN_TIPS,
    UNDERTONE_INFO,
    DatasetLoader,
    FaceEngine,
)

app = Flask(__name__)
CORS(app)

_engine = FaceEngine()
_loader = DatasetLoader(DATASET_ROOT)
_dataset_root = DATASET_ROOT.resolve()


def _bgr_to_data_url(bgr) -> str:
    ok, buf = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
    if not ok:
        return ""
    encoded = base64.b64encode(buf).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def _image_entry(path: Path) -> dict:
    rel = path.relative_to(_dataset_root)
    return {
        "name": path.stem.replace("_", " ").title(),
        "url": f"/api/dataset/{rel.as_posix()}",
    }


def _paths_to_entries(paths) -> list:
    return [_image_entry(p) for p in paths if p and p.exists()]


def _build_recommendations(face_shape: str, eye_shape: str, undertone: str) -> dict:
    return {
        "hairstyles":    _paths_to_entries(_loader.hairstyles(face_shape, 3)),
        "hijaab":        _paths_to_entries(_loader.hijaab(face_shape, 3)),
        "outfit_styles": _paths_to_entries(_loader.outfit_styles(face_shape, undertone, 3)),
        "colours":       _paths_to_entries(_loader.colours(face_shape, undertone, 4)),
        "accessories":   _paths_to_entries(_loader.accessories(face_shape, 2)),
        "eyeliner":      _paths_to_entries(_loader.eyeliner(eye_shape, 1)),
        "face_shape":    _paths_to_entries(_loader.face_shape_imgs(face_shape, 1)),
        "eye_shape":     _paths_to_entries(_loader.eye_shape_imgs(eye_shape, 1)),
    }


def _build_tips(face_shape: str, eye_shape: str, undertone: str) -> dict:
    face = FACE_TIPS.get(face_shape, {})
    ut_info = UNDERTONE_INFO.get(undertone, {})
    return {
        "face_shape": face,
        "eyeliner": EYE_EYELINER.get(eye_shape, "Soft liner along the lash line suits most eye shapes."),
        "makeup": MAKEUP_TIPS.get(undertone, ""),
        "skin": SKIN_TIPS.get(undertone, ""),
        "undertone": ut_info,
    }


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "dataset_exists": _dataset_root.exists(),
        "dataset_root": str(_dataset_root),
    })


@app.route("/api/analyze", methods=["POST"])
def analyze():
    upload = request.files.get("image")
    if upload is None or upload.filename == "":
        return jsonify({"error": "No image uploaded."}), 400

    suffix = Path(upload.filename).suffix.lower() or ".jpg"
    if suffix not in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
        return jsonify({"error": "Unsupported image format."}), 400

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        upload.save(tmp.name)
        tmp_path = tmp.name

    try:
        result = _engine.analyse(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if result.get("error"):
        return jsonify({"error": result["error"]}), 422

    annotated = result.pop("annotated")
    face_shape = result["face_shape"]
    eye_shape = result["eye_shape"]
    undertone = result["undertone"]

    return jsonify({
        **result,
        "annotated": _bgr_to_data_url(annotated),
        "tips": _build_tips(face_shape, eye_shape, undertone),
        "recommendations": _build_recommendations(face_shape, eye_shape, undertone),
    })


@app.route("/api/dataset/<path:filepath>")
def serve_dataset(filepath):
    full = (_dataset_root / filepath).resolve()
    if not str(full).startswith(str(_dataset_root)):
        abort(403)
    if not full.is_file():
        abort(404)
    return send_file(full)


if __name__ == "__main__":
    print(f"FormaFace API running — dataset: {_dataset_root}")
    app.run(host="0.0.0.0", port=5000, debug=True)
