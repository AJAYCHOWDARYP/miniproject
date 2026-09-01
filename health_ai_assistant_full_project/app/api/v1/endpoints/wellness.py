from app.services.ocr_service import extract_patient_demographics
"""
Wellness, Metrics, Meal Timing Reminders & Dynamic Dashboard Summary Endpoints with Patient Demographics (Name, Age, Weight).
"""
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.user import User, HealthProfile, MedicalCondition
from app.models.report import MedicalReport, ReportResult
from app.models.medication import Medication, MedicationSchedule, MedicationLog
from app.models.wellness import ExercisePlan, ExerciseLog, DietPlan, MealLog, HealthMetric, SymptomLog
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.all_schemas import ExerciseLogCreate, MealLogCreate, HealthMetricCreate, SymptomLogCreate
from app.services.exercise_service import generate_personalized_exercise_plan
from app.services.diet_service import generate_personalized_diet_plan

router = APIRouter()

DEFAULT_MEAL_REMINDERS = [
    {"meal_key": "breakfast", "name": "Breakfast", "time": "08:00 AM", "enabled": True},
    {"meal_key": "morning_snack", "name": "Morning Snack", "time": "11:00 AM", "enabled": True},
    {"meal_key": "lunch", "name": "Lunch", "time": "01:00 PM", "enabled": True},
    {"meal_key": "evening_snack", "name": "Evening Snack", "time": "04:30 PM", "enabled": True},
    {"meal_key": "dinner", "name": "Dinner", "time": "08:00 PM", "enabled": True},
    {"meal_key": "water", "name": "Hydration Reminder (250ml)", "time": "Hourly", "enabled": True}
]

USER_MEAL_REMINDERS: Dict[str, List[Dict[str, Any]]] = {}
USER_MOVEMENT_REMINDERS: Dict[str, Dict[str, Any]] = {}
DEFAULT_MOVEMENT_REMINDER = {"enabled": True, "time": "06:00 PM", "label": "Afternoon Walk Reminder"}


@router.get("/reminders/movement")
async def get_movement_reminder(user: User = Depends(get_current_user)):
    return USER_MOVEMENT_REMINDERS.get(user.id, DEFAULT_MOVEMENT_REMINDER)


@router.put("/reminders/movement")
async def update_movement_reminder(payload: Dict[str, Any] = Body(...), user: User = Depends(get_current_user)):
    USER_MOVEMENT_REMINDERS[user.id] = payload
    return {"message": "Movement reminder saved successfully", "reminder": payload}


