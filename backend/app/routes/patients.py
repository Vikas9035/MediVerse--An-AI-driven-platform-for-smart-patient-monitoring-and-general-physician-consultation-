from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
import datetime

from app.database import get_collection
from app.auth.dependencies import get_current_user, get_current_active_patient
from app.models.schemas import PatientProfileUpdate

router = APIRouter(prefix="/api/patients", tags=["Patients"])

@router.get("/profile")
async def get_patient_profile(current_user: Dict[str, Any] = Depends(get_current_active_patient)):
    profiles_col = get_collection("patient_profiles")
    profile = profiles_col.find_one({"patient_id": current_user["_id"]})
    if not profile:
        profile = {
            "patient_id": current_user["_id"],
            "name": current_user["name"],
            "email": current_user["email"],
            "age": 30,
            "gender": "Not Specified",
            "blood_group": "O+",
            "height_cm": 170.0,
            "weight_kg": 68.0,
            "bmi": 23.5,
            "allergies": [],
            "chronic_conditions": [],
            "is_smoker": False,
            "physical_activity_level": "moderate"
        }
    return {"profile": profile}

@router.put("/profile")
async def update_patient_profile(
    profile_data: PatientProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_patient)
):
    profiles_col = get_collection("patient_profiles")
    update_fields = {k: v for k, v in profile_data.dict().items() if v is not None}
    
    # Calculate BMI if height and weight are provided
    height_cm = update_fields.get("height_cm")
    weight_kg = update_fields.get("weight_kg")
    
    if height_cm and weight_kg and height_cm > 0:
        height_m = height_cm / 100.0
        bmi = round(weight_kg / (height_m * height_m), 1)
        update_fields["bmi"] = bmi

    update_fields["updated_at"] = datetime.datetime.utcnow().isoformat()

    profiles_col.update_one(
        {"patient_id": current_user["_id"]},
        {"$set": update_fields},
        upsert=True
    )
    
    updated = profiles_col.find_one({"patient_id": current_user["_id"]})
    return {"message": "Profile updated successfully", "profile": updated}

@router.get("/{patient_id}")
async def get_patient_by_id(
    patient_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # Only doctor, admin, or the patient themselves can view
    if current_user["role"] not in ["doctor", "admin"] and current_user["_id"] != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden to this patient record."
        )
    
    profiles_col = get_collection("patient_profiles")
    profile = profiles_col.find_one({"patient_id": patient_id})
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
    
    # Fetch recent vitals count & report summary for doctor view
    vitals_col = get_collection("vitals")
    recent_vitals = list(vitals_col.find({"patient_id": patient_id}).sort("recorded_at", -1).limit(5))
    
    reports_col = get_collection("reports")
    reports = list(reports_col.find({"patient_id": patient_id}).sort("created_at", -1))

    return {
        "profile": profile,
        "recent_vitals": recent_vitals,
        "reports": reports
    }
