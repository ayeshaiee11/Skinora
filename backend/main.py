"""Skinora unified API — auth, profiles (MongoDB), ML, all static pages."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from config import ASSETS_ROOT, FEMALE_DASH_ROOT, LANDING_ROOT, LOGIN_ROOT, MALE_DASH_ROOT, ROOT
from database import close_db, get_db
from female_ml import analyze_bytes as analyze_female_bytes
from female_ml import available as female_ml_available
from female_ml import dataset_root as female_dataset_root
from routes.auth import router as auth_router
from routes.profile import router as profile_router

_male_ml = False
_engine = None
_loader = None
_DATASET_ROOT = None

try:
    male_backend = ROOT / "male" / "malemodel" / "backend"
    sys.path.insert(0, str(male_backend))
    from core import (  # type: ignore
        DATASET_ROOT as _DATASET_ROOT,
        DatasetLoader,
        FaceEngine,
        build_analysis_response,
    )

    _engine = FaceEngine()
    _loader = DatasetLoader(_DATASET_ROOT)
    _male_ml = True
except Exception:
    pass

_female_ml = female_ml_available()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_db()
    await db.users.create_index("email", unique=True)
    yield
    await close_db()


app = FastAPI(title="Skinora API", version="1.0.0", lifespan=lifespan)


class NoCacheStaticMiddleware(BaseHTTPMiddleware):
    """Prevent stale login JS from sticking in the browser cache."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path == "/" or path.endswith((".js", ".html", ".css")):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        return response


app.add_middleware(NoCacheStaticMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profile_router)

MAX_UPLOAD = 12 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/bmp"}


@app.get("/api/health")
async def health():
    try:
        db = get_db()
        await db.command("ping")
        mongo_ok = True
    except Exception:
        mongo_ok = False
    return {
        "status": "ok" if mongo_ok else "degraded",
        "mongodb": mongo_ok,
        "formaface_male": _male_ml,
        "formaface_female": _female_ml,
    }


@app.get("/male")
async def go_male():
    return RedirectResponse(url="/male/")


@app.get("/female")
async def go_female():
    return RedirectResponse(url="/female/")


@app.post("/api/analyze")
async def analyze_face_male(image: UploadFile = File(...)):
    if not _male_ml:
        raise HTTPException(503, "Male FormaFace engine is not available.")
    if image.content_type and image.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Please upload a JPEG or PNG image.")
    data = await image.read()
    if not data:
        raise HTTPException(400, "Empty file uploaded.")
    if len(data) > MAX_UPLOAD:
        raise HTTPException(400, "Image too large (max 12 MB).")
    response = build_analysis_response(_engine, _loader, data)
    if not response.get("ok"):
        raise HTTPException(422, response.get("error", "Analysis failed."))
    return response


@app.post("/api/analyze/female")
async def analyze_face_female(image: UploadFile = File(...)):
    if not _female_ml:
        raise HTTPException(503, "Female FormaFace engine is not available.")
    if image.content_type and image.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Please upload a JPEG or PNG image.")
    data = await image.read()
    if not data:
        raise HTTPException(400, "Empty file uploaded.")
    if len(data) > MAX_UPLOAD:
        raise HTTPException(400, "Image too large (max 12 MB).")
    suffix = Path(image.filename or "photo.jpg").suffix.lower() or ".jpg"
    result = analyze_female_bytes(data, suffix)
    if result.get("error"):
        raise HTTPException(422, result["error"])
    return result


if _male_ml and _DATASET_ROOT and _DATASET_ROOT.exists():
    app.mount("/dataset", StaticFiles(directory=str(_DATASET_ROOT)), name="dataset")

_female_ds = female_dataset_root()
if _female_ml and _female_ds and _female_ds.exists():
    app.mount(
        "/api/dataset/female",
        StaticFiles(directory=str(_female_ds)),
        name="female-dataset",
    )

if ASSETS_ROOT.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_ROOT)), name="assets")
if MALE_DASH_ROOT.exists():
    app.mount("/male", StaticFiles(directory=str(MALE_DASH_ROOT), html=True), name="male")
if FEMALE_DASH_ROOT.exists():
    app.mount("/female", StaticFiles(directory=str(FEMALE_DASH_ROOT), html=True), name="female")
if LOGIN_ROOT.exists():
    app.mount("/login", StaticFiles(directory=str(LOGIN_ROOT), html=True), name="login")
if LANDING_ROOT.exists():
    app.mount("/", StaticFiles(directory=str(LANDING_ROOT), html=True), name="landing")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
