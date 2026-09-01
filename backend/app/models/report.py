"""
Medical Report and Lab Result Models.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Float, Date, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class MedicalReport(Base):
    __tablename__ = "medical_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    report_type = Column(String(100), default="Laboratory Report")
    report_date = Column(Date, nullable=False)
    laboratory_name = Column(String(255), nullable=True)
    doctor_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(50), default="pdf")
    ocr_status = Column(String(50), default="COMPLETED")
    ocr_confidence = Column(Float, default=1.0)
    raw_extracted_text = Column(Text, nullable=True)
    is_user_verified = Column(Boolean, default=False)
    ai_summary_layers = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="reports")
    results = relationship("ReportResult", back_populates="report", cascade="all, delete-orphan")


class ReportResult(Base):
    __tablename__ = "report_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("medical_reports.id", ondelete="CASCADE"), nullable=False)
    biomarker_name = Column(String(255), nullable=False)
    canonical_code = Column(String(100), nullable=True)
    numeric_value = Column(Float, nullable=True)
    string_value = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=True)
    ref_min = Column(Float, nullable=True)
    ref_max = Column(Float, nullable=True)
    ref_range_raw = Column(String(100), nullable=True)
    status_flag = Column(String(50), default="within_range")
    confidence = Column(Float, default=1.0)
    explanation_simple = Column(Text, nullable=True)
    recorded_date = Column(Date, nullable=False)

    report = relationship("MedicalReport", back_populates="results")
