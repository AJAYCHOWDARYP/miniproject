"""
Authentication & Patient Profile Endpoints with support for Gmail and Mobile Number login.
"""
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token, decode_access_token
from app.models.user import User, HealthProfile
from app.schemas.all_schemas import UserCreate, UserLogin, TokenResponse, HealthProfileUpdate, HealthProfileOut
from app.services.audit_service import log_audit_event

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def clean_phone_number(raw: str) -> str:
    """Removes spaces, parentheses, and dashes from phone numbers."""
    if not raw:
        return ""
    # Keep leading + if present, strip others
    has_plus = raw.strip().startswith("+")
    digits = re.sub(r"\D", "", raw)
    return f"+{digits}" if (has_plus and digits) else digits


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


@router.post("/register", response_model=TokenResponse)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    email_clean = payload.email.strip().lower() if payload.email else None
    phone_clean = clean_phone_number(payload.phone_number) if payload.phone_number else None

    if not email_clean and not phone_clean and payload.identifier:
        ident = payload.identifier.strip()
        if "@" in ident:
            email_clean = ident.lower()
        else:
            phone_clean = clean_phone_number(ident)

    if not email_clean and not phone_clean:
        raise HTTPException(status_code=400, detail="Please provide a valid Gmail/Email address or Mobile phone number.")

    # Generate synthetic email for mobile-only accounts if email is missing
    if not email_clean and phone_clean:
        clean_digits = re.sub(r"[^\d]", "", phone_clean)
        email_clean = f"user_{clean_digits}@mobile.health.ai"

    # Check for duplicate email or phone
    conditions = []
    if email_clean:
        conditions.append(User.email == email_clean)
    if phone_clean:
        conditions.append(User.phone_number == phone_clean)

    if conditions:
        existing = await db.execute(select(User).where(or_(*conditions)))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="An account with this Gmail or Mobile number already exists.")

    hashed_pw = hash_password(payload.password)
    user = User(
        email=email_clean,
        phone_number=phone_clean,
        password_hash=hashed_pw,
        full_name=payload.full_name or "Patient"
    )
    db.add(user)
    await db.flush()

    profile = HealthProfile(user_id=user.id)
    db.add(profile)
    await db.commit()
    await db.refresh(user)

    await log_audit_event(db, "REGISTER_USER", "User", user.id, user.id)
    access_token = create_access_token({"sub": user.id, "email": user.email, "phone_number": user.phone_number})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "phone_number": user.phone_number,
        "full_name": user.full_name
    }


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    raw_ident = (payload.identifier or payload.email or payload.phone_number or "").strip()
    if not raw_ident:
        raise HTTPException(status_code=400, detail="Please enter your Gmail / Email or Mobile number.")

    user = None
    if "@" in raw_ident:
        # Match by email / gmail
        res = await db.execute(select(User).where(User.email.ilike(raw_ident.lower())))
        user = res.scalar_one_or_none()
    else:
        # Match by phone number or exact email fallback
        clean_phone = clean_phone_number(raw_ident)
        res = await db.execute(
            select(User).where(
                or_(
                    User.phone_number == raw_ident,
                    User.phone_number == clean_phone,
                    User.email.ilike(raw_ident.lower())
                )
            )
        )
        user = res.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect Gmail / Mobile number or password.")

    access_token = create_access_token({"sub": user.id, "email": user.email, "phone_number": user.phone_number})
    await log_audit_event(db, "LOGIN_SUCCESS", "User", user.id, user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "phone_number": user.phone_number,
        "full_name": user.full_name
    }


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "user_id": user.id,
        "email": user.email,
        "phone_number": user.phone_number,
        "full_name": user.full_name,
        "is_active": user.is_active
    }


@router.get("/profile")
async def get_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HealthProfile).where(HealthProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = HealthProfile(user_id=user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "email": user.email,
        "phone_number": user.phone_number,
        "full_name": user.full_name or "Patient",
        "date_of_birth": str(profile.date_of_birth) if profile.date_of_birth else None,
        "gender": profile.gender,
        "height_cm": profile.height_cm,
        "weight_kg": profile.weight_kg,
        "bmi": profile.bmi,
        "allergies": profile.allergies or [],
        "chronic_conditions": profile.chronic_conditions or [],
        "dietary_preference": profile.dietary_preference or "balanced",
        "activity_level": profile.activity_level or "moderate",
        "lifestyle_notes": "No specific lifestyle notes provided by patient."
    }


@router.put("/profile")
async def update_profile(
    payload: HealthProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(HealthProfile).where(HealthProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = HealthProfile(user_id=user.id)
        db.add(profile)

    if payload.full_name and payload.full_name != user.full_name:
        user.full_name = payload.full_name
        db.add(user)

    if payload.date_of_birth is not None: profile.date_of_birth = payload.date_of_birth
    if payload.gender is not None:
        profile.gender = payload.gender
        profile.sex = payload.gender
    if payload.height_cm is not None: profile.height_cm = payload.height_cm
    if payload.weight_kg is not None: profile.weight_kg = payload.weight_kg
    if payload.allergies is not None: profile.allergies = payload.allergies
    if payload.chronic_conditions is not None: profile.chronic_conditions = payload.chronic_conditions
    if payload.dietary_preference is not None: profile.dietary_preference = payload.dietary_preference
    if payload.activity_level is not None: profile.activity_level = payload.activity_level

    # Calculate BMI
    if profile.height_cm and profile.weight_kg and profile.height_cm > 0:
        h_m = profile.height_cm / 100.0
        profile.bmi = round(profile.weight_kg / (h_m * h_m), 1)

    await db.commit()
    await db.refresh(profile)
    await log_audit_event(db, "UPDATE_PROFILE", "HealthProfile", profile.id, user.id)

    return {
        "message": "Profile updated successfully",
        "profile": {
            "id": profile.id,
            "user_id": profile.user_id,
            "email": user.email,
            "phone_number": user.phone_number,
            "full_name": user.full_name,
            "bmi": profile.bmi,
            "height_cm": profile.height_cm,
            "weight_kg": profile.weight_kg
        }
    }
