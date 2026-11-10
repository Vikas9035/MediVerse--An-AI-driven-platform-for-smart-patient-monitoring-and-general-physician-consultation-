from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List
import datetime
import uuid

from app.database import get_collection
from app.auth.dependencies import get_current_user, get_current_active_patient
from app.models.schemas import WellnessActivityLog, RewardClaim

router = APIRouter(prefix="/api/wellness", tags=["Wellness Rewards System"])

AVAILABLE_REWARDS_CATALOG = [
    {
        "id": "rew_1",
        "title": "$15 Off Physician Teleconsultation",
        "category": "Doctor Consultation",
        "points_cost": 150,
        "description": "Applies an instant $15 deduction on any General Physician appointment.",
        "icon": "Stethoscope"
    },
    {
        "id": "rew_2",
        "title": "Comprehensive Lipid & HbA1c Lab Voucher",
        "category": "Lab Diagnostics",
        "points_cost": 300,
        "description": "Full waiver for regular metabolic preventive blood testing at partner clinics.",
        "icon": "Activity"
    },
    {
        "id": "rew_3",
        "title": "MediPulse Smartwatch Sync Pass (Annual)",
        "category": "IoT & Devices",
        "points_cost": 450,
        "description": "Unlocks high-frequency telemetry sync & priority AI anomaly streaming.",
        "icon": "Watch"
    },
    {
        "id": "rew_4",
        "title": "Clinical Nutritionist Meal Plan (1-on-1)",
        "category": "Nutrition & Wellness",
        "points_cost": 600,
        "description": "Personalized 4-week DASH/Diabetic preventive nutrition guidance.",
        "icon": "Apple"
    }
]

HABIT_POINT_VALUES = {
    "water_intake": {"points": 15, "name": "Hydration Goal (2L Water)"},
    "daily_walk": {"points": 25, "name": "8,000 Steps Walk Completed"},
    "medication_taken": {"points": 20, "name": "Prescribed Medication Taken on Time"},
    "mindfulness": {"points": 15, "name": "15-Min Mindfulness or Deep Breathing"},
    "vitals_logged": {"points": 25, "name": "Daily Vitals Checked & Recorded"}
}

