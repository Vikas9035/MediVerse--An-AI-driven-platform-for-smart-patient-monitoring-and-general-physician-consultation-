import datetime
import uuid
from app.database import get_collection
from app.auth.security import get_password_hash

def seed_database_if_empty():
    users_col = get_collection("users")
    
    # Check if admin already exists
    if users_col.count_documents({"email": "admin@mediverse.health"}) > 0:
        return

    print("[SEED] Seeding MediVerse database with comprehensive demo accounts & clinical records...")
    now = datetime.datetime.utcnow()
    pwd_hash = get_password_hash("Password123!")
    admin_pwd_hash = get_password_hash("AdminPass123!")

    # 1. Admin Account
    admin_id = "user_admin_01"
    users_col.insert_one({
        "_id": admin_id,
        "name": "Platform Administrator",
        "email": "admin@mediverse.health",
        "password_hash": admin_pwd_hash,
        "role": "admin",
        "phone": "+1 (555) 019-2834",
        "is_active": True,
        "created_at": (now - datetime.timedelta(days=60)).isoformat(),
        "updated_at": now.isoformat()
    })

    # 2. Doctors
    doctors_info = [
        {
            "id": "doc_sarah_01",
            "name": "Dr. Sarah Chen, MD",
            "email": "doctor.sarah@mediverse.health",
            "specialty": "General Physician",
            "qualification": "MD - Internal Medicine, Harvard Medical School",
            "experience_years": 11,
            "consultation_fee": 50.0,
            "rating": 4.96,
            "total_reviews": 68,
            "bio": "Senior General Physician specializing in preventive medicine, continuous vital monitoring, metabolic health, and patient-centered lifestyle interventions.",
            "is_verified": True,
            "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "time_slots": ["09:00 AM", "10:30 AM", "12:00 PM", "02:30 PM", "04:00 PM", "05:30 PM"]
        },
        {
            "id": "doc_marcus_02",
            "name": "Dr. Marcus Vance, MD, FACC",
            "email": "doctor.marcus@mediverse.health",
            "specialty": "Cardiologist",
            "qualification": "MD - Cardiology, Johns Hopkins Medicine",
            "experience_years": 14,
            "consultation_fee": 75.0,
            "rating": 4.92,
            "total_reviews": 84,
            "bio": "Cardiovascular specialist focused on early hypertension detection, heart failure prevention, lipidology, and digital wearable telemetry monitoring.",
            "is_verified": True,
            "available_days": ["Monday", "Wednesday", "Thursday", "Saturday"],
            "time_slots": ["10:00 AM", "11:30 AM", "02:00 PM", "03:30 PM", "05:00 PM"]
        },
        {
            "id": "doc_priya_03",
            "name": "Dr. Priya Patel, MD",
            "email": "doctor.priya@mediverse.health",
            "specialty": "Endocrinologist",
            "qualification": "MD, DM - Endocrinology, Stanford Health",
            "experience_years": 9,
            "consultation_fee": 65.0,
            "rating": 4.88,
            "total_reviews": 52,
            "bio": "Consultant endocrinologist with special interest in Type 2 Diabetes reversal strategies, thyroid disorders, and preventive metabolic wellness.",
            "is_verified": True,
            "available_days": ["Tuesday", "Wednesday", "Friday", "Saturday"],
            "time_slots": ["09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"]
        }
    ]

    doctors_col = get_collection("doctor_profiles")
    for doc in doctors_info:
        users_col.insert_one({
            "_id": doc["id"],
            "name": doc["name"],
            "email": doc["email"],
            "password_hash": pwd_hash,
            "role": "doctor",
            "phone": "+1 (555) 234-8901",
            "is_active": True,
            "created_at": (now - datetime.timedelta(days=45)).isoformat(),
            "updated_at": now.isoformat()
        })
        doctors_col.insert_one({
            "_id": doc["id"],
            "doctor_id": doc["id"],
            "name": doc["name"],
            "email": doc["email"],
            "specialty": doc["specialty"],
            "qualification": doc["qualification"],
            "experience_years": doc["experience_years"],
            "consultation_fee": doc["consultation_fee"],
            "rating": doc["rating"],
            "total_reviews": doc["total_reviews"],
            "bio": doc["bio"],
            "is_verified": doc["is_verified"],
            "available_days": doc["available_days"],
            "time_slots": doc["time_slots"],
            "created_at": (now - datetime.timedelta(days=45)).isoformat()
        })

    # 3. Patient Account
    patient_id = "user_patient_alex"
    users_col.insert_one({
        "_id": patient_id,
        "name": "Alexander Wright",
        "email": "patient@mediverse.health",
        "password_hash": pwd_hash,
        "role": "patient",
        "phone": "+1 (555) 789-4321",
        "is_active": True,
        "created_at": (now - datetime.timedelta(days=30)).isoformat(),
        "updated_at": now.isoformat()
    })

    profiles_col = get_collection("patient_profiles")
    profiles_col.insert_one({
        "_id": patient_id,
        "patient_id": patient_id,
        "name": "Alexander Wright",
        "email": "patient@mediverse.health",
        "age": 38,
        "gender": "Male",
        "blood_group": "A+",
        "height_cm": 178.0,
        "weight_kg": 76.5,
        "bmi": 24.1,
        "allergies": ["Penicillin", "Dust Mites"],
        "chronic_conditions": ["Mild Essential Hypertension (Controlled)"],
        "is_smoker": False,
        "physical_activity_level": "moderate",
        "emergency_contact_name": "Eleanor Wright (Spouse)",
        "emergency_contact_phone": "+1 (555) 789-4322",
        "address": "742 Evergreen Terrace, Springfield",
        "created_at": (now - datetime.timedelta(days=30)).isoformat()
    })

    # 4. Patient Wellness Rewards Record
    wellness_col = get_collection("wellness_rewards")
    wellness_col.insert_one({
        "_id": patient_id,
        "user_id": patient_id,
        "total_points": 340,
        "current_streak_days": 6,
        "tier": "Silver",
        "completed_habits_today": [
            "Hydration Goal (2L Water)",
            "Daily Vitals Checked & Recorded"
        ],
        "earned_badges": [
            {
                "name": "MediVerse Pioneer",
                "icon": "Award",
                "description": "Joined the smart healthcare platform",
                "earned_at": (now - datetime.timedelta(days=30)).isoformat()
            },
            {
                "name": "Vitals Vigilant",
                "icon": "Heart",
                "description": "Consistently logged vitals for 5 consecutive days",
                "earned_at": (now - datetime.timedelta(days=10)).isoformat()
            },
            {
                "name": "Silver Health Advocate",
                "icon": "ShieldCheck",
                "description": "Surpassed 250 wellness points through preventive care",
                "earned_at": (now - datetime.timedelta(days=2)).isoformat()
            }
        ],
        "claimed_rewards": [
            {
                "claim_id": "claim_001",
                "reward_id": "rew_1",
                "title": "$15 Off Physician Teleconsultation",
                "voucher_code": "MV-PERK-A93K2F",
                "points_spent": 150,
                "claimed_at": (now - datetime.timedelta(days=7)).isoformat()
            }
        ],
        "updated_at": now.isoformat()
    })

    # 5. Seed Vitals History (7 Days of realistic time-series vitals)
    vitals_col = get_collection("vitals")
    vitals_samples = [
        {"days_ago": 6, "hr": 74, "sys": 126, "dia": 82, "glu": 98, "spo2": 98.5, "temp": 36.7, "source": "MediPulse Smartwatch"},
        {"days_ago": 5, "hr": 71, "sys": 124, "dia": 80, "glu": 94, "spo2": 99.0, "temp": 36.6, "source": "MediPulse Smartwatch"},
        {"days_ago": 4, "hr": 78, "sys": 132, "dia": 84, "glu": 104, "spo2": 98.0, "temp": 36.8, "source": "Manual Entry"},
        {"days_ago": 3, "hr": 69, "sys": 122, "dia": 79, "glu": 92, "spo2": 99.0, "temp": 36.5, "source": "MediPulse Smartwatch"},
        {"days_ago": 2, "hr": 75, "sys": 128, "dia": 83, "glu": 101, "spo2": 98.5, "temp": 36.7, "source": "IoT Bedside Monitor"},
        {"days_ago": 1, "hr": 72, "sys": 121, "dia": 79, "glu": 95, "spo2": 99.0, "temp": 36.6, "source": "MediPulse Smartwatch"},
        {"days_ago": 0, "hr": 70, "sys": 120, "dia": 78, "glu": 93, "spo2": 99.2, "temp": 36.7, "source": "MediPulse Smartwatch (Live)"}
    ]

    for v in vitals_samples:
        rec_time = now - datetime.timedelta(days=v["days_ago"], hours=4, minutes=15)
        vitals_col.insert_one({
            "_id": uuid.uuid4().hex,
            "patient_id": patient_id,
            "patient_name": "Alexander Wright",
            "heart_rate": float(v["hr"]),
            "blood_pressure_sys": float(v["sys"]),
            "blood_pressure_dia": float(v["dia"]),
            "blood_glucose": float(v["glu"]),
            "spo2": float(v["spo2"]),
            "body_temperature": float(v["temp"]),
            "respiratory_rate": 16.0,
            "device_source": v["source"],
            "notes": "Daily morning monitoring reading",
            "anomaly_status": "Normal",
            "is_anomaly": False,
            "is_critical": False,
            "anomaly_issues": [],
            "recorded_at": rec_time.isoformat()
        })

    # 6. Seed Medical Reports
    reports_col = get_collection("reports")
    reports_col.insert_one({
        "_id": "rep_cbc_01",
        "patient_id": patient_id,
        "patient_name": "Alexander Wright",
        "title": "Comprehensive Metabolic & Lipid Panel",
        "report_type": "Blood Work",
        "doctor_name": "Dr. Sarah Chen, MD",
        "facility_name": "MediVerse Diagnostics Central",
        "report_date": (now - datetime.timedelta(days=12)).strftime("%Y-%m-%d"),
        "notes": "Annual preventive screening panel.",
        "file_url": "/uploads/metabolic_panel.pdf",
        "file_name": "metabolic_panel.pdf",
        "ai_summary": "Overall metabolic profile is in solid condition. Fasting glucose (94 mg/dL) is within normal limits. Lipid panel shows total cholesterol at 198 mg/dL and HDL at 52 mg/dL. Renal and liver enzymes are optimal.",
        "extracted_markers": [
            {"parameter": "Fasting Plasma Glucose", "value": "94 mg/dL", "reference": "70 - 99 mg/dL", "status": "Normal"},
            {"parameter": "Total Cholesterol", "value": "198 mg/dL", "reference": "< 200 mg/dL", "status": "Optimal"},
            {"parameter": "HDL Cholesterol", "value": "52 mg/dL", "reference": "> 40 mg/dL", "status": "Optimal"},
            {"parameter": "LDL Cholesterol", "value": "118 mg/dL", "reference": "< 100 mg/dL", "status": "Borderline"},
            {"parameter": "HbA1c", "value": "5.4%", "reference": "< 5.7%", "status": "Normal"}
        ],
        "abnormal_parameters_count": 1,
        "doctor_action_needed": False,
        "status": "Verified & Analyzed",
        "created_at": (now - datetime.timedelta(days=12)).isoformat()
    })

    reports_col.insert_one({
        "_id": "rep_ecg_02",
        "patient_id": patient_id,
        "patient_name": "Alexander Wright",
        "title": "12-Lead Rest ECG Cardiac Evaluation",
        "report_type": "ECG",
        "doctor_name": "Dr. Marcus Vance, MD",
        "facility_name": "Cardiology Center of Excellence",
        "report_date": (now - datetime.timedelta(days=22)).strftime("%Y-%m-%d"),
        "notes": "Routine cardiovascular assessment.",
        "file_url": "/uploads/ecg_evaluation.pdf",
        "file_name": "ecg_evaluation.pdf",
        "ai_summary": "Electrocardiogram confirms normal sinus rhythm at 68 bpm. PR and QT intervals are within standard physiologic limits. No evidence of ventricular hypertrophy or acute ischemic ST changes.",
        "extracted_markers": [
            {"parameter": "Heart Rhythm", "value": "Sinus Rhythm", "reference": "Sinus Rhythm", "status": "Normal"},
            {"parameter": "Resting Heart Rate", "value": "68 bpm", "reference": "60 - 100 bpm", "status": "Normal"},
            {"parameter": "PR Interval", "value": "152 ms", "reference": "120 - 200 ms", "status": "Normal"},
            {"parameter": "QTc Interval", "value": "408 ms", "reference": "< 450 ms", "status": "Normal"}
        ],
        "abnormal_parameters_count": 0,
        "doctor_action_needed": False,
        "status": "Verified & Analyzed",
        "created_at": (now - datetime.timedelta(days=22)).isoformat()
    })

    # 7. Seed Appointments
    appts_col = get_collection("appointments")
    upcoming_date = (now + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
    past_date = (now - datetime.timedelta(days=10)).strftime("%Y-%m-%d")

    # Upcoming Appointment
    appts_col.insert_one({
        "_id": "appt_up_01",
        "patient_id": patient_id,
        "patient_name": "Alexander Wright",
        "patient_email": "patient@mediverse.health",
        "doctor_id": "doc_sarah_01",
        "doctor_name": "Dr. Sarah Chen, MD",
        "doctor_specialty": "General Physician",
        "consultation_fee": 50.0,
        "appointment_date": upcoming_date,
        "time_slot": "10:30 AM",
        "reason_for_visit": "Routine general health follow-up and discussion of recent smartwatch vitals trends.",
        "symptoms": ["Occasional fatigue", "Mild work stress"],
        "consultation_type": "Online Video",
        "status": "confirmed",
        "meeting_link": "https://meet.mediverse.health/room-alex-sarah",
        "created_at": (now - datetime.timedelta(days=2)).isoformat(),
        "updated_at": (now - datetime.timedelta(days=2)).isoformat()
    })

    # Completed Appointment & Consultation Record
    appts_col.insert_one({
        "_id": "appt_past_01",
        "patient_id": patient_id,
        "patient_name": "Alexander Wright",
        "patient_email": "patient@mediverse.health",
        "doctor_id": "doc_sarah_01",
        "doctor_name": "Dr. Sarah Chen, MD",
        "doctor_specialty": "General Physician",
        "consultation_fee": 50.0,
        "appointment_date": past_date,
        "time_slot": "02:30 PM",
        "reason_for_visit": "Mild seasonal allergy flare-up and review of blood pressure baseline.",
        "symptoms": ["Sneezing", "Nasal congestion"],
        "consultation_type": "Online Video",
        "status": "completed",
        "consultation_id": "cons_alex_01",
        "meeting_link": "https://meet.mediverse.health/room-alex-archive",
        "created_at": (now - datetime.timedelta(days=12)).isoformat(),
        "updated_at": (now - datetime.timedelta(days=10)).isoformat()
    })

    consultations_col = get_collection("consultations")
    consultations_col.insert_one({
        "_id": "cons_alex_01",
        "appointment_id": "appt_past_01",
        "patient_id": patient_id,
        "patient_name": "Alexander Wright",
        "doctor_id": "doc_sarah_01",
        "doctor_name": "Dr. Sarah Chen, MD",
        "doctor_specialty": "General Physician",
        "diagnosis": "Allergic Rhinitis & Optimal Blood Pressure Control",
        "symptoms_observed": ["Mild nasal mucosal swelling", "Clear rhinorrhea"],
        "clinical_notes": "Patient is in excellent overall spirits. Resting vitals recorded during consultation: BP 122/80 mmHg, HR 72 bpm. Symptoms are consistent with environmental pollen allergy. Advised non-sedating antihistamines and saline nasal irrigation.",
        "prescriptions": [
            {
                "medicine_name": "Cetirizine 10mg Tablets",
                "dosage": "1 tablet",
                "frequency": "Once daily at bedtime",
                "duration_days": 10,
                "instructions": "Non-drowsy formulation. Avoid alcohol."
            },
            {
                "medicine_name": "Fluticasone Propionate Nasal Spray",
                "dosage": "2 sprays per nostril",
                "frequency": "Once daily in the morning",
                "duration_days": 14,
                "instructions": "Shake well before use."
            }
        ],
        "dietary_advice": "Maintain hydration with warm herbal teas, boost vitamin C intake from citrus fruits and bell peppers.",
        "lifestyle_recommendations": "Keep bedroom windows closed during peak pollen morning hours. Continue daily 30-minute moderate walks.",
        "follow_up_recommended": True,
        "follow_up_date": upcoming_date,
        "created_at": (now - datetime.timedelta(days=10)).isoformat()
    })

    # 8. Audit Logs
    logs_col = get_collection("audit_logs")
    logs_col.insert_one({
        "event": "DATABASE_INITIALIZED",
        "detail": "MediVerse seed accounts and UN SDG 3 health profiles generated",
        "timestamp": now.isoformat()
    })

    print("[SEED] Database successfully seeded with Doctors, Patient profile, Vitals, Reports, and Appointments.")
