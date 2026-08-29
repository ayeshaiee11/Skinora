from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from database import get_db
from deps import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])


class ProfileBody(BaseModel):
    skinType: str | None = None
    undertone: str | None = None
    age: int | None = None
    height: int | None = None
    weight: int | None = None
    smoking: str | None = None
    period: str | None = None
    pcos: str | None = None
    formaface: dict | None = None
    faceShape: str | None = None
    eyeShape: str | None = None
    mlUndertone: str | None = None
    contrast: str | None = None
    formafaceScannedAt: str | None = None


@router.get("")
async def get_profile(user=Depends(get_current_user)):
    db = get_db()
    doc = await db.users.find_one({"_id": ObjectId(user["id"])}, {"profile": 1, "gender": 1, "email": 1})
    profile = (doc or {}).get("profile") or {}
    return {
        "email": user["email"],
        "gender": user.get("gender"),
        "profile": profile,
    }


@router.put("")
async def save_profile(body: ProfileBody, user=Depends(get_current_user)):
    db = get_db()
    data = body.model_dump(exclude_none=True)
    doc = await db.users.find_one({"_id": ObjectId(user["id"])}, {"profile": 1})
    merged = {**(doc.get("profile") if doc else {}), **data}
    await db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {
            "$set": {
                "profile": merged,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    return {"ok": True, "profile": merged}
