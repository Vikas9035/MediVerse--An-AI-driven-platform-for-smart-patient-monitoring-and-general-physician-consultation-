from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Dict, Any, Optional
import datetime
import uuid
import random

from app.database import get_collection
from app.auth.dependencies import get_current_user, get_current_active_patient
from app.models.schemas import VitalsCreate
from app.ml.risk_models import ml_health_engine

router = APIRouter(prefix="/api/vitals", tags=["Health Monitoring & Vitals"])

@router.post("/")
async def log_vitals(
    vitals_in: VitalsCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_patient)
):
    vitals_col = get_collection("vitals")
    now = datetime.datetime.utcnow().isoformat()
    
    # 1. Run AI/ML Anomaly Check
    anomaly_result = ml_health_engine.detect_vitals_anomaly(
        heart_rate=vitals_in.heart_rate,
        sys_bp=vitals_in.blood_pressure_sys,
        dia_bp=vitals_in.blood_pressure_dia,
        glucose=vitals_in.blood_glucose,
        spo2=vitals_in.spo2,
        temp=vitals_in.body_temperature
    )

    vitals_doc = {
        "_id": uuid.uuid4().hex,
        "patient_id": current_user["_id"],
        "patient_name": current_user.get("name", "Patient"),
        "heart_rate": vitals_in.heart_rate,
        "blood_pressure_sys": vitals_in.blood_pressure_sys,
        "blood_pressure_dia": vitals_in.blood_pressure_dia,
        "blood_glucose": vitals_in.blood_glucose,
        "spo2": vitals_in.spo2,
        "body_temperature": vitals_in.body_temperature,
        "respiratory_rate": vitals_in.respiratory_rate or 16.0,
        "device_source": vitals_in.device_source or "Manual Entry",
        "notes": vitals_in.notes or "",
        "anomaly_status": anomaly_result["status"],
        "is_anomaly": anomaly_result["is_anomaly"],
        "is_critical": anomaly_result["is_critical"],
        "anomaly_issues": anomaly_result["issues"],
        "recorded_at": now
    }

    vitals_col.insert_one(vitals_doc)

    # 2. Reward user with Wellness Points for active health tracking (+25 points)
    wellness_col = get_collection("wellness_rewards")
    wellness = wellness_col.find_one({"user_id": current_user["_id"]})
    if wellness:
        new_points = wellness.get("total_points", 0) + 25
        # Check tier
        tier = "Bronze"
        if new_points >= 1000:
            tier = "Platinum"
        elif new_points >= 500:
            tier = "Gold"
        elif new_points >= 250:
            tier = "Silver"

        wellness_col.update_one(
            {"user_id": current_user["_id"]},
            {
                "$set": {
                    "total_points": new_points,
                    "tier": tier,
                    "updated_at": now
                },
                "$push": {
                    "completed_habits_today": f"Vitals logged at {datetime.datetime.utcnow().strftime('%H:%M')}"
                }
            }
        )

    return {
        "message": "Vitals successfully logged.",
        "vitals": vitals_doc,
        "anomaly_assessment": anomaly_result,
        "points_earned": 25
    }

