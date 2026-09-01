"""
Audit & Compliance Endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.user import User, AuditLog, HealthProfile, MedicalCondition, Allergy
from app.models.report import MedicalReport
from app.models.medication import Medication
from app.models.wellness import HealthMetric
from app.api.v1.endpoints.auth import get_current_user
from app.services.audit_service import log_audit_event

router = APIRouter()


@router.get("/logs")
async def get_my_audit_logs(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(AuditLog).where(AuditLog.user_id == user.id).order_by(desc(AuditLog.created_at)).limit(50)
    )
    logs = res.scalars().all()
    return [
        {
            "id": l.id,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "details": l.details,
            "timestamp": str(l.created_at)
        }
        for l in logs
    ]


@router.get("/export-data")
async def export_patient_data(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    prof_res = await db.execute(select(HealthProfile).where(HealthProfile.user_id == user.id))
    profile = prof_res.scalar_one_or_none()

    cond_res = await db.execute(select(MedicalCondition).where(MedicalCondition.user_id == user.id))
    conditions = cond_res.scalars().all()

    allg_res = await db.execute(select(Allergy).where(Allergy.user_id == user.id))
    allergies = allg_res.scalars().all()

    rep_res = await db.execute(select(MedicalReport).where(MedicalReport.user_id == user.id))
    reports = rep_res.scalars().all()

    med_res = await db.execute(select(Medication).where(Medication.user_id == user.id))
    meds = med_res.scalars().all()

    met_res = await db.execute(select(HealthMetric).where(HealthMetric.user_id == user.id))
    metrics = met_res.scalars().all()

    await log_audit_event(db, "EXPORT_ALL_DATA", "User", user.id, user.id)

    return {
        "export_metadata": {
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name
        },
        "health_profile": {
            "dob": str(profile.date_of_birth) if profile else None,
            "sex": profile.sex if profile else None
        },
        "medical_conditions": [{"name": c.condition_name, "status": c.status} for c in conditions],
        "allergies": [{"allergen": a.allergen_name, "severity": a.severity} for a in allergies],
        "medical_reports_count": len(reports),
        "medications_count": len(meds),
        "health_metrics_count": len(metrics)
    }
