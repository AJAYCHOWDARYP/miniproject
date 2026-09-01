"""
Guardrailed AI Assistant Endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User, MedicalCondition
from app.models.medication import Medication
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.all_schemas import ChatMessageIn, ChatMessageOut
from app.services.ai_guardrails import (
    evaluate_emergency_triage,
    evaluate_prescription_refusal,
    evaluate_diagnosis_refusal,
    STANDARD_DISCLAIMER
)

router = APIRouter()


@router.post("/chat", response_model=ChatMessageOut)
async def chat_with_assistant(
    payload: ChatMessageIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_msg = payload.message.strip()

    emergency_eval = evaluate_emergency_triage(user_msg)
    if emergency_eval:
        return ChatMessageOut(
            reply=emergency_eval["message"],
            is_emergency=True,
            emergency_guidance=emergency_eval,
            source_layer="emergency_triage_interceptor",
            suggested_follow_up_questions=["Call local emergency services immediately"],
            disclaimer=STANDARD_DISCLAIMER
        )

    rx_refusal = evaluate_prescription_refusal(user_msg)
    if rx_refusal:
        return ChatMessageOut(
            reply=rx_refusal,
            is_emergency=False,
            source_layer="prescription_safety_guardrail",
            suggested_follow_up_questions=[
                "What questions should I ask my doctor about my current prescription?",
                "How do I set up reminders for my doctor-provided medicines?",
                "What should I do if I miss a dose?"
            ],
            disclaimer=STANDARD_DISCLAIMER
        )

    diag_refusal = evaluate_diagnosis_refusal(user_msg)
    if diag_refusal:
        return ChatMessageOut(
            reply=diag_refusal,
            is_emergency=False,
            source_layer="diagnosis_safety_guardrail",
            suggested_follow_up_questions=[
                "Which values in my recent blood test are outside the reference range?",
                "What questions can I take to my next doctor appointment?",
                "Explain what HbA1c or Cholesterol tests measure."
            ],
            disclaimer=STANDARD_DISCLAIMER
        )

    med_res = await db.execute(select(Medication).where(Medication.user_id == user.id, Medication.is_active == True))
    meds = [f"{m.brand_name} {m.strength}" for m in med_res.scalars().all()]

    msg_lower = user_msg.lower()
    if "hba1c" in msg_lower:
        reply = (
            "HbA1c (Glycated Hemoglobin) reflects your average blood sugar level over the past 2 to 3 months.\\n\\n"
            "• Standard Reference Range: Typically below 5.7%\\n"
            "• 5.7% to 6.4%: Often evaluated by laboratories as prediabetes range\\n"
            "• 6.5% or above: Prompts physician evaluation for glycemic management\\n\\n"
            "Please review your testing laboratory's exact interval with your doctor."
        )
        suggestions = ["What questions should I ask my doctor about HbA1c?", "How often should HbA1c be tested?"]
    elif "next medicine" in msg_lower or "schedule" in msg_lower:
        if meds:
            reply = f"You currently have active medication(s): {', '.join(meds)}. You can check your exact reminder slots in the Medications tab."
        else:
            reply = "You currently have no active medications recorded in your profile."
        suggestions = ["View today's medicine checklist", "How do I log my adherence?"]
    elif "questions for doctor" in msg_lower or "ask doctor" in msg_lower:
        reply = (
            "Here are high-value questions for your next clinic visit:\\n\\n"
            "1. 'Are there specific lab values from my recent tests that we should monitor or re-test?'\\n"
            "2. 'Are my current medications still appropriate, or are any dosage adjustments needed?'\\n"
            "3. 'Are there specific dietary or exercise boundaries I should observe?'"
        )
        suggestions = ["Generate a Doctor Sharing Summary", "Review my recent lab values"]
    else:
        reply = (
            "Hello! I am your personal health organizer and decision-support assistant. "
            "I can help you review uploaded lab reports, organize doctor-prescribed medications, "
            "track wellness routines, and prepare questions for your doctor.\\n\\n"
            "How can I assist you with your health records today?"
        )
        suggestions = [
            "Explain HbA1c in simple words",
            "What questions should I ask my doctor?",
            "What should I do if I miss a dose?"
        ]

    return ChatMessageOut(
        reply=reply,
        is_emergency=False,
        source_layer="guardrailed_assistant",
        suggested_follow_up_questions=suggestions,
        disclaimer=STANDARD_DISCLAIMER
    )
