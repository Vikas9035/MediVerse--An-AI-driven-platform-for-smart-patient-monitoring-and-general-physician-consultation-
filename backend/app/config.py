import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "mediverse_db")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "mediverse-super-secure-production-ready-secret-key-2026")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))
DATA_DIR = os.getenv("DATA_DIR", str(BASE_DIR / "data"))

Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

# Platform Branding & SDG Alignment
PLATFORM_NAME = "MediVerse"
TAGLINE = "AI-Driven Smart Patient Monitoring & General Physician Consultation"
SDG_GOAL = "UN SDG 3: Good Health and Well-Being"
