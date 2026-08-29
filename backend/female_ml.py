"""Female FormaFace engine wrapper for unified Skinora API."""

import base64
import sys
import tempfile
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
FEMALE_MODEL = ROOT / "female" / "femalemodel"

_female_ok = False
_engine = None
_loader = None
_DATASET_ROOT = None
_FACE_TIPS = None
_EYE_EYELINER = None
_MAKEUP_TIPS = None
_SKIN_TIPS = None
_UNDERTONE_INFO = None


def _init():
    global _female_ok, _engine, _loader, _DATASET_ROOT
    global _FACE_TIPS, _EYE_EYELINER, _MAKEUP_TIPS, _SKIN_TIPS, _UNDERTONE_INFO
    if _female_ok:
        return True
    try:
        sys.path.insert(0, str(FEMALE_MODEL))
        from engine_core import (  # type: ignore
            DATASET_ROOT,
            EYE_EYELINER,
            FACE_TIPS,
            MAKEUP_TIPS,
            SKIN_TIPS,
            UNDERTONE_INFO,
            DatasetLoader,
            FaceEngine,
        )

        _DATASET_ROOT = DATASET_ROOT
        _engine = FaceEngine()
        _loader = DatasetLoader(DATASET_ROOT)
        _FACE_TIPS = FACE_TIPS
        _EYE_EYELINER = EYE_EYELINER
        _MAKEUP_TIPS = MAKEUP_TIPS
        _SKIN_TIPS = SKIN_TIPS
        _UNDERTONE_INFO = UNDERTONE_INFO
        _female_ok = True
        return True
    except Exception:
        return False


def available() -> bool:
    return _init()


def dataset_root() -> Path | None:
    _init()
    return _DATASET_ROOT


def _bgr_to_data_url(bgr) -> str:
    ok, buf = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
    if not ok:
        return ""
    return "data:image/jpeg;base64," + base64.b64encode(buf).decode("ascii")


def _image_entry(path: Path) -> dict:
    rel = path.relative_to(_DATASET_ROOT)
    return {
        "name": path.stem.replace("_", " ").title(),
        "url": f"/api/dataset/female/{rel.as_posix()}",
    }


def _paths_to_entries(paths) -> list:
    return [_image_entry(p) for p in paths if p and p.exists()]


def _build_recommendations(face_shape: str, eye_shape: str, undertone: str) -> dict:
    return {
        "hairstyles": _paths_to_entries(_loader.hairstyles(face_shape, 3)),
        "hijaab": _paths_to_entries(_loader.hijaab(face_shape, 3)),
        "outfit_styles": _paths_to_entries(_loader.outfit_styles(face_shape, undertone, 3)),
        "colours": _paths_to_entries(_loader.colours(face_shape, undertone, 4)),
        "accessories": _paths_to_entries(_loader.accessories(face_shape, 2)),
        "eyeliner": _paths_to_entries(_loader.eyeliner(eye_shape, 1)),
        "face_shape": _paths_to_entries(_loader.face_shape_imgs(face_shape, 1)),
        "eye_shape": _paths_to_entries(_loader.eye_shape_imgs(eye_shape, 1)),
    }


def _build_tips(face_shape: str, eye_shape: str, undertone: str) -> dict:
    face = _FACE_TIPS.get(face_shape, {})
    ut_info = _UNDERTONE_INFO.get(undertone, {})
    return {
        "face_shape": face,
        "eyeliner": _EYE_EYELINER.get(eye_shape, "Soft liner along the lash line suits most eye shapes."),
        "makeup": _MAKEUP_TIPS.get(undertone, ""),
        "skin": _SKIN_TIPS.get(undertone, ""),
        "undertone": ut_info,
    }


def analyze_bytes(data: bytes, suffix: str = ".jpg") -> dict:
    if not _init():
        return {"error": "Female FormaFace engine is not available."}

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        result = _engine.analyse(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if result.get("error"):
        return {"error": result["error"]}

    annotated = result.pop("annotated")
    face_shape = result["face_shape"]
    eye_shape = result["eye_shape"]
    undertone = result["undertone"]

    return {
        **result,
        "annotated": _bgr_to_data_url(annotated),
        "tips": _build_tips(face_shape, eye_shape, undertone),
        "recommendations": _build_recommendations(face_shape, eye_shape, undertone),
    }
