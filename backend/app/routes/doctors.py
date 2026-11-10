from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Dict, Any, Optional, List
import datetime

from app.database import get_collection
from app.auth.dependencies import get_current_user, get_current_active_doctor
from app.models.schemas import DoctorProfileUpdate

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])

def sync_doctor_users_to_profiles():
    """Ensure all accounts with role == 'doctor' in users collection exist in doctor_profiles."""
    users_col = get_collection("users")
    doctors_col = get_collection("doctor_profiles")
    
    doctor_users = list(users_col.find({"role": "doctor"}))
    for d_user in doctor_users:
        doc_id = d_user["_id"]
        existing = doctors_col.find_one({"doctor_id": doc_id}) or doctors_col.find_one({"_id": doc_id}) or doctors_col.find_one({"email": d_user.get("email", "").lower()})
        if not existing:
            now = datetime.datetime.utcnow().isoformat()
            doctors_col.insert_one({
                "_id": doc_id,
                "doctor_id": doc_id,
                "name": d_user.get("name", "Dr. Physician"),
                "email": d_user.get("email", "").lower(),
                "specialty": d_user.get("specialty") or "General Physician",
                "qualification": d_user.get("qualification") or "MBBS, MD",
                "experience_years": d_user.get("experience_years") or 8,
                "consultation_fee": d_user.get("consultation_fee") or 45.0,
                "rating": 4.9,
                "total_reviews": 18,
                "bio": "Dedicated specialist focusing on comprehensive patient care, preventive medicine, and digital telehealth.",
                "is_verified": True,
                "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                "time_slots": ["09:00 AM", "10:30 AM", "12:00 PM", "02:30 PM", "04:00 PM", "05:30 PM"],
                "created_at": now
            })

@router.get("/")
async def list_doctors(
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    search: Optional[str] = Query(None, description="Search by doctor name or specialty")
):
    try:
        sync_doctor_users_to_profiles()
    except Exception as e:
        print(f"[DOCTORS] Sync warning: {e}")

    doctors_col = get_collection("doctor_profiles")
    query = {}
    if specialty and specialty.strip() and specialty != "All":
        query["specialty"] = specialty

    raw_doctors = list(doctors_col.find(query))
    doctors = []
    for doc in raw_doctors:
        doc_copy = dict(doc)
        if "doctor_id" not in doc_copy:
            doc_copy["doctor_id"] = str(doc_copy.get("_id"))
        doc_copy["_id"] = str(doc_copy.get("_id"))
        doctors.append(doc_copy)
    
    if search and search.strip():
        s = search.lower().strip()
        doctors = [
            doc for doc in doctors
            if s in doc.get("name", "").lower() 
            or s in doc.get("specialty", "").lower()
            or s in doc.get("qualification", "").lower()
            or s in doc.get("bio", "").lower()
        ]
    
    return {"doctors": doctors, "total": len(doctors)}

@router.get("/specialties")
async def get_specialties():
    try:
        sync_doctor_users_to_profiles()
    except Exception:
        pass
    doctors_col = get_collection("doctor_profiles")
    specialties = doctors_col.distinct("specialty")
    standard = ["General Physician", "Cardiologist", "Endocrinologist", "Pulmonologist", "Internal Medicine", "Preventive Healthcare"]
    all_spec = sorted(list(set([s for s in specialties if s] + standard)))
    return {"specialties": all_spec}

@router.get("/profile")
async def get_my_doctor_profile(current_user: Dict[str, Any] = Depends(get_current_active_doctor)):
    doctors_col = get_collection("doctor_profiles")
    profile = doctors_col.find_one({"doctor_id": current_user["_id"]}) or doctors_col.find_one({"_id": current_user["_id"]}) or doctors_col.find_one({"email": current_user["email"].lower()})
    if not profile:
        profile = {
            "_id": current_user["_id"],
            "doctor_id": current_user["_id"],
            "name": current_user["name"],
            "email": current_user["email"].lower(),
            "specialty": "General Physician",
            "qualification": "MBBS, MD",
            "experience_years": 8,
            "consultation_fee": 45.0,
            "rating": 4.9,
            "total_reviews": 24,
            "bio": "Experienced General Physician focused on comprehensive patient care.",
            "is_verified": True,
            "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "time_slots": ["09:00 AM", "10:30 AM", "12:00 PM", "02:30 PM", "04:00 PM", "05:30 PM"],
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        doctors_col.update_one({"doctor_id": current_user["_id"]}, {"$set": profile}, upsert=True)
    return {"profile": profile}

@router.put("/profile")
async def update_doctor_profile(
    profile_data: DoctorProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_doctor)
):
    doctors_col = get_collection("doctor_profiles")
    update_fields = {k: v for k, v in profile_data.dict().items() if v is not None}
    update_fields["updated_at"] = datetime.datetime.utcnow().isoformat()
    update_fields["name"] = current_user.get("name")
    update_fields["email"] = current_user.get("email")
    
    doctors_col.update_one(
        {"doctor_id": current_user["_id"]},
        {"$set": update_fields},
        upsert=True
    )
    
    updated = doctors_col.find_one({"doctor_id": current_user["_id"]}) or doctors_col.find_one({"_id": current_user["_id"]})
    return {"message": "Doctor profile updated successfully", "profile": updated}

@router.get("/{doctor_id}")
async def get_doctor_by_id(doctor_id: str):
    doctors_col = get_collection("doctor_profiles")
    doctor = doctors_col.find_one({"doctor_id": doctor_id}) or doctors_col.find_one({"_id": doctor_id})
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return {"doctor": doctor}

