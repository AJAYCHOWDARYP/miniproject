"""
Pydantic Schemas for Authentication, Profiles, Reports, Medications, Assistant, and Wellness.
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    email: Optional[str] = None
    phone_number: Optional[str] = None
    identifier: Optional[str] = None
    password: str
    full_name: Optional[str] = "Patient"


class UserLogin(BaseModel):
    identifier: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    full_name: Optional[str] = "Patient"


class HealthProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    dietary_preference: Optional[str] = None
    activity_level: Optional[str] = None
    lifestyle_notes: Optional[str] = None


class HealthProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    full_name: Optional[str] = "Patient"
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    dietary_preference: Optional[str] = "balanced"
    activity_level: Optional[str] = "moderate"
    lifestyle_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class VerifiedResultItem(BaseModel):
    biomarker_name: str
    canonical_code: Optional[str] = None
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    ref_range_raw: Optional[str] = None
    status_flag: Optional[str] = "within_range"


class ReportVerificationPayload(BaseModel):
    title: Optional[str] = None
    report_date: Optional[date] = None
    results: List[VerifiedResultItem]


class MedicationScheduleCreate(BaseModel):
    scheduled_time_str: str = "08:00 AM"
    dose_quantity: str = "1 tablet"
    reminder_enabled: bool = True


class MedicationItemCreate(BaseModel):
    brand_name: str
    generic_name: Optional[str] = None
    strength: str
    dosage_form: Optional[str] = "tablet"
    frequency_type: str = "once_daily"
    route: Optional[str] = "oral"
    food_relation: str = "after_food"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_days: Optional[int] = 30
    special_instructions: Optional[str] = None
    schedules: List[MedicationScheduleCreate] = []


class PrescriptionCreate(BaseModel):
    prescribing_doctor: Optional[str] = "Healthcare Provider"
    clinic_or_hospital: Optional[str] = None
    prescription_date: Optional[date] = None
    valid_until: Optional[date] = None
    diagnosis_indicated: Optional[str] = None
    notes: Optional[str] = None
    medications: List[MedicationItemCreate] = []


class PrescriptionUploadPayload(BaseModel):
    prescribing_doctor: Optional[str] = None
    prescription_date: Optional[date] = None
    notes: Optional[str] = None
    medications: List[MedicationItemCreate] = []


class MedicationLogAction(BaseModel):
    medication_id: str
    schedule_id: Optional[str] = None
    action: str  # TAKEN, SKIPPED, SNOOZED
    scheduled_for: datetime
    notes: Optional[str] = None


class ExerciseLogCreate(BaseModel):
    activity_type: str = "Walking"
    duration_minutes: int = 30
    intensity: str = "moderate"
    calories_burned_estimated: Optional[float] = None
    notes: Optional[str] = None


class MealLogCreate(BaseModel):
    meal_type: str = "breakfast"
    food_items_logged: str = "Water"
    water_intake_ml: Optional[float] = 250.0
    estimated_calories_kcal: Optional[float] = None
    notes: Optional[str] = None


class HealthMetricCreate(BaseModel):
    metric_type: str
    numeric_value: float
    unit: str
    context: Optional[str] = None


class SymptomLogCreate(BaseModel):
    symptom_name: str
    severity_scale: int = 1
    notes: Optional[str] = None


class ReminderPreferenceItem(BaseModel):
    meal_key: str
    name: str
    time: str
    enabled: bool = True


class ChatMessageIn(BaseModel):
    message: str
    context_report_id: Optional[str] = None


class ChatMessageOut(BaseModel):
    reply: str
    is_emergency: bool = False
    emergency_details: Optional[Dict[str, Any]] = None
    disclaimer: str


class DoctorShareRequest(BaseModel):
    recipient_email: Optional[EmailStr] = None
    recipient_name: Optional[str] = None
    share_duration_days: int = 7
    include_reports: bool = True
    include_prescriptions: bool = True
    include_lifestyle_logs: bool = True
    doctor_notes: Optional[str] = None
