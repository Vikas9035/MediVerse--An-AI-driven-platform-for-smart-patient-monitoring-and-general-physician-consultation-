from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Dict, Any, Optional, List
import datetime
import uuid

from app.database import get_collection
from app.auth.dependencies import get_current_user, get_current_active_patient, get_current_active_doctor
from app.models.schemas import AppointmentCreate, AppointmentStatusUpdate

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appt_in: AppointmentCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_patient)
):
    doctors_col = get_collection("doctor_profiles")
    doctor = doctors_col.find_one({"doctor_id": appt_in.doctor_id})
    if not doctor:
        doctor = doctors_col.find_one({"_id": appt_in.doctor_id})
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selected doctor was not found.")

    appointments_col = get_collection("appointments")
    now = datetime.datetime.utcnow().isoformat()
    appt_id = uuid.uuid4().hex

    # Check for slot conflicts
    conflict = appointments_col.find_one({
        "doctor_id": doctor.get("doctor_id", doctor.get("_id")),
        "appointment_date": appt_in.appointment_date,
        "time_slot": appt_in.time_slot,
        "status": {"$in": ["pending", "confirmed"]}
    })
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This appointment slot is already booked. Please choose a different time."
        )

    appt_doc = {
        "_id": appt_id,
        "patient_id": current_user["_id"],
        "patient_name": current_user.get("name", "Patient"),
        "patient_email": current_user.get("email"),
        "doctor_id": doctor.get("doctor_id", doctor.get("_id")),
        "doctor_name": doctor.get("name", "Doctor"),
        "doctor_specialty": doctor.get("specialty", "General Physician"),
        "consultation_fee": doctor.get("consultation_fee", 40.0),
        "appointment_date": appt_in.appointment_date,
        "time_slot": appt_in.time_slot,
        "reason_for_visit": appt_in.reason_for_visit,
        "symptoms": appt_in.symptoms or [],
        "consultation_type": appt_in.consultation_type or "Online Video",
        "status": "confirmed", # auto-confirm for seamless doctor-patient workflow
        "meeting_link": f"https://meet.mediverse.health/room-{appt_id[:8]}",
        "created_at": now,
        "updated_at": now
    }

    appointments_col.insert_one(appt_doc)

    # Award points for proactive preventive healthcare booking (+40 pts)
    wellness_col = get_collection("wellness_rewards")
    wellness = wellness_col.find_one({"user_id": current_user["_id"]})
    if wellness:
        new_points = wellness.get("total_points", 0) + 40
        wellness_col.update_one(
            {"user_id": current_user["_id"]},
            {
                "$set": {"total_points": new_points},
                "$push": {"completed_habits_today": f"Booked consultation with {doctor.get('name')}"}
            }
        )

    # Audit log
    logs_col = get_collection("audit_logs")
    logs_col.insert_one({
        "event": "APPOINTMENT_BOOKED",
        "appointment_id": appt_id,
        "patient_id": current_user["_id"],
        "doctor_id": appt_doc["doctor_id"],
        "timestamp": now
    })

    return {
        "message": "Appointment successfully booked.",
        "appointment": appt_doc
    }

@router.get("/")
async def list_appointments(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    scope: Optional[str] = Query("all", description="Scope: 'my' or 'all'"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    appointments_col = get_collection("appointments")
    
    if current_user["role"] == "patient":
        query = {"patient_id": current_user["_id"]}
        if status_filter and status_filter != "all":
            query["status"] = status_filter
        appts = list(appointments_col.find(query).sort("appointment_date", -1))
        return {"appointments": appts, "total": len(appts)}

    # Doctor or Admin
    doctors_col = get_collection("doctor_profiles")
    doc_prof = (
        doctors_col.find_one({"doctor_id": current_user["_id"]}) or
        doctors_col.find_one({"email": current_user.get("email")}) or
        doctors_col.find_one({"_id": current_user["_id"]})
    )
    doc_ids = {str(current_user["_id"])}
    if doc_prof:
        if doc_prof.get("doctor_id"): doc_ids.add(str(doc_prof["doctor_id"]))
        if doc_prof.get("_id"): doc_ids.add(str(doc_prof["_id"]))
    
    doc_name_clean = current_user.get("name", "").replace("Dr. ", "").strip().lower()

    base_query = {}
    if status_filter and status_filter != "all":
        base_query["status"] = status_filter

    raw_appts = list(appointments_col.find(base_query).sort("appointment_date", -1))

    processed = []
    for a in raw_appts:
        a_copy = dict(a)
        a_doc_id = str(a_copy.get("doctor_id", ""))
        a_doc_email = str(a_copy.get("doctor_email", "")).lower()
        a_doc_name = str(a_copy.get("doctor_name", "")).lower()
        
        is_mine = (
            a_doc_id in doc_ids or
            (current_user.get("email") and a_doc_email == current_user["email"].lower()) or
            (doc_name_clean and doc_name_clean in a_doc_name)
        )
        a_copy["is_my_appointment"] = is_mine
        a_copy["needs_checkup"] = (a_copy.get("status") == "confirmed")
        processed.append(a_copy)

    if scope == "my":
        my_only = [a for a in processed if a["is_my_appointment"]]
        if len(my_only) > 0:
            return {"appointments": my_only, "total": len(my_only)}

    return {"appointments": processed, "total": len(processed)}

@router.get("/{appointment_id}")
async def get_appointment(
    appointment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    appointments_col = get_collection("appointments")
    appt = appointments_col.find_one({"_id": appointment_id})
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    
    if current_user["role"] not in ["admin"] and appt["patient_id"] != current_user["_id"] and appt["doctor_id"] != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return {"appointment": appt}

@router.put("/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: str,
    status_update: AppointmentStatusUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    appointments_col = get_collection("appointments")
    appt = appointments_col.find_one({"_id": appointment_id})
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    # Patient can cancel, doctor can confirm/complete/cancel, admin can do all
    if current_user["role"] == "patient" and status_update.status != "cancelled":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patients can only cancel their appointments.")

    now = datetime.datetime.utcnow().isoformat()
    update_data = {
        "status": status_update.status,
        "updated_at": now
    }
    if status_update.cancellation_reason:
        update_data["cancellation_reason"] = status_update.cancellation_reason

    appointments_col.update_one({"_id": appointment_id}, {"$set": update_data})
    updated = appointments_col.find_one({"_id": appointment_id})

    return {"message": f"Appointment status updated to {status_update.status}", "appointment": updated}
