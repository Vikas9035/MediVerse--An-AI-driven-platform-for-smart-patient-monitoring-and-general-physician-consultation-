from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from typing import Dict, Any, Optional, List
import datetime
import uuid
import os
from pathlib import Path

from app.database import get_collection
from app.config import UPLOAD_DIR
from app.auth.dependencies import get_current_user, get_current_active_patient
from app.ml.risk_models import ml_health_engine

router = APIRouter(prefix="/api/reports", tags=["Medical Reports"])

@router.post("/upload")
async def upload_medical_report(
    title: str = Form(...),
    report_type: str = Form(...),
    doctor_name: Optional[str] = Form(""),
    facility_name: Optional[str] = Form(""),
    report_date: Optional[str] = Form(""),
    notes: Optional[str] = Form(""),
    file: Optional[UploadFile] = File(None),
    current_user: Dict[str, Any] = Depends(get_current_active_patient)
):
    reports_col = get_collection("reports")
    report_id = uuid.uuid4().hex
    now = datetime.datetime.utcnow().isoformat()
    
    file_path_str = ""
    file_name_str = ""
    if file and file.filename:
        file_name_str = f"{report_id}_{file.filename}"
        dest_path = Path(UPLOAD_DIR) / file_name_str
        try:
            contents = await file.read()
            with open(dest_path, "wb") as f:
                f.write(contents)
            file_path_str = f"/uploads/{file_name_str}"
        except Exception as e:
            print(f"Error saving file: {e}")
    else:
        file_name_str = "digital_lab_panel.pdf"
        file_path_str = "/uploads/sample_report.pdf"

    # AI Analysis of the uploaded report
    ai_analysis = ml_health_engine.analyze_medical_report(
        report_title=title,
        report_type=report_type,
        text_content=notes or ""
    )

    report_doc = {
        "_id": report_id,
        "patient_id": current_user["_id"],
        "patient_name": current_user.get("name", "Patient"),
        "title": title,
        "report_type": report_type,
        "doctor_name": doctor_name or "Attending Physician",
        "facility_name": facility_name or "MediVerse Diagnostics & Clinical Labs",
        "report_date": report_date or datetime.date.today().isoformat(),
        "notes": notes or "",
        "file_url": file_path_str,
        "file_name": file_name_str,
        "ai_summary": ai_analysis["ai_clinical_summary"],
        "extracted_markers": ai_analysis["extracted_markers"],
        "abnormal_parameters_count": ai_analysis["abnormal_parameters_count"],
        "doctor_action_needed": ai_analysis["doctor_action_needed"],
        "status": "Verified & Analyzed",
        "created_at": now
    }

    reports_col.insert_one(report_doc)

    # Award wellness points for staying on top of medical documentation (+30 pts)
    wellness_col = get_collection("wellness_rewards")
    wellness = wellness_col.find_one({"user_id": current_user["_id"]})
    if wellness:
        new_points = wellness.get("total_points", 0) + 30
        wellness_col.update_one(
            {"user_id": current_user["_id"]},
            {
                "$set": {"total_points": new_points},
                "$push": {"completed_habits_today": f"Uploaded medical report: {title}"}
            }
        )

    return {
        "message": "Medical report successfully uploaded and analyzed by AI.",
        "report": report_doc
    }

@router.get("/")
async def list_reports(
    patient_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    target_patient_id = current_user["_id"]
    if current_user["role"] in ["doctor", "admin"] and patient_id:
        target_patient_id = patient_id

    reports_col = get_collection("reports")
    query = {"patient_id": patient_id} if patient_id else ({} if current_user["role"] in ["doctor", "admin"] else {"patient_id": current_user["_id"]})
    reports = list(reports_col.find(query).sort("created_at", -1))

    return {"reports": reports, "total": len(reports)}

@router.get("/{report_id}")
async def get_report_detail(
    report_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    reports_col = get_collection("reports")
    report = reports_col.find_one({"_id": report_id})
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    
    # Check permissions
    if current_user["role"] not in ["doctor", "admin"] and report["patient_id"] != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this report")

    return {"report": report}

@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    reports_col = get_collection("reports")
    report = reports_col.find_one({"_id": report_id})
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    
    if current_user["role"] != "admin" and report["patient_id"] != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete this report")

    reports_col.delete_one({"_id": report_id})
    return {"message": "Report deleted successfully"}
