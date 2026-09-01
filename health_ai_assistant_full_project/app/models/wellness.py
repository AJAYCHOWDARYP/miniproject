"""
Wellness models.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Float, Date, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class ExercisePlan(Base):
    __tablename__ = "exercise_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    weekly_goal_description = Column(Text, nullable=True)
    safety_guidelines = Column(Text, nullable=True)
    medical_clearance_advised = Column(Boolean, default=False)
    routines = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="exercise_plans")
    logs = relationship("ExerciseLog", back_populates="plan", cascade="all, delete-orphan")


class ExerciseLog(Base):
    __tablename__ = "exercise_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    plan_id = Column(String(36), ForeignKey("exercise_plans.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_name = Column(String(255), nullable=False)
    category = Column(String(100), default="walking")
    duration_minutes = Column(Float, nullable=False)
    intensity = Column(String(50), default="moderate")
    calories_burned_est = Column(Float, nullable=True)
    logged_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(Text, nullable=True)

    plan = relationship("ExercisePlan", back_populates="logs")


class DietPlan(Base):
    __tablename__ = "diet_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    target_calories_kcal = Column(Float, nullable=True)
    target_water_liters = Column(Float, default=2.5)
    macro_distribution = Column(JSON, default=dict)
    dietary_type = Column(String(100), default="balanced")
    safety_disclaimer = Column(Text, nullable=True)
    meal_structure = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="diet_plans")
    meal_logs = relationship("MealLog", back_populates="plan", cascade="all, delete-orphan")


class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    plan_id = Column(String(36), ForeignKey("diet_plans.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    meal_type = Column(String(50), nullable=False)
    food_items_logged = Column(Text, nullable=False)
    approx_calories = Column(Float, nullable=True)
    water_intake_ml = Column(Float, default=0.0)
    logged_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(Text, nullable=True)

    plan = relationship("DietPlan", back_populates="meal_logs")


class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    metric_type = Column(String(100), nullable=False)
    value_primary = Column(Float, nullable=False)
    value_secondary = Column(Float, nullable=True)
    unit = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="health_metrics")


class SymptomLog(Base):
    __tablename__ = "symptom_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symptom_name = Column(String(255), nullable=False)
    severity = Column(String(50), default="mild")
    duration_hours = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    logged_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="symptom_logs")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="medication_reminder")
    scheduled_for = Column(DateTime, nullable=False)
    is_sent = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    action_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="notifications")
