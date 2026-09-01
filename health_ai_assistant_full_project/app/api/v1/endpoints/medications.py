"""
Medication and Schedule Endpoints.
"""
from typing import List, Optional
from datetime import date, datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_db
from app.models.user import User
from app.models.medication import Prescription, Medication, MedicationSchedule, MedicationLog
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.all_schemas import PrescriptionCreate, MedicationLogAction
from app.services.medical_extractor import parse_prescription_text
from app.services.scheduler_service import calculate_adherence_statistics, get_safe_missed_dose_guidance
from app.services.audit_service import log_audit_event

router = APIRouter()


@router.post("/prescriptions")
async def create_prescription(
    payload: PrescriptionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    rx = Prescription(
        user_id=user.id,
        prescribing_doctor=payload.prescribing_doctor,
        clinic_or_hospital=payload.clinic_or_hospital,
        prescription_date=payload.prescription_date,
        valid_until=payload.valid_until,
        diagnosis_indicated=payload.diagnosis_indicated,
        notes=payload.notes
    )
    db.add(rx)
    await db.flush()

    for med_data in payload.medications:
        med = Medication(
            user_id=user.id,
            prescription_id=rx.id,
            brand_name=med_data.brand_name,
            generic_name=med_data.generic_name,
            strength=med_data.strength,
            dosage_form=med_data.dosage_form,
            frequency_type=med_data.frequency_type,
            route=med_data.route,
            food_relation=med_data.food_relation,
            start_date=med_data.start_date,
            end_date=med_data.end_date,
            duration_days=med_data.duration_days,
            prescribing_doctor=payload.prescribing_doctor,
            special_instructions=med_data.special_instructions,
            is_active=True
        )
        db.add(med)
        await db.flush()

        for sch in med_data.schedules:
            ms = MedicationSchedule(
                medication_id=med.id,
                scheduled_time_str=sch.scheduled_time_str,
                dose_quantity=sch.dose_quantity,
                reminder_enabled=sch.reminder_enabled
            )
            db.add(ms)

    await db.commit()
    await db.refresh(rx)
    await log_audit_event(db, "CREATE_PRESCRIPTION", "Prescription", rx.id, user.id)
    return {"message": "Prescription and schedule saved successfully", "prescription_id": rx.id}


@router.post("/prescriptions/upload-text")
async def upload_prescription_text(
    text: str = Form(...),
    doctor_name: Optional[str] = Form("Dr. Healthcare Provider")
):
    extracted = parse_prescription_text(text, doctor_name or "Dr. Healthcare Provider")
    return {"message": "Prescription parsed", "extracted_data": extracted}


@router.get("/")
async def list_medications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Medication).where(Medication.user_id == user.id))
    meds = res.scalars().all()
    
    output = []
    for m in meds:
        sch_res = await db.execute(select(MedicationSchedule).where(MedicationSchedule.medication_id == m.id))
        schedules = sch_res.scalars().all()
        output.append({
            "id": m.id,
            "brand_name": m.brand_name,
            "generic_name": m.generic_name,
            "strength": m.strength,
            "dosage_form": m.dosage_form,
            "frequency_type": m.frequency_type,
            "food_relation": m.food_relation,
            "start_date": str(m.start_date),
            "end_date": str(m.end_date) if m.end_date else None,
            "prescribing_doctor": m.prescribing_doctor,
            "special_instructions": m.special_instructions,
            "is_active": m.is_active,
            "schedules": [
                {"id": s.id, "time": s.scheduled_time_str, "quantity": s.dose_quantity, "reminder": s.reminder_enabled}
                for s in schedules
            ]
        })
    return output


@router.get("/today-reminders")
async def get_today_reminders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    today = date.today()
    med_res = await db.execute(select(Medication).where(Medication.user_id == user.id, Medication.is_active == True))
    meds = med_res.scalars().all()

    reminders = []
    for m in meds:
        sch_res = await db.execute(select(MedicationSchedule).where(MedicationSchedule.medication_id == m.id))
        for sch in sch_res.scalars().all():
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            log_res = await db.execute(
                select(MedicationLog).where(
                    MedicationLog.schedule_id == sch.id,
                    MedicationLog.scheduled_for >= today_start,
                    MedicationLog.scheduled_for <= today_end
                )
            )
            log = log_res.scalar_one_or_none()

            reminders.append({
                "schedule_id": sch.id,
                "medication_id": m.id,
                "brand_name": m.brand_name,
                "strength": m.strength,
                "dosage_form": m.dosage_form,
                "food_relation": m.food_relation,
                "scheduled_time": sch.scheduled_time_str,
                "dose_quantity": sch.dose_quantity,
                "status": log.status if log else "PENDING",
                "logged_time": str(log.action_time) if log else None
            })

    reminders.sort(key=lambda r: r["scheduled_time"])
    return reminders


@router.post("/log-action")
async def log_medication_action(
    payload: MedicationLogAction,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    log = MedicationLog(
        schedule_id=payload.schedule_id,
        medication_id=payload.medication_id,
        user_id=user.id,
        scheduled_for=payload.scheduled_for,
        action_time=datetime.now(timezone.utc),
        status=payload.action,
        skip_reason=payload.skip_reason,
        notes=payload.notes
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    await log_audit_event(db, f"MED_ACTION_{payload.action}", "MedicationLog", log.id, user.id)

    guidance = None
    if payload.action == "SKIPPED":
        med_res = await db.execute(select(Medication).where(Medication.id == payload.medication_id))
        med = med_res.scalar_one_or_none()
        med_name = med.brand_name if med else "your medication"
        guidance = get_safe_missed_dose_guidance(med_name)

    return {
        "message": f"Dose marked as {payload.action}",
        "log_id": log.id,
        "missed_dose_guidance": guidance
    }


@router.get("/adherence")
async def get_adherence(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logs_res = await db.execute(select(MedicationLog).where(MedicationLog.user_id == user.id))
    logs = logs_res.scalars().all()
    
    dict_logs = [{"status": l.status, "action_time": l.action_time} for l in logs]
    return calculate_adherence_statistics(dict_logs)


@router.delete("/clear-all")
async def clear_all_medications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    med_res = await db.execute(select(Medication).where(Medication.user_id == user.id))
    meds = med_res.scalars().all()
    for m in meds:
        await db.execute(delete(MedicationSchedule).where(MedicationSchedule.medication_id == m.id))
        await db.execute(delete(MedicationLog).where(MedicationLog.medication_id == m.id))
        await db.delete(m)
    
    rx_res = await db.execute(select(Prescription).where(Prescription.user_id == user.id))
    for rx in rx_res.scalars().all():
        await db.delete(rx)
        
    await db.commit()
    await log_audit_event(db, "CLEAR_ALL_MEDICATIONS", "Medication", "ALL", user.id)
    return {"message": "All prescriptions and medication schedules have been cleared."}


@router.delete("/{med_id}")
async def delete_medication(
    med_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Medication).where(Medication.id == med_id, Medication.user_id == user.id))
    med = res.scalar_one_or_none()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
        
    await db.execute(delete(MedicationSchedule).where(MedicationSchedule.medication_id == med.id))
    await db.execute(delete(MedicationLog).where(MedicationLog.medication_id == med.id))
    await db.delete(med)
    await db.commit()
    
    await log_audit_event(db, "DELETE_MEDICATION", "Medication", med.id, user.id)
    return {"message": f"Medication '{med.brand_name}' deleted successfully."}

