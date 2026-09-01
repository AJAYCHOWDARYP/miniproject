"""
Trends & Timeline Endpoints with Multi-Patient Segregation.
Ensures biomarker trendlines are calculated strictly for the same patient.
"""
from typing import Optional, Dict, Any, List
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.user import User
from app.models.report import ReportResult, MedicalReport
from app.models.medication import Prescription
from app.models.wellness import HealthMetric
from app.api.v1.endpoints.auth import get_current_user
from app.services.trend_service import build_biomarker_trendlines
from app.services.ocr_service import extract_patient_demographics

router = APIRouter()


def get_report_patient_name(report: MedicalReport) -> str:
    if report.ai_summary_layers and isinstance(report.ai_summary_layers, dict):
        demo = report.ai_summary_layers.get("patient_demographics", {})
        if demo and demo.get("name"):
            return demo["name"]
    if report.raw_extracted_text:
        raw_demo = extract_patient_demographics(report.raw_extracted_text)
        if raw_demo and raw_demo.get("name"):
            return raw_demo["name"]
    return "Not Specified in Report"


@router.get("/biomarkers")
async def get_biomarker_trends(
    patient_name: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Fetch all user reports ordered chronologically
    rep_res = await db.execute(
        select(MedicalReport).where(MedicalReport.user_id == user.id).order_by(MedicalReport.report_date.asc())
    )
    reports = rep_res.scalars().all()

    # Identify all distinct patients in this account
    patient_reports_map: Dict[str, List[MedicalReport]] = {}
    for r in reports:
        p_name = get_report_patient_name(r)
        if p_name not in patient_reports_map:
            patient_reports_map[p_name] = []
        patient_reports_map[p_name].append(r)

    available_patients = [
        {"patient_name": k, "report_count": len(v)}
        for k, v in patient_reports_map.items()
    ]

    # Select target patient
    target_patient = patient_name
    if not target_patient or target_patient.strip().lower() == "all":
        # Default to the patient with the most recent report if available
        if reports:
            target_patient = get_report_patient_name(reports[-1])
        else:
            target_patient = "Not Specified in Report"

    # Filter reports strictly for target patient
    target_reports = patient_reports_map.get(target_patient, [])
    target_report_ids = [r.id for r in target_reports]

    if not target_report_ids:
        empty_plan = build_biomarker_trendlines([])
        empty_plan["patient_name"] = target_patient
        empty_plan["available_patients"] = available_patients
        return empty_plan

    # Fetch results belonging strictly to this patient's reports
    q = (
        select(ReportResult)
        .where(ReportResult.report_id.in_(target_report_ids))
        .order_by(ReportResult.recorded_date.asc())
    )
    res = await db.execute(q)
    results = res.scalars().all()

    dict_results = [
        {
            "biomarker_name": r.biomarker_name,
            "canonical_code": r.canonical_code,
            "numeric_value": r.numeric_value,
            "string_value": r.string_value,
            "unit": r.unit,
            "ref_min": r.ref_min,
            "ref_max": r.ref_max,
            "status_flag": r.status_flag,
            "recorded_date": r.recorded_date
        }
        for r in results
    ]

    trends = build_biomarker_trendlines(dict_results)
    trends["patient_name"] = target_patient
    trends["available_patients"] = available_patients
    trends["patient_report_count"] = len(target_reports)
    return trends


@router.get("/timeline")
async def get_health_timeline(
    patient_name: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    events = []

    rep_res = await db.execute(select(MedicalReport).where(MedicalReport.user_id == user.id))
    for r in rep_res.scalars().all():
        pt_name = get_report_patient_name(r)
        if patient_name and patient_name.lower() != "all" and pt_name.lower() != patient_name.lower():
            continue

        events.append({
            "category": "MEDICAL_REPORT",
            "title": f"Report ({pt_name}): {r.title}",
            "patient_name": pt_name,
            "description": f"{r.report_type} from {r.laboratory_name or 'Diagnostic Lab'}",
            "date": str(r.report_date),
            "icon": "file-text"
        })

    rx_res = await db.execute(select(Prescription).where(Prescription.user_id == user.id))
    for rx in rx_res.scalars().all():
        events.append({
            "category": "PRESCRIPTION",
            "title": f"Prescription by {rx.prescribing_doctor}",
            "description": rx.notes or "New medication schedule added",
            "date": str(rx.prescription_date),
            "icon": "pill"
        })

    met_res = await db.execute(select(HealthMetric).where(HealthMetric.user_id == user.id))
    for m in met_res.scalars().all():
        events.append({
            "category": "BIOMETRIC",
            "title": f"Vital Logged: {m.metric_type.replace('_', ' ').title()}",
            "description": f"{m.value_primary}{'/' + str(m.value_secondary) if m.value_secondary else ''} {m.unit}",
            "date": str(m.recorded_at.date() if m.recorded_at else date.today()),
            "icon": "activity"
        })

    events.sort(key=lambda e: e["date"], reverse=True)
    return events
