"""
Doctor Sharing Endpoints.
"""
import uuid
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.user import User, HealthProfile, MedicalCondition, Allergy
from app.models.report import ReportResult, MedicalReport
from app.models.medication import Medication, MedicationLog
from app.models.wellness import SymptomLog
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.all_schemas import DoctorShareRequest
from app.services.share_service import generate_doctor_clinical_summary
from app.services.scheduler_service import calculate_adherence_statistics
from app.services.audit_service import log_audit_event

router = APIRouter()

SHARE_TOKENS: Dict[str, Dict[str, Any]] = {}


@router.post("/generate-summary")
async def generate_share_summary(
    payload: DoctorShareRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    prof_res = await db.execute(select(HealthProfile).where(HealthProfile.user_id == user.id))
    profile = prof_res.scalar_one_or_none()

    cond_res = await db.execute(select(MedicalCondition).where(MedicalCondition.user_id == user.id))
    conditions = [c.condition_name for c in cond_res.scalars().all()]

    allg_res = await db.execute(select(Allergy).where(Allergy.user_id == user.id))
    allergies = [f"{a.allergen_name} ({a.severity})" for a in allg_res.scalars().all()]

    med_res = await db.execute(select(Medication).where(Medication.user_id == user.id, Medication.is_active == True))
    meds = [
        {
            "brand_name": m.brand_name,
            "strength": m.strength,
            "frequency_type": m.frequency_type,
            "food_relation": m.food_relation,
            "prescribing_doctor": m.prescribing_doctor
        }
        for m in med_res.scalars().all()
    ]

    logs_res = await db.execute(select(MedicationLog).where(MedicationLog.user_id == user.id))
    dict_logs = [{"status": l.status} for l in logs_res.scalars().all()]
    adherence_stats = calculate_adherence_statistics(dict_logs)

    q = (
        select(ReportResult)
        .join(MedicalReport, ReportResult.report_id == MedicalReport.id)
        .where(MedicalReport.user_id == user.id)
        .order_by(desc(ReportResult.recorded_date))
        .limit(15)
    )
    labs_res = await db.execute(q)
    recent_labs = [
        {
            "biomarker_name": r.biomarker_name,
            "numeric_value": r.numeric_value,
            "unit": r.unit,
            "status_flag": r.status_flag,
            "recorded_date": r.recorded_date
        }
        for r in labs_res.scalars().all()
    ]

    symp_res = await db.execute(select(SymptomLog).where(SymptomLog.user_id == user.id).order_by(desc(SymptomLog.logged_at)).limit(5))
    symptoms = [{"symptom": s.symptom_name, "severity": s.severity, "date": str(s.logged_at.date())} for s in symp_res.scalars().all()]

    summary = generate_doctor_clinical_summary(
        user_name=user.full_name,
        age=profile.age if profile and profile.age else 35.0,
        sex=profile.sex if profile and profile.sex else "Not specified",
        active_conditions=conditions,
        allergies=allergies,
        medications=meds,
        adherence_stats=adherence_stats,
        recent_lab_results=recent_labs,
        recent_symptoms=symptoms,
        patient_notes=payload.notes_for_doctor or ""
    )

    token = str(uuid.uuid4())
    SHARE_TOKENS[token] = {
        "summary": summary,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=48),
        "user_id": user.id
    }

    await log_audit_event(db, "GENERATE_DOCTOR_SHARE", "ShareToken", token, user.id)

    return {
        "message": "Doctor summary generated successfully",
        "share_token": token,
        "expires_in_hours": 48,
        "summary": summary
    }


@router.get("/shared/{token}")
async def view_shared_summary(token: str):
    data = SHARE_TOKENS.get(token)
    if not data or data["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=404, detail="Shared link is invalid or has expired.")
    return data["summary"]
