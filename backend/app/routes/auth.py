from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
import datetime
import uuid

from app.database import get_collection
from app.auth.security import get_password_hash, verify_password, create_access_token
from app.auth.dependencies import get_current_user
from app.models.schemas import UserRegister, UserLogin, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
async def register(user_in: UserRegister):
    users_col = get_collection("users")
    
    # Check if user already exists
    existing = users_col.find_one({"email": user_in.email.lower()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )
    
    user_id = uuid.uuid4().hex
    hashed_pwd = get_password_hash(user_in.password)
    now = datetime.datetime.utcnow().isoformat()
    
    user_doc = {
        "_id": user_id,
        "name": user_in.name,
        "email": user_in.email.lower(),
        "password_hash": hashed_pwd,
        "role": user_in.role,
        "phone": user_in.phone or "",
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    
    users_col.insert_one(user_doc)
    
    # If patient, initialize patient profile & wellness account
    if user_in.role == "patient":
        profiles_col = get_collection("patient_profiles")
        profiles_col.insert_one({
            "_id": user_id,
            "patient_id": user_id,
            "name": user_in.name,
            "email": user_in.email.lower(),
            "age": 32,
            "gender": "Other",
            "blood_group": "O+",
            "height_cm": 172.0,
            "weight_kg": 68.0,
            "bmi": 23.0,
            "allergies": [],
            "chronic_conditions": [],
            "is_smoker": False,
            "physical_activity_level": "moderate",
            "emergency_contact_name": "",
            "emergency_contact_phone": "",
            "created_at": now
        })
        
        # Initialize wellness rewards
        wellness_col = get_collection("wellness_rewards")
        wellness_col.insert_one({
            "_id": user_id,
            "user_id": user_id,
            "total_points": 100, # Welcome bonus!
            "current_streak_days": 1,
            "tier": "Bronze",
            "completed_habits_today": ["welcome_signup"],
            "earned_badges": ["MediVerse Welcome Pioneer"],
            "claimed_rewards": [],
            "updated_at": now
        })
        
    elif user_in.role == "doctor":
        doctors_col = get_collection("doctor_profiles")
        doctors_col.insert_one({
            "_id": user_id,
            "doctor_id": user_id,
            "name": user_in.name,
            "email": user_in.email.lower(),
            "specialty": user_in.specialty or "General Physician",
            "qualification": user_in.qualification or "MBBS, MD (General Medicine)",
            "experience_years": user_in.experience_years or 5,
            "consultation_fee": user_in.consultation_fee or 40.0,
            "rating": 4.9,
            "total_reviews": 18,
            "bio": f"Dedicated {user_in.specialty or 'General Physician'} focusing on preventive healthcare, continuous monitoring, and evidence-based medicine.",
            "is_verified": True,
            "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "time_slots": ["09:00 AM", "10:30 AM", "12:00 PM", "02:30 PM", "04:00 PM", "05:30 PM"],
            "created_at": now
        })
    
    # Audit log
    logs_col = get_collection("audit_logs")
    logs_col.insert_one({
        "event": "USER_REGISTERED",
        "user_id": user_id,
        "email": user_in.email.lower(),
        "role": user_in.role,
        "timestamp": now
    })
    
    access_token = create_access_token({"sub": user_id, "role": user_in.role, "email": user_in.email.lower()})
    
    safe_user = {k: v for k, v in user_doc.items() if k != "password_hash"}
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": safe_user
    }

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    users_col = get_collection("users")
    user = users_col.find_one({"email": credentials.email.lower()})
    
    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password. Please verify your credentials.",
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Please contact support.",
        )
        
    access_token = create_access_token({"sub": user["_id"], "role": user.get("role", "patient"), "email": user["email"]})
    
    # Audit log
    logs_col = get_collection("audit_logs")
    logs_col.insert_one({
        "event": "USER_LOGIN",
        "user_id": user["_id"],
        "email": user["email"],
        "role": user.get("role"),
        "timestamp": datetime.datetime.utcnow().isoformat()
    })
    
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": safe_user
    }

@router.get("/me")
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    safe_user = {k: v for k, v in current_user.items() if k != "password_hash"}
    return {"user": safe_user}
