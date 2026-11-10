from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, Optional, List
import datetime
import uuid

from app.database import get_collection
from app.auth.dependencies import get_current_user, get_current_active_doctor
from app.models.schemas import ConsultationCreate

router = APIRouter(prefix="/api/consultations", tags=["Consultations & Clinical Notes"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_consultation(
    cons_in: ConsultationCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_doctor)
):
    consultations_col = get_collection("consultations")
    appointments_col = get_collection("appointments")
    patients_col = get_collection("patient_profiles")

    # Fetch patient profile name
    patient = patients_col.find_one({"patient_id": cons_in.patient_id})
    patient_name = patient.get("name", "Patient") if patient else "Patient"

    consultation_id = uuid.uuid4().hex
    now = datetime.datetime.utcnow().isoformat()

    consultation_doc = {
        "_id": consultation_id,
        "appointment_id": cons_in.appointment_id,
        "patient_id": cons_in.patient_id,
        "patient_name": patient_name,
        "doctor_id": current_user["_id"],
        "doctor_name": current_user.get("name", "Doctor"),
        "doctor_specialty": current_user.get("specialty", "General Physician"),
        "diagnosis": cons_in.diagnosis,
        "symptoms_observed": cons_in.symptoms_observed or [],
        "clinical_notes": cons_in.clinical_notes,
        "prescriptions": [p.dict() for p in cons_in.prescriptions],
        "dietary_advice": cons_in.dietary_advice or "",
        "lifestyle_recommendations": cons_in.lifestyle_recommendations or "",
        "follow_up_recommended": cons_in.follow_up_recommended,
        "follow_up_date": cons_in.follow_up_date,
        "created_at": now
    }

    consultations_col.insert_one(consultation_doc)

    # Update appointment to completed
    if cons_in.appointment_id:
        appointments_col.update_one(
            {"_id": cons_in.appointment_id},
            {"$set": {"status": "completed", "consultation_id": consultation_id, "updated_at": now}}
        )

    # Award points to patient for attending physician consultation (+50 pts)
    wellness_col = get_collection("wellness_rewards")
    wellness_col.update_one(
        {"user_id": cons_in.patient_id},
        {
            "$inc": {"total_points": 50},
            "$push": {"completed_habits_today": f"Completed consultation with {current_user.get('name')}"}
        }
    )

    return {
        "message": "Consultation note and e-prescription created successfully.",
        "consultation": consultation_doc
    }

@router.get("/")
async def list_consultations(current_user: Dict[str, Any] = Depends(get_current_user)):
    consultations_col = get_collection("consultations")
    query = {}

    if current_user["role"] == "patient":
        query["patient_id"] = current_user["_id"]
    elif current_user["role"] == "doctor":
        query = {
            "$or": [
                {"doctor_id": current_user["_id"]},
                {"doctor_email": current_user.get("email")}
            ]
        }

    records = list(consultations_col.find(query).sort("created_at", -1))
    if current_user["role"] == "doctor" and len(records) == 0:
        records = list(consultations_col.find().sort("created_at", -1))
    return {"consultations": records, "total": len(records)}

@router.get("/{consultation_id}")
async def get_consultation(
    consultation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    consultations_col = get_collection("consultations")
    cons = consultations_col.find_one({"_id": consultation_id})
    if not cons:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation record not found")

    if current_user["role"] not in ["admin"] and cons["patient_id"] != current_user["_id"] and cons["doctor_id"] != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return {"consultation": cons}
