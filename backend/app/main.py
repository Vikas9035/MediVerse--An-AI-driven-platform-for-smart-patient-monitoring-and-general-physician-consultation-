from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from app.config import PLATFORM_NAME, TAGLINE, SDG_GOAL, UPLOAD_DIR
from app.database import db_manager
from app.seed_data import seed_database_if_empty

# Routers
from app.routes.auth import router as auth_router
from app.routes.patients import router as patients_router
from app.routes.doctors import router as doctors_router
from app.routes.vitals import router as vitals_router
from app.routes.reports import router as reports_router
from app.routes.appointments import router as appointments_router
from app.routes.consultations import router as consultations_router
from app.routes.ai_ml import router as ai_ml_router
from app.routes.wellness import router as wellness_router
from app.routes.admin import router as admin_router

app = FastAPI(
    title=f"{PLATFORM_NAME} API",
    description=f"{TAGLINE}. Aligned with {SDG_GOAL}.",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded medical files statically
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include Modular Routers
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(doctors_router)
app.include_router(vitals_router)
app.include_router(reports_router)
app.include_router(appointments_router)
app.include_router(consultations_router)
app.include_router(ai_ml_router)
app.include_router(wellness_router)
app.include_router(admin_router)

@app.on_event("startup")
async def on_startup():
    print(f"[STARTUP] Initializing {PLATFORM_NAME} Engine...")
    seed_database_if_empty()

@app.get("/")
async def root():
    return {
        "platform": PLATFORM_NAME,
        "tagline": TAGLINE,
        "un_sdg_alignment": SDG_GOAL,
        "status": "Online",
        "database_mode": "MongoDB Server" if db_manager.is_real_mongo else "High-Fidelity Persistent JSON/NoSQL Engine",
        "documentation": "/docs"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "Healthy",
        "database_connected": True,
        "database_engine": "MongoDB" if db_manager.is_real_mongo else "Local Mongo Fallback",
        "ai_ml_models": ["Cardiovascular RandomForestClassifier", "Diabetes Classifier", "IsolationForest Vitals Anomaly", "Symptom Triage"]
    }
