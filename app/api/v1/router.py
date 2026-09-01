"""
API v1 Router aggregator.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    reports,
    medications,
    wellness,
    trends,
    assistant,
    share,
    audit
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth & Profile"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports & OCR"])
api_router.include_router(medications.router, prefix="/medications", tags=["Medications & Reminders"])
api_router.include_router(wellness.router, prefix="/wellness", tags=["Wellness & Metrics"])
api_router.include_router(trends.router, prefix="/trends", tags=["Biomarker Trends"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["AI Assistant"])
api_router.include_router(share.router, prefix="/share", tags=["Doctor Share"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit & Compliance"])
