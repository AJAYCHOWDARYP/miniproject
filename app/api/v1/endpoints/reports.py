"""
Medical Reports & OCR Endpoints with instant analysis preview, file download/view, search, filter, comparison, and deletion.
"""
import os
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.config import settings, UPLOAD_DIR
from app.models.user import User
from app.models.report import MedicalReport, ReportResult
from app.api.v1.endpoints.auth import get_current_user
from app.services.ocr_service import extract_text_from_pdf, parse_lab_text_to_structured_results, extract_patient_demographics, is_valid_medical_report_text
from app.services.ai_guardrails import generate_layered_report_insights
from app.services.audit_service import log_audit_event
from app.schemas.all_schemas import ReportVerificationPayload

router = APIRouter()

def get_report_patient_name(report: MedicalReport) -> str:
    """Extracts patient name from report's stored ai layers or raw text."""
    if report.ai_summary_layers and isinstance(report.ai_summary_layers, dict):
        demo = report.ai_summary_layers.get("patient_demographics", {})
        if demo and demo.get("name"):
            return demo["name"]
    if report.raw_extracted_text:
        raw_demo = extract_patient_demographics(report.raw_extracted_text)
        if raw_demo and raw_demo.get("name"):
            return raw_demo["name"]
    return "Not Specified in Report"



