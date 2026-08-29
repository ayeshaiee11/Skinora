import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "backend" / ".env")
load_dotenv(ROOT / ".env")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "skinora")
JWT_SECRET = os.getenv("JWT_SECRET", "skinora-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "168"))

LOGIN_ROOT = ROOT / "Skinora-login" / "Skinora-login"
LANDING_ROOT = ROOT / "Skinora landing page" / "Skinora landing page" / "Skinora LP"
MALE_DASH_ROOT = ROOT / "male" / "maledash"
FEMALE_DASH_ROOT = ROOT / "female" / "femaledash"
ASSETS_ROOT = ROOT / "backend" / "assets"
