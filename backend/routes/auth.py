from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from auth_utils import create_access_token, hash_password, verify_password
from database import get_db
from deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class GenderBody(BaseModel):
    gender: str = Field(pattern="^(male|female|skip)$")


def _user_public(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "email": doc["email"],
        "gender": doc.get("gender"),
    }


@router.post("/register")
async def register(body: RegisterBody):
    db = get_db()
    email = body.email.strip().lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    now = datetime.now(timezone.utc)
    doc = {
        "email": email,
        "password_hash": hash_password(body.password),
        "gender": None,
        "profile": {},
        "created_at": now,
        "updated_at": now,
    }
    result = await db.users.insert_one(doc)
    user_id = str(result.inserted_id)
    token = create_access_token(user_id, email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user_id, "email": email, "gender": None},
    }


@router.post("/login")
async def login(body: LoginBody):
    db = get_db()
    email = body.email.strip().lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"updated_at": datetime.now(timezone.utc)}},
    )
    token = create_access_token(str(user["_id"]), email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_public(user),
    }


@router.patch("/gender")
async def set_gender(body: GenderBody, user=Depends(get_current_user)):
    db = get_db()
    await db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {"gender": body.gender, "updated_at": datetime.now(timezone.utc)}},
    )
    return {"ok": True, "gender": body.gender}


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return user
