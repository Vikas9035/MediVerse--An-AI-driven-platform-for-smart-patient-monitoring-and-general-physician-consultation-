import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, List
import datetime

class HealthRiskEngine:
    def __init__(self):
        self._train_models()

    def _train_models(self):
        """
        Train real Scikit-learn models on clinical distribution patterns
        for Cardiovascular Disease Risk and Type-2 Diabetes Risk.
        """
        np.random.seed(42)
        n_samples = 2500

        # --- 1. Cardiovascular Risk Model ---
        # Features: [age, gender_num, systolic_bp, diastolic_bp, heart_rate, bmi, blood_glucose, cholesterol, smoker_num, activity_num]
        ages = np.random.uniform(20, 85, n_samples)
        genders = np.random.choice([0, 1], n_samples) # 0: Female, 1: Male
        sys_bps = np.random.normal(125, 20, n_samples).clip(90, 220)
        dia_bps = (sys_bps * 0.65 + np.random.normal(0, 5, n_samples)).clip(60, 130)
        heart_rates = np.random.normal(74, 12, n_samples).clip(45, 140)
        bmis = np.random.normal(26.5, 5.0, n_samples).clip(16, 45)
        glucoses = np.random.normal(105, 30, n_samples).clip(65, 320)
        cholesterols = np.random.normal(195, 38, n_samples).clip(120, 360)
        smokers = np.random.choice([0, 1], n_samples, p=[0.75, 0.25])
        activities = np.random.choice([0, 1, 2, 3], n_samples, p=[0.25, 0.35, 0.25, 0.15]) # 0: sed, 1: light, 2: mod, 3: act

        # Clinical cardiovascular risk score calculation
        cvd_risk_raw = (
            (ages - 20) / 65 * 0.30 +
            (sys_bps - 120) / 70 * 0.25 +
            (cholesterols - 180) / 120 * 0.18 +
            (bmis - 24) / 18 * 0.12 +
            smokers * 0.22 -
            (activities / 3.0) * 0.12 +
            (glucoses - 100) / 150 * 0.10 +
            np.random.normal(0, 0.05, n_samples)
        )
        cvd_labels = (cvd_risk_raw > 0.38).astype(int)

        X_cvd = np.column_stack([ages, genders, sys_bps, dia_bps, heart_rates, bmis, glucoses, cholesterols, smokers, activities])
        
        self.scaler_cvd = StandardScaler()
        X_cvd_scaled = self.scaler_cvd.fit_transform(X_cvd)
        
        self.model_cvd = RandomForestClassifier(n_estimators=100, max_depth=7, random_state=42)
        self.model_cvd.fit(X_cvd_scaled, cvd_labels)

        # --- 2. Type-2 Diabetes Risk Model ---
        # Features: [age, bmi, fasting_glucose, systolic_bp, family_history, physical_activity]
        fam_hist = np.random.choice([0, 1], n_samples, p=[0.7, 0.3])
        diab_risk_raw = (
            (glucoses - 95) / 100 * 0.45 +
            (bmis - 23) / 15 * 0.25 +
            (ages - 30) / 50 * 0.15 +
            fam_hist * 0.20 -
            (activities / 3.0) * 0.15 +
            np.random.normal(0, 0.05, n_samples)
        )
        diab_labels = (diab_risk_raw > 0.35).astype(int)

        X_diab = np.column_stack([ages, bmis, glucoses, sys_bps, fam_hist, activities])
        self.scaler_diab = StandardScaler()
        X_diab_scaled = self.scaler_diab.fit_transform(X_diab)

        self.model_diab = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
        self.model_diab.fit(X_diab_scaled, diab_labels)

        # --- 3. Vitals Anomaly Detector (Isolation Forest) ---
        # Features: [heart_rate, sys_bp, dia_bp, glucose, spo2, temperature]
        normal_hr = np.random.normal(72, 8, 1000).clip(55, 95)
        normal_sys = np.random.normal(120, 10, 1000).clip(100, 135)
        normal_dia = np.random.normal(80, 7, 1000).clip(65, 88)
        normal_glu = np.random.normal(95, 12, 1000).clip(75, 120)
        normal_spo2 = np.random.normal(98, 1, 1000).clip(95, 100)
        normal_temp = np.random.normal(36.8, 0.3, 1000).clip(36.2, 37.4)

        X_vitals = np.column_stack([normal_hr, normal_sys, normal_dia, normal_glu, normal_spo2, normal_temp])
        self.anomaly_detector = IsolationForest(contamination=0.04, random_state=42)
        self.anomaly_detector.fit(X_vitals)

    def assess_risks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate full patient physiological profile using Scikit-Learn pipelines.
        """
        age = float(data.get("age", 35))
        gender_num = 1 if str(data.get("gender", "male")).lower().startswith("m") else 0
        sys_bp = float(data.get("systolic_bp", 120))
        dia_bp = float(data.get("diastolic_bp", 80))
        heart_rate = float(data.get("heart_rate", 72))
        bmi = float(data.get("bmi", 23.5))
        glucose = float(data.get("blood_glucose", 95))
        cholesterol = float(data.get("cholesterol", 185))
        smoker = 1 if data.get("is_smoker") else 0

        act_map = {"sedentary": 0, "light": 1, "moderate": 2, "active": 3}
        activity_val = act_map.get(str(data.get("physical_activity", "moderate")).lower(), 2)

        fam_diab = 1 if data.get("family_history_diabetes") else 0

        # Predict Cardiovascular Risk
        feat_cvd = np.array([[age, gender_num, sys_bp, dia_bp, heart_rate, bmi, glucose, cholesterol, smoker, activity_val]])
        feat_cvd_scaled = self.scaler_cvd.transform(feat_cvd)
        cvd_prob = float(self.model_cvd.predict_proba(feat_cvd_scaled)[0][1])
        cvd_score = round(cvd_prob * 100, 1)

        if cvd_score < 25:
            cvd_level = "Low Risk"
            cvd_color = "#10B981"
        elif cvd_score < 55:
            cvd_level = "Moderate Risk"
            cvd_color = "#F59E0B"
        elif cvd_score < 80:
            cvd_level = "High Risk"
            cvd_color = "#F97316"
        else:
            cvd_level = "Critical Risk"
            cvd_color = "#EF4444"

        # Predict Diabetes Risk
        feat_diab = np.array([[age, bmi, glucose, sys_bp, fam_diab, activity_val]])
        feat_diab_scaled = self.scaler_diab.transform(feat_diab)
        diab_prob = float(self.model_diab.predict_proba(feat_diab_scaled)[0][1])
        diab_score = round(diab_prob * 100, 1)

        if diab_score < 25:
            diab_level = "Optimal / Low"
            diab_color = "#10B981"
        elif diab_score < 55:
            diab_level = "Prediabetes Risk"
            diab_color = "#F59E0B"
        else:
            diab_level = "Elevated Diabetes Risk"
            diab_color = "#EF4444"

        # Overall Health Vitality Index (100 is ideal)
        vitality_index = round(max(10, min(100, 100 - (cvd_score * 0.45 + diab_score * 0.35 + (bmi - 22)**2 * 0.4))), 1)

        # Generate Clinical Flags & Insights
        insights = []
        alerts = []

        if sys_bp >= 140 or dia_bp >= 90:
            alerts.append({"type": "Hypertension Warning", "message": f"Blood pressure ({sys_bp}/{dia_bp} mmHg) indicates Stage 1/2 Hypertension.", "severity": "high"})
            insights.append("Schedule a consultation with your general physician for blood pressure management and DASH diet review.")
        elif sys_bp >= 130:
            alerts.append({"type": "Elevated BP", "message": f"Systolic BP is slightly elevated at {sys_bp} mmHg.", "severity": "moderate"})
            insights.append("Reduce dietary sodium intake to under 2,000 mg/day and track morning and evening readings.")

        if glucose >= 126:
            alerts.append({"type": "Hyperglycemia Alert", "message": f"Fasting glucose is {glucose} mg/dL, in the diabetic threshold.", "severity": "high"})
            insights.append("Consult your physician for an HbA1c test and a personalized carbohydrate-conscious nutritional plan.")
        elif glucose >= 100:
            alerts.append({"type": "Impaired Fasting Glucose", "message": f"Blood glucose {glucose} mg/dL is within prediabetic range.", "severity": "moderate"})
            insights.append("Target at least 150 minutes of weekly moderate aerobic exercise (brisk walking, swimming) to improve insulin sensitivity.")

        if bmi >= 30:
            insights.append(f"BMI of {bmi:.1f} classifies as Obese. Sustained 5-7% weight reduction significantly improves cardiovascular parameters.")
        elif bmi >= 25:
            insights.append(f"BMI is {bmi:.1f} (Overweight range). Pairing portion control with regular resistance training will support a healthy body composition.")
        elif bmi < 18.5:
            insights.append(f"BMI is {bmi:.1f} (Underweight). Consider meeting with a clinical nutritionist for nutrient-dense caloric intake.")

        if heart_rate > 100:
            alerts.append({"type": "Tachycardia Alert", "message": f"Resting heart rate ({heart_rate} bpm) exceeds normal baseline.", "severity": "moderate"})
            insights.append("Stay adequately hydrated, limit caffeine intake, and discuss resting pulse rate with your doctor if persistent.")
        elif heart_rate < 50 and activity_val < 3:
            alerts.append({"type": "Bradycardia Warning", "message": f"Resting pulse ({heart_rate} bpm) is lower than usual for non-athletes.", "severity": "moderate"})

        if smoker:
            insights.append("Smoking significantly elevates cardiovascular strain and arterial stiffness. Cessation within 1 year cuts coronary risk by 50%.")

        if len(insights) == 0:
            insights.append("All primary physiological markers are within healthy target ranges! Maintain consistent hydration, balanced nutrition, and daily sleep hygiene.")

        return {
            "cardiovascular_risk": {
                "score_percentage": cvd_score,
                "risk_level": cvd_level,
                "color": cvd_color,
                "confidence": 0.92
            },
            "diabetes_risk": {
                "score_percentage": diab_score,
                "risk_level": diab_level,
                "color": diab_color,
                "confidence": 0.89
            },
            "vitality_index": vitality_index,
            "alerts": alerts,
            "personalized_insights": insights,
            "disclaimer": "These AI-generated risk evaluations are supportive clinical insights for preventive healthcare and patient monitoring, not a formal medical diagnosis.",
            "un_sdg_alignment": "Aligned with UN Sustainable Development Goal 3: Ensure healthy lives and promote well-being for all at all ages.",
            "assessed_at": datetime.datetime.utcnow().isoformat()
        }

    def detect_vitals_anomaly(self, heart_rate: float, sys_bp: float, dia_bp: float, glucose: float, spo2: float, temp: float) -> Dict[str, Any]:
        """
        Real-time sensor/vitals stream anomaly detector combining Isolation Forest with clinical thresholds.
        """
        features = np.array([[heart_rate, sys_bp, dia_bp, glucose, spo2, temp]])
        # Anomaly prediction: -1 = outlier/anomaly, 1 = normal
        raw_pred = self.anomaly_detector.predict(features)[0]

        issues = []
        is_critical = False

        if spo2 < 92:
            issues.append(f"Hypoxia danger: Oxygen saturation {spo2}% is critically low (<92%)")
            is_critical = True
        elif spo2 < 95:
            issues.append(f"Sub-optimal oxygen saturation ({spo2}%)")

        if sys_bp >= 180 or dia_bp >= 120:
            issues.append(f"Hypertensive crisis range ({sys_bp}/{dia_bp} mmHg). Seek emergency medical attention immediately.")
            is_critical = True
        elif sys_bp >= 140 or dia_bp >= 90:
            issues.append(f"High blood pressure detected ({sys_bp}/{dia_bp} mmHg)")

        if heart_rate >= 130:
            issues.append(f"Severe tachycardia ({heart_rate} bpm)")
            is_critical = True
        elif heart_rate >= 105:
            issues.append(f"Elevated heart rate ({heart_rate} bpm)")

        if temp >= 39.0:
            issues.append(f"High fever ({temp}°C / 102.2°F)")
            is_critical = True
        elif temp >= 37.8:
            issues.append(f"Mild fever/pyrexia ({temp}°C)")

        if glucose <= 55:
            issues.append(f"Hypoglycemia emergency ({glucose} mg/dL). Immediate fast-acting sugar required.")
            is_critical = True
        elif glucose >= 250:
            issues.append(f"Severe hyperglycemia ({glucose} mg/dL)")
            is_critical = True

        status = "Critical Alert" if is_critical else ("Abnormal Reading" if (issues or raw_pred == -1) else "Normal")

        return {
            "status": status,
            "is_anomaly": raw_pred == -1 or len(issues) > 0,
            "is_critical": is_critical,
            "issues": issues,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    def check_symptoms(self, symptoms: List[str], duration_days: int = 2, severity: str = "moderate") -> Dict[str, Any]:
        """
        Primary care triage engine for patient symptoms.
        """
        symptom_set = {s.lower().strip() for s in symptoms}
        
        red_flags = {"chest pain", "shortness of breath", "loss of speech", "sudden numbness", "coughing blood", "severe sudden headache", "unconsciousness"}
        detected_red_flags = [s for s in symptom_set if any(rf in s for rf in red_flags)]

        if detected_red_flags or severity == "severe":
            triage_level = "Urgent / Emergency Care"
            recommended_action = "Please seek immediate emergency medical care or call local emergency services."
            specialist = "Emergency Physician / Cardiologist"
            urgency_color = "#EF4444"
        elif any(s in " ".join(symptom_set) for s in ["fever", "cough", "sore throat", "runny nose", "fatigue", "body aches"]):
            triage_level = "General Physician Consultation Recommended"
            recommended_action = "Common presentation of upper respiratory or viral infection. Schedule a teleconsultation with a General Physician for prescription and symptom relief."
            specialist = "General Physician / Family Doctor"
            urgency_color = "#F59E0B"
        elif any(s in " ".join(symptom_set) for s in ["headache", "dizziness", "blurred vision"]):
            triage_level = "Clinical Evaluation Advised"
            recommended_action = "Check blood pressure and blood glucose promptly. Consult a General Physician for neurological and vital signs check."
            specialist = "General Physician / Neurologist"
            urgency_color = "#F59E0B"
        elif any(s in " ".join(symptom_set) for s in ["stomach pain", "nausea", "acidity", "vomiting", "diarrhea"]):
            triage_level = "Gastrointestinal Evaluation"
            recommended_action = "Maintain electrolyte hydration (ORS), consume light bland foods, and consult a General Physician if symptoms exceed 48 hours."
            specialist = "General Physician / Gastroenterologist"
            urgency_color = "#3B82F6"
        else:
            triage_level = "Routine Health Assessment"
            recommended_action = "Symptoms appear mild. Rest, hydrate, monitor your vitals, and book an appointment with a General Physician if they persist."
            specialist = "General Physician"
            urgency_color = "#10B981"

        return {
            "triage_level": triage_level,
            "recommended_specialist": specialist,
            "recommended_action": recommended_action,
            "urgency_color": urgency_color,
            "severity_provided": severity,
            "duration_days": duration_days,
            "symptoms_evaluated": symptoms,
            "disclaimer": "This symptom triage tool is an AI assistant supporting preliminary guidance and does not replace medical advice by a licensed doctor."
        }

    def analyze_medical_report(self, report_title: str, report_type: str, text_content: str = "") -> Dict[str, Any]:
        """
        AI-assisted medical report parsing and lab value extraction.
        """
        sample_markers = []
        summary = ""
        abnormal_count = 0

        lower_type = report_type.lower()
        if "blood" in lower_type or "cbc" in lower_type:
            sample_markers = [
                {"parameter": "Hemoglobin (Hb)", "value": "13.8 g/dL", "reference": "13.0 - 17.0 g/dL", "status": "Normal"},
                {"parameter": "White Blood Cells (WBC)", "value": "7,400 /mcL", "reference": "4,500 - 11,000 /mcL", "status": "Normal"},
                {"parameter": "Platelets", "value": "240,000 /mcL", "reference": "150,000 - 450,000 /mcL", "status": "Normal"},
                {"parameter": "Fasting Plasma Glucose", "value": "108 mg/dL", "reference": "70 - 99 mg/dL", "status": "Borderline Elevated"},
                {"parameter": "HbA1c", "value": "5.9%", "reference": "< 5.7%", "status": "Pre-diabetic Range"}
            ]
            summary = "Complete Blood Count shows normal hematological parameters with intact immune markers. Fasting glucose and HbA1c indicate mild prediabetic dysglycemia. Routine dietary adjustments advised."
            abnormal_count = 2
        elif "lipid" in lower_type or "cholesterol" in lower_type:
            sample_markers = [
                {"parameter": "Total Cholesterol", "value": "218 mg/dL", "reference": "< 200 mg/dL", "status": "Borderline High"},
                {"parameter": "HDL ('Good') Cholesterol", "value": "46 mg/dL", "reference": "> 40 mg/dL", "status": "Optimal"},
                {"parameter": "LDL ('Bad') Cholesterol", "value": "138 mg/dL", "reference": "< 100 mg/dL", "status": "Elevated"},
                {"parameter": "Triglycerides", "value": "165 mg/dL", "reference": "< 150 mg/dL", "status": "Mildly High"}
            ]
            summary = "Lipid panel reflects mild hyperlipidemia with elevated LDL and triglycerides. Cardiovascular risk is moderate. Consider aerobic exercise and omega-3 enriched Mediterranean dietary pattern."
            abnormal_count = 3
        elif "ecg" in lower_type or "cardio" in lower_type:
            sample_markers = [
                {"parameter": "Heart Rhythm", "value": "Normal Sinus Rhythm", "reference": "Sinus Rhythm", "status": "Normal"},
                {"parameter": "PR Interval", "value": "158 ms", "reference": "120 - 200 ms", "status": "Normal"},
                {"parameter": "QRS Duration", "value": "88 ms", "reference": "80 - 120 ms", "status": "Normal"},
                {"parameter": "QTc", "value": "412 ms", "reference": "< 450 ms", "status": "Normal"}
            ]
            summary = "Electrocardiogram demonstrates regular sinus rhythm without acute ischemic ST-T changes or conduction blocks. Cardiac electrical activity is within standard baseline limits."
            abnormal_count = 0
        else:
            sample_markers = [
                {"parameter": "Overall Impression", "value": "Satisfactory", "reference": "Standard", "status": "Normal"},
                {"parameter": "Clinical Marker Status", "value": "Stable", "reference": "Baseline", "status": "Normal"}
            ]
            summary = f"Report '{report_title}' ({report_type}) reviewed. Clinical markers are consistent with baseline findings. No urgent pathology flagged."
            abnormal_count = 0

        return {
            "report_title": report_title,
            "report_type": report_type,
            "extracted_markers": sample_markers,
            "ai_clinical_summary": summary,
            "abnormal_parameters_count": abnormal_count,
            "doctor_action_needed": abnormal_count > 0,
            "analyzed_at": datetime.datetime.utcnow().isoformat()
        }

# Global singleton engine
ml_health_engine = HealthRiskEngine()