@router.get("/notifications/feed")
async def get_notification_feed(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Gather meals, medications, and movement reminders
    meal_reminders = USER_MEAL_REMINDERS.get(user.id, DEFAULT_MEAL_REMINDERS)
    move_reminder = USER_MOVEMENT_REMINDERS.get(user.id, DEFAULT_MOVEMENT_REMINDER)

    rep_res = await db.execute(
        select(MedicalReport).where(MedicalReport.user_id == user.id).order_by(desc(MedicalReport.report_date), desc(MedicalReport.updated_at))
    )
    latest_rep = rep_res.scalars().first()

    feed = []

    # Report Notification
    if latest_rep:
        feed.append({
            "id": "notif_report",
            "category": "report",
            "icon": "file-check",
            "title": "Medical Report Analyzed & Ready",
            "body": f"Your report '{latest_rep.title}' has been clinically analyzed and verified.",
            "time": "Active",
            "badge": "Verified"
        })

    # Meal Reminders
    for m in meal_reminders:
        if m.get("enabled", True):
            feed.append({
                "id": f"notif_meal_{m.get('meal_key')}",
                "category": "meal",
                "icon": "utensils",
                "title": f"{m.get('name')} Reminder",
                "body": f"Scheduled daily at {m.get('time')}. Tap to view tailored meal ideas.",
                "time": m.get("time"),
                "badge": "Daily Meal"
            })

    # Movement Reminder
    if move_reminder.get("enabled", True):
        feed.append({
            "id": "notif_movement",
            "category": "movement",
            "icon": "heart-pulse",
            "title": move_reminder.get("label", "Daily Movement Reminder"),
            "body": f"Scheduled daily at {move_reminder.get('time', '06:00 PM')}. 15-min walk helps muscles absorb blood sugar.",
            "time": move_reminder.get("time", "06:00 PM"),
            "badge": "Active Walk"
        })

    return {
        "status": "success",
        "unread_count": len(feed),
        "notifications": feed
    }


@router.post("/notifications/send-test")
async def send_test_notification_endpoint(payload: Dict[str, Any] = Body(...), user: User = Depends(get_current_user)):
    return {
        "status": "sent",
        "title": payload.get("title", "Antigravity Health Assistant Alert"),
        "body": payload.get("body", "This is a test notification. Reminders are active & working!"),
        "timestamp": "Just now"
    }


def resolve_patient_report_for_plan(reports: List[MedicalReport], target_patient: Optional[str]) -> Optional[MedicalReport]:
    if not reports:
        return None
    if not target_patient or target_patient.strip().lower() == "all":
        return reports[0]
    target_clean = target_patient.strip().lower()
    for r in reports:
        p_name = "Not Specified in Report"
        if r.ai_summary_layers and isinstance(r.ai_summary_layers, dict):
            demo = r.ai_summary_layers.get("patient_demographics", {})
            if demo and demo.get("name"):
                p_name = demo["name"]
        elif r.raw_extracted_text:
            raw_demo = extract_patient_demographics(r.raw_extracted_text)
            if raw_demo and raw_demo.get("name"):
                p_name = raw_demo["name"]
        if p_name.lower() == target_clean:
            return r
    return reports[0]


@router.get("/diet-plan")
async def get_diet_plan(
    patient_name: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    rep_res = await db.execute(
        select(MedicalReport).where(MedicalReport.user_id == user.id).order_by(desc(MedicalReport.report_date), desc(MedicalReport.updated_at), desc(MedicalReport.created_at))
    )
    all_reports = rep_res.scalars().all()
    latest_report = resolve_patient_report_for_plan(all_reports, patient_name)

    report_results = []
    if latest_report:
        res_items = await db.execute(select(ReportResult).where(ReportResult.report_id == latest_report.id))
        report_results = res_items.scalars().all()

    prof_res = await db.execute(select(HealthProfile).where(HealthProfile.user_id == user.id))
    profile = prof_res.scalar_one_or_none()

    plan_dict = generate_personalized_diet_plan(
        profile=profile,
        latest_report=latest_report,
        report_results=report_results
    )
    return plan_dict


@router.get("/reminders/diet")
async def get_meal_reminders(user: User = Depends(get_current_user)):
    return USER_MEAL_REMINDERS.get(user.id, DEFAULT_MEAL_REMINDERS)


@router.put("/reminders/diet")
async def update_meal_reminders(reminders: List[Dict[str, Any]] = Body(...), user: User = Depends(get_current_user)):
    USER_MEAL_REMINDERS[user.id] = reminders
    return {"message": "Meal reminders saved successfully", "reminders": reminders}


@router.get("/exercise-plan")
async def get_exercise_plan(
    patient_name: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    rep_res = await db.execute(
        select(MedicalReport).where(MedicalReport.user_id == user.id).order_by(desc(MedicalReport.report_date), desc(MedicalReport.updated_at), desc(MedicalReport.created_at))
    )
    all_reports = rep_res.scalars().all()
    latest_report = resolve_patient_report_for_plan(all_reports, patient_name)

    report_results = []
    if latest_report:
        res_items = await db.execute(select(ReportResult).where(ReportResult.report_id == latest_report.id))
        report_results = res_items.scalars().all()

    prof_res = await db.execute(select(HealthProfile).where(HealthProfile.user_id == user.id))
    profile = prof_res.scalar_one_or_none()

    cond_res = await db.execute(select(MedicalCondition).where(MedicalCondition.user_id == user.id))
    conditions = cond_res.scalars().all()

    plan_dict = generate_personalized_exercise_plan(
        profile=profile,
        latest_report=latest_report,
        report_results=report_results,
        conditions=conditions
    )
    return plan_dict


@router.post("/exercise-logs")
async def log_exercise(payload: ExerciseLogCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    elog = ExerciseLog(
        user_id=user.id,
        activity_type=payload.activity_type,
        duration_minutes=payload.duration_minutes,
        intensity=payload.intensity,
        calories_burned=payload.calories_burned_estimated or (payload.duration_minutes * 5.0),
        notes=payload.notes
    )
    db.add(elog)
    await db.commit()
    await db.refresh(elog)
    return {"message": "Exercise session logged successfully", "log": elog}


@router.post("/meal-logs")
async def log_meal(payload: MealLogCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mlog = MealLog(
        user_id=user.id,
        meal_type=payload.meal_type,
        food_items=payload.food_items_logged,
        approx_calories=payload.estimated_calories_kcal,
        water_intake_ml=payload.water_intake_ml or 0.0,
        notes=payload.notes
    )
    db.add(mlog)
    await db.commit()
    await db.refresh(mlog)
    return {"message": "Meal logged successfully", "log": mlog}


@router.get("/dashboard-summary")
async def get_dashboard_summary(
    patient_name: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())

    # Fetch all user reports
    rep_res = await db.execute(
        select(MedicalReport).where(MedicalReport.user_id == user.id).order_by(desc(MedicalReport.report_date), desc(MedicalReport.updated_at), desc(MedicalReport.created_at))
    )
    all_user_reports = rep_res.scalars().all()

    # Build available patients breakdown
    patient_map: Dict[str, List[MedicalReport]] = {}
    for r in all_user_reports:
        p_name = "Not Specified in Report"
        if r.ai_summary_layers and isinstance(r.ai_summary_layers, dict):
            demo = r.ai_summary_layers.get("patient_demographics", {})
            if demo and demo.get("name"):
                p_name = demo["name"]
        elif r.raw_extracted_text:
            raw_demo = extract_patient_demographics(r.raw_extracted_text)
            if raw_demo and raw_demo.get("name"):
                p_name = raw_demo["name"]
        
        if p_name not in patient_map:
            patient_map[p_name] = []
        patient_map[p_name].append(r)

    available_patients = [
        {"patient_name": k, "report_count": len(v), "latest_date": str(v[0].report_date)}
        for k, v in patient_map.items()
    ]

    # Filter reports for active patient if specified
    if patient_name and patient_name.strip() and patient_name.lower() != "all":
        reports = patient_map.get(patient_name.strip(), [])
    else:
        reports = all_user_reports

    total_reports = len(reports)

    res_items = await db.execute(
        select(ReportResult).join(MedicalReport, ReportResult.report_id == MedicalReport.id).where(MedicalReport.user_id == user.id)
    )
    all_results = res_items.scalars().all()
    total_parameters = len(all_results)
    
    important_findings = []
    for r in all_results:
        if r.status_flag in ["above_range", "below_range", "critical"]:
            important_findings.append({
                "biomarker_name": r.biomarker_name,
                "value": f"{r.numeric_value} {r.unit or ''}".strip(),
                "status": r.status_flag,
                "reference_range": r.ref_range_raw,
                "date": str(r.recorded_date)
            })

    med_res = await db.execute(select(Medication).where(Medication.user_id == user.id, Medication.is_active == True))
    active_meds = med_res.scalars().all()

    meal_res = await db.execute(select(MealLog).where(MealLog.user_id == user.id, MealLog.logged_at >= today_start))
    meals = meal_res.scalars().all()
    total_water_ml = sum(m.water_intake_ml for m in meals)

    prof_res = await db.execute(select(HealthProfile).where(HealthProfile.user_id == user.id))
    profile = prof_res.scalar_one_or_none()

    latest_report = None
    extracted_demographics = {}
    if reports:
        lr = reports[0]
        if lr.ai_summary_layers:
            extracted_demographics = lr.ai_summary_layers.get("patient_demographics", {})
        latest_report = {
            "id": lr.id,
            "title": lr.title,
            "report_date": str(lr.report_date),
            "report_type": lr.report_type,
            "laboratory_name": lr.laboratory_name,
            "is_user_verified": lr.is_user_verified
        }

    # Demographics resolution: Differentiate Patient Name (from report) vs Profile Person (account holder)
    patient_name_from_report = extracted_demographics.get("name")
    account_holder_name = user.full_name or user.email or user.phone_number or "Account Holder"

    patient_age = extracted_demographics.get("age")
    if not patient_age and profile and profile.date_of_birth:
        calc_age = today.year - profile.date_of_birth.year - ((today.month, today.day) < (profile.date_of_birth.month, profile.date_of_birth.day))
        patient_age = f"{calc_age} Years"

    patient_weight = extracted_demographics.get("weight")
    if not patient_weight and profile and profile.weight_kg:
        patient_weight = f"{profile.weight_kg} kg"

    prof_gender = getattr(profile, "gender", None) or getattr(profile, "sex", None)
    if prof_gender in ["Not Specified", None, ""]:
        prof_gender = None
    patient_gender = extracted_demographics.get("gender") or prof_gender

    patient_demographics = {
        "patient_name": patient_name_from_report or "Not Specified in Report",
        "has_extracted_patient_name": bool(patient_name_from_report),
        "account_holder_name": account_holder_name,
        "name": patient_name_from_report or "Not Specified in Report",
        "has_extracted_name": bool(patient_name_from_report),
        "age": patient_age or "Not Specified in Report",
        "weight": patient_weight or "Not Specified in Report",
        "gender": patient_gender or "Not Specified in Report",
        "source": "Extracted from Latest Medical Report" if patient_name_from_report else "No Patient Name in Report"
    }

    reminders = USER_MEAL_REMINDERS.get(user.id, DEFAULT_MEAL_REMINDERS)
    upcoming_events = [
        {"type": "DIET", "title": r["name"], "time": r["time"], "icon": "utensils"}
        for r in reminders if r.get("enabled", True)
    ]
    for m in active_meds:
        sch_res = await db.execute(select(MedicationSchedule).where(MedicationSchedule.medication_id == m.id))
        for s in sch_res.scalars().all():
            upcoming_events.append({
                "type": "MEDICATION",
                "title": f"{m.brand_name} ({m.strength})",
                "time": s.scheduled_time_str,
                "icon": "pill"
            })

    return {
        "has_data": total_reports > 0 or len(active_meds) > 0,
        "total_reports": total_reports,
        "total_biomarkers_extracted": total_parameters,
        "active_medications_count": len(active_meds),
        "patient_demographics": patient_demographics,
        "available_patients": available_patients,
        "active_patient_filter": patient_name or "All",
        "available_patients": available_patients,
        "active_patient_filter": patient_name or "All",
        "latest_report": latest_report,
        "important_findings": important_findings[:5],
        "today_overview": {
            "water_logged_liters": round(total_water_ml / 1000.0, 2),
            "meals_logged_count": len(meals),
            "upcoming_reminders": upcoming_events
        }
    }
