from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Auth Schemas ---
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field(default="patient", pattern="^(patient|doctor|admin)$")
    phone: Optional[str] = None
    # For doctors only:
    specialty: Optional[str] = "General Physician"
    qualification: Optional[str] = "MBBS, MD"
    experience_years: Optional[int] = 5
    consultation_fee: Optional[float] = 40.0

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

# --- Patient Profile ---
class PatientProfileUpdate(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    allergies: Optional[List[str]] = []
    chronic_conditions: Optional[List[str]] = []
    is_smoker: Optional[bool] = False
    physical_activity_level: Optional[str] = "moderate" # sedentary, light, moderate, active
    address: Optional[str] = None

# --- Doctor Profile ---
class DoctorProfileUpdate(BaseModel):
    specialty: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[float] = None
    bio: Optional[str] = None
    clinic_address: Optional[str] = None
    available_days: Optional[List[str]] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    time_slots: Optional[List[str]] = ["09:00 AM", "10:00 AM", "11:00 AM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM"]
    is_verified: Optional[bool] = None

# --- Vitals Schemas ---
class VitalsCreate(BaseModel):
    heart_rate: float = Field(..., ge=30, le=240, description="Beats per minute")
    blood_pressure_sys: float = Field(..., ge=60, le=260, description="Systolic mmHg")
    blood_pressure_dia: float = Field(..., ge=40, le=180, description="Diastolic mmHg")
    blood_glucose: float = Field(..., ge=40, le=500, description="Fasting/Random mg/dL")
    spo2: float = Field(..., ge=60, le=100, description="Blood oxygen percentage")
    body_temperature: float = Field(..., ge=34.0, le=43.0, description="Celsius")
    respiratory_rate: Optional[float] = Field(default=16.0, ge=8, le=60)
    device_source: Optional[str] = "Manual Entry" # Manual Entry, MediPulse Smartwatch, IoT Vitals Bedside, Clinical Monitor
    notes: Optional[str] = None

# --- Medical Report Schemas ---
class ReportCreate(BaseModel):
    title: str
    report_type: str # Blood Work, ECG, Lipid Panel, Glucose Tolerance, Chest X-Ray, General Health Checkup
    doctor_name: Optional[str] = None
    facility_name: Optional[str] = None
    report_date: Optional[str] = None
    notes: Optional[str] = None

# --- Appointment Schemas ---
class AppointmentCreate(BaseModel):
    doctor_id: str
    appointment_date: str # YYYY-MM-DD
    time_slot: str
    reason_for_visit: str
    symptoms: Optional[List[str]] = []
    consultation_type: Optional[str] = "Online Video" # Online Video, In-Clinic, Chat

class AppointmentStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|confirmed|completed|cancelled)$")
    cancellation_reason: Optional[str] = None

# --- Consultation & E-Prescription ---
class PrescriptionItem(BaseModel):
    medicine_name: str
    dosage: str
    frequency: str # e.g. "1-0-1 after food"
    duration_days: int
    instructions: Optional[str] = ""

class ConsultationCreate(BaseModel):
    appointment_id: str
    patient_id: str
    diagnosis: str
    symptoms_observed: Optional[List[str]] = []
    clinical_notes: str
    prescriptions: List[PrescriptionItem] = []
    dietary_advice: Optional[str] = ""
    lifestyle_recommendations: Optional[str] = ""
    follow_up_recommended: Optional[bool] = False
    follow_up_date: Optional[str] = None

# --- AI & ML Schemas ---
class HealthRiskInput(BaseModel):
    age: int = Field(default=35, ge=10, le=110)
    gender: str = "male" # male, female
    systolic_bp: float = Field(default=120, ge=60, le=250)
    diastolic_bp: float = Field(default=80, ge=40, le=160)
    blood_glucose: float = Field(default=95, ge=50, le=450)
    heart_rate: float = Field(default=72, ge=40, le=200)
    bmi: float = Field(default=23.5, ge=12, le=60)
    spo2: float = Field(default=98, ge=70, le=100)
    cholesterol: Optional[float] = Field(default=185, ge=100, le=400)
    is_smoker: bool = False
    physical_activity: str = "moderate" # sedentary, light, moderate, active
    family_history_diabetes: bool = False
    family_history_heart_disease: bool = False

class SymptomCheckerInput(BaseModel):
    symptoms: List[str]
    duration_days: Optional[int] = 2
    severity: Optional[str] = "moderate" # mild, moderate, severe
    additional_context: Optional[str] = None

# --- Wellness Schemas ---
class WellnessActivityLog(BaseModel):
    activity_type: str # vitals_logged, water_intake, daily_walk, medication_taken, mindfulness
    value: Optional[float] = 1.0
    notes: Optional[str] = None

class RewardClaim(BaseModel):
    reward_id: str