@router.get("/history")
async def get_vitals_history(
    limit: int = Query(30, ge=1, le=200),
    patient_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    vitals_col = get_collection("vitals")
    if current_user["role"] in ["doctor", "admin"]:
        query = {"patient_id": patient_id} if patient_id else {}
    else:
        query = {"patient_id": current_user["_id"]}
    history = list(vitals_col.find(query).sort("recorded_at", -1).limit(limit))

    return {
        "patient_id": patient_id or current_user["_id"],
        "vitals": history,
        "total_records": len(history)
    }

@router.get("/latest")
async def get_latest_vitals(
    patient_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    target_patient_id = current_user["_id"]
    if current_user["role"] in ["doctor", "admin"] and patient_id:
        target_patient_id = patient_id

    vitals_col = get_collection("vitals")
    latest = vitals_col.find_one({"patient_id": target_patient_id}, sort=[("recorded_at", -1)])
    
    if not latest:
        # Default healthy fallback if none logged yet
        latest = {
            "patient_id": target_patient_id,
            "heart_rate": 72.0,
            "blood_pressure_sys": 120.0,
            "blood_pressure_dia": 80.0,
            "blood_glucose": 95.0,
            "spo2": 98.0,
            "body_temperature": 36.8,
            "respiratory_rate": 16.0,
            "device_source": "MediVerse Smart Baseline",
            "anomaly_status": "Normal",
            "is_anomaly": False,
            "is_critical": False,
            "anomaly_issues": [],
            "recorded_at": datetime.datetime.utcnow().isoformat()
        }

    return {"latest": latest}

@router.post("/simulate-stream")
async def simulate_iot_vitals_stream(
    mode: str = Query("normal", description="Simulate scenario: normal, elevated_bp, tachycardia, post_workout"),
    current_user: Dict[str, Any] = Depends(get_current_active_patient)
):
    """
    Simulates real-time telemetry from connected wearable smartwatch / medical sensor.
    """
    if mode == "elevated_bp":
        sys_bp = round(random.uniform(142.0, 155.0), 1)
        dia_bp = round(random.uniform(92.0, 98.0), 1)
        hr = round(random.uniform(78.0, 88.0), 1)
        spo2 = round(random.uniform(96.0, 98.0), 1)
        glucose = round(random.uniform(105.0, 125.0), 1)
    elif mode == "tachycardia":
        sys_bp = round(random.uniform(128.0, 138.0), 1)
        dia_bp = round(random.uniform(82.0, 88.0), 1)
        hr = round(random.uniform(112.0, 130.0), 1)
        spo2 = round(random.uniform(96.0, 99.0), 1)
        glucose = round(random.uniform(95.0, 110.0), 1)
    elif mode == "post_workout":
        sys_bp = round(random.uniform(130.0, 140.0), 1)
        dia_bp = round(random.uniform(75.0, 82.0), 1)
        hr = round(random.uniform(98.0, 115.0), 1)
        spo2 = round(random.uniform(97.0, 99.0), 1)
        glucose = round(random.uniform(88.0, 102.0), 1)
    else: # normal
        sys_bp = round(random.uniform(116.0, 124.0), 1)
        dia_bp = round(random.uniform(76.0, 82.0), 1)
        hr = round(random.uniform(68.0, 76.0), 1)
        spo2 = round(random.uniform(98.0, 99.5), 1)
        glucose = round(random.uniform(85.0, 98.0), 1)

    temp = round(random.uniform(36.6, 37.1), 1)
    
    anomaly_result = ml_health_engine.detect_vitals_anomaly(
        heart_rate=hr, sys_bp=sys_bp, dia_bp=dia_bp, glucose=glucose, spo2=spo2, temp=temp
    )

    doc = {
        "_id": uuid.uuid4().hex,
        "patient_id": current_user["_id"],
        "patient_name": current_user.get("name", "Patient"),
        "heart_rate": hr,
        "blood_pressure_sys": sys_bp,
        "blood_pressure_dia": dia_bp,
        "blood_glucose": glucose,
        "spo2": spo2,
        "body_temperature": temp,
        "respiratory_rate": round(random.uniform(15.0, 18.0), 1),
        "device_source": "MediPulse Connected Smartwatch (BLE / IoT Stream)",
        "notes": f"Auto-synced sensor packet [{mode}]",
        "anomaly_status": anomaly_result["status"],
        "is_anomaly": anomaly_result["is_anomaly"],
        "is_critical": anomaly_result["is_critical"],
        "anomaly_issues": anomaly_result["issues"],
        "recorded_at": datetime.datetime.utcnow().isoformat()
    }

    vitals_col = get_collection("vitals")
    vitals_col.insert_one(doc)

    return {
        "message": "Connected device sensor packet received & validated.",
        "stream_data": doc,
        "anomaly_assessment": anomaly_result
    }
