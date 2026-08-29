"""FormaFace API — FastAPI backend for Skinora dashboard."""

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core import (
    DATASET_ROOT,
    FACE_TIPS,
    GROOMING_TIPS,
    STYLE_TIPS,
    UNDERTONE_INFO,
    DatasetLoader,
    FaceEngine,
    build_analysis_response,
)

ROOT = Path(__file__).resolve().parent.parent.parent
MALEDASH_ROOT = ROOT / "maledash"

app = FastAPI(title="FormaFace API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = FaceEngine()
loader = DatasetLoader(DATASET_ROOT)

MAX_UPLOAD_BYTES = 12 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/bmp"}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "dataset_exists": DATASET_ROOT.exists(),
        "dataset_root": str(DATASET_ROOT),
    }


@app.get("/api/knowledge")
def knowledge():
    return {
        "undertones": UNDERTONE_INFO,
        "face_shapes": list(FACE_TIPS.keys()),
        "face_tips": FACE_TIPS,
        "grooming_tips": GROOMING_TIPS,
        "style_tips": STYLE_TIPS,
    }


@app.post("/api/analyze")
async def analyze(image: UploadFile = File(...)):
    if image.content_type and image.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Please upload a JPEG or PNG image.")

    data = await image.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Image too large (max 12 MB).")

    response = build_analysis_response(engine, loader, data)
    if not response.get("ok"):
        raise HTTPException(status_code=422, detail=response.get("error", "Analysis failed."))

    return response


if DATASET_ROOT.exists():
    app.mount("/dataset", StaticFiles(directory=str(DATASET_ROOT)), name="dataset")

if MALEDASH_ROOT.exists():
    app.mount("/", StaticFiles(directory=str(MALEDASH_ROOT), html=True), name="maledash")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