@router.post("/upload")
async def upload_medical_report(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    report_type: Optional[str] = Form("Laboratory Report"),
    report_date_str: Optional[str] = Form(None),
    laboratory_name: Optional[str] = Form(None),
    doctor_name: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    file_bytes = await file.read()
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File size exceeds maximum 20MB limit.")

    filename = file.filename or "report.pdf"
    ext = filename.split(".")[-1].lower() if "." in filename else "txt"
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File extension '.{ext}' is not supported.")

    save_path = UPLOAD_DIR / f"{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    with open(save_path, "wb") as f:
        f.write(file_bytes)

    if ext == "pdf":
        extracted_text = extract_text_from_pdf(file_bytes)
    else:
        try:
            extracted_text = file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            extracted_text = "Medical Report Document"

    parsed_results = parse_lab_text_to_structured_results(extracted_text)
    extracted_demographics = extract_patient_demographics(extracted_text)

    # Validation: reject non-medical documents
    if not is_valid_medical_report_text(extracted_text, parsed_results):
        if save_path.exists():
            try:
                save_path.unlink()
            except Exception:
                pass
        raise HTTPException(
            status_code=400,
            detail="Please upload medical reports (such as blood tests, lab panels, or clinical diagnostics)."
        )

    rep_date = date.today()
    if report_date_str:
        try:
            rep_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    elif extracted_text:
        import re
        date_match = re.search(r"(?:date|collected|tested|recorded|sample\s*date)\s*[:\-\|]?\s*(\d{4}-\d{2}-\d{2})", extracted_text, re.IGNORECASE)
        if date_match:
            try:
                rep_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").date()
            except ValueError:
                pass

    report_title = title or f"{report_type} - {rep_date.strftime('%b %d, %Y')}"
    insights = generate_layered_report_insights(report_title, str(rep_date), parsed_results, demographics=extracted_demographics)

    report = MedicalReport(
        user_id=user.id,
        title=report_title,
        report_type=report_type,
        report_date=rep_date,
        laboratory_name=laboratory_name or "Diagnostic Laboratory",
        doctor_name=doctor_name,
        file_path=str(save_path),
        file_type=ext,
        ocr_status="COMPLETED",
        ocr_confidence=0.95 if parsed_results else 0.70,
        raw_extracted_text=extracted_text,
        is_user_verified=False,
        ai_summary_layers=insights
    )
    db.add(report)
    await db.flush()

    for item in parsed_results:
        res = ReportResult(
            report_id=report.id,
            biomarker_name=item["biomarker_name"],
            canonical_code=item.get("canonical_code"),
            numeric_value=item.get("numeric_value"),
            string_value=item.get("string_value"),
            unit=item.get("unit"),
            ref_min=item.get("ref_min"),
            ref_max=item.get("ref_max"),
            ref_range_raw=item.get("ref_range_raw"),
            status_flag=item.get("status_flag", "within_range"),
            confidence=item.get("confidence", 0.9),
            explanation_simple=item.get("explanation_simple"),
            recorded_date=rep_date
        )
        db.add(res)

    await db.commit()
    await db.refresh(report)
    await log_audit_event(db, "UPLOAD_REPORT", "MedicalReport", report.id, user.id)

    return {
        "message": "Report uploaded and parsed successfully.",
        "report_id": report.id,
        "title": report.title,
        "report_date": str(report.report_date),
        "file_name": filename,
        "file_type": ext,
        "is_user_verified": report.is_user_verified,
        "results_extracted_count": len(parsed_results),
        "results": parsed_results,
        "ai_insights": insights,
        "patient_demographics": extracted_demographics
    }


@router.get("/patients")
async def list_distinct_patients(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns all distinct patients whose reports exist in this account."""
    res = await db.execute(
        select(MedicalReport).where(MedicalReport.user_id == user.id).order_by(desc(MedicalReport.report_date))
    )
    reports = res.scalars().all()
    
    patient_map: Dict[str, Dict[str, Any]] = {}
    for r in reports:
        p_name = get_report_patient_name(r)
        if p_name not in patient_map:
            patient_map[p_name] = {
                "patient_name": p_name,
                "report_count": 0,
                "latest_date": str(r.report_date),
                "reports": []
            }
        patient_map[p_name]["report_count"] += 1
        patient_map[p_name]["reports"].append({
            "id": r.id,
            "title": r.title,
            "report_date": str(r.report_date),
            "report_type": r.report_type
        })
    
    return list(patient_map.values())


@router.get("/")
async def list_reports(
    search: Optional[str] = Query(None),
    patient_name: Optional[str] = Query(None),
    sort_order: Optional[str] = Query("desc"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(MedicalReport).where(MedicalReport.user_id == user.id)
    if sort_order == "asc":
        query = query.order_by(MedicalReport.report_date.asc())
    else:
        query = query.order_by(MedicalReport.report_date.desc(), desc(MedicalReport.updated_at), desc(MedicalReport.created_at))

    res = await db.execute(query)
    reports = res.scalars().all()
    
    output = []
    for r in reports:
        extracted_pt_name = get_report_patient_name(r)
        
        # Segregation filter by patient
        if patient_name and patient_name.strip() and patient_name.lower() != "all":
            if extracted_pt_name.strip().lower() != patient_name.strip().lower():
                continue

        res_items = await db.execute(select(ReportResult).where(ReportResult.report_id == r.id))
        results = res_items.scalars().all()

        if search:
            s_lower = search.lower()
            matches_title = s_lower in r.title.lower() or s_lower in (r.laboratory_name or "").lower()
            matches_pt = s_lower in extracted_pt_name.lower()
            matches_bio = any(s_lower in b.biomarker_name.lower() for b in results)
            if not (matches_title or matches_bio or matches_pt):
                continue
        
        file_name = os.path.basename(r.file_path) if r.file_path else f"{r.title}.{r.file_type or 'txt'}"
        file_size_kb = round(os.path.getsize(r.file_path) / 1024, 1) if (r.file_path and os.path.exists(r.file_path)) else 4.2

        output.append({
            "id": r.id,
            "title": r.title,
            "patient_name": extracted_pt_name,
            "report_type": r.report_type,
            "report_date": str(r.report_date),
            "laboratory_name": r.laboratory_name,
            "doctor_name": r.doctor_name,
            "file_name": file_name,
            "file_type": r.file_type or "txt",
            "file_size_kb": file_size_kb,
            "has_file": bool(r.file_path and os.path.exists(r.file_path)),
            "ocr_status": r.ocr_status,
            "ocr_confidence": r.ocr_confidence,
            "is_user_verified": r.is_user_verified,
            "raw_extracted_text": r.raw_extracted_text,
            "results_count": len(results),
            "results": [
                {
                    "id": item.id,
                    "biomarker_name": item.biomarker_name,
                    "canonical_code": item.canonical_code,
                    "numeric_value": item.numeric_value,
                    "unit": item.unit,
                    "ref_range_raw": item.ref_range_raw,
                    "status_flag": item.status_flag
                }
                for item in results
            ],
            "ai_summary_layers": r.ai_summary_layers,
            "created_at": str(r.created_at)
        })
    return output


@router.get("/compare")
async def compare_two_reports(
    report_id_1: str = Query(...),
    report_id_2: str = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    r1_res = await db.execute(select(MedicalReport).where(MedicalReport.id == report_id_1, MedicalReport.user_id == user.id))
    r2_res = await db.execute(select(MedicalReport).where(MedicalReport.id == report_id_2, MedicalReport.user_id == user.id))
    r1 = r1_res.scalar_one_or_none()
    r2 = r2_res.scalar_one_or_none()
    
    if not r1 or not r2:
        raise HTTPException(status_code=404, detail="One or both reports not found.")

    res1 = (await db.execute(select(ReportResult).where(ReportResult.report_id == r1.id))).scalars().all()
    res2 = (await db.execute(select(ReportResult).where(ReportResult.report_id == r2.id))).scalars().all()

    dict1 = {r.canonical_code or r.biomarker_name: r for r in res1}
    dict2 = {r.canonical_code or r.biomarker_name: r for r in res2}

    all_keys = set(dict1.keys()).union(set(dict2.keys()))
    comparisons = []

    for k in all_keys:
        item1 = dict1.get(k)
        item2 = dict2.get(k)
        name = (item1 or item2).biomarker_name
        unit = (item1 or item2).unit or ""

        v1 = item1.numeric_value if item1 else None
        v2 = item2.numeric_value if item2 else None
        
        delta = None
        pct = None
        if v1 is not None and v2 is not None:
            delta = round(v2 - v1, 2)
            if v1 != 0:
                pct = round(((v2 - v1) / abs(v1)) * 100.0, 1)

        comparisons.append({
            "parameter": name,
            "unit": unit,
            "report_1_value": v1,
            "report_1_status": item1.status_flag if item1 else "N/A",
            "report_2_value": v2,
            "report_2_status": item2.status_flag if item2 else "N/A",
            "delta": delta,
            "percent_change": pct,
            "trend": "Increased" if delta and delta > 0 else "Decreased" if delta and delta < 0 else "Stable" if delta == 0 else "Single Reading"
        })

    p1_name = get_report_patient_name(r1)
    p2_name = get_report_patient_name(r2)
    is_same = (p1_name.strip().lower() == p2_name.strip().lower())

    warning_msg = None
    if not is_same:
        warning_msg = f"Notice: Comparing reports of two different patients ('{p1_name}' vs '{p2_name}'). Reports should ideally be compared with the same patient's own historical tests."

    return {
        "is_same_patient": is_same,
        "patient_name": p1_name if is_same else f"{p1_name} & {p2_name}",
        "patient_1_name": p1_name,
        "patient_2_name": p2_name,
        "warning": warning_msg,
        "report_1": {"id": r1.id, "title": r1.title, "date": str(r1.report_date), "patient_name": p1_name},
        "report_2": {"id": r2.id, "title": r2.title, "date": str(r2.report_date), "patient_name": p2_name},
        "comparison_table": comparisons
    }


@router.delete("/clear-all")
async def delete_all_reports(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(MedicalReport).where(MedicalReport.user_id == user.id))
    reports = res.scalars().all()
    count = len(reports)

    for r in reports:
        res_items = await db.execute(select(ReportResult).where(ReportResult.report_id == r.id))
        for item in res_items.scalars().all():
            await db.delete(item)
        if r.file_path and os.path.exists(r.file_path):
            try:
                os.remove(r.file_path)
            except Exception:
                pass
        await db.delete(r)

    await db.commit()
    await log_audit_event(db, "DELETE_ALL_REPORTS", "MedicalReport", "ALL", user.id)
    return {"message": f"Successfully deleted all {count} reports and related history.", "deleted_count": count}


@router.get("/{report_id}")
async def get_report_detail(
    report_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(MedicalReport).where(MedicalReport.id == report_id, MedicalReport.user_id == user.id))
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    res_items = await db.execute(select(ReportResult).where(ReportResult.report_id == report.id))
    results = res_items.scalars().all()

    await log_audit_event(db, "VIEW_REPORT", "MedicalReport", report.id, user.id)

    file_name = os.path.basename(report.file_path) if report.file_path else f"{report.title}.{report.file_type or 'txt'}"
    file_size_kb = round(os.path.getsize(report.file_path) / 1024, 1) if (report.file_path and os.path.exists(report.file_path)) else 4.2

    return {
        "id": report.id,
        "title": report.title,
        "report_type": report.report_type,
        "report_date": str(report.report_date),
        "laboratory_name": report.laboratory_name,
        "doctor_name": report.doctor_name,
        "file_name": file_name,
        "file_type": report.file_type or "txt",
        "file_size_kb": file_size_kb,
        "ocr_status": report.ocr_status,
        "ocr_confidence": report.ocr_confidence,
        "is_user_verified": report.is_user_verified,
        "raw_extracted_text": report.raw_extracted_text,
        "results": [
            {
                "id": item.id,
                "biomarker_name": item.biomarker_name,
                "canonical_code": item.canonical_code,
                "numeric_value": item.numeric_value,
                "unit": item.unit,
                "ref_range_raw": item.ref_range_raw,
                "status_flag": item.status_flag
            }
            for item in results
        ],
        "ai_summary_layers": report.ai_summary_layers
    }


@router.get("/{report_id}/file")
async def get_report_original_file(
    report_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(MedicalReport).where(MedicalReport.id == report_id, MedicalReport.user_id == user.id))
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    await log_audit_event(db, "DOWNLOAD_FILE", "MedicalReport", report.id, user.id)

    if report.file_path and os.path.exists(report.file_path):
        media_type = "application/pdf" if report.file_type == "pdf" else "text/plain"
        return FileResponse(report.file_path, media_type=media_type, filename=os.path.basename(report.file_path))

    fallback_text = report.raw_extracted_text or f"Report: {report.title} | Date: {report.report_date} | Lab: {report.laboratory_name}"
    return PlainTextResponse(fallback_text, media_type="text/plain")


@router.delete("/{report_id}")
async def delete_single_report(
    report_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(MedicalReport).where(MedicalReport.id == report_id, MedicalReport.user_id == user.id))
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    res_items = await db.execute(select(ReportResult).where(ReportResult.report_id == report.id))
    for item in res_items.scalars().all():
        await db.delete(item)

    if report.file_path and os.path.exists(report.file_path):
        try:
            os.remove(report.file_path)
        except Exception:
            pass

    await db.delete(report)
    await db.commit()
    await log_audit_event(db, "DELETE_REPORT", "MedicalReport", report_id, user.id)

    return {"message": "Report permanently removed from records.", "report_id": report_id}


@router.put("/{report_id}/verify")
async def verify_and_confirm_report(
    report_id: str,
    payload: ReportVerificationPayload,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(MedicalReport).where(MedicalReport.id == report_id, MedicalReport.user_id == user.id))
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if payload.title:
        report.title = payload.title
    if payload.report_date:
        report.report_date = payload.report_date

    old_res = await db.execute(select(ReportResult).where(ReportResult.report_id == report.id))
    for r in old_res.scalars().all():
        await db.delete(r)

    dict_results = []
    for item in payload.results:
        flag = "within_range"
        if item.numeric_value is not None:
            if item.ref_min is not None and item.numeric_value < item.ref_min:
                flag = "below_range"
            elif item.ref_max is not None and item.numeric_value > item.ref_max:
                flag = "above_range"

        nr = ReportResult(
            report_id=report.id,
            biomarker_name=item.biomarker_name,
            canonical_code=item.canonical_code,
            numeric_value=item.numeric_value,
            string_value=str(item.numeric_value) if item.numeric_value else "",
            unit=item.unit,
            ref_min=item.ref_min,
            ref_max=item.ref_max,
            ref_range_raw=item.ref_range_raw or f"{item.ref_min} - {item.ref_max} {item.unit or ''}",
            status_flag=flag,
            confidence=1.0,
            recorded_date=report.report_date
        )
        db.add(nr)
        dict_results.append({
            "biomarker_name": item.biomarker_name,
            "numeric_value": item.numeric_value,
            "unit": item.unit,
            "ref_range_raw": item.ref_range_raw,
            "status_flag": flag
        })

    demographics = report.ai_summary_layers.get("patient_demographics", {}) if (report.ai_summary_layers and isinstance(report.ai_summary_layers, dict)) else {}
    if not demographics and report.raw_extracted_text:
        demographics = extract_patient_demographics(report.raw_extracted_text)
    insights = generate_layered_report_insights(report.title, str(report.report_date), dict_results, demographics=demographics)
    report.ai_summary_layers = insights
    report.is_user_verified = True

    await db.commit()
    await db.refresh(report)
    await log_audit_event(db, "VERIFY_REPORT", "MedicalReport", report.id, user.id)

    return {
        "message": "Report verified and permanently added to patient history.",
        "report_id": report.id,
        "is_user_verified": True,
        "ai_insights": insights
    }
