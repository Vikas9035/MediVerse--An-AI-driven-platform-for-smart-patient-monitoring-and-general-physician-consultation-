from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, Optional
import datetime

from app.database import get_collection
from app.auth.dependencies import get_current_user, get_current_active_patient
from app.models.schemas import HealthRiskInput, SymptomCheckerInput
from app.ml.risk_models import ml_health_engine

router = APIRouter(prefix="/api/ai", tags=["AI & Machine Learning Insights"])

@router.post("/assess-risks")
async def assess_health_risks(
    risk_input: HealthRiskInput,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    results = ml_health_engine.assess_risks(risk_input.dict())
    
    # If patient, persist the assessment in their history
    if current_user["role"] == "patient":
        ai_assessments_col = get_collection("ai_assessments")
        doc = {
            "patient_id": current_user["_id"],
            "patient_name": current_user.get("name", "Patient"),
            "input_features": risk_input.dict(),
            "results": results,
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        ai_assessments_col.insert_one(doc)

    return results

@router.get("/insights")
async def get_patient_ai_insights(
    patient_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    target_patient_id = current_user["_id"]
    if current_user["role"] in ["doctor", "admin"] and patient_id:
        target_patient_id = patient_id

    # 1. Fetch latest profile
    profiles_col = get_collection("patient_profiles")
    profile = profiles_col.find_one({"patient_id": target_patient_id}) or {}

    # 2. Fetch latest vitals
    vitals_col = get_collection("vitals")
    latest_vitals = vitals_col.find_one({"patient_id": target_patient_id}, sort=[("recorded_at", -1)])

    age = profile.get("age", 35)
    gender = profile.get("gender", "male")
    bmi = profile.get("bmi", 23.8)
    is_smoker = profile.get("is_smoker", False)
    activity = profile.get("physical_activity_level", "moderate")

    if latest_vitals:
        sys_bp = latest_vitals.get("blood_pressure_sys", 120.0)
        dia_bp = latest_vitals.get("blood_pressure_dia", 80.0)
        glucose = latest_vitals.get("blood_glucose", 95.0)
        hr = latest_vitals.get("heart_rate", 72.0)
        spo2 = latest_vitals.get("spo2", 98.0)
    else:
        sys_bp = 120.0
        dia_bp = 80.0
        glucose = 95.0
        hr = 72.0
        spo2 = 98.0

    features = {
        "age": age,
        "gender": gender,
        "systolic_bp": sys_bp,
        "diastolic_bp": dia_bp,
        "blood_glucose": glucose,
        "heart_rate": hr,
        "bmi": bmi,
        "spo2": spo2,
        "is_smoker": is_smoker,
        "physical_activity": activity,
        "family_history_diabetes": any("diabetes" in str(c).lower() for c in profile.get("chronic_conditions", [])),
        "family_history_heart_disease": False
    }

    assessment = ml_health_engine.assess_risks(features)

    # UN SDG 3 health metric indicators
    sdg_alignment = {
        "goal": "UN SDG 3: Ensure healthy lives and promote well-being for all at all ages",
        "target_3_4": "Reduce premature mortality from non-communicable diseases (NCDs) via prevention & continuous monitoring",
        "target_3_8": "Achieve universal health coverage, access to quality essential healthcare services and safe medicines",
        "patient_preventive_score": assessment["vitality_index"],
        "monitoring_frequency": "Continuous / Connected" if latest_vitals else "Periodic",
        "active_recommendations_count": len(assessment["personalized_insights"])
    }

    return {
        "patient_id": target_patient_id,
        "current_vitals_summary": {
            "heart_rate": hr,
            "blood_pressure": f"{int(sys_bp)}/{int(dia_bp)} mmHg",
            "blood_glucose": f"{int(glucose)} mg/dL",
            "spo2": f"{int(spo2)}%",
            "bmi": bmi
        },
        "assessment": assessment,
        "sdg_alignment": sdg_alignment
    }

@router.post("/symptom-checker")
async def check_symptoms(
    symptom_in: SymptomCheckerInput,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    result = ml_health_engine.check_symptoms(
        symptoms=symptom_in.symptoms,
        duration_days=symptom_in.duration_days or 2,
        severity=symptom_in.severity or "moderate"
    )
    return result