@router.get("/leaderboard")
async def get_wellness_leaderboard(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns the leaderboard of patients ranked by total wellness tokens earned,
    along with platform-wide health gamification metrics.
    Accessible to patients, doctors, and administrators.
    """
    wellness_col = get_collection("wellness_rewards")
    users_col = get_collection("users")
    patient_profiles_col = get_collection("patient_profiles")

    patients = list(users_col.find({"role": "patient"}))
    profiles_list = list(patient_profiles_col.find())
    profiles = {str(p.get("patient_id") or p.get("_id")): p for p in profiles_list}
    rewards_list = list(wellness_col.find())
    rewards_map = {str(r.get("user_id") or r.get("_id")): r for r in rewards_list}

    patient_ids = set()
    for p in patients:
        patient_ids.add(str(p["_id"]))
    for pid in profiles:
        patient_ids.add(str(pid))
    for r_id in rewards_map:
        patient_ids.add(str(r_id))

    if current_user.get("role") == "patient":
        patient_ids.add(str(current_user["_id"]))

    ranked_list = []
    for pid in patient_ids:
        usr = next((u for u in patients if str(u["_id"]) == pid), None)
        prof = profiles.get(pid)

        # Exclude administrative and doctor accounts from the patient leaderboard
        if usr and usr.get("role") in ["doctor", "admin"] and pid not in profiles:
            continue
        if not usr:
            general_u = users_col.find_one({"_id": pid})
            if general_u and general_u.get("role") in ["doctor", "admin"] and pid not in profiles:
                continue

        name = (prof and prof.get("name")) or (usr and usr.get("name")) or "MediVerse Patient"
        email = (prof and prof.get("email")) or (usr and usr.get("email")) or ""

        reward = rewards_map.get(pid)
        if not reward:
            pts = 100
            streak = 1
            tier = "Bronze"
            badges = [{"name": "MediVerse Pioneer", "icon": "Award"}]
            habits = ["welcome_signup"]
        else:
            pts = reward.get("total_points", 100)
            streak = reward.get("current_streak_days", 1)
            if pts >= 1000:
                tier = "Platinum"
            elif pts >= 500:
                tier = "Gold"
            elif pts >= 250:
                tier = "Silver"
            else:
                tier = "Bronze"
            badges = reward.get("earned_badges", [])
            habits = reward.get("completed_habits_today", [])

        ranked_list.append({
            "patient_id": pid,
            "name": name,
            "email": email,
            "tokens": pts,
            "streak_days": streak,
            "tier": tier,
            "badges_count": len(badges),
            "habits_count": len(habits),
            "is_current_user": pid == str(current_user["_id"])
        })

    # Sort descending by tokens, then streak days
    ranked_list.sort(key=lambda x: (x["tokens"], x["streak_days"]), reverse=True)

    # Assign rank positions
    for idx, item in enumerate(ranked_list):
        item["rank"] = idx + 1

    total_circulated = sum(item["tokens"] for item in ranked_list)
    avg_tokens = round(total_circulated / len(ranked_list)) if ranked_list else 0
    top_patient = ranked_list[0] if ranked_list else None

    current_user_id = str(current_user["_id"])
    user_entry = next((item for item in ranked_list if item["patient_id"] == current_user_id), None)

    return {
        "leaderboard": ranked_list,
        "stats": {
            "total_tokens_circulated": total_circulated,
            "active_participants": len(ranked_list),
            "average_tokens": avg_tokens,
            "top_earner_name": top_patient["name"] if top_patient else "None",
            "top_tokens": top_patient["tokens"] if top_patient else 0,
            "current_user_rank": user_entry["rank"] if user_entry else None,
            "current_user_tokens": user_entry["tokens"] if user_entry else None,
            "is_patient": current_user.get("role") == "patient"
        }
    }

@router.get("/summary")
async def get_wellness_summary(current_user: Dict[str, Any] = Depends(get_current_active_patient)):
    wellness_col = get_collection("wellness_rewards")
    data = wellness_col.find_one({"user_id": current_user["_id"]})
    
    now = datetime.datetime.utcnow().isoformat()
    if not data:
        data = {
            "_id": current_user["_id"],
            "user_id": current_user["_id"],
            "total_points": 125,
            "current_streak_days": 3,
            "tier": "Bronze",
            "completed_habits_today": ["Hydration Goal (2L Water)"],
            "earned_badges": [
                {"name": "MediVerse Pioneer", "icon": "Award", "description": "Joined the smart healthcare revolution", "earned_at": now},
                {"name": "Vitals Vigilant", "icon": "Heart", "description": "Logged physiological vitals 3 days in a row", "earned_at": now}
            ],
            "claimed_rewards": [],
            "updated_at": now
        }
        wellness_col.insert_one(data)

    # Calculate tier progression
    pts = data.get("total_points", 0)
    tier = "Bronze"
    next_tier = "Silver"
    tier_threshold = 250
    tier_progress = min(100, int((pts / 250) * 100))

    if pts >= 1000:
        tier = "Platinum"
        next_tier = "Max Tier"
        tier_threshold = 1000
        tier_progress = 100
    elif pts >= 500:
        tier = "Gold"
        next_tier = "Platinum"
        tier_threshold = 1000
        tier_progress = int(((pts - 500) / 500) * 100)
    elif pts >= 250:
        tier = "Silver"
        next_tier = "Gold"
        tier_threshold = 500
        tier_progress = int(((pts - 250) / 250) * 100)

    return {
        "user_id": current_user["_id"],
        "total_points": pts,
        "current_streak_days": data.get("current_streak_days", 1),
        "tier": tier,
        "next_tier": next_tier,
        "tier_progress": tier_progress,
        "completed_habits_today": data.get("completed_habits_today", []),
        "earned_badges": data.get("earned_badges", []),
        "catalog": AVAILABLE_REWARDS_CATALOG,
        "claimed_rewards": data.get("claimed_rewards", []),
        "habit_point_values": HABIT_POINT_VALUES
    }

@router.post("/log-activity")
async def log_wellness_activity(
    activity_in: WellnessActivityLog,
    current_user: Dict[str, Any] = Depends(get_current_active_patient)
):
    wellness_col = get_collection("wellness_rewards")
    data = wellness_col.find_one({"user_id": current_user["_id"]})
    if not data:
        data = {
            "user_id": current_user["_id"],
            "total_points": 100,
            "current_streak_days": 1,
            "completed_habits_today": [],
            "earned_badges": []
        }

    habit_info = HABIT_POINT_VALUES.get(activity_in.activity_type, {"points": 15, "name": activity_in.activity_type.replace("_", " ").title()})
    earned = habit_info["points"]
    habit_name = habit_info["name"]

    new_points = data.get("total_points", 0) + earned
    habits = data.get("completed_habits_today", [])
    if habit_name not in habits:
        habits.append(habit_name)

    # Check tier
    tier = "Bronze"
    if new_points >= 1000:
        tier = "Platinum"
    elif new_points >= 500:
        tier = "Gold"
    elif new_points >= 250:
        tier = "Silver"

    # Check milestone badges
    badges = data.get("earned_badges", [])
    now = datetime.datetime.utcnow().isoformat()
    badge_names = [b["name"] if isinstance(b, dict) else str(b) for b in badges]

    if new_points >= 250 and "Silver Health Advocate" not in badge_names:
        badges.append({"name": "Silver Health Advocate", "icon": "ShieldCheck", "description": "Accumulated over 250 health reward points", "earned_at": now})
    if len(habits) >= 3 and "Triple Goal Crusher" not in badge_names:
        badges.append({"name": "Triple Goal Crusher", "icon": "Zap", "description": "Completed 3 wellness activities in a single day", "earned_at": now})

    wellness_col.update_one(
        {"user_id": current_user["_id"]},
        {
            "$set": {
                "total_points": new_points,
                "tier": tier,
                "completed_habits_today": habits,
                "earned_badges": badges,
                "updated_at": now
            }
        },
        upsert=True
    )

    return {
        "message": f"Awesome! You earned +{earned} wellness points for '{habit_name}'.",
        "points_earned": earned,
        "new_total": new_points,
        "tier": tier
    }

@router.post("/claim")
async def claim_reward(
    claim_in: RewardClaim,
    current_user: Dict[str, Any] = Depends(get_current_active_patient)
):
    reward = next((r for r in AVAILABLE_REWARDS_CATALOG if r["id"] == claim_in.reward_id), None)
    if not reward:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reward not found in catalog.")

    wellness_col = get_collection("wellness_rewards")
    data = wellness_col.find_one({"user_id": current_user["_id"]})
    if not data or data.get("total_points", 0) < reward["points_cost"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient points. You need {reward['points_cost']} points to claim this reward."
        )

    now = datetime.datetime.utcnow().isoformat()
    claim_voucher = f"MV-PERK-{uuid.uuid4().hex[:8].upper()}"

    claimed_item = {
        "claim_id": uuid.uuid4().hex,
        "reward_id": reward["id"],
        "title": reward["title"],
        "voucher_code": claim_voucher,
        "points_spent": reward["points_cost"],
        "claimed_at": now
    }

    new_points = data.get("total_points", 0) - reward["points_cost"]

    wellness_col.update_one(
        {"user_id": current_user["_id"]},
        {
            "$set": {"total_points": new_points, "updated_at": now},
            "$push": {"claimed_rewards": claimed_item}
        }
    )

    return {
        "message": f"Congratulations! You claimed '{reward['title']}'.",
        "voucher_code": claim_voucher,
        "remaining_points": new_points,
        "claimed_item": claimed_item
    }
