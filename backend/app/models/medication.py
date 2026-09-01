"""
Prescription and Medication models.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Float, Date, Time, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    prescribing_doctor = Column(String(255), nullable=False)
    clinic_or_hospital = Column(String(255), nullable=True)
    prescription_date = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)
    diagnosis_indicated = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="prescriptions")
    medications = relationship("Medication", back_populates="prescription", cascade="all, delete-orphan")


class Medication(Base):
    __tablename__ = "medications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    prescription_id = Column(String(36), ForeignKey("prescriptions.id", ondelete="SET NULL"), nullable=True)
    brand_name = Column(String(255), nullable=False)
    generic_name = Column(String(255), nullable=True)
    strength = Column(String(100), nullable=False)
    dosage_form = Column(String(50), default="Tablet")
    frequency_type = Column(String(100), default="twice_daily")
    route = Column(String(50), default="Oral")
    food_relation = Column(String(100), default="after_food")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    duration_days = Column(Float, nullable=True)
    prescribing_doctor = Column(String(255), nullable=True)
    special_instructions = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="medications")
    prescription = relationship("Prescription", back_populates="medications")
    schedules = relationship("MedicationSchedule", back_populates="medication", cascade="all, delete-orphan")
    logs = relationship("MedicationLog", back_populates="medication", cascade="all, delete-orphan")


class MedicationSchedule(Base):
    __tablename__ = "medication_schedules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    medication_id = Column(String(36), ForeignKey("medications.id", ondelete="CASCADE"), nullable=False)
    scheduled_time_str = Column(String(10), nullable=False)
    dose_quantity = Column(String(50), default="1 tablet")
    reminder_enabled = Column(Boolean, default=True)

    medication = relationship("Medication", back_populates="schedules")
    logs = relationship("MedicationLog", back_populates="schedule", cascade="all, delete-orphan")


class MedicationLog(Base):
    __tablename__ = "medication_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    schedule_id = Column(String(36), ForeignKey("medication_schedules.id", ondelete="SET NULL"), nullable=True)
    medication_id = Column(String(36), ForeignKey("medications.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scheduled_for = Column(DateTime, nullable=False)
    action_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(50), default="TAKEN")
    skip_reason = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    medication = relationship("Medication", back_populates="logs")
    schedule = relationship("MedicationSchedule", back_populates="logs")
